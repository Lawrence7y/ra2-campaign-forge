"""INI 读写：保留注释/顺序/大小写与原始编码，只改动指定键。

不用 `configparser`，因为它会丢掉注释和键名大小写，而 RA2 的 ra2md.ini 是
玩家与配置器共同维护的文件，重排一次就会让用户看不懂自己的配置。

编码：中文版游戏的 INI 是系统 ANSI（GBK）。这里按 utf-8-sig → gbk → latin-1
顺序探测，写回时沿用探测结果，避免把中文注释变成乱码。

写盘统一走 `safewrite`，只允许改写游戏目录的直属既有文件。
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path

from . import safewrite

_ENCODINGS = ("gbk", "utf-8", "latin-1")
_SECTION_RE = re.compile(r"^\s*\[([^\]]+)\]\s*$")
_KEY_RE = re.compile(r"^(\s*)([^=;\s][^=]*?)(\s*)=(.*)$")
BOM_UTF8 = b"\xef\xbb\xbf"


def detect_encoding(data: bytes) -> str:
    """探测编码。**不**返回 utf-8-sig —— 见 `has_bom()`。

    纯 ASCII 文件用 `utf-8` 和 `utf-8-sig` 都能解码，但用 `utf-8-sig` 编码回去时
    Python 会**加上一个 BOM**。RA2 的 INI 原本没有 BOM，凭空加一段字节会让游戏的
    INI 解析器把第一节的 `[Section]` 当成 `\\xEF\\xBB\\xBF[Section]` 而整节失效。
    所以这里只认「UTF-8（不带 BOM）」，BOM 的有无由调用方单独记录并原样保留。
    """
    for enc in _ENCODINGS:
        try:
            data.decode(enc)
        except (UnicodeDecodeError, LookupError):
            continue
        return enc
    return "latin-1"


def has_bom(data: bytes) -> bool:
    return data.startswith(BOM_UTF8)


@dataclass
class IniLine:
    raw: str
    section: str | None = None
    key: str | None = None


@dataclass
class IniFile:
    """行级保留的 INI 文档。`name` 是相对游戏目录的文件名。"""

    name: str | None
    base_dir: Path | None = None
    lines: list[IniLine] = field(default_factory=list)
    encoding: str = "gbk"
    newline: str = "\r\n"
    original: str = ""
    bom: bool = False

    # -- 构造 -------------------------------------------------------------
    @classmethod
    def load(cls, base_dir, name) -> "IniFile":
        """从 base_dir/name 读取（沙箱内读取，拒绝越界）。"""
        base = Path(os.path.realpath(str(base_dir)))
        raw = safewrite.read_bytes(base, name)
        bom = has_bom(raw)
        body = raw[len(BOM_UTF8):] if bom else raw
        # 只在去掉 BOM 之后的字节上探测编码：否则 BOM 会作为 \ufeff 混进第一行，
        # 让 `^\s*\[` 匹配不上首个节头，整节设置被归到"无节"里丢失。
        encoding = detect_encoding(body)
        newline = "\r\n" if b"\r\n" in body else "\n"
        obj = cls.parse(
            body.decode(encoding),
            name=Path(os.fspath(name)).name,
            base_dir=base,
            encoding=encoding,
            newline=newline,
            bom=bom,
        )
        return obj

    @classmethod
    def parse(cls, text: str, *, name=None, base_dir=None, encoding="utf-8",
              newline="\r\n", bom: bool = False) -> "IniFile":
        """从字符串解析。`text` 里 CRLF/LF 混用都能处理，输出统一用 newline。"""
        if text.startswith("\ufeff"):
            text = text[1:]
            bom = True
        normalized = text.replace("\r\n", "\n").replace("\r", "\n")
        obj = cls(name=name, base_dir=base_dir, encoding=encoding, newline=newline,
                  # original 必须与 text() 的可比形态一致（同一种换行），
                  # 否则 is_modified() 会永远为真
                  original=newline.join(normalized.split("\n")), bom=bom)
        current: str | None = None
        for raw_line in normalized.split("\n"):
            m = _SECTION_RE.match(raw_line)
            if m:
                current = m.group(1).strip()
                obj.lines.append(IniLine(raw_line, section=current))
                continue
            if raw_line.lstrip().startswith((";", "#")):
                obj.lines.append(IniLine(raw_line, section=current))
                continue
            km = _KEY_RE.match(raw_line)
            if km:
                obj.lines.append(IniLine(raw_line, section=current, key=km.group(2).strip()))
            else:
                obj.lines.append(IniLine(raw_line, section=current))
        return obj

    # -- 读值 -------------------------------------------------------------
    def has_section(self, section: str) -> bool:
        return any((li.section or "").lower() == section.lower() for li in self.lines)

    def get(self, section: str, key: str, default=None):
        want_s, want_k = section.lower(), key.lower()
        for li in self.lines:
            if (li.section or "").lower() == want_s and (li.key or "").lower() == want_k:
                return _KEY_RE.match(li.raw).group(4).strip()
        return default

    def get_int(self, section: str, key: str, default=None):
        raw = self.get(section, key)
        if raw is None:
            return default
        try:
            return int(str(raw).strip())
        except ValueError:
            return default

    def keys(self, section: str) -> dict:
        out = {}
        for li in self.lines:
            if (li.section or "").lower() == section.lower() and li.key:
                out[li.key] = _KEY_RE.match(li.raw).group(4).strip()
        return out

    def sections(self) -> list:
        seen, out = set(), []
        for li in self.lines:
            if li.section and li.section.lower() not in seen:
                seen.add(li.section.lower())
                out.append(li.section)
        return out

    # -- 写值 -------------------------------------------------------------
    def set(self, section: str, key: str, value) -> bool:
        """设置键值。已存在则原地改值（保留缩进与 `=` 两侧的空白风格），否则插入。"""
        value = str(value)
        want_s, want_k = section.lower(), key.lower()
        for li in self.lines:
            if (li.section or "").lower() == want_s and (li.key or "").lower() == want_k:
                m = _KEY_RE.match(li.raw)
                indent, name, pre_eq, body = m.groups()
                post_eq = body[:len(body) - len(body.lstrip())]  # `= 2` 里那个空格
                new_raw = f"{indent}{name}{pre_eq}={post_eq}{value}"
                if new_raw == li.raw:
                    return False
                li.raw = new_raw
                return True
        insert_at = None
        for idx, li in enumerate(self.lines):
            if (li.section or "").lower() == want_s:
                insert_at = idx + 1
        if insert_at is None:
            if self.lines and self.lines[-1].raw.strip():
                self.lines.append(IniLine(""))
            self.lines.append(IniLine(f"[{section}]", section=section))
            self.lines.append(IniLine(f"{key}={value}", section=section, key=key))
        else:
            self.lines.insert(insert_at, IniLine(f"{key}={value}", section=section, key=key))
        return True

    def set_many(self, section: str, pairs: dict) -> list:
        """批量设置，返回真正发生变化的 `Section.Key` 列表。"""
        changed = []
        for key, value in pairs.items():
            if self.set(section, key, value):
                changed.append(f"{section}.{key}")
        return changed

    # -- 输出 -------------------------------------------------------------
    def text(self) -> str:
        return self.newline.join(li.raw for li in self.lines)

    def is_modified(self) -> bool:
        return self.text() != self.original

    def save(self) -> bool:
        """写回原文件。返回是否有内容变化。

        BOM 原样保留：原本有就写回 BOM，原本没有就一个字节也不加。
        """
        if self.name is None or self.base_dir is None:
            raise ValueError("IniFile 未绑定转换目标，无法保存")
        if not self.is_modified():
            return False
        payload = self.text().encode(self.encoding, errors="replace")
        if self.bom:
            payload = BOM_UTF8 + payload
        safewrite.write_bytes(self.base_dir, self.name, payload)
        return True
