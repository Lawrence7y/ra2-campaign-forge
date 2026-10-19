"""cnc-ddraw 的获取、安装与 ddraw.ini 调优。

为什么升级是本项目优先级最高的一项：cnc-ddraw 就是本机已经装着的 DirectDraw
代理（`ddraw.dll` v4.4.7 / 2021 年），而官方在 2021→2024 之间发到 v7.1.0，
其中多条是**针对 RA2 的崩溃修复**：

- v6.3   Steam 版红色警戒 2 崩溃 workaround
- v6.4   非活动窗口下步兵相关鼠标输入修复
- v7.0   特权指令崩溃修复、窗口尺寸与整型缩放修复
- v7.1   OpenGL 无硬件加速时的崩溃、退出时崩溃、GDI 限速器支持等

ddraw.ini 的调优依据是 cnc-ddraw 官方注释 + RA2/YR 引擎特性（见 docs/OPTIMIZE.md）。
调优以官方新版 ddraw.ini 为基线，只覆盖我们明确要改的键，避免下发该版本里
已不存在的过时键。

所有出网请求都走 `net.fetch()`（协议/主机白名单/IP 边界校验）。
"""

from __future__ import annotations

import json
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

from . import inifile, net, safewrite

RELEASE_API = "https://api.github.com/repos/CnCNet/cnc-ddraw/releases/latest"
ASSET_NAME = "cnc-ddraw.zip"
VENDOR_DIR = Path(__file__).resolve().parent / "vendor"
_ZIP_MAGIC = b"PK\x03\x04"

# cnc-ddraw 为每个游戏准备的专属节，节名 = exe 主名（不含扩展名）。
# 专属节的优先级高于全局 [ddraw] 节。
DDRAW_EXE_SECTIONS = ("gamemd", "ra2md", "gamemd-spawn")

# 下发的 [ddraw] 全局设置。依据：cnc-ddraw 官方 ddraw.ini 注释 + RA2/YR 引擎特性。
#
# 这里刻意**不**碰 `windowed` / `fullscreen`：那是玩家的显示偏好（有人要独占全屏，
# 有人要窗口化），不属于"稳定性/性能"范畴，工具不该替玩家决定。
DDRAW_GLOBAL = {
    # 0x0 = 跟随游戏自身分辨率（ra2md.ini 的 ScreenWidth/Height），1:1 输出。
    # 这一条针对的是一类常见错配：窗口写了别的尺寸而 maintas 关着，画面被
    # 非等比拉伸得又糊又变形。
    "width": "0",
    "height": "0",
    "maintas": "false",
    "boxing": "false",
    "renderer": "direct3d9",
    # 刻意不设缩放滤镜：v4 的 `d3d9linear` 在 v7 已改名为 `d3d9_filter`
    # （0=邻近 1=双线性 2=双三次 3=Lanczos），而且当 width/height=0（1:1 输出）时
    # 根本不发生缩放，滤镜不参与。要用缩放时再看 v7 自带的默认值即可。
    "nonexclusive": "true",
    "noactivateapp": "true",
    "adjmouse": "true",
    # 0 = 模拟 60Hz 垂直同步；RA2/YR 的时序就是按 60Hz 设计的
    "maxgameticks": "0",
    "vsync": "false",
    # 绑定 CPU0：跨核时序/中断处理是这类 2001 年引擎崩溃与卡死的常见来源
    "singlecpu": "true",
    "savesettings": "1",
}

# 上面这些键里，属于"显示/缩放"的一组：用 --keep-display 可以整个跳过
DDRAW_DISPLAY_KEYS = ("width", "height", "maintas", "boxing")

# 每个 exe 专属节的设置
DDRAW_PER_EXE = {
    "maxfps": "60",     # 渲染上限 60，避免空转烧 CPU
    "minfps": "-1",     # 跟随 maxfps
    "tshack": "true",   # TS/RA2 引擎专用兼容开关（必须开）
}


# ---------------------------------------------------------------------------
# 获取
# ---------------------------------------------------------------------------

@dataclass
class Release:
    version: str = ""
    published: str = ""
    url: str = ""
    size: int = 0
    body: str = ""
    source: str = ""


def latest_release(*, timeout: int = 15) -> Release:
    """查询 cnc-ddraw 最新版。失败时抛 OSError，由调用方决定是否降级。"""
    payload = net.fetch(RELEASE_API, timeout=timeout)
    data = json.loads(payload.decode("utf-8"))
    rel = Release(version=str(data.get("tag_name", "")).lstrip("v"),
                  published=str(data.get("published_at") or "")[:10],
                  body=str(data.get("body") or ""), source="github")
    for asset in data.get("assets", []):
        if asset.get("name") == ASSET_NAME:
            rel.url = str(asset.get("browser_download_url") or "")
            rel.size = int(asset.get("size") or 0)
            break
    return rel


def cached_zip() -> Path | None:
    """返回 vendor 缓存里最新的 cnc-ddraw zip。"""
    if not VENDOR_DIR.is_dir():
        return None
    zips = sorted(VENDOR_DIR.glob("cnc-ddraw-*.zip"))
    return zips[-1] if zips else None


def download(rel: Release, *, timeout: int = 180, force: bool = False) -> Path:
    """下载 release zip 到 `ra2opt/vendor/`。已有同名非空缓存则直接复用。"""
    if not rel.url:
        raise OSError("release 信息里没有 cnc-ddraw.zip 下载地址")
    VENDOR_DIR.mkdir(parents=True, exist_ok=True)
    target = VENDOR_DIR / f"cnc-ddraw-{rel.version or 'latest'}.zip"
    if target.is_file() and not force and target.stat().st_size > 100_000:
        return target
    payload = net.fetch(rel.url, timeout=timeout)
    if not payload.startswith(_ZIP_MAGIC):
        raise ValueError("下载内容不是 zip（前 4 字节不匹配）")
    staging = target.with_name(target.name + ".part")
    staging.write_bytes(payload)
    staging.replace(target)
    return target


def read_zip(zip_path) -> dict:
    """从 release zip 中取出 ddraw.dll、官方 ddraw.ini 与文件清单。"""
    out = {"dll": None, "ini": None, "members": []}
    with zipfile.ZipFile(zip_path) as zf:
        for name in zf.namelist():
            out["members"].append(name)
            low = name.lower()
            if low.endswith("ddraw.dll") and "legacy" not in low and out["dll"] is None:
                out["dll"] = zf.read(name)
            elif low.endswith("ddraw.ini") and out["ini"] is None:
                out["ini"] = zf.read(name).decode("latin-1")
    if out["dll"] is None:
        raise ValueError(f"{zip_path} 里没有找到 ddraw.dll")
    return out


# ---------------------------------------------------------------------------
# ddraw.ini 调优
# ---------------------------------------------------------------------------

@dataclass
class TuneResult:
    text: str
    changes: list = field(default_factory=list)
    unknown_keys: list = field(default_factory=list)
    missing_sections: list = field(default_factory=list)


def tune_ini(current_text: str, baseline_text: str | None = None,
             *, keep_display: bool = False) -> TuneResult:
    """在现有 ddraw.ini 上做 RA2/YR 专项调优。

    `baseline_text` 传官方新版的 ddraw.ini：用来校验要写的键在新版里确实存在。
    为 None 时跳过校验（只用于离线测试）。

    `keep_display=True` 时跳过显示/缩放相关键（`DDRAW_DISPLAY_KEYS`），
    保留玩家已有的分辨率与缩放偏好。
    """
    doc = inifile.IniFile.parse(current_text)
    baseline = inifile.IniFile.parse(baseline_text) if baseline_text else None
    known_global = {k.lower() for k in baseline.keys("ddraw")} if baseline else None
    known_exe = {k.lower() for k in baseline.keys("gamemd")} if baseline else None

    changes, unknown = [], []
    for key, value in DDRAW_GLOBAL.items():
        if keep_display and key in DDRAW_DISPLAY_KEYS:
            continue
        if known_global is not None and key.lower() not in known_global:
            unknown.append(f"ddraw.{key}")
            continue
        if doc.set("ddraw", key, value):
            changes.append(f"ddraw.{key}={value}")

    missing = []
    for section in DDRAW_EXE_SECTIONS:
        if section != "gamemd" and not doc.has_section(section):
            continue
        for key, value in DDRAW_PER_EXE.items():
            if known_exe is not None and key.lower() not in known_exe:
                unknown.append(f"{section}.{key}")
                continue
            if doc.set(section, key, value):
                changes.append(f"{section}.{key}={value}")
    if not doc.has_section("gamemd"):
        missing.append("gamemd")

    return TuneResult(text=doc.text(), changes=changes,
                      unknown_keys=unknown, missing_sections=missing)


_WHY = {
    "ddraw.width": "窗口宽跟随游戏分辨率，1:1 像素输出（0 = 用游戏请求的尺寸）",
    "ddraw.height": "窗口高跟随游戏分辨率，1:1 像素输出",
    "ddraw.maintas": "关闭信箱模式：1:1 输出时不需要补边，也就不会出现额外缩放",
    "ddraw.boxing": "关闭黑边整数缩放，避免分辨率不匹配时的二次缩放",
    "ddraw.renderer": "Direct3D9 渲染器（比 GDI 更稳、缩放质量更好）",
    "ddraw.d3d9linear": "缩放用线性过滤，减少锯齿/块状",
    "ddraw.nonexclusive": "禁用独占模式，避免按钮/影片不可见的老问题",
    "ddraw.noactivateapp": "屏蔽 WM_ACTIVATEAPP，避免 Alt+Tab 崩溃",
    "ddraw.adjmouse": "鼠标灵敏度随缩放自动校正",
    "ddraw.maxgameticks": "0 = 模拟 60Hz 垂直同步，与 RA2/YR 的时序设计一致",
    "ddraw.vsync": "关闭垂直同步（开启会引入输入延迟）",
    "ddraw.singlecpu": "绑定 CPU0，规避多核时序导致的崩溃/卡死",
    "ddraw.savesettings": "退出时保存窗口位置与尺寸",
    "gamemd.maxfps": "渲染上限 60 帧，避免空转烧 CPU",
    "gamemd.minfps": "-1 = 跟随 maxfps",
    "gamemd.tshack": "TS/RA2 引擎专用兼容开关（必须开）",
}


def compare_ini_keys(current_text: str, baseline_text: str,
                     sections=("ddraw",)) -> dict:
    """列出官方新版 ddraw.ini 里有、但当前配置里没有的键。

    只做提示、不写值：升级 wrapper 之后有些新键（`center_window` 之类）值得知道，
    但我们不替玩家填值——cnc-ddraw 对缺失的键就用它自己的默认值。
    """
    current = inifile.IniFile.parse(current_text)
    baseline = inifile.IniFile.parse(baseline_text)
    out = {}
    for section in sections:
        have = {k.lower() for k in current.keys(section)}
        want = [k for k in baseline.keys(section) if k.lower() not in have]
        if want:
            out[section] = want
    return out


def describe_changes(changes) -> list:
    """把变更列表配上人话解释。"""
    out = []
    for c in changes:
        full = c.split("=")[0]
        key = full.split(".")[-1]
        out.append((c, _WHY.get(full, _WHY.get(key, ""))))
    return out


# ---------------------------------------------------------------------------
# 安装
# ---------------------------------------------------------------------------

def install(game, zip_path, *, backup=None, apply_ini=True,
            keep_display: bool = False) -> dict:
    """把 cnc-ddraw 的 ddraw.dll 装进游戏目录，并按需调优 ddraw.ini。

    `backup` 传 `backup.BackupSet`：覆盖前先留原始快照。
    """
    payload = read_zip(zip_path)
    report = {"dll_written": False, "ini_written": False, "ini_changes": [],
              "unknown_keys": [], "new_keys_available": {},
              "members": len(payload["members"]),
              "dll_unchanged": False, "ini_unchanged": False}

    # 内容相同就不写、也不记成改动——否则"改动了几个文件"这个数字会失真
    if game.has("ddraw.dll") and safewrite.read_bytes(game.path, "ddraw.dll") == payload["dll"]:
        report["dll_unchanged"] = True
    else:
        if backup is not None:
            backup.snapshot("ddraw.dll")
        safewrite.write_bytes(game.path, "ddraw.dll", payload["dll"], allow_create=True)
        report["dll_written"] = True
        if backup is not None:
            backup.record_file("ddraw.dll")

    if apply_ini:
        if game.has("ddraw.ini"):
            current = safewrite.read_bytes(game.path, "ddraw.ini").decode("latin-1")
        else:
            current = payload["ini"] or ""
        tuned = tune_ini(current, baseline_text=payload["ini"], keep_display=keep_display)
        report["ini_changes"] = tuned.changes
        report["unknown_keys"] = tuned.unknown_keys
        report["new_keys_available"] = compare_ini_keys(current, payload["ini"] or "")
        if tuned.text == current:
            report["ini_unchanged"] = True
        else:
            if backup is not None:
                backup.snapshot("ddraw.ini")
            safewrite.write_bytes(game.path, "ddraw.ini",
                                  tuned.text.encode("latin-1", errors="replace"),
                                  allow_create=True)
            report["ini_written"] = True
            if backup is not None:
                backup.record_file("ddraw.ini")

    return report
