#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R207 m10：把「额外视图 COL 何时生成」收成一条可证伪律（本轮核心交付）。
候选律 L*：类 a 的 BCA 中 mdisp==m 的项若存在，则该 m 产生一条视图 COL，
           当且仅当 m 上有**至少一个**基类 pTD 在全局（任一类的 BCA 中）出现过 mdisp==0 的记录；
           即 pTD 以「主基类(primary base)」身份出现过 ⇒ 它有 vftable 视图。
反控：
  C1 忽略该条件（只要有非零 mdisp 就生成视图）⇒ 多预测若干
  C2 用「pTD 有类头」做条件（R207 m9 的错误律）
  C3 用 pTD 名以 .?AV 开头
  C4 全局置换 pTD → mdisp==0 关系
  C5 把条件改成「该 pTD 的全部记录 mdisp!=0」
逐类精确比对 954 类、260 条视图。"""
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
# 全局：哪些 pTD 曾在任何类的 BCA 中以 mdisp==0 身份出现
primary = {R[b][0] for b in phys if R[b][2] == 0}
onlysec = {R[b][0] for b in phys if R[b][2] != 0} - primary
print('== 0 基础计数 ==')
ck('C0.1 pTD 总数 %d；曾以 mdisp==0 出现 %d；只在非零 mdisp 出现 %d'
   % (len(primary) + len(onlysec), len(primary), len(onlysec)), len(primary) + len(onlysec) == 988,
   (len(primary), len(onlysec)))
print(' 只在非零 mdisp 出现的 pTD %d 个：%s' %
      (len(onlysec), sorted(tn(t) for t in onlysec)))

print('== L* 律 ==')
pred = {}
for a in CHD:
    ms = {R[x][2] for x in BCA[a] if R[x][2] != 0 and R[x][0] in primary}
    pred[a] = sorted(ms)
eqv = sum(1 for a in CHD if pred[a] == views[a])
ck('L*1 逐类预测视图 mdisp 集 == 实际：954/954', eqv == 954, (eqv, 954))
bad = [(hex(a), tn(own_td[a]).split('@@')[0], pred[a], views[a]) for a in CHD if pred[a] != views[a]]
for b in bad[:8]:
    print('   例外', b)
ck('L*2 视图总数 260 且预测一致', sum(len(v) for v in pred.values()) == 260 ==
   sum(len(v) for v in views.values()), (sum(len(v) for v in pred.values()),
                                         sum(len(v) for v in views.values())))

print('== 反控 ==')
c1 = sum(1 for a in CHD if sorted({R[x][2] for x in BCA[a] if R[x][2] != 0}) == views[a])
ck('C1 忽略 primary 条件 ⇒ 命中 %d/954' % c1, c1 < 954, (c1, 954 - c1))
c2 = sum(1 for a in CHD if sorted({R[x][2] for x in BCA[a]
                                   if R[x][2] != 0 and R[x][0] in td2c}) == views[a])
ck('C2 用「pTD 有类头」条件（m9 错律）⇒ 命中 %d/954' % c2, c2 < 954, c2)
c3 = sum(1 for a in CHD if sorted({R[x][2] for x in BCA[a]
                                   if R[x][2] != 0 and tn(R[x][0]).startswith('.?AV')}) == views[a])
ck('C3 用「名字 .?AV 前缀」⇒ 命中 %d/954' % c3, c3 < 954, c3)
c5 = sum(1 for a in CHD if sorted({R[x][2] for x in BCA[a]
                                   if R[x][2] != 0 and R[x][0] in onlysec}) == views[a])
ck('C5 用「只在非零 mdisp 出现」反条件 ⇒ 命中 %d/954' % c5, c5 < 954, c5)
random.seed(207)
sh = list(primary)
random.shuffle(sh)
ps = set(sh)
c4 = sum(1 for a in CHD if sorted({R[x][2] for x in BCA[a] if R[x][2] != 0 and R[x][0] in ps}) == views[a])
ck('C4 反控：primary 集随机置换 ⇒ 命中 %d/954' % c4, c4 < 700, c4)

print('== 15 例外的归因（用 L* 口径）==')
exc = [a for a in CHD if sorted({R[x][2] for x in BCA[a] if R[x][2] != 0}) != views[a]]
ck('L*3 15 个例外类', len(exc) == 15, len(exc))
for a in exc:
    miss = sorted({R[x][2] for x in BCA[a] if R[x][2] != 0} - set(views[a]))
    culp = sorted({tn(R[x][0]).split('@@')[0] for x in BCA[a] if R[x][2] in miss})
    print('   %-9s %-32s attr=%d 缺=%s 肇因=%s' %
          (hex(a), tn(own_td[a]).split('@@')[0], ATTR[a], miss, culp))
culpits = collections.Counter()
for a in exc:
    miss = {R[x][2] for x in BCA[a] if R[x][2] != 0} - set(views[a])
    for x in BCA[a]:
        if R[x][2] in miss:
            culpits[tn(R[x][0])] += 1
ck('L*4 肇因 pTD 全集（只应在 onlysec 里）', set(culpits) <= {tn(t) for t in onlysec},
   (len(culpits), sorted(culpits)))
print(' 肇因 pTD 命中次数:', culpits.most_common())

print('== 5 个 onlysec pTD 的完整记录 ==')
for t in sorted(onlysec):
    recs = [b for b in phys if R[b][0] == t]
    print('  %-42s %s' % (tn(t), [(hex(b), R[b][2], R[b][1], R[b][5]) for b in recs]))

print('== L* 的等价表述：「视图 ⟺ 该 mdisp 上存在曾经当过主基类的 pTD」 ==')
# 逐条 mdisp 级验证（不按类聚合）
tot = 0
ok = 0
for a in CHD:
    vset = set(views[a])
    for m in {R[x][2] for x in BCA[a] if R[x][2] != 0}:
        tot += 1
        hasprim = any(R[x][2] == m and R[x][0] in primary for x in BCA[a])
        if hasprim == (m in vset):
            ok += 1
ck('L*5 (类,mdisp) 级双向：%d/%d' % (ok, tot), ok == tot, (ok, tot))

out = dict(asserts=NA, fails=fails, facts=dict(
    law_eq=eqv, views=260, primaryPTD=len(primary), secondaryOnly=len(onlysec),
    secondaryNames=sorted(tn(t) for t in onlysec),
    c1=c1, c2=c2, c3=c3, c4=c4, c5=c5, exc=len(exc),
    level2=[ok, tot], culpit=culpits.most_common()))
open('/home/t628/projects/ra2-campaign-forge/_r207/m10_law.json', 'w').write(
    json.dumps(out, ensure_ascii=False, indent=1))
print(json.dumps(out['facts'], ensure_ascii=False)[:1000])
print('== SUMMARY asserts=%d fails=%d ==' % (NA, len(fails)))
for f in fails:
    print('  FAIL:', f)
