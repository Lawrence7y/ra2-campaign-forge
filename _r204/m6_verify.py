#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R204 m6（权威复算）：复算执行员 hy4 的 7 项 + 审计卡 10 条中的机制性断言，全部由主会话亲跑。
重点复算两条「与卡面预期不符」：
 A5 BCD 非 24 网格（模 24 = {0,8,16}）；
 A6 BCA 严格降序段 490/954（不是绝大多数）；
 A10 执行员提出的 b-16 直方图 == mdisp 直方图（这是它给出的「24 步长」替代证据，必须亲验）。
"""
import sys, struct, collections, json
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
import hashlib
fails = []; N = 0
def ck(nm, c, d=''):
    global N; N += 1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ') + nm + ((' | ' + str(d)) if d != '' else ''))
def s32(v): return struct.unpack('<i', struct.pack('<I', v))[0]
def wv(sn):
    s = P.B[sn]; n = s['rawsize'] // 4
    return s['lo'], struct.unpack_from('<%dI' % n, P.RAW, s['rawptr']), n
T = P.B['.text']; LO = T['lo']; HI = T['hi_file']
def in_text(x): return x is not None and LO <= x < HI
print('   bin sha256 %s' % hashlib.sha256(P.RAW).hexdigest())
COL = {}
for sn in ('.rdata', '.data'):
    base, w, n = wv(sn)
    for i in range(n - 4):
        if w[i] not in (0, 1, 2) or w[i + 2] != 0: continue
        if P.where(w[i + 3]) != '.data' or P.where(w[i + 4]) != '.rdata': continue
        nm = P.cstr(w[i + 3] + 8, 400)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base + 4 * i] = dict(mdisp=s32(w[i+1]), ncb=P.dw(base+4*i+4) if False else None, ptd=w[i+3], pchd=w[i+4], name=nm.decode('latin1'))
VTI = {}
for sn in ('.rdata', '.data'):
    base, w, n = wv(sn)
    for i in range(n):
        if in_text(w[i]) and P.dw(base + 4 * i - 4) in COL: VTI[base + 4 * i] = P.dw(base + 4 * i - 4)
G = collections.defaultdict(list)
for c, v in COL.items(): G[v['pchd']].append(c)
CHD = sorted(G)
BCD = {a: [P.dw(P.dw(a + 12) + 4 * j) for j in range(P.dw(a + 8))] for a in CHD}
uniq = sorted(set(b for v in BCD.values() for b in v))

# --- 复算 A1/A2 ---
ck('X1a COL 1214 / 类名 954', (len(COL), len(set(v['name'] for v in COL.values()))) == (1214, 954),
   (len(COL), len(set(v['name'] for v in COL.values()))))
gd = collections.Counter(len(v) for v in G.values())
ck('X1b pCHD 分组 954，分布 1:860/2:10/3:6/4:76/5:1/7:1',
   dict(gd) == {1: 860, 2: 10, 3: 6, 4: 76, 5: 1, 7: 1}, dict(gd))
# partition 等价（双向细化）
NB = {}
for a, cols in G.items():
    nm = set(COL[c]['name'] for c in cols)
    NB[a] = nm
ck('X1c 每 pCHD 组内类名唯一（组 == 类）', all(len(v) == 1 for v in NB.values()),
   sum(1 for v in NB.values() if len(v) > 1))

# --- 复算 A3 ---
f4 = collections.Counter(P.dw(a + 4) for a in CHD)
ck('X2a CHD+4 分布 == {0:855, 1:66, 5:33}', dict(f4) == {0: 855, 1: 66, 5: 33}, dict(f4))
ck('X2b CHD+0 恒 0', all(P.dw(a) == 0 for a in CHD), None)
ck('X2c CHD+8 max 18 且全部 <= 200', max(P.dw(a+8) for a in CHD) == 18, max(P.dw(a+8) for a in CHD))

# --- 复算 A4/A5 网格 ---
ck('X3a 1002 个 BCD 全部 8 字节对齐', all(u % 8 == 0 for u in uniq), sum(1 for u in uniq if u % 8))
m24 = collections.Counter(u % 24 for u in uniq)
print('   X3 BCD 地址 mod 24 = %s' % dict(m24))
ck('X3b BCD 非 24 统一网格（mod 24 有 3 种）', len(m24) == 3, dict(m24))

# --- 复算 A10（执行员的替代证据）---
def hist(vals): 
    c = collections.Counter(vals)
    return sorted(c.items())
mdisp_hist = hist(s32(P.dw(b + 8)) for b in uniq)
b16_hist = hist(s32(P.dw(b - 16)) for b in uniq)
b8_hist = hist(s32(P.dw(b - 8)) for b in uniq)
print('   X4 mdisp(+8) 直方图 top6 %s' % mdisp_hist[:3])
print('   X4 b-16 直方图 top6 %s' % b16_hist[:3])
print('   X4 b-8 直方图 top6 %s' % b8_hist[:3])
ck('X4a 执行员断言 b-16 直方图 == mdisp 直方图', b16_hist == mdisp_hist, (len(b16_hist), len(mdisp_hist)))
ck('X4b b-8 直方图 != mdisp（反控：不是任意偏移都成立）', b8_hist != mdisp_hist, (len(b8_hist), len(mdisp_hist)))

# --- 复算 A6 严格降序 ---
contig = 0; non = []
for a in CHD:
    v = BCD[a]; n = len(v); base = P.dw(a + 12)
    if v == [base - 24 * j for j in range(n)]: contig += 1
    else: non.append(a)
ck('X5a 严格 {p-24j} 判据成立数 == 执行员的 490', contig == 490, (contig, len(CHD)))
# 正确判据：组内相邻差分全 == -24（不看绝对基址）
local = sum(1 for a in CHD if all(BCD[a][i+1] - BCD[a][i] == -24 for i in range(len(BCD[a]) - 1)))
print('   X5 组内全等差 -24 的 CHD %d / %d' % (local, len(CHD)))
ck('X5b 组内等差成立数 > 严格基址判据（基址判据本身错）', local > contig, (local, contig))
# 纯 -24 的 CHD（全等差的）与 MI 类的关系
pure = [a for a in CHD if all(BCD[a][i+1] - BCD[a][i] == -24 for i in range(len(BCD[a]) - 1))]
pure_mi = sum(1 for a in pure if any(s32(P.dw(b+8)) != 0 for b in BCD[a]))
print('   X5 全等差 CHD %d 中 MI 类 %d' % (len(pure), pure_mi))
ck('X5c 全等差 CHD 里 MI 类占比低（大跳集中在 MI）', pure_mi < 0.1 * len(pure) if pure else False, (pure_mi, len(pure)))

# --- 复算 A7 最强判据 ---
def ptd_set(a): return set(P.dw(b) for b in BCD[a])
ok = sum(1 for a in CHD if set(COL[c]['ptd'] for c in G[a]) <= ptd_set(a))
ck('X6a 自有 pTD ⊆ BCA pTD 集合 954/954', ok == 954, ok)
import random
random.seed(2046)
fake_ok = 0
for a in CHD:
    c2 = [x for x in CHD if len(BCD[x]) == len(BCD[a]) and x != a]
    if c2 and set(COL[c]['ptd'] for c in G[a]) <= ptd_set(random.choice(c2)): fake_ok += 1
ck('X6b 反控：换用同长度 BCA 成立 0/954', fake_ok == 0, fake_ok)

# --- 复算 A8 共享 ---
refc = collections.Counter(b for v in BCD.values() for b in v)
sh = sum(1 for v in refc.values() if v >= 2)
ck('X7a 共享 BCD 304 个 / 最多 98 次', (sh, max(refc.values())) == (304, 98), (sh, max(refc.values())))

# --- 复算 A9 五条 ATL ---
mi_bca = [a for a in CHD if any(s32(P.dw(b + 8)) != 0 for b in BCD[a])]
mi_view = [a for a in CHD if len(G[a]) >= 2]
only_bca = sorted(set(mi_bca) - set(mi_view))
ck('X8a 仅 BCA 侧 5 个', len(only_bca) == 5, [hex(x) for x in only_bca])
ck('X8b 五个地址与执行员一致',
   [hex(x) for x in only_bca] == ['0x80e680', '0x80e740', '0x80e780', '0x80e7c0', '0x80e998'],
   [hex(x) for x in only_bca])
ck('X8c 五个都是 ATL 模板/事件 sink 类',
   all(('ATL@@' in COL[G[a][0]]['name']) or ('EventSink' in COL[G[a][0]]['name']) for a in only_bca),
   [COL[G[a][0]]['name'][:46] for a in only_bca])

# --- 交付：964 语义补充，CHD+4 的 66/33 是什么 ---
c1 = [a for a in CHD if P.dw(a + 4) == 1]
c5 = [a for a in CHD if P.dw(a + 4) == 5]
print('   X9 CHD+4==1 的 66 个样例类名 %s' % [COL[G[a][0]]['name'][:32] for a in c1[:6]])
print('   X9 CHD+4==5 的 33 个样例类名 %s' % [COL[G[a][0]]['name'][:32] for a in c5[:6]])
# 与 attributes(=2/9) 的 BCD 是否相关
attr2 = set(b for b in uniq if P.dw(b + 20) == 2)
attr9 = set(b for b in uniq if P.dw(b + 20) == 9)
chd_with_attr2 = [a for a in CHD if ptd_set(a) & set(P.dw(b) for b in attr2)]
chd_with_attr9 = [a for a in CHD if ptd_set(a) & set(P.dw(b) for b in attr9)]
print('   X9 含 attributes==2 的 BCD 的 CHD %d；含 attributes==9 的 %d' % (len(chd_with_attr2), len(chd_with_attr9)))
attr2_names = sorted(set(COL[G[a][0]]['name'] for a in chd_with_attr2))[:8]
print('   X9 attributes==2 所在类的样例 %s' % attr2_names)
ck('X9a CHD+4 与 attributes 有相关性（同时存在非默认值）',
   len(chd_with_attr2) > 0 and len(c1) > 0, (len(chd_with_attr2), len(c1), len(c5)))

json.dump(dict(N=N, fails=fails, contig=contig, local=local, pure=len(pure), pure_mi=pure_mi,
               b16_eq=(b16_hist == mdisp_hist), m24=dict(m24), f4=dict(f4),
               only_bca=[hex(x) for x in only_bca], chd_attr2=len(chd_with_attr2), chd_attr9=len(chd_with_attr9),
               sh=sh, maxref=max(refc.values())),
          open('/home/t628/projects/ra2-campaign-forge/_r204/m6_verify.json','w'), ensure_ascii=False, indent=1)
print('\n== %d assertions, %d FAIL ==' % (N, len(fails)))
print('FAILS:', fails)
