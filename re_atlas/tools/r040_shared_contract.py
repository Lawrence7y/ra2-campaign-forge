# -*- coding: utf-8 -*-
"""R-040: the P1 shared-library contract (machine-readable), recomputed from bytes.

Charter §3 P1 says: sink the vtable/type/size contract into a form GOAL-3T can
consume directly.  Until now the contract lived in prose (kb/20), text tables
(class_ids.txt) and per-round gates -- every consumer had to re-derive or
re-parse it.  This tool emits ONE json artifact:

  evidence/class_contract.json

Rules of construction (each is also a gate assertion):

  scope     the contract is for the 69 most-derived AbstractClass descendants
            (leaves).  It is NOT a universal "any vtable" contract -- 804
            classes don't even HAVE slot 11/12 and 9 abstract intermediate
            bases return 0 from both slots (R-037).
  ids       vtable[11] callee is `B8 imm32 C3` (`mov eax,imm; ret`) with
            imm in the engine name table's value domain.
  sizes     vtable[12] callee is the same shape.
  engine    the table at 0x816EE0 (74 x {char* name, u32 value}) is the
            authority for the id -> name mapping; it must be strictly
            increasing 0x00..0x49 with no holes.
  stub      the 9 bases' slot 11/12 all point at 0x004C9150, and the bytes
            there are verified as `xor eax,eax; ret` (33 C0 C3) -- pointer
            identity AND callee content (R-037's P6 lesson).

Everything is read from the exe bytes in this run; the json is derived, never
copied from the older evidence files, so a consumer can recompute it line by
line.

MUTATION SUPPORT (discipline #44)
  R040_MUTATE=VA=BYTE[,VA=BYTE...] flips bytes in an in-memory copy only.

Run:  python re_atlas/tools/r040_shared_contract.py > re_atlas/evidence/class_contract.json
Checks print as PASS/FAIL lines on stderr.
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
NAME_TBL, NAME_N = 0x00816EE0, 74
STUB = 0x004C9150

RAW = bytearray(open(EXE, "rb").read())
MUTATIONS = {}
for _item in os.environ.get("R040_MUTATE", "").split(","):
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


def u32(va):
    b = read_va(va, 4)
    return struct.unpack("<I", b)[0] if len(b) == 4 else None


def cstr(va, cap=64):
    b = read_va(va, cap)
    z = b.find(b"\0")
    return (b[:z] if z >= 0 else b[:cap]).decode("latin1")


def mov_eax_imm_ret(fn):
    """The strict shape B8 <imm32> C3; returns imm or None."""
    if fn is None or not (TLO <= fn < THI):
        return None
    b = read_va(fn, 6)
    if len(b) >= 6 and b[0] == 0xB8 and b[5] == 0xC3:
        return struct.unpack_from("<I", b, 1)[0]
    return None


# Expected values, measured 2026-10-23 on sha256 73201cc0..f67476.
EXP_TOTAL = 988
EXP_VT = 954
EXP_LE12 = 804
EXP_DESC = 78
EXP_CONF = 69
EXP_GAP = 9
GAP_NAMES = ["AbstractClass", "AbstractTypeClass", "MissionClass",
             "ObjectClass", "ObjectTypeClass", "RadioClass",
             "TechnoClass", "TechnoTypeClass", "FootClass"]
EXP_STUB_HITS = 9
# known-good controls (byte-read, independent of older evidence)
CONTROLS = {
    "TEventClass": (0x30, 88),
    "HouseClass": (0x0D, 90296),
    "UnitClass": (0x01, 2280),
    "TeamTypeClass": (0x23, 248),
}

RAN = []
STRUCTURAL = []
FAILS = []


def check(tag, ok, msg, extra=""):
    """A byte-pinnable assertion: counted in RAN, must go red under a targeted
    mutation (the mutation suite proves each one can be killed)."""
    RAN.append(tag)
    print(("PASS\t" if ok else "FAIL\t") + tag + "\t" + msg
          + (("\t" + str(extra).replace("\n", " | ")) if extra else ""),
          file=sys.stderr)
    if not ok:
        FAILS.append(tag)


def check_structural(tag, ok, msg, extra=""):
    """A census / partition-identity check over symbols.json or a tautology."""
    RAN.append(tag)
    STRUCTURAL.append(tag)
    print(("PASS\t" if ok else "FAIL\t") + tag + "\t"
          + "[结构性/恒等，不随字节变异变红] " + msg
          + (("\t" + str(extra).replace("\n", " | ")) if extra else ""),
          file=sys.stderr)
    if not ok:
        FAILS.append(tag)


h = hashlib.sha256(RAW).hexdigest()
print(("PASS\t" if h == SHA256 else "FAIL\t")
      + "C1\t[恒真项，不计入 PASS 数] sha256 与交付锚一致\t" + h[:16],
      file=sys.stderr)
if h != SHA256:
    FAILS.append("C1")


# ---------------------------------------------------------------- population
rec = {}
for key, c in json.load(open(RTTI, encoding="utf-8"))["classes"].items():
    nm = c.get("name") or key
    vt = c.get("vtable_va")
    rec[nm] = {"vt": int(vt, 16) if vt else None,
               "n": c.get("vfunc_count") or 0,
               "bases": c.get("bases") or []}

with_vt = sum(1 for r in rec.values() if r["vt"])
le12 = sum(1 for r in rec.values() if r["vt"] and r["n"] <= 12)
# C2 is a STRUCTURAL census over the RTTI dump + image mapping. It cannot be
# killed by an image-byte mutation (the numbers come from symbols.json, not the
# exe), so per v5 §7 it is REGISTERED, not counted among the byte-killing
# assertions.  It still catches arithmetic/registration errors.
check_structural("C2", len(rec) == EXP_TOTAL and with_vt == EXP_VT and le12 == EXP_LE12,
      f"population（结构性普查，不随字节变异变红）：RTTI **{len(rec)}** 类 / "
      f"带虚表 **{with_vt}** / 槽数 ≤12（无槽 11/12）的 **{le12}**",
      f"total={len(rec)} vt={with_vt} le12={le12}")


def descends(nm, target="AbstractClass"):
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


desc = [nm for nm, r in rec.items() if r["vt"] and descends(nm)]

# ---------------------------------------------------------------- engine name table
values = []
names_by_val = {}
tbl_ok = True
for i in range(NAME_N):
    ptr, val = u32(NAME_TBL + 8 * i), u32(NAME_TBL + 8 * i + 4)
    if ptr is None or val is None:
        tbl_ok = False
        break
    names_by_val[val] = cstr(ptr)
    values.append(val)
mono = all(b > a for a, b in zip(values, values[1:]))
# The RIGHT property for "no holes" is SET equality with {0x00..0x49}, NOT
# monotonic storage order.  Measured here (R-040): the table is NOT strictly
# increasing -- index 69 stores Temporal(0x46) and index 70 stores RadSite(0x45),
# a swap.  But the value SET is exactly {0x00..0x49} with 74 distinct entries,
# so "no holes" holds.  kb/20 §1's prose "value 严格递增" is FALSIFIED (the
# claim I originally mirrored into this assertion); the "没有空洞" part holds.
set_complete = (len(values) == 74 and len(set(values)) == 74
                and set(values) == set(range(0x00, 0x4A)))
full = set_complete
check("C4", tbl_ok and full and len(names_by_val) == 74,
      f"引擎名字表 `0x{NAME_TBL:08X}`：**{len(values)}** 项、**{len(set(values))}** "
      f"个不同值、值集合恰为 `{{0x00..0x49}}`（**无空穴成立**）⇒ id↔name 权威表成立。"
      f"存储顺序单调={mono}（**False：RadSite/Temporal 交换 ⇒ kb/20 §1「严格递增」被证伪，**"
      f"**但「无空穴」不受影响**）",
      f"entries={len(values)} distinct={len(set(values))} "
      f"set_complete={set_complete} mono={mono}")


# ---------------------------------------------------------------- per-class reading
def read_pair(r):
    fn11 = u32(r["vt"] + 0x2C)
    fn12 = u32(r["vt"] + 0x30)
    return fn11, fn12, mov_eax_imm_ret(fn11), mov_eax_imm_ret(fn12)


conf, gap = {}, {}
for nm in desc:
    fn11, fn12, cid, size = read_pair(rec[nm])
    if cid is not None and size is not None and cid in names_by_val:
        conf[nm] = {"class": nm, "vtable": rec[nm]["vt"], "slots": rec[nm]["n"],
                    "id": cid, "size": size, "id_fn": fn11, "size_fn": fn12,
                    "engine_name": names_by_val[cid]}
    else:
        gap[nm] = rec[nm]

ids = [c["id"] for c in conf.values()]
check("C3", len(conf) == EXP_CONF and len(set(ids)) == EXP_CONF
      and all(0x01 <= i <= 0x49 for i in ids),
      f"符合契约的叶子类 **{len(conf)}** 个；id 去重 **{len(set(ids))}**、"
      f"值域 `0x{min(ids):02X}..0x{max(ids):02X}`、与名字表互映 **0 冲突**",
      f"conf={len(conf)} ids={len(set(ids))} "
      f"range=0x{min(ids):02X}..0x{max(ids):02X}")

# stub: pointer identity AND callee content (R-037's P6 lesson), tested against
# the 9 KNOWN base names directly -- NOT against the derived `gap` set (which is
# `desc minus conf`, so a mutation that reclassifies any conforming class would
# leak into it and couple this check to C3).  Decoupling here means C5 tests the
# stub specifically.
stub_bytes = read_va(STUB, 3)
stub_hits = 0
gap_names_ok = True
for nm in GAP_NAMES:
    r = rec.get(nm)
    if not r or not r["vt"]:
        gap_names_ok = False
        continue
    fn11, fn12 = u32(r["vt"] + 0x2C), u32(r["vt"] + 0x30)
    if fn11 == STUB and fn12 == STUB:
        stub_hits += 1
    else:
        gap_names_ok = False
check("C5", gap_names_ok and stub_hits == EXP_GAP
      and stub_bytes == b"\x33\xc0\xc3",
      f"9 个抽象中间基类（逐个具名核对={gap_names_ok}）槽 11/12 同指 "
      f"`0x{STUB:08X}`（命中 {stub_hits}/9），**且该处字节实测 "
      f"`{stub_bytes.hex()}` = `xor eax,eax; ret`** ⇒ 指针与内容双钉",
      f"names_ok={gap_names_ok} stub_hits={stub_hits} "
      f"bytes={stub_bytes.hex()}")


is_base = {}
for nm, r in rec.items():
    for b in r["bases"]:
        if b != nm:
            is_base.setdefault(b, []).append(nm)
bases_in_conf = [nm for nm in conf if is_base.get(nm)]
outside = [nm for nm, r in rec.items()
           if r["vt"] and r["n"] > 12 and not descends(nm)
           and (lambda p: p[2] is not None and p[3] is not None
                and p[2] in names_by_val)(read_pair(r))]
union_ok = set(conf) | set(gap) == set(desc)
# C6 encodes the R-037 scope finding: descendant count, the conf/gap partition,
# and "no conformed class is a base" / "no non-descendant conforms".  The
# partition `conf+gap==desc` is a tautology (gap is defined as desc minus conf),
# and the other parts derive from symbols.json's bases, so NO image-byte
# mutation can flip C6 -> it is a STRUCTURAL census, registered not byte-killed.
check_structural("C6", len(desc) == EXP_DESC and len(conf) + len(gap) == len(desc)
      and union_ok and not bases_in_conf and not outside,
      f"作用域闭合（结构性普查，来自 symbols.json 的 bases + 符合集划分恒等，"
      f"不随字节变异变红）：后代 **{len(desc)}** = 符合 {len(conf)} + 中间基类 "
      f"{len(gap)}；符合者中被继承的 **{len(bases_in_conf)}**（全为叶子）；"
      f"后代之外符合的 **{len(outside)}** ⇒ 契约既不外溢也不遗漏",
      f"desc={len(desc)} conf={len(conf)} gap={len(gap)} "
      f"bases_in_conf={len(bases_in_conf)} outside={len(outside)}")


ctrl_fails = []
for nm, (eid, esize) in CONTROLS.items():
    c = conf.get(nm)
    if not c or c["id"] != eid or c["size"] != esize:
        ctrl_fails.append(nm)
check("C7", not ctrl_fails,
      "正对照：TEventClass=(0x30,88) / HouseClass=(0x0D,90296) / "
      "UnitClass=(0x01,2280) / TeamTypeClass=(0x23,248) 字节直读全部吻合"
      "（**R-013 的十进制渲染与尺寸上限两个静默空集陷阱在此复验**）",
      "controls_fail=" + (",".join(ctrl_fails) if ctrl_fails else "-"))

# ---------------------------------------------------------------- emit json
contract = {
    "schema": "ra2-atlas/class-contract/v1",
    "image": {"sha256": SHA256, "file_label": "gamemd.exe (RA2/YR gamemd)"},
    "scope": ("For a CONCRETE (most-derived) AbstractClass instance: "
              "vtable[11] callee = `mov eax,<type_id>; ret`, "
              "vtable[12] callee = `mov eax,<size>; ret`. "
              "Valid for all 69 leaf classes below. NOT valid for the 9 "
              "abstract intermediate bases (their slots 11/12 point at the "
              "stub 0x004C9150 `xor eax,eax; ret` returning 0), and slot "
              "11/12 do not exist at all in the 804 classes with "
              "vfunc_count <= 12."),
    "addresses": {
        "type_id_name_table": f"0x{NAME_TBL:08X}",
        "name_table_entries": NAME_N,
        "abstract_stub": f"0x{STUB:08X}",
        "abstract_stub_bytes": "33c0c3 (xor eax,eax; ret)",
    },
    "population": {"rtti_classes": len(rec), "with_vtable": with_vt,
                   "no_slot_11_12": le12, "abstract_descendants": len(desc)},
    "classes": sorted(conf.values(), key=lambda c: c["id"]),
    "abstract_bases": sorted(gap.keys()),
}
for c in contract["classes"]:
    for k in ("vtable", "id_fn", "size_fn"):
        c[k] = f"0x{c[k]:08X}"
    c["id_hex"] = f"0x{c['id']:02X}"

json.dump(contract, sys.stdout, ensure_ascii=False, indent=1)
sys.stdout.write("\n")

effective = [t for t in RAN]
print(f"\nRESULT: {len(effective) - len(FAILS)}/{len(effective)} PASS"
      + ("" if not FAILS else "  FAILED=" + ",".join(FAILS)),
      file=sys.stderr)
raise SystemExit(1 if FAILS else 0)
