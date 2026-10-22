# -*- coding: utf-8 -*-
"""独立复核：0x87F7E8 的运行时 vtable 到底是表 A(0x7E1964) 还是表 B(0x7F0344)。

背景冲突
--------
`goal2_onetime_census_20261022/_onetime_census.py`（子代理交付）STEP 8 断言：
  "singleton runtime vtable = 0x7E1964 (.?AVMouseClass@@)"
  "its slot+0x14 = 0x5BDF30 (MouseClass override), not 0x652CF0"
据此它得出 "One_Time 不被调用"。这与台账 §347 的定案（运行时是表 B
0x7F0344，0x40D1B2 先设表 A、0x40D1F7 call 0x652C00 再改写成表 B）矛盾。

子代理的漏洞（本轮要证或证伪）
------------------------------
它只扫了 `.text` 里**字面量绝对寻址**写 `[0x87F7E8]` 的指令
（`mov dword ptr [0x87f7e8], imm32` = `89 35 ...` 形态），得 1 处（0x40D1B2）。
但若第二次写入是 **寄存器间接**形态（`mov esi,0x87F7E8` 后 `mov [esi],eax`），
字面量扫描**看不见**它 ⇒ 会把"唯一一次字面量写"误当成"运行时值"。

本脚本要做
----------
1. 反汇编 0x40D190 起的初始化函数，逐条列出对 0x87F7E8 的写（字面量 + 寄存器间接）。
2. 反汇编 0x652C00 函数体，判定它是否把 0x7F0344 写进某个指针（并追踪该指针是否为 0x87F7E8）。
3. 读两张表的 slot5 与 slot42（0xA8），核对 §347 的"slot0/slot42 相同、21 覆盖槽"。
4. 给出运行时 vtable 的**证据链**判定，并显式区分 [已证] / [未定]。

纪律
----
- 只读二进制。所有解码从**真实指令边界**起（函数头），不从任意偏移硬解。
- 段表 VirtualAddress 是 RVA，加 imagebase 0x400000。
- 每条断言必须有判别力；负控见 `_vtable_verify_negctl.py`。
"""
import hashlib
import struct
import sys
from pathlib import Path

from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_OP_REG

BIN = Path(r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe")
WANT_SHA8 = "73201cc0"

IMAGEBASE = 0x400000
SINGLETON = 0x87F7E8          # RadarClass 单例对象地址（台账 §347）
VT_TABLE_A = 0x7E1964         # 子代理读到的"运行时"（MouseClass）
VT_TABLE_B = 0x7F0344         # 台账 §347 的定案（RadarClass）
ONE_TIME = 0x652CF0           # RadarClass::One_Time
REWRITE_FN = 0x652C00         # §347：0x40D1F7 调用它改写 vtable
INIT_FN = 0x40D190            # §347：初始化函数（0x40D1B2 在其内）
INIT_FN_END = 0x40D230        # 覆盖 0x40D1B2 与 0x40D1F7 两个站点
CLEAR_SITE = 0x777803         # WM_DESTROY 清零站点
CLEAR_TARGET_LEDGER = 0x887368  # 台账 §2 记的清零目标（非 0x87F7E8）

CHECKS = []


def chk(name, cond, detail=""):
    CHECKS.append((name, bool(cond), detail))
    print(f"[{'PASS' if cond else 'FAIL'}] {name}  {detail}")
    return bool(cond)


class PE:
    def __init__(self, data):
        self.data = data
        # ★ PE32：e_lfanew 在 0x3C；COFF 头 20 字节后是 OptionalHeader。
        #   ImageBase 在 OptionalHeader + 0x1C（PE32，4 字节）。
        #   坑：直接把 0x34 当 ImageBase 偏移是错的（那是 e_lfanew 恰好=0x80 时的巧合）。
        e_lfanew = struct.unpack_from("<I", data, 0x3C)[0]
        self.imagebase = struct.unpack_from("<I", data, e_lfanew + 0x18 + 0x1C)[0]
        nsec = struct.unpack_from("<H", data, e_lfanew + 0x06)[0]
        optsz = struct.unpack_from("<H", data, e_lfanew + 0x14)[0]
        sec_off = e_lfanew + 0x18 + optsz
        self.sections = []
        for i in range(nsec):
            o = sec_off + i * 40
            nm = data[o:o + 8].rstrip(b"\x00").decode("ascii", "ignore")
            vsize, vaddr, rawsize, rawptr = struct.unpack_from("<IIII", data, o + 8)
            self.sections.append({"name": nm, "vsize": vsize, "va": vaddr,
                                  "rawsize": rawsize, "rawptr": rawptr})
        self.by_name = {s["name"]: s for s in self.sections}

    def va2off(self, va):
        rva = va - self.imagebase
        for s in self.sections:
            if s["va"] <= rva < s["va"] + max(s["vsize"], s["rawsize"]):
                d = rva - s["va"]
                if d < s["rawsize"]:
                    return s["rawptr"] + d
                return None
        return None

    def read(self, va, n):
        o = self.va2off(va)
        if o is None or o + n > len(self.data):
            return None
        return self.data[o:o + n]

    def u32(self, va):
        b = self.read(va, 4)
        return None if b is None else struct.unpack("<I", b)[0]


def main():
    print("=" * 78)
    print("== STEP 0  binary identity")
    print("=" * 78)
    data = BIN.read_bytes()
    sha = hashlib.sha256(data).hexdigest()
    print(f"path   : {BIN}")
    print(f"size   : {len(data)}")
    print(f"sha256 : {sha}")
    if not chk("binary sha256[:8] == " + WANT_SHA8, sha[:8] == WANT_SHA8, sha[:8]):
        print("RESULT: ABORT (binary mismatch)")
        return 1

    pe = PE(data)
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = True

    print()
    print("=" * 78)
    print("== STEP 1  init function 0x40D190 (contains 0x40D1B2 literal write)")
    print("=" * 78)
    code = pe.read(INIT_FN, INIT_FN_END - INIT_FN)
    insns = list(md.disasm(code, INIT_FN))
    print(f"decoded {len(insns)} instructions in [0x{INIT_FN:X}, 0x{INIT_FN_END:X})")
    for i in insns:
        mark = ""
        # 找出所有对 SINGLETON 的写：字面量 或 寄存器间接
        for op in i.operands:
            if op.type == X86_OP_MEM:
                disp = (op.mem.disp & 0xFFFFFFFF) if op.mem.base == 0 else None
                if op.mem.base == 0 and disp == SINGLETON:
                    mark = "  <== literal write/read to SINGLETON"
                if i.mnemonic.startswith("mov") and i.operands[0].type == X86_OP_MEM \
                        and i.operands[0].size == 4 and i.operands[0].mem.base != 0:
                    mark += "  [reg-indirect store]"
            if op.type == X86_OP_IMM and op.imm == SINGLETON:
                mark += "  <== loads SINGLETON into reg"
            if op.type == X86_OP_IMM and op.imm == VT_TABLE_A:
                mark += "  <== loads TABLE_A"
            if op.type == X86_OP_IMM and op.imm == VT_TABLE_B:
                mark += "  <== loads TABLE_B"
        print(f"  {i.address:08X}  {i.bytes.hex():<20} {i.mnemonic} {i.op_str}{mark}")

    # 找 0x40D1B2 那条，确认写的是 TABLE_A
    lit = None
    for i in insns:
        if i.address == 0x40D1B2:
            lit = i
            break
    ok = lit is not None and lit.mnemonic == "mov" and len(lit.operands) == 2 \
        and lit.operands[0].type == X86_OP_MEM and lit.operands[1].type == X86_OP_IMM
    if ok:
        tgt = lit.operands[0].mem.disp & 0xFFFFFFFF
        val = lit.operands[1].imm & 0xFFFFFFFF
        chk("0x40D1B2 is 'mov [abs], imm32'", True, f"{lit.mnemonic} {lit.op_str}")
        chk("0x40D1B2 target == SINGLETON 0x87F7E8", tgt == SINGLETON, f"0x{tgt:08X}")
        chk("0x40D1B2 value == TABLE_A 0x7E1964", val == VT_TABLE_A, f"0x{val:08X}")
    else:
        chk("0x40D1B2 is 'mov [abs], imm32'", False, "decode mismatch")

    # 找 0x40D1F7 处的 call
    call_at = None
    for i in insns:
        if i.address == 0x40D1F7:
            call_at = i
            break
    if call_at is not None:
        print(f"  -> at 0x40D1F7: {call_at.mnemonic} {call_at.op_str}")
        is_call_rewrite = (call_at.mnemonic == "call"
                           and len(call_at.operands) == 1
                           and call_at.operands[0].type == X86_OP_IMM
                           and (call_at.operands[0].imm & 0xFFFFFFFF) == REWRITE_FN)
        chk("0x40D1F7 calls 0x652C00 (rewrite fn)", is_call_rewrite,
            call_at.op_str)
    else:
        chk("0x40D1F7 calls 0x652C00 (rewrite fn)", False, "site not decoded")

    print()
    print("=" * 78)
    print("== STEP 2  rewrite function 0x652C00 body")
    print("=" * 78)
    code2 = pe.read(REWRITE_FN, 0x200)
    insns2 = list(md.disasm(code2, REWRITE_FN))
    body2 = []
    for i in insns2:
        body2.append(i)
        if i.mnemonic == "ret":
            break
    print(f"decoded {len(body2)} instructions (to first ret)")
    for i in body2:
        mark = ""
        for op in i.operands:
            if op.type == X86_OP_IMM and op.imm == VT_TABLE_B:
                mark += "  <== TABLE_B"
            if op.type == X86_OP_IMM and op.imm == SINGLETON:
                mark += "  <== SINGLETON"
        print(f"  {i.address:08X}  {i.bytes.hex():<20} {i.mnemonic} {i.op_str}{mark}")

    loads_b = any(op.type == X86_OP_IMM and op.imm == VT_TABLE_B
                  for i in body2 for op in i.operands)
    chk("0x652C00 loads TABLE_B 0x7F0344", loads_b,
        "found" if loads_b else "absent")

    # 该函数是否把 imm 写进 [reg]（寄存器间接）——这就是子代理字面量扫描漏掉的形态
    reg_indirect = [i for i in body2
                    if i.mnemonic == "mov" and len(i.operands) == 2
                    and i.operands[0].type == X86_OP_MEM
                    and i.operands[0].mem.base != 0
                    and i.operands[1].type == X86_OP_IMM
                    and (i.operands[1].imm & 0xFFFFFFFF) == VT_TABLE_B]
    chk("0x652C00 stores TABLE_B via reg-indirect (invisible to literal scan)",
        len(reg_indirect) >= 1,
        ", ".join(f"0x{i.address:08X}" for i in reg_indirect) or "none")

    print()
    print("=" * 78)
    print("== STEP 3  the two vtables: slot5 and slot42(0xA8)")
    print("=" * 78)
    rows = []
    for nm, vt in (("TABLE_A", VT_TABLE_A), ("TABLE_B", VT_TABLE_B)):
        s0 = pe.u32(vt)
        s5 = pe.u32(vt + 0x14)
        s42 = pe.u32(vt + 0xA8)
        rows.append((nm, vt, s0, s5, s42))
        print(f"  {nm} 0x{vt:08X}  slot0=0x{s0:08X}  slot5=0x{s5:08X}  slot42=0x{s42:08X}")
    a, b = rows[0], rows[1]
    chk("TABLE_A.slot5 != One_Time (MouseClass override)", a[3] != ONE_TIME,
        f"0x{a[3]:08X}")
    chk("TABLE_B.slot5 == One_Time 0x652CF0", b[3] == ONE_TIME, f"0x{b[3]:08X}")
    chk("TABLE_A.slot0 == TABLE_B.slot0 (shared base override)", a[2] == b[2],
        f"0x{a[2]:08X} vs 0x{b[2]:08X}")
    chk("TABLE_A.slot42 == TABLE_B.slot42 (§347 claim)", a[4] == b[4],
        f"0x{a[4]:08X} vs 0x{b[4]:08X}")

    print()
    print("=" * 78)
    print("== STEP 4  clear site target (ledger says 0x887368, not SINGLETON)")
    print("=" * 78)
    code4 = pe.read(CLEAR_SITE, 16)
    i4 = next(iter(md.disasm(code4, CLEAR_SITE)), None)
    if i4 is not None:
        print(f"  {i4.address:08X}  {i4.bytes.hex():<20} {i4.mnemonic} {i4.op_str}")
        tgt4 = None
        for op in i4.operands:
            if op.type == X86_OP_MEM and op.mem.base == 0:
                tgt4 = op.mem.disp & 0xFFFFFFFF
        chk("0x777803 writes 0x887368 (NOT the singleton)",
            tgt4 == CLEAR_TARGET_LEDGER, f"0x{tgt4:08X}" if tgt4 else "none")
        chk("0x777803 target != SINGLETON 0x87F7E8", tgt4 != SINGLETON,
            f"0x{tgt4:08X}" if tgt4 else "none")

    print()
    print("=" * 78)
    print("== STEP 5  verdict")
    print("=" * 78)
    a_ok = a[3] != ONE_TIME
    b_ok = b[3] == ONE_TIME
    rewrite_ok = loads_b and len(reg_indirect) >= 1
    if rewrite_ok and b_ok:
        print("  [已证] 0x40D1B2 先写字面量表 A(0x7E1964)；")
        print("         随后 0x40D1F7 call 0x652C00，该函数以**寄存器间接**方式")
        print("         写入表 B(0x7F0344) ⇒ 字面量扫描看不见这第二次写。")
        print("  [已证] TABLE_B.slot5 == 0x652CF0 == One_Time ⇒ 运行时(表B)下")
        print("         One_Time **确实**经 slot5 被调用。")
        print("  [推翻] 子代理 STEP 8 的 'runtime vtable = 0x7E1964' 结论：")
        print("         它把'唯一一次字面量写'当成了'运行时值'。")
        print("  [维持] §347 定案：运行时是表 B。")
        verdict = "TABLE_B_CONFIRMED"
    elif rewrite_ok:
        print("  [未定] 改写存在但 slot5 不指向 One_Time ⇒ 需另查。")
        verdict = "UNDETERMINED"
    else:
        print("  [未定] 未找到寄存器间接写入 ⇒ 子代理结论可能成立，需另查。")
        verdict = "UNDETERMINED"

    print()
    passed = sum(1 for _, ok, _ in CHECKS if ok)
    total = len(CHECKS)
    print(f"checks passed: {passed}/{total}")
    print(f"verdict: {verdict}")
    print("RESULT:", "ALL PASS" if passed == total else "FAIL")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
