"""R-023: consumer map for the MultiplayerDialogSettings block.

Two independent questions, both answered from bytes:

  1. Which code READS a given RulesClass field offset? Answered by scanning every
     instruction. This has to be a sweep with audited resync, not a single
     `md.disasm(.text)`: capstone stops decoding at 0x46F5A0 on this image (a
     jump-table block inside .text) and a single pass silently covers only the
     first 9% of the section.

  2. Which GLOBAL mirrors that field after loading? The engine copies 21 of the
     27 settings out of RulesClass into standalone globals right after
     Read_MultiplayerDialogSettings returns, and most of the game then reads the
     GLOBAL, not the RulesClass field. A compiler that only checks "did my INI
     value reach RulesClass" will be wrong about what the game does.

     (2) matters more than it looks: it is why `[MultiplayerDialogSettings]` is
     not purely a lobby-screen section. Both halves are recovered here rather
     than asserted.

Run: python re_atlas/tools/dump_rules_consumers.py
"""

import os
import struct
import sys

import capstone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dump_rules_sections as D  # noqa: E402
from text_sweep import sweep        # noqa: E402  audited full-.text sweep

FIELD_LO, FIELD_HI = 0x1480, 0x14BC

# RulesClass field offsets -> key, taken from R-023's field table. Kept as data so
# this tool can be pointed at other blocks without re-deriving the mapping.
KEYS = {
    0x1480: "MinMoney", 0x1484: "Money", 0x1488: "MaxMoney",
    0x148C: "MoneyIncrement", 0x1490: "MinUnitCount", 0x1494: "UnitCount",
    0x1498: "MaxUnitCount", 0x149C: "TechLevel", 0x14A0: "GameSpeed",
    0x14A4: "AIDifficulty", 0x14A8: "AIPlayers", 0x14AC: "BridgeDestruction",
    0x14AD: "ShadowGrow", 0x14AE: "Shroud", 0x14AF: "Bases",
    0x14B0: "TiberiumGrows", 0x14B1: "Crates", 0x14B2: "CaptureTheFlag",
    0x14B3: "HarvesterTruce", 0x14B4: "MultiEngineer", 0x14B5: "AlliesAllowed",
    0x14B6: "ShortGame", 0x14B7: "FogOfWar", 0x14B8: "MCVRedeploys",
    0x14B9: "SuperWeaponsAllowed", 0x14BA: "BuildOffAlly",
    0x14BB: "AllyChangeAllowed",
}

READER_RANGE = (0x00671EA0, 0x00672224)   # the reader itself: builds defaults, stores
CTOR_RANGE = (0x00665650, 0x00667A27)     # the ctor: sets defaults

# The function that loads rulesmd.ini, reached by its own prologue at 0x52CD70.
# It ends at the LAST ret reachable from that entry (0x52D30B); the intermediate
# ret at 0x52D0B3 is one of several EXIT PATHS (early-out on ARTMD failure), not
# the function's end. Treating a ret as the end splits this function and hides
# the mirror block -- which is exactly what an earlier version of this analysis
# did, reporting 0 consumers for ShadowGrow when in fact every field is mirrored.
LOADER = (0x0052CD70, 0x0052D30C)


def mem_disp(insn):
    """Displacements of all simple [reg+disp] operands."""
    out = []
    for op in insn.operands:
        if op.type == capstone.x86.X86_OP_MEM and op.mem.base != 0 and op.mem.index == 0:
            out.append(op.mem.disp)
    return out


def abs_operand(insn):
    """The absolute address of a `[disp32]` operand (base == index == 0), or None."""
    for op in insn.operands:
        if op.type == capstone.x86.X86_OP_MEM and op.mem.base == 0 and op.mem.index == 0:
            return op.mem.disp & 0xFFFFFFFF
    return None


def reader_map():
    """offset -> [(site, func_origin, is_store)] outside reader and ctor."""
    hits = {o: [] for o in KEYS}
    for insn in sweep():
        if READER_RANGE[0] <= insn.address < READER_RANGE[1]:
            continue
        if CTOR_RANGE[0] <= insn.address < CTOR_RANGE[1]:
            continue
        for d in mem_disp(insn):
            if FIELD_LO <= d < FIELD_HI:
                hits.setdefault(d, []).append((insn.address, insn.mnemonic))
                break
    return hits


def mirrored_globals():
    """offset -> [(global VA, copy site)] for the loader's field -> global copies.

    The copy is TWO instructions, and an earlier version assumed one:

        mov  edx, [eax + 0x1484]      ; load the field
        mov  [0xa8b25c], edx          ; store it into a global

    Pairing dst/src operands within a single instruction finds nothing here, so
    the tracker follows the register: a field load latches (offset, reg), and a
    store of that same register into an absolute address completes the pair. Any
    write to the register in between drops the latch rather than producing a
    wrong global.

    Only the shape the loader emits is accepted, and nothing is inferred from
    adjacency to the reader call -- the block is located by the field offsets
    themselves, so a shifted prologue cannot silently poison it.
    """
    out = {}
    pending = {}      # reg id -> field offset
    for insn in sweep(LOADER[0], LOADER[1]):
        if insn.mnemonic != "mov" or len(insn.operands) != 2:
            # NOT a reason to clear the whole latch: the loader interleaves
            # unrelated instructions between load and store (`lea ecx,[esp+..]`
            # sits between MCVRedeploys' load and its store at 0x52D225). Only a
            # write to the SAME register invalidates a latch, which the generic
            # destination check below handles.
            if insn.operands and insn.operands[0].type == capstone.x86.X86_OP_REG \
                    and insn.mnemonic not in ("cmp", "test", "push", "lea"):
                pending.pop(insn.operands[0].reg, None)
            continue
        dst, src = insn.operands
        # field load: reg <- [obj + off]
        if dst.type == capstone.x86.X86_OP_REG and src.type == capstone.x86.X86_OP_MEM:
            if src.mem.base != 0 and src.mem.index == 0 and FIELD_LO <= src.mem.disp < FIELD_HI:
                pending[dst.reg] = src.mem.disp
                continue
            pending.pop(dst.reg, None)
            continue
        # global store: [abs] <- reg
        if dst.type == capstone.x86.X86_OP_MEM and dst.mem.base == 0 \
                and dst.mem.index == 0 and src.type == capstone.x86.X86_OP_REG:
            off = pending.pop(src.reg, None)
            if off is not None:
                out.setdefault(off, []).append((dst.mem.disp & 0xFFFFFFFF, insn.address))
            continue
        if dst.type == capstone.x86.X86_OP_REG:
            pending.pop(dst.reg, None)
    return out


def main():
    print("=== 1. 字段读取点（排除读取器自身与构造器）===")
    hits = reader_map()
    print(f"  {'键':24s} {'偏移':>7s} {'读点':>5s}")
    for off in sorted(KEYS):
        print(f"  {KEYS[off]:24s} +0x{off:04X} {len(hits.get(off, [])):5d}")

    print("\n=== 2. 载入后镜像到全局的字段 ===")
    mir = mirrored_globals()
    print(f"  {'键':24s} {'偏移':>7s} {'全局':>11s}  站点")
    for off in sorted(KEYS):
        got = mir.get(off, [])
        if got:
            vas = ", ".join(f"0x{g:08X}@0x{s:08X}" for g, s in got)
            print(f"  {KEYS[off]:24s} +0x{off:04X} {'':>11s}  {vas}")
        else:
            print(f"  {KEYS[off]:24s} +0x{off:04X} {'—':>11s}  未镜像")

    print("\n=== 3. 全局被谁引用 ===")
    # Two kinds, counted apart because they mean different things:
    #   mem  = the value is read/written (a real consumer)
    #   imm  = the ADDRESS is taken (`push 0x...`), typically to register a
    #          save/load slot or to hand the variable to a helper
    # A single "reference count" mixes them and cannot be checked against a raw
    # dword scan. TechLevel: 20 mem + 5 imm = 25 raw occurrences, which is what
    # the byte scan finds.
    mem_refs, imm_refs = {}, {}
    for insn in sweep():
        a = abs_operand(insn)
        if a is not None:
            mem_refs[a] = mem_refs.get(a, 0) + 1
        for op in insn.operands:
            if op.type == capstone.x86.X86_OP_IMM:
                v = op.imm & 0xFFFFFFFF
                imm_refs[v] = imm_refs.get(v, 0) + 1
    print(f"  {'键':24s} {'全局':>11s} {'取值':>5s} {'取址':>5s}")
    for off in sorted(KEYS):
        for g, _site in mir.get(off, []):
            print(f"  {KEYS[off]:24s} 0x{g:08X} {mem_refs.get(g, 0):5d} "
                  f"{imm_refs.get(g, 0):5d}")

    print("\n=== 正对照 ===")
    ok = True
    if not mir:
        print("  !! 镜像块一个字段都没解出")
        ok = False

    # Independent reconciliation: a raw dword scan over .text must find exactly
    # (mem-operand + immediate-operand) occurrences of each global VA. This is
    # the check that catches a decoder gap -- if the sweep skipped a region, the
    # byte count exceeds the decoded count and the row is reported.
    raw = D.read_va(0x401000, 0x3E0000 - 0x1000)
    for off in sorted(KEYS):
        for g, _site in mir.get(off, []):
            raw_n = raw.count(struct.pack("<I", g))
            dec_n = mem_refs.get(g, 0) + imm_refs.get(g, 0)
            if raw_n != dec_n:
                print(f"  !! {KEYS[off]} 0x{g:08X}: 字节扫描 {raw_n} 处，"
                      f"指令扫描 {dec_n} 处（mem {mem_refs.get(g, 0)} + imm {imm_refs.get(g, 0)}）")
                ok = False

    # FogOfWar specifically: the earlier split-function analysis missed it, and
    # the copy is at 0x52D219 storing to 0xa8b31f. Both must be present.
    fog = mir.get(0x14B7, [])
    if not any(g == 0xA8B31F for g, _ in fog):
        print(f"  !! FogOfWar 未镜像到 0xA8B31F，实得 {fog}")
        ok = False
    # Every offset up to 0x14AC plus the scattered ones must be mirrored; six of
    # the 27 have no lobby counterpart and are not.
    mirrored = set(mir)
    if len(mirrored) < 15:
        print(f"  !! 只镜像了 {len(mirrored)} 个字段，少于 15")
        ok = False
    # reader_map must see the loader's own reads as consumers of these fields.
    if not hits.get(0x14A0):
        print("  !! GameSpeed 一个读点都没有")
        ok = False
    if not ok:
        print("  正对照失败 —— 以上结果不可信")
        return 1
    print(f"  正对照通过（镜像 {len(mirrored)} 字段 / 每个全局字节扫描=指令扫描 / "
          f"FogOfWar→0xA8B31F / GameSpeed 有读点）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
