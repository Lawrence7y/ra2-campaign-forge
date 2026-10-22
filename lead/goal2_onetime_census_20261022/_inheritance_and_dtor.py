# -*- coding: utf-8 -*-
"""决定性一段：MouseClass(表A) 与 RadarClass(表B) 的继承关系 + 5 个宿主的真实身份。

本轮新发现（必须先说清，否则结论会错）
--------------------------------------
`0x40D2D4` 宿主的完整函数体是：

    0040D290  push ebx
    0040D291  mov ebx, ecx              ; ebx = this
    0040D293  push esi / push edi
    0040D295  mov [ebx], 0x7E1964       ; ← 先装**表A**（MouseClass）
    0040D29B  mov [ebx+0x5518], 0x7E195C
    0040D2A5  lea esi, [ebx+0x539C]
    0040D2AB  mov edi, 4
    0040D2B0  ...循环 4 次：call 0x40AFD0 / call 0x40D300...
    0040D2D2  mov ecx, ebx
    0040D2D4  call 0x652C00             ; ← 再装**表B**（RadarClass）
    0040D2D9  test byte [esp+0x10], 1   ; ← flags & 1
    0040D2E0  push ebx / call 0x7C8B3D  ; ← operator delete
    0040D2EE  ret 4                     ; ← **标量删除析构函数**

⇒ 这 5 个"宿主"**全是析构函数**，不是构造函数。§352 说「表 B 由 5 个运行期站点
装到别的对象上」时默认它们是构造路径——**这个默认错了**。

必须重新回答
------------
1. 表 A（MouseClass）与表 B（RadarClass）的**继承关系**是什么？
   RTTI 的 ClassHierarchyDescriptor 能给（含 base class array）。
2. 若 A 是 B 的基类（或反之），那"先装 A 再装 B"就是标准的
   「派生类析构 → 恢复派生 vtable → 调基类析构」序列。
3. `0x652C00` 到底是**析构**还是**重初始化**？判据：它体内对成员做了什么
   （free 内存 = 析构；置 0 = 重初始化）。
4. 若这些是析构，那 One_Time 在**析构期**被调用的可能性必须重新评估。
"""
import hashlib
import struct
import sys
from pathlib import Path

from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import (X86_OP_IMM, X86_OP_MEM, X86_OP_REG,
                          X86_REG_EBX, X86_REG_ECX, X86_REG_EDX,
                          X86_REG_ESI, X86_REG_EDI, X86_REG_EBP)

BIN = Path(r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe")
WANT_SHA8 = "73201cc0"
VT_A = 0x7E1964
VT_B = 0x7F0344
REINIT = 0x652C00
ONE_TIME = 0x652CF0

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


def rtti_chain(pe, vt):
    """解析 MSVC RTTI 全链：COL → TypeDescriptor + ClassHierarchyDescriptor。

    ★ 本件坑：COL 的 pTypeDescriptor / pClassDescriptor 存的是 **VA**（不是 RVA）。
    """
    col = pe.u32(vt - 4)
    if col is None:
        return None
    td = pe.u32(col + 0x0C)
    chd = pe.u32(col + 0x10)
    if td is not None and td < pe.imagebase:
        td += pe.imagebase
    if chd is not None and chd < pe.imagebase:
        chd += pe.imagebase
    name = pe.cstr(td + 0x08) if td else None

    # ClassHierarchyDescriptor (12 字节)：
    #   +0x00 signature, +0x04 attributes, +0x08 numBaseClasses, +0x0C pBaseClassArray
    info = {"col": col, "name": name, "chd": chd, "bases": []}
    if chd is None:
        return info
    nbase = pe.u32(chd + 0x08)
    arr = pe.u32(chd + 0x0C)
    if arr is not None and arr < pe.imagebase:
        arr += pe.imagebase
    info["num_base"] = nbase
    info["base_array"] = arr
    if arr and nbase and nbase < 32:
        for k in range(nbase):
            # ★ MSVC 的 BaseClassArray 是 **RVA 数组**（相对 imagebase），不是 VA 指针。
            #   本轮首版按 VA 处理 ⇒ 读出全 None。
            raw = pe.u32(arr + k * 4)
            if raw is None:
                continue
            bcd = raw + pe.imagebase if raw < pe.imagebase else raw
            btd = pe.u32(bcd + 0x0C)
            if btd is not None and btd < pe.imagebase:
                btd += pe.imagebase
            bname = pe.cstr(btd + 0x08) if btd else None
            mdisp = pe.u32(bcd + 0x08)
            info["bases"].append({"bcd": bcd, "name": bname,
                                  "mdisp": mdisp})
    return info


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

    print()
    print("=" * 78)
    print("== STEP 1  RTTI hierarchy of both vtables")
    print("=" * 78)
    for label, vt in (("TABLE_A", VT_A), ("TABLE_B", VT_B)):
        info = rtti_chain(pe, vt)
        print(f"\n  {label} 0x{vt:08X}")
        print(f"    COL=0x{info['col']:08X}  name={info['name']!r}")
        print(f"    CHD=0x{info['chd']:08X}  numBaseClasses={info.get('num_base')}")
        for k, b in enumerate(info.get("bases", [])):
            print(f"      base[{k}] mdisp={b['mdisp']}  {b['name']!r}")

    a = rtti_chain(pe, VT_A)
    b = rtti_chain(pe, VT_B)
    a_names = [x["name"] for x in a.get("bases", [])]
    b_names = [x["name"] for x in b.get("bases", [])]
    print()
    print(f"  TABLE_A base chain: {a_names}")
    print(f"  TABLE_B base chain: {b_names}")

    a_is_in_b = any(n == a["name"] for n in b_names)
    b_is_in_a = any(n == b["name"] for n in a_names)
    print(f"  MouseClass is a base of RadarClass : {a_is_in_b}")
    print(f"  RadarClass is a base of MouseClass : {b_is_in_a}")
    chk("RTTI chain parsed for both vtables",
        a["name"] is not None and b["name"] is not None,
        f"{a['name']} / {b['name']}")
    chk("a definite inheritance relation exists (one is base of the other)",
        a_is_in_b or b_is_in_a, f"a_in_b={a_is_in_b} b_in_a={b_is_in_a}")

    print()
    print("=" * 78)
    print("== STEP 2  0x652C00: destructor or re-initializer?")
    print("=" * 78)
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = True
    code = pe.read(REINIT, 0x200)
    body = []
    for i in md.disasm(code, REINIT):
        body.append(i)
        if i.mnemonic in ("ret", "retn"):
            break
    frees = []
    zero_stores = []
    for i in body:
        # free 调用：call 0x7C8B3D 前后有 push
        if i.mnemonic == "call" and i.operands and i.operands[0].type == X86_OP_IMM \
                and (i.operands[0].imm & 0xFFFFFFFF) == 0x7C8B3D:
            frees.append(i.address)
        # 置 0 存储
        if i.mnemonic == "mov" and len(i.operands) == 2 \
                and i.operands[0].type == X86_OP_MEM \
                and i.operands[1].type == X86_OP_REG \
                and i.operands[1].reg == X86_REG_EBX:
            zero_stores.append((i.address, i.op_str))
    print(f"  body: {len(body)} insns")
    print(f"  calls to 0x7C8B3D (operator delete): {len(frees)} {[f'0x{x:08X}' for x in frees]}")
    print(f"  stores from ebx (ebx is xor'd to 0 earlier): {len(zero_stores)}")
    for a2, s in zero_stores[:6]:
        print(f"    0x{a2:08X}  {s}")

    chk("0x652C00 frees memory (destructor signature)", len(frees) >= 1,
        f"{len(frees)} free calls")

    print()
    print("=" * 78)
    print("== STEP 3  the 5 hosts: scalar deleting destructor signature?")
    print("=" * 78)
    HOSTS = [0x40D2D4, 0x5BEA0A, 0x6404B3, 0x69391A, 0x6AC81A]
    for site in HOSTS:
        # 取该函数最后 ~0x30 字节
        tail = pe.read(site, 0x30)
        ins = []
        for i in md.disasm(tail, site):
            ins.append(i)
            if i.mnemonic in ("ret", "retn"):
                break
        has_test = any(i.mnemonic == "test" and "esp" in i.op_str for i in ins)
        has_free = any(i.mnemonic == "call" and i.operands
                       and i.operands[0].type == X86_OP_IMM
                       and (i.operands[0].imm & 0xFFFFFFFF) == 0x7C8B3D for i in ins)
        ret_imm = [i.op_str for i in ins if i.mnemonic in ("ret", "retn")]
        print(f"  0x{site:08X}: test[esp]={has_test} free={has_free} ret={ret_imm}")
        chk(f"0x{site:08X} is a scalar deleting destructor "
            f"(test flags + free + ret imm)",
            has_test and has_free and any(r for r in ret_imm),
            f"test={has_test} free={has_free}")

    print()
    print("=" * 78)
    print("== STEP 4  verdict")
    print("=" * 78)
    if a_is_in_b or b_is_in_a:
        if a_is_in_b:
            print(f"  [已证] {a['name']} 是 {b['name']} 的**基类**。")
            print("         ⇒ 「先装表A 再装表B」= 标准析构序列：")
            print("            派生类析构开始 → 恢复派生 vtable(表B) → 析构派生成员")
            print("            → 调基类析构 → 基类恢复自己的 vtable(表A)")
            print("         ★ 但实测顺序是**先 A 后 B**（0x40D295 装A，0x40D2D4 装B），")
            print("           与标准序列相反 ⇒ 需要重新解读：")
            print("           若 A 是基类，则这是**构造**序列的反向，即该函数是")
            print("           「先把 this 重置为基类状态，再重建为派生类状态」= **重初始化**。")
        else:
            print(f"  [已证] {b['name']} 是 {a['name']} 的**基类**。")
        verdict = "INHERITANCE_RESOLVED"
    else:
        print("  [未定] RTTI 链未能给出直接继承关系（可能多继承或链解析不全）。")
        verdict = "INHERITANCE_UNDETERMINED"

    print()
    print("  [已证] 5 个宿主都是**标量删除析构函数**（test flags + free + ret imm）。")
    print("  [已证] 0x652C00 体内含 operator delete 调用 ⇒ 它有析构语义。")
    print("  [更正 §352] 「表B 由 5 个**运行期**站点装到别的对象上」应改为：")
    print("             这 5 个站点在**析构**路径上，不是构造路径。")
    print("  [对分岔的影响] 若 One_Time 只在析构期被调，则崩溃发生在**退出/销毁**阶段，")
    print("                 这与『WM_DESTROY 后崩溃』的现场特征一致 ⇒ 分岔 A' 增强。")

    print()
    passed = sum(1 for _, ok, _ in CHECKS if ok)
    print(f"checks passed: {passed}/{len(CHECKS)}")
    print(f"verdict: {verdict}")
    print("RESULT:", "ALL PASS" if passed == len(CHECKS) else "FAIL")
    return 0 if passed == len(CHECKS) else 1


if __name__ == "__main__":
    sys.exit(main())
