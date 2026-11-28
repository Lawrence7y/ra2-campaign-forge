#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R194 第九刀：递归下降指令图（不是线性扫描），把「序列化辅助函数调用面」从两套互相矛盾的
计数（lite 线性 118/94/6 vs 播种合并 262/268/85）收敛成一个可复算的数。

方法（每一步都可被否掉）：
  R1 种子集合 = .text 起点 ∪ 全段 E8/E9/EB/0F8x rel32 字节模式命中的落点 ∪ 填充后的首指令。
  R2 从每个种子线性解码到控制转移（ret / jmp / 无条件离开当前块）或 >=2 个 0xCC/0x90 填充为止；
     jcc/jmp 的落点入队。每解码到一条指令就把地址登记进 MAP（幂等）。
  R3 计数口径 = MAP 里 mnemonic == call 且 op_str 是立即数落点的条目（去重按调用点地址）。
  R4 三套口径并列输出（lite 线性 / 播种合并 / 递归下降），并给「递归下降是上界还是下界」的判据：
     若某调用点能从 .text 起点可达 ⇒ 是下界（漏不了可达路径），不可达的孤立函数只能由种子覆盖。
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
def d(va, n=64):
    return list(md.disasm_lite(at(va, n), va))

# ---- 先看两个执行员漏掉的 CRC 表引用点所在函数 ----
def dump(va, lim=200, tag=''):
    print('   --- %s %08X ---' % (tag, va))
    for a, sz, mn, op in d(va, lim):
        print('     %08X  %-24s %-8s %s' % (a, at(a, sz).hex(' ').upper(), mn, op))
        if mn.startswith('ret'): break
dump(0x4A1FA0, 60, 'jump target after tail')
dump(0x4A1FA0+0x33, 260, 'after')

# ---- R2 递归下降 ----
start = LO
seeds = set([start])
# 字节模式种子：E8/E9 rel32
p = 0; L = len(BUF)
while p < L - 5:
    b = BUF[p]
    if b in (0xE8, 0xE9):
        rel = struct.unpack_from('<i', BUF, p + 1)[0]
        t = LO + p + 5 + rel
        if in_text(t): seeds.add(t)
        p += 5; continue
    p += 1
print('   字节模式种子 %d 个' % len(seeds))
MAP = {}
work = collections.deque(sorted(seeds))
guard = 0
while work and guard < 400000:
    s = work.popleft(); guard += 1
    va = s; pad = 0
    while in_text(va) and guard < 400000:
        if va in MAP:
            break
        got = d(va, 32)
        if not got: break
        a, sz, mn, op = got[0]
        if a != va: break
        MAP[va] = (sz, mn, op)
        if mn == 'ret' or mn.startswith('ret'):
            break
        if mn in ('jmp', 'call', 'je', 'jne', 'jz', 'jnz', 'jbe', 'jae', 'jb', 'ja', 'jl', 'jg', 'jle',
                  'jge', 'js', 'jns', 'jo', 'jno', 'jp', 'jnp', 'loop', 'loope', 'loopne'):
            if op.startswith('0x'):
                try: t = int(op, 16)
                except ValueError: t = None
                if t is not None and in_text(t): work.append(t)
            if mn == 'jmp': break
        if mn in ('int3', 'nop'):
            pad += 1
            if pad >= 2: break
        else: pad = 0
        va = va + sz
print('   递归下降 MAP %d 条指令，种子队列残留 %d，循环 %d 次' % (len(MAP), len(work), guard))
ck('R2a 递归下降覆盖 > 50% 的 .text 字节（防止只覆盖局部）',
   sum(v[0] for v in MAP.values()) > 0.5 * (HI - LO),
   (sum(v[0] for v in MAP.values()), HI - LO))

TGT = (0x4A1CA0, 0x4A1D50, 0x4A1DE0, 0x4A1C10, 0x4A1FB0)
c = {t: [] for t in TGT}
ind = 0
for a, (sz, mn, op) in MAP.items():
    if mn == 'call':
        if op.startswith('0x'):
            try: t = int(op, 16)
            except ValueError: t = None
            if t in c: c[t].append(a)
        else: ind += 1
print('   递归下降 call 计数：%s；间接 call %d' % ({hex(k): len(v) for k, v in c.items()}, ind))
for t in TGT[:3]:
    print('     %s 前 12 个调用点 %s' % (hex(t), [hex(x) for x in sorted(c[t])[:12]]))

# 宿主归属（函数起点 = MAP 里「前一条不是顺序落下的指令」的地址）
def starts():
    st = set([LO])
    for a, (sz, mn, op) in MAP.items():
        if mn in ('call', 'jmp') and op.startswith('0x'):
            try: t = int(op, 16)
            except ValueError: continue
            if in_text(t): st.add(t)
        nxt = a + sz
        if nxt in MAP:
            prev_ok = mn in ('nop', 'int3')
            if (MAP[nxt][1] in ('nop', 'int3')) and mn.startswith('ret'): st.add(nxt)
            if mn == 'jmp': st.add(nxt)
    return st
ST = sorted(starts())
import bisect
def host(a):
    i = bisect.bisect_right(ST, a) - 1
    return ST[i] if i >= 0 else None
for t in TGT:
    hs = collections.Counter(host(x) for x in c[t])
    print('     %s 宿主函数数 %d：%s' % (hex(t), len(hs), [(hex(k), v) for k, v in hs.most_common(6)]))
hs410 = collections.Counter(host(x) for x in c[0x4A1CA0]) | collections.Counter(host(x) for x in c[0x4A1D50])
ck('R2b 0x410410 是否是两个写路径的宿主起点之一',
   0x410410 in hs410, [hex(k) for k in hs410 if k == 0x410410])

# ---- CRC 表引用面（递归下降口径）----
tab = sorted(a for a, (sz, mn, op) in MAP.items() if '0x81f7b4' in op)
print('   递归下降口径 CRC 表引用 %d 处：%s' % (len(tab), [hex(x) for x in tab]))
pat = struct.pack('<I', 0x81F7B4)
bh = []; p = BUF.find(pat)
while p >= 0:
    bh.append(LO + p); p = BUF.find(pat, p + 1)
print('   字节口径 disp32 命中 %d 处：%s' % (len(bh), [hex(x) for x in bh]))
ck('R2c 递归下降口径的 CRC 表引用数 == 字节口径命中数（7 处，不是执行员报的 5 处）',
   len(tab) == len(bh) == 7, (len(tab), len(bh)))
ck('R2d 每个字节命中都落在一条已解码指令内（disp32 位置 = 指令地址 + 3）',
   all((h - 3) in MAP for h in bh), [hex(h) for h in bh if (h - 3) not in MAP])
for h in bh:
    a = h - 3
    print('     %08X  %s' % (a, at(a, MAP[a][0]).hex(' ').upper()))
print('\n断言 %d 条，FAIL %d 条' % (N, len(fails)))
if fails: print('FAIL 明细：' + ' | '.join(fails)); sys.exit(1)
