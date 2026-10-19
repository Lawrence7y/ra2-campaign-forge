"""游戏目录模型：识别版本、探测已装组件、读取包装 DLL 版本、生成 ddraw 调优配置。"""

from __future__ import annotations

import hashlib
import os
import re
from dataclasses import dataclass
from pathlib import Path

from . import KNOWN_GAMEMD, GAMEMD_EXE, pe, safewrite

# 游戏目录内的文件名一律用裸文件名（无分隔符、无盘符、无 ..）。
# 这是防越界的第一道门：`Path("D:/game") / "C:/Windows/System32/x.dll"` 在 Windows 上
# 会把整个路径**替换**成右侧的绝对路径，于是"拼路径"就变成了"写任意文件"。
BARE_NAME_RE = re.compile(r"^[A-Za-z0-9._-]{1,64}$")


@dataclass
class ExeIdentity:
    name: str
    path: Path
    size: int
    sha256: str
    info: pe.PEInfo | None
    known: str | None
    text_sha256: str | None = None
    patched: bool = False

    @property
    def laa(self) -> bool:
        return bool(self.info and self.info.laa)

    @property
    def high_entropy_va(self) -> bool:
        return bool(self.info and self.info.high_entropy_va)

    @property
    def stack_mb(self) -> float:
        return (self.info.stack_reserve / pe.MB) if self.info else 0.0

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "size": self.size,
            "sha256": self.sha256,
            "text_sha256": self.text_sha256,
            "known_as": self.known,
            "patched_by_ra2opt": self.patched,
            "laa": self.laa,
            "characteristics": "%04X" % self.info.characteristics if self.info else None,
            "high_entropy_va": self.high_entropy_va,
            "nx_compat": bool(self.info and self.info.nx_compat),
            "has_detour_section": bool(self.info and self.info.has_detour_section),
            "writable_executable_sections": self.info.writable_executable_sections if self.info else [],
            "stack_reserve": self.info.stack_reserve if self.info else None,
            "heap_reserve": self.info.heap_reserve if self.info else None,
            "checksum": "%08X" % self.info.checksum if self.info else None,
            "dll_characteristics": "%04X" % self.info.dll_characteristics if self.info else None,
        }


class GameDir:
    """一个 RA2/YR 安装目录。构造时就校验它是合法的游戏目录。"""

    def __init__(self, path):
        self.path = Path(os.path.realpath(os.fspath(path)))
        if not self.path.is_dir():
            raise ValueError(f"目录不存在：{self.path}")
        self.gamemd = self.path / GAMEMD_EXE
        self.valid = self.gamemd.is_file()

    # -- 基础 -------------------------------------------------------------
    def exe(self, name: str) -> Path:
        """游戏目录内的某个文件路径。

        `name` 必须是**裸文件名**：带分隔符 / 盘符 / `..` 一律拒绝。
        没有这道门，`Path("D:/game") / "C:/Windows/x.dll"` 会因为 pathlib 的
        "绝对路径替换"语义直接跳出游戏目录。
        """
        if not BARE_NAME_RE.match(name or "") or ".." in str(name):
            raise ValueError(f"非法的文件名：{name!r}（只接受字母数字 . _ - 组成的裸文件名）")
        return self.path / name

    def resolve_exe(self, name: str) -> Path:
        """解析成游戏目录内**真实存在**的文件路径；非法 / 越界 / 不存在都拒绝。

        凡是文件名来自用户输入（如 `--exe`）的地方都必须过这里，
        而不是直接用 `exe()` 拼路径后就写盘。
        """
        return safewrite.resolve_within(self.path, self.exe(name))

    def has(self, name: str) -> bool:
        try:
            return self.exe(name).is_file()
        except ValueError:
            return False

    def present_exes(self) -> list:
        from . import GAME_EXES

        return [n for n in GAME_EXES if self.has(n)]

    def identity(self, name: str) -> ExeIdentity | None:
        path = self.exe(name)
        if not path.is_file():
            return None
        sha = sha256_file(path)
        info = None
        text_sha = None
        try:
            info = pe.read(path)
            text_sha = pe.text_section_sha256(path)
        except pe.PEError:
            info = None
        known = None
        entry = KNOWN_GAMEMD.get(text_sha or "")
        if entry:
            known = entry["name"]
        elif info is not None and info.has_detour_section:
            known = "未知（exe 被第三方 Detours 补丁改过，代码段指纹无法匹配官方版）"
        patched = bool(entry and sha != entry.get("full_sha256"))
        return ExeIdentity(name=name, path=path, size=path.stat().st_size, sha256=sha,
                           info=info, known=known, text_sha256=text_sha, patched=patched)

    # -- 已装组件 ---------------------------------------------------------
    def components(self) -> dict:
        names = {p.name.lower() for p in self.path.iterdir() if p.is_file()}
        return {
            "cnc_ddraw": "ddraw.dll" in names,
            "ddraw_ini": "ddraw.ini" in names,
            "xwis": "xwis.dll" in names or "xwis0.dll" in names,
            "ipxwrapper": "ipxwrapper.dll" in names,
            "ares": any(n.startswith("ares") and n.endswith(".dll") for n in names),
            "phobos": any("phobos" in n for n in names),
            "syringe": "syringe.exe" in names,
            "expandmd98": "expandmd98.mix" in names,
            "expandmd99": "expandmd99.mix" in names,
            "battlemd": any(n.startswith("battlemd") and n.endswith(".ini") for n in names),
            "ra2md_ini": "ra2md.ini" in names,
            "ra2_ini": "ra2.ini" in names,
        }

    def ddraw_version(self) -> str | None:
        dll = self.exe("ddraw.dll")
        if not dll.is_file():
            return None
        return read_version_resource(dll)


def sha256_file(path, *, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            block = fh.read(chunk)
            if not block:
                break
            h.update(block)
    return h.hexdigest()


def read_version_resource(path) -> str | None:
    """从 PE 版本资源里取出 FileVersion。

    版本资源是纯 UTF-16 的 `VS_VERSIONINFO`，这里不完整解析整棵资源树，
    只扫描 `FileVersion` 这个键名之后的一小段，找形如 a.b.c.d 的字符串——
    对"判断 wrapper 是哪个版本"这个用途足够可靠。
    """
    try:
        data = Path(path).read_bytes()
    except OSError:
        return None

    patterns = [b"FileVersion", "FileVersion".encode("utf-16-le")]
    for pat in patterns:
        start = 0
        while True:
            idx = data.find(pat, start)
            if idx < 0:
                break
            start = idx + len(pat)
            window = data[idx:idx + 1024]
            for enc in ("utf-16-le", "latin-1"):
                try:
                    text = window.decode(enc, errors="ignore")
                except LookupError:
                    continue
                text = "".join(ch for ch in text if ch.isprintable() or ch in "\r\n")
                m = re.search(r"(\d{1,5}\.\d{1,5}\.\d{1,5}\.\d{1,5})", text)
                if m and enc == "utf-16-le":
                    return m.group(1)
            # UTF-16 命中但没匹配到数字时也继续找下一个
    # 退路：整个文件里找 ASCII 版本号
    m = re.search(rb"(\d{1,5}\.\d{1,5}\.\d{1,5}\.\d{1,5})", data)
    return m.group(1).decode("ascii") if m else None


def version_tuple(version: str | None) -> tuple:
    if not version:
        return ()
    try:
        return tuple(int(x) for x in version.split("."))
    except ValueError:
        return ()


def compare_versions(a: str | None, b: str | None) -> int:
    """返回 -1/0/1；任一为空时返回 0（无法比较）。"""
    ta, tb = version_tuple(a), version_tuple(b)
    if not ta or not tb:
        return 0
    n = max(len(ta), len(tb))
    ta = ta + (0,) * (n - len(ta))
    tb = tb + (0,) * (n - len(tb))
    return (ta > tb) - (ta < tb)

