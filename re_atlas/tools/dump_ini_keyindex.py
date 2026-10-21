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

import struct

import capstone

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
IMAGE_BASE = 0x400000
TEXT_LO, TEXT_HI = 0x401000, 0x7E1000
RDATA_LO, RDATA_HI = 0x7E1000, 0x811074
DATA_LO, DATA_HI = 0x812000, 0xB79BE4
TEXT_RAW = (0x1000, 0x3E0000)

with open(EXE, "rb") as fh:
    BLOB = fh.read()


def read_va(va, n):
    fo = va - IMAGE_BASE
    if fo < 0 or fo >= len(BLOB):
        return b""
    return BLOB[fo:fo + n]


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
    lo, size = TEXT_RAW
    out = []
    func_start = TEXT_LO
    pending_ret = False
    for insn in md.disasm(BLOB[lo:lo + size], TEXT_LO):
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
    # Name/UIName must appear exactly once each, from LoadFromINI (0x410A60).
    ok = True
    for key in ("Name", "UIName"):
        hits = by_key.get(key, [])
        good = len(hits) == 1 and abs(hits[0][1] - 0x00410A60) < 0x180
        print(f"  {key!r}: {len(hits)} 处, 所在函数 ~0x{hits[0][1]:08X} 期望 0x00410A60 -> {good}")
        ok = ok and good
    ctl = cstr(0x00817854)
    print(f"  字面量 0x00817854 = {ctl!r} 期望 'Name' -> {ctl == 'Name'}")
    ok = ok and ctl == "Name"
    if not ok:
        print("  !! 正对照失败 —— 索引不可信")
        return 1
    print("  正对照通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
