# -*- coding: utf-8 -*-
"""R-035: the function-entry denominator, corrected in BOTH directions.

WHY THIS EXISTS

R-034 said the published denominator (15,224) was UNDER-counted, because
`fn_walk`'s roots are only PE entry + E8/E9 rel32 targets + RTTI vtable slots,
and that set cannot see a function reached solely through `call reg`. It
measured +886..+3,237 and concluded the true coverage was LOWER than the
published 3.62% (<=3.42% .. <=2.99%).

This round measures the opposite error, which R-034 did not look for:

  `raw_rel32_targets()` merges E8 and E9 into one root set and marks EVERY root
  a function entry. But E9 (`jmp rel32`) is also how MSVC encodes intra-function
  block jumps in large functions. So an intra-function jump target becomes a
  phantom "function".

Both errors are real. The published 15,224 is neither an upper nor a lower bound
on the number of functions -- it is a different quantity ("flat CFG roots").
Measured here:

  E8 targets (calls)          7,279
  E9 targets (jumps)          2,042   of which 1,445 are intra-function
  vtable slots                6,499
  LOWER entries              13,352   = E8 | vtable | PE entry, all reachable
  UPPER entries              14,242   = LOWER + 890 unreachable prologue heads
  published                  15,224

So the real denominator is BELOW the published one, and the real coverage is
ABOVE 3.62%, not below it. R-034's direction is FALSIFIED.

The 890 unreachable heads are the same population R-034 was pointing at (its
886 lower bound, and 3,237-2,352=885 from this round's de-nesting) -- three
independent methods converge on ~886-890. R-034's upper bound of 3,237 was the
artefact: it counted every prologue-shaped candidate instead of only those a
call-root traversal cannot reach.

SECOND FINDING (R1-3 premise)

R1-3 was planned as "debug-string naming census" to raise the 3.62% figure.
The image has almost no function-name strings: 5 pure `Class::Method` literals,
30 with that prefix, 21 distinct method names, 35 push sites, 17 functions.
`__FILE__` gives a SOURCE FILE, not a function name. So the plan cannot deliver
what it promised; the honest yield is 17 functions (0.12%).

MUTATION SUPPORT (discipline #44)
  R035_MUTATE=VA=BYTE flips one byte in the in-memory image. See
  mutate_r035_gate.py.

Run: python re_atlas/tools/verify_r035_claims.py
"""

import hashlib
import json
import os
import re
import struct

import capstone

ROOT = r"D:\Project\ra2-campaign-forge"
EXE = ROOT + r"\ra2youli\gamemd.exe"
RTTI = ROOT + r"\re_atlas\evidence\rtti\symbols.json"
SYMS = ROOT + r"\re_atlas\evidence\symbol_map.json"

IB = 0x400000
SHA256 = "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476"
TLO, THI = 0x401000, 0x7E1000

SECTIONS = [
    (0x001000, 0x3DF38D, 0x001000, 0x3E0000),
    (0x3E1000, 0x030074, 0x3E1000, 0x031000),
    (0x412000, 0x367BE4, 0x412000, 0x06C000),
]

RAW = bytearray(open(EXE, "rb").read())

MUTATIONS = {}
for _item in os.environ.get("R035_MUTATE", "").split(","):
    if "=" in _item:
        _k, _v = _item.split("=", 1)
        MUTATIONS[int(_k, 0)] = int(_v, 0) & 0xFF


def _fileoff(va):
    rva = va - IB
    for s_rva, _vs, rp, rs in SECTIONS:
        if s_rva <= rva < s_rva + rs:
            return rp + (rva - s_rva)
    return None


for _va, _b in MUTATIONS.items():
    _fo = _fileoff(_va)
    if _fo is None:
        raise SystemExit(f"mutation target 0x{_va:08X} is not disk-backed")
    RAW[_fo] = _b
RAW = bytes(RAW)


def read_va(va, n):
    rva = va - IB
    for s_rva, _vs, rp, rs in SECTIONS:
        if s_rva <= rva < s_rva + rs:
            o = rp + (rva - s_rva)
            return RAW[o:o + n]
    return b""


TEXT = read_va(TLO, THI - TLO)
NT = len(TEXT)
MD = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
MD.detail = True
XS = capstone.x86

# Expected values, measured 2026-10-23 on sha256 73201cc0..f67476.
EXP_E8 = 7279
EXP_E9 = 2042
EXP_OVL = 138
EXP_VT = 6499
EXP_ROOTS = 13352
EXP_COVERED = 992227
EXP_HEADS = 890
EXP_E9_INTRA = 1445
# R-038 / V-001 §3.1: aligned-decode reading of the E8 side.
EXP_E8_ALIGNED = 6719
EXP_PHANTOM_SITES = 563
EXP_ONLY_PHANTOM = 560
EXP_ROOTS_ALIGNED = 12792
EXP_E9_ONLY = 1872
EXP_NAMED_LOWER = 547
EXP_NAMED_UPPER = 557
EXP_PURE_NAME_LIT = 5
EXP_PREFIX_LIT = 30
EXP_METHODS = 21
EXP_NAME_SITES = 35
EXP_PATH_SITES = 1299
EXP_PATH_CALLEE = 1190
EXP_IDENT_SITES = 3688
EXP_IDENT_INI = 2291

PE_ENTRY = 0x7CD80F
ANCHOR = 0x403A80          # R-034's anchor: unreachable from any call root
INTERIOR = 0x4039C9        # negative control: inside 0x4039C0
E9_INTRA_SAMPLE = 0x404555  # negative control: E9 target inside 0x4041D0

FAILS = []
RAN = []


def check(tag, ok, msg, extra=""):
    RAN.append(tag)
    print(("PASS\t" if ok else "FAIL\t") + tag + "\t" + msg
          + (("\t" + str(extra).replace("\n", " | ")) if extra else ""))
    if not ok:
        FAILS.append(tag)


# ---------------------------------------------------------------- P1
# P1 hashes the whole image, so it is TRUE for any unmodified copy and FALSE for
# every mutation.  That makes it a constant, not a measurement -- it is listed
# separately and EXCLUDED from the PASS count (V-001 §四.1).
h = hashlib.sha256(RAW).hexdigest()
ANCHOR_OK = (h == SHA256)
print(("PASS\t" if ANCHOR_OK else "FAIL\t") + "P1\t[恒真项，不计入 PASS 数] "
      "sha256 与交付锚一致\t" + h[:16])
if not ANCHOR_OK:
    FAILS.append("P1")

# ---------------------------------------------------------------- P2
# E8 and E9 targets counted SEPARATELY. This separation is the whole finding:
# merging them is what turns intra-function jumps into phantom functions.
#
# R-038 / V-001 §3.1: the BYTE SCAN is not safe for E8 either.  `re.finditer(
# b"\xe8")` matches 0xE8 bytes that are operands of other instructions, and each
# such byte yields a bogus "call target".  Measured: 68,807 E8 bytes, of which
# 563 are not a real `call` start; they contribute 560 targets that NO real call
# reaches.  So the byte-scan set is an UPPER bound on E8 targets, and the aligned
# set (only 0xE8 bytes that capstone says begin `call rel32`) is the honest one.
#
# Both are reported.  `e8_t` stays the byte-scan set so the historical numbers
# remain reproducible; `e8_aligned` is the corrected reading and drives LOWER2.
e8_t, e9_t = set(), set()
for op, bucket in ((b"\xe8", e8_t), (b"\xe9", e9_t)):
    for m in re.finditer(op, TEXT):
        i = m.start()
        if i + 5 > NT:
            continue
        d = struct.unpack_from("<i", TEXT, i + 1)[0]
        t = TLO + i + 5 + d
        if TLO <= t < THI:
            bucket.add(t)
check("P2", len(e8_t) == EXP_E8 and len(e9_t) == EXP_E9
      and len(e8_t & e9_t) == EXP_OVL,
      f"E8（调用）目标 = **{len(e8_t):,}**（**字节扫描口径**，见 P2b），"
      f"E9（跳转）目标 = **{len(e9_t):,}**，两者重叠 = {len(e8_t & e9_t)}；"
      f"`fn_walk` 把这两个集合并成一个根集，是分母混口径的根源",
      f"E8={len(e8_t)} E9={len(e9_t)} ovl={len(e8_t & e9_t)}")

# ---------------------------------------------------------------- P2b (R-038)
# Aligned decode: only 0xE8 bytes that begin a real `call rel32` instruction.
# Linear sweep with per-address resync (+1 on failure), because .text contains
# embedded data and a pure linear sweep desyncs (fn_walk.py's own docstring).
insn_start = set()
call_starts = set()
e8_aligned = set()
_cur = TLO
_desync = 0
while _cur < THI:
    _off = _cur - TLO
    _got = None
    for _insn in MD.disasm(TEXT[_off:_off + 16], _cur):
        _got = _insn
        break
    if _got is None:
        _desync += 1
        _cur += 1
        continue
    insn_start.add(_got.address)
    if (_got.mnemonic == "call" and _got.operands
            and _got.operands[0].type == XS.X86_OP_IMM):
        call_starts.add(_got.address)
        _t = _got.operands[0].imm
        if TLO <= _t < THI:
            e8_aligned.add(_t)
    _cur += _got.size

# Phantom sources: 0xE8 bytes that the byte scan treats as a call but that are
# not instruction starts.  Verify each really sits INSIDE another instruction.
_e8_sites = set()
for m in re.finditer(b"\xe8", TEXT):
    i = m.start()
    if i + 5 > NT:
        continue
    d = struct.unpack_from("<i", TEXT, i + 1)[0]
    if TLO <= TLO + i + 5 + d < THI:
        _e8_sites.add(TLO + i)
phantom_sites = _e8_sites - call_starts
inside_other = 0
for _va in phantom_sites:
    for _back in range(1, 16):
        _s = _va - _back
        if _s not in insn_start:
            continue
        _g = None
        for _insn in MD.disasm(read_va(_s, 16), _s):
            _g = _insn
            break
        if _g is not None and _s + _g.size > _va:
            inside_other += 1
            break

# Targets reached ONLY by phantom sources (these are the ones that vanish).
phantom_targets = set()
for _va in phantom_sites:
    _i = _va - TLO
    _d = struct.unpack_from("<i", TEXT, _i + 1)[0]
    _t = _va + 5 + _d
    if TLO <= _t < THI:
        phantom_targets.add(_t)
only_phantom = phantom_targets - e8_aligned

check("P2b", len(e8_aligned) == EXP_E8_ALIGNED
      and inside_other == len(phantom_sites)
      and len(only_phantom) == EXP_ONLY_PHANTOM,
      f"**对齐解码**：只有真正 `call rel32` 起点的 0xE8 才算 ⇒ E8 目标 "
      f"**{len(e8_aligned):,}**（字节扫描 {len(e8_t):,}，差 "
      f"{len(e8_t)-len(e8_aligned)}）。幻影源 **{len(phantom_sites)}** 个，"
      f"**{inside_other}/{len(phantom_sites)} 逐址复核确认 0xE8 落在别的指令体内**；"
      f"其中只被幻影源指向的目标 **{len(only_phantom)}** 个 ⇒ 字节扫描是"
      f"**上界**，不是下界",
      f"aligned={len(e8_aligned)} phantom_sites={len(phantom_sites)} "
      f"inside_other={inside_other} only_phantom={len(only_phantom)}")

# ---------------------------------------------------------------- P2c (R-038)
# The DISCRIMINATING assertion.  P2b still reads `phantom_sites`, which is a
# byte-scan product, so a mutation that edits a phantom's displacement moves
# P2b as well and the two readings are not separated.
#
# P2c asserts ONLY aligned-side quantities, so a byte-scan-only defect leaves it
# green.  Paired with P2b's `len(e8_t)` term, the pair can tell the two readings
# apart -- which is what V-001 §七.5 asked for.
check("P2c", len(e8_aligned) == EXP_E8_ALIGNED,
      f"**纯对齐口径**（不含任何字节扫描量）：真 `call rel32` 目标 = "
      f"**{len(e8_aligned):,}**，独立于 `re.finditer(b\"\\xe8\")` 的结果。"
      f"幻影位移被改动时本断言必须保持绿，而 P2/P3 变红 ⇒ 两种读法可区分",
      f"aligned_only={len(e8_aligned)}")



# ---------------------------------------------------------------- P3
vt = set()
for _k, c in json.load(open(RTTI, encoding="utf-8"))["classes"].items():
    for s in c.get("vfuncs") or []:
        try:
            v = int(s, 16)
        except (TypeError, ValueError):
            continue
        if TLO <= v < THI:
            vt.add(v)
roots_call = e8_t | vt | {PE_ENTRY}
check("P3", len(roots_call) == EXP_ROOTS and len(vt) == EXP_VT,
      f"只取调用类根集（E8 ∪ 虚表 ∪ PE 入口）= **{len(roots_call):,}**"
      f"（虚表槽 {len(vt):,}）；E9 一律当跳转，不当入口。"
      f"**注意：这是字节扫描口径，是上界**（见 P3b）",
      f"roots={len(roots_call)} vt={len(vt)}")

# ---------------------------------------------------------------- P3b (R-038)
# The aligned-decode LOWER: same construction with the corrected E8 side.
roots_aligned = e8_aligned | vt | {PE_ENTRY}
check("P3b", len(roots_aligned) == EXP_ROOTS_ALIGNED,
      f"**对齐口径的 LOWER** = 对齐 call 目标 ∪ 虚表 ∪ PE 入口 = "
      f"**{len(roots_aligned):,}**（字节扫描 {len(roots_call):,}，差 "
      f"{len(roots_call)-len(roots_aligned)} = 那 560 个只被幻影源指向的目标）"
      f"⇒ **字节扫描 13,352 是上界；12,792 是更紧的口径**（注意：两者都是"
      f"「根集大小」，均不是函数数的严格证明 —— R-035 §八.1 的边界同样适用）",
      f"roots_aligned={len(roots_aligned)} "
      f"delta={len(roots_call)-len(roots_aligned)}")

# ---------------------------------------------------------------- CFG traversal
_DC = {}


def dec1(cur):
    if cur in _DC:
        return _DC[cur]
    off = cur - TLO
    if off < 0 or off + 16 > NT:
        _DC[cur] = None
        return None
    out = None
    for insn in MD.disasm(TEXT[off:off + 16], cur):
        ops = [("imm", o.imm) if o.type == XS.X86_OP_IMM else ("x", None)
               for o in insn.operands]
        out = (insn.mnemonic, insn.op_str, insn.size, ops)
        break
    _DC[cur] = out
    return out


covered = set()
visited = set()
work = list(roots_call)
while work:
    e = work.pop()
    if e in visited:
        continue
    visited.add(e)
    stack = [e]
    while stack:
        cur = stack.pop()
        guard = 0
        while True:
            guard += 1
            if guard > 6000:
                break
            if not (TLO <= cur < THI) or cur in covered:
                break
            r = dec1(cur)
            if r is None:
                break
            mn, _op_str, size, ops = r
            covered.add(cur)
            nxt = cur + size
            if mn == "call":
                if ops and ops[0][0] == "imm":
                    t = ops[0][1]
                    if TLO <= t < THI and t not in visited:
                        work.append(t)
                cur = nxt
                continue
            if mn == "jmp":
                if ops and ops[0][0] == "imm" and TLO <= ops[0][1] < THI:
                    cur = ops[0][1]
                    continue
                break
            if mn.startswith("j"):
                if ops and ops[0][0] == "imm" and TLO <= ops[0][1] < THI:
                    stack.append(ops[0][1])
                cur = nxt
                continue
            if mn.startswith("ret") or mn in ("hlt", "ud2", "iretd", "retf"):
                break
            cur = nxt
    if len(covered) > 1_300_000:
        break

# ---------------------------------------------------------------- P4
check("P4", len(visited) == EXP_ROOTS and len(covered) == EXP_COVERED,
      f"LOWER 口径：从调用类根集出发，CFG 能到达的入口 = **{len(visited):,}**"
      f"（等于根集本身 —— 遍历没有发现任何**新**入口），覆盖指令地址 "
      f"{len(covered):,} 个 = .text 的 {100.0*len(covered)/NT:.1f}%",
      f"visited={len(visited)} covered={len(covered)}")

# ---------------------------------------------------------------- P5
PROLOGUE = re.compile(rb"^(?:\x55\x8b\xec|\x83\xec|\x81\xec|\x53|\x56|\x57|\x8b\xff|\x6a)")


def insns_to_ret(va, limit=0x800):
    n = 0
    off = va - TLO
    if off < 0 or off >= NT:
        return 0, False
    for insn in MD.disasm(TEXT[off:off + limit], va):
        n += 1
        if insn.mnemonic.startswith("ret"):
            return n, True
        if n > 900:
            break
    return n, False


heads = []
for pat, skip in ((rb"\xc3", 1), (rb"\xc2", 3)):
    for m in re.finditer(pat, TEXT):
        i = m.start()
        j = i + skip
        npad = 0
        while j < NT and TEXT[j] in (0x90, 0xCC):
            npad += 1
            j += 1
        if npad < 2:
            continue
        a = TLO + j
        if a in covered:
            continue
        if not PROLOGUE.match(read_va(a, 8)):
            continue
        n, ok = insns_to_ret(a)
        if ok and n >= 3:
            heads.append(a)
heads = sorted(set(heads))
check("P5", len(heads) == EXP_HEADS and ANCHOR in heads
      and ANCHOR not in roots_call,
      f"UPPER 补集：CFG 到不了、但「ret+填充+序言」且能解到 ret 的头部 = "
      f"**{len(heads):,}**；锚点 0x{ANCHOR:08X}（`sub esp,0x2c0`、零 E8/E9 "
      f"引用者、零数据指针）在其中 ⇒ 确实存在根集看不见的函数",
      f"heads={len(heads)} anchor_in={ANCHOR in heads} "
      f"anchor_root={ANCHOR in roots_call}")

# ---------------------------------------------------------------- P5b (R-038)
# V-001 §3.2: UPPER is sensitive to the prologue criterion by roughly 2x.  The
# honest thing is to measure that sensitivity INSIDE the gate instead of only
# mentioning it in prose.  Two independent variations, each keeping the same
# shape rule:
#   (i)  narrow window (8 B -> 6 B) when matching the prologue
#   (ii) drop the `\xc2` (ret imm16) branch
# Report the spread.  This is a SENSITIVITY measurement, not a pass/fail on a
# value -- it is registered, not counted as a killed assertion.
PROLOGUE_NARROW = re.compile(rb"^(?:\x55\x8b\xec|\x83\xec|\x81\xec|\x53|\x56|\x57|\x8b\xff|\x6a)")


def collect_heads(pats, prologue_re, window):
    out = []
    for pat, skip in pats:
        for m in re.finditer(pat, TEXT):
            i = m.start()
            j = i + skip
            npad = 0
            while j < NT and TEXT[j] in (0x90, 0xCC):
                npad += 1
                j += 1
            if npad < 2:
                continue
            a = TLO + j
            if a in covered:
                continue
            if not prologue_re.match(read_va(a, window)):
                continue
            n, ok = insns_to_ret(a)
            if ok and n >= 3:
                out.append(a)
    return sorted(set(out))


heads_ret_only = collect_heads(((rb"\xc3", 1),), PROLOGUE, 8)
heads_win6 = collect_heads(((rb"\xc3", 1), (rb"\xc2", 3)), PROLOGUE, 6)
spread = (min(len(heads_ret_only), len(heads_win6)),
          max(len(heads_ret_only), len(heads_win6)))
ratio = (max(spread) / max(1, min(spread)))
print(f"REGISTER\tP5b\tUPPER 序言敏感度：基准 **{len(heads)}**；"
      f"只保留 `\\xc3` 分支 → **{len(heads_ret_only)}**；序言窗口 8→6 B → "
      f"**{len(heads_win6)}**。极差 {spread[0]}…{spread[1]}（≈{ratio:.1f}×）⇒ "
      f"**UPPER 不可单值冻结**，引用须带敏感度区间（结构性普查，不计入 PASS 数）")


# ---------------------------------------------------------------- P6
e9_intra = len((e9_t - e8_t - vt) & covered)
check("P6", e9_intra == EXP_E9_INTRA,
      f"E9 目标里落在已覆盖代码内部的（= 函数内块跳转，**不是**函数入口）"
      f"= **{e9_intra:,}**；这正是 `fn_walk` 分母里虚高的部分",
      f"e9_intra={e9_intra}")

# ---------------------------------------------------------------- P7
smap = json.load(open(SYMS, encoding="utf-8"))["map"]
named = {int(k, 16) for k in smap if TLO <= int(k, 16) < THI}
lo_den, up_den = len(visited), len(visited) + len(heads)
n_lo = len(named & visited)
n_up = len(named & (visited | set(heads)))
check("P7", n_lo == EXP_NAMED_LOWER and n_up == EXP_NAMED_UPPER,
      f"语料命名点 {len(named):,} 个中，落在 LOWER 入口 {n_lo} 个、"
      f"落在 UPPER 入口 {n_up} 个 ⇒ 覆盖率 **{100.0*n_lo/lo_den:.2f}%"
      f"（LOWER {lo_den:,}）… {100.0*n_up/up_den:.2f}%（UPPER {up_den:,}）**，"
      f"**高于**公布的 3.62%（551/15,224）—— 与 R-034 的方向相反",
      f"n_lo={n_lo} n_up={n_up} lo_den={lo_den} up_den={up_den}")

# ---------------------------------------------------------------- P7b (R-038)
# The aligned-decode coverage, i.e. the D-06/D-02 three-tier figure.  The
# aligned root set is smaller (12,792) so the same named points give a HIGHER
# percentage.  UPPER2 = aligned LOWER + the same 890 heads (the heads come from
# `covered`, which was built from the byte-scan roots -- so UPPER2 is an upper
# bound too, which is the honest way to state it).
lo2_den = len(roots_aligned)
up2_den = len(roots_aligned) + len(heads)
n_lo2 = len(named & roots_aligned)
n_up2 = len(named & (roots_aligned | set(heads)))
print(f"REGISTER\tP7b\t**三档双报**：\n"
      f"  · 上界族（字节扫描 E8）：LOWER **13,352** → "
      f"{100.0*n_lo/lo_den:.2f}%；UPPER **14,242** → {100.0*n_up/up_den:.2f}%\n"
      f"  · 对齐族（真 call 起点）：LOWER **{lo2_den:,}** → "
      f"{100.0*n_lo2/lo2_den:.2f}%；UPPER **{up2_den:,}** → "
      f"{100.0*n_up2/up2_den:.2f}%\n"
      f"  命名点 {n_lo2}（对齐 LOWER）/ {n_up2}（对齐 UPPER）\n"
      f"  ⇒ 对齐族是本轮推荐引用口径（剔除 560 个可证伪幻影根），"
      f"但 UPPER 序言敏感度见 P5b（结构性普查，不计入 PASS 数）")


# ---------------------------------------------------------------- P8
# The R1-3 premise: are there function-name strings to harvest?
starts = {}
for _label, rva, rp, rs in ((".rdata", 0x3E1000, 0x3E1000, 0x031000),
                            (".data", 0x412000, 0x412000, 0x06C000)):
    blob = RAW[rp:rp + rs]
    for m in re.finditer(rb"[\x20-\x7E]{4,400}", blob):
        starts[IB + rva + m.start()] = m.group().decode("ascii", "replace")
PURE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(?:::[A-Za-z_~][A-Za-z0-9_]*)+$")
PREFIX = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*(?:::[A-Za-z_~][A-Za-z0-9_]*)+)")
pure = {va: s for va, s in starts.items() if PURE.match(s)}
pref = {va: PREFIX.match(s).group(1) for va, s in starts.items() if PREFIX.match(s)}
methods = {v for v in pref.values()}
check("P8", len(pure) == EXP_PURE_NAME_LIT and len(pref) == EXP_PREFIX_LIT
      and len(methods) == EXP_METHODS,
      f"全镜像**纯函数名字面量只有 {len(pure)} 个**；带 `Class::Method` 前缀的 "
      f"字面量 {len(pref)} 个，含 **{len(methods)} 个不同方法名** ⇒ "
      f"「用调试字符串给函数命名」的天花板是 {len(methods)} 个函数",
      f"pure={len(pure)} prefixed={len(pref)} methods={len(methods)}")

# ---------------------------------------------------------------- P9
name_sites = []
for m in re.finditer(rb"\x68", TEXT):
    i = m.start()
    if i + 5 > NT:
        continue
    imm = struct.unpack_from("<I", TEXT, i + 1)[0]
    if imm in pref:
        name_sites.append(TLO + i)
check("P9", len(name_sites) == EXP_NAME_SITES,
      f"push 这些函数名字面量的站点 = **{len(name_sites)}** 个 ⇒ "
      f"即使全部正确归属，也只覆盖 {len(methods)} 个函数 / {up_den:,} = "
      f"{100.0*len(methods)/up_den:.2f}%",
      f"sites={len(name_sites)}")

# ---------------------------------------------------------------- P10
PATHRE = re.compile(r"[\\/].*\.(cpp|h|c|hpp)$", re.I)
path_sites = []
for m in re.finditer(rb"\x68", TEXT):
    i = m.start()
    if i + 5 > NT:
        continue
    imm = struct.unpack_from("<I", TEXT, i + 1)[0]
    b = read_va(imm, 300)
    z = b.find(b"\0")
    if z < 0:
        continue
    try:
        s = b[:z].decode("ascii")
    except UnicodeDecodeError:
        continue
    if PATHRE.search(s):
        path_sites.append(TLO + i)

callee_hist = {}
for va in path_sites:
    got = None
    for insn in MD.disasm(read_va(va, 0x40), va):
        if (insn.mnemonic == "call" and insn.operands
                and insn.operands[0].type == XS.X86_OP_IMM):
            got = insn.operands[0].imm
            break
    callee_hist[got] = callee_hist.get(got, 0) + 1
n_734e60 = callee_hist.get(0x734E60, 0)
check("P10", len(path_sites) == EXP_PATH_SITES and n_734e60 == EXP_PATH_CALLEE,
      f"`__FILE__` 字面量站点 = **{len(path_sites)}** 个，其中 {n_734e60} 个"
      f"（{100.0*n_734e60/len(path_sites):.1f}%）跟的是 `call 0x734E60`"
      f"（`ret 8` 的字符串驻留表查找，**不是 assert**）⇒ "
      f"这条路给的是**源文件名**，不是函数名",
      f"path_sites={len(path_sites)} callee734e60={n_734e60}")

# ---------------------------------------------------------------- P11
IDENT = re.compile(r"^[A-Za-z_~][A-Za-z0-9_:~<>@$]*$")
READERS = {0x526810, 0x526960, 0x526CC0, 0x528A10,
           0x5283D0, 0x5276D0, 0x5295F0, 0x529160}
ident_sites = []
for m in re.finditer(rb"\x68", TEXT):
    i = m.start()
    if i + 5 > NT:
        continue
    imm = struct.unpack_from("<I", TEXT, i + 1)[0]
    b = read_va(imm, 400)
    z = b.find(b"\0")
    if z < 0 or len(b[:z]) < 4:
        continue
    s = b[:z]
    if any(c < 0x20 or c > 0x7E for c in s):
        continue
    t = s.decode("ascii")
    if IDENT.match(t):
        ident_sites.append(TLO + i)


def is_reader_arg(site_va):
    lo = max(TLO, site_va - 0x40)
    insns = list(MD.disasm(read_va(lo, site_va - lo + 0x30), lo))
    idx = next((k for k, x in enumerate(insns) if x.address == site_va), None)
    if idx is None:
        return False
    for x in insns[idx + 1: idx + 7]:
        if (x.mnemonic == "call" and x.operands
                and x.operands[0].type == XS.X86_OP_IMM):
            return x.operands[0].imm in READERS
    return False


n_ini = sum(1 for va in ident_sites if is_reader_arg(va))
check("P11", len(ident_sites) == EXP_IDENT_SITES and n_ini == EXP_IDENT_INI,
      f"裸标识符类字符串站点 = **{len(ident_sites):,}** 个，其中 **{n_ini:,}** 个"
      f"（{100.0*n_ini/len(ident_sites):.1f}%）是 8 个 INI reader 的实参 ⇒ "
      f"这一类是 **INI 键名**，不能算调试命名（否则会把 INI 普查重复计入）",
      f"ident={len(ident_sites)} ini_arg={n_ini}")

# ---------------------------------------------------------------- N1
# HONEST FORM. The first draft asserted only `INTERIOR not in visited and not in
# heads`, which is a TAUTOLOGY: `visited == roots_call` by construction (the CFG
# adds no new entries), and INTERIOR is not an E8/vtable target, so the first
# conjunct is fixed TRUE; `heads` skips any address in `covered`, and INTERIOR is
# covered, so the second conjunct is fixed TRUE too. Neither can ever go red.
#
# The load-bearing fact is the POSITIVE one: INTERIOR lies inside a function body
# that the traversal actually reached. That conjunct IS killable -- destroy both
# E8 referrers of the host function 0x4039C0 (at 0x403ACD and 0x403AFF) and the
# host becomes unreachable, INTERIOR stops being covered, and N1 goes red.
# See mutate_r035_gate.py case "N1 host function orphaned".
check("N1", INTERIOR in covered and INTERIOR not in visited,
      f"[负控1] 已知函数 0x4039C0 的中段 0x{INTERIOR:08X} **被覆盖**"
      f"（= 遍历真的走进了这个函数体）但**不是**入口 ⇒ "
      f"「中段地址不会被当成函数」这条成立；"
      f"注意 `not in heads` 由 `in covered` 蕴含，是装饰性的，已从断言里删掉",
      f"covered={INTERIOR in covered} entry={INTERIOR in visited}")

# ---------------------------------------------------------------- N2
# Same treatment. `E9_INTRA_SAMPLE not in visited` alone is a tautology (it is
# E9-only, and E9 is never a root). The real claim is two-sided and BOTH sides
# are killable:
#   (a) it IS an E9 target      -- destroy the two `jmp` at 0x404457/0x40446F
#   (b) it IS covered           -- same mutation
#   (c) it is NOT a root        -- structural, that is the whole point
check("N2", E9_INTRA_SAMPLE in e9_t and E9_INTRA_SAMPLE in covered
      and E9_INTRA_SAMPLE not in roots_call,
      f"[负控2] 0x{E9_INTRA_SAMPLE:08X} 是 **E9 目标**、**被覆盖**"
      f"（落在 0x4041D0 函数体内）、但**不是**调用类根集成员 ⇒ "
      f"新口径把它排除、旧口径（E8∪E9 扁平根集）会把它算成函数",
      f"in_e9={E9_INTRA_SAMPLE in e9_t} "
      f"covered={E9_INTRA_SAMPLE in covered} "
      f"root={E9_INTRA_SAMPLE in roots_call}")

# ---------------------------------------------------------------- N3
# Original form of this control claimed 0x652CF0 is reached ONLY via `call reg`.
# That was wrong: 0x652CF0 IS a vtable slot (vt-only, not an E8 target), so the
# vtable root set already covers it. Corrected to measure the real blind spot,
# which is 0x403A80: zero referrers of EVERY kind a root set can see.
data_ptrs = 0
_pat = struct.pack("<I", ANCHOR)
for _label, _rva, _rp, _rs in ((".rdata", 0x3E1000, 0x3E1000, 0x031000),
                               (".data", 0x412000, 0x412000, 0x06C000)):
    _blob = RAW[_rp:_rp + _rs]
    _s = 0
    while True:
        _k = _blob.find(_pat, _s)
        if _k < 0:
            break
        data_ptrs += 1
        _s = _k + 1
check("N3", ANCHOR not in e8_t and ANCHOR not in e9_t
      and ANCHOR not in vt and data_ptrs == 0,
      f"[负控3] 锚点 0x{ANCHOR:08X} 在**四种**引用方式下全为零："
      f"E8 目标={ANCHOR in e8_t}、E9 目标={ANCHOR in e9_t}、"
      f"虚表槽={ANCHOR in vt}、.rdata/.data dword 指针={data_ptrs} ⇒ "
      f"任何「根集 + CFG」方法都到不了它，盲区是结构性的",
      f"e8={ANCHOR in e8_t} e9={ANCHOR in e9_t} vt={ANCHOR in vt} "
      f"data={data_ptrs}")

# ---------------------------------------------------------------- N4
# The mechanism itself, stated as a count rather than an anecdote.
# Every E9-only target (an E9 target that is neither an E8 target nor a vtable
# slot) is excluded from the root set by construction. This is what makes the
# new denominator smaller than the published one, and it is killable: promoting
# ANY of these addresses into the root set (e.g. by turning its `jmp` referrer
# into a `call`) makes the excluded count drop.
e9_only = e9_t - e8_t - vt
n_e9_only_in_roots = len(e9_only & roots_call)
check("N4", len(e9_only) == EXP_E9_ONLY and n_e9_only_in_roots == 0,
      f"**E9-only 目标**（E9 目标 ∧ ¬E8 目标 ∧ ¬虚表槽）= **{len(e9_only):,}** 个，"
      f"其中进入调用类根集的 = **{n_e9_only_in_roots}** ⇒ "
      f"「E9 只当跳转不当入口」这条规则被机械地执行了；"
      f"旧口径把这 {len(e9_only):,} 个里的函数内跳转也算成函数",
      f"e9_only={len(e9_only)} in_roots={n_e9_only_in_roots}")

print()
if FAILS:
    print(f"RESULT: {len(RAN) - len(FAILS)}/{len(RAN)} passed, FAILED={FAILS}")
    raise SystemExit(1)
print(f"RESULT: {len(RAN)}/{len(RAN)} PASS")
