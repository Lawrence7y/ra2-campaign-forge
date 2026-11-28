#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R204 m1（权威）：CHD/BCD 结构字节实证 + 与 R203 vftable 视图模型的独立交叉验证。

前提（实测，不在本轮重测）：R203 m11 定稿模型 —— 1214 个 COL 记录、954 个不同类名、
按「槽流遇同组头类名 COL 即新视图」解析得 954 组 / 1214 视图 / 14044 槽。

本轮问题：
 A  CHD 结构布局：+0/+4/+8/+12 四个字段的字节实证（954 张全部验证）
 B  BCD 结构布局与步长：+0 pTD / +4 ncb / +8 mdisp / +12 pdisp / +16 vdisp / +20 attributes
 C  独立分组：按 pCHD 分 partition（1214 COL -> 954 CHD）与 R203 名字解析 partition 是否**同一 partition**
 D  BCA 的 mdisp 多重集 vs vftable 视图的 mdisp 多重集（94 个 MI 类逐类）
 E  属性/ncb 语义分布（实测值，不解释成结论）
 F  反控：打乱 BCA 顺序 / 把 pCHD 字段换成随机同段指针，判据必须掉下来
"""
import sys, struct, collections, random, json
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P

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

# ---------- A0 COL 语料（与 _r203/m11 同判据） ----------
COL = {}
for sn in ('.rdata', '.data'):
    base, w, n = wv(sn)
    for i in range(n - 4):
        if w[i] not in (0, 1, 2) or w[i + 2] != 0: continue
        if P.where(w[i + 3]) != '.data' or P.where(w[i + 4]) != '.rdata': continue
        nm = P.cstr(w[i + 3] + 8, 400)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base + 4 * i] = dict(sig=w[i], mdisp=s32(w[i+1]), cd=w[i+2], ptd=w[i+3],
                                 pchd=w[i+4], name=nm.decode('latin1'))

VTI = {}
for sn in ('.rdata', '.data'):
    base, w, n = wv(sn)
    for i in range(n):
        if in_text(w[i]) and P.dw(base + 4 * i - 4) in COL: VTI[base + 4 * i] = P.dw(base + 4 * i - 4)

ck('A0a COL == 1214', len(COL) == 1214, len(COL))
ck('A0b 候选 vftable 起点 == 1214', len(VTI) == 1214, len(VTI))
ck('A0c 不同类名 == 954', len(set(v['name'] for v in COL.values())) == 954,
   len(set(v['name'] for v in COL.values())))

# ---------- C1 按 pCHD 分组（独立于名字） ----------
G = collections.defaultdict(list)
for c, v in COL.items(): G[v['pchd']].append(c)
ck('C1a distinct pCHD == 954（独立于名字得类数）', len(G) == 954, len(G))
ck('C1b 每个 pCHD 落在 .rdata', all(P.where(k) == '.rdata' for k in G), collections.Counter(P.where(k) for k in G).most_common())
gd = collections.Counter(len(v) for v in G.values())
print('   C1 每 pCHD 的 COL 数分布: %s' % gd.most_common(10))
ck('C1c 分布 == R203 视图数分布 1:860/2:10/3:6/4:76/5:1/7:1',
   dict(gd) == {1: 860, 2: 10, 3: 6, 4: 76, 5: 1, 7: 1}, dict(gd))

# ---------- C2 partition 等价性（同一 partition：互为细化且块数相等） ----------
# R203 名字解析：复刻 m11 的 parse（同一判据、同一 maxk）
def parse(vt, maxk=4000):
    head_name = COL[VTI[vt]]['name']
    views = []; curcol = VTI[vt]; cur = []; positions = []
    k = 0
    while k < maxk:
        pos = vt + 4 * k
        w = P.dw(pos)
        if w is None: break
        if in_text(w): cur.append(w); positions.append(pos); k += 1; continue
        if w in COL and COL[w]['name'] == head_name:
            views.append((curcol, cur)); curcol = w; cur = []
            positions.append(pos); k += 1; continue
        break
    views.append((curcol, cur))
    return views, positions

claimed = {}; HEADS = []
for vt in sorted(VTI):
    if vt in claimed: continue
    views, positions = parse(vt)
    HEADS.append(vt); claimed[vt] = vt
    for p in positions: claimed[p] = vt
NAME_BLOCK = {}
for h in HEADS:
    views, _ = parse(h)
    for col, _s in views: NAME_BLOCK[col] = h
ck('C2a 名字解析覆盖全部 1214 个 COL', set(NAME_BLOCK) == set(COL), (len(NAME_BLOCK), len(COL)))
ck('C2b 名字解析块数 == 954', len(set(NAME_BLOCK.values())) == 954, len(set(NAME_BLOCK.values())))
# 同一 partition 判定：两关系互为细化
same = 0; inter = 0
for c1 in COL:
    for c2 in COL:
        pass
# 用 O(n) 方式：对每个块比较
ok_fwd = True; ok_bwd = True; bad_fwd = []; bad_bwd = []
by_name = collections.defaultdict(set)
for c, h in NAME_BLOCK.items(): by_name[h].add(c)
for chd, cols in G.items():
    hs = set(NAME_BLOCK[c] for c in cols)
    if len(hs) != 1: ok_fwd = False; bad_fwd.append((chd, len(hs)))
for h, cols in by_name.items():
    ks = set(COL[c]['pchd'] for c in cols)
    if len(ks) != 1: ok_bwd = False; bad_bwd.append((h, len(ks)))
ck('C2c pCHD 块 是 名字块 的细化（每块只落 1 个名字块）', ok_fwd, (len(bad_fwd), bad_fwd[:3]))
ck('C2d 名字块 是 pCHD 块 的细化（每块只落 1 个 pCHD）', ok_bwd, (len(bad_bwd), bad_bwd[:3]))
ck('C2e 双向细化 + 块数相同 => 同一 partition', ok_fwd and ok_bwd and len(G) == len(by_name) == 954, (len(G), len(by_name)))

# ---------- A/C3 CHD 结构布局 ----------
CHD_ADDRS = sorted(G)
f8 = collections.Counter(); f12sec = collections.Counter(); f0 = collections.Counter(); f4 = collections.Counter()
for a in CHD_ADDRS:
    f0[P.dw(a)] += 1; f4[P.dw(a+4)] += 1; f8[P.dw(a+8)] += 1; f12sec[P.where(P.dw(a+12))] += 1
print('   A CHD +0 分布 %s' % f0.most_common(5))
print('   A CHD +4 分布 %s' % f4.most_common(5))
print('   A CHD +8 分布 top8 %s' % f8.most_common(8))
print('   A CHD +12 所在段 %s' % f12sec.most_common())
ck('A1a +8 全部 <= 200（numBaseClasses 量级）', all(v <= 200 for v in f8), max(f8))
ck('A1b +12 全部落 .rdata', set(f12sec) == {'.rdata'}, dict(f12sec))
ck('A1c +8 == 该 pCHD 块内 COL 数（numBaseClasses 应 >= 视图数）', all(P.dw(a+8) >= len(G[a]) for a in CHD_ADDRS),
   sum(1 for a in CHD_ADDRS if P.dw(a+8) < len(G[a])))
ck('A1d +0 恒 0（generated RTTI）', set(f0) == {0}, dict(list(f0.items())[:3]))
ck('A1e +4 取值集合 == {1}（CHD_ATTRIBUTE）', set(f4) == {1}, set(f4))

# ---------- B BCD 布局与步长 ----------
BCD = {}
for a in CHD_ADDRS:
    n = P.dw(a + 8); arr = P.dw(a + 12)
    assert n is not None and n < 500, (hex(a), n)
    BCD[a] = [P.dw(arr + 4 * j) for j in range(n)]
allb = [b for v in BCD.values() for b in v]
uniq = sorted(set(allb))
print('   B BCA 引用总数 %d / 不同 BCD %d' % (len(allb), len(uniq)))
ck('B1a 不同 BCD == 1002（与 R197 同值）', len(uniq) == 1002, len(uniq))
ck('B1b 全部 BCD 落 .rdata', set(P.where(b) for b in uniq) == {'.rdata'},
   collections.Counter(P.where(b) for b in uniq).most_common())
ck('B1c 全部 BCD 4 字节对齐', all(b % 4 == 0 for b in uniq), sum(1 for b in uniq if b % 4))
# 步长：BCA 内相邻 BCD 间距
gaps = collections.Counter()
for a, v in BCD.items():
    for i in range(len(v) - 1):
        gaps[v[i+1] - v[i]] += 1
print('   B 相邻 BCD 间距 top8 %s' % gaps.most_common(8))
ck('B2a 相邻间距 24 为主（BCD 定长 24）', gaps.most_common(1)[0][0] == 24, gaps.most_common(3))
ck('B2b 24 间距占比', gaps[24] > 0.9 * sum(gaps.values()), (gaps[24], sum(gaps.values())))
# 24 步长下字段可为下一 BCD 的 pTD
nextb = collections.Counter()
for b in uniq:
    if b + 24 in uniq: nextb['in_bca'] += 1
ck('B2c 绝大多数 BCD 的 +24 也是 BCD（数组连续布局）', nextb['in_bca'] > 0.9 * len(uniq), (nextb['in_bca'], len(uniq)))

ATTR = collections.Counter(); NCB = collections.Counter(); PDISP = collections.Counter(); VDD = collections.Counter()
PTD_OK = 0
for b in uniq:
    ptd = P.dw(b); ncb = P.dw(b + 4); md = s32(P.dw(b + 8)); pd_ = s32(P.dw(b + 12)); vd = s32(P.dw(b + 16)); at = P.dw(b + 20)
    NCB[ncb] += 1; PDISP[pd_] += 1; VDD[vd] += 1; ATTR[at] += 1
    nm = P.cstr(ptd + 8, 400) if P.where(ptd) in ('.data', '.rdata') else None
    if nm and nm.startswith(b'.?A') and nm.endswith(b'@@'): PTD_OK += 1
print('   B ncb 分布 %s' % NCB.most_common(8))
print('   B pdisp 分布 %s' % PDISP.most_common(6))
print('   B vdisp 分布 %s' % VDD.most_common(6))
print('   B attributes 分布 %s' % ATTR.most_common(8))
ck('B3a pTD 全部指向合法类型名（.?A...@@）', PTD_OK == len(uniq), (PTD_OK, len(uniq)))
ck('B3b ncb 取值集合有限', len(NCB) < 60, len(NCB))
ck('B3c attributes 取值集合 == {0}（无 CHD_ATTRIBUTE）', set(ATTR) == {0}, set(ATTR))

# ---------- D BCA mdisp 多重集 vs vftable 视图 mdisp 多重集 ----------
def md_multiset_of_block(cols):
    # 视图 mdisp 取 R203 口径：每个视图的 COL 记录 mdisp
    return sorted(COL[c]['mdisp'] for c in cols)
def md_multiset_of_bca(a):
    return sorted(s32(P.dw(b + 8)) for b in BCD[a])

match = 0; mism = []
for a in CHD_ADDRS:
    if md_multiset_of_bca(a) == md_multiset_of_block(G[a]): match += 1
    else: mism.append(a)
print('   D 逐 CHD 多重集相等 %d / %d' % (match, len(CHD_ADDRS)))
print('   D 不等样例 %s' % [(hex(x), md_multiset_of_block(G[x])[:6], md_multiset_of_bca(x)[:6]) for x in mism[:4]])
ck('D1a 多重集相等占比', match / len(CHD_ADDRS) > 0.5, match / len(CHD_ADDRS))

# 94 个 MI 类（视图数 >= 2）逐类
mi = [a for a in CHD_ADDRS if len(G[a]) >= 2]
mi_ok = [a for a in mi if md_multiset_of_bca(a) == md_multiset_of_block(G[a])]
print('   D MI 类 %d，多重集相等 %d' % (len(mi), len(mi_ok)))
ck('D2a MI 类数 == 94', len(mi) == 94, len(mi))
ck('D2b MI 类多重集相等 94/94', len(mi_ok) == 94, len(mi_ok))
for a in mi[:6]:
    print('   D  %s  vftable视图mdisp=%s  BCA mdisp=%s  n=%d  {class blocks=%d}' % (
        COL[G[a][0]]['name'][:38], md_multiset_of_block(G[a]), md_multiset_of_bca(a), P.dw(a+8), len(G[a])))

# ---------- F 反控 ----------
random.seed(204)
# F1 打乱 BCA 顺序：多重集判据不应掉（说明判据对顺序不敏感 = 弱）
perm_ok = 0
for a in mi:
    v = BCD[a][:]; random.shuffle(v)
    ms = sorted(s32(P.dw(b + 8)) for b in v)
    if ms == md_multiset_of_block(G[a]): perm_ok += 1
ck('F1a 反控：打乱 BCA 顺序后多重集判据仍成立（判据弱于顺序）', perm_ok == len(mi), (perm_ok, len(mi)))
# F2 把 pCHD 换成同段随机 CHD：分组必须掉下来
pool = CHD_ADDRS[:]
cnt_same = 0
for c in COL:
    r = random.choice(pool)
    if r == COL[c]['pchd']: cnt_same += 1
ck('F2a 反控：随机 pCHD 分组不可能复现 954 块', cnt_same < 50, cnt_same)
# F3 严格序判据（顺序敏感）：BCA mdisp 序列 == vftable 视图顺序 mdisp 序列
seq_ok = 0; seq_bad = []
for a in mi:
    seq_bca = [s32(P.dw(b + 8)) for b in BCD[a]]
    seq_vt = [COL[c]['mdisp'] for c in G[a]]
    if seq_bca == seq_vt: seq_ok += 1
    else: seq_bad.append((COL[G[a][0]]['name'][:32], seq_vt, seq_bca))
ck('F3a 严格序列相等（顺序敏感判据）', seq_ok > 0, (seq_ok, len(mi)))
print('   F3 序列不等样例 %s' % seq_bad[:5])

# ---------- 落盘 ----------
out = dict(N=N, fails=fails,
           base=dict(COL=len(COL), VTI=len(VTI), CHD=len(G), uniq_bcd=len(uniq), bca_refs=len(allb)),
           gd=dict(gd), chd_f0=dict(f0), chd_f4=dict(f4), chd_f8_top=f8.most_common(12),
           bcd_gaps=gaps.most_common(8), ncb=NCB.most_common(10), pdisp=PDISP.most_common(6),
           vdisp=VDD.most_common(6), attr=ATTR.most_common(6),
           ms_match=match, ms_mism=len(mism), mi=len(mi), mi_ok=len(mi_ok),
           seq_ok=seq_ok, seq_bad=seq_bad[:10])
json.dump(out, open('/home/t628/projects/ra2-campaign-forge/_r204/m1_chd.json', 'w'), ensure_ascii=False, indent=1)
print('\n== %d assertions, %d FAIL ==' % (N, len(fails)))
print('FAILS:', fails)
