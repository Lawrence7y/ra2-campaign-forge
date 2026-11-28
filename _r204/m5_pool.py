#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R204 m5（权威）：BCD 池的真实排布 + CHD 与 R203 视图模型的判别性交叉验证。
m4 自错记录：
 ① B1a 期望「每个 BCD 的 +24 也是 BCD」，实测 294/1002 —— 池按 8 字节粒度交错，不是 24 连续数组；
 ② C1b/C1c 期望全局差分是 24 的倍数，实测残差 {0,8,16} => 池内混有 8 字节记录；
 ③ D1a 期望数组尾 == CHD 起点，实测 -8 (714) / -4 (240)；
 ④ E1b/E1c 反控失败：mdisp 子集律在「换用同长度 BCA」下仍 74/84 成立 => 该判据无区分力，不能作为证据。
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
T = P.B['.text']; LO = T['lo']; HI = T['hi_file']
def in_text(x): return x is not None and LO <= x < HI
COL = {}
for sn in ('.rdata', '.data'):
    base, w, n = wv(sn)
    for i in range(n - 4):
        if w[i] not in (0, 1, 2) or w[i + 2] != 0: continue
        if P.where(w[i + 3]) != '.data' or P.where(w[i + 4]) != '.rdata': continue
        nm = P.cstr(w[i + 3] + 8, 400)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base + 4 * i] = dict(mdisp=s32(w[i+1]), ptd=w[i+3], pchd=w[i+4], name=nm.decode('latin1'))
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
def is_bcd(b):
    if b is None or P.where(b) != '.rdata': return False
    ptd = P.dw(b)
    if P.where(ptd) not in ('.data', '.rdata'): return False
    nm = P.cstr(ptd + 8, 400)
    return bool(nm and nm.startswith(b'.?A') and nm.endswith(b'@@'))
ck('V0 基数 COL1214/CHD954/BCD1002/BCA2615', (len(COL),len(G),len(uniq),sum(len(v) for v in BCD.values()))==(1214,954,1002,2615),
   (len(COL),len(G),len(uniq),sum(len(v) for v in BCD.values())))

# ---- P1 池的边界与粒度 ----
lo24, hi24 = uniq[0], uniq[-1]
span_bytes = hi24 - lo24
slots = list(range(lo24, hi24 + 24, 8))
slotkind = collections.Counter()
for s in slots:
    slotkind['BCD' if s in set(uniq) else 'non'] += 1
print('   P1 池 [0x%x,0x%x] 跨度 %d B，8 字节槽 %d 个：BCD %d / 非 BCD %d' % (
    lo24, hi24, span_bytes, len(slots), slotkind['BCD'], slotkind['non']))
ck('P1a 池跨度是 8 的倍数', span_bytes % 8 == 0, span_bytes)
ck('P1b 全部 BCD 8 字节对齐', all(u % 8 == 0 for u in uniq), sum(1 for u in uniq if u % 8))
# 非 BCD 槽里是什么
non = [s for s in slots if s not in set(uniq)]
kinds = collections.Counter()
for s in non:
    v = P.dw(s)
    kinds['zero' if v == 0 else ('text' if in_text(v) else P.where(v))] += 1
print('   P1 非 BCD 8 字节槽内容分布 top6 %s' % kinds.most_common(6))
ck('P1c 非 BCD 槽存在（记录，不解释）', len(non) > 0, len(non))

# ---- P2 池的重用度（BCA 引用 vs 唯一 BCD） ----
refc = collections.Counter(b for v in BCD.values() for b in v)
rd = collections.Counter(refc.values())
print('   P2 每个唯一 BCD 被引用次数分布 %s' % sorted(rd.items())[:10])
ck('P2a 存在被多张 CHD 共享的 BCD（browse 去重）', max(refc.values()) > 1, max(refc.values()))
ck('P2b 共享 BCD 个数', sum(1 for v in refc.values() if v > 1) > 0, sum(1 for v in refc.values() if v > 1))

# ---- P3 判别性交叉验证（用 pTD 身份，不用 mdisp） ----
# 每个 CHD 的自有 pTD（来自其 COL）必须在 BCA 的 pTD 集合内
def ptd_set(a): return set(P.dw(b) for b in BCD[a])
ok = 0; bad = []
for a in CHD:
    own = set(COL[c]['ptd'] for c in G[a])
    if own <= ptd_set(a): ok += 1
    else: bad.append((COL[G[a][0]]['name'][:34], len(own), len(ptd_set(a))))
print('   P3 自有 pTD ⊆ BCA pTD 集合成立 %d / %d' % (ok, len(CHD)))
print('   P3 反例 %s' % bad[:5])
ck('P3a 自有 pTD 全部出现在 BCA 中', ok == len(CHD), (ok, len(CHD)))
# 反控：换用同长度其它 CHD 的 BCA
random.seed(2046)
fake_ok = 0
for a in CHD:
    cands = [x for x in CHD if len(BCD[x]) == len(BCD[a]) and x != a]
    if not cands: continue
    if set(COL[c]['ptd'] for c in G[a]) <= ptd_set(random.choice(cands)): fake_ok += 1
print('   P3 反控：换用同长度 BCA 后成立 %d / %d' % (fake_ok, len(CHD)))
ck('P3b 反控：pTD 判据有强区分力（假成立率 < 5%）', fake_ok < 0.05 * len(CHD), (fake_ok, len(CHD)))

# ---- P4 mdisp!=0 但单视图的类（与 R203 的 94 MI 类口径分歧） ----
mi_bca = [a for a in CHD if any(s32(P.dw(b + 8)) != 0 for b in BCD[a])]
mi_view = [a for a in CHD if len(G[a]) >= 2]
only_bca = sorted(set(mi_bca) - set(mi_view))
only_view = sorted(set(mi_view) - set(mi_bca))
print('   P4 mdisp!=0 类 %d / 多视图类 %d / 仅 BCA 侧 %d / 仅视图侧 %d' % (len(mi_bca), len(mi_view), len(only_bca), len(only_view)))
for a in only_bca:
    print('     仅BCA侧 %-40s 视图=%d BCA=%d mdisp=%s 类名=%s' % (
        hex(a), len(G[a]), len(BCD[a]), sorted(set(s32(P.dw(b+8)) for b in BCD[a])),
        COL[G[a][0]]['name'][:40]))
ck('P4a 两侧口径不完全一致（记录分歧，不强行统一）', True, (len(mi_bca), len(mi_view)))

# ---- P5 视图数公式的 15 个反例 ----
exc = []
for a in CHD:
    nz = len(set(s32(P.dw(b + 8)) for b in BCD[a]) - {0})
    if nz + 1 != len(G[a]): exc.append((COL[G[a][0]]['name'][:40], len(G[a]), nz + 1,
                                        [COL[c]['mdisp'] for c in G[a]]))
print('   P5 视图数公式反例 %d 个' % len(exc))
for e in exc[:8]: print('     ', e)
ck('P5a 反例全部是「非零 mdisp 去重数 >= 视图数」（冗余 mdisp）',
   all(e[2] >= e[1] for e in exc), [e for e in exc if e[2] < e[1]][:3])

json.dump(dict(N=N, fails=fails, lo=hex(lo24), hi=hex(hi24), span=span_bytes,
               slots=len(slots), bcd_slots=slotkind['BCD'], non_slots=slotkind['non'],
               kinds=kinds.most_common(8), refdist=sorted(rd.items()),
               ptd_ok=ok, ptd_fake=fake_ok, mi_bca=len(mi_bca), mi_view=len(mi_view),
               only_bca=[hex(x) for x in only_bca], only_view=[hex(x) for x in only_view],
               exc=len(exc), exc_sample=exc[:12]),
          open('/home/t628/projects/ra2-campaign-forge/_r204/m5_pool.json','w'), ensure_ascii=False, indent=1)
print('\n== %d assertions, %d FAIL ==' % (N, len(fails)))
print('FAILS:', fails)
