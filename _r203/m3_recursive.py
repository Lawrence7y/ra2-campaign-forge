#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R203 m3：递归下降解码（recursive descent）——用「真入口种子」驱动，检验 13 条失步槽位目标。
种子 = 直接 call 目标（落 .text）∪ 槽位目标 ∪ E3 严格序言位。
G1 递归展开后的已访问指令起点数 vs 线性扫描；
G2 13 条失步目标是否被递归下降访问到；
G3 线性扫描独有的指令起点（=数据区伪指令）数量；
G4 反控：从任意非种子地址起递归，应几乎不产生长串。
防 OOM：按地址单点 detail 解码（每次只解 1 条，不批量），visited 用 set。
"""
import sys, struct, json, collections, bisect
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
import capstone
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
fails = []; N = 0
def ck(nm, c, d=''):
    global N; N += 1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ') + nm + ((' | ' + str(d)) if d != '' else ''))
T = P.B['.text']; LO = T['lo']; HI = T['hi_file']; RAW = P.RAW; RP = T['rawptr']
def by(va, n=16): return RAW[RP + va - LO: RP + va - LO + n]
def in_text(x): return x is not None and LO <= x < HI
def s32(v): return struct.unpack('<i', struct.pack('<I', v))[0]
def wv(sn):
    s = P.B[sn]; n = s['rawsize'] // 4
    return s['lo'], struct.unpack_from('<%dI' % n, P.RAW, s['rawptr']), n
# ---- 基线：COL/VT/SLOT ----
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
        if in_text(w[i]) and P.dw(base + 4 * i - 4) in COL: VT[base + 4 * i] = P.dw(base + 4 * i - 4)
SLOT = {}
for vt in VT:
    k = 0
    while k <= 400:
        t = P.dw(vt + 4 * k)
        if not in_text(t): break
        SLOT[(vt, 4 * k)] = t; k += 1
VTGT = set(SLOT.values())
# ---- 线性扫描 ----
BUF = RAW[RP:RP + (HI - LO)]
LIN = []; p = 0
while p < len(BUF):
    g = False
    for off, sz, mn, op in md.disasm_lite(BUF[p:p + 65536], LO + p):
        g = True; LIN.append((off, sz, mn, op)); p += sz
    if not g: p += 1
LIN.sort(); LASET = set(a for a, _, _, _ in LIN)
DIRT = set(int(op, 16) for a, s, mn, op in LIN if mn == 'call' and op.startswith('0x') and LO <= int(op, 16) < HI)
# E3 序言位（区间起点的严格序言）
REGB = []; st = LO
for a, sz, mn, op in LIN:
    if mn.startswith('ret') or mn == 'int3':
        REGB.append((st, a + sz)); st = a + sz
if st < HI: REGB.append((st, HI))
RL = set(r[0] for r in REGB)
I2R = {a: i for i, a in enumerate([x[0] for x in LIN])}
def pro(a):
    i = I2R.get(a)
    if i is None: return None
    w = LIN[i:i + 3]; m = [x[2] for x in w]; o = [x[3].replace(' ', '') for x in w]
    if len(w) < 2: return None
    if m[0] == 'push' and o[0] == 'ebp' and m[1] == 'mov' and o[1] == 'ebp,esp': return 'P1'
    if m[0] == 'mov' and o[0] == 'edi,edi' and m[1] == 'push' and o[1] == 'ebp': return 'P3'
    if m[1] == 'mov' and o[1] == 'ebp,esp' and m[0] == 'push': return 'P1'
    if m[0] == 'sub' and o[0].startswith('esp,'): return 'P4'
    return None
PROSET = set(a for a in RL if pro(a))
SEED = (DIRT | VTGT) | PROSET
print('   种子：直接调用目标 %d / 槽位目标 %d / 序言位 %d  => 并集 %d' % (len(DIRT), len(VTGT), len(PROSET), len(SEED)))
JCC = ('je', 'jne', 'jz', 'jnz', 'ja', 'jae', 'jb', 'jbe', 'jg', 'jge', 'jl', 'jle', 'js', 'jns',
       'jo', 'jno', 'jp', 'jnp', 'jcxz', 'jecxz', 'loop', 'loope', 'loopne')
STOP = ('ret', 'retf', 'int3', 'hlt', 'ud2')
visited = {}
work = [x for x in SEED if x in LASET or True]
queue = list(SEED)
stats = collections.Counter()
while queue:
    a = queue.pop()
    if not in_text(a) or a in visited: continue
    if not (LO <= a < HI): continue
    seq = list(md.disasm(by(a, 16), a, count=1))
    if not seq: stats['bad'] += 1; continue
    ins = seq[0]
    visited[a] = (ins.size, ins.mnemonic, ins.op_str.replace(' ', ''))
    stats['dec'] += 1
    mn = ins.mnemonic; op = ins.op_str.replace(' ', '')
    nxt = a + ins.size
    if mn in STOP:
        stats['stop'] += 1; continue
    if mn == 'jmp' and op.startswith('0x'):
        t = int(op, 16)
        if in_text(t): queue.append(t)
        continue
    if mn in JCC and op.startswith('0x'):
        t = int(op, 16)
        if in_text(t): queue.append(t)
        queue.append(nxt); continue
    if mn in ('call',):
        if op.startswith('0x'):
            t = int(op, 16)
            if in_text(t) and not t in visited: queue.append(t)   # 调用目标作为独立函数
        queue.append(nxt); continue
    queue.append(nxt)
VSET = set(visited)
print('   递归下降：解码 %d 条，访问指令起点 %d，停 %d，坏 %d' % (stats['dec'], len(VSET), stats['stop'], stats['bad']))
ck('G1a 递归下降访问起点 60000..140000', 60000 <= len(VSET) <= 140000, len(VSET))
ck('G1b 线性扫描起点 118491', len(LASET) == 118491, len(LASET))
both = VSET & LASET
onlyR = VSET - LASET
onlyL = LASET - VSET
print('   交集 %d / 仅递归 %d / 仅线性 %d' % (len(both), len(onlyR), len(onlyL)))
ck('G1c 递归访问的起点 100%% 也在线性扫描集内（失步点除外）',
   len(onlyR) <= 20, (len(onlyL), len(onlyR)))
# G2：13 条失步目标
MISS = sorted(t for t in VTGT if t not in LASET)
ck('G2a 失步槽位目标 13 条', len(MISS) == 13, len(MISS))
hit = [t for t in MISS if t in VSET]
ck('G2b 13 条全部被递归下降访问到', len(hit) == 13, '%d/13' % len(hit))
for t in MISS:
    v = visited.get(t)
    print('      %s -> %s' % (hex(t), ('%s %s (size %d)' % (v[1], v[2], v[0])) if v else 'NOT VISITED'))
# G3：线性扫描独有的起点（数据区伪指令）
ck('G3a 线性扫描独有起点 > 10000（数据区伪指令）', len(onlyL) > 10000, len(onlyL))
# G4 反控：从 13+1 起点递归，序列极短
def probe(start, maxn=400):
    seen = set(); q = [start]; n = 0
    while q and len(seen) < maxn:
        a = q.pop()
        if a in seen or not in_text(a): continue
        seq = list(md.disasm(by(a, 16), a, count=1))
        if not seq: continue
        i = seq[0]; seen.add(a); n += 1
        mn = i.mnemonic; op = i.op_str.replace(' ', ''); nx = a + i.size
        if mn in STOP: continue
        if mn == 'jmp' and op.startswith('0x'):
            t = int(op, 16)
            if in_text(t): q.append(t)
            continue
        if mn in JCC and op.startswith('0x'):
            t = int(op, 16)
            if in_text(t): q.append(t)
        q.append(nx)
    return len(seen)
ctrl = [probe(t + 1) for t in MISS]
print('   反控：从 13 条的 +1 偏移递归，访问条数 %s' % ctrl)
ck('G4a 反控：非入口偏移递归访问条数 < 60', max(ctrl) < 60, max(ctrl))
OUT = dict(seeds=dict(dirt=len(DIRT), vtgt=len(VTGT), pro=len(PROSET), union=len(SEED)),
           rec=dict(dec=stats['dec'], vis=len(VSET), both=len(both), onlyL=len(onlyL), onlyR=len(onlyR)),
           lin=len(LASET), miss=[hex(x) for x in MISS], hit=[hex(x) for x in hit], ctrl=ctrl,
           asserts=N, fails=fails)
json.dump(OUT, open('/home/t628/projects/ra2-campaign-forge/_r203/m3_recursive.json', 'w'), ensure_ascii=False, indent=1)
print('\nSUMMARY asserts=%d fails=%d %s' % (N, len(fails), fails))
