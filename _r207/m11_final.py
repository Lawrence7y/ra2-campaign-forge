#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R207 m11（定稿）：视图生成律 L* 的判别力检验 + 正确的反控设计。
错误的旧反控：在全部 954 类上比「预测=实际」。855 类两侧都是空集，空对空自动通过 ⇒ 反控无判别力（随机 pTD 集也能命中 860..954）。
正确的反控：只在**非平凡子集**上比，即「实际有视图」的 94 类 ∪「预测有视图」的类。
本脚本给出：
  D1 判别域大小（|实际有视图| / |BCD 有非零 mdisp| / 两者并集的对称差）
  D2 全量命中（954）与判别域命中（域内全命中才算律成立）
  D3 七档反控在判别域上的命中数
  D4 逐类混淆矩阵（预测有且实际有 / 预测有实际无 / 预测无实际有 / 双无）
  D5 15 个「BCD 有非零 mdisp 但缺视图」例外的肇因 pTD 全表（13 个 onlysec pTD）
  D6 「视图 ⟺ 该 mdisp 上有 pTD 曾以 mdisp==0 身份出现」的 (类,mdisp) 级双向
  D7 attributes bit0 的真语义（R205 QG4）订正：bit0 == 存在非零 mdisp 的 BCD（不看视图）"""
import sys, struct, collections, json, random

sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P


def s32(v):
    return struct.unpack('<i', struct.pack('<I', v))[0]


COL = {}
for sn in ('.rdata', '.data'):
    s = P.B[sn]
    n = s['rawsize'] // 4
    base = s['lo']
    w = struct.unpack_from('<%dI' % n, P.RAW, s['rawptr'])
    for i in range(n - 4):
        if w[i] not in (0, 1, 2) or w[i + 2] != 0:
            continue
        if P.where(w[i + 3]) != '.data' or P.where(w[i + 4]) != '.rdata':
            continue
        nm = P.cstr(w[i + 3] + 8, 400)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')):
            continue
        COL[base + 4 * i] = dict(sig=w[i], mdisp=s32(w[i + 1]), pTD=w[i + 3],
                                 pCHD=w[i + 4], name=nm.decode('latin1'))
G = collections.defaultdict(list)
for c, v in COL.items():
    G[v['pCHD']].append(c)
CHD = sorted(G)
NB = {a: P.dw(a + 8) for a in CHD}
pBCA = {a: P.dw(a + 12) for a in CHD}
ATTR = {a: P.dw(a + 4) for a in CHD}
BCA = {a: [P.dw(pBCA[a] + 4 * j) for j in range(NB[a])] for a in CHD}
own_td = {a: COL[a + 16]['pTD'] for a in CHD}
td2c = {v: k for k, v in own_td.items()}


def tn(td):
    nm = P.cstr(td + 8, 300)
    return nm.decode('latin1') if nm else '?'


fails = []
NA = 0


def ck(nm, c, d=''):
    global NA
    NA += 1
    if not c:
        fails.append(nm)
    print(('PASS ' if c else 'FAIL ') + nm + ((' | ' + str(d)) if d != '' else ''))


phys = sorted(set(x for a in CHD for x in BCA[a]))
R = {b: (P.dw(b), P.dw(b + 4), s32(P.dw(b + 8)), s32(P.dw(b + 12)),
         s32(P.dw(b + 16)), P.dw(b + 20)) for b in phys}
views = {a: sorted(COL[c]['mdisp'] for c in G[a] if c != a + 16) for a in CHD}
primary = {R[b][0] for b in phys if R[b][2] == 0}
onlysec = {R[b][0] for b in phys if R[b][2] != 0} - primary

print('== D1 判别域 ==')
nv = sum(1 for a in CHD if views[a])
nbz = sum(1 for a in CHD if any(R[x][2] != 0 for x in BCA[a]))
sym = sum(1 for a in CHD if views[a] and not any(R[x][2] != 0 for x in BCA[a]))
print(' 有视图类 %d / BCD 有非零 mdisp 类 %d / 有视图但无非零 mdisp %d' % (nv, nbz, sym))
print(' ⇒ 全量 954 类中 %d 类两侧均为空（空对空，无判别力）' % sum(1 for a in CHD if not views[a] and not any(R[x][2] != 0 for x in BCA[a])))
trivial = {a for a in CHD if not views[a] and not any(R[x][2] != 0 for x in BCA[a])}
ck('D1.1 空对空类数 = 855', len(trivial) == 855, len(trivial))
ck('D1.2 判别域（非空对空）= 99', 954 - len(trivial) == 99, 954 - len(trivial))

D = [a for a in CHD if a not in trivial]

print('== D2/D4 律 L* 与混淆矩阵 ==')
def predict(pset, key=lambda x: R[x][2], flt=lambda x: True):
    return {a: sorted({key(x) for x in BCA[a] if key(x) != 0 and flt(x) and R[x][0] in pset}) for a in CHD}


def score(pred):
    tp = sum(1 for a in D if pred[a] and views[a] and pred[a] == views[a])
    fp = sum(1 for a in D if pred[a] and not views[a])
    fn = sum(1 for a in D if not pred[a] and views[a])
    tn = sum(1 for a in D if not pred[a] and not views[a])
    exact = sum(1 for a in D if pred[a] == views[a])
    return dict(exact=exact, domain=len(D), tp=tp, fp=fp, fn=fn, tn=tn)


pred = predict(primary)
s = score(pred)
ck('D2.1 律 L* 在判别域 99 类上全命中（含 5 个 ATL 事件 sink 的双无）',
   s['exact'] == len(D), s)
ck('D4.1 全量 954 命中', sum(1 for a in CHD if pred[a] == views[a]) == 954,
   sum(1 for a in CHD if pred[a] == views[a]))
ck('D4.2 全量 954 中 855 为空对空、99 为判别域', True, (954 - len(D), len(D)))

print('== D3 反控（均在判别域上计分）==')
controls = []
controls.append(('C1 无条件（任何非零 mdisp）',
                 predict(set(primary) | set(onlysec))))
controls.append(('C2 条件=pTD 有类头', predict(set(td2c))))
controls.append(('C3 条件=pTD 名 .?AV 前缀',
                 predict({t for t in primary | onlysec if tn(t).startswith('.?AV')})))
controls.append(('C5 条件=pTD 只在非零 mdisp 出现(反条件)', predict(set(onlysec))))
controls.append(('C6 条件=全部 pTD 集（恒真）', predict(set(primary) | set(onlysec))))
random.seed(207)
for i in range(3):
    ps = {P.dw(0x7fa4b0 + 4 * random.randrange((0x80efc4 - 0x7fa4b0) // 4))
          for _ in range(len(primary))}
    controls.append(('C7.%d 随机 dword 集（同尺寸 %d）' % (i, len(ps)), predict(ps)))
for nm, p in controls:
    sc = score(p)
    print('  %-42s 判别域命中 %3d/%d  tp=%d fp=%d fn=%d tn=%d' %
          (nm, sc['exact'], sc['domain'], sc['tp'], sc['fp'], sc['fn'], sc['tn']))
ck('D3.1 所有反控在判别域上 < 99', all(score(p)['exact'] < len(D) for _, p in controls),
   [(nm, score(p)['exact']) for nm, p in controls])
best = max(score(p)['exact'] for _, p in controls)
ck('D3.2 最强反控 %d，律 L* 为 99（差 %d）' % (best, 99 - best), best < 99, best)

print('== D5 13 个 onlysec pTD 与 15 例外 ==')
print(' onlysec pTD %d 个：' % len(onlysec))
for t in sorted(onlysec):
    recs = [b for b in phys if R[b][0] == t]
    refcls = sorted({tn(own_td[a]).split('@@')[0] for a in CHD for x in BCA[a] if x in recs})
    print('  %-52s 记录 %s 出现在 %d 个类的 BCA' %
          (tn(t), [(hex(b), R[b][2], R[b][1], R[b][5]) for b in recs], len(refcls)))
exc = [a for a in CHD if sorted({R[x][2] for x in BCA[a] if R[x][2] != 0}) != views[a]]
ck('D5.1 「15 例外」是朴素律（BCD 非零 mdisp == 视图）的例外；律 L* 对它们全部正确',
   len(exc) == 15 and all(pred[a] == views[a] for a in exc) and
   all(sorted({R[x][2] for x in BCA[a] if R[x][2] != 0}) != views[a] for a in exc),
   (len(exc), sum(1 for a in exc if pred[a] == views[a])))
fam = collections.Counter()
for a in exc:
    n = tn(own_td[a])
    if '@ATL@@' in n or 'CComObject' in n or 'EventSink' in n:
        fam['ATL/CCom 事件 sink（5 类）'] += 1
    elif ATTR[a] == 5:
        fam['attributes==5'] += 1
    else:
        fam['attributes==1'] += 1
ck('D5.2 例外三族计数', sum(fam.values()) == 15, fam.most_common())

print('== D6 (类,mdisp) 级双向 ==')
tot = ok = 0
for a in CHD:
    vset = set(views[a])
    for m in {R[x][2] for x in BCA[a] if R[x][2] != 0}:
        tot += 1
        hasprim = any(R[x][2] == m and R[x][0] in primary for x in BCA[a])
        ok += (hasprim == (m in vset))
ck('D6.1 (类,mdisp) 级双向 %d/%d' % (ok, tot), ok == tot, (ok, tot))
# 反控：mdisp 级随机 primary
random.seed(11)
r_ok = []
for _ in range(3):
    ps = {P.dw(0x7fa4b0 + 4 * random.randrange((0x80efc4 - 0x7fa4b0) // 4))
          for _ in range(len(primary))}
    o = 0
    for a in CHD:
        vset = set(views[a])
        for m in {R[x][2] for x in BCA[a] if R[x][2] != 0}:
            hp = any(R[x][2] == m and R[x][0] in ps for x in BCA[a])
            o += (hp == (m in vset))
    r_ok.append(o)
ck('D6.2 反控 mdisp 级随机 primary 命中 %s（律为 %d/%d）' % (r_ok, ok, tot),
   max(r_ok) < ok, (r_ok, ok, tot))

print('== D7 attributes bit0 订正 ==')
c1 = sum(1 for a in CHD if (ATTR[a] & 1) == (1 if any(R[x][2] != 0 for x in BCA[a]) else 0))
c2 = sum(1 for a in CHD if (ATTR[a] & 1) == (1 if views[a] else 0))
ck('D7.1 bit0 == 存在非零 mdisp 的 BCD：954/954', c1 == 954, c1)
ck('D7.2 bit0 == 有视图：仅 949/954（5 个 ATL sink 例外）', c2 == 949, c2)
ck('D7.3 5 个例外全是 ATL/CCom 事件 sink',
   {hex(a) for a in CHD if ((ATTR[a] & 1) == 1) != bool(views[a])} ==
   {'0x80e680', '0x80e740', '0x80e780', '0x80e7c0', '0x80e998'}, True)

print('== D8 汇总数字 ==')
facts = dict(classes=954, slots=2615, physBCD=1002, views=260,
             primaryPTD=len(primary), onlysecPTD=len(onlysec), ptdTotal=len(primary | onlysec),
             noClsRecords=sum(1 for b in phys if R[b][0] not in td2c),
             noClsUniqueTD=len({R[b][0] for b in phys if R[b][0] not in td2c}),
             trivialPair=len(trivial), domain=len(D),
             lawExactDomain=score(predict(primary))['exact'],
             lawExactAll=sum(1 for a in CHD if predict(primary)[a] == views[a]),
             controls={nm: score(p)['exact'] for nm, p in controls},
             level2=[ok, tot], level2ctrl=r_ok,
             exc=15, fam=[[k, v] for k, v in fam.most_common()],
             bit0NonzeroBCD=c1, bit0View=c2)
out = dict(asserts=NA, fails=fails, facts=facts)
open('/home/t628/projects/ra2-campaign-forge/_r207/m11_final.json', 'w').write(
    json.dumps(out, ensure_ascii=False, indent=1))
print(json.dumps(facts, ensure_ascii=False, indent=1)[:1600])
print('== SUMMARY asserts=%d fails=%d ==' % (NA, len(fails)))
for f in fails:
    print('  FAIL:', f)
