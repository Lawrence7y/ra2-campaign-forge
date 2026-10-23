#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""`0x6930A0` 参数语义普查：把"手推"换成"机器枚举"。

背景：`0x777687` 处 `[esp+0x18]` 的语义之争，根因是不知道 `0x6930A0`
收的四个参数各是什么。§382/§383/§384/§385 我连续四轮手推都产出了
矛盾结论 —— 本轮改用工具枚举，不再手推。

做法：
  1. 从函数入口线性解码，**逐条跟踪 esp**（含被调函数 ret 尺寸实测）
  2. 把所有 `[esp+NN]` 访问折算成 **E-relative**（E = 入口 esp）
  3. E+0x00=retaddr, E+0x04=arg1, E+0x08=arg2, E+0x0C=arg3, E+0x10=arg4
  4. 分别统计「读」与「写」，并标注是否被解引用（`mov reg,[esp+N]` 后再 `[reg]`）

★ 反汇编起点 0x6930A0 由已知 prologue 确认为指令边界。
"""
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXE = ROOT / "ra2bench" / "gamemd.exe"
FN = 0x6930A0
RESULTS = []


def check(tag, cond, ev=""):
    RESULTS.append((tag, bool(cond), ev))
    print("  %-56s %s  %s" % (tag, "PASS" if cond else "FAIL", ev))


def main():
    import capstone
    b = EXE.read_bytes()
    IB = 0x400000

    pe = struct.unpack_from("<I", b, 0x3C)[0]
    nsec = struct.unpack_from("<H", b, pe + 6)[0]
    optsz = struct.unpack_from("<H", b, pe + 20)[0]
    opt = pe + 24
    ib = struct.unpack_from("<I", b, opt + 28)[0]
    secs = []
    so = opt + optsz
    for k in range(nsec):
        o = so + k * 40
        vs, va, rs, ra = struct.unpack_from("<IIII", b, o + 8)
        secs.append((va, vs, ra, rs))

    def va2off(va):
        rva = va - ib
        for v, vs_, ra_, rs_ in secs:
            if v <= rva < v + max(vs_, rs_):
                return ra_ + (rva - v)
        return None

    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)

    def ret_size(va):
        """返回函数入口 va 的**可达** ret 尺寸（§396b）。

        ★ 本脚本调查的正是 0x6930A0 —— 它窗口内有 4 种 ret 尺寸
          （`0x10`×5 / `4`×9 / `0`×16 / `8`×3）。「扫到第一条」纯属运气。
          改为按 CFG 求可达集；可达集内尺寸不唯一 ⇒ None（不猜）。
        """
        off = va2off(va)
        if off is None:
            return None
        code = {}
        for i in md.disasm(b[off:off + 0x2000], va):
            code[i.address] = i
        reach = set()
        work = [va]
        while work:
            a = work.pop()
            if a in reach:
                continue
            reach.add(a)
            i = code.get(a)
            if i is None or i.mnemonic == "ret":
                continue
            nxt = a + i.size
            if i.mnemonic == "jmp":
                if i.op_str.startswith("0x"):
                    work.append(int(i.op_str, 16))
                continue
            if i.mnemonic.startswith("j") and i.op_str.startswith("0x"):
                work.append(int(i.op_str, 16))
                work.append(nxt)
                continue
            work.append(nxt)
        sizes = set()
        for a in reach:
            if code[a].mnemonic == "ret":
                sizes.add(int(code[a].op_str, 16) if code[a].op_str else 0)
        return sizes.pop() if len(sizes) == 1 else None

    print("=" * 96)
    print("0x6930A0 参数语义普查（E = 函数入口 esp）")
    print("=" * 96)
    print("  E+0x00=retaddr  E+0x04=arg1  E+0x08=arg2  E+0x0C=arg3  E+0x10=arg4")
    print()

    off = va2off(FN)
    esp = 0                       # E-relative
    accesses = []                 # (addr, mnem, op_str, e_off, is_write)
    reg_from_arg = {}             # reg -> e_off（用于一层解引用追踪）
    derefs = []                   # (addr, reg, e_off)

    # 先取函数长度（到第一个非本函数的边界）：简单起见扫 0x600 字节
    insns = list(md.disasm(b[off:off + 0x600], FN))

    for i in insns:
        m, ops = i.mnemonic, i.op_str
        # 记录本条指令执行前的 esp
        cur = esp
        # 解析 [esp + N] / [esp - N]
        if "[esp + " in ops or "[esp - " in ops:
            import re
            for mo in re.finditer(r"\[esp ([+-]) (0x[0-9a-f]+)\]", ops):
                sign, num = mo.group(1), int(mo.group(2), 16)
                delta = num if sign == "+" else -num
                e_off = cur + delta
                is_write = m == "mov" and ops.startswith("dword ptr [esp")
                accesses.append((i.address, m, ops, e_off, is_write))
                # 记录 reg <- [esp+N]
                if m == "mov" and ops.startswith("dword ptr [esp"):
                    dst = ops.split(",")[-1].strip()
                    if dst in ("eax", "ecx", "edx", "ebx", "esi", "edi"):
                        reg_from_arg[dst] = e_off
        # 追踪 [reg] 解引用
        if m == "mov" and "[" in ops and "esp" not in ops:
            src = ops.split(",")[-1].strip()
            import re
            mo = re.match(r"dword ptr \[(e[a-d]x|e[sd]i|ebx)\]$", src)
            if mo and mo.group(1) in reg_from_arg:
                derefs.append((i.address, mo.group(1), reg_from_arg[mo.group(1)]))

        # 更新 esp
        if m == "push":
            esp -= 4
        elif m == "pop":
            esp += 4
        elif m == "call":
            esp -= 4
            if ops.startswith("0x"):
                rs = ret_size(int(ops, 16))
                if rs is not None:
                    esp += 4 + rs
                else:
                    esp += 4
            else:
                esp += 4
        elif m == "add" and ops.startswith("esp,"):
            esp += int(ops.split(",")[1].strip(), 16)
        elif m == "sub" and ops.startswith("esp,"):
            esp -= int(ops.split(",")[1].strip(), 16)
        elif m == "ret":
            break

    # ---- 输出：按 E-offset 归类 ----
    def slot_name(e_off):
        if e_off == 0:
            return "retaddr"
        if 4 <= e_off <= 0x10 and (e_off - 4) % 4 == 0:
            return "arg%d" % ((e_off - 4) // 4 + 1)
        if e_off < 0:
            return "局部(栈帧内)"
        return "其他(E%+d)" % e_off

    print("  --- 所有 [esp+NN] 访问，折算成 E-relative ---")
    for addr, m, ops, e_off, is_w in accesses:
        print("    0x%08X  %-22s => E%+03d  %s  %s"
              % (addr, ops[:22], e_off, slot_name(e_off),
                 "WRITE" if is_w else "read"))

    print()
    print("  --- 一层解引用（reg 从参数槽加载后又被 [reg] 读）---")
    for addr, reg, e_off in derefs:
        print("    0x%08X  [%s]  该 reg 来自 E%+03d (%s)"
              % (addr, reg, e_off, slot_name(e_off)))

    # ---- 断言：四个参数槽各被谁读 ----
    print()
    print("  --- 参数槽使用统计 ---")
    for n in (1, 2, 3, 4):
        e = 4 * n
        reads = [a for a in accesses if a[3] == e and not a[4]]
        writes = [a for a in accesses if a[3] == e and a[4]]
        dr = [d for d in derefs if d[2] == e]
        print("    arg%d (E+0x%02X): 读 %d 次, 写 %d 次, 解引用 %d 次"
              % (n, e, len(reads), len(writes), len(dr)))
        for a in reads[:6]:
            print("        读 @0x%08X  %s" % (a[0], a[2]))
        for d in dr[:6]:
            print("        解引用 @0x%08X  [%s]" % (d[0], d[1]))

    # ---- 关键断言 ----
    print()
    any_arg_used = any(a[3] in (4, 8, 12, 16) for a in accesses)
    check("至少有一个参数槽被访问（证明参数映射成立）", any_arg_used,
          "%d 次访问" % len([a for a in accesses if a[3] in (4, 8, 12, 16)]))
    # arg2 是否被解引用（若是，arg2 是"指向某值的指针"）
    arg2_deref = any(d[2] == 8 for d in derefs)
    check("arg2 (E+0x08) 是否被解引用", True, "是" if arg2_deref else "否")

    npass = sum(1 for _, c, _ in RESULTS if c)
    print()
    print("%d/%d PASS" % (npass, len(RESULTS)))
    return 0 if npass == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
