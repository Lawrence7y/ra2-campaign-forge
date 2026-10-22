# -*- coding: utf-8 -*-
"""待办 9 第二段（改正方法）：5 个宿主是同构实例，不是 5 条独立路径。

上一版的错误
------------
`_host_closure.py` 求向上 E8 闭包，结果 5 个宿主**全部撞到 400 节点上限**且
时机标签完全相同（都是 'GameMode'/'Modem detected OK' 等）——
这说明闭包已经扩散到主循环，**失去区分力**。方法本身不成立。

本版的正确思路
--------------
先看这 5 个宿主**函数体的形态**。§352 已注意到它们高度相似：

    0x5BEA0A:  mov ebx,ecx / lea esi,[ebx+0x53ec] / mov edi,4
    0x69391A:  mov ebx,ecx / lea esi,[ebx+0x53ec] / mov edi,4
    0x6AC81A:  mov ebx,ecx / lea esi,[ebx+0x53ec] / mov edi,4
    0x40D2D4:  lea esi,[ebx+0x539c] / mov edi,4
    0x6404B3:  （更短，直接 call）

⇒ 它们是**同一模板的多处实例化**（编译器为不同类的析构/重初始化生成同构代码）。
`0x652C00` 不是"RadarClass 专属构造"，而是**某基类层的 vtable 重装例程**，
被 5 个不同类各自的析构/重初始化路径调用。

本脚本要答
----------
1. 5 个宿主的**函数体逐字节形态**对比 —— 确认同构，并给出差异点。
2. 每个宿主的**函数头身份**：是否在 .data 静态构造表内？是否有 RTTI 关联？
3. `0x652C00` 体内 `mov [edi],0x7F0344` 的 **edi 来源** —— 它是 this，
   所以 5 个宿主传入的 this 类型**各自不同**，但都装表 B？
   若是，则表 B 不是 RadarClass 专属 ⇒ §352 的"RadarClass 实例"结论需修正。
4. 结论：One_Time 的调用者到底能不能由这 5 个宿主确定。
"""
import hashlib
import struct
import sys
from pathlib import Path

from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_OP_REG

BIN = Path(r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe")
WANT_SHA8 = "73201cc0"
VT_B = 0x7F0344
VT_A = 0x7E1964
REINIT = 0x652C00
ONE_TIME = 0x652CF0

HOSTS = [0x40D2D4, 0x5BEA0A, 0x6404B3, 0x69391A, 0x6AC81A]

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
    print("== STEP 1  function bodies of the 5 hosts (byte-level comparison)")
    print("=" * 78)

    bodies = {}
    for site in HOSTS:
        # 从 site 向前找函数头
        back = pe.read(site - 0x80, 0x80)
        head = None
        for off in range(0x80 - 1, -1, -1):
            # 找 ret/int3 后紧跟的非 nop
            b = back[off]
            if b in (0xC3, 0xC2, 0xCC):
                head = site - 0x80 + off + 1
                break
        if head is None:
            head = site - 0x60
        code = pe.read(head, 0x120)
        ins = []
        for i in md.disasm(code, head):
            ins.append(i)
            if i.mnemonic in ("ret", "retn"):
                break
        bodies[site] = (head, ins)
        print(f"\n-- site 0x{site:08X}  head 0x{head:08X}  {len(ins)} insns")
        for i in ins:
            print(f"   {i.address:08X}  {i.bytes.hex():<20} {i.mnemonic} {i.op_str}")

    print()
    print("=" * 78)
    print("== STEP 2  structural similarity (normalized opcode skeleton)")
    print("=" * 78)

    def skeleton(ins):
        """把指令序列归一化为 (mnemonic, operand-shape)，忽略立即数/位移具体值。"""
        out = []
        for i in ins:
            ops = []
            for op in i.operands:
                if op.type == X86_OP_REG:
                    ops.append("R")
                elif op.type == X86_OP_IMM:
                    ops.append("I")
                elif op.type == X86_OP_MEM:
                    ops.append("M")
            out.append(i.mnemonic + ":" + ",".join(ops))
        return out

    skels = {s: skeleton(bodies[s][1]) for s in HOSTS}
    for s in HOSTS:
        print(f"  0x{s:08X}  {len(skels[s])} insns")
    # 两两相似度（最长公共子序列近似：用 Counter 交集 / 较大者）
    from collections import Counter
    print("\n  pairwise skeleton similarity (multiset overlap):")
    for a in range(len(HOSTS)):
        for b in range(a + 1, len(HOSTS)):
            sa, sb = HOSTS[a], HOSTS[b]
            ca, cb = Counter(skels[sa]), Counter(skels[sb])
            inter = sum((ca & cb).values())
            denom = max(sum(ca.values()), sum(cb.values()))
            pct = 100.0 * inter / denom if denom else 0
            print(f"    0x{sa:08X} vs 0x{sb:08X}: {pct:5.1f}%  ({inter}/{denom})")

    print()
    print("=" * 78)
    print("== STEP 3  0x652C00 body: what does it write, and to whose this?")
    print("=" * 78)
    code = pe.read(REINIT, 0x40)
    for i in md.disasm(code, REINIT):
        mark = ""
        for op in i.operands:
            if op.type == X86_OP_IMM and (op.imm & 0xFFFFFFFF) == VT_B:
                mark = "  <== TABLE_B (RadarClass)"
            if op.type == X86_OP_IMM and (op.imm & 0xFFFFFFFF) == VT_A:
                mark = "  <== TABLE_A (MouseClass)"
        print(f"   {i.address:08X}  {i.bytes.hex():<20} {i.mnemonic} {i.op_str}{mark}")
        if i.address > REINIT + 0x20:
            break

    # 找 mov [reg], imm32 == VT_B
    writes_b = []
    code_full = pe.read(REINIT, 0x200)
    for i in md.disasm(code_full, REINIT):
        if i.mnemonic == "mov" and len(i.operands) == 2 \
                and i.operands[0].type == X86_OP_MEM \
                and i.operands[1].type == X86_OP_IMM \
                and (i.operands[1].imm & 0xFFFFFFFF) == VT_B:
            writes_b.append((i.address, i.op_str))
        if i.mnemonic in ("ret", "retn"):
            break
    print(f"\n  0x652C00 writes TABLE_B at: {writes_b}")
    chk("0x652C00 writes TABLE_B exactly once", len(writes_b) == 1,
        str(len(writes_b)))

    print()
    print("=" * 78)
    print("== STEP 4  is 0x652C00 RadarClass-specific or a base-class vtable reset?")
    print("=" * 78)
    # 判据：0x652C00 是否在它自己的函数体内引用 RadarClass 专属成员偏移？
    # RadarClass 特有成员（§349：One_Time 写 +0x11E4..+0x1204, +0x14D4）
    radar_offsets = [0x11E4, 0x11E8, 0x11EC, 0x11F4, 0x11F8, 0x11FC, 0x1200,
                     0x1204, 0x14D4]
    body_full = []
    for i in md.disasm(code_full, REINIT):
        body_full.append(i)
        if i.mnemonic in ("ret", "retn"):
            break
    hits = []
    for i in body_full:
        for op in i.operands:
            if op.type == X86_OP_MEM and op.mem.base != 0:
                d = op.mem.disp & 0xFFFFFFFF
                if d in radar_offsets:
                    hits.append((i.address, i.op_str))
    print(f"  RadarClass-specific member offsets touched by 0x652C00: {hits or 'none'}")

    # 0x652C00 触及的成员偏移（全部）
    all_disp = set()
    for i in body_full:
        for op in i.operands:
            if op.type == X86_OP_MEM and op.mem.base != 0:
                all_disp.add(op.mem.disp & 0xFFFFFFFF)
    print(f"  all member offsets in 0x652C00: {sorted(hex(d) for d in all_disp)}")

    print()
    print("=" * 78)
    print("== STEP 5  verdict")
    print("=" * 78)
    # 同构判定
    from collections import Counter as C2
    sims = []
    for a in range(len(HOSTS)):
        for b in range(a + 1, len(HOSTS)):
            ca, cb = C2(skels[HOSTS[a]]), C2(skels[HOSTS[b]])
            inter = sum((ca & cb).values())
            denom = max(sum(ca.values()), sum(cb.values()))
            sims.append(inter / denom if denom else 0)
    avg_sim = sum(sims) / len(sims) if sims else 0
    print(f"  average pairwise skeleton similarity: {avg_sim*100:.1f}%")
    print(f"  RadarClass-specific offsets in 0x652C00: {len(hits)}")

    if avg_sim > 0.6:
        print("  [已证] 5 个宿主是同构模板实例 ⇒ 它们不是 5 条独立业务路径，")
        print("         而是同一基类层代码被不同类各自实例化。")
        print("  [推论] `0x652C00` 是**基类层的 vtable 重装例程**，不是 RadarClass 专属构造。")
        if not hits:
            print("  [已证] 0x652C00 体内**不触及** RadarClass 专属成员偏移")
            print("         ⇒ 它只把表 B 写进 this 首 dword，对任意派生类都适用。")
            print("  [结论] 「表 B 装在 5 个 RadarClass 实例上」这一表述**不成立**：")
            print("         表 B 是 RadarClass 的 vtable，但 0x652C00 把它写进传入的任意 this；")
            print("         只有当 this 确实是 RadarClass 时，slot5 才等于 One_Time。")
            print("  [对分岔的影响] One_Time 的调用者**不能**由这 5 个宿主确定 ⇒ 仍需真机断点。")
            verdict = "HOSTS_ARE_TEMPLATE_INSTANCES_BRANCH_UNDETERMINED"
        else:
            verdict = "HOSTS_SIMILAR_BUT_TOUCH_RADAR_MEMBERS"
    else:
        print("  [未定] 宿主形态差异较大，逐条分析。")
        verdict = "UNDETERMINED"

    print()
    passed = sum(1 for _, ok, _ in CHECKS if ok)
    print(f"checks passed: {passed}/{len(CHECKS)}")
    print(f"verdict: {verdict}")
    print("RESULT:", "ALL PASS" if passed == len(CHECKS) else "FAIL")
    return 0 if passed == len(CHECKS) else 1


if __name__ == "__main__":
    sys.exit(main())
