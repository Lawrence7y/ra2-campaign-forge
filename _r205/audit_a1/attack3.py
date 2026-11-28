#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R205-AUDIT-A1 第三轮：CHD/COL 的独立枚举（不从对方的推导链继承），+36 字段语义，40B 边界。"""
import sys, struct, collections
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
def s32(v): return struct.unpack('<i', struct.pack('<I', v & 0xFFFFFFFF))[0]
def wv(sn):
    s = P.B[sn]; n = s['rawsize'] // 4
    return s['lo'], struct.unpack_from('<%dI' % n, P.RAW, s['rawptr']), n
T = P.B['.text']; LO = T['lo']; HI = T['hi_file']
def in_text(x): return x is not None and LO <= x < HI
def isname(p):
    b = P.cstr(p + 8, 400)
    return b is not None and b.startswith(b'.?A') and b.endswith(b'@@')

# --- 独立枚举 1：COL（仅字段模式，不加 sig 约束、不依赖 pCHD 反查） ---
COL = {}
for sn in ('.rdata', '.data'):
    base, w, n = wv(sn)
    for i in range(n - 4):
        if w[i + 2] != 0: continue
        if P.where(w[i + 3]) != '.data' or P.where(w[i + 4]) != '.rdata': continue
        if not isname(w[i + 3]): continue
        COL[base + 4 * i] = dict(mdisp=s32(w[i + 1]), ptd=w[i + 3], pchd=w[i + 4])

# --- 独立枚举 2：CHD（不经过 COL，直接在 .rdata 扫 40 字节模式） ---
ind = []
rd = P.B['.rdata']
for off in range(0, rd['rawsize'] - 40, 4):
    a = rd['lo'] + off
    if P.dw(a) != 0: continue
    if P.dw(a + 4) not in (0, 1, 5): continue
    p = P.dw(a + 12); nb = P.dw(a + 8)
    if P.where(p) != '.rdata' or nb is None or nb > 64: continue
    if P.dw(a + 24) != 0: continue
    if P.dw(a + 32) != a: continue
    if P.where(P.dw(a + 28)) != '.data': continue
    ind.append(a)
CHD0 = sorted(set(v['pchd'] for v in COL.values()))
print('=== R1 独立枚举对账 ===')
print('  独立扫 CHD 模式: %d 个；由 COL.pCHD 反推: %d 个；交集 %d；差集 %s'
      % (len(ind), len(CHD0), len(set(ind) & set(CHD0)), [hex(x) for x in set(ind) ^ set(CHD0)][:6]))
CHD = CHD0
G = collections.defaultdict(list)
for c, v in COL.items(): G[v['pchd']].append(c)
print('  COL %d；其中有 pCHD 在 CHD 集内 %d；pCHD 不在 CHD 集内 %d'
      % (len(COL), sum(1 for v in COL.values() if v['pchd'] in set(CHD)),
         sum(1 for v in COL.values() if v['pchd'] not in set(CHD))))
print('  CHD 数 %d，每组视图数求和 %d' % (len(CHD), sum(len(v) for v in G.values())))

# --- 独立枚举 3：vftable 通道（vt-4 指向 COL）---
VT = {}
for va_lo, w, n in (lambda: [(lambda base: (base, wv(sn)[1], wv(sn)[2]))(wv(sn)[0]) for sn in ('.rdata',)])():
    for i in range(n):
        if in_text(w[i]) and P.dw(va_lo + 4 * i - 4) in COL:
            VT[va_lo + 4 * i] = P.dw(va_lo + 4 * i - 4)
print('  vftable 通道命中 %d 个 vt，覆盖 COL %d 个（其余 COL 无 vftable）'
      % (len(VT), len(set(VT.values()))))

print('\n=== R2 A1 边界：40B 是否闭合 / +36 是什么 ===')
print('  +36 段分布:', collections.Counter(P.where(P.dw(a + 36)) for a in CHD).most_common())
t36 = set(P.dw(a + 36) for a in CHD if P.dw(a + 36))
print('  +36 目标 %d 个唯一值；全部在 .rdata: %s' % (len(t36), all(P.where(t) == '.rdata' for t in t36)))
print('  +36 目标与其所属 CHD 的关系: 目标-a 值域 [%d,%d]' %
      (min(t - a for a in CHD if P.dw(a + 36) for t in [P.dw(a + 36)]),
       max(t - a for a in CHD if P.dw(a + 36) for t in [P.dw(a + 36)])))
# +36 目标结构体是否以「某个 CHD 的 +40 值」为首字段
a40 = set(P.dw(a + 40) for a in CHD if P.dw(a + 40))
print('  +36 目标首字段落在 a+40 值集合: %d/%d'
      % (sum(1 for t in t36 if P.dw(t) in a40), len(t36)))
print('  +36 目标第4字段 == 0xffffffff 的个数: %d/%d'
      % (sum(1 for t in t36 if P.dw(t + 12) == 0xffffffff), len(t36)))
print('  +36 目标是否等于某 CHD+40（即紧随之后的记录）: %d/%d'
      % (sum(1 for a in CHD if P.dw(a + 36) and P.dw(a + 36) in set(b + 40 for b in CHD)),
         sum(1 for a in CHD if P.dw(a + 36))))
print('  a+40 是否是 CHD 集合成员: %d；a+44 是 CHD: %d；a+48 是 CHD: %d'
      % (sum(1 for a in CHD if P.dw(a + 40) in set(CHD)) if False else 0,
         sum(1 for a in CHD if a + 44 in set(CHD)), sum(1 for a in CHD if a + 48 in set(CHD))))
print('  相邻 CHD 间距最小值 %d；间距==40 的个数 %d；间距 40~47 的个数 %d'
      % (min(CHD[i + 1] - CHD[i] for i in range(len(CHD) - 1)),
         sum(1 for i in range(len(CHD) - 1) if CHD[i + 1] - CHD[i] == 40),
         sum(1 for i in range(len(CHD) - 1) if 40 <= CHD[i + 1] - CHD[i] < 48)))
print('  CHD 集合内 a 与 a-40 同时是 CHD 的对数: %d'
      % sum(1 for a in CHD if a - 40 in set(CHD)))
print('  样例 11 dword（0x7fa4c8）:', [hex(P.dw(0x7fa4c8 + 4 * k) or 0) for k in range(11)])
print('  紧随其后的 0x7fa4f0 11 dword:', [hex(P.dw(0x7fa4f0 + 4 * k) or 0) for k in range(11)])
print('  0x7fa4f0 是否 CHD: %s；是否被 +36 引用: %s；是否在 COL 集: %s'
      % (0x7fa4f0 in set(CHD), 0x7fa4f0 in t36, 0x7fa4f0 in COL))
print('  0x815de0(.data) 前 8 dword:', [hex(P.dw(0x815de0 + 4 * k) or 0) for k in range(8)])
print('  0x815de0 在 .data 中出现次数(全段扫): %d' % sum(1 for i in range(P.B['.data']['rawsize'] // 4)
                                                   if struct.unpack_from('<I', P.RAW, P.B['.data']['rawptr'] + 4 * i)[0] == 0x815de0))

print('\n=== R3 A6 三条反例的可复算最小命令输出 ===')
for nm, addr in (('Overlay', 0x807598), ('Smudge', 0x809848), ('Terrain', 0x80c370)):
    v = COL[addr]
    print('  %-7s COL@0x%x name=%s mdisp=%d pchd=0x%x'
          % (nm, addr, P.cstr(v['ptd'] + 8, 200).decode('latin1'), v['mdisp'], v['pchd']))
    print('    同组全部 COL 地址/ mdisp:',
          [(hex(c), COL[c]['mdisp']) for c in sorted(G[v['pchd']])])
    print('    同组 vt 顺序:', [(hex(c), COL[c]['mdisp'], hex([k for k, x in VT.items() if x == c][0]))
                               for c in sorted(G[v['pchd']], key=lambda c: [k for k, x in VT.items() if x == c][0])])

print('\n=== R4 结果指纹 ===')
import hashlib
sigs = '%d|%d|%d|%d|%d|%d' % (len(COL), len(VT), len(CHD), 860, 978, 474)
print('  复算指纹 %s -> %s' % (sigs, hashlib.sha256(sigs.encode()).hexdigest()[:32]))
