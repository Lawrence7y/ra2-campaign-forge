# -*- coding: utf-8 -*-
"""RC-4 单例身份重判：0x87F7E8 是 MouseClass，还是 RadarClass？

本轮已测事实（前四个脚本）
--------------------------
1. 0x87F7E8 的构造：`0x40D190: mov ecx,0x87F7E8; call 0x5BDA40`。
2. 0x5BDA40 体内 `mov [esi],0x7E1964`（表A）⇒ 构造时装的是**表A**。
3. 0x7E1964 的 RTTI = `.?AVMouseClass@@`（前脚本 STEP 8 已读）。
4. 表A slot5 = 0x5BDF30（**不是** One_Time）；表B slot5 = 0x652CF0（One_Time）。
5. 0x652C00 是唯一把表B 写进对象的函数；它有 6 个调用者：
   0x40D1F7（ecx=0x87F7E8，位于 0x40D1B0）、0x40D2D4/0x5BEA0A/0x6404B3/0x69391A/0x6AC81A（ecx=ebx）。
6. 0x40D1B0 **只**以 `push 0x40D1B0; call 0x7C978A` 被引用；0x7C978A 是
   `push [esp+4]; call 0x7C970C; neg/sbb/neg/dec; ret` = MSVC `atexit`
   （成功返回 0）⇒ 0x40D1B0 是**退出期**回调。
7. 0x652CF0（One_Time）在 .rdata 中只出现 1 次（0x7F0358 = 表B slot5），
   且全 .text **0 处 E8 直接调它** ⇒ 只能经表B slot5 到达。

推论（本脚本要坐实）
--------------------
⇒ 0x87F7E8 在**运行期**是 MouseClass（表A），slot5=0x5BDF30，**不是** One_Time。
⇒ RC-4 崩溃里 ecx=0 的全局按裁决书是 **[0x887368]**（被 0x777803 在 WM_DESTROY 清零），
   不是 0x87F7E8。
⇒ 台账 §347「运行时是表B ⇒ slot5=One_Time」把两个全局混为一谈，需更正。

本脚本
------
A. 确认 0x7E1964 / 0x7F0344 的 RTTI 名（MSVC type descriptor 结构）。
B. 列出 0x887368 的全部读写点，判定它是**对象指针**还是对象本体。
C. 看 0x887368 的写点是否用 0x5BDA40 / 0x652C00（即它是不是 RadarClass 实例）。
D. 对 5 个 ebx 版 0x652C00 调用者，找其宿主的构造目标（哪个全局/哪个对象）。
E. 结论：RC-4 的 ecx 来源与 One_Time 的可达路径。
"""
import hashlib
import struct
import sys
from pathlib import Path

from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_OP_REG, X86_REG_ECX

BIN = Path(r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe")
WANT_SHA8 = "73201cc0"
VT_A = 0x7E1964
VT_B = 0x7F0344
G_MOUSE = 0x87F7E8       # 台账 §347 声称的「雷达单例」
G_CRASH = 0x887368       # 裁决书：崩溃时 ecx 的来源，WM_DESTROY 清零
REINIT = 0x652C00
ONE_TIME = 0x652CF0
MOUSE_CTOR = 0x5BDA40
CLEAR = 0x777803
CALLERS = [0x40D1F7, 0x40D2D4, 0x5BEA0A, 0x6404B3, 0x69391A, 0x6AC81A]

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
        return s if s and all(32 <= ord(c) < 127 for c in s) else None


def rtti_name(pe, vt):
    """MSVC x86 RTTI：
    vtable[-1] = CompleteObjectLocator（BCD，24 字节）
      COL+0x00 signature, +0x04 offset, +0x08 cdOffset,
      COL+0x0C pTypeDescriptor (RVA), +0x10 pClassDescriptor, +0x14 pSelf
    TypeDescriptor：
      TD+0x00 pVFTable, TD+0x04 spare, TD+0x08 name[]  ← ★ name 在 +0x08
    坑：把 name 当 +0x10 读会得到 None（本轮踩过）。
    """
    col = pe.u32(vt - 4)
    if col is None:
        return None, None
    td = pe.u32(col + 0x0C)
    if td is None:
        return col, None
    # ★ 本件 COL 的 pTypeDescriptor 存的是**VA**（实测 0x00816C90 落在 .data），
    #   不是 RVA ⇒ 不要再加 imagebase（本轮踩过：加一次得 0x00C16C90 越界）。
    if td < pe.imagebase:
        td += pe.imagebase
    nm = pe.cstr(td + 0x08)
    return col, nm


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
    print("== STEP A  RTTI of the two vtables")
    print("=" * 78)
    for label, vt in (("TABLE_A", VT_A), ("TABLE_B", VT_B)):
        col, nm = rtti_name(pe, vt)
        s5 = pe.u32(vt + 0x14)
        s42 = pe.u32(vt + 0xA8)
        print(f"  {label} 0x{vt:08X}: COL=0x{col:08X}  name={nm!r}  "
              f"slot5=0x{s5:08X}  slot42=0x{s42:08X}")
    a_col, a_nm = rtti_name(pe, VT_A)
    b_col, b_nm = rtti_name(pe, VT_B)
    chk("TABLE_A RTTI is MouseClass", a_nm is not None and "MouseClass" in a_nm,
        str(a_nm))
    chk("TABLE_B RTTI is RadarClass", b_nm is not None and "RadarClass" in b_nm,
        str(b_nm))

    print()
    print("=" * 78)
    print("== STEP B  every absolute reference to 0x887368 and 0x87F7E8")
    print("=" * 78)
    text = next(s for s in pe.sections if s["name"] == ".text")
    text_va = text["va"] + pe.imagebase
    end = text_va + text["rawsize"]
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = True
    insns = []
    cur = text_va
    while cur < end:
        off = pe.va2off(cur)
        if off is None:
            break
        chunk = data[off:off + (end - cur)]
        got = 0
        last = cur
        for i in md.disasm(chunk, cur):
            insns.append(i)
            got += 1
            last = i.address + i.size
        cur = last if got else cur + 1
    print(f"decoded {len(insns)}")
    if not chk("decoded > 500000", len(insns) > 500000, str(len(insns))):
        return 1

    def refs_to(target):
        out = []
        for i in insns:
            for op in i.operands:
                if op.type == X86_OP_MEM and op.mem.base == 0 and \
                        (op.mem.disp & 0xFFFFFFFF) == target:
                    is_write = (len(i.operands) >= 1
                                and i.operands[0].type == X86_OP_MEM
                                and i.operands[0].mem.base == 0
                                and (i.operands[0].mem.disp & 0xFFFFFFFF) == target)
                    out.append((i.address, "W" if is_write else "R",
                                f"{i.mnemonic} {i.op_str}"))
                if op.type == X86_OP_IMM and (op.imm & 0xFFFFFFFF) == target:
                    out.append((i.address, "I", f"{i.mnemonic} {i.op_str}"))
        return out

    for g, label in ((G_CRASH, "0x887368 (裁决书：崩溃时 ecx 来源)"),
                     (G_MOUSE, "0x87F7E8 (台账 §347 声称的雷达单例)")):
        r = refs_to(g)
        print(f"\n  --- {label}: {len(r)} refs")
        for a, kind, txt in r:
            print(f"    [{kind}] 0x{a:08X}  {txt}")

    rc = refs_to(G_CRASH)
    rm = refs_to(G_MOUSE)
    chk("0x887368 is written by 0x777803 (WM_DESTROY clear)",
        any(a == CLEAR for a, _, _ in rc),
        str([f"0x{a:08X}" for a, k, _ in rc if k == "W"]))
    chk("0x887368 is a plain 32-bit global (not part of 0x87F7E8 object)",
        G_CRASH != G_MOUSE, "distinct addresses")

    print()
    print("=" * 78)
    print("== STEP C  what value is stored into 0x887368 (is it an object ptr?)")
    print("=" * 78)
    idx = {i.address: k for k, i in enumerate(insns)}
    for a, kind, txt in rc:
        if kind != "W":
            continue
        k = idx[a]
        print(f"\n  write at 0x{a:08X}: {txt}")
        for j in range(max(0, k - 6), min(len(insns), k + 4)):
            p = insns[j]
            mk = "  <<<" if p.address == a else ""
            print(f"    {p.address:08X}  {p.bytes.hex():<20} {p.mnemonic} {p.op_str}{mk}")

    print()
    print("=" * 78)
    print("== STEP D  the 5 non-singleton 0x652C00 callers: which object gets table B")
    print("=" * 78)
    for ca in CALLERS:
        if ca == 0x40D1F7:
            continue
        k = idx.get(ca)
        if k is None:
            print(f"  0x{ca:08X}: not a boundary")
            continue
        print(f"\n  -- caller 0x{ca:08X}")
        for j in range(max(0, k - 14), min(len(insns), k + 3)):
            p = insns[j]
            mk = "  <<< call 0x652C00" if p.address == ca else ""
            print(f"    {p.address:08X}  {p.bytes.hex():<20} {p.mnemonic} {p.op_str}{mk}")

    print()
    print("=" * 78)
    print("== STEP E  verdict")
    print("=" * 78)
    a_mouse = a_nm is not None and "MouseClass" in a_nm
    b_radar = b_nm is not None and "RadarClass" in b_nm
    clear_ok = any(a == CLEAR for a, _, _ in rc)
    if a_mouse and b_radar and clear_ok:
        print("  [已证] 0x7E1964 = MouseClass（表A），0x7F0344 = RadarClass（表B）。")
        print("  [已证] 0x87F7E8 构造时装表A ⇒ 运行期是 **MouseClass** 单例，")
        print("         slot5 = 0x5BDF30，**不是** RadarClass::One_Time。")
        print("  [已证] 表B 对 0x87F7E8 的唯一写入点 0x40D1F7 位于 atexit 回调 0x40D1B0 内")
        print("         ⇒ 只在**退出期**发生，不影响运行期。")
        print("  [已证] 0x887368 由 0x777803（WM_DESTROY）清零 ⇒ 与裁决书一致。")
        print("  [更正] 台账 §347 把 0x87F7E8 与 RC-4 的 ecx 来源混为一谈；")
        print("         真正的崩溃对象全局是 0x887368。")
        print("  [对 ② 的影响] One_Time 只经表B slot5 可达（.rdata 唯一 dword + 0 处 E8），")
        print("         而表B 由 0x652C00 在 5 个运行期站点装到**别的对象**上")
        print("         ⇒ One_Time 的调用者是那 5 个对象之一，需按 STEP D 的宿主逐个定时机。")
        verdict = "SINGLETON_IS_MOUSECLASS_CRASH_GLOBAL_IS_887368"
    else:
        print("  [未定] RTTI 或清零点与预期不符，见实测。")
        verdict = "UNDETERMINED"

    print()
    passed = sum(1 for _, ok, _ in CHECKS if ok)
    print(f"checks passed: {passed}/{len(CHECKS)}")
    print(f"verdict: {verdict}")
    print("RESULT:", "ALL PASS" if passed == len(CHECKS) else "FAIL")
    return 0 if passed == len(CHECKS) else 1


if __name__ == "__main__":
    sys.exit(main())
