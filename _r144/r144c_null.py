#!/usr/bin/env python3
"""R144 C：0.9231 这个一致率是不是退化判据 —— 正确零模型 + 子集判别力。

R144 B 里我写了三条「一致率」断言，其中两条已被自己的输出否掉：
  置换反控（同 disp 桶内打乱 vt）得到**与实测完全相同**的 0.9231 ⇒ 该反控退化：
  统计量 = Σ_sites [COLoff(vt)==disp] 在「按 disp 分桶内重排 vt」下是不变量。

本脚本给出：
  ① 恒等式证明的数值验证：桶内置换 K=5 次，一致率逐次相等（差值 0）；
  ② 正确零模型（边缘独立性基线）Σ_d P(COLoff=d)·P(disp=d)，两边缘均实测；
  ③ 判别力更好的统计量：只在 disp≠0 子集上算一致率，并与同口径零模型对比；
  ④ 44 个 disp=0 但 COLoff≠0 的站点：它们是不是「把次虚表装到偏移 0」——
     查这些站点所在函数里是否同时装了同 TD 的主虚表（offset=0 的那张）。
"""
import sys, json, collections, random, hashlib, time
sys.path.insert(0, '_r143')
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
import r143lib as L

T0 = time.time()
B = L.Bin(); md = Cs(CS_ARCH_X86, CS_MODE_32)
TDs, COL, VTS = B.vtset()
GEN = L.GEN

COLof = {}
for vt in VTS:
    c = B.dw(vt - 4)
    if c in COL: COLof[vt] = c
coloff = {c: B.dw(c + 4) for c in COL}
coltd = {c: B.dw(c + 12) for c in COL}
def off_of(vt):
    c = COLof.get(vt)
    return None if c is None else coloff[c]
def td_of(vt):
    c = COLof.get(vt)
    return None if c is None else coltd[c]

def immv(t): return (int(t, 16) if t.startswith('0x') else int(t)) & 0xFFFFFFFF

sites = []
for a, sz, mn, op in B.sweep(md):
    if not op: continue
    m = L.RE_STORE.match(op)
    if not m: continue
    base = m.group(1); ds = L.disp_of(m.group(2)); tgt = m.group(3)
    if tgt is not None and L.RE_IMM.match(tgt):
        iv = immv(tgt)
        if iv in VTS and base in GEN:
            sites.append((a, base, ds, iv))

def rate(pairs):
    ok = tot = 0
    for vt, d in pairs:
        o = off_of(vt)
        if o is None: continue
        tot += 1; ok += (o == d)
    return ok, tot

real = [(s[3], s[2]) for s in sites]
ok0, tot0 = rate(real)

# ① 桶内置换 K 次
random.seed(144)
buckets = collections.defaultdict(list)
for vt, d in real: buckets[d].append(vt)
perma = []
for k in range(5):
    rows = []
    for d, vs in buckets.items():
        sh = vs[:]; random.shuffle(sh)
        rows += list(zip(sh, [d] * len(sh)))
    ok, tot = rate(rows)
    perma.append([ok, tot, round(ok / tot, 6)])

# ② 边缘独立性零模型
cnt_off = collections.Counter(o for vt in VTS for o in [off_of(vt)] if o is not None)
cnt_disp = collections.Counter(s[2] for s in sites)
n_off = sum(cnt_off.values()); n_disp = sum(cnt_disp.values())
null = sum((cnt_off[d] / n_off) * (cnt_disp[d] / n_disp) for d in set(cnt_off) | set(cnt_disp))

# ③ disp≠0 子集
sub = [(vt, d) for vt, d in real if d != 0]
okS, totS = rate(sub)
cnt_disp_nz = collections.Counter(d for d in cnt_disp.elements() if d != 0)
n_nz = sum(cnt_disp_nz.values())
null_nz = sum((cnt_off[d] / n_off) * (cnt_disp_nz[d] / n_nz) for d in set(cnt_off) | set(cnt_disp_nz))

# disp==0 子集
sub0 = [(vt, d) for vt, d in real if d == 0]
okS0, totS0 = rate(sub0)
null0 = (cnt_off[0] / n_off)

# ④ 44 个 disp=0 但 offset!=0
odd = [(a, base, vt, off_of(vt), td_of(vt)) for a, base, d, vt in sites if d == 0 and off_of(vt) not in (0, None)]
# 同 TD 是否有 offset==0 的成员且被 disp0 装过
f1vt = {vt for vt in VTS if off_of(vt) == 0}
td0 = collections.defaultdict(list)
for vt in VTS:
    t = td_of(vt)
    if t is not None: td0[t].append(vt)
odd_detail = []
for a, base, vt, o, t in odd[:20]:
    tw = [x for x in td0.get(t, []) if off_of(x) == 0]
    odd_detail.append([hex(a), base, hex(vt), o, hex(t) if t else None,
                       [hex(x) for x in tw[:2]], any(x in {s[3] for s in sites if s[2] == 0} for x in tw)])

# ⑤ 增量：disp≠0 一致性里，「同 TD 存在 offset=0 成员」的比例（多重继承的确证形态）
pos_mi = [(vt, d) for vt, d in sub if off_of(vt) is not None]
mi_ok = sum(1 for vt, d in pos_mi if any(off_of(x) == 0 for x in td0.get(td_of(vt), [])))
mi_all = len(pos_mi)

res = {
 'exe_sha256': hashlib.sha256(B.data).hexdigest(), 'exe_bytes': B.N,
 'vt_distinct': len(VTS), 'sites': len(sites),
 'rate_all': [ok0, tot0, round(ok0 / tot0, 6)],
 'perm_within_bucket': perma,
 'perm_identical': all(p[2] == round(ok0 / tot0, 6) for p in perma),
 'null_independence': round(null, 6),
 'rate_disp_nonzero': [okS, totS, round(okS / totS, 6)],
 'null_disp_nonzero': round(null_nz, 6),
 'rate_disp0': [okS0, totS0, round(okS0 / totS0, 6)],
 'null_disp0': round(null0, 6),
 'off0_share_of_vts': round(cnt_off[0] / n_off, 6),
 'disp0_share_of_sites': round(cnt_disp[0] / n_disp, 6),
 'odd_disp0_nonooffset_n': len(odd),
 'odd_detail': odd_detail,
 'mi_confirm_rate': [mi_ok, mi_all, round(mi_ok / mi_all, 4) if mi_all else None],
 'elapsed_s': round(time.time() - T0, 1),
}

POS = []
def chk(n, c, v): POS.append([n, bool(c), v])
chk('桶内置换 5 次的一致率与实测完全相同（反控退化，已被证明）', res['perm_identical'], [p[2] for p in perma])
chk('正确零模型基线 < 实测一致率（实测有超出独立性的信号）', null < ok0 / tot0, [round(null, 4), round(ok0 / tot0, 4)])
chk('disp≠0 子集上实测一致率 > 0.9', totS and okS / totS > 0.9, round(okS / totS, 4) if totS else None)
chk('disp≠0 子集零模型 < 0.1（子集口径才有判别力）', null_nz < 0.1, round(null_nz, 4))
chk('disp==0 子集一致率 == off0 在 VTS 中的占比（同一恒等式）', abs((okS0 / totS0) - null0) < 1e-9, [round(okS0 / totS0, 6), round(null0, 6)])
chk('存在 disp=0 却装 offset≠0 虚表的站点（需单独定性）', len(odd) > 0, len(odd))
chk('disp≠0 且 offset=0 的成员存在（多重继承主虚表被装在非零位移）', mi_all - mi_ok > 0, [mi_ok, mi_all])
res['POS'] = POS
res['pos_pass'] = sum(1 for x in POS if x[1]); res['pos_fail'] = sum(1 for x in POS if not x[1])
json.dump(res, open('_r144/r144c_null.json', 'w'), indent=1)
print(json.dumps({k: v for k, v in res.items() if k not in ('POS', 'odd_detail')}, indent=1, ensure_ascii=False)[:4200])
print('odd', json.dumps(res['odd_detail'], ensure_ascii=False))
print('\n'.join('%-70s %s %s' % (p[0], p[1], p[2]) for p in POS))
print('POS %d/%d FAIL %d' % (res['pos_pass'], len(POS), res['pos_fail']))
