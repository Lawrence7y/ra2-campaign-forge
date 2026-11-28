#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R207 m9：把 15 个「BCD 有 mdisp!=0 却无视图」例外收成一条统一律（本轮核心交付）。
候选律 L：类 a 产生某条额外视图 COL（mdisp=m）⟺ a 的 BCA 中存在一条 BCD 记录 x，
          满足 R[x].mdisp == m 且 R[x].pTD **在本镜像中有对应类头**（pTD ∈ 954 own_td 值集）。
反控：
  C1 去掉后半条件（只看 mdisp!=0）⇒ 预测 954 类全有视图，实为 949
  C2 用「pTD 名以 .?AV 开头」作代理量
  C3 随机置换 pTD 后律崩塌
  C4 把 mdisp 换成 pdisp 后律崩塌
逐类精确预测 260 条视图（mdisp 值级），与实际比对。"""
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
views = {a: [(c, COL[c]['mdisp']) for c in sorted(G[a]) if c != a + 16] for a in CHD}

print('== L 律：视图 ⟺ BCD(mdisp!=0 且 pTD 有类头) ==')
pred = {}
for a in CHD:
    pred[a] = sorted({R[x][2] for x in BCA[a] if R[x][2] != 0 and R[x][0] in td2c})
act = {a: sorted(m for _, m in views[a]) for a in CHD}
eqv = sum(1 for a in CHD if pred[a] == act[a])
ck('L1.1 逐类预测的视图 mdisp 集 == 实际：954/954', eqv == 954, (eqv, 954))
bad = [(hex(a), tn(own_td[a]), pred[a], act[a]) for a in CHD if pred[a] != act[a]]
for b in bad[:8]:
    print('   例外', b)
ck('L1.2 视图总数预测 = 实际 = 260',
   sum(len(v) for v in pred.values()) == 260 == sum(len(v) for v in act.values()),
   (sum(len(v) for v in pred.values()), sum(len(v) for v in act.values())))

print('== 反控 ==')
c1 = sum(1 for a in CHD if sorted({R[x][2] for x in BCA[a] if R[x][2] != 0}) == act[a])
ck('C1 去掉「pTD 有类头」条件后命中数下降', c1 < 954, (c1, 954, 954 - c1))
c2 = sum(1 for a in CHD if sorted({R[x][2] for x in BCA[a]
                                   if R[x][2] != 0 and tn(R[x][0]).startswith('.?AV')}) == act[a])
ck('C2 用「名字以 .?AV 开头」当代理量：命中数', True, (c2, 954))
random.seed(207)
shuffled = list(own_td.values())
random.shuffle(shuffled)
tset = set(shuffled)
c3 = sum(1 for a in CHD if sorted({R[x][2] for x in BCA[a] if R[x][2] != 0 and R[x][0] in tset}) == act[a])
ck('C3 反控：pTD 集随机置换后命中数崩溃', c3 < 600, c3)
c4 = sum(1 for a in CHD if sorted({R[x][3] for x in BCA[a] if R[x][3] != 0}) == act[a])
ck('C4 反控：把 mdisp 换成 pdisp(恒-1) ⇒ 0', c4 == 0, c4)

print('== 15 个原始例外逐条归因 ==')
exc = [a for a in CHD if sorted({R[x][2] for x in BCA[a] if R[x][2] != 0}) != act[a]]
ck('L2.1 15 个例外 = 「BCD 有非零 mdisp 但缺视图」单向', len(exc) == 15, len(exc))
rows = []
for a in exc:
    miss = sorted({R[x][2] for x in BCA[a] if R[x][2] != 0 and R[x][0] not in td2c})
    names = sorted({tn(R[x][0]).split('@@')[0] for x in BCA[a]
                    if R[x][2] != 0 and R[x][0] not in td2c})
    rows.append((hex(a), tn(own_td[a]).split('@@')[0], ATTR[a], miss, names))
    print('   %-9s %-34s attr=%d 缺视图 mdisp=%s 基类=%s' % (hex(a), rows[-1][1], ATTR[a], miss, names))
ck('L2.2 每个例外缺的视图 mdisp 全部由「无类头 pTD」解释（无残留）',
   all(all(R[x][0] not in td2c for x in BCA[a] if R[x][2] in
           ({R[y][2] for y in BCA[a] if R[y][2] != 0} - {m for _, m in views[a]})) for a in exc), True)
# 例外族分解
f1 = [a for a in exc if ATTR[a] == 5 or tn(own_td[a]).startswith('.?AVStageClass')]
fam = collections.Counter()
for a in exc:
    n = tn(own_td[a])
    if '@ATL@@' in n or 'CComObject' in n or 'EventSink' in n:
        fam['ATL/CCom 事件 sink'] += 1
    elif ATTR[a] == 5:
        fam['attributes==5'] += 1
    else:
        fam['attributes==1（普通）'] += 1
ck('L2.3 例外两族分解', sum(fam.values()) == 15, fam.most_common())
print(' 例外族:', fam.most_common())

print('== 43 条无类头 TD 与视图缺失的一一对应 ==')
nohead = {R[b][0] for b in phys if R[b][0] not in td2c}
used_missing = set()
for a in exc:
    for x in BCA[a]:
        if R[x][2] != 0 and R[x][0] not in td2c:
            used_missing.add((R[x][0], R[x][2]))
print(' 例外引用的 (无类头 pTD, mdisp) 对 %d 个' % len(used_missing))
nh = sorted({t for t in nohead})
print(' 43 个无类头 pTD 中，被例外引用的 %d 个' %
      len({t for t, m in used_missing}))
ck('L3.1 视图缺失只由「例外类引用的无类头 pTD」造成',
   len({m for t, m in used_missing}) <= 6, sorted({m for t, m in used_missing}))
# 未被例外引用的无类头 pTD（即其 mdisp!=0 记录出现在有视图的类里？）
rest = nohead - {t for t, m in used_missing}
print(' 未被例外引用的无类头 pTD %d 个，例：%s' % (len(rest), [tn(t) for t in sorted(rest)[:5]]))
ck('L3.2 未被例外引用的无类头 pTD 只以 mdisp==0 出现',
   all(all(R[x][2] == 0 for a in CHD for x in BCA[a] if R[x][0] == t) for t in rest),
   sum(1 for t in rest if any(R[x][2] != 0 for a in CHD for x in BCA[a] if R[x][0] == t)))

print('== 与 attributes bit0 的关系（R205 QG4）==')
tab = collections.Counter((ATTR[a] & 1, len(views[a]) > 0) for a in CHD)
ck('L4.1 bit0 == 有视图：949 一致 + 5 例外（ATL 事件 sink）',
   tab[(0, False)] + tab[(1, True)] == 949 and tab[(1, False)] == 5, tab.most_common())
ck('L4.2 bit0 的真语义 = 存在 mdisp!=0 的 BCD（不看有无类头）：954/954',
   all((ATTR[a] & 1) == (1 if any(R[x][2] != 0 for x in BCA[a]) else 0) for a in CHD),
   collections.Counter((ATTR[a] & 1, bool(any(R[x][2] != 0 for x in BCA[a]))) for a in CHD).most_common())

out = dict(asserts=NA, fails=fails, facts=dict(
    law_eq=eqv, viewsPred=sum(len(v) for v in pred.values()), viewsAct=260,
    c1=c1, c2=c2, c3=c3, c4=c4, exc=len(exc),
    fam=[[k, v] for k, v in fam.most_common()],
    excRows=rows,
    noHeadUse=len(used_missing), noHeadRest=len(rest),
    bit0cross=[[list(k), v] for k, v in tab.most_common()]))
open('/home/t628/projects/ra2-campaign-forge/_r207/m9_unified.json', 'w').write(
    json.dumps(out, ensure_ascii=False, indent=1))
print(json.dumps(out['facts'], ensure_ascii=False)[:900])
print('== SUMMARY asserts=%d fails=%d ==' % (NA, len(fails)))
for f in fails:
    print('  FAIL:', f)
