#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R194 第十刀：把「序列化辅助函数的调用面」的计数争议收敛成区间（下界/上界），而不是
在三个互相矛盾的点估计之间挑一个。

口径定义（每一条都是字节流的不变式，不依赖解码成败）：
  U（上界）= .text 里所有 5 字节模式 E8 + rel32 且 LO+off+5+rel32 == 目标 的位置。
             这是「可能是 call」的上界：包含落在数据里/指令中间的假命中。
  L（下界）= U 中「该位置被递归下降解码成一条 call 指令 且 op_str 等于目标」的位置。
  F（假命中）= U 里被解码成非 call 指令、或根本不落在任何已解码指令起始处的位置。
判定：U = L + F，且 L 的每个元素都能给出该 call 指令的完整 5 字节 hex。
"""
import sys, struct, collections, capstone
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
fails = []; N = 0
def ck(nm, c, d=''):
    global N; N += 1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ') + nm + ((' | ' + str(d)) if d != '' else ''))
T = P.B['.text']; LO = T['lo']; HI = T['hi_file']; RP = T['rawptr']
BUF = P.RAW[RP:RP + (HI - LO)]
def in_text(x): return x is not None and LO <= x < HI
def at(va, n): return BUF[va - LO: va - LO + n]
def d(va, n=32): return list(md.disasm_lite(at(va, n), va))

# 先解释 0x4A200E 处的第三个 CRC 例程
print('   --- 0x4A1FE8..0x4A2030 ---')
for a, sz, mn, op in d(0x4A1FE8, 90):
    print('     %08X  %-24s %-8s %s' % (a, at(a, sz).hex(' ').upper(), mn, op))
    if mn.startswith('ret'): break

# 递归下降（沿用第九刀方法，精简）
seeds = {LO}
p = 0
while p < len(BUF) - 5:
    if BUF[p] in (0xE8, 0xE9):
        rel = struct.unpack_from('<i', BUF, p + 1)[0]
        t = LO + p + 5 + rel
        if in_text(t): seeds.add(t)
        p += 5; continue
    p += 1
MAP = {}
work = collections.deque(sorted(seeds)); guard = 0
while work and guard < 500000:
    s = work.popleft(); guard += 1; va = s; pad = 0
    while in_text(va) and guard < 500000:
        if va in MAP: break
        got = d(va, 32)
        if not got or got[0][0] != va: break
        a, sz, mn, op = got[0]; MAP[va] = (sz, mn, op)
        if mn.startswith('ret'): break
        if mn in ('jmp','call','je','jne','jz','jnz','jbe','jae','jb','ja','jl','jg','jle','jge','js','jns','jo','jno','jp','jnp','loop','loope','loopne'):
            if op.startswith('0x'):
                try: t = int(op, 16)
                except ValueError: t = None
                if t is not None and in_text(t): work.append(t)
            if mn == 'jmp': break
        if mn in ('int3','nop'):
            pad += 1
            if pad >= 2: break
        else: pad = 0
        va += sz
print('   MAP %d 条' % len(MAP))

def bracket(target):
    U = []
    q = 0
    while q < len(BUF) - 5:
        if BUF[q] == 0xE8:
            rel = struct.unpack_from('<i', BUF, q + 1)[0]
            if LO + q + 5 + rel == target: U.append(LO + q)
        q += 1
    L = [a for a in U if a in MAP and MAP[a][1] == 'call' and MAP[a][2] == hex(target)]
    F = [a for a in U if a not in L]
    Fnoc = [a for a in F if a not in MAP]
    Fmis = [a for a in F if a in MAP]
    return U, L, F, Fnoc, Fmis

print('\n   目标       U(上界)  L(下界)  F(假命中)  其中未解码/解码为他物')
res = {}
for t in (0x4A1CA0, 0x4A1D50, 0x4A1DE0, 0x4A1C10, 0x4A1FB0):
    U, L, F, Fnoc, Fmis = bracket(t)
    res[t] = (len(U), len(L), len(F), len(Fnoc), len(Fmis))
    print('   %s  %5d  %5d  %5d  %d/%d' % (hex(t), len(U), len(L), len(F), len(Fnoc), len(Fmis)))
    print('      L 前 8 个（含字节）：%s' % ' '.join('%08X:%s' % (a, at(a, 5).hex(' ').upper()) for a in L[:8]))
    print('      F 样例（前 4）：%s' % ' '.join('%08X(%s)' % (a, 'undec' if a in Fnoc else MAP[a][1]) for a in F[:4]))
ck('B1 每个目标都满足 U = L + F（记账自洽）', all(u == l + f for u, l, f, _, _ in res.values()), res)
ck('B2 0x4A1CA0 的下界 L >= 80（不是三轮里最小的 94 那种量级的零头）', res[0x4A1CA0][1] >= 80, res[0x4A1CA0][:2])
ck('B3 0x4A1C10（第三个写路径，执行员称「读侧校验」）确实有真实调用点 L >= 4',
   res[0x4A1C10][1] >= 4, res[0x4A1C10][:2])
ck('B4 0x4A1FB0 只有 1 个真实调用点（0x4A1E4B，与第六刀一致）', res[0x4A1FB0][1] == 1, res[0x4A1FB0][:2])

# CRC 表引用：7 处 disp32，逐处给出所在指令与宿主
pat = struct.pack('<I', 0x81F7B4)
bh = []
p = BUF.find(pat)
while p >= 0:
    bh.append(LO + p); p = BUF.find(pat, p + 1)
print('\n   CRC 表 disp32 命中 %d 处：%s' % (len(bh), [hex(x) for x in bh]))
rows = []
for h in bh:
    ins = h - 3
    if ins in MAP:
        mn = MAP[ins][1]; ok = True
    else:
        g = d(ins, 16)
        mn = g[0][2] if g and g[0][0] == ins else '?'
        ok = False
    rows.append((hex(ins), ok, mn, at(ins, 7).hex(' ').upper()))
    print('     ins=%s decoded=%s %-6s %s' % (rows[-1][0], ok, mn, rows[-1][3]))
ck('B5 CRC 表引用共 7 处（执行员报 5 处漏了 0x4A1FD3 与 0x4A200E 两处）',
   len(bh) == 7, len(bh))
ck('B6 7 处全部落在 mov reg,[reg*4+0x81f7b4] 形态的指令上（SIB + disp32）',
   all(r[2] == 'mov' and 'B4 F7 81 00' in r[3] for r in rows), rows)
print('\n断言 %d 条，FAIL %d 条' % (N, len(fails)))
if fails: print('FAIL 明细：' + ' | '.join(fails)); sys.exit(1)
