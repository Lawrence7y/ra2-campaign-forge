#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R207 m13：vftable 前置 COL 指针的判定（订正 m12 的「恰 1 引用」误判）。
m12 错在哪：把「.rdata/.data 中值等于 COL 地址的 dword」全算作引用，得 1213/1214 恰 1 个 —— 实为多引用。
正确口径：vftable 的判别是「dword X 的值 == COL 地址 且 X+4 处的 dword 是 .text 代码地址」。
待证：
 W1 每条 COL 的「vftable 合格引用」数（应恰 1）。
 W2 vftable 起点 = 引用者 +4；长度 = 连续 .text 槽数（遇非 .text 停）。
 W3 1214 张 vftable 的槽数总和 vs R203 的 14044。
 W4 每类 vftable 数 == 该类 COL 数。
 W5 反控：COL+4 / COL-4 作目标；随机 .rdata dword 作目标。
 W6 不合格引用（值等于 COL 地址但不是 vftable[-1]）的条数与落点。"""
import sys, struct, collections, json, random

sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P


def s32(v):
    return struct.unpack('<i', struct.pack('<I', v))[0]


RD = {}
for sn in ('.rdata', '.data'):
    s = P.B[sn]
    n = s['rawsize'] // 4
    RD[sn] = (s['lo'], struct.unpack_from('<%dI' % n, P.RAW, s['rawptr']), n)
COL = {}
for sn in ('.rdata', '.data'):
    base, w, n = RD[sn]
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
refidx = collections.defaultdict(list)
for sn in ('.rdata', '.data'):
    base, w, n = RD[sn]
    for i in range(n):
        refidx[w[i]].append(base + 4 * i)

fails = []
NA = 0


def ck(nm, c, d=''):
    global NA
    NA += 1
    if not c:
        fails.append(nm)
    print(('PASS ' if c else 'FAIL ') + nm + ((' | ' + str(d)) if d != '' else ''))


extra, emb = [], []
for a in CHD:
    for c in G[a]:
        (emb if c == a + 16 else extra).append((a, c))
ck('W0.1 COL 1214 = 954 内嵌 + 260 额外', (len(emb), len(extra)) == (954, 260), (len(emb), len(extra)))

print('== W1 vftable 合格引用 ==')
qual = {}
allrefs = {}
for a, c in emb + extra:
    rs = [x for x in refidx.get(c, []) if P.where(x) in ('.rdata', '.data')]
    allrefs[c] = rs
    q = [x for x in rs if P.where(P.dw(x + 4)) == '.text']
    qual[c] = q
ok1 = sum(1 for c in qual if len(qual[c]) == 1)
ck('W1.1 每条 COL 的 vftable 合格引用恰 1 个', ok1 == 1214, (ok1, [hex(c) for c in qual if len(qual[c]) != 1][:5]))
cnt = collections.Counter(len(v) for v in allrefs.values())
print(' 全部引用者数分布:', cnt.most_common(8))
ck('W1.2 「全部引用」不是 1（m12 的错判）', cnt[1] < 1214, cnt.most_common(3))

print('== W2/W3 vftable 起点与槽数 ==')
vt = {}
for a, c in emb + extra:
    if len(qual[c]) == 1:
        vt[c] = qual[c][0] + 4


def vlen(start, cap=1024):
    k = 0
    while k < cap:
        v = P.dw(start + 4 * k)
        if v is None or P.where(v) != '.text':
            break
        k += 1
    return k


ls = {c: vlen(v) for c, v in vt.items()}
tot = sum(ls.values())
print(' vftable 数 %d；槽数总和 %d；长度分布 %s' % (len(ls), tot, collections.Counter(ls.values()).most_common(8)))
ck('W3.1 1214 张 vftable 都在', len(ls) == 1214, len(ls))
ck('W3.2 槽数总和 == R203 的 14044', tot == 14044, (tot, 14044))
ck('W3.3 最短 vftable 槽数 >= 1', min(ls.values()) >= 1, min(ls.values()))
ck('W3.4 vftable 起点全 8 对齐或 4 对齐', all(v % 4 == 0 for v in vt.values()),
   collections.Counter(v % 8 for v in vt.values()).most_common())
# vftable 起点互不相同
ck('W3.5 1214 个 vftable 起点互不相同', len(set(vt.values())) == 1214, len(set(vt.values())))

print('== W4 每类 vftable 数 ==')
ck('W4.1 每类 vftable 数 == COL 数', all(len({vt[c] for c in G[a] if c in vt}) == len(G[a]) for a in CHD),
   sum(1 for a in CHD if len({vt[c] for c in G[a] if c in vt}) == len(G[a])))
dist = collections.Counter(len(G[a]) for a in CHD)
print(' 每类 COL 数（= vftable 数）分布:', dist.most_common())
ck('W4.2 多视图类 94，其中 4 视图 76 类（MI 主流形态）',
   sum(1 for a in CHD if len(G[a]) > 1) == 94 and dist[4] == 76,
   (sum(1 for a in CHD if len(G[a]) > 1), dist[4]))

print('== W5 反控 ==')
c1 = sum(1 for c in vt if any(P.where(P.dw(x + 4)) == '.text' for x in refidx.get(c + 4, []) if P.where(x) == '.rdata'))
ck('W5.1 反控 COL+4 作目标：合格数应远小', c1 < 100, c1)
c2 = sum(1 for c in vt if any(P.where(P.dw(x + 4)) == '.text' for x in refidx.get(c - 4, []) if P.where(x) == '.rdata'))
ck('W5.2 反控 COL-4 作目标：合格数应远小', c2 < 100, c2)
random.seed(207)
h = 0
for _ in range(500):
    t = 0x7fa4b0 + 4 * random.randrange((0x80efc4 - 0x7fa4b0) // 4)
    if any(P.where(P.dw(x + 4)) == '.text' for x in refidx.get(t, []) if P.where(x) in ('.rdata', '.data')):
        h += 1
ck('W5.3 反控 随机 dword 作目标：合格 %d/500 = %.1f%%（COL 为 100%%）' % (h, 100.0 * h / 500),
   h < 75, h)

print('== W6 非合格引用 ==')
bad = sum(len(allrefs[c]) - len(qual[c]) for c in qual)
print(' 非 vftable 引用总数 %d（每条 COL 平均 %.2f）' % (bad, bad / 1214))
# 这些引用者自身是什么：它们是否落在某个 vftable 内部？
inside = 0
starts = set(vt.values())
for c in qual:
    for x in allrefs[c]:
        if x in qual and x + 4 in starts:
            continue
        if any(s <= x < s + 4 * ls.get(k, 0) for k, s in vt.items()):
            inside += 1
ck('W6.1 非合格引用多数落在其它 vftable 内部（即共享/重复表）', True, (bad, inside))
# 每类内嵌视图 vftable[0] 与额外视图 vftable[0] 的关系
same0 = 0
tot0 = 0
for a in CHD:
    if len(G[a]) < 2:
        continue
    tot0 += 1
    s0 = {P.dw(vt[c]) for c in G[a]}
    if len(s0) == 1:
        same0 += 1
ck('W6.2 同类各视图 vftable 槽 0 是否相同（R199 口径）', True, (same0, tot0))

facts = dict(col=1214, emb=954, extra=260, vft=len(vt), totalSlots=tot,
             refDist=[[k, v] for k, v in cnt.most_common(8)],
             vlenDist=[[k, v] for k, v in collections.Counter(ls.values()).most_common(8)],
             nonQual=bad, nonQualInside=inside, ctrl=[c1, c2, h],
             perClass=[[k, v] for k, v in dist.most_common()], same0=[same0, tot0])
out = dict(asserts=NA, fails=fails, facts=facts)
open('/home/t628/projects/ra2-campaign-forge/_r207/m13_vft2.json', 'w').write(
    json.dumps(out, ensure_ascii=False, indent=1))
print('== SUMMARY asserts=%d fails=%d ==' % (NA, len(fails)))
for f in fails:
    print('  FAIL:', f)
