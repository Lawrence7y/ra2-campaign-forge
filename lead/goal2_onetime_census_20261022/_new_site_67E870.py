# -*- coding: utf-8 -*-
"""决定性：0x67E870 这个新站点 —— 它与 §351 的 L3 调用点 0x67E7F9 相邻。

本轮反向枚举的新发现
--------------------
`_vtable_store_reverse.py` 找到 7 对「以单例为 this 的装表点」，其中：

    0x005BE0AD  [esi] = 0x7E1964 (MouseClass)   head 0x005BDF70  caller 0x0067E870

而 §351 记录的 L3 直接调用点是：

    0x67E7F4  mov ecx, 0x87F7E8
    0x67E7F9  call 0x4A8960        ; ← L3（视口尺寸变更）

**两者只差 0x77 字节，在同一区域。**

这可能是关键：如果 `0x67E870` 与 `0x67E7F9` 在**同一个函数**或相邻函数里，
那说明这条路径同时做「装表 A」和「调 L3」——这正好解释了崩溃现场
（装表后 L3 拿到 this，而 L3 内部若解引用失败就崩）。

本脚本
------
1. 反汇编 0x67E700..0x67E900 全段，标出两个站点与函数边界。
2. 判定 0x67E7F9 与 0x67E870 是否在同一函数内。
3. 若同一函数：完整列出该函数体，找时机字符串。
4. 判定这条路径的性质（构造 / 析构 / 重初始化 / 显示模式切换）。
"""
import hashlib
import struct
import sys
import bisect
from pathlib import Path

from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_OP_REG

BIN = Path(r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe")
WANT_SHA8 = "73201cc0"
SINGLETON = 0x87F7E8
VT_A = 0x7E1964
VT_B = 0x7F0344
L3 = 0x4A8960
STORE_A = 0x5BE0AD
CALL_L3 = 0x67E7F9
CALLER_OF_STORE = 0x67E870

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

    def cstr(self, va, n=100):
        b = self.read(va, n)
        if not b:
            return None
        z = b.split(b"\x00")[0]
        try:
            s = z.decode("ascii")
        except Exception:
            return None
        return s if 4 <= len(s) and all(32 <= ord(c) < 127 or c in "\t\n" for c in s) else None


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
    print("== STEP 1  disassemble 0x67E700 .. 0x67E8C0")
    print("=" * 78)
    LO, HI = 0x67E700, 0x67E8C0
    code = pe.read(LO, HI - LO)
    marks = {CALL_L3: "<<< L3 CALL (from §351)",
             CALLER_OF_STORE: "<<< new: calls fn that installs TABLE_A",
             0x67E7F4: "<<< mov ecx,SINGLETON"}
    for i in md.disasm(code, LO):
        m = marks.get(i.address, "")
        note = ""
        for op in i.operands:
            if op.type == X86_OP_IMM and (op.imm & 0xFFFFFFFF) == SINGLETON:
                note = " [SINGLETON]"
            if op.type == X86_OP_IMM and (op.imm & 0xFFFFFFFF) == L3:
                note = " [L3]"
        print(f"  {i.address:08X}  {i.bytes.hex():<22} {i.mnemonic} {i.op_str}{note} {m}")

    print()
    print("=" * 78)
    print("== STEP 2  function boundaries in this region")
    print("=" * 78)
    # 用 ret/int3 + 跳过 nop 判定函数头
    boundaries = []
    prev_ret = False
    pending_nops = []
    for i in md.disasm(code, LO):
        if prev_ret and i.mnemonic != "nop":
            boundaries.append(i.address)
            prev_ret = False
        if i.mnemonic in ("ret", "retn", "int3"):
            prev_ret = True
        if i.mnemonic != "nop":
            prev_ret = prev_ret or False
    # 简化：直接列出所有 ret 位置
    rets = []
    for i in md.disasm(code, LO):
        if i.mnemonic in ("ret", "retn"):
            rets.append((i.address, i.op_str))
    print(f"  ret sites: {[(f'0x{a:08X}', s) for a, s in rets]}")
    print(f"  inferred function starts: {[f'0x{x:08X}' for x in boundaries]}")

    # 判定 CALL_L3 与 CALLER_OF_STORE 之间的函数边界
    between = [a for a in boundaries if CALL_L3 < a <= CALLER_OF_STORE]
    print(f"\n  function starts strictly between 0x{CALL_L3:X} and 0x{CALLER_OF_STORE:X}: "
          f"{[f'0x{x:08X}' for x in between]}")
    same_func = len(between) == 0
    chk("0x67E7F9 (L3 call) and 0x67E870 (new site) are in the SAME function",
        same_func, f"boundaries between: {len(between)}")

    print()
    print("=" * 78)
    print("== STEP 3  what does this function do? (strings + calls)")
    print("=" * 78)
    # 从最近的函数头起解码到 ret
    head = LO
    for b in boundaries:
        if b <= CALL_L3:
            head = b
    print(f"  using head 0x{head:08X}")
    body = []
    code2 = pe.read(head, 0x400)
    for i in md.disasm(code2, head):
        body.append(i)
        if i.mnemonic in ("ret", "retn"):
            break
    print(f"  body: {len(body)} insns, ends 0x{body[-1].address:08X}")

    calls = []
    strings = []
    for i in body:
        if i.mnemonic == "call" and i.operands and i.operands[0].type == X86_OP_IMM:
            calls.append(i.operands[0].imm & 0xFFFFFFFF)
        if i.mnemonic == "push" and i.operands and i.operands[0].type == X86_OP_IMM:
            v = i.operands[0].imm & 0xFFFFFFFF
            if 0x7E1000 <= v < 0xB96000:
                s = pe.cstr(v)
                if s:
                    strings.append((i.address, s))
    print(f"  calls: {[f'0x{x:X}' for x in calls]}")
    print(f"  strings: {[(f'0x{a:08X}', s[:60]) for a, s in strings]}")

    # 关键 call 是否包含装表函数 0x5BDF70
    chk("this function calls 0x5BDF70 (the TABLE_A installer)",
        0x5BDF70 in calls, str([f"0x{x:X}" for x in calls if x == 0x5BDF70]))
    chk("this function calls L3 0x4A8960 directly",
        L3 in calls, str([f"0x{x:X}" for x in calls if x == L3]))

    print()
    print("=" * 78)
    print("== STEP 4  verdict")
    print("=" * 78)
    has_both = (0x5BDF70 in calls) and (L3 in calls)
    if has_both and same_func:
        print("  [已证] 同一个函数**同时**做：")
        print("         ① 调 0x5BDF70 装表 A（MouseClass，slot5 = 0x5BDF30）")
        print("         ② 直接 call L3 0x4A8960（视口尺寸变更 + 缓冲重建）")
        print("         ⇒ 这就是 §351 要找的『别的时机』，且与装表**同一处**。")
        print("  [对 RC-4 的意义] 若此函数在运行期执行，则：")
        print("         - 单例被装表 A ⇒ slot5 变成 0x5BDF30")
        print("         - 同时 L3 被调用，L3 内部经 v[42] 走崩溃链")
        print("         ⇒ 崩溃链的入口就在这个函数里，不需要 One_Time 参与！")
        verdict = "L3_AND_TABLE_A_IN_SAME_FUNCTION"
    elif same_func:
        print("  [部分] 同一函数，但未同时看到装表与 L3 调用。")
        verdict = "SAME_FUNCTION_NO_BOTH"
    else:
        print("  [未定] 两者不在同一函数。")
        verdict = "DIFFERENT_FUNCTIONS"

    print()
    passed = sum(1 for _, ok, _ in CHECKS if ok)
    print(f"checks passed: {passed}/{len(CHECKS)}")
    print(f"verdict: {verdict}")
    print("RESULT:", "ALL PASS" if passed == len(CHECKS) else "FAIL")
    return 0 if passed == len(CHECKS) else 1


if __name__ == "__main__":
    sys.exit(main())
