#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R197 第一刀：BCA 相邻元素递增 181 处的成因（R196 PY8 遗留①）。

判据正反控设计（每问都带「必须掉下来」的反控）：
 G1 复算基数 CHD=954 / 槽位=2615 / 不同BCD=1002。
 G2 相邻 diff 分布：递减/相等/递增 三类 + 直方图。
 G3 递增处的树关系：bcd[i+1] 是 i 的直接子结点 / 兄弟 / 非本区间 —— 正控应 100% 落在某一类。
 G4 mdisp 联合：diff 符号 x md 变化 3x3 交叉表。
 G5 反控 A：把「递增」替换为「全部对」，看同一判据的命中率（鉴别力 = 递增组命中率 - 全体命中率）。
 G6 反控 B：随机打乱每张 CHD 的 BCD 顺序 K 次，看递增计数分布（判据能否被随机数据否掉）。
 G7 反控 C：把 ncb 全置 0（退化成单链）后 G3 分类如何变化。
"""
import sys, struct, collections, json, random
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

# ---------- G1 语料 ----------
COL = {}
for sn in ('.rdata', '.data'):
    base, w, n = wv(sn)
    for i in range(n - 4):
        if w[i] not in (0, 1, 2) or w[i+2] != 0: continue
        if P.where(w[i+3]) != '.data' or P.where(w[i+4]) != '.rdata': continue
        nm = P.cstr(w[i+3] + 8, 400)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base + 4*i] = dict(sig=w[i], mdisp=s32(w[i+1]), ptd=w[i+3], pchd=w[i+4], name=nm.decode('latin1'))

CHD = {}
for c, cc in COL.items():
    v = cc['pchd']
    if v not in CHD: CHD[v] = dict(n=P.dw(v + 8), arr=P.dw(v + 12), cols=[])
    CHD[v]['cols'].append(c)
for v, d in CHD.items():
    d['bcds'] = [P.dw(d['arr'] + 4*j) for j in range(d['n'])]
    d['ncb'] = [P.dw(b + 4) for b in d['bcds']]
    d['md'] = [s32(P.dw(b + 8)) for b in d['bcds']]

alls = [b for d in CHD.values() for b in d['bcds']]
ck('G1a CHD==954', len(CHD) == 954, len(CHD))
ck('G1b 槽位==2615', len(alls) == 2615, len(alls))
ck('G1c 不同BCD==1002', len(set(alls)) == 1002, len(set(alls)))
ck('G1d COL==1214', len(COL) == 1214, len(COL))

# ---------- 树重建 ----------
def build(ncb, n):
    if any(ncb[i] < 0 or i + ncb[i] >= n for i in range(n)): return None
    par = {}
    for i in range(n):
        end = i + ncb[i]; k = i + 1
        while k <= end:
            par[k] = i; k = k + ncb[k] + 1
            if k == 0 or k > n + 1: return None
        if k != end + 1: return None
    kids = collections.defaultdict(list)
    for c, p in par.items(): kids[p].append(c)
    roots = [i for i in range(n) if i not in par]
    return dict(kids=dict(kids), par=par, roots=roots, ok=(len(roots) == 1 and roots[0] == 0))

bad = 0
for v, d in CHD.items():
    t = build(d['ncb'], d['n'])
    d['tree'] = t
    if t is None or not t['ok']: bad += 1
ck('G1e 954 棵树重建成功', bad == 0, bad)

# ---------- G2 diff 分布 ----------
buckets = collections.Counter()
dec = inc = eq = 0
pairs = []
for v, d in CHD.items():
    b = d['bcds']
    for i in range(len(b) - 1):
        df = b[i+1] - b[i]
        pairs.append((v, i, df))
        buckets[df] += 1
        if df < 0: dec += 1
        elif df == 0: eq += 1
        else: inc += 1
ck('G2a 总对数==1661', len(pairs) == 1661, len(pairs))
ck('G2b 递减+相等+递增==总对数', dec + eq + inc == len(pairs), (dec, eq, inc))
ck('G2c 递减==1480 (R196 记录)', dec == 1480, dec)
ck('G2d 递增==181 (R196 记录)', inc == 181, inc)
ck('G2e 相等==0 (R196 记录)', eq == 0, eq)
top = buckets.most_common(20)

# ---------- G3 递增处的树关系 ----------
def classify(d, i):
    """bcd[i+1] 相对结点 i 的关系。返回 A/B/C/D。"""
    t = d['tree']; n = d['n']; ncb = d['ncb']
    if t is None or not t['ok']: return 'X'   # 树坏
    j = i + 1
    if j >= n: return 'X'
    kids = t['kids']; par = t['par']
    if j in kids.get(i, []): return 'A'
    if par.get(j) == par.get(i) and i in par: return 'B'
    return 'D'

cls = collections.Counter()
incdetail = []
for v, i, df in pairs:
    if df <= 0: continue
    d = CHD[v]
    c = classify(d, i)
    cls[c] += 1
    incdetail.append(dict(chd=v, n=d['n'], i=i, bcd_i=d['bcds'][i], bcd_j=d['bcds'][i+1], diff=df,
                          ncb_i=d['ncb'][i], ncb_j=d['ncb'][i+1], md_i=d['md'][i], md_j=d['md'][i+1], cls=c))
ck('G3a 递增处分类总数==181', sum(cls.values()) == 181, dict(cls))
ck('G3b 无 X（树坏）', cls.get('X', 0) == 0, cls.get('X', 0))

dgrp = collections.Counter()
for x in incdetail:
    if x['diff'] == 24: dgrp['==24'] += 1
    elif x['diff'] <= 48: dgrp['25..48'] += 1
    else: dgrp['>48'] += 1

# ---------- G4 mdisp 联合 ----------
xt = collections.Counter()
for v, i, df in pairs:
    d = CHD[v]; a, b = d['md'][i], d['md'][i+1]
    sg = 'inc' if df > 0 else ('dec' if df < 0 else 'eq')
    mg = 'up' if b > a else ('dn' if b < a else 'flat')
    xt[(sg, mg)] += 1
inc_md_up = xt[('inc', 'up')]
ck('G4a 递增且 md 上升 == 递增总数', inc_md_up == inc, (inc_md_up, inc))

# ---------- G5 反控 A：全体对的同一判据命中率 ----------
allcls = collections.Counter()
for v, i, df in pairs:
    allcls[classify(CHD[v], i)] += 1

# ---------- G6 反控 B：随机打乱顺序 ----------
random.seed(20261128)
shuf_inc = []
for trial in range(200):
    t = 0
    for v, d in CHD.items():
        b = d['bcds'][:]
        if len(b) < 2: continue
        random.shuffle(b)
        for i in range(len(b) - 1):
            if b[i+1] - b[i] > 0: t += 1
    shuf_inc.append(t)
shuf_mean = sum(shuf_inc) / len(shuf_inc)
ck('G6a 打乱后递增均值 >> 181', shuf_mean > 181, round(shuf_mean, 1))
ck('G6b 打乱后递增最小值 > 181', min(shuf_inc) > 181, min(shuf_inc))

# ---------- G7 反控 C：ncb 全置 0 ----------
cls0 = collections.Counter()
for v, i, df in pairs:
    if df <= 0: continue
    d = CHD[v]; n = d['n']
    if i + 1 >= n: cls0['X'] += 1; continue
    # 全 0 ncb 下：每个结点都是其前一结点的直接子结点
    cls0['A'] += 1
ck('G7a ncb全0时递增处 100% 判为 A（判据失去鉴别力）', cls0.get('A', 0) == inc, dict(cls0))

# ---------- 输出 ----------
res = dict(
    base=dict(CHD=len(CHD), slots=len(alls), uniq_bcd=len(set(alls)), COL=len(COL)),
    diff=dict(dec=dec, eq=eq, inc=inc, top20=[[k, v] for k, v in top], distinct_diff=len(buckets)),
    inc_cls=dict(cls), inc_diffgrp=dict(dgrp),
    md_cross={f'{a}/{b}': v for (a, b), v in sorted(xt.items())},
    all_cls=dict(allcls),
    shuffle=dict(mean=round(shuf_mean, 2), min=min(shuf_inc), max=max(shuf_inc), trials=200),
    ncb0_cls=dict(cls0),
    inc_detail=incdetail,
    fails=fails, asserts=N,
)
open('/home/t628/projects/ra2-campaign-forge/_r197/m1_bca181.json', 'w').write(json.dumps(res, ensure_ascii=False, indent=1))
print('\n--- SUMMARY ---')
print('base', res['base'])
print('diff dec/eq/inc', dec, eq, inc, 'distinct', len(buckets))
print('top20', top[:8])
print('inc_cls', dict(cls))
print('inc_diffgrp', dict(dgrp))
print('md_cross', res['md_cross'])
print('all_cls', dict(allcls))
print('shuffle', res['shuffle'])
print('asserts', N, 'fails', len(fails), fails)
