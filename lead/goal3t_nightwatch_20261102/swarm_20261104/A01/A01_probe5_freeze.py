# -*- coding: utf-8 -*-
"""A01 probe 5: 冻结链缺口补全。
1) 0x53B560 全函数 + 跳表 + 调用者 + 状态全局 0xA9FA98/0xA9FAB0 引用
2) 0x684060 其余调用者上下文 (0x657CA0 / 0x6DF703 / 0x6E4086)
3) 函数 0x684060 内 0x68411B-0x684120 缺口字节
4) 0x683610 头部（清 +0x62C 的复位函数）与 0x684180 尾部 0x6841F6..0x684240
5) GameMode 0xA8B238 全部写点
6) 0x62C 间接写排查（add/sub imm 0x62c 形式）
7) 0x5d4d50 头部（pump?）
只读 gamemd.exe。"""
import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\goal3t_nightwatch_20261102\swarm_20261104")
from ra2tool import Engine

eng = Engine()
print("== coverage ==")
print("coverage: %.2f%%  insns=%d  resync=%d" % eng.coverage)

def show(lo, hi, mark=()):
    print("\n--- 0x%08X .. 0x%08X ---" % (lo, hi))
    for a, b, m, o in eng.disasm(lo, hi - lo):
        t = " <<<" if a in mark else ""
        print("0x%08X  %-22s %-8s %s%s" % (a, b, m, o, t))

print("== 1) 0x53B560 jump table ==")
for i in range(4):
    print("  state %d -> 0x%08X" % (i, eng.u32(0x53B770 + 4 * i)))

show(0x53B560, 0x53B7D0, {0x53B612, 0x53B6E6})

print("\n== callers of 0x53B560 ==")
for ins in eng.stream:
    if ins.mnemonic == "call" and ins.op_str == "0x53b560":
        print("0x%08X  call 0x53b560" % ins.address)

print("\n== refs to 0xA9FA98 / 0xA9FAB0 ==")
for g in (0xA9FA98, 0xA9FAB0):
    print("-- 0x%08X --" % g)
    for va, rw, mn, ops in eng.disp_hits(g):
        print("0x%08X %s  %-8s %s" % (va, rw, mn, ops))

print("\n== 2) other callers of 0x684060 ==")
for site in (0x657CA0, 0x6DF703, 0x6E4086):
    show(site - 0x40, site + 0x50, {site})
print("--- 0x657CC8 (call 0x684180) ctx ---")
show(0x657CB0, 0x657D10, {0x657CC8})

print("\n== 3) gap bytes 0x68411B..0x684124 ==")
print(eng.rd(0x68411B, 9).hex(" "))

print("\n== 4a) 0x683610 head .. 0x683690 ==")
show(0x683610, 0x683690)
print("== 4b) 0x6841F6 .. 0x684240 (0x684180 zero-branch tail) ==")
show(0x6841F6, 0x684244)

print("\n== 5) GameMode 0xA8B238 write points ==")
for va, rw, mn, ops in eng.disp_hits(0x00A8B238):
    if rw == "W":
        print("0x%08X %s  %-8s %s" % (va, rw, mn, ops))

print("\n== 6) indirect 0x62c forms (imm in op_str) ==")
n = 0
for ins in eng.stream:
    if "0x62c" in ins.op_str and ins.mnemonic not in ("mov", "lea", "cmp", "test", "inc", "dec", "add", "sub"):
        continue
    if ins.mnemonic in ("add", "sub") and ins.op_str.endswith("0x62c"):
        print("0x%08X  %-8s %s" % (ins.address, ins.mnemonic, ins.op_str))
        n += 1
print("add/sub-imm-0x62c count: %d" % n)

print("\n== 7) 0x5d4d50 head ==")
show(0x5D4D50, 0x5D4DC0)
