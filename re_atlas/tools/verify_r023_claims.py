"""Independent machine gate for R-023 / H-016: `RulesClass` MultiplayerDialogSettings
fields and their mirror globals.

What is under test (H-016, as delivered):

  1. `Read_MultiplayerDialogSettings` (0x671EA0) reads 27 fixed keys into
     `RulesClass+0x1480..+0x14BB`.
  2. Right after it returns, the loader (0x52CD70) copies **18** of those fields
     into standalone globals; **9** are not copied.
  3. `ShortGame` -> 0x00A8B262 (50 reads), `FogOfWar` -> 0x00A8B31F (22),
     `MCVRedeploys` -> 0x00A8B320 (44).
  4. `ShadowGrow` +0x14AD has zero consumers: its disp32 occurs 3 times in .text
     (ctor write + reader read + reader write).
  5. Compiler implication: at runtime you must patch the GLOBAL; patching the
     `RulesClass` field has no effect once mirrored.

Implementation notes -- where this gate is deliberately orthogonal to
`dump_rules_consumers.py`:

  * That tool recovers the field->global pairs with a FORWARD latch: it walks the
    loader once, remembers `(offset, reg)` on a field load, and completes the
    pair on a later store of the same register. Its failure mode is a stale
    latch.
  * This gate goes the other way: it first enumerates every absolute store in
    the loader block, then walks BACKWARD from each store to the nearest preceding
    load into the same register. A pair whose load is more than a few
    instructions back fails loudly instead of silently pairing with the previous
    field.
  * The 18 globals are DISCOVERED (the set of absolute stores in the block), not
    taken from the claim. The claim's own list is then compared as a set, so a
    wrong global in the delivered table shows up as two differences rather than
    as a silent pass.

Assertions 10-12 are additions the original analysis never made: they test the
compiler implication itself rather than the field table, and two of them
FALSIFY the implied "written once at load" model.

Run: python re_atlas/tools/verify_r023_claims.py
"""

import hashlib
import os
import struct
import sys

import capstone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dump_rules_sections as D  # noqa: E402  read_va with per-section bounds
from text_sweep import sweep, resyncs  # noqa: E402

EXPECTED_SHA256 = "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476"

TEXT_LO, TEXT_HI = 0x401000, 0x7E1000
RDATA_LO, RDATA_HI = 0x7E1000, 0x811000

READER = (0x00671EA0, 0x00672224)
CTOR = (0x00665650, 0x00667A27)

LOADER_ENTRY = 0x0052CD70
# DELIVERED bound. The doc claims the function's last `ret` is 0x52D30B, so the
# body would be [0x52CD70, 0x52D30C). Assertion P3 FALSIFIES that: an in-function
# `jle` at 0x52D277 targets 0x52D30C, and a normal epilogue follows it, ending in
# `ret` at 0x52D42F. The delivered bound is 0x124 bytes short.
LOADER_DOC_END = 0x0052D30C
# Branch-closure extent, independently derived in the gate (see closure()).
LOADER_SCAN_HI = 0x0052E200
LOADER_EARLY_RETS = (0x0052D032, 0x0052D0B3)   # early exits, not the end

# The mirror block as delivered: first store .. last store, inclusive.
BLOCK_LO, BLOCK_HI = 0x0052D149, 0x0052D230

# --- claim tables -----------------------------------------------------------
# offset -> (key, width in bytes)
FIELDS = {
    0x1480: ("MinMoney", 4), 0x1484: ("Money", 4), 0x1488: ("MaxMoney", 4),
    0x148C: ("MoneyIncrement", 4), 0x1490: ("MinUnitCount", 4),
    0x1494: ("UnitCount", 4), 0x1498: ("MaxUnitCount", 4),
    0x149C: ("TechLevel", 4), 0x14A0: ("GameSpeed", 4),
    0x14A4: ("AIDifficulty", 4), 0x14A8: ("AIPlayers", 4),
    0x14AC: ("BridgeDestruction", 1), 0x14AD: ("ShadowGrow", 1),
    0x14AE: ("Shroud", 1), 0x14AF: ("Bases", 1), 0x14B0: ("TiberiumGrows", 1),
    0x14B1: ("Crates", 1), 0x14B2: ("CaptureTheFlag", 1),
    0x14B3: ("HarvesterTruce", 1), 0x14B4: ("MultiEngineer", 1),
    0x14B5: ("AlliesAllowed", 1), 0x14B6: ("ShortGame", 1),
    0x14B7: ("FogOfWar", 1), 0x14B8: ("MCVRedeploys", 1),
    0x14B9: ("SuperWeaponsAllowed", 1), 0x14BA: ("BuildOffAlly", 1),
    0x14BB: ("AllyChangeAllowed", 1),
}

MIRRORED = {
    0x1484: 0x00A8B25C, 0x1494: 0x00A8B270, 0x149C: 0x00822CF4,
    0x14A0: 0x00A8B268, 0x14A4: 0x00A8B278, 0x14A8: 0x00A8B274,
    0x14AC: 0x00A8B260, 0x14AF: 0x00A8B258, 0x14B1: 0x00A8B261,
    0x14B2: 0x00A8B31E, 0x14B3: 0x00A8B31D, 0x14B4: 0x00A8B26C,
    0x14B5: 0x00A8B31C, 0x14B6: 0x00A8B262, 0x14B9: 0x00A8B263,
    0x14BA: 0x00A8B264, 0x14B7: 0x00A8B31F, 0x14B8: 0x00A8B320,
}
UNMIRRORED = sorted(set(FIELDS) - set(MIRRORED))

# The second, undocumented write-back block: ModemGst session packet decoder.
# H-016 never mentions it; assertion 11 measures it.
MODEM_FN = 0x005B6011
MODEM_BLOCK = (0x005B69E4, 0x005B6B50)
MODEM_STRING_VA = 0x0082C7A4
MODEM_STRING = "Decoding game options\n"

RULES_GLOBAL = 0x008871E0
ART_INI = 0x00887180

# Offset-collision witnesses used by assertion 12.
COLLISION_SITES = {
    0x00463A48: 0x1499, 0x00463A65: 0x149A, 0x00463A82: 0x149B,
    0x00652A70: 0x1488, 0x006544F4: 0x1498,
}

RESULTS = []


def check(tag, ok, msg, detail=""):
    RESULTS.append((tag, bool(ok), msg, detail))
    print(f"  [{'PASS' if ok else 'FAIL'}] {tag}  {msg}")
    if detail and not ok:
        for line in detail.splitlines():
            print(f"         {line}")
    return bool(ok)


# --- decode helpers ---------------------------------------------------------
_SUB = {"al": "eax", "ah": "eax", "cl": "ecx", "ch": "ecx",
        "dl": "edx", "dh": "edx", "bl": "ebx", "bh": "ebx"}


def canon(insn, reg_id):
    n = insn.reg_name(reg_id)
    return _SUB.get(n, n)


def abs_addr(insn, idx=0):
    if len(insn.operands) <= idx:
        return None
    op = insn.operands[idx]
    if op.type != capstone.x86.X86_OP_MEM:
        return None
    if op.mem.base != 0 or op.mem.index != 0:
        return None
    return op.mem.disp & 0xFFFFFFFF


def reg_field_load(insn, lo, hi):
    """(dst_reg_canon, offset) when insn is `mov REG, [base + off]` in range."""
    if insn.mnemonic != "mov" or len(insn.operands) != 2:
        return None
    dst, src = insn.operands
    if dst.type != capstone.x86.X86_OP_REG or src.type != capstone.x86.X86_OP_MEM:
        return None
    if src.mem.base == 0 or src.mem.index != 0:
        return None
    if not (lo <= src.mem.disp < hi):
        return None
    return canon(insn, dst.reg), src.mem.disp


def is_abs_store(insn):
    """(src_reg_canon) when insn is `mov [abs], REG` (memory dst, abs, reg src)."""
    if insn.mnemonic != "mov" or len(insn.operands) != 2:
        return None
    dst, src = insn.operands
    if dst.type != capstone.x86.X86_OP_MEM or src.type != capstone.x86.X86_OP_REG:
        return None
    if dst.mem.base != 0 or dst.mem.index != 0:
        return None
    return canon(insn, src.reg)


def is_mem_write(insn):
    """True when the instruction writes memory through its first operand."""
    if not insn.operands:
        return False
    op = insn.operands[0]
    if op.type != capstone.x86.X86_OP_MEM:
        return False
    m = insn.mnemonic
    return (m.startswith("mov") or m.startswith("fst") or m.startswith("fild")
            or m in ("and", "or", "xor", "add", "sub", "inc", "dec", "neg", "not",
                     "adc", "sbb", "xchg"))


def mem_disp_of(insn):
    """disp of a `[reg+disp]` operand, preferring a WRITE (operand 0).

    BUG THIS FIXES: an earlier version of this gate only looked at operand[0].
    That silently drops every memory READ, because in `mov cl, [esi+0x14AD]` the
    memory operand is operand[1]. ShadowGrow then appeared to have 2 sites
    instead of 3, and all 18 global reference counts came out roughly half the
    byte-scan counts. Counting only writes is not a conservative choice -- it is
    a wrong one, because the claim being tested is "zero consumers".
    """
    for idx in (0, 1):
        if len(insn.operands) <= idx:
            continue
        op = insn.operands[idx]
        if op.type != capstone.x86.X86_OP_MEM:
            continue
        if op.mem.base == 0 or op.mem.index != 0:
            continue
        return op.mem.disp
    return None


def disp_list(insn):
    """Every simple [reg+disp] in the instruction, whatever the operand position."""
    out = []
    for op in insn.operands:
        if op.type == capstone.x86.X86_OP_MEM and op.mem.base and op.mem.index == 0:
            out.append(op.mem.disp)
    return out


def closure(md, entry, limit):
    """Branch-closure of the function at `entry`: address -> instruction.

    Needed because this function has a SEPARATED COLD BLOCK. A `jle` from inside
    the body lands at 0x52D30C, which is immediately AFTER the `ret` at 0x52D30B.
    Linear decoding stops at that ret and silently loses the tail; walking
    branch targets from inside the function recovers it.

    "The function ends at its own last `ret`" is only true when you already know
    the whole instruction set of the function. It is a conclusion, not a
    detector.
    """
    seen = {}
    work = [entry]
    while work:
        start = work.pop()
        if start in seen or not (entry <= start < limit):
            continue
        for insn in md.disasm(D.read_va(start, limit - start), start):
            if insn.address in seen:
                break
            seen[insn.address] = insn
            if insn.mnemonic.startswith("ret") or insn.mnemonic == "int3":
                break
            if insn.mnemonic == "jmp":
                break
            if insn.mnemonic.startswith("j"):
                for op in insn.operands:
                    if op.type == capstone.x86.X86_OP_IMM:
                        v = op.imm & 0xFFFFFFFF
                        if entry <= v < limit and v not in seen:
                            work.append(v)
    return seen


def main():
    print("=== R-023 / H-016 独立门禁 ===\n")

    # ---- P1 binary identity ------------------------------------------------
    got = hashlib.sha256(D.BLOB).hexdigest()
    check("P1", got == EXPECTED_SHA256, "目标二进制指纹",
          f"expect {EXPECTED_SHA256}\n got    {got}")

    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = True

    # ---- P2 loader really calls the reader exactly once -------------------
    # Uses the branch-closure extent, not the delivered bound: the delivered
    # bound cuts the function short (assertion P3b), and using it here would
    # make P2 inherit the same truncation.
    clo = closure(md, LOADER_ENTRY, LOADER_SCAN_HI)
    loader_insns = [clo[a] for a in sorted(clo)]
    calls = [i for i in loader_insns
             if i.mnemonic == "call" and i.op_str.startswith("0x671ea0")]
    check("P2", len(calls) == 1,
          f"loader 内恰 1 次 `call Read_MultiplayerDialogSettings`（实得 {len(calls)}）",
          "\n".join(f"0x{i.address:08X}" for i in calls))

    # ---- P3 function extent: branch closure vs the delivered bound -------
    # P3a: the two early rets ARE inside the function (they are exits reached by
    # in-body jumps), not function boundaries.
    # P3b: the delivered end 0x52D30C is WRONG -- an in-body `jle` targets it,
    # so the cold block after 0x52D30B belongs to the same function.
    clo_rets = sorted(a for a, i in clo.items() if i.mnemonic.startswith("ret"))
    early_inside = all(r in clo_rets for r in LOADER_EARLY_RETS)
    check("P3a", early_inside,
          f"0x52D032 / 0x52D0B3 都在函数可达集内（提前退出，非边界）；"
          f"闭包 rets = {['0x%X' % r for r in clo_rets]}",
          f"clo_rets={['0x%X' % r for r in clo_rets]}")

    # Find an in-function branch whose target is inside the delivered span but
    # beyond a ret -- that is the cold-block signature.
    cold_edges = []
    for a, i in clo.items():
        if not i.mnemonic.startswith("j"):
            continue
        for op in i.operands:
            if op.type == capstone.x86.X86_OP_IMM:
                v = op.imm & 0xFFFFFFFF
                if v in clo and any(a < r < v for r in clo_rets):
                    cold_edges.append((a, v))
    true_end = max(clo) + clo[max(clo)].size
    check("P3b", bool(cold_edges) and true_end > LOADER_DOC_END,
          f"★ 交付边界 0x{LOADER_DOC_END:08X} 太短：函数内有 "
          f"{len(cold_edges)} 条跳转越过 ret 进入冷块，真尾 0x{true_end:08X}"
          f"（差 {true_end - LOADER_DOC_END} 字节）",
          f"cold_edges={[('0x%X' % a, '0x%X' % v) for a, v in cold_edges]}\n"
          f"true_end=0x{true_end:08X}")

    # ---- P4 discover the mirror block ------------------------------------
    block = [i for i in loader_insns if BLOCK_LO <= i.address < BLOCK_HI]
    stores = []
    for i in block:
        src = is_abs_store(i)
        if src is not None:
            stores.append((i.address, abs_addr(i, 0), src))
    found_globals = [g for _a, g, _s in stores]
    check("P4", len(stores) == 18 and len(set(found_globals)) == 18,
          f"镜像块内恰 18 条绝对存回、18 个互不相同的全局（实得 {len(stores)}/{len(set(found_globals))}）",
          "\n".join(f"0x{a:08X} -> 0x{g:08X}" for a, g, _ in stores))

    claim_set = set(MIRRORED.values())
    actual_set = set(found_globals)
    check("P4b", claim_set == actual_set,
          "交付件给出的 18 个全局 == 从字节发现的集合",
          f"only_in_claim={sorted('%08X' % g for g in claim_set - actual_set)}\n"
          f"only_in_bytes={sorted('%08X' % g for g in actual_set - claim_set)}")

    # ---- P5 backward pair recovery ---------------------------------------
    pairs = {}
    bad = []
    idx_by_addr = {i.address: k for k, i in enumerate(loader_insns)}
    for addr, g, src in stores:
        k = idx_by_addr[addr]
        off = None
        for j in range(k - 1, max(k - 7, -1), -1):
            hit = reg_field_load(loader_insns[j], min(FIELDS), max(FIELDS) + 1)
            if hit is None:
                continue
            cand_reg, cand_off = hit
            if cand_reg == src:
                off = (loader_insns[j].address, cand_off)
                break
            # A load into a DIFFERENT register is not automatically fatal (the
            # block interleaves two alternating registers), but walking past
            # several of them means the pair is not local.
        if off is None:
            bad.append(f"0x{addr:08X} -> 0x{g:08X}: 回找不到同寄存器的字段载入")
            continue
        pairs[off[1]] = (g, addr, off[0])
    check("P5", len(pairs) == 18 and not bad,
          f"18 对 (字段, 全局) 全部由「存回点向前找同寄存器载入」独立复原（实得 {len(pairs)}）",
          "\n".join(bad))

    mismatch = []
    for off, (g, _addr, _load) in sorted(pairs.items()):
        want = MIRRORED.get(off)
        if want is None:
            mismatch.append(f"+0x{off:04X} 字节里有存回，交付表说未镜像")
        elif want != g:
            mismatch.append(f"+0x{off:04X} 交付 0x{want:08X} / 字节 0x{g:08X}")
    check("P5b", not mismatch,
          "每一对的字段->全局与交付表逐项相等（18/18）",
          "\n".join(mismatch))

    # ---- P6 the 9 unmirrored really have no store ------------------------
    seen_offs = set(pairs)
    leaked = [off for off in UNMIRRORED if off in seen_offs]
    # Also: no store anywhere in the loader may source from an unmirrored offset.
    stray = []
    for i in loader_insns:
        src = is_abs_store(i)
        if src is None:
            continue
        k = idx_by_addr[i.address]
        for j in range(k - 1, max(k - 7, -1), -1):
            hit = reg_field_load(loader_insns[j], min(FIELDS), max(FIELDS) + 1)
            if hit and hit[0] == src and hit[1] in UNMIRRORED:
                stray.append(f"0x{i.address:08X} 存回来自未镜像字段 +0x{hit[1]:04X}")
                break
    check("P6", not leaked and not stray,
          f"9 个未镜像字段在 loader 内确实无存回（{len(UNMIRRORED)} 项）",
          "\n".join([f"leaked={leaked}"] + stray))

    # ---- P7 layout: 11 dwords then 16 bytes, no holes --------------------
    sorted_offs = sorted(FIELDS)
    contiguous = all(sorted_offs[k + 1] == off + FIELDS[off][1]
                     for k, off in enumerate(sorted_offs[:-1]))
    dword_run = sorted_offs[:11]
    byte_run = sorted_offs[11:]
    layout_ok = (contiguous
                 and all(FIELDS[o][1] == 4 for o in dword_run)
                 and all(FIELDS[o][1] == 1 for o in byte_run)
                 and dword_run[0] == 0x1480 and byte_run[0] == 0x14AC
                 and byte_run[-1] == 0x14BB)
    check("P7", layout_ok,
          "布局 = 11×dword(0x1480..0x14AB) + 16×byte(0x14AC..0x14BB)，零空洞",
          f"dword_run={['0x%X' % o for o in dword_run]}\n"
          f"byte_run={['0x%X' % o for o in byte_run]}")

    # ---- P8 reader touches all 27 (read AND write) -----------------------
    reader_insns = list(md.disasm(D.read_va(READER[0], READER[1] - READER[0]), READER[0]))
    r_read, r_write = set(), set()
    for i in reader_insns:
        d = mem_disp_of(i)
        if d is not None and d in FIELDS and is_mem_write(i):
            r_write.add(d)
        for op in i.operands:
            if op.type == capstone.x86.X86_OP_MEM and op.mem.base != 0 \
                    and op.mem.index == 0 and op.mem.disp in FIELDS:
                # a `mov [reg+off], x` is a write; anything else reading it is a read
                r_read.add(op.mem.disp)
    check("P8", len(r_write) == 27 and len(r_read) == 27,
          f"读取器对 27 个偏移都有读与写（写 {len(r_write)} / 触及 {len(r_read)}）",
          f"missing_write={sorted('0x%X' % o for o in set(FIELDS) - r_write)}\n"
          f"missing_any={sorted('0x%X' % o for o in set(FIELDS) - r_read)}")

    # ---- full sweep: everything below needs it ---------------------------
    print("\n  ... 全段扫描（约 2 分钟）...")
    insns = sweep()
    insns.sort(key=lambda i: i.address)
    rs = resyncs()
    check("P9", len(insns) > 1_300_000,
          f"全段扫描 {len(insns):,} 条，重同步 {len(rs)} 处",
          f"resyncs={rs[:4]}")

    # ---- P10 ShadowGrow zero consumers ----------------------------------
    raw_text = D.read_va(TEXT_LO, 0x3E0000 - 0x1000)
    sg_raw = raw_text.count(struct.pack("<I", 0x14AD))
    sg_sites = []
    for i in insns:
        if 0x14AD in disp_list(i):
            sg_sites.append(i.address)
    outside = [a for a in sg_sites
               if not (READER[0] <= a < READER[1] or CTOR[0] <= a < CTOR[1])]
    check("P10", sg_raw == 3 and len(sg_sites) == 3 and not outside,
          f"ShadowGrow +0x14AD：字节扫描 {sg_raw} / 指令 {len(sg_sites)}，"
          f"读取器+构造器之外 {len(outside)} 处",
          f"sites={['0x%X' % a for a in sg_sites]}\n"
          f"outside={['0x%X' % a for a in outside]}")

    # ---- P11 byte-scan reconciliation for each global -------------------
    # Every absolute operand, in ANY position. operand[0]-only counting drops
    # `mov eax, [0xa8b25c]` entirely and halves every row.
    mem_refs, imm_refs = {}, {}
    for i in insns:
        for op in i.operands:
            if op.type == capstone.x86.X86_OP_MEM and op.mem.base == 0 \
                    and op.mem.index == 0:
                a = op.mem.disp & 0xFFFFFFFF
                mem_refs[a] = mem_refs.get(a, 0) + 1
            elif op.type == capstone.x86.X86_OP_IMM:
                v = op.imm & 0xFFFFFFFF
                imm_refs[v] = imm_refs.get(v, 0) + 1
    recon = []
    for off, g in sorted(MIRRORED.items()):
        raw_n = raw_text.count(struct.pack("<I", g))
        dec_n = mem_refs.get(g, 0) + imm_refs.get(g, 0)
        if raw_n != dec_n:
            recon.append(f"{FIELDS[off][0]:20s} 0x{g:08X}: 字节 {raw_n} != 指令 {dec_n}"
                         f" (mem {mem_refs.get(g, 0)} + imm {imm_refs.get(g, 0)})")
    check("P11", not recon,
          "18 个全局：字节扫描出现次数 == 指令扫描(取值+取址) 次数",
          "\n".join(recon))

    # ---- P12 ADDITION: globals are NOT written only at load -------------
    # A write is operand[0] memory AND a mnemonic that stores. `cmp [abs],0`
    # also has operand[0] in memory but does not write -- counting it would
    # inflate every row and turn this assertion into a tautology.
    write_sites = {g: [] for g in MIRRORED.values()}
    for i in insns:
        if not is_mem_write(i):
            continue
        a = abs_addr(i, 0)
        if a in write_sites:
            write_sites[a].append(i.address)
    counts = {FIELDS[off][0]: len(write_sites[g]) for off, g in MIRRORED.items()}
    split = {}
    for off, g in MIRRORED.items():
        in_load = sum(1 for a in write_sites[g] if BLOCK_LO <= a < BLOCK_HI)
        in_modem = sum(1 for a in write_sites[g] if MODEM_BLOCK[0] <= a < MODEM_BLOCK[1])
        other = len(write_sites[g]) - in_load - in_modem
        split[FIELDS[off][0]] = (in_load, in_modem, other)
    min_other = min(v[2] for v in split.values())
    # Deliberately EXCLUDES both the loader block and the ModemGst block: if this
    # counted either, the assertion would just restate P13 and prove nothing.
    check("P12", min_other >= 2,
          f"★ 补充事实：排除载入块与 ModemGst 块后，每个全局仍被别处写入"
          f"（最少 {min_other} 处，共 {sum(v[2] for v in split.values())} 处）。"
          f"「载入后只写一次」不成立",
          "\n".join(f"{k:20s} 载入 {split[k][0]} Modem {split[k][1]} 其他 {split[k][2]:2d}"
                    for k in sorted(split)))

    # ---- P13 ADDITION: the second mirror block (ModemGst) ---------------
    modem_str = b""
    for k in range(len(MODEM_STRING) + 2):
        c = D.read_va(MODEM_STRING_VA + k, 1)
        if c == b"\x00":
            break
        modem_str += c
    modem_insns = list(md.disasm(D.read_va(MODEM_BLOCK[0],
                                          MODEM_BLOCK[1] - MODEM_BLOCK[0]),
                                 MODEM_BLOCK[0]))
    modem_hits = {}
    for i in modem_insns:
        if not is_mem_write(i):
            continue
        a = abs_addr(i, 0)
        if a in write_sites:
            modem_hits[a] = i.address
    # source struct offsets touched in the same block
    src_offs = sorted({op.mem.disp for i in modem_insns for op in i.operands
                       if op.type == capstone.x86.X86_OP_MEM
                       and op.mem.base == capstone.x86.X86_REG_EBX})
    modem_ok = (modem_str.decode("ascii", "replace") == MODEM_STRING
                and len(modem_hits) >= 16
                and all(o < 0x100 for o in src_offs))
    check("P13", modem_ok,
          f"★ 第二个镜像块：0x{MODEM_BLOCK[0]:08X}（{MODEM_STRING.strip()}）"
          f" 写入 {len(modem_hits)}/18 个同名全局，源字段只到 +0x{max(src_offs, default=0):02X}",
          f"string={modem_str!r}\n"
          f"globals_written={sorted('0x%08X' % g for g in modem_hits)}\n"
          f"missing={sorted(FIELDS[o][0] for o, g in MIRRORED.items() if g not in modem_hits)}\n"
          f"src_offs={['0x%X' % o for o in src_offs]}")

    # ---- P14 ADDITION: offset collisions are not RulesClass -------------
    coll = []
    coll_ok = True
    for site, off in COLLISION_SITES.items():
        near = [i for i in insns if site <= i.address < site + 1]
        if not near:
            coll.append(f"0x{site:08X} 不在指令边界")
            coll_ok = False
            continue
        d = mem_disp_of(near[0])
        if d != off:
            coll.append(f"0x{site:08X} disp=0x{d if d is None else format(d, 'X')} 期望 0x{off:X}")
            coll_ok = False
    # The 0x463Axx family must be the artmd TypeClass reader, i.e. it must load
    # INI_Art (0x887180) and must NOT reference the RulesClass global.
    win = D.read_va(0x00463800, 0x400)
    art_ref = struct.pack("<I", ART_INI) in win
    rules_ref = struct.pack("<I", RULES_GLOBAL) in win
    collision_is_other_class = art_ref and not rules_ref
    check("P14", coll_ok and collision_is_other_class,
          "★ 0x463Axx 的 [ebp+0x1488..] 写入属 artmd TypeClass（引 0x887180、不引 0x8871E0），"
          "不是 RulesClass 的 MaxMoney",
          "\n".join(coll) + f"\nart_ref={art_ref} rules_ref={rules_ref}")

    # ---- N1 negative control: a DIFFERENT function writes none of them ---
    ctor_insns = list(md.disasm(D.read_va(CTOR[0], CTOR[1] - CTOR[0]), CTOR[0]))
    ctor_hits = [i.address for i in ctor_insns if abs_addr(i, 0) in write_sites]
    check("N1", not ctor_hits,
          f"负控（不同函数）：构造器 0x{CTOR[0]:08X} 对 18 个镜像全局 0 次写入",
          "\n".join(f"0x{a:08X}" for a in ctor_hits))

    # ---- N2 negative control: a fabricated global ----------------------
    fake = 0x00A8B25D     # Money+1: a real address expression, never used
    fake_raw = raw_text.count(struct.pack("<I", fake))
    fake_dec = mem_refs.get(fake, 0) + imm_refs.get(fake, 0)
    check("N2", fake_raw == 0 and fake_dec == 0,
          f"负控：伪造全局 0x{fake:08X} 在两口径下都是 0",
          f"raw={fake_raw} dec={fake_dec}")

    # ---- N3 truncation control -----------------------------------------
    trunc_hi = 0x0052D1FE   # stops just before the last three copies
    trunc = list(md.disasm(D.read_va(LOADER_ENTRY, trunc_hi - LOADER_ENTRY), LOADER_ENTRY))
    trunc_stores = [i for i in trunc if BLOCK_LO <= i.address < trunc_hi
                    and is_abs_store(i) is not None]
    check("N3", len(trunc_stores) < 18,
          f"负控（截断）：窗口止于 0x{trunc_hi:08X} 时只得 {len(trunc_stores)} 条，"
          f"证明边界确实决定结论",
          f"trunc_stores={len(trunc_stores)}")

    # ---- result ---------------------------------------------------------
    npass = sum(1 for _t, ok, _m, _d in RESULTS if ok)
    ntot = len(RESULTS)
    print(f"\n=== {npass}/{ntot} PASS ===")
    if npass != ntot:
        print("失败项：")
        for t, ok, m, _d in RESULTS:
            if not ok:
                print(f"  {t}: {m}")
        return 1
    print("EXIT=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
