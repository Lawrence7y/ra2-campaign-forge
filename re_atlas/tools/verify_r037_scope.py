# -*- coding: utf-8 -*-
"""R-037: the real scope of the vtable[11]/[12] contract.

WHY THIS EXISTS

kb/20_vtable_contract.md says:

    "任何 AbstractClass* 都能用 vtable[11] 识别真实类型，不需要 RTTI、
     不需要 dynamic_cast。这是写「按类型分派」补丁的正确入口。"

and reports "69 个类全部命中" for vtable[11] = WhatAmI / vtable[12] = GetSize.

The 69 is correct, but it is a count of the classes that PASS, not of the
classes the claim ranges over.  RTTI lists 988 classes, 954 of them with a
vtable.  Before this contract is handed to another line as a shared library,
the denominator has to be stated: 69 out of WHAT, and which classes fall
outside.

WHAT THIS GATE MEASURES

  P2  population: 954 classes have a vtable
  P3  the <=12-slot stratum: 804 classes have vfunc_count <= 12, so slot 11/12
      do not exist for them (the contract is not applicable, not violated)
  P4  the AbstractClass descendants: 78
  P5  of those 78, 69 conform and 9 do not
  P6  the 9 non-conforming are exactly the ABSTRACT INTERMEDIATE BASES
      (AbstractClass, AbstractTypeClass, ObjectClass, ObjectTypeClass,
       MissionClass, RadioClass, TechnoClass, TechnoTypeClass, FootClass)
      -- their slots 11/12 point at the abstract stub 0x004C9150
      (`xor eax,eax; ret`), not at `mov eax,imm; ret`
  P7  no non-AbstractClass class conforms (the 69 are exactly the
      AbstractClass descendants that override the stub)
  P8  every conforming class is a leaf: nothing in the RTTI dump derives
      from it.  So the contract holds for INSTANCES (whose vtable is the
      most-derived class's) and not for the 9 base vtables.

THE HONEST STATEMENT (what kb/20 must say instead of "任何")

  For a concrete (most-derived) AbstractClass instance, vtable[11] is its type
  id and vtable[12] its size.  This is true for all 69 leaf type classes.
  It is NOT true for the 9 abstract intermediate base classes, whose slots
  11/12 are the stub returning 0 -- and those are never instantiated, which is
  why the contract is still safe to use on real objects.

MUTATION SUPPORT (discipline #44)
  R037_MUTATE=VA=BYTE flips one byte in the in-memory image.

Run: python re_atlas/tools/verify_r037_scope.py
"""

import hashlib
import json
import os
import struct
import sys

import capstone

ROOT = r"D:\Project\ra2-campaign-forge"
EXE = ROOT + r"\ra2youli\gamemd.exe"
RTTI = ROOT + r"\re_atlas\evidence\rtti\symbols.json"

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
for _item in os.environ.get("R037_MUTATE", "").split(","):
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


MD = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
MD.detail = True

# Expected values, measured 2026-10-23 on sha256 73201cc0..f67476.
EXP_CLASSES = 988
EXP_WITH_VT = 954
EXP_LE12 = 804
EXP_ABSD = 78
EXP_CONFORM = 69
EXP_GAP = 9
EXP_STUB = 0x004C9150
GAP_NAMES = [
    "AbstractClass", "AbstractTypeClass", "ObjectClass", "ObjectTypeClass",
    "MissionClass", "RadioClass", "TechnoClass", "TechnoTypeClass", "FootClass",
]

FAILS = []
RAN = []


def check(tag, ok, msg, extra=""):
    RAN.append(tag)
    print(("PASS\t" if ok else "FAIL\t") + tag + "\t" + msg
          + (("\t" + str(extra).replace("\n", " | ")) if extra else ""),
          file=sys.stderr)
    if not ok:
        FAILS.append(tag)


# ---------------------------------------------------------------- P1
check("P1", hashlib.sha256(RAW).hexdigest() == SHA256,
      "sha256 与交付锚一致", hashlib.sha256(RAW).hexdigest()[:16])

# ---------------------------------------------------------------- load RTTI
rec = {}
for key, c in json.load(open(RTTI, encoding="utf-8"))["classes"].items():
    nm = c.get("name") or key
    vt = c.get("vtable_va")
    rec[nm] = {"vt": int(vt, 16) if vt else None,
               "n": c.get("vfunc_count") or 0,
               "bases": c.get("bases") or []}

check("P2", len(rec) == EXP_CLASSES
      and sum(1 for r in rec.values() if r["vt"]) == EXP_WITH_VT,
      f"RTTI 总类数 **{len(rec)}**，带虚表 **{sum(1 for r in rec.values() if r['vt'])}** "
      f"⇒ 契约的分母不是 69，先要说清 69 / 954",
      f"classes={len(rec)} with_vt={sum(1 for r in rec.values() if r['vt'])}")


# ---------------------------------------------------------------- readers
def read_slots(vt, n):
    out = []
    for i in range(n):
        b = read_va(vt + 4 * i, 4)
        if len(b) < 4:
            return out
        out.append(struct.unpack("<I", b)[0])
    return out


def imm_at(vt, n, slot):
    """Return the immediate if the callee is `mov eax,imm32; ret`, else None."""
    if n <= slot:
        return None
    ptrs = read_slots(vt, n)
    if slot >= len(ptrs):
        return None
    p = ptrs[slot]
    b = read_va(p, 6)
    if len(b) >= 6 and b[0] == 0xB8 and b[5] == 0xC3:
        return struct.unpack_from("<I", b, 1)[0]
    return None


# ---------------------------------------------------------------- P3
le12 = [nm for nm, r in rec.items() if r["vt"] and r["n"] <= 12]
check("P3", len(le12) == EXP_LE12,
      f"虚表槽数 ≤12 的类 **{len(le12)}** 个（`vfunc_count` 字段独立给出）⇒ "
      f"对它们**根本不存在槽 11/12**，契约是「不适用」而不是「被违反」",
      f"le12={len(le12)}")


# ---------------------------------------------------------------- P4
def descends(nm, target):
    seen, stack = set(), [nm]
    while stack:
        cur = stack.pop()
        if cur in seen:
            continue
        seen.add(cur)
        if cur == target:
            return True
        stack.extend(rec.get(cur, {}).get("bases", []))
    return False


absd = [nm for nm, r in rec.items() if r["vt"] and descends(nm, "AbstractClass")]
check("P4", len(absd) == EXP_ABSD,
      f"`AbstractClass` 后代（有虚表）**{len(absd)}** 个 ⇒ 这才是契约真正的作用域，"
      f"不是 954 也不是 988",
      f"abstract_descendants={len(absd)}")

# ---------------------------------------------------------------- P5
conform = []
gap = []
for nm in absd:
    r = rec[nm]
    i11 = imm_at(r["vt"], r["n"], 11)
    i12 = imm_at(r["vt"], r["n"], 12)
    if i11 is not None and i12 is not None:
        conform.append((nm, i11, i12))
    else:
        gap.append(nm)

check("P5", len(conform) == EXP_CONFORM and len(gap) == EXP_GAP,
      f"78 个后代里 **{len(conform)}** 个符合（槽 11/12 都是 `mov eax,imm; ret`）、"
      f"**{len(gap)}** 个不符合 ⇒ 覆盖率 {len(conform)}/78 = "
      f"{100.0*len(conform)/len(absd):.1f}%，不是 69/69 = 100%",
      f"conform={len(conform)} gap={len(gap)}")

# ---------------------------------------------------------------- P6
# The assertion must pin BOTH facts, not just the pointer value:
#   (a) the 9 classes' slot 11/12 point at the SAME address, and
#   (b) that address is really the stub `xor eax,eax; ret` (33 C0 C3).
# Checking only (a) would survive a mutation that corrupts the stub's bytes,
# because the pointer would still be 0x4C9150 -- that is a gate that cannot
# reject, i.e. decoration.  (a) alone was the first draft and the mutation run
# caught it: `0x4C9150=0x90` left P6 green.
gap_ok = sorted(gap) == sorted(GAP_NAMES)
stub_hits = 0
for nm in gap:
    r = rec[nm]
    ptrs = read_slots(r["vt"], min(r["n"], 13))
    if len(ptrs) > 12 and ptrs[11] == EXP_STUB and ptrs[12] == EXP_STUB:
        stub_hits += 1
stub_bytes = read_va(EXP_STUB, 3)
stub_is_xor_eax_eax_ret = stub_bytes == b"\x33\xc0\xc3"
check("P6", gap_ok and stub_hits == EXP_GAP and stub_is_xor_eax_eax_ret,
      f"9 个不符合的**全部是抽象中间基类**，且槽 11/12 都指向同一地址 "
      f"`0x{EXP_STUB:08X}`（名字集合一致={gap_ok}，指针命中 {stub_hits}/9），"
      f"**且该地址的字节确实是 `xor eax,eax; ret`**（`{stub_bytes.hex()}`）⇒ "
      f"它不是「某个函数」而是抽象桩",
      f"names_match={gap_ok} stub_hits={stub_hits} "
      f"stub_bytes={stub_bytes.hex()} stub_ok={stub_is_xor_eax_eax_ret}")

# ---------------------------------------------------------------- P7
# No class outside AbstractClass descendants may conform.
outside = []
for nm, r in rec.items():
    if not r["vt"] or r["n"] <= 12:
        continue
    if descends(nm, "AbstractClass"):
        continue
    if imm_at(r["vt"], r["n"], 11) is not None and \
       imm_at(r["vt"], r["n"], 12) is not None:
        outside.append(nm)
check("P7", len(outside) == 0,
      f"非 `AbstractClass` 后代里符合的类 = **{len(outside)}** ⇒ 69 恰好等于"
      f"「后代中覆写了桩的叶子类」，契约不外溢",
      f"outside={len(outside)}")

# ---------------------------------------------------------------- P8
is_base = {}
for nm, r in rec.items():
    for b in r["bases"]:
        if b != nm:
            is_base.setdefault(b, []).append(nm)

bases_among_conform = [c[0] for c in conform if is_base.get(c[0])]
check("P8", len(bases_among_conform) == 0,
      f"69 个符合的类里，**被别的类继承的 = {len(bases_among_conform)}** ⇒ "
      f"它们全是叶子（最派生）类；所以契约对**实例**成立（实例的虚表必是最派生的），"
      f"对 9 个中间基类的虚表不成立",
      f"conforming_that_are_bases={len(bases_among_conform)}")

# ---------------------------------------------------------------- report
out = []
P = out.append
P("# R-037 · vtable[11]/[12] 契约的真实作用域")
P("")
P(f"镜像 sha256 `{hashlib.sha256(RAW).hexdigest()}`")
P("")
P("## 一句话")
P("")
P("`kb/20` 说「**任何** `AbstractClass*` 都能用 `vtable[11]` 识别真实类型」。")
P("这句话**对实例成立、对中间基类不成立**，而且 69 这个数字的分母从来不是 69。")
P("")
P("## 漏斗")
P("")
P("| 层 | 类数 | 说明 |")
P("|:--|--:|:--|")
P(f"| RTTI 总类数 | {len(rec)} | `symbols.json` 全部 |")
P(f"| 带虚表 | {sum(1 for r in rec.values() if r['vt'])} | 其余 34 个无虚表 |")
P(f"| 虚表槽数 ≤12 | {len(le12)} | **槽 11/12 不存在**，契约不适用 |")
P(f"| 虚表槽数 >12 | {sum(1 for r in rec.values() if r['vt'] and r['n'] > 12)} | 槽 11/12 存在 |")
P(f"| **`AbstractClass` 后代** | **{len(absd)}** | **契约真正的作用域** |")
P(f"| 其中符合 | **{len(conform)}** | 槽 11/12 都是 `mov eax,imm; ret` |")
P(f"| 其中不符合 | **{len(gap)}** | 全是抽象中间基类，槽 11/12 = 抽象桩 |")
P("")
P("## 9 个不符合的类（抽象中间基类）")
P("")
P("| 类 | 槽数 | 槽 11 | 槽 12 |")
P("|:--|--:|:--|:--|")
for nm in sorted(gap):
    r = rec[nm]
    ptrs = read_slots(r["vt"], min(r["n"], 13))
    s11 = ptrs[11] if len(ptrs) > 11 else None
    s12 = ptrs[12] if len(ptrs) > 12 else None
    P(f"| `{nm}` | {r['n']} | "
      f"{'`0x%08X`' % s11 if s11 else '—'} | {'`0x%08X`' % s12 if s12 else '—'} |")
P("")
P(f"全部指向 `0x{EXP_STUB:08X}`：`xor eax,eax; ret`（`31 C0 C3`）。")
P("它们**从不被实例化**，所以真实对象的虚表永远不会是这 9 张。")
P("")
P("## 可以安全依赖的表述")
P("")
P("> 对**具体的（最派生的）`AbstractClass` 实例**，`vtable[11]` 是类型 ID、")
P("> `vtable[12]` 是实例尺寸。69 个叶子类型类全部成立。")
P("> **不要**把这套读法用在中间基类的虚表上 —— 那 9 张的槽 11/12 返回 0。")
P("")
P("## 69 个符合类的 ID / 尺寸")
P("")
P("| ID | 尺寸 | 类 |")
P("|--:|--:|:--|")
for nm, i11, i12 in sorted(conform, key=lambda x: x[1]):
    P(f"| `0x{i11:02X}` | {i12} | `{nm}` |")

sys.stdout.write("\n".join(out) + "\n")
print(f"\nRESULT: {len(RAN)-len(FAILS)}/{len(RAN)} PASS"
      + ("" if not FAILS else "  FAILED=" + ",".join(FAILS)),
      file=sys.stderr)
raise SystemExit(1 if FAILS else 0)
