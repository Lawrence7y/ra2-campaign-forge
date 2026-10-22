# -*- coding: utf-8 -*-
"""待办 9 决定性一段：多级回溯 —— 273 处 call [reg+0x14] 里有没有
「对象 == 雷达单例 0x87F7E8」的站点。

前一段（`_slot5_callers.py`）的漏洞
----------------------------------
它的 `reg_source()` 只回溯**一层**。对典型形态：

    0x????: mov ecx, 0x87F7E8      ; ecx = 雷达单例对象地址
    0x????: mov edx, [ecx]         ; edx = vtable（= 表B 0x7F0344）
    0x????: call [edx+0x14]        ; slot5 = One_Time

它只会报 `src = mem[ecx+0x0]`，归入 "mem[vtable]"，**不继续追 ecx**。
⇒ 若真有这种站点，会被漏掉，得出错误的「0 处从单例取址」。

本脚本
------
对每处 `call [reg+0x14]`：
1. 找 reg 的来源 `S1`（如 `mem[ecx+0]`）⇒ 得基址寄存器 R1。
2. 再回溯 R1 的来源 `S2`（如 `imm(0x87F7E8)`）⇒ 得基址 R2。
3. 继续到固定深度（4 层）或到函数头。
4. 若链上任一环节解析为 `imm(0x87F7E8)` 或 `abs[0x87F7E8]` ⇒ 标记 SINGLETON 命中。
5. 同时判定对象虚表**是否可静态确定为表B**：若 R1 的来源是 `mem[imm(0x87F7E8)]`，
   则 vtable = [0x87F7E8] 运行期值，静态只能给出「表A 或 表B」。

附加：确认 0x5BDF30 的真实函数头（前一段只解出 6 条指令，疑边界错误）。
"""
import hashlib
import struct
import sys
from pathlib import Path

from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import (X86_OP_IMM, X86_OP_MEM, X86_OP_REG,
                          X86_REG_EAX, X86_REG_EBX, X86_REG_ECX, X86_REG_EDX,
                          X86_REG_ESI, X86_REG_EDI, X86_REG_EBP, X86_REG_ESP)

BIN = Path(r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe")
WANT_SHA8 = "73201cc0"
SINGLETON = 0x87F7E8
VT_A = 0x7E1964
VT_B = 0x7F0344
ONE_TIME = 0x652CF0
TABLE_A_SLOT5 = 0x5BDF30
SLOT5 = 0x14

REGS = {X86_REG_EAX: "eax", X86_REG_EBX: "ebx", X86_REG_ECX: "ecx",
        X86_REG_EDX: "edx", X86_REG_ESI: "esi", X86_REG_EDI: "edi",
        X86_REG_EBP: "ebp", X86_REG_ESP: "esp"}
VOLATILE = (X86_REG_EAX, X86_REG_ECX, X86_REG_EDX)

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

    def sec_of(self, va):
        rva = va - self.imagebase
        for s in self.sections:
            if s["va"] <= rva < s["va"] + max(s["vsize"], s["rawsize"]):
                return s["name"]
        return None


def main():
    print("=" * 78)
    print("== STEP 0  identity + decode")
    print("=" * 78)
    data = BIN.read_bytes()
    sha = hashlib.sha256(data).hexdigest()
    print(f"sha256 : {sha}")
    if not chk("sha256[:8] == " + WANT_SHA8, sha[:8] == WANT_SHA8, sha[:8]):
        return 1
    pe = PE(data)
    text = next(s for s in pe.sections if s["name"] == ".text")
    text_va = text["va"] + pe.imagebase
    end = text_va + text["rawsize"]
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = True

    insns = []
    stops = []
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
            stops.append(cur)
            cur += 1
        else:
            cur = last
    print(f"decoded {len(insns)} instructions, {len(stops)} undecodable stops")
    if not chk("decoded > 500000", len(insns) > 500000, str(len(insns))):
        return 1
    idx_of = {i.address: k for k, i in enumerate(insns)}

    def func_head_of(k):
        """向前找函数头：前一条是 ret/int3/hlt，或前面全是 nop 填充。"""
        j = k - 1
        while j >= 0:
            p = insns[j]
            if p.mnemonic in ("ret", "retn", "int3", "hlt"):
                return j + 1
            if p.mnemonic == "nop":
                j -= 1
                continue
            j -= 1
        return 0

    def last_write_before(k, reg):
        """在 k 之前找 reg 的最后一次写，返回 (kind, detail, insn)。"""
        j = k - 1
        head = func_head_of(k)
        while j >= head:
            p = insns[j]
            if p.operands and p.operands[0].type == X86_OP_REG \
                    and p.operands[0].reg == reg:
                if p.mnemonic == "mov" and len(p.operands) == 2:
                    s = p.operands[1]
                    if s.type == X86_OP_MEM:
                        base = s.mem.base
                        if base == 0:
                            return ("abs", s.mem.disp & 0xFFFFFFFF, p)
                        return ("mem", (REGS.get(base, "?"), s.mem.disp & 0xFFFFFFFF), p)
                    if s.type == X86_OP_REG:
                        return ("reg", s.reg, p)
                    if s.type == X86_OP_IMM:
                        return ("imm", s.imm & 0xFFFFFFFF, p)
                if p.mnemonic == "lea" and len(p.operands) == 2:
                    s = p.operands[1]
                    if s.type == X86_OP_MEM and s.mem.base == 0 and s.mem.index == 0:
                        return ("imm", s.mem.disp & 0xFFFFFFFF, p)
                if p.mnemonic == "call":
                    return ("callret", None, p)
                if p.mnemonic in ("xor", "sub") and len(p.operands) == 2 \
                        and p.operands[1].type == X86_OP_REG \
                        and p.operands[1].reg == reg:
                    return ("zero", None, p)
                return ("other", p.mnemonic, p)
            if p.mnemonic == "call" and reg in VOLATILE:
                return ("clobber", None, p)
            j -= 1
        return ("undef", None, None)

    print()
    print("=" * 78)
    print("== STEP 1  multi-level trace of all call [reg+0x14] sites")
    print("=" * 78)
    sites = []
    for k, i in enumerate(insns):
        if i.mnemonic != "call" or len(i.operands) != 1:
            continue
        op = i.operands[0]
        if op.type != X86_OP_MEM or op.mem.base == 0 or op.mem.index != 0:
            continue
        if op.mem.disp != SLOT5:
            continue
        sites.append((k, i, op.mem.base))
    print(f"total sites: {len(sites)}")

    singleton_hits = []
    vtable_from_singleton = []
    trace_kinds = {}
    for k, i, reg in sites:
        chain = []
        cur_reg = reg
        depth = 0
        hit = False
        vt_from_single = False
        prev_was_single = False
        while depth < 5:
            kind, detail, ins = last_write_before(k if depth == 0 else idx_of[ins.address], cur_reg)
            if ins is None:
                chain.append("undef")
                break
            if kind == "imm" and detail == SINGLETON:
                chain.append(f"imm(SINGLETON)")
                hit = True
                if prev_was_single:
                    vt_from_single = True
                break
            if kind == "abs" and detail == SINGLETON:
                chain.append(f"abs(SINGLETON)")
                hit = True
                break
            if kind == "mem":
                base, disp = detail
                chain.append(f"mem[{base}+0x{disp:X}]")
                if base == "?":
                    break
                # 若上一层就是 imm(SINGLETON)，则这一层 mem[?] 是 [单例]
                prev_was_single = (disp == 0)
                # 继续追 base 寄存器
                rb = None
                for rr, nm in REGS.items():
                    if nm == base:
                        rb = rr
                        break
                if rb is None or rb == X86_REG_ESP:
                    break
                cur_reg = rb
                k = idx_of[ins.address]
                depth += 1
                continue
            if kind == "reg":
                chain.append(f"reg({REGS.get(detail,'?')})")
                if detail == X86_REG_ESP:
                    break
                cur_reg = detail
                k = idx_of[ins.address]
                depth += 1
                continue
            chain.append(kind)
            break
        key = " -> ".join(chain)
        trace_kinds[key] = trace_kinds.get(key, 0) + 1
        if hit:
            singleton_hits.append((i.address, key))
            if vt_from_single or "mem[ecx+0x0] -> imm(SINGLETON)" in key:
                vtable_from_singleton.append((i.address, key))

    print()
    print("  top trace shapes:")
    for k2, v in sorted(trace_kinds.items(), key=lambda x: -x[1])[:12]:
        print(f"    {v:>4}  {k2}")

    print()
    print(f"  sites whose chain reaches SINGLETON 0x87F7E8 : {len(singleton_hits)}")
    for a, ch in singleton_hits:
        print(f"     site 0x{a:08X}  {ch}")
    chk("no slot5 site is reached from the singleton literal",
        len(singleton_hits) == 0, str(len(singleton_hits)))

    print()
    print("=" * 78)
    print("== STEP 2  0x5BDF30 real function head (prior decode gave only 6 insns)")
    print("=" * 78)
    # 向前找边界
    back = pe.read(TABLE_A_SLOT5 - 0x40, 0x40)
    print(f"  bytes before 0x{TABLE_A_SLOT5:X}:")
    for off in range(0, 0x40, 16):
        row = back[off:off + 16]
        print(f"    {TABLE_A_SLOT5 - 0x40 + off:08X}  {row.hex(' ')}")
    k = idx_of.get(TABLE_A_SLOT5)
    if k is not None:
        print(f"  linear-decode boundary at 0x{TABLE_A_SLOT5:X}: {insns[k].mnemonic} {insns[k].op_str}")
        chk("0x5BDF30 IS an instruction boundary", True, insns[k].mnemonic)
    else:
        chk("0x5BDF30 IS an instruction boundary", False, "not in linear decode")

    # 解 0x5BDF30 起 0x100 字节
    code = pe.read(TABLE_A_SLOT5, 0x100)
    body = []
    for i in md.disasm(code, TABLE_A_SLOT5):
        body.append(i)
        if i.mnemonic in ("ret", "retn"):
            break
    print(f"  0x5BDF30 body: {len(body)} insns")
    for i in body:
        print(f"    {i.address:08X}  {i.bytes.hex():<20} {i.mnemonic} {i.op_str}")
    chk("0x5BDF30 body is longer than 6 insns (prior 6 was a bad boundary)",
        len(body) > 6, f"{len(body)} insns")

    print()
    print("=" * 78)
    print("== STEP 3  verdict")
    print("=" * 78)
    if len(singleton_hits) == 0:
        print("  [已证] 273 处 call [reg+0x14] 中，**0 处**的对象可静态追到雷达单例。")
        print("         ⇒ One_Time 不被任何『直接拿单例调 slot5』的站点调用。")
        print("         ⇒ 它只可能经『遍历对象集合、对每个对象调 slot5』被调用；")
        print("           但 slot5 在表A 上是 0x5BDF30（非 One_Time）⇒ 该类槽语义随类变，")
        print("           通用遍历调 slot5 时，雷达对象是否被遍历到**无法静态确定**。")
        print("  [结论] 分岔 A/B **不能**由静态普查定案。需要真机断点 0x652CF0。")
        verdict = "A_B_UNDETERMINED_NEEDS_RUNTIME_BP"
    else:
        print(f"  [已证] 找到 {len(singleton_hits)} 处直接以单例调 slot5 的站点：")
        for a, ch in singleton_hits:
            print(f"         0x{a:08X}  {ch}")
        print("         ⇒ 这些站点是 One_Time 的调用者，需看其宿主时机。")
        verdict = "SINGLETON_CALLERS_FOUND"

    print()
    passed = sum(1 for _, ok, _ in CHECKS if ok)
    print(f"checks passed: {passed}/{len(CHECKS)}")
    print(f"verdict: {verdict}")
    print("RESULT:", "ALL PASS" if passed == len(CHECKS) else "FAIL")
    return 0 if passed == len(CHECKS) else 1


if __name__ == "__main__":
    sys.exit(main())
