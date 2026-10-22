# -*- coding: utf-8 -*-
"""待办 9 根因段：0x40D1B0 到底是「初始化」还是「退出期回调」？
以及雷达单例在**游戏运行期**的虚表究竟是表A 还是表B。

为什么这是根因
--------------
前一段（`_vtable_verify.py`）与台账 §347 都依据这条顺序：
    0x40D1B2  mov [0x87F7E8], 0x7E1964     ; 表A
    0x40D1F7  call 0x652C00                ; 0x652C00 内 mov [edi],0x7F0344 ⇒ 表B
⇒ 结论「运行时是表B ⇒ slot5 = One_Time」。

但反汇编显示 0x40D1B0 **不是** 0x40D190 的直落后继，而是：
    0x40D190  mov ecx,0x87F7E8
    0x40D195  call 0x5BDA40          ; 构造单例
    0x40D19A  push 0x40D1B0
    0x40D19F  call 0x7C978A          ; ← 这个像 atexit()！
    0x40D1A5  ret
    0x40D1A6..AF  nop 填充
    0x40D1B0  ...                    ; ← 若 0x7C978A = atexit，这是**退出期**回调

若 0x7C978A 是 atexit，则「写表A→改表B」发生在**进程退出时**，
与「运行期虚表」无关 ⇒ §347 的推论前提被推翻，且 One_Time 是否被调需重判。

本脚本判定
----------
1. 0x7C978A 是不是 atexit：看它是否把参数存入一张函数指针表、且该表由
   0x7C97xx 区域的 exit 处理器遍历调用；同时看它是否与已知 CRT 符号一致。
2. 0x5BDA40（单例构造）体内**写的是哪个虚表**（表A 还是表B）。
3. 0x652C00 的全部调用者（若只有 0x40D1F7 一处，且该处在 atexit 回调内，
   则运行期不会执行它）。
4. 结论：游戏运行期单例的 vtable = 表A 还是表B ⇒ slot5 = 0x5BDF30 还是 0x652CF0。
"""
import hashlib
import struct
import sys
from pathlib import Path

from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_OP_REG

BIN = Path(r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe")
WANT_SHA8 = "73201cc0"
SINGLETON = 0x87F7E8
VT_A = 0x7E1964
VT_B = 0x7F0344
CTOR = 0x5BDA40
REGISTER_FN = 0x7C978A
EXIT_CB = 0x40D1B0
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


def disasm_fn(pe, md, va, maxb=0x400):
    code = pe.read(va, maxb)
    if code is None:
        return []
    out = []
    for i in md.disasm(code, va):
        out.append(i)
        if i.mnemonic in ("ret", "retn"):
            break
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
    print("== STEP 1  what is 0x7C978A ?  (called with push 0x40D1B0 before it)")
    print("=" * 78)
    body = disasm_fn(pe, md, REGISTER_FN, 0x300)
    print(f"  0x7C978A body: {len(body)} insns")
    for i in body:
        print(f"    {i.address:08X}  {i.bytes.hex():<22} {i.mnemonic} {i.op_str}")

    # 判定特征：atexit 实现通常 ① 有全局函数表 ② 有 __onexit 表指针 ③ 用 InterlockedIncrement
    has_interlocked = any("lock" in i.op_str or "xadd" in i.mnemonic
                          or "cmpxchg" in i.mnemonic for i in body)
    writes_table = False
    table_addr = None
    for i in body:
        if i.mnemonic == "mov" and len(i.operands) == 2 \
                and i.operands[0].type == X86_OP_MEM \
                and i.operands[0].mem.base != 0 \
                and i.operands[1].type == X86_OP_REG:
            writes_table = True
            table_addr = i.address
    # 找该函数引用的绝对地址（表位置）
    abs_refs = set()
    for i in body:
        for op in i.operands:
            if op.type == X86_OP_MEM and op.mem.base == 0:
                abs_refs.add(op.mem.disp & 0xFFFFFFFF)
            if op.type == X86_OP_IMM:
                v = op.imm & 0xFFFFFFFF
                if 0x800000 <= v < 0xC00000:
                    abs_refs.add(v)
    print(f"  absolute refs inside 0x7C978A: {[f'0x{x:08X}' for x in sorted(abs_refs)]}")
    print(f"  has interlocked-ish op: {has_interlocked}")
    print(f"  writes through a table pointer at: "
          f"{f'0x{table_addr:08X}' if table_addr else 'none'}")

    print()
    print("=" * 78)
    print("== STEP 2  who else calls 0x7C978A (is it the atexit family?)")
    print("=" * 78)
    text = next(s for s in pe.sections if s["name"] == ".text")
    text_va = text["va"] + pe.imagebase
    end = text_va + text["rawsize"]
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
        if got == 0:
            cur += 1
        else:
            cur = last
    callers = [i.address for i in insns
               if i.mnemonic == "call" and i.operands
               and i.operands[0].type == X86_OP_IMM
               and (i.operands[0].imm & 0xFFFFFFFF) == REGISTER_FN]
    print(f"  callers of 0x7C978A: {len(callers)}")
    for a in callers[:20]:
        print(f"    0x{a:08X}")
    # 看这些调用点前是否都是 push <fn>
    push_before = 0
    idx = {i.address: k for k, i in enumerate(insns)}
    for a in callers:
        k = idx[a]
        if k > 0 and insns[k - 1].mnemonic == "push":
            push_before += 1
    print(f"  of which preceded by 'push imm': {push_before}/{len(callers)}")
    chk("0x7C978A is called as 'push fn; call' (atexit registration shape)",
        len(callers) > 0 and push_before == len(callers),
        f"{push_before}/{len(callers)}")

    print()
    print("=" * 78)
    print("== STEP 3  singleton constructor 0x5BDA40 — which vtable does it install?")
    print("=" * 78)
    cb = disasm_fn(pe, md, CTOR, 0x800)
    print(f"  0x5BDA40 body: {len(cb)} insns")
    a_at = [i.address for i in cb
            if i.mnemonic == "mov" and len(i.operands) == 2
            and i.operands[1].type == X86_OP_IMM
            and (i.operands[1].imm & 0xFFFFFFFF) == VT_A]
    b_at = [i.address for i in cb
            if i.mnemonic == "mov" and len(i.operands) == 2
            and i.operands[1].type == X86_OP_IMM
            and (i.operands[1].imm & 0xFFFFFFFF) == VT_B]
    print(f"  installs TABLE_A 0x7E1964 at: {[f'0x{x:08X}' for x in a_at]}")
    print(f"  installs TABLE_B 0x7F0344 at: {[f'0x{X:08X}' for X in b_at]}")
    for i in cb[:40]:
        mark = ""
        for op in i.operands:
            if op.type == X86_OP_IMM and op.imm in (VT_A, VT_B):
                mark = "  <== VTABLE"
        print(f"    {i.address:08X}  {i.bytes.hex():<22} {i.mnemonic} {i.op_str}{mark}")
    chk("constructor 0x5BDA40 installs TABLE_A", len(a_at) >= 1,
        f"{len(a_at)} site(s)")
    chk("constructor 0x5BDA40 does NOT install TABLE_B", len(b_at) == 0,
        f"{len(b_at)} site(s)")

    print()
    print("=" * 78)
    print("== STEP 4  all callers of 0x652C00 (the table-B installer)")
    print("=" * 78)
    c_reinit = [i.address for i in insns
                if i.mnemonic == "call" and i.operands
                and i.operands[0].type == X86_OP_IMM
                and (i.operands[0].imm & 0xFFFFFFFF) == REINIT]
    print(f"  callers of 0x652C00: {len(c_reinit)}")
    for a in c_reinit:
        print(f"    0x{a:08X}")
    chk("0x652C00 has exactly 1 caller and it is 0x40D1F7",
        c_reinit == [0x40D1F7], str([f"0x{x:08X}" for x in c_reinit]))

    print()
    print("=" * 78)
    print("== STEP 5  all callers of 0x40D1B0 (the exit callback)")
    print("=" * 78)
    cb_callers = [i.address for i in insns
                  if i.mnemonic == "push" and i.operands
                  and i.operands[0].type == X86_OP_IMM
                  and (i.operands[0].imm & 0xFFFFFFFF) == EXIT_CB]
    print(f"  push 0x40D1B0 sites: {[f'0x{x:08X}' for x in cb_callers]}")
    chk("0x40D1B0 is only referenced as an atexit argument",
        cb_callers == [0x40D19A], str([f"0x{x:08X}" for x in cb_callers]))

    print()
    print("=" * 78)
    print("== STEP 6  verdict: runtime vtable of the singleton")
    print("=" * 78)
    ctor_a = len(a_at) >= 1
    ctor_b = len(b_at) >= 1
    only_exit_installs_b = (c_reinit == [0x40D1F7])
    if ctor_a and not ctor_b and only_exit_installs_b:
        print("  [已证] 单例在 0x5BDA40 构造时安装的是 **表A 0x7E1964**。")
        print("  [已证] 表B 0x7F0344 的唯一写入点是 0x652C00，而它只被 0x40D1F7 调用，")
        print("         0x40D1F7 位于 0x40D1B0 —— 该函数仅以 'push 0x40D1B0; call 0x7C978A'")
        print("         形式被引用（atexit 注册形状）⇒ **退出期**才执行。")
        print("  [推翻] §347「运行时是表B ⇒ slot5 = One_Time」的推论前提不成立：")
        print("         运行期单例 vtable = 表A，slot5 = 0x5BDF30（不是 One_Time）。")
        print("  [推论] One_Time(0x652CF0) **不**经 slot5 在运行期被调用。")
        print("         但它仍可能被直接 call —— 前脚本已证全 .text **0 处 E8 调它**。")
        print("         ⇒ One_Time 在运行期**不可达**，除非有非 E8/非 slot5 的路径。")
        print("  [对 ② 的影响] 崩溃栈上的返回地址 0x652D51 说明 One_Time **确实跑过**，")
        print("         因此上面这条推论必须再核：0x5BDA40 是否只是基类构造、")
        print("         雷达类另有构造点写表B（需查 0x652B45 / 0x6587AC / 0x6A4F78 三处）。")
        verdict = "RUNTIME_TABLE_A_EXIT_INSTALLS_B"
    else:
        print("  [未定] 构造/写入格局与预期不符，见上文各步实测。")
        verdict = "UNDETERMINED"

    print()
    passed = sum(1 for _, ok, _ in CHECKS if ok)
    print(f"checks passed: {passed}/{len(CHECKS)}")
    print(f"verdict: {verdict}")
    print("RESULT:", "ALL PASS" if passed == len(CHECKS) else "FAIL")
    return 0 if passed == len(CHECKS) else 1


if __name__ == "__main__":
    sys.exit(main())
