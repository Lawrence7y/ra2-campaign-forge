#!/usr/bin/env python3
"""R144 D：disp≠0 装表群体的分层 + 三条待定项的定性。

上一步（r144c）得到的净结论：整体一致率 0.9231 是 disp=0 桶撑起来的（0.9839 × 2741），
只有在 disp≠0 子集上才看得出信号：1038/1305 = 0.7954，独立性零模型 0.0542（14.7 倍）。
本脚本回答三个剩余问题：
  Q1 disp≠0 内部是不是双峰：小位移 {4,8,12}（多重继承子对象）与其它（成员数组槽）——
     一致率、不匹配站点落在哪一侧；
  Q2 F6（.data 里值等于虚表地址的 dword）990 处却只有 3 个 distinct vt —— 是哪三张、
     这些 dword 落在什么结构里；
  Q3 被 RE_STORE 排除的「索引式」内存写（[reg+idx*4+disp]）里，是否存在
     「寄存器搬运装表」（F5 的索引版）——若有，F5 的召回偏低要写明。
"""
import sys, json, collections, hashlib, time
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
off_of = lambda vt: coloff.get(COLof.get(vt))
td_of = lambda vt: coltd.get(COLof.get(vt))
def immv(t): return (int(t, 16) if t.startswith('0x') else int(t)) & 0xFFFFFFFF

RE_IDX = __import__('re').compile(r'^dword ptr \[([a-z0-9]+)(?:[+-]0x[0-9a-f]+)?\+([a-z0-9]+)\*([48])([+-]0x[0-9a-f]+)?\]$')

sites = []
idx_stores = []      # (va, op, tgtreg)
idx_imm = []         # 索引式且来源是立即数
pendv = {}
allops = []
for a, sz, mn, op in B.sweep(md):
    allops.append((a, mn, op))
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
            if iv in VTS: idx_imm.append((a, op, hex(iv)))
        elif tgt in GEN:
            idx_stores.append((a, op, tgt))

# Q1 分层
bucket = lambda d: 'small' if d in (4, 8, 12) else 'large'
strat = collections.defaultdict(lambda: [0, 0, 0])   # key -> [sites, agree, distinct_vt]
for a, base, d, vt in sites:
    if d == 0: continue
    k = bucket(d)
    strat[k][0] += 1
    strat[k][1] += (off_of(vt) == d)
    strat[k][2] += 1
distinct_by = collections.defaultdict(set)
for a, base, d, vt in sites:
    if d != 0: distinct_by[bucket(d)].add(vt)
mismatch = [(a, base, d, vt, off_of(vt)) for a, base, d, vt in sites if d != 0 and off_of(vt) != d]
mm_small = sum(1 for x in mismatch if bucket(x[2]) == 'small')
mm_large = len(mismatch) - mm_small
mm_by_disp = collections.Counter(x[2] for x in mismatch).most_common(8)

# Q2 F6
data_init = []
for nm, ava, vs, raw, rs in B.secs:
    if nm in ('.data', '.rdata'):
        blob = B.data[raw:raw + rs]
        for i in range(len(blob) // 4):
            v = __import__('struct').unpack_from('<I', blob, i * 4)[0]
            if v in VTS: data_init.append((B.IB + ava + i * 4, v))
f6_vt = collections.Counter(v for _, v in data_init)
f6_detail = []
for vt, n in f6_vt.most_common(6):
    addrs = sorted(a for a, v in data_init if v == vt)
    f6_detail.append([hex(vt), n, off_of(vt), hex(td_of(vt)) if td_of(vt) else None,
                      [hex(a) for a in addrs[:6]],
                      B.sec_of(addrs[0]), B.sec_of(addrs[-1])])
f6_gap = collections.Counter()
# 同一 vt 的多个出现位置是否相邻（步长直方图）
for vt, n in f6_vt.most_common(1):
    addrs = sorted(a for a, v in data_init if v == vt)
    f6_gap = collections.Counter(addrs[i + 1] - addrs[i] for i in range(len(addrs) - 1)).most_common(6)

# Q3 索引式寄存器搬运
idx_reg_hit = 0
idx_reg_sample = []
seen = {}
for a, mn, op in allops:
    ml = None
    if mn == 'mov':
        import re as _re
        ml = _re.match(r'^([a-z0-9]+),(0x[0-9a-f]+)$', op or '')
        if ml and ml.group(1) in GEN:
            v = immv(ml.group(2))
            if v in VTS: seen[ml.group(1)] = v
    mi = RE_IDX.match(op or '')
    if mi:
        tgt = (op or '').partition(',')[2]
        if tgt in seen:
            idx_reg_hit += 1
            if len(idx_reg_sample) < 8: idx_reg_sample.append([hex(a), op, hex(seen[tgt])])

def r(ok, tot): return [ok, tot, round(ok / tot, 4) if tot else None]

res = {
 'exe_sha256': hashlib.sha256(B.data).hexdigest(), 'exe_bytes': B.N,
 'sites_nonzero': sum(1 for s in sites if s[2] != 0),
 'strat': {k: r(v[1], v[0]) for k, v in strat.items()},
 'strat_distinct': {k: len(v) for k, v in distinct_by.items()},
 'mismatch_n': len(mismatch), 'mismatch_small': mm_small, 'mismatch_large': mm_large,
 'mismatch_by_disp': mm_by_disp,
 'mismatch_sample': [[hex(a), base, d, hex(vt), o] for a, base, d, vt, o in mismatch[:10]],
 'f6_distinct': len(f6_vt), 'f6_detail': f6_detail, 'f6_gap_top': f6_gap,
 'idx_store_total': len(idx_stores), 'idx_imm_total': len(idx_imm),
 'idx_imm_sample': idx_imm[:6],
 'idx_reg_stream_hits': idx_reg_hit, 'idx_reg_sample': idx_reg_sample,
 'elapsed_s': round(time.time() - T0, 1),
}
POS = []
def chk(n, c, v): POS.append([n, bool(c), v])
sm, lg = res['strat']['small'], res['strat']['large']
chk('小位移 {4,8,12} 的一致率 > 0.95', sm[2] > 0.95, sm)
chk('大位移一致率 < 0.2（成员数组槽，与 COL.offset 无关）', (lg[2] or 0) < 0.2, lg)
chk('不匹配站点绝大多数落在「大位移」侧', mm_large > mm_small, [mm_large, mm_small])
chk('F6 distinct 虚表数 <= 5 且出现次数 >= 100', len(f6_vt) <= 5 and max(f6_vt.values()) >= 100, [len(f6_vt), max(f6_vt.values()) if f6_vt else None])
chk('索引式且来源为立即数的装表站点为 0（R143 正则排除这些不影响 imm 形态结论）', len(idx_imm) == 0, len(idx_imm))
chk('索引式寄存器搬运命中数很小（不作为覆盖来源）', idx_reg_hit < 50, idx_reg_hit)
res['POS'] = POS
res['pos_pass'] = sum(1 for x in POS if x[1]); res['pos_fail'] = sum(1 for x in POS if not x[1])
json.dump(res, open('_r144/r144d_strat.json', 'w'), indent=1)
print(json.dumps(res, indent=1, ensure_ascii=False)[:5000])
print('\n'.join('%-64s %s %s' % (p[0], p[1], p[2]) for p in POS))
print('POS %d/%d FAIL %d' % (res['pos_pass'], len(POS), res['pos_fail']))
