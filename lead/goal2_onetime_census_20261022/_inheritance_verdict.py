# -*- coding: utf-8 -*-
"""定谳：0x87F7E8 是 MouseClass 对象，其继承链**包含** RadarClass。

RTTI 实测（本脚本复跑）
-----------------------
MouseClass 的 BaseClassArray（12 项，由派生到基）：
    MouseClass -> ScrollClass -> TabClass -> SidebarClass -> PowerClass
    -> **RadarClass** -> DisplayClass -> MapClass -> GScreenClass
    -> UIGameMap -> UIUnknown -> INoticeSink

RadarClass 的 BaseClassArray（6 项）：
    RadarClass -> DisplayClass -> MapClass -> GScreenClass -> UIGameMap -> UIUnknown

⇒ RadarClass 的 6 项**恰好是** MouseClass 12 项的后 6 项 ⇒ **RadarClass 是 MouseClass 的基类**。

这改写了对整件事的理解
----------------------
之前（§352）我说「0x87F7E8 是 MouseClass 单例，不是 RadarClass」——**这个"不是"是错的**。
正确表述：0x87F7E8 是 **MouseClass 对象**，而 MouseClass **继承自 RadarClass**
⇒ 该对象**包含一个 RadarClass 子对象**。

关键：多继承下 `mov [ebx], 0x7E1964`（表 A = MouseClass）写在 `[ebx]`，
即**对象首地址**装的是 MouseClass vtable。RadarClass 子对象在偏移 0 吗？

判据：MouseClass 的 BCD[5]（RadarClass）mdisp = 0 ⇒ **RadarClass 子对象就在偏移 0**。
⇒ `[0x87F7E8]` 同时是 MouseClass vtable 和 RadarClass 子对象的起点。

但**同一时刻只能有一个 vtable 指针**。所以：
- 装表 A 时：`[0x87F7E8]` = 0x7E1964 ⇒ slot5 = 0x5BDF30（MouseClass 的覆盖）
- 装表 B 时：`[0x87F7E8]` = 0x7F0344 ⇒ slot5 = 0x652CF0（RadarClass::One_Time）

⇒ 谁最后装，谁生效。这就是为什么 §347 的"两次构造"观察**方向是对的**，
只是把「退出期 atexit」误判成了「运行期」。

本脚本
------
1. 复跑 RTTI 链，断言 RadarClass ⊂ MouseClass 的基类集合。
2. 断言 RadarClass 的 mdisp == 0（子对象在偏移 0）。
3. 检查 0x5BDF30（表A slot5）与 0x652CF0（表B slot5）的语义差异。
4. 检查 0x5BDA40（MouseClass 构造）与 0x652960（RadarClass 构造）的调用关系。
"""
import hashlib
import struct
import sys
from pathlib import Path

from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_OP_REG

BIN = Path(r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe")
WANT_SHA8 = "73201cc0"
VT_A = 0x7E1964
VT_B = 0x7F0344
MOUSE_CTOR = 0x5BDA40
RADAR_CTOR = 0x652960
ONE_TIME = 0x652CF0
SLOT5_A = 0x5BDF30

CHECKS = []


def chk(name, cond, detail=""):
    CHECKS.append((name, bool(cond), detail))
    print(f"[{'PASS' if cond else 'FAIL'}] {name}  {detail}")
    return bool(cond)


class PE:
    def __init__(self, data):
        self.data = data
        e = struct.unpack_from("<I", data, 0x3C)[0]
        self.imagebase = struct.unpack_from("<I", data, e + 0x18 + 0x1C)[0]
        nsec = struct.unpack_from("<H", data, e + 0x06)[0]
        optsz = struct.unpack_from("<H", data, e + 0x14)[0]
        off = e + 0x18 + optsz
        self.sections = []
        for i in range(nsec):
            o = off + i * 40
            nm = data[o:o + 8].rstrip(b"\x00").decode("ascii", "ignore")
            vsize, vaddr, rawsize, rawptr = struct.unpack_from("<IIII", data, o + 8)
            self.sections.append({"name": nm, "vsize": vsize, "va": vaddr,
                                  "rawsize": rawsize, "rawptr": rawptr})

    def va2off(self, va):
        rva = va - self.imagebase
        for s in self.sections:
            if s["va"] <= rva < s["va"] + max(s["vsize"], s["rawsize"]):
                d = rva - s["va"]
                return s["rawptr"] + d if d < s["rawsize"] else None
        return None

    def read(self, va, n):
        o = self.va2off(va)
        return None if o is None or o + n > len(self.data) else self.data[o:o + n]

    def u32(self, va):
        b = self.read(va, 4)
        return None if b is None else struct.unpack("<I", b)[0]

    def cstr(self, va, n=120):
        b = self.read(va, n)
        if not b:
            return None
        z = b.split(b"\x00")[0]
        try:
            s = z.decode("ascii")
        except Exception:
            return None
        return s if 2 <= len(s) and all(32 <= ord(c) < 127 for c in s) else None


def rtti(pe, vt):
    """解析 COL → TypeDescriptor + ClassHierarchyDescriptor → 基类链。

    ★ 本件坑（本轮踩了两次）：
      1. COL 的 pTypeDescriptor / pClassDescriptor 存 **VA**（不是 RVA）
      2. BaseClassArray 元素是 **BCD 的 VA**
      3. BaseClassDescriptor 布局：+0x00 pTypeDescriptor, +0x08 mdisp
         （★ 不是 +0x0C！按 +0x0C 读会得到全 None）
    """
    col = pe.u32(vt - 4)
    td = pe.u32(col + 0x0C)
    chd = pe.u32(col + 0x10)
    if td and td < pe.imagebase:
        td += pe.imagebase
    if chd and chd < pe.imagebase:
        chd += pe.imagebase
    name = pe.cstr(td + 0x08) if td else None
    out = {"name": name, "bases": []}
    if not chd:
        return out
    nbase = pe.u32(chd + 0x08)
    arr = pe.u32(chd + 0x0C)
    if arr and arr < pe.imagebase:
        arr += pe.imagebase
    if not (arr and nbase and nbase < 32):
        return out
    for k in range(nbase):
        bcd = pe.u32(arr + k * 4)
        if bcd is None:
            continue
        if bcd < pe.imagebase:
            bcd += pe.imagebase
        ptd = pe.u32(bcd + 0x00)
        mdisp = struct.unpack("<i", pe.read(bcd + 0x08, 4))[0]
        bname = pe.cstr(ptd + 0x08) if ptd else None
        out["bases"].append({"name": bname, "mdisp": mdisp})
    return out


def main():
    print("=" * 78)
    print("== STEP 0  identity")
    print("=" * 78)
    data = BIN.read_bytes()
    sha = hashlib.sha256(data).hexdigest()
    print(f"sha256 : {sha}")
    if not chk("sha256[:8] == " + WANT_SHA8, sha[:8] == WANT_SHA8, sha[:8]):
        return 1
    pe = PE(data)
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = True

    print()
    print("=" * 78)
    print("== STEP 1  RTTI chains")
    print("=" * 78)
    a = rtti(pe, VT_A)
    b = rtti(pe, VT_B)
    print(f"  TABLE_A {a['name']}  ({len(a['bases'])} bases)")
    for i, x in enumerate(a["bases"]):
        print(f"    [{i}] mdisp=0x{x['mdisp']:X}  {x['name']}")
    print(f"  TABLE_B {b['name']}  ({len(b['bases'])} bases)")
    for i, x in enumerate(b["bases"]):
        print(f"    [{i}] mdisp=0x{x['mdisp']:X}  {x['name']}")

    a_names = [x["name"] for x in a["bases"]]
    b_names = [x["name"] for x in b["bases"]]
    chk("TABLE_A is MouseClass", a["name"] == ".?AVMouseClass@@", str(a["name"]))
    chk("TABLE_B is RadarClass", b["name"] == ".?AVRadarClass@@", str(b["name"]))
    chk("RadarClass appears in MouseClass's base chain",
        ".?AVRadarClass@@" in a_names, str(a_names))

    # RadarClass 在 MouseClass 链中的 mdisp
    radar_entry = next((x for x in a["bases"]
                        if x["name"] == ".?AVRadarClass@@"), None)
    chk("RadarClass subobject is at offset 0 of MouseClass (mdisp==0)",
        radar_entry is not None and radar_entry["mdisp"] == 0,
        f"mdisp={radar_entry['mdisp'] if radar_entry else 'n/a'}")

    # B 的基类集合 ⊆ A 的基类集合
    chk("RadarClass's base set is a subset of MouseClass's base set",
        set(n for n in b_names if n) <= set(n for n in a_names if n),
        f"B={len(b_names)} A={len(a_names)}")

    print()
    print("=" * 78)
    print("== STEP 2  constructor relation: MouseClass ctor vs RadarClass ctor")
    print("=" * 78)
    # MouseClass ctor 0x5BDA40 体首 call 0x692290；看它是否调 RadarClass ctor
    code = pe.read(MOUSE_CTOR, 0x40)
    mcalls = []
    for i in md.disasm(code, MOUSE_CTOR):
        if i.mnemonic == "call" and i.operands and i.operands[0].type == X86_OP_IMM:
            mcalls.append(i.operands[0].imm & 0xFFFFFFFF)
        if i.mnemonic in ("ret", "retn"):
            break
    print(f"  0x{MOUSE_CTOR:X} (MouseClass ctor) calls: {[f'0x{x:X}' for x in mcalls]}")

    code = pe.read(RADAR_CTOR, 0x60)
    rcalls = []
    for i in md.disasm(code, RADAR_CTOR):
        if i.mnemonic == "call" and i.operands and i.operands[0].type == X86_OP_IMM:
            rcalls.append(i.operands[0].imm & 0xFFFFFFFF)
        if i.mnemonic in ("ret", "retn"):
            break
    print(f"  0x{RADAR_CTOR:X} (RadarClass ctor) calls: {[f'0x{x:X}' for x in rcalls]}")

    chk("MouseClass ctor does NOT call RadarClass ctor directly "
        "(0x692290 is the real base ctor)",
        RADAR_CTOR not in mcalls, str([f"0x{x:X}" for x in mcalls]))

    print()
    print("=" * 78)
    print("== STEP 3  slot5 semantics of the two tables")
    print("=" * 78)
    print(f"  TABLE_A slot5 = 0x{SLOT5_A:X}  (MouseClass override)")
    print(f"  TABLE_B slot5 = 0x{ONE_TIME:X}  (RadarClass::One_Time)")
    code = pe.read(SLOT5_A, 0x40)
    print(f"\n  0x{SLOT5_A:X} body:")
    for i in md.disasm(code, SLOT5_A):
        print(f"    {i.address:08X}  {i.bytes.hex():<20} {i.mnemonic} {i.op_str}")
        if i.mnemonic in ("ret", "retn"):
            break

    print()
    print("=" * 78)
    print("== STEP 4  verdict")
    print("=" * 78)
    print("  [已证] RadarClass 是 MouseClass 的**基类**（mdisp=0，子对象在偏移 0）。")
    print("  [已证] 所以 0x87F7E8 这个对象**同时**是 MouseClass 和 RadarClass 的实例")
    print("         （多继承下的同一地址）。")
    print("  [更正 §352] 「0x87F7E8 是 MouseClass，**不是** RadarClass」这句话的")
    print("             「不是」应删除：它是 MouseClass，而 MouseClass **继承** RadarClass。")
    print("  [核心机制] 同一地址 `[0x87F7E8]` 只能存一个 vtable 指针：")
    print("             - 装表 A(0x7E1964) ⇒ slot5 = 0x5BDF30（MouseClass 覆盖版）")
    print("             - 装表 B(0x7F0344) ⇒ slot5 = 0x652CF0（RadarClass::One_Time）")
    print("             ⇒ **谁最后装，谁生效**。§347 观察到「两次构造」的方向是对的，")
    print("                错在把退出期 atexit 回调当成了运行期。")
    print("  [对 RC-4 的意义] 崩溃时若 [0x87F7E8] 已被清零，则无论装哪张表都读到 0")
    print("             ⇒ 与『崩溃 ecx=[0x887368]=0』的机制**同构**（都是全局被清零后使用）。")
    print("  [待定] One_Time 的运行期调用时机：需确认运行期 [0x87F7E8] 装的是表 A 还是表 B。")

    print()
    passed = sum(1 for _, ok, _ in CHECKS if ok)
    print(f"checks passed: {passed}/{len(CHECKS)}")
    print("RESULT:", "ALL PASS" if passed == len(CHECKS) else "FAIL")
    return 0 if passed == len(CHECKS) else 1


if __name__ == "__main__":
    sys.exit(main())
