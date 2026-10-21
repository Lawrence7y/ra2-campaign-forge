"""R-021: recover the RulesClass section table and its load order.

The campaign compiler needs two things this provides:

  1. which INI section is consumed by which loader, and
  2. what order the loaders run in (later loaders can overwrite earlier ones).

Both are read straight out of the image rather than from YRpp:

  - the section names live in a pointer table at 0x007F0C78, 4 bytes per entry,
    each dword being a `const char*` into .data;
  - each `Read_*` member loads its section name through one of those globals and
    then calls GetSection, so the function -> section mapping is recovered from
    the code, not assumed from the function name;
  - the order comes from the call sequence inside RulesClass::Init (0x006686C0).

The trap this tool is written around: capstone renders a memory-source mov as
'reg, dword ptr [0xADDR]' -- the address is AFTER the comma. R-021's first
attempt matched `op_str.startswith("dword ptr [")` and therefore found 0 of 37
functions. Every global is now extracted with a regex anywhere in op_str, and the
tool prints how many functions yielded a section so "found nothing" cannot be
mistaken for "fine".

Run: python re_atlas/tools/dump_rules_sections.py
"""

import re
import struct

import capstone

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
IMAGE_BASE = 0x400000
TEXT_LO, TEXT_HI = 0x401000, 0x7E1000
DATA_LO, DATA_HI = 0x812000, 0xB79BE4

SECTION_TABLE = 0x007F0C78
SECTION_TABLE_END = 0x007F0CF8
INIT = 0x006686C0

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

    The naive `fo = va - 0x400000; BLOB[fo:fo+n]` is wrong in a way that is
    silent: the file is longer than .data's backing, so a BSS address such as
    0x885780 turns into file offset 0x485780, which is inside the file, and the
    call returns .detour bytes as if they were data. That produced a bogus
    "section name" `ostMessageA` out of what is actually a Win32 import string.
    Bounds are therefore checked per section, and BSS returns b"".
    """
    rva = va - IMAGE_BASE
    for _name, s_rva, s_vsize, raw_ptr, raw_size in SECTIONS:
        if s_rva <= rva < s_rva + max(s_vsize, raw_size):
            d = rva - s_rva
            if d >= raw_size:
                return b""          # past the raw backing: BSS / zero-fill
            return BLOB[raw_ptr + d: raw_ptr + d + n]
    return b""


def u32(va):
    b = read_va(va, 4)
    return struct.unpack("<I", b)[0] if len(b) == 4 else None


def cstr(va, n=64):
    if not va:
        return ""
    b = read_va(va, n)
    if not b:
        return ""
    z = b.find(b"\x00")
    return (b[:z] if z >= 0 else b).decode("ascii", "replace")


# RulesClass::Read_* entry points, from YRpp's JMP_THIS addresses.
READERS = {
    0x00668BF0: "Read_File",
    0x00668FB0: "Read_SpecialWeapons",
    0x006691E0: "Read_AudioVisual",
    0x0066B900: "Read_CrateRules",
    0x0066BBB0: "Read_CombatDamage",
    0x0066CF70: "Read_Radiation",
    0x0066D150: "Read_ElevationModel",
    0x0066D1F0: "Read_WallModel",
    0x0066D270: "Read_Difficulty",
    0x0066D3A0: "Read_Colors",
    0x0066D480: "Read_ColorAdd",
    0x0066D530: "Read_General",
    0x00671EA0: "Read_MultiplayerDialogSettings",
    0x00672230: "Read_Maximums",
    0x00672280: "Read_InfantryTypes",
    0x006722F0: "Read_Countries",
    0x00672360: "Read_VehicleTypes",
    0x006723D0: "Read_AircraftTypes",
    0x00672440: "Read_Sides",
    0x006725F0: "Read_SuperWeaponTypes",
    0x00672660: "Read_BuildingTypes",
    0x006726D0: "Read_TerrainTypes",
    0x00672740: "Read_Teams_obsolete",
    0x006727D0: "Read_SmudgeTypes",
    0x00672840: "Read_OverlayTypes",
    0x006728B0: "Read_Animations",
    0x00672920: "Read_VoxelAnims",
    0x00672990: "Read_Warheads",
    0x00672A00: "Read_Particles",
    0x00672A70: "Read_ParticleSystems",
    0x00672AE0: "Read_AI",
    0x00673E80: "Read_Powerups",
    0x00674000: "Read_LandCharacteristics",
    0x00674240: "Read_IQ",
    0x006743D0: "Read_JumpjetControls",
    0x00674500: "Read_Difficulties",
    0x00674550: "Read_Movies",
    0x00674650: "Read_AdvancedCommandBar",
}

MEM_PTR = re.compile(r"dword ptr \[(0x[0-9a-f]+)\]")


def section_table():
    """The pointer table at 0x7F0C78: list of (global VA, section name)."""
    out = []
    for g in range(SECTION_TABLE, SECTION_TABLE_END, 4):
        p = u32(g)
        out.append((g, cstr(p)))
    return out


def is_string(va, min_len=2):
    """True when the bytes at va look like a printable C string.

    min_len is 2, not 3: real section names in this table include "AI" and
    "IQ", both two characters. A min_len of 3 silently dropped both and the
    scanner then reported "no section found" for Read_AI and Read_IQ.
    """
    s = cstr(va)
    return bool(s) and len(s) >= min_len and all(0x20 < ord(ch) < 0x7F for ch in s)


def resolve_section_operand(va):
    """Resolve an operand address to a section name, following at most one indirection.

    Three storage shapes occur, and the first string pushed is NOT always the
    section name -- it is often a KEY name:

      direct    : `push 0x83D0DC`                  -> "Animations" at that address
      ptr-table : `mov eax,[0x7F0C94]`             -> slot holds a `const char*`
      table-base: `mov esi,0x839D68; mov eax,[esi]`-> 0x839D68 is an ARRAY of
                  `const char*`; read the first dword and follow it

    An earlier version returned the first printable string it saw, which made
    Read_Difficulty come back as "FirePower" and Read_LandCharacteristics as
    "Hover" -- both are KEYS, not section names.
    """
    if not (0x7E1000 <= va < 0xB79BE4):
        return None
    if is_string(va):
        return cstr(va)
    p = u32(va)
    if p and is_string(p):
        return cstr(p)
    return None


def section_used_by(fn_va, window=0x1200):
    """Recover the section name a Read_* function works on.

    There are two distinct shapes and the tool must handle both:

      A) the reader itself resolves the section: it either loads a
         section-name global (`mov eax,[0x7F0C94]`) or pushes the literal
         string address, then calls GetSection (0x526810) -- or, for the
         list readers, GetKeyCount (0x526960), because the section was already
         parsed by Read_File and this reader only enumerates its keys.

      B) the reader takes the section name as a PARAMETER and never references
         a section string at all. Read_Difficulty is this shape: the section
         arrives in edx and goes straight into GetSection. Nothing can be
         recovered from the body, so returning None is the honest answer.

    What went wrong before: anchoring only on GetSection missed every list
    reader (shape A via GetKeyCount) and every literal-pushed section; adding a
    whitelist then made the scanner fall back to neighbouring strings. Both are
    gone. The GetSection/GetKeyCount calls are the anchor and the LAST string
    operand before that call is the answer.
    """
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = True

    insns = []
    for insn in md.disasm(read_va(fn_va, window), fn_va):
        insns.append(insn)
        if insn.mnemonic.startswith("ret"):
            break

    anchors = {0x00526810, 0x00526960}   # GetSection, GetKeyCount
    for idx, insn in enumerate(insns):
        if insn.mnemonic != "call" or not insn.operands:
            continue
        op = insn.operands[0]
        if op.type != capstone.x86.X86_OP_IMM or (op.imm & 0xFFFFFFFF) not in anchors:
            continue
        # Walk back over this call's argument setup. The section is the operand
        # whose resolved string is NOT a bare key-looking token when a table
        # member is available; in practice the last resolvable string wins.
        best = None
        for prior in insns[:idx]:
            cand = operand_string(prior)
            if cand:
                best = cand
        if best:
            return best
    # Shape 2: no GetSection/GetKeyCount call (the section arrives as a
    # parameter). Read_Difficulty is this shape -- the section string is in edx
    # and goes straight into GetSection -- so nothing is recoverable from the
    # body and None is the honest answer.
    return None, None, None


def operand_string(insn):
    """(site, name, shape) if this instruction references a printable string."""
    if insn.mnemonic == "push":
        txt = insn.op_str.strip()
        if txt.startswith("0x") and "[" not in txt:
            v = int(txt, 16)
            s = resolve_section_operand(v)
            if s:
                return v, s, "direct"
            return None
    m = MEM_PTR.search(insn.op_str)
    if m:
        v = int(m.group(1), 16)
        s = resolve_section_operand(v)
        if s:
            return v, s, "indirect"
    if insn.mnemonic == "mov":
        txt = insn.op_str.strip()
        if "," in txt:
            src = txt.split(",", 1)[1].strip()
            if src.startswith("0x") and "[" not in src:
                v = int(src, 16)
                s = resolve_section_operand(v)
                if s:
                    return v, s, "table-base"
    return None


def fn_calls(lo, hi):
    """Call targets inside an explicit address range, in program order.

    An explicit [lo,hi) rather than a "window size" is the whole point here.
    RulesClass::Init (0x6686C0-0x668BE5) and Read_File (0x668BF0-0x668F8D) are
    adjacent in the image, so any oversized window silently sweeps the next
    function's calls into the report. The first version used a 0x1600 window
    from Init and attributed Read_File's 28 loaders to Init.
    """
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = True
    out = []
    for insn in md.disasm(read_va(lo, hi - lo), lo):
        if insn.mnemonic != "call" or not insn.operands:
            continue
        op = insn.operands[0]
        if op.type != capstone.x86.X86_OP_IMM:
            continue
        out.append((insn.address, op.imm & 0xFFFFFFFF))
    return out


# True extents, found by scanning each function to its first `ret`.
INIT_RANGE = (0x006686C0, 0x00668BE6)
READ_FILE_RANGE = (0x00668BF0, 0x00668F8E)


# Read_File is itself listed in READERS but it is a CONTAINER: it calls the other
# loaders. Counting it as a leaf loader makes "Init calls Read_File three times"
# look like "Init directly calls three loaders", which is what the first version
# of the boundary control wrongly flagged.
CONTAINERS = {0x00668BF0}   # Read_File


def loader_sequence(lo, hi, include_containers=False):
    """The loader calls inside a range, in program order."""
    out = []
    for site, target in fn_calls(lo, hi):
        if target not in READERS:
            continue
        if target in CONTAINERS and not include_containers:
            continue
        out.append((site, READERS[target]))
    return out


def main():
    print("=== 节名指针表 0x007F0C78（4 字节一项，指向 .data 的 C 字符串）===")
    table = section_table()
    for g, s in table:
        print(f"  0x{g:08X} -> {s!r}")
    named = sum(1 for _, s in table if s)
    print(f"  非空项 {named} / {len(table)}")

    print("\n=== 函数 -> 节名（从代码里读，不按函数名猜）===")
    mapping = {}
    missing = []
    for va, name in sorted(READERS.items()):
        g, s, how = section_used_by(va)
        if s is None:
            missing.append(name)
            print(f"  0x{va:08X}  {name:34s} （未找到节名）")
        else:
            mapping[name] = s
            print(f"  0x{va:08X}  {name:34s} 0x{g:08X}  {s!r}  [{how}]")
    print(f"  解析成功 {len(mapping)} / {len(READERS)}")

    print("\n=== RulesClass::Init (0x6686C0-0x668BE5) 的 Read_* 调用 ===")
    init_seq = loader_sequence(*INIT_RANGE)
    if init_seq:
        for site, label in init_seq:
            print(f"  0x{site:08X} -> {label}")
    else:
        print("  （Init 不直接调用任何 Read_*；它只调 Read_File）")
    init_raw = fn_calls(*INIT_RANGE)
    n_rf = sum(1 for _, t in init_raw if t == 0x00668BF0)
    print(f"  Init 内 call Read_File 次数: {n_rf}  （期望 3：第一份 / gamemode / map）")

    print("\n=== Read_File (0x668BF0-0x668F8D) 内的 Read_* 顺序（后读覆盖先读）===")
    rf_seq = loader_sequence(*READ_FILE_RANGE)
    for i, (site, label) in enumerate(rf_seq, 1):
        print(f"  {i:2d}. 0x{site:08X} {label}")
    print(f"  合计 {len(rf_seq)} 个 loader 调用")

    print("\n=== 与节名表交叉核对 ===")
    # Every section the code reads should be a member of the pointer table.
    table_names = {s for _, s in table if s}
    unknown = sorted(set(mapping.values()) - table_names)
    print(f"  代码读到的节名都在指针表里: {not unknown}"
          + ("" if not unknown else f"  例外: {unknown}"))
    unused = sorted(table_names - set(mapping.values()))
    print(f"  指针表里存在但没有 Read_ 函数把它当首节名的项: {unused}")

    print("\n=== 正对照 ===")
    ctl_ok = True
    if mapping.get("Read_Colors") != "Colors":
        print(f"  !! Read_Colors 的节名 = {mapping.get('Read_Colors')!r}，期望 'Colors'")
        ctl_ok = False
    if mapping.get("Read_General") != "General":
        print(f"  !! Read_General 的节名 = {mapping.get('Read_General')!r}，期望 'General'")
        ctl_ok = False
    if INIT != 0x006686C0 or read_va(INIT, 6) != b"\x81\xec\xd0\x00\x00\x00":
        print(f"  !! Init 头部字节 = {read_va(INIT, 6).hex(' ')}，期望 '81 ec d0 00 00 00'")
        ctl_ok = False
    if named < 28:
        print(f"  !! 指针表非空项只有 {named}，少于 28 —— 表基址或范围可能错")
        ctl_ok = False
    # Boundary control: Init must reach Read_File exactly 3 times and must not
    # call any Read_* directly. If the ranges are wrong these silently move --
    # an oversized Init window produced "28 loaders in Init" in the first version.
    if n_rf != 3:
        print(f"  !! Init 内 call Read_File 次数 = {n_rf}，期望 3")
        ctl_ok = False
    if init_seq:
        print(f"  !! Init 直接调用了 {len(init_seq)} 个 Read_*，期望 0")
        ctl_ok = False
    if len(rf_seq) != 28:
        print(f"  !! Read_File 内 loader 调用数 = {len(rf_seq)}，期望 28")
        ctl_ok = False
    if not ctl_ok:
        print("  正对照失败 —— 以上结果不可信")
        return 1
    print("  正对照通过（Read_Colors / Read_General / Init 头 / 表≥28项 / Init→Read_File×3 / Read_File 28 loaders）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


def sections_referenced(fn_va, window=0x400):
    """Every section name referenced from fn_va up to its first `ret`, in order.

    section_used_by() answers "which section does this function look up first",
    which is an implementation detail, NOT the function's responsibility: a
    loader can call other loaders or loop over several sections. Read_File calls
    Read_Colors and then enumerates seven sections; reporting only the first one
    would misdescribe it.

    Keys are filtered out by requiring the string to be a member of the
    section-name pointer table OR to be pushed as a bare literal that is not a
    known difficulty key. Cases that cannot be told apart are still printed, so
    the reader decides rather than the tool guessing.
    """
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = True
    table_names = {s for _, s in section_table() if s}
    out = []
    seen = set()
    for insn in md.disasm(read_va(fn_va, window), fn_va):
        cand = operand_string(insn)
        if cand:
            va, name, shape = cand
            # Dedup by NAME: one section is referenced several times (once to
            # call GetSection, once per key read), and listing it per reference
            # makes the output look like several different sections.
            if name in seen:
                continue
            # A data-region immediate is only a section if it is either in the
            # pointer table or a push. Otherwise it is some other constant whose
            # bytes happen to read as ASCII -- capstone will happily render a
            # Win32 API pointer as a truncated string like "ostMessageA".
            if name not in table_names and shape != "direct":
                continue
            seen.add(name)
            out.append((va, name, shape))
        if insn.mnemonic == "ret":
            break
    return out
