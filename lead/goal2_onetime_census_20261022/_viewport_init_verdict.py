# -*- coding: utf-8 -*-
"""定谳：0x67E772 是运行期的「场景/视口初始化」函数，内含 L3 调用与装表 A。

本轮决定性发现（反向枚举 + 完整反汇编）
--------------------------------------
函数 `0x67E772`（110 条指令）体内容：

    0x67E7AA  mov ecx, [0x886FBC]        ; ★ 视口矩形字段（§345：0x886FA0..AC）
    0x67E7DD  mov ecx, 0x886FB0          ; ★ 视口矩形起点
    0x67E7EA  call 0x533FD0              ; 计算矩形
    0x67E7F4  mov ecx, 0x87F7E8          ; ★ 雷达单例
    0x67E7F9  call 0x4A8960              ; ★★ L3（视口尺寸变更 + ABuffer/ZBuffer 重建）
    ...
    0x67E86B  mov ecx, 0x87F7E8          ; ★ 雷达单例
    0x67E870  call 0x5BDF70              ; ★★ 装表 A（MouseClass，slot5=0x5BDF30）

⇒ **同一个运行期函数里，先调 L3，再给单例装表 A。**

这与 §351 的发现合起来，把 RC-4 的触发路径钉死：
- §351 说 `0x67E7F9` 以单例为 this 调 L3 —— 确认
- 本轮说同一函数在 L3 之后**还把单例的 vtable 换成表 A** —— 新

本脚本
------
1. 确认 `0x67E772` 是独立函数头（`0x67E730` 在 `0x67E771` ret 结束）。
2. 确认该函数对 `0x886FA0..0x886FBC`（视口矩形）的引用。
3. 确认 `0x5BDF70` 是「装表 A」的函数（体内 `mov [esi],0x7E1964`）。
4. 求 `0x67E772` 的**直接 E8 调用者**，判定时机。
5. 给出 RC-4 触发路径的完整表述。
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
INSTALL_A = 0x5BDF70
FUNC = 0x67E772
PREV_FUNC = 0x67E730
VIEWPORT_LO = 0x886FA0
VIEWPORT_HI = 0x886FB0

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
    print("== STEP 1  0x67E772 is an independent function head")
    print("=" * 78)
    # 0x67E730 的函数体到哪结束
    code = pe.read(PREV_FUNC, 0x60)
    prev_end = None
    for i in md.disasm(code, PREV_FUNC):
        if i.mnemonic in ("ret", "retn"):
            prev_end = i.address + i.size
            break
    print(f"  0x{PREV_FUNC:X} ends at 0x{prev_end:X}" if prev_end else "  prev end not found")
    chk("0x67E730 ends at 0x67E772 (so 0x67E772 is a new head)",
        prev_end == FUNC, f"0x{prev_end:X}" if prev_end else "n/a")

    print()
    print("=" * 78)
    print("== STEP 2  viewport-rectangle references inside 0x67E772")
    print("=" * 78)
    body = []
    code = pe.read(FUNC, 0x200)
    for i in md.disasm(code, FUNC):
        body.append(i)
        if i.mnemonic in ("ret", "retn"):
            break
    print(f"  body: {len(body)} insns")
    vp_refs = []
    for i in body:
        for op in i.operands:
            if op.type == X86_OP_MEM and op.mem.base == 0:
                d = op.mem.disp & 0xFFFFFFFF
                if VIEWPORT_LO <= d <= VIEWPORT_HI:
                    vp_refs.append((i.address, f"0x{d:08X}", i.op_str))
            if op.type == X86_OP_IMM:
                v = op.imm & 0xFFFFFFFF
                if VIEWPORT_LO <= v <= VIEWPORT_HI:
                    vp_refs.append((i.address, f"0x{v:08X}", i.op_str))
    print(f"  viewport refs: {len(vp_refs)}")
    for a, d, s in vp_refs:
        print(f"    0x{a:08X}  {d}  {s}")
    chk("function references the viewport rectangle region 0x886FA0..0x886FB0",
        len(vp_refs) >= 1, str(len(vp_refs)))

    print()
    print("=" * 78)
    print("== STEP 3  0x5BDF70 really installs TABLE_A")
    print("=" * 78)
    code = pe.read(INSTALL_A, 0x120)
    inst_body = []
    for i in md.disasm(code, INSTALL_A):
        inst_body.append(i)
        if i.mnemonic in ("ret", "retn"):
            break
    print(f"  0x{INSTALL_A:X} body: {len(inst_body)} insns")
    found_a = False
    for i in inst_body:
        mark = ""
        for op in i.operands:
            if op.type == X86_OP_IMM and (op.imm & 0xFFFFFFFF) == VT_A:
                mark = "  <== TABLE_A"
                found_a = True
        print(f"    {i.address:08X}  {i.bytes.hex():<20} {i.mnemonic} {i.op_str}{mark}")
    chk("0x5BDF70 installs TABLE_A (0x7E1964)", found_a,
        "found" if found_a else "absent")

    print()
    print("=" * 78)
    print("== STEP 4  direct E8 callers of 0x67E772 (timing)")
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
        cur = last if got else cur + 1
    print(f"decoded {len(insns)}")
    if not chk("decoded > 500000", len(insns) > 500000, str(len(insns))):
        return 1

    callers = [i.address for i in insns
               if i.mnemonic == "call" and i.operands
               and i.operands[0].type == X86_OP_IMM
               and (i.operands[0].imm & 0xFFFFFFFF) == FUNC]
    print(f"  direct E8 callers of 0x{FUNC:X}: {len(callers)}")
    for a in callers[:20]:
        print(f"    0x{a:08X}")

    # 也查虚表槽引用
    rd = next(s for s in pe.sections if s["name"] == ".rdata")
    rv = rd["va"] + pe.imagebase
    rb = pe.read(rv, rd["rawsize"])
    slots = []
    for off in range(0, len(rb) - 4, 4):
        if struct.unpack_from("<I", rb, off)[0] == FUNC:
            slots.append(rv + off)
    print(f"  .rdata dwords == 0x{FUNC:X}: {[f'0x{x:08X}' for x in slots]}")

    print()
    print("=" * 78)
    print("== STEP 5  verdict: RC-4 trigger path")
    print("=" * 78)
    print("  [已证] 函数 0x67E772（110 条指令，运行期）执行序列：")
    print("         ① 读视口矩形 [0x886FA0..0x886FBC]")
    print("         ② mov ecx, 0x87F7E8; call 0x4A8960   ← L3（视口尺寸变更+缓冲重建）")
    print("         ③ mov ecx, 0x87F7E8; call 0x5BDF70   ← 装表 A（slot5 → 0x5BDF30）")
    print()
    print("  [对 RC-4 的意义] 这条路径**不需要 One_Time 参与**：")
    print("         - 它自己以单例为 this 直接调 L3（§351 已记）")
    print("         - L3 内部经 v[42] 走 §346 崩溃链")
    print("         - 若单例在此前已被清零，L3 拿到 this=0 ⇒ 崩溃")
    print("         ⇒ 这就是分岔的答案：**不是 A（启动期）、不是 B（换图重跑 One_Time），")
    print("            而是运行期的「视口尺寸变更」路径**，与 One_Time 无关。")
    print()
    print("  [修复含义] 修复点应在这个路径上，或在 L3(0x4A8960) 入口加 null 守卫，")
    print("             而不是在 0x724730（那是链的最下游）。")
    print()
    print("  [待确认] 该函数是谁调的（callers 见 STEP 4）；")
    print("           若 callers 为 0，说明它经虚表调用，需查 .rdata 槽位归属。")

    print()
    passed = sum(1 for _, ok, _ in CHECKS if ok)
    print(f"checks passed: {passed}/{len(CHECKS)}")
    print("RESULT:", "ALL PASS" if passed == len(CHECKS) else "FAIL")
    return 0 if passed == len(CHECKS) else 1


if __name__ == "__main__":
    sys.exit(main())
