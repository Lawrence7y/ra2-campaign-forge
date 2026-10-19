"""PE32 头部读写：Large Address Aware 与栈/堆保留空间。

只改 PE 头里的固定字段，不动任何代码字节——这是社区惯用的
"4GB 补丁" 做法，风险可控且完全可逆。

LAA 位在 **COFF File Header**（不是 Optional Header，更不是 DllCharacteristics）::

    e_lfanew+0x00  "PE\0\0"      (4)
    e_lfanew+0x04  COFF File Header
    e_lfanew+0x16    Characteristics (2)   bit 0x20 = IMAGE_FILE_LARGE_ADDRESS_AWARE
    e_lfanew+0x18  Optional Header（相对起点）
    +64  CheckSum            (4)
    +68  Subsystem           (2)
    +70  DllCharacteristics  (2)   bit 0x0020 = IMAGE_DLLCHARACTERISTICS_HIGH_ENTROPY_VA
    +72  SizeOfStackReserve  (4)
    +76  SizeOfStackCommit   (4)
    +80  SizeOfHeapReserve   (4)
    +84  SizeOfHeapCommit    (4)

历史教训（2026-10 复算定案）：旧版把 LAA 写进了 `DllCharacteristics` 的 0x0020，
按 PE 规范那是 HIGH_ENTROPY_VA 而非 LAA；且它要配合 DYNAMIC_BASE(0x0040) 才生效，
老引擎两者皆无，等于写了一个惰性位。官方 gamemd.exe 的 COFF Characteristics 出厂
就是 0x032F（LAA 已置），所以这一笔既非必需、也从没真正动过 LAA。`set_laa` 现在
读写 COFF Characteristics；`DllCharacteristics` 的 0x0020 由独立的
`set_high_entropy_va` 管理，与 LAA 彻底解耦。

说明：

- 用户态 exe 的 CheckSum 被加载器忽略（本目录三个 exe 原本就是 0），改头
  之后也保持 0，不需要重算。
- LAA 只有在 64 位 Windows 上才有意义：32 位系统上用户态地址空间本来就只有
  2GB，翻不了倍。
"""

from __future__ import annotations

import struct
from dataclasses import dataclass, field
from pathlib import Path

PE32_MAGIC = 0x10B
PE32PLUS_MAGIC = 0x20B
DOS_SIGNATURE = b"MZ"
PE_SIGNATURE = b"PE\x00\x00"

# LAA 在 COFF File Header 的 Characteristics 里；0x0020 在 DllCharacteristics 里
# 是另一个含义（HIGH_ENTROPY_VA）——两个常量数值相同、字段不同，绝不可混用。
IMAGE_FILE_LARGE_ADDRESS_AWARE = 0x0020              # COFF Characteristics
IMAGE_DLLCHARACTERISTICS_HIGH_ENTROPY_VA = 0x0020    # DllCharacteristics
IMAGE_DLLCHARACTERISTICS_DYNAMIC_BASE = 0x0040       # DllCharacteristics（ASLR）
IMAGE_DLLCHARACTERISTICS_NX_COMPAT = 0x0100
IMAGE_DLLCHARACTERISTICS_TERMINAL_SERVER_AWARE = 0x8000

MB = 1024 * 1024


class PEError(RuntimeError):
    """PE 文件无法解析或不符合预期布局。"""


@dataclass
class Section:
    name: str
    virtual_address: int
    virtual_size: int
    raw_offset: int
    raw_size: int
    characteristics: int

    @property
    def is_executable(self) -> bool:
        return bool(self.characteristics & 0x20000000)

    @property
    def is_writable(self) -> bool:
        return bool(self.characteristics & 0x80000000)


@dataclass
class PEInfo:
    path: Path
    size: int
    machine: int
    number_of_sections: int
    timestamp: int
    characteristics: int
    is_pe32: bool
    image_base: int
    size_of_image: int
    subsystem: int
    dll_characteristics: int
    stack_reserve: int
    stack_commit: int
    heap_reserve: int
    heap_commit: int
    checksum: int
    entry_point: int
    sections: list[Section] = field(default_factory=list)
    _coff_offset: int = 0
    _opt_offset: int = 0
    _data: bytes = b""

    # -- 派生属性 ---------------------------------------------------------
    @property
    def laa(self) -> bool:
        """是否已标记 Large Address Aware（COFF Characteristics 的 0x0020）。"""
        return bool(self.characteristics & IMAGE_FILE_LARGE_ADDRESS_AWARE)

    @property
    def high_entropy_va(self) -> bool:
        """DllCharacteristics 的 0x0020（HIGH_ENTROPY_VA）。

        注意：这一位要配合 DYNAMIC_BASE（ASLR）才有意义；老引擎两者皆无时
        它是惰性的。它与 LAA 毫无关系，只是数值上同为 0x0020。
        """
        return bool(self.dll_characteristics & IMAGE_DLLCHARACTERISTICS_HIGH_ENTROPY_VA)

    @property
    def dynamic_base(self) -> bool:
        return bool(self.dll_characteristics & IMAGE_DLLCHARACTERISTICS_DYNAMIC_BASE)

    @property
    def nx_compat(self) -> bool:
        return bool(self.dll_characteristics & IMAGE_DLLCHARACTERISTICS_NX_COMPAT)

    @property
    def has_detour_section(self) -> bool:
        """是否带第三方 Detours 补丁段（社区整合版常见，说明 exe 已被改过）。"""
        return any(s.name.lower() == ".detour" for s in self.sections)

    @property
    def writable_executable_sections(self) -> list[str]:
        """同时可写+可执行的段。这类段是 DEP 崩溃与漏洞的常见来源。"""
        return [s.name for s in self.sections if s.is_writable and s.is_executable]

    def field_offset(self, optional_field_offset: int) -> int:
        return self._opt_offset + optional_field_offset

    def coff_field_offset(self, coff_field_offset: int) -> int:
        """COFF File Header 内字段的文件偏移（Characteristics = +18）。"""
        return self._coff_offset + coff_field_offset

    def summary(self) -> dict:
        return {
            "path": str(self.path),
            "size": self.size,
            "is_pe32": self.is_pe32,
            "machine": "%04X" % self.machine,
            "timestamp": self.timestamp,
            "sections": self.number_of_sections,
            "image_base": "%08X" % self.image_base,
            "size_of_image": self.size_of_image,
            "subsystem": self.subsystem,
            "characteristics": "%04X" % self.characteristics,
            "dll_characteristics": "%04X" % self.dll_characteristics,
            "laa": self.laa,
            "high_entropy_va": self.high_entropy_va,
            "dynamic_base": self.dynamic_base,
            "nx_compat": self.nx_compat,
            "has_detour_section": self.has_detour_section,
            "writable_executable_sections": self.writable_executable_sections,
            "stack_reserve": self.stack_reserve,
            "stack_commit": self.stack_commit,
            "heap_reserve": self.heap_reserve,
            "heap_commit": self.heap_commit,
            "checksum": "%08X" % self.checksum,
        }


def read(path) -> PEInfo:
    """解析 PE 头。不加载整个文件（只读头部与段表所需的字节）。"""
    path = Path(path)
    if not path.is_file():
        raise PEError(f"文件不存在：{path}")
    size = path.stat().st_size
    with open(path, "rb") as fh:
        data = fh.read(min(size, 4096))
        if data[:2] != DOS_SIGNATURE:
            raise PEError(f"{path.name}: 缺少 MZ 头，不是 PE 文件")
        if len(data) < 0x40:
            raise PEError(f"{path.name}: DOS 头不完整")
        e_lfanew = struct.unpack_from("<I", data, 0x3C)[0]
        if e_lfanew + 24 > len(data):
            fh.seek(0)
            data = fh.read(e_lfanew + 24 + 240)
        if data[e_lfanew:e_lfanew + 4] != PE_SIGNATURE:
            raise PEError(f"{path.name}: 缺少 PE 签名")

        coff = e_lfanew + 4
        machine, n_sections, timestamp, _symtab, _nsym, opt_size, coff_chars = struct.unpack_from(
            "<HHIIIHH", data, coff
        )
        opt = coff + 20
        if opt + opt_size > len(data):
            raise PEError(f"{path.name}: Optional Header 被截断")
        magic = struct.unpack_from("<H", data, opt)[0]
        is_pe32 = magic == PE32_MAGIC
        if not is_pe32:
            raise PEError(
                f"{path.name}: Optional Header magic={magic:#06x}，本工具只处理 PE32（32 位）"
            )

        image_base = struct.unpack_from("<I", data, opt + 28)[0]
        entry_point = struct.unpack_from("<I", data, opt + 16)[0]
        size_of_image = struct.unpack_from("<I", data, opt + 56)[0]
        checksum = struct.unpack_from("<I", data, opt + 64)[0]
        subsystem = struct.unpack_from("<H", data, opt + 68)[0]
        dll_char = struct.unpack_from("<H", data, opt + 70)[0]
        stack_reserve, stack_commit, heap_reserve, heap_commit = struct.unpack_from(
            "<4I", data, opt + 72
        )

        sections = []
        sec_off = opt + opt_size
        for i in range(n_sections):
            base = sec_off + i * 40
            if base + 40 > len(data):
                break
            name = data[base:base + 8].rstrip(b"\x00").decode("latin-1")
            vsize, va, rsize, raw = struct.unpack_from("<IIII", data, base + 8)
            chars = struct.unpack_from("<I", data, base + 36)[0]
            sections.append(Section(name, va, vsize, raw, rsize, chars))

    return PEInfo(
        path=path,
        size=size,
        machine=machine,
        number_of_sections=n_sections,
        timestamp=timestamp,
        characteristics=coff_chars,
        is_pe32=is_pe32,
        image_base=image_base,
        size_of_image=size_of_image,
        subsystem=subsystem,
        dll_characteristics=dll_char,
        stack_reserve=stack_reserve,
        stack_commit=stack_commit,
        heap_reserve=heap_reserve,
        heap_commit=heap_commit,
        checksum=checksum,
        entry_point=entry_point,
        sections=sections,
        _coff_offset=coff,
        _opt_offset=opt,
        _data=data,
    )


def _patch_u16(path, offset: int, value: int) -> None:
    raw = bytearray(path.read_bytes())
    if offset + 2 > len(raw):
        raise PEError(f"{path.name}: 偏移 {offset:#x} 越界")
    struct.pack_into("<H", raw, offset, value)
    _atomic_write(path, raw)


def _patch_u32(path, offset: int, value: int) -> None:
    raw = bytearray(path.read_bytes())
    if offset + 4 > len(raw):
        raise PEError(f"{path.name}: 偏移 {offset:#x} 越界")
    struct.pack_into("<I", raw, offset, value)
    _atomic_write(path, raw)


def _atomic_write(path, raw: bytearray) -> None:
    """原子替换整个文件。

    `pe` 不知道"游戏目录"是什么，所以**不做沙箱判断**——那是调用方的责任
    （见 `game.GameDir.resolve_exe()`）。这里只留两道防线：拒绝带 `..` 的路径，
    拒绝把目录或不存在的东西当文件写。
    """
    target = Path(path)
    if ".." in target.parts:
        raise PEError(f"拒绝含 .. 的路径：{target}")
    if not target.is_file():
        raise PEError(f"目标不是已存在的普通文件：{target}")
    staging = target.with_name(target.name + ".ra2opt.tmp")
    staging.write_bytes(bytes(raw))
    staging.replace(target)


def set_laa(path, enabled: bool = True) -> bool:
    """设置/清除 Large Address Aware 标记。返回是否有改动。

    LAA 位在 COFF File Header 的 Characteristics（e_lfanew + 0x16），
    不在 DllCharacteristics——后者同数值的 0x0020 是 HIGH_ENTROPY_VA。
    """
    info = read(path)
    if info.laa == bool(enabled):
        return False
    value = info.characteristics | IMAGE_FILE_LARGE_ADDRESS_AWARE if enabled \
        else info.characteristics & ~IMAGE_FILE_LARGE_ADDRESS_AWARE
    _patch_u16(info.path, info.coff_field_offset(18), value)
    return True


def set_high_entropy_va(path, enabled: bool = True) -> bool:
    """设置/清除 DllCharacteristics 的 0x0020（IMAGE_DLLCHARACTERISTICS_HIGH_ENTROPY_VA）。

    这是旧版 `set_laa` 误写的那个位，现予正名并独立出来。注意它**不是 LAA**，
    而且需要 DYNAMIC_BASE(0x0040，ASLR) 配合才生效；gamemd.exe 出厂两个字段
    皆无，置了也是惰性位，因此任何 profile 都不应调用它，仅为完整性与
    "撤销旧版留痕"而保留。
    """
    info = read(path)
    if info.high_entropy_va == bool(enabled):
        return False
    value = info.dll_characteristics | IMAGE_DLLCHARACTERISTICS_HIGH_ENTROPY_VA if enabled \
        else info.dll_characteristics & ~IMAGE_DLLCHARACTERISTICS_HIGH_ENTROPY_VA
    _patch_u16(info.path, info.field_offset(70), value)
    return True


def set_nx_compat(path, enabled: bool = True) -> bool:
    """设置 IMAGE_DLLCHARACTERISTICS_NX_COMPAT（声明兼容 DEP）。

    老游戏默认不声明，于是系统只能用"仅关键 Windows 服务"的 DEP 策略兜底；
    声明之后配合 SystemDepPolicy 可以更干净地共存。默认不开——见 docs。
    """
    info = read(path)
    has = info.nx_compat
    if has == bool(enabled):
        return False
    value = info.dll_characteristics | IMAGE_DLLCHARACTERISTICS_NX_COMPAT if enabled \
        else info.dll_characteristics & ~IMAGE_DLLCHARACTERISTICS_NX_COMPAT
    _patch_u16(info.path, info.field_offset(70), value)
    return True


def set_stack_reserve(path, megabytes: int) -> bool:
    """调整主线程栈保留空间（SizeOfStackReserve）。

    MSVC6 默认 1MB。引擎的寻路/AI 递归在大地图 + 大量单位时会吃栈，
    栈溢出表现为"毫无征兆的闪退"。改成 2–4MB 只多占地址空间（提交仍是按需），
    不会改变任何指针运算，属于低风险高收益的一档。
    """
    info = read(path)
    new = megabytes * MB
    if info.stack_reserve == new:
        return False
    _patch_u32(info.path, info.field_offset(72), new)
    return True


def set_heap_reserve(path, megabytes: int) -> bool:
    """调整堆保留空间（SizeOfHeapReserve）。默认 1MB，显式堆申请会被限制在这个数。"""
    info = read(path)
    new = megabytes * MB
    if info.heap_reserve == new:
        return False
    _patch_u32(info.path, info.field_offset(80), new)
    return True


def is_64bit_host() -> bool:
    """宿主是否为 64 位 Windows（决定 LAA 是否有意义）。"""
    import os

    if os.environ.get("PROCESSOR_ARCHITEW6432"):
        return True
    return os.environ.get("PROCESSOR_ARCHITECTURE", "").upper() in ("AMD64", "ARM64")


def text_section_sha256(path) -> str | None:
    """`.text` 段（代码段）的 SHA-256。

    用它当引擎指纹：LAA / 栈 / 堆这些优化都只改 Optional Header，代码段字节
    不变，所以打完补丁之后依然能认出"这是哪个版本的 gamemd.exe"，
    而整文件 SHA-256 会被自己的补丁改掉。
    """
    import hashlib

    info = read(path)
    target = next((s for s in info.sections if s.name.lower() == ".text"), None)
    if target is None:
        return None
    with open(info.path, "rb") as fh:
        fh.seek(target.raw_offset)
        block = fh.read(target.raw_size)
    return hashlib.sha256(block).hexdigest()

