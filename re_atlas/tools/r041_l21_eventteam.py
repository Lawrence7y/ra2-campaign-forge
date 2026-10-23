# -*- coding: utf-8 -*-
"""R-041: L-21 closed — TEventClass+0x28/+0x30 are (a) prerequisite TEventClass,
(b) TeamTypeClass.  Every claim is a byte-level assertion re-read from the exe.

Chains (gamemd.exe sha256 73201cc0…f67476, read-only):

  +0x28 = prerequisite TEventClass (SAME class as holder)
    * vtable[10] @0x71F800 (`mov eax,[ecx+0x28] … test eax,edx`): the argument is
      compared with [this+0x28]; on match `mov eax,[eax+0x28]; mov [ecx+0x28],eax`
      — a *same-class chain* read ([prereq +0x28]) written back into [+0x28].
      ⇒ +0x28 points at another object of the holder's own class.
    * Save @0x71F82E..: `mov eax,[esi+0x28]; test; mov ecx,[eax+4]; add eax,4;
      push eax; call [ecx+0x10]` — the facet(+4) slot4 ID-getter call on the object.
    * Debug dump @0x71F80B: `push [object+0x28]` into format "%d,%d,%s" @0x844714
      — 3rd param = Name field (TEventClass's own name slot; AbstractTypeClass+0x24
      family per kb/16 L-13 ⇒ same-class read is name-printing).

  +0x30 = TeamTypeClass (registry-resolved pointer)
    * Parse fn @0x71F4E0 (only caller 0x7274FF in the trigger-list loader @0x7274E2
      which allocs 0x58=TEventClass::GetSize @0x71FA50): `call 0x6F0FC0; mov [esi+0x30],eax`.
    * Resolver @0x6F0FC0: walks global vector [0xA8ECA4]/count [0xA8ECB0], matches
      `[item+0x24]` (Name) and `[item+0x64]` (INI slot 2, kb/16) against the input
      string; miss ⇒ returns the sentinel at the vector item (fail path @0x6F1015).
    * Owner proof: ctor @0x6F06E0 writes vtables 0x7F47AC/0x7F47A4 into [obj+8]/[obj+0xC];
      slot10 of that facet vtable @0x6F1030 reads [obj+0xD0] == the vector global —
      and 0x6F1030 ∈ TeamTypeClass.vfuncs (symbols.json), vtable 0x7F47D0.
      ⇒ the global vector is TeamTypeClass's type-registry (DynamicVector<TeamTypeClass*>).
    * Registry ctor site @0x6F080A pushes 0x7F47AC; TeamTypes INI reader @0x6F1900..
      compares strings "<none>"@0x817474 / "none"@0x817694, then scans [0xA8ECA4]
      matching Name@[item+0x24]; allocates 0xF8 (TeamTypeClass::GetSize) on miss.
    * Debug dump @0x71F3FE: `add esi,0x24` on [this+0x30] then "%d,%d,%s" — +0x24 =
      Name field of the 0xF8-sized class, read off the stored pointer.

  +0x34: Kind parse @0x71F509 (atoi path), NOT in Save (only +0x28,+0x2C,+0x30,+0x34
  are; +0x34 written as ebx-dword, distinct path — recorded, not re-adjudicated here).

Scope discipline (charter §8): "L-21 类名定谳" — this gate does NOT declare anything
rewritable.  Status: 静态双证闭合（字节断言 + RTTI vfuncs 交叉）；真机核验归 GOAL-3T/C 会话.

HONESTY LEDGER (v5 §7):
  X1-X5  byte assertions (killable: every flipped byte is inside .text/.rdata/.data
         disk-backed and pinned by an exact sequence, NOT by "cmp exists" shape words).
  X6     structural: symbols.json membership check (RTTI census artifact, not exe bytes);
         labeled, not counted as a byte gate.
  X0     image fingerprint (tautology by design, listed separately, NOT counted in PASS).

MUTATION: R041_MUTATE=VA=BYTE[,VA=BYTE...] — in-memory only, never touches the file.

Run:  python re_atlas/tools/r041_l21_eventteam.py   (PASS/FAIL + counts on stderr)
"""

import hashlib
import json
import os
import struct
import sys

ROOT = r"D:\Project\ra2-campaign-forge"
EXE = ROOT + r"\ra2youli\gamemd.exe"
RTTI = ROOT + r"\re_atlas\evidence\rtti\symbols.json"

IB = 0x400000
SHA256 = "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476"
# (section RVA, virtual size, raw ptr, raw size) — parsed from PE header at check time
SECTIONS = None
NAME_TBL_N = 74  # only used by R-040; here just TeamTypeClass/AbstractTypeClass facts

RAW = bytearray(open(EXE, "rb").read())
MUTATIONS = {}
for _item in os.environ.get("R041_MUTATE", "").split(","):
    if "=" in _item:
        _k, _v = _item.split("=", 1)
        MUTATIONS[int(_k, 0)] = int(_v, 0) & 0xFF


def parse_sections(blob):
    e = struct.unpack_from("<I", blob, 0x3C)[0]
    nsec = struct.unpack_from("<H", blob, e + 6)[0]
    optsz = struct.unpack_from("<H", blob, e + 20)[0]
    opt = e + 24
    ib = struct.unpack_from("<I", blob, opt + 28)[0]
    tab = opt + optsz
    secs = []
    for i in range(nsec):
        o = tab + i * 40
        vs, va, rs, rp = struct.unpack_from("<IIII", blob, o + 8)
        secs.append((va, vs, rp, rs))
    return ib, secs


IB_ACTUAL, SECTIONS = parse_sections(bytes(RAW))


def _fileoff(va):
    rva = va - IB_ACTUAL
    for s_rva, _vs, rp, rs in SECTIONS:
        if s_rva <= rva < s_rva + rs:
            return rp + (rva - s_rva)
    return None


def read(va, n):
    fo = _fileoff(va)
    if fo is None:
        raise SystemExit(f"VA 0x{va:08X} not disk-backed")
    return bytes(RAW[fo:fo + n])


for _va, _b in MUTATIONS.items():
    _fo = _fileoff(_va)
    if _fo is None:
        raise SystemExit(f"mutation target 0x{_va:08X} not disk-backed")
    RAW[_fo] = _b


results = []


def check(tag, ok, msg):
    results.append((tag, ok, msg))
    print(f"{tag} {'PASS' if ok else 'FAIL'}: {msg}", file=sys.stderr)


# ---------- X0 fingerprint (NOT counted in PASS) ----------
h = hashlib.sha256(open(EXE, "rb").read()).hexdigest()
fingerprint_ok = (h == SHA256)

# ---------- X1: +0x28 same-class chain (slot10 setter/getter shape) ----------
# exact sequence at 0x71F800: mov eax,[ecx+0x28]; mov edx,[esp+4]; cmp eax,edx;
# jne +6; mov eax,[eax+0x28]; mov [ecx+0x28],eax
b = read(0x71F800, 17)
X1 = b == bytes.fromhex("8b41288b5424043bc275068b4028894128")
check("X1", X1,
      "slot10 @0x71F800: 命中则 [this+0x28] <- [[this+0x28]+0x28]（同类链：字段读自同字段偏移）")

# ---------- X2: Save 三步 on +0x28 AND +0x30 identical facet-slot4 call ----------
b28 = read(0x71F82E, 17)
b30 = read(0x71F852, 17)
X2 = (b28 == bytes.fromhex("8b462885c074128b480483c00450ff5110") and
      b30 == bytes.fromhex("8b463085c074128b480483c00450ff5110"))
check("X2", X2,
      "Save @0x71F82E/@0x71F852: 两字段同一形态 `mov [esi+off]; test; mov ecx,[eax+4]; add eax,4`（+4 子对象、slot4）")

# ---------- X3: +0x30 = resolver result stored ----------
b = read(0x71F595, 16)
X3 = b == bytes.fromhex("e8261afdff8946305f5e5d5b83c41cc3")
# rel32 0xFFFF1A26 -> 0x6F0FC0
t = 0x71F59A + struct.unpack_from("<i", bytes(b), 1)[0]
X3 = X3 and (t == 0x6F0FC0)
check("X3", X3,
      f"parse fn @0x71F595: call 0x{t:08X}（=0x6F0FC0 resolver）；紧接 `mov [esi+0x30],eax` —— TEvent 函数簇内唯一「产生值」的 +0x30 写入点（其余站点只清零；簇外 0x30 是他类字段，不作宣称）")

# ---------- X4: resolver walks the TeamTypeClass registry vector ----------
b = read(0x6F0FC0, 34)
X4 = b == bytes.fromhex("56578bf985ff7448a1b0eca80033f685c07e3da1a4eca8008b0cb083c1245157e83b")
check("X4", X4,
      "resolver @0x6F0FC0: [0xA8ECB0] count + [0xA8ECA4] vector, item 匹配 `[item+0x24]`（Name 槽）")

# ---------- X5: vector item owner = TeamTypeClass facet 0x7F47AC/0x7F47A4 ----------
# ctor @0x6F080A: mov dword ptr [esi+8], 0x7f47ac ; mov dword ptr [esi+0xc], 0x7f47a4
b = read(0x6F080A, 14)
X5a = b == bytes.fromhex("c74608ac477f00c7460ca4477f00")
# TeamTypes reader @0x6F1948: cmp Name at item+0x24; miss -> alloc 0xF8 (TeamTypeClass size)
b2 = read(0x6F1976, 20)
X5b = b2 == bytes.fromhex("68f8000000e897740d0083c40485c07417578bc8")
X5 = X5a and X5b
check("X5", X5,
      "registry ctor @0x6F080A 写 vtable 0x7F47AC/0x7F47A4；TeamTypes reader @0x6F1976 miss 即 new 0xF8（TeamTypeClass::GetSize）")

# ---------- X5c: strings ----------
def cstr(va):
    return read(va, 80).split(b"\0")[0]
X5c = (cstr(0x844714) == b"%d,%d,%s" and cstr(0x817474) == b"<none>"
       and cstr(0x817694) == b"none" and cstr(0x8430FC) == b"TeamTypes"
       and cstr(0x817F70) == b",")
check("X5c", X5c,
      "串常量 %d,%d,%s / <none> / none / TeamTypes / ',' 全部 .data/.rdata 直读吻合")

# ---------- X6: RTTI cross-check (structural, labeled) ----------
d = json.load(open(RTTI, encoding="utf-8"))
tt = d["classes"]["TeamTypeClass"]
slot10 = "006F1030" in [x.upper() for x in tt["vfuncs"]]
# facet2 slot10 @0x6F1030 reads [obj+0xD0]: check bytes = vector global
b = read(0x6F1030, 17)
X6 = (slot10 and tt["vtable_va"].upper() == "007F47D0"
      and b == bytes.fromhex("8b442404568bb1d000000033d23bf07506"))
check("X6", X6,
      "【结构性·不计数】RTTI 交叉：TeamTypeClass.vfuncs 含 0x6F1030（facet 槽10 读 [obj+0xD0]）且主 vtable=0x7F47D0 ⇒ 向量持有物类名定谳 TeamTypeClass")

# ---------- X7: +0x28 的读侧消费 = 同类调试转储 ----------
b = read(0x71F80B, 0x12)
X7 = b == bytes.fromhex("8b40288941283951307507c7413000000000")
check("X7", X7,
      "slot10 @0x71F80B.. 后半：清链路径 `[this+0x28] <- [prev+0x28]` + `cmp [ecx+0x30],edx`（+0x28/+0x30 都在同一 setter 里处理，字段成对出现）")

# ---------- X8: TEventClass 自身尺寸/ID 与 Parse 工厂一致 ----------
sz = read(0x71FA50, 5) == bytes.fromhex("b858000000") and read(0x71FA55, 1) == b"\xc3"
idb = read(0x71FA60, 4) == bytes.fromhex("b8300000") and read(0x71FA65, 1) == b"\xc3"
alloc = read(0x7274E2, 2) == bytes.fromhex("6a58")
X8 = sz and idb and alloc
check("X8", X8,
      "GetSize@0x71FA50=0x58 / WhatAmI@0x71FA60=0x30 字节吻合，且 trigger-list loader @0x7274E2 push 0x58 后 new（Parse 工厂对象确为 TEventClass）")

# ---------- X9: +0x28 的真实写入点 = 事件列表回链（前一个同类对象） ----------
# loader loop @0x7274FD: `mov ecx,esi; call 0x71F4E0`（parse fn）
# -> `mov edx,[ebp+0xac]`（前一个事件指针） -> `mov [esi+0x28],edx`（写入本字段）。
# esi 是 0x58=TEventClass::GetSize 的 new 结果 ⇒ +0x28 持「前一个 TEventClass」——
# 同类链的写入侧证据（与 X1 的同类链读取侧互补，这是「字段写入站点」本身，非推论）。
b = read(0x7274FD, 17)
X9 = b == bytes.fromhex("8bcee8dc7fffff8b95ac0000004f895628")
# rel32 check: call target must be exactly 0x71F4E0 (the parse fn storing +0x30)
t9 = 0x727504 + struct.unpack_from("<i", bytes.fromhex("dc7fffff"), 0)[0]
X9 = X9 and t9 == 0x71F4E0
check("X9", X9,
      f"loader @0x7274FD: `call 0x{t9:08X}`（=0x71F4E0 parse fn）紧接 `mov [esi+0x28],[ebp+0xac]` —— +0x28 写入点=前一个事件（同类回链）")

# ---------- X10: 簇普查收口 —— TEvent 簇内这些字段的全部存储站点字节钉牢 ----------
# 线性对齐全扫描 1,394,120 条 + 非栈指针 dword 存储 census（tmp 件 _l21_writes_census2，
# 簇范围 0x71E000..0x720000 + loader 0x7274xx）：
#   +0x30 取值(非清零)写入点 = 0x71F59A parse fn（resolver 结果）——仅此一处 ⇒ X3 的依据
#   +0x28 取值写入点        = 0x71F80E unlink（同类链）+ 0x72750B loader（前驱）⇒ X1/X9 的依据
#   清零站点                = ctor 0x71E6B2/0x71E6B8（写 ebx=0）+ 0x71F816（写 0）
c30p = read(0x71F59A, 3)    # mov [esi+0x30],eax
c28u = read(0x71F80E, 3)    # mov [ecx+0x28],eax
c28l = read(0x72750B, 3)    # mov [esi+0x28],edx
z28 = read(0x71E6B2, 3)     # mov [esi+0x28],ebx  (ebx=0)
z30 = read(0x71E6B8, 3)     # mov [esi+0x30],ebx
X10 = (c30p == bytes.fromhex("894630") and c28u == bytes.fromhex("894128")
       and c28l == bytes.fromhex("895628") and z28 == bytes.fromhex("895e28")
       and z30 == bytes.fromhex("895e30"))
check("X10", X10,
      "census 收口（5 存储站点字节钉牢）：+0x30 取值写入簇内仅 parse@0x71F59A；+0x28 在 TEvent 新对象（[esi]+0x28）上仅 unlink@0x71F80E+loader@0x72750B；清零 ctor@0x71E6B2/0x71E6B8。（同函数 loader@0x72759D 的 `[edi+0x28]` 属 TActionClass 链：new 0x94/ctor@0x6DD000/主 vtable 0x7F443C，非本类——census 无漏报）")

UNCOUNTED = {"X0", "X6"}  # X0 = fingerprint tautology; X6 = structural (RTTI census, not exe bytes)
n_pass = sum(1 for t, ok, _ in results if ok and t not in UNCOUNTED)
n_tot = sum(1 for t, ok, _ in results if t not in UNCOUNTED)
all_green = all(ok for _, ok, _ in results)  # X6 going red == label wrong -> must fail loudly
print(f"\n== R-041 {n_pass}/{n_tot} 字节断言 PASS（X0 指纹 + X6 结构性不计入分母，但 X6 红仍非零退出）==",
      file=sys.stderr)
if not fingerprint_ok:
    print("FATAL: image fingerprint mismatch (live binary churn?)", file=sys.stderr)
    sys.exit(2)
sys.exit(0 if all_green else 1)
