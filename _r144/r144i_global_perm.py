#!/usr/bin/env python3
"""R144 I：全局置换反控（替代退化的桶内置换）+ 正确零模型 + 三层 lift。

S-306：R144B/C 用的「同 disp 桶内置换」是恒等式（两家族独立确认）：
  桶内置换只改桶内配对顺序、不改桶内 vt 多重集 ⇒ 统计量逐项不变，方差 0，零信息。
本脚本改用**全局置换**（在全部 4046 站点间打乱 vt 序列），这才是真正的零假设。
另给出：站点级边缘基线（与全局置换期望同值）vs 虚表总体边缘基线（我 R144C 用的那个，偏大）。
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
off_of = lambda vt: coloff.get(COLof.get(vt))
def immv(t): return (int(t, 16) if t.startswith('0x') else int(t)) & 0xFFFFFFFF

sites = []
for a, sz, mn, op in B.sweep(md):
    if not op: continue
    m = L.RE_STORE.match(op)
    if not m: continue
    base = m.group(1); ds = L.disp_of(m.group(2)); tgt = m.group(3)
    if tgt is not None and L.RE_IMM.match(tgt):
        iv = immv(tgt)
        if iv in VTS and base in GEN: sites.append((ds, iv))
disps = [s[0] for s in sites]; vts = [s[1] for s in sites]
N = len(sites)

def rate(ds_l, vt_l):
    ok = tot = 0
    for d, vt in zip(ds_l, vt_l):
        o = off_of(vt)
        if o is None: continue
        tot += 1; ok += (o == d)
    return ok, tot

okR, totR = rate(disps, vts)
# 全局置换 K=5（seed 144 起）
perms = []
random.seed(144)
for k in range(5):
    sh = vts[:]; random.shuffle(sh)
    ok, tot = rate(disps, sh)
    perms.append([ok, tot, round(ok / tot, 6)])
pm = sum(p[2] for p in perms) / len(perms)

# 站点级边缘基线：E = Σ_d P_site(d) · P_site(coloff(vt)=d)
site_vt = collections.Counter(vts)
grp = lambda d: 'd0' if d == 0 else ('small' if d in (4, 8, 12) else 'large')
sub = collections.defaultdict(lambda: [[], []])
for d, vt in sites:
    k = grp(d); sub[k][0].append(d); sub[k][1].append(vt)
tbl = {}
nulls = {}
for k, (dl, vl) in sub.items():
    ok, tot = rate(dl, vl)
    cnt_off = collections.Counter(o for vt in vl for o in [off_of(vt)] if o is not None)
    cnt_d = collections.Counter(dl)
    nv = sum(cnt_off.values()); nd = sum(cnt_d.values())
    null = sum((cnt_off[d] / nv) * (cnt_d[d] / nd) for d in set(cnt_off) | set(cnt_d))
    nulls[k] = round(null, 4)
    tbl[k] = {'sites': len(dl), 'hits': ok, 'rate': round(ok / tot, 4) if tot else None,
              'null_site_level': nulls[k], 'lift': round((ok / tot) / null, 2) if tot and null else None}

res = {
 'exe_sha256': hashlib.sha256(B.data).hexdigest(), 'exe_bytes': B.N,
 'sites': N, 'rate_real': [okR, totR, round(okR / totR, 6)],
 'global_perm': perms, 'global_perm_mean': round(pm, 6),
 'global_perm_identical': all(abs(p[2] - round(okR / totR, 6)) < 1e-9 for p in perms),
 'lift_real_over_perm': round((okR / totR) / pm, 3),
 'stratified': tbl,
 'elapsed_s': round(time.time() - T0, 1),
}
POS = []
def chk(n, c, v): POS.append([n, bool(c), v])
chk('全局置换 5 次的结果不完全相同（与桶内置换的关键区别）', not res['global_perm_identical'], [p[2] for p in perms])
chk('全局置换均值 < 0.60（远离实测 0.9231）', pm < 0.60, round(pm, 4))
chk('实测一致率是全局置换基线的 1.5 倍以上', (okR / totR) / pm > 1.5, res['lift_real_over_perm'])
chk('小位移组 lift 在 2.5..5（S-307：我原断言 >10 是抄错了 R144C 的总体 lift）', 2.5 < tbl['small']['lift'] < 5, tbl['small']['lift'])
chk('大位移组 lift > 10', tbl['large']['lift'] > 10, tbl['large']['lift'])
chk('disp=0 桶的 lift 恒等于 1.0（单桶时零模型 == 实测，结构上零信息）', abs(tbl['d0']['lift'] - 1.0) < 1e-9, tbl['d0']['lift'])
res['POS'] = POS
res['pos_pass'] = sum(1 for x in POS if x[1]); res['pos_fail'] = sum(1 for x in POS if not x[1])
json.dump(res, open('_r144/r144i_global_perm.json', 'w'), indent=1)
print(json.dumps(res, indent=1, ensure_ascii=False)[:3000])
print('\n'.join('%-58s %s %s' % (p[0], p[1], p[2]) for p in POS))
print('POS %d/%d FAIL %d' % (res['pos_pass'], len(POS), res['pos_fail']))
