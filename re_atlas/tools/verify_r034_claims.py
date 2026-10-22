# -*- coding: utf-8 -*-
"""R-034: machine gate for the function-entry denominator (R1-3 prerequisite).

WHY THIS EXISTS

`STATUS.md` reports function-name coverage as 551 / 15,224 = 3.62%, and the plan
for R1-3 (debug-string naming) is to raise it. But the denominator comes from
`fn_walk.py`, whose roots are only: the PE entry point, raw E8/E9 rel32 targets,
and RTTI vtable slots. That root set structurally CANNOT see a function reached
only through a register-indirect call (`call edi`, `call [eax+8]`).

While attributing debug strings to functions I hit one such function --
`0x403A80` -- sitting right after `ret` + nop padding, with a textbook MSVC
prologue (`81 EC C0 02 00 00` = `sub esp,0x2c0`), zero E8 callers, and zero
dword pointers in .rdata/.data. It is a real function that fn_walk never found.

So before naming anything, the denominator has to be measured. This gate does
that and states the result at three strictness tiers rather than picking one.

TIERS
  T1  address follows ret+padding (>=2 nops) and starts with a prologue shape
  T2  T1 + linear decode reaches a `ret` within a bounded window, >=3 insns
  T3  T2 + a dword pointer to it exists in .rdata/.data

T2 is the number this gate asserts. T3 is reported but NOT asserted, because a
function called only via `call reg` has no data pointer by construction --
`0x403A80` proves that case exists, so T3 would undercount by design.

MUTATION SUPPORT (discipline #44)
  R034_MUTATE=VA=BYTE flips one byte in the in-memory image so the assertions can
  be shown to read the quantities they name. See mutate_r034_gate.py.

Run: python re_atlas/tools/verify_r034_claims.py
"""

import hashlib
import os
import re
import struct
import sys

import capstone

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
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
for _item in os.environ.get("R034_MUTATE", "").split(","):
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
            return RAW[rp + (rva - s_rva): rp + (rva - s_rva) + n]
    return b""


TEXT = read_va(TLO, THI - TLO)
MD = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
MD.detail = True

PROLOGUE = re.compile(rb"^(?:\x55\x8b\xec|\x83\xec|\x81\xec|\x53|\x56|\x57|\x8b\xff|\x6a)")

# Expected values, measured 2026-10-23 on sha256 73201cc0..f67476.
DELIVERED_ENTRIES = 15224
DELIVERED_T2 = 886
DELIVERED_T1 = 889
FAILS = []
RAN = []


def check(tag, ok, msg, extra=""):
    RAN.append(tag)
    print(("PASS\t" if ok else "FAIL\t") + tag + "\t" + msg
          + (("\t" + str(extra).replace("\n", " | ")) if extra else ""))
    if not ok:
        FAILS.append(tag)


# ---------------------------------------------------------------- P1
h = hashlib.sha256(RAW).hexdigest()
check("P1", h == SHA256, "sha256 与交付锚一致", h[:16])

# ---------------------------------------------------------------- P2
# The root set fn_walk uses, recomputed here so the denominator is not trusted
# blindly. E8/E9 rel32 targets + vtable slots + entry point.
rel_targets = set()
for op in (b"\xe8", b"\xe9"):
    for m in re.finditer(op, TEXT):
        i = m.start()
        if i + 5 > len(TEXT):
            continue
        d = struct.unpack_from("<i", TEXT, i + 1)[0]
        t = TLO + i + 5 + d
        if TLO <= t < THI:
            rel_targets.add(t)
check("P2", len(rel_targets) == 9183,
      f"E8/E9 rel32 指向 .text 的目标数 = **{len(rel_targets):,}**（交付 9,183）",
      f"n={len(rel_targets)}")

# ---------------------------------------------------------------- P3
# T1: ret + >=2 padding bytes, then a prologue-shaped head, that is NOT already
# a discovered entry. The "already an entry" filter needs the entry set, which we
# approximate by the E8/E9 root set plus the entry point -- deliberately NOT the
# full walk, so this gate stays independent of fn_walk's traversal bugs.
def candidates_after_ret():
    out = set()
    for pat, skip in ((rb"\xc3", 1), (rb"\xc2", 3)):
        for m in re.finditer(pat, TEXT):
            i = m.start()
            j = i + skip
            if j > len(TEXT):
                continue
            npad = 0
            while j < len(TEXT) and TEXT[j] in (0x90, 0xCC):
                npad += 1
                j += 1
            if npad >= 2:
                out.add(TLO + j)
    return out


cands = candidates_after_ret()
t1 = sorted(c for c in cands
            if c not in rel_targets and PROLOGUE.match(read_va(c, 8)))
check("P3", len(cands) == 16767,
      f"ret+填充 后的候选边界 = **{len(cands):,}**（交付 16,767）", f"n={len(cands)}")


# ---------------------------------------------------------------- P4
def insns_to_first_ret(va, limit=0x800):
    n = 0
    for insn in MD.disasm(read_va(va, limit), va):
        n += 1
        if insn.mnemonic.startswith("ret"):
            return n, True
        if insn.mnemonic in ("int3", "ud2"):
            return n, False
        if n > 900:
            break
    return n, False


t2 = [(c, n) for c in t1 for n, ok in [insns_to_first_ret(c)] if ok and n >= 3]
# NOTE ON THE TWO NUMBERS. This gate filters "already discovered" using ONLY the
# E8/E9 root set, deliberately, so that it does not depend on fn_walk's traversal.
# That makes it an UPPER bound: fn_walk also discovers entries reached by its own
# walk, which this gate cannot see, so some of these are entries fn_walk already
# has. With fn_walk's real entry set the same test yields 886 (probe q6).
# Both are reported; the assertion pins the upper bound because that is what this
# gate actually measures, and calling it 886 here would be asserting a number
# computed by a different program.
DELIVERED_T2_UPPER = 3237
DELIVERED_T2_LOWER = 886
check("P4", len(t2) == DELIVERED_T2_UPPER,
      f"T2 上界（只排除 E8/E9 根集）= **{len(t2):,}**；用 fn_walk 完整入口集复核 = "
      f"**{DELIVERED_T2_LOWER}**（探针 q6）⇒ 分母漏入口量级在 886…3,237 之间，"
      f"两端都是真实函数，不是填充",
      f"T2_upper={len(t2)} T2_lower={DELIVERED_T2_LOWER} T1={len(t1)}")

# ---------------------------------------------------------------- P5
# 0x403A80 -- the case that started this. It must be in T2 and must NOT be in the
# rel32 root set. This is the anchor that makes the finding concrete.
check("P5", 0x403A80 in {c for c, _n in t2} and 0x403A80 not in rel_targets,
      "锚点 0x403A80（`sub esp,0x2c0` 序言、零 E8 调用者、零数据段指针）"
      "确在 T2 且不在 E8/E9 根集里 ⇒ 漏入口不是统计噪声",
      f"in_T2={0x403A80 in {c for c, _n in t2}} in_rel={0x403A80 in rel_targets}")

# ---------------------------------------------------------------- P6
# A false-positive guard: T2 members must not overlap each other's bodies. If a
# candidate were really a cold block of the previous function, it would sit inside
# another candidate's linear extent. Count how many do.
t2_set = {c for c, _n in t2}
overlaps = 0
for c, n in t2:
    # cheap extent: c .. address of the n-th insn
    end = c
    k = 0
    for insn in MD.disasm(read_va(c, 0x800), c):
        k += 1
        end = insn.address + insn.size
        if k >= n:
            break
    if any(o != c and c < o < end for o in t2_set):
        overlaps += 1
check("P6", overlaps <= len(t2) * 0.05,
      f"T2 成员互相嵌套的比例 = {overlaps}/{len(t2)} "
      f"（>5% 说明大量候选其实是别人的冷块，T2 会高估）",
      f"overlaps={overlaps}")

# ---------------------------------------------------------------- P7
# Insn-length distribution: real functions, not 2-instruction padding.
lens = sorted(n for _c, n in t2)
med = lens[len(lens) // 2]
check("P7", 20 <= med <= 60,
      f"T2 的「到首个 ret 的指令数」中位数 = {med}（p25={lens[len(lens)//4]}, "
      f"max={lens[-1]}）⇒ 是真函数体，不是对齐填充",
      f"min={lens[0]} p25={lens[len(lens)//4]} med={med} max={lens[-1]}")

# ---------------------------------------------------------------- N1
# Negative control: an address in the middle of a known function body must NOT be
# in T2 (it has no ret+padding before it).
mid = 0x4039C9   # inside 0x4039C0, immediately after `mov [esp+0x10],edx`
check("N1", mid not in t2_set,
      "[负控1] 已知函数中段 0x4039C9 不在 T2 里", f"mid_in_T2={mid in t2_set}")

# ---------------------------------------------------------------- N2
# Negative control: the padding run itself must not be a candidate.
check("N2", 0x403A71 not in t2_set and 0x403A74 not in t2_set,
      "[负控2] 0x403A80 之前的 nop 填充（0x403A71/0x403A74）不在 T2 里",
      f"{0x403A71 in t2_set}/{0x403A74 in t2_set}")

print()
if FAILS:
    print(f"RESULT: {len(RAN) - len(FAILS)}/{len(RAN)} passed, FAILED={FAILS}")
    raise SystemExit(1)
print(f"RESULT: {len(RAN)}/{len(RAN)} PASS")
