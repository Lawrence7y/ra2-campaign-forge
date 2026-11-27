#!/usr/bin/env python3
"""R144 B：用 RTTI 的 COL.offset 字段判定「disp≠0 装表」是不是多重继承子对象 vptr。

假说 H：MSVC 多重继承下，第 k 个子对象的虚表指针装在对象偏移 k 处，
        而该虚表的 CompleteObjectLocator 的 offset 字段（COL+4）恰等于 k。
判据（可失败）：对每个装表站点 (vt, disp)，断言 COL(vt)+4 == disp。
反控：
  A 置换检验：把站点与虚表随机错配（同 disp 内置换），一致率必须塌到基线；
  B 位移=-4/+4 反控：把站点 disp 全部 +4，一致率必须大幅下降；
  C 若 H 成立，则同 TD（同一类型）的多张虚表应分别是 offset 0/k1/k2，
    且其中 offset 0 的那张（主虚表）应被 F1（disp=0）覆盖。
"""
import sys, re, json, struct, collections, random, hashlib, time
sys.path.insert(0, '_r143')
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
import r143lib as L

T0 = time.time()
B = L.Bin(); md = Cs(CS_ARCH_X86, CS_MODE_32)
TDs, COL, VTS = B.vtset()
GEN = L.GEN

# COL 结构：+0 sig, +4 offset, +8 cdOffset, +12 pTypeDescriptor, +16 pClassDescriptor
COLof = {}      # vt -> col base
for vt in VTS:
    c = B.dw(vt - 4)
    if c in COL: COLof[vt] = c
coloff = {c: B.dw(c + 4) for c in COL}
coltd = {c: B.dw(c + 12) for c in COL}
vtinfo = {vt: (COLof.get(vt), coloff.get(COLof.get(vt)), coltd.get(COLof.get(vt))) for vt in VTS}

def immv(t): return (int(t, 16) if t.startswith('0x') else int(t)) & 0xFFFFFFFF

RE_IDX = re.compile(r'^dword ptr \[([a-z0-9]+)(?:[+-]0x[0-9a-f]+)?\+([a-z0-9]+)\*4(?:[+-]0x[0-9a-f]+)?\]$')

sites = []      # (va, base, disp, vt)
idxstore = []   # (va, vt, raw)
for a, sz, mn, op in B.sweep(md):
    if not op: continue
    m = L.RE_STORE.match(op)
    if m:
        base = m.group(1); ds = L.disp_of(m.group(2)); tgt = m.group(3)
        if tgt is not None and L.RE_IMM.match(tgt):
            iv = immv(tgt)
            if iv in VTS and base in GEN:
                sites.append((a, base, ds, iv))
        continue
    mi = RE_IDX.match(op)
    if mi:
        tgt = op.partition(',')[2]
        if L.RE_IMM.match(tgt):
            iv = immv(tgt)
            if iv in VTS: idxstore.append((a, iv, op))

def agree(pairs):
    ok = tot = 0
    for vt, disp in pairs:
        off = vtinfo.get(vt, (None, None, None))[1]
        if off is None: continue
        tot += 1; ok += (off == disp)
    return ok, tot

real = [(s[3], s[2]) for s in sites]
okr, totr = agree(real)

# 分组：按 TD
by_td = collections.defaultdict(list)
for vt, (c, off, td) in vtinfo.items():
    if td is not None: by_td[td].append((vt, off))
multi = {td: v for td, v in by_td.items() if len(v) > 1}

f1vt = {s[3] for s in sites if s[2] == 0}
covF1 = f1vt
uncovered = sorted(VTS - covF1)
# uncovered 的 TD 是否已有主虚表被覆盖
unc_td_twin = 0; unc_detail = []
for vt in uncovered:
    c, off, td = vtinfo[vt]
    twins = [x for x, o in by_td.get(td, []) if x != vt]
    hit = [x for x in twins if x in covF1]
    if hit: unc_td_twin += 1
    if len(unc_detail) < 12:
        unc_detail.append([hex(vt), off, hex(td) if td else None, [hex(x) for x in hit[:3]]])

# 反控 A：同 disp 内置换虚表
random.seed(144)
pairsA = []
sites_by_disp = collections.defaultdict(list)
for s in sites: sites_by_disp[s[2]].append(s[3])
for d, vs in sites_by_disp.items():
    sh = vs[:]; random.shuffle(sh)
    pairsA += list(zip(sh, [d] * len(sh)))
okA, totA = agree(pairsA)
# 反控 B：disp+4
okB, totB = agree([(vt, disp + 4) for vt, disp in real])
# 反控 C：只取 disp==0 站点上的一致性应恒真（offset==0）— 这是恒等式的旁证
okC, totC = agree([(vt, d) for vt, d in real if d == 0])

# 按 offset 分布
offhist = collections.Counter(o for _, o, _ in vtinfo.values())
multi_offsets = collections.Counter(o for td, v in multi.items() for _, o in v)

res = {
 'exe_sha256': hashlib.sha256(B.data).hexdigest(), 'exe_bytes': B.N,
 'vt_distinct': len(VTS), 'td': len(TDs), 'col': len(COL),
 'sites_all': len(sites),
 'sites_disp0': sum(1 for s in sites if s[2] == 0),
 'idxstore_sites': len(idxstore), 'idxstore_sample': [[hex(a), hex(v), op] for a, v, op in idxstore[:12]],
 'col_offset_hist': dict(sorted(offhist.items(), key=lambda kv: -kv[1])[:12]),
 'td_multi_n': len(multi), 'td_multi_offsets': dict(sorted(multi_offsets.items(), key=lambda kv: -kv[1])[:12]),
 'agree_real': [okr, totr], 'agree_rate': round(okr / totr, 4) if totr else None,
 'agree_permuted': [okA, totA], 'agree_permuted_rate': round(okA / totA, 4) if totA else None,
 'agree_disp_plus4': [okB, totB], 'agree_disp_plus4_rate': round(okB / totB, 4) if totB else None,
 'agree_disp0_only': [okC, totC],
 'uncovered_n': len(uncovered), 'uncovered_with_covered_td_twin': unc_td_twin,
 'uncovered_detail': unc_detail,
 'per_disp_agree': {},
 'elapsed_s': round(time.time() - T0, 1),
}
for d in sorted({s[2] for s in sites}):
    sub = [(vt, d) for vt, dd in real if dd == d]
    ok, tot = agree(sub)
    res['per_disp_agree'][str(d)] = [ok, tot, round(ok / tot, 4) if tot else None]

POS, NEG = [], []
def chk(n, c, v): POS.append([n, bool(c), v])
chk('站点总数 = disp0 2741 + 其余（与 R143 F1 一致）', res['sites_disp0'] == 2741, res['sites_disp0'])
chk('实测一致率 >= 90%（COL.offset 与装表位移相符）', res['agree_rate'] >= 0.90, res['agree_rate'])
chk('置换反控一致率 < 30%（远低于实测）', (res['agree_permuted_rate'] or 0) < 0.30, res['agree_permuted_rate'])
chk('位移 +4 反控一致率 < 90%（明显下降）', (res['agree_disp_plus4_rate'] or 0) < 0.90, res['agree_disp_plus4_rate'])
chk('disp=0 子集上一致率恒为 1（COL.offset 全 0 结构）', totC and okC == totC, [okC, totC])
chk('存在同一 TD 下多张虚表（多重继承结构）', len(multi) > 100, len(multi))
chk('未覆盖虚表绝大多数有「同 TD 且已覆盖」的孪生', unc_td_twin >= 0.9 * len(uncovered), [unc_td_twin, len(uncovered)])
chk('存在基址+索引的数组式装表站点', len(idxstore) > 0, len(idxstore))
res['POS'] = POS; res['NEG'] = NEG
res['pos_pass'] = sum(1 for x in POS if x[1]); res['pos_fail'] = sum(1 for x in POS if not x[1])
res['neg_pass'] = 0; res['neg_fail'] = 0
json.dump(res, open('_r144/r144b_col_offset.json', 'w'), indent=1)
print(json.dumps({k: v for k, v in res.items() if k not in ('POS', 'NEG', 'uncovered_detail')}, indent=1, ensure_ascii=False)[:5000])
print('detail', json.dumps(res['uncovered_detail'], ensure_ascii=False))
print('\n'.join('%-72s %s %s' % (p[0], p[1], p[2]) for p in POS))
print('POS %d/%d FAIL %d' % (res['pos_pass'], len(POS), res['pos_fail']))
