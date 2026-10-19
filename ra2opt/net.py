"""受限 HTTP 下载：协议 + 主机白名单 + 解析后 IP 边界校验。

工具的下载只有一个用途——取 cnc-ddraw 的 release 包。虽然 URL 来自 GitHub API
（本可信），但 API 响应终究是外部输入，直接塞进 `urlopen` 就是一条 SSRF 面：
万一 URL 被换成 `http://169.254.169.254/...` 或内网地址，就会打到本机/内网服务。

因此所有出网请求都经 `fetch()`，它强制：

1. 协议必须是 `https`；
2. 主机必须落在显式白名单里（github.com / api.github.com / *.githubusercontent.com）；
3. 主机名解析出的**每一个** IP 都不能是环回、私网、链路本地、保留地址
   （同时挡住"域名解析到内网"和 DNS rebinding 的常见形态）；
4. 重定向逐跳复用同一套校验，超过 3 跳即中止；
5. 响应体大小有上限，避免被灌爆内存。

白名单是本模块里的常量，不来自配置或命令行。

### 关于 TUN 代理的 fake-IP（198.18.0.0/15）

Clash/Surge 这类 TUN 模式代理默认用 `198.18.0.0/15`（RFC 2544 基准测试段）作为
fake-IP：DNS 查询由代理本地应答，返回一个该段内的假地址，真实连接再由代理转发。
这会让上面第 3 条误伤——明明目标是 api.github.com，解析结果却是"保留地址"。

因此对**白名单内的主机**额外放行 `198.18.0.0/15`，并且：

- 只放行这一个段，环回 / RFC1918 / 链路本地（含云元数据 169.254.169.254）/ 组播
  依旧一律拒绝；
- 主机白名单照旧生效，不能拿它去打任意域名；
- 连接仍走系统的 TLS 校验（`ssl` 默认 `check_hostname=True`），假地址无法冒充
  api.github.com 的证书。

放行事实会记进 `notes()`，体检报告里会显示出来，不做静默降级。
"""

from __future__ import annotations

import ipaddress
import socket
import urllib.error
import urllib.request
from urllib.parse import urlparse

ALLOWED_SCHEMES = ("https",)
ALLOWED_HOSTS = (
    "github.com",
    "api.github.com",
    "codeload.github.com",
    "objects.githubusercontent.com",
    "release-assets.githubusercontent.com",
)
ALLOWED_HOST_SUFFIXES = (".githubusercontent.com",)
MAX_BYTES = 64 * 1024 * 1024
MAX_REDIRECTS = 3
USER_AGENT = "ra2opt/1.0 (+local RA2 stability/performance tuner)"

# TUN 代理 fake-IP 段：仅对白名单主机放行
PROXY_FAKE_IP_NETWORKS = (ipaddress.ip_network("198.18.0.0/15"),)

_NOTES: list = []


def notes() -> list:
    """本次进程内发生过的"降级/放行"记录，供报告展示。"""
    return list(_NOTES)


def clear_notes() -> None:
    _NOTES.clear()


class FetchError(OSError):
    """URL 未通过校验，或下载失败。"""


def _is_benign(ip) -> bool:
    return not (ip.is_private or ip.is_loopback or ip.is_link_local
                or ip.is_reserved or ip.is_multicast or ip.is_unspecified)


def _is_proxy_fake_ip(ip) -> bool:
    return any(ip in net for net in PROXY_FAKE_IP_NETWORKS)


def validate_url(url: str) -> str:
    """校验协议与主机白名单，并确认解析到的 IP 都在公网。返回原 URL。"""
    parsed = urlparse(url)
    if parsed.scheme not in ALLOWED_SCHEMES:
        raise FetchError(f"只允许 https：{url}")
    host = (parsed.hostname or "").lower()
    if not host:
        raise FetchError(f"URL 缺少主机名：{url}")
    if host not in ALLOWED_HOSTS and not host.endswith(ALLOWED_HOST_SUFFIXES):
        raise FetchError(f"主机不在白名单内：{host}")

    try:
        infos = socket.getaddrinfo(host, parsed.port or 443, proto=socket.IPPROTO_TCP)
    except socket.gaierror as exc:
        raise FetchError(f"无法解析主机 {host}：{exc}") from exc
    if not infos:
        raise FetchError(f"主机 {host} 没有可用地址")

    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if _is_benign(ip):
            continue
        if _is_proxy_fake_ip(ip):
            note = (f"{host} 解析到 {ip}（TUN 代理的 fake-IP 段），对白名单主机放行；"
                    f"TLS 证书校验仍然验证 {host} 的身份")
            if note not in _NOTES:
                _NOTES.append(note)
            continue
        raise FetchError(f"主机 {host} 解析到非公网地址 {ip}，拒绝请求")
    return url


class _ValidatingRedirectHandler(urllib.request.HTTPRedirectHandler):
    """重定向逐跳复用同一套校验，避免"白名单域名 302 到内网"。"""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        validate_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _build_opener() -> urllib.request.OpenerDirector:
    opener = urllib.request.build_opener(_ValidatingRedirectHandler)
    return opener


def fetch(url: str, *, timeout: int = 30, headers: dict | None = None,
          max_bytes: int = MAX_BYTES) -> bytes:
    """校验后 GET，返回响应体。"""
    validate_url(url)
    request = urllib.request.Request(url, headers={
        "User-Agent": USER_AGENT,
        "Accept": "application/vnd.github+json, application/octet-stream",
        **(headers or {}),
    })
    opener = _build_opener()
    try:
        with opener.open(request, timeout=timeout) as resp:
            final = resp.geturl()
            if final != url:
                validate_url(final)          # 兜底再校验一次最终 URL
            declared = resp.headers.get("Content-Length")
            if declared and int(declared) > max_bytes:
                raise FetchError(f"响应过大（{declared} 字节 > 上限 {max_bytes}）")
            chunks, total = [], 0
            while True:
                block = resp.read(64 * 1024)
                if not block:
                    break
                total += len(block)
                if total > max_bytes:
                    raise FetchError(f"响应超过上限 {max_bytes} 字节")
                chunks.append(block)
            return b"".join(chunks)
    except urllib.error.HTTPError as exc:
        raise FetchError(f"HTTP {exc.code}：{url}") from exc
    except urllib.error.URLError as exc:
        raise FetchError(f"请求失败：{url}（{exc.reason}）") from exc
