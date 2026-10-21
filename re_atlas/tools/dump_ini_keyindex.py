"""R-019: build the engine-wide key -> read-site index.

`AbstractTypeClass::LoadFromINI` only reads two keys, so the interesting part of
the INI surface is everywhere else. Every place the engine reads an INI value by
key funnels through a small set of readers; this tool walks each call site and
recovers the key literal pushed immediately before it.

Why this matters for a campaign compiler: it answers "is this key read at all,
and by which function" without guessing. A key with no read site here is dead
config as far as these readers go; a key with several sites is read by several
distinct loaders.

The window trap this tool is written against: starting the backward scan at an
arbitrary byte offset will happily decode mid-instruction bytes as a `push imm`
and invent keys. Every candidate is therefore checked against two filters --
the pushed value must land inside the string region AND decode to printable
ASCII of length >= 2 -- and the tool prints how many sites yielded no key at
all, so "found nothing" is distinguishable from "predicate is broken".

Run: python re_atlas/tools/dump_ini_keyindex.py
"""

import os
import struct
import sys

import capstone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from text_sweep import sweep  # noqa: E402  audited full-.text sweep

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
IMAGE_BASE = 0x400000
TEXT_LO, TEXT_HI = 0x401000, 0x7E1000
RDATA_LO, RDATA_HI = 0x7E1000, 0x811074
DATA_LO, DATA_HI = 0x812000, 0xB79BE4
TEXT_RAW = (0x1000, 0x3E0000)

with open(EXE, "rb") as fh:
    BLOB = fh.read()


# Backed sections, as (name, rva, vsize, rawptr, rawsize). Only these three map
# by VA - 0x400000; .rsrc/.detour use a different delta and BSS has no bytes.
SECTIONS = [
    (".text", 0x001000, 0x3DF38D, 0x001000, 0x3E0000),
    (".rdata", 0x3E1000, 0x030074, 0x3E1000, 0x031000),
    (".data", 0x412000, 0x367BE4, 0x412000, 0x06C000),
]


def read_va(va, n):
    """Read n bytes at VA, but ONLY when the address is disk-backed.

    A bare `fo = va - 0x400000` is wrong in a way that fails silently: the file
    is longer than .data's raw backing, so a BSS address such as 0x885780 maps to
    file offset 0x485780, which is inside the file, and the call returns .detour
    bytes as if they were data (it produced a fake section name "ostMessageA").
    Bounds are checked per section; BSS (past raw_size) returns b"".
    """
    rva = va - IMAGE_BASE
    for _name, s_rva, s_vsize, raw_ptr, raw_size in SECTIONS:
        if s_rva <= rva < s_rva + max(s_vsize, raw_size):
            d = rva - s_rva
            if d >= raw_size:
                return b""
            return BLOB[raw_ptr + d: raw_ptr + d + n]
    return b""


def cstr(va, n=64):
    b = read_va(va, n)
    if not b:
        return ""
    z = b.find(b"\x00")
    return (b[:z] if z >= 0 else b).decode("ascii", "replace")


# The reader entry points this index covers, with the argument layout after
# `this`: (section, key, ...) for the readers, so the key literal is pushed
# immediately before the call for all of them.
READERS = {
    0x00528A10: ("ReadString", "ret 0x14, 参数 (section, key, dst, cap)"),
    0x00528F00: ("ReadUnicodeString", "ret 0x14"),
    0x00529160: ("ReadStringtableEntry", "ret 0x10"),
    0x005283D0: ("ReadDouble", "ret 0x14"),
    0x005276D0: ("ReadInteger", "ret 0xC, 参数 (section, key, default)"),
    0x005295F0: ("ReadBool", "ret 0xC"),
    0x00526810: ("GetSection", "ret 4, 参数 (name)"),
}


# Filled by call_sites(): for each target VA, the call sites and, for each, the
# address of the enclosing function's first instruction.
_CALL_INDEX = {}
_FUNC_OF = {}


def e8_scan():
    """Every `call rel32` to a READER, found by scanning bytes for 0xE8.

    This is the independent baseline for the positive control: it decodes
    nothing, so it cannot inherit the disassembler's stop points. A false
    positive would need an immediate or data byte equal to E8 whose following
    four bytes happen to encode a displacement landing exactly on a reader --
    possible in principle, which is why the control compares the two sets rather
    than trusting either alone.
    """
    lo, size = TEXT_RAW
    raw = BLOB[lo:lo + size]
    out = set()
    i = 0
    while True:
        j = raw.find(b"\xe8", i)
        if j < 0 or j + 5 > len(raw):
            break
        va = TEXT_LO + j
        rel = struct.unpack_from("<i", raw, j + 1)[0]
        if ((va + 5 + rel) & 0xFFFFFFFF) in READERS:
            out.add(va)
        i = j + 1
    return out


def call_sites():
    """One linear pass over .text from its true start, recording call sites.

    The pass starts at TEXT_LO, which is a real instruction boundary, so every
    address it reports is one too. It simultaneously tracks the start of the
    current function (first non-nop byte after a `ret`), giving each call site a
    decoding origin that is guaranteed aligned. Deriving that origin by walking
    backwards from the call does NOT work: the window edge is an arbitrary byte
    and capstone will happily decode garbage there ("les edx, ptr [...]"),
    which is how the first version of this tool lost 42 of 477 sites.
    """
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = True
    out = []
    func_start = TEXT_LO
    pending_ret = False
    # SWEEP, not a single disasm: `md.disasm(.text)` stops at 0x46F5A0 on this
    # image (a jump table inside .text) and silently leaves 89% of the section
    # unscanned. The first version of this tool used the single pass and
    # reported 473 key sites; the audited sweep finds far more. See
    # text_sweep.py for why, and for the resync audit trail.
    for insn in sweep(TEXT_LO, 0x7E1000):
        if pending_ret and insn.mnemonic != "nop":
            func_start = insn.address
            pending_ret = False
        if insn.mnemonic.startswith("ret"):
            pending_ret = True
        elif insn.mnemonic != "nop":
            pending_ret = False
        if insn.mnemonic != "call" or not insn.operands:
            continue
        op = insn.operands[0]
        if op.type != capstone.x86.X86_OP_IMM:
            continue
        t = op.imm & 0xFFFFFFFF
        if t in READERS:
            out.append((insn.address, t))
            _FUNC_OF[insn.address] = func_start
            _CALL_INDEX.setdefault(t, []).append(insn.address)
    return out


def function_start(call_va):
    """The enclosing function's first instruction, from the single linear pass."""
    return _FUNC_OF.get(call_va, TEXT_LO)


def function_start_unused(call_va, walk=0x1000):
    """Deprecated: backward-window origin. Kept only as a note, never called.

    Walking backwards from a call to a fixed offset yields an arbitrary byte,
    not an instruction boundary; see call_sites() for the linear-pass version.
    """
    raise NotImplementedError


def pushes_before(call_va):
    """All pushes from the enclosing prologue up to `call_va`, in order.

    Each entry is (site, kind, value): kind is "imm" for an immediate, "other"
    for a register/memory push. Decoding starts at the prologue so no operand is
    read out of the middle of an instruction.
    """
    origin = function_start(call_va)
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    out = []
    for insn in md.disasm(read_va(origin, call_va - origin), origin):
        if insn.address >= call_va:
            break
        if insn.mnemonic != "push":
            continue
        txt = insn.op_str.strip()
        if txt.startswith("0x") and "[" not in txt:
            out.append((insn.address, "imm", int(txt, 16)))
        else:
            out.append((insn.address, "other", txt))
    return out


def key_before(call_va):
    """Nearest string-literal push before a call, or None.

    Scans forward from the enclosing prologue; only accepts a push whose operand
    is an immediate landing in the string region and decoding to printable
    ASCII. Returns (site, value, text) for the last such push before the call.
    """
    found = None
    for site, kind, val in pushes_before(call_va):
        if kind != "imm":
            continue
        if not (RDATA_LO <= val < DATA_HI):
            continue
        s = cstr(val)
        # printable-ASCII filter: rejects pushes of floats / colours / pointers
        # that happen to live in .data and decode to control bytes.
        if len(s) < 2 or not all(0x20 < ord(ch) < 0x7F for ch in s):
            continue
        found = (site, val, s)
    return found


def classify_indirect(call_va):
    """Why no literal key was found: 'register' or 'bss_key'."""
    pushes = pushes_before(call_va)
    for site, kind, val in pushes:
        if kind == "imm" and 0x87E000 <= val < 0xB79BE4:
            return "bss_key"
    for site, kind, val in pushes:
        if kind == "other" and val not in ("ebp", "ebx", "esi", "edi"):
            return "register"
    return "unknown"


def main():
    sites = call_sites()
    print(f"=== call sites per reader ===")
    per = {}
    for _, t in sites:
        per[t] = per.get(t, 0) + 1
    for t, (name, note) in sorted(READERS.items()):
        print(f"  0x{t:08X}  {name:22s} {per.get(t, 0):4d} 处   {note}")

    rows = []
    no_key = []
    for call_va, t in sites:
        k = key_before(call_va)
        fn = function_start(call_va)
        if k is None:
            no_key.append((call_va, READERS[t][0], classify_indirect(call_va)))
            continue
        rows.append((k[2], READERS[t][0], fn, call_va, k[1]))

    print(f"\n=== 恢复到的 键 -> 读取点 ({len(rows)}) ===")
    print(f"    未能恢复字面量键的调用点: {len(no_key)}")
    if no_key:
        kinds = {}
        for _, _, kind in no_key:
            kinds[kind] = kinds.get(kind, 0) + 1
        print(f"    其中: {kinds}")
        print("    （register/bss_key 是真正经寄存器或 BSS 字符串传键，不是工具缺陷；")
        print("      unknown 才说明窗口或判据有问题）")
        for call_va, reader, kind in no_key[:12]:
            print(f"      0x{call_va:08X}  {reader:22s} {kind}")

    by_key = {}
    for key, reader, fn, call_va, kva in rows:
        by_key.setdefault(key, []).append((reader, fn, call_va, kva))

    for key in sorted(by_key, key=lambda s: (-len(by_key[s]), s)):
        hits = by_key[key]
        print(f"\n  {key!r}  ({len(hits)} 处)")
        for reader, fn, call_va, kva in hits:
            print(f"     {reader:22s} 调用 0x{call_va:08X}  键字面量 0x{kva:08X}  所在函数 ~0x{fn:08X}")

    print("\n=== 汇总 ===")
    print(f"  不同键: {len(by_key)}")
    print(f"  读取点总数: {len(rows)}")
    multi = [k for k in by_key if len(by_key[k]) > 1]
    print(f"  被多处读取的键: {len(multi)} -> {sorted(multi)}")

    print("\n=== 正对照 ===")
    ok = True

    # Independent baseline: a raw E8-rel32 byte scan finds every call to these
    # readers without decoding a single instruction, so it cannot be affected by
    # the decoder's own stop points. The swept set must equal it EXACTLY, not
    # approximately. R-023's first attempt compared against the single-pass set
    # and "passed" only because both sides were truncated the same way.
    scan = e8_scan()
    swept = {site for _tgt, sites in _CALL_INDEX.items() for site in sites}
    if swept != scan:
        print(f"  !! E8 扫描 {len(scan)} 处，指令扫描 {len(swept)} 处，"
              f"差集 {len(scan - swept)}/{len(swept - scan)}")
        ok = False
    else:
        print(f"  E8 字节扫描 {len(scan)} 处 == 指令扫描 {len(swept)} 处（零差异）")

    # Name/UIName: the old "exactly 1" expectation was calibrated against the
    # TRUNCATED index, so it had encoded the bug as the correct answer. The real
    # requirement is that LoadFromINI (0x410A60) is among the readers -- other
    # loaders read the same key too and must not be suppressed.
    for key in ("Name", "UIName"):
        hits = by_key.get(key, [])
        near = [h for h in hits if abs(h[1] - 0x00410A60) < 0x180]
        good = bool(near)
        print(f"  {key!r}: {len(hits)} 处，其中 {len(near)} 处属 "
              f"LoadFromINI(0x00410A60) -> {good}")
        ok = ok and good
    ctl = cstr(0x00817854)
    print(f"  字面量 0x00817854 = {ctl!r} 期望 'Name' -> {ctl == 'Name'}")
    ok = ok and ctl == "Name"

    # Coverage: the single pass stopped at 0x46F5A0 and still reported 473.
    if len(scan) < 2000:
        print(f"  !! 只有 {len(scan)} 处调用点，与已知量级不符")
        ok = False
    if not ok:
        print("  !! 正对照失败 —— 索引不可信")
        return 1
    print("  正对照通过（E8 与指令扫描逐址相等 / LoadFromINI 在册 / 调用点≥2000）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
