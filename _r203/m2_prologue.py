#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R203 m2：13 条线性扫描失步的 vtable 槽位目标 —— 它们是不是真函数入口（就地 detail 解码）。
只对 13 个命中地址开 detail=True，不对整段开。
E1 逐条 detail 解码，检查是否 MSVC 序言；
E2 解码到首个 ret/int3 的长度，是否在合理函数长度内；
E3 该地址是否能在"另一条路径"上被证明是入口（区间起点 / 直接调用目标 / 前一字节是 ret/int3）；
E4 反控：取 13 个非入口地址（区间内部任意 +1 偏移）做同样检查，应几乎不满足序言。"""
import sys, struct, json, bisect, collections
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
import capstone
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
mdd = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
fails = []; N = 0
def ck(nm, c, d=''):
    global N; N += 1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ') + nm + ((' | ' + str(d)) if d != '' else ''))
T = P.B['.text']; LO = T['lo']; HI = T['hi_file']; RAW = P.RAW
RP = T['rawptr']
def by(va, n=32): return RAW[RP + va - LO: RP + va - LO + n]
def s32(v): return struct.unpack('<i', struct.pack('<I', v))[0]
def wv(sn):
    s = P.B[sn]; n = s['rawsize'] // 4
    return s['lo'], struct.unpack_from('<%dI' % n, P.RAW, s['rawptr']), n
COL = {}
for sn in ('.rdata', '.data'):
    base, w, n = wv(sn)
    for i in range(n - 4):
        if w[i] not in (0, 1, 2) or w[i + 2] != 0: continue
        if P.where(w[i + 3]) != '.data' or P.where(w[i + 4]) != '.rdata': continue
        nm = P.cstr(w[i + 3] + 8, 400)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base + 4 * i] = dict(mdisp=s32(w[i + 1]), name=nm.decode('latin1'))
VT = {}
for sn in ('.rdata', '.data'):
    base, w, n = wv(sn)
    for i in range(n):
        if LO <= w[i] < HI and P.dw(base + 4 * i - 4) in COL: VT[base + 4 * i] = P.dw(base + 4 * i - 4)
SLOT = {}
for vt in VT:
    k = 0
    while k <= 400:
        t = P.dw(vt + 4 * k)
        if not (t is not None and LO <= t < HI): break
        SLOT[(vt, 4 * k)] = t; k += 1
# 线性扫描
BUF = RAW[RP:RP + (HI - LO)]
INS = []; p = 0
while p < len(BUF):
    g = False
    for off, sz, mn, op in md.disasm_lite(BUF[p:p + 65536], LO + p):
        g = True; INS.append((off, sz, mn, op)); p += sz
    if not g: p += 1
INS.sort(); ADDRS = [a for a, _, _, _ in INS]; ASET = set(ADDRS)
TGT = sorted(set(SLOT.values()))
MISS = [t for t in TGT if t not in ASET]
ck('E0 槽位去重目标 6692 / 线性扫描未覆盖 13', len(TGT) == 6692 and len(MISS) == 13, (len(TGT), len(MISS)))
REG = []; st = LO
for a, sz, mn, op in INS:
    if mn.startswith('ret') or mn == 'int3':
        REG.append((st, a + sz)); st = a + sz
if st < HI: REG.append((st, HI))
RL = set(r[0] for r in REG)
# 直接调用目标
DIRT = set(int(op, 16) for a, s, mn, op in INS if mn == 'call' and op.startswith('0x') and LO <= int(op, 16) < HI)
PRO = [('push ebp', 'mov ebp,esp'), ('sub esp',), ('push ebx',), ('mov esi,ecx',)]
def decode(va, maxn=600):
    out = []
    for ins in mdd.disasm(by(va, 1400), va):
        out.append((ins.address, ins.size, ins.mnemonic, ins.op_str.replace(' ', '')))
        if ins.mnemonic.startswith('ret') or ins.mnemonic == 'int3' or len(out) >= maxn: break
    return out
def ispro(seq):
    # MSVC 典型序言：前 6 条内出现 sub esp,imm 或 push 链 + mov reg,ecx
    m = [x[2] for x in seq[:6]]; o = [x[3] for x in seq[:6]]
    has_esp = any(m[i] == 'sub' and o[i].startswith('esp,') for i in range(min(6, len(m))))
    has_push = any(m[i] == 'push' for i in range(min(6, len(m))))
    has_ecx = any(m[i] == 'mov' and o[i].endswith(',ecx') for i in range(min(8, len(m))))
    return has_esp and has_push and has_ecx
rows = []
for t in MISS:
    seq = decode(t)
    ln = sum(x[1] for x in seq)
    ok_break = bool(seq) and (seq[-1][2].startswith('ret') or seq[-1][2] == 'int3')
    rows.append(dict(va=hex(t), pro=ispro(seq), len=ln, brk=ok_break,
                     head='; '.join('%s %s' % (x[2], x[3]) for x in seq[:5]),
                     nslot=[hex(vt) for (vt, d), vv in SLOT.items() if vv == t],
                     prevbyte_is_retint3=(by(t - 1, 1)[0] in (0xC3, 0xC2, 0xCC)),
                     is_regstart=t in RL, is_dirt=t in DIRT))
    print('   E %s pro=%s len=%-4d brk=%s slots=%d | %s' % (rows[-1]['va'], rows[-1]['pro'], ln, ok_break,
          len(rows[-1]['nslot']), rows[-1]['head'][:76]))
ck('E1a 13 条中序言形态 13', sum(1 for r in rows if r['pro']) == 13, sum(1 for r in rows if r['pro']))
ck('E1b 13 条解码都以 ret/int3 结束', all(r['brk'] for r in rows), sum(1 for r in rows if r['brk']))
ck('E1c 13 条函数长度均 < 600 字节', all(r['len'] < 600 for r in rows), sorted(r['len'] for r in rows))
ck('E1d 13 条全不在区间起点集', not any(r['is_regstart'] for r in rows), sum(1 for r in rows if r['is_regstart']))
ck('E1e 13 条全不是直接调用目标', not any(r['is_dirt'] for r in rows), sum(1 for r in rows if r['is_dirt']))
# 反控：从每个命中地址 +1/+2/+3 偏移取址，序言率
ctrl = []
for t in MISS:
    for off in (1, 2, 3):
        ctrl.append(ispro(decode(t + off)))
rate = sum(1 for c in ctrl if c) / len(ctrl)
print('   E4 反控：13×{+1,+2,+3} 共 %d 个偏移地址，序言率 %.4f' % (len(ctrl), rate))
ck('E4a 反控序言率 < 20%', rate < 0.20, '%.4f' % rate)
# 反控2：整段线性扫描里序言形态占比（抽样 2000 个指令起点）
import random
random.seed(203)
samp = random.sample(ADDRS, 2000)
sr = sum(1 for a in samp if ispro(decode(a)))
print('   E4b 随机 2000 个指令起点的序言率 %.4f' % (sr / 2000))
ck('E4b 随机指令起点序言率 < 15%', sr / 2000 < 0.15, '%.4f' % (sr / 2000))
OUT = dict(miss=rows, ctrl_rate=rate, rand_rate=sr / 2000, asserts=N, fails=fails)
json.dump(OUT, open('/home/t628/projects/ra2-campaign-forge/_r203/m2_prologue.json', 'w'), ensure_ascii=False, indent=1)
print('\nSUMMARY asserts=%d fails=%d %s' % (N, len(fails), fails))
