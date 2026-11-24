# -*- coding: utf-8 -*-
# _sg_probe_shift.py —— 第二轮候选：「部分去相关」类实现错误 + 证伪量化
# 只读语料（safe_open 校验防路径穿越）；写域 = lead/s604_script_gap_20261109/。零真机、零采样代码。
# 候选：
#   C8a/C8b  gap 挂到时间后继/前继帧（off-by-one 挂接；时长列仍 edge 三分）
#   C9       分组宽度网格：fast=ids[:a] / slow=ids[n-b:]，检验稀释类能否给出负 diff
#   C10      中位算子偶数处理量化：upper/lower median 与 median 的最大偏差（证伪用）
#   C11      k±1 边界 off-by-one 量化（证伪用）
#   C12      maxgap 时间序 lag-1 自相关 + C8 残差耦合度量
import json, statistics, math, os

BASE = os.path.normpath('D:/Project/ra2-campaign-forge')
CORPUS_REL = ('out', 're_work', 'work_chain', 'CONTINUE_20261003', 'lead', 'qc161_u0400_trip')
OUT_REL = ('lead', 's604_script_gap_20261109', '_sg_probe_shift_out.txt')

TRIPS = ['l1c_20261021', 'l1d_20261021', 'l1e_20261021', 'l3_20261021', 't55k_20261020']
WINDOWS = [(t, w) for t in TRIPS for w in (0, 1, 2)]
TABLE = {
    ('l1c_20261021', 0): (65.8, 2.70, 147.9, 2.73,  0.032),
    ('l1c_20261021', 1): (64.3, 2.68, 154.8, 2.71,  0.028),
    ('l1c_20261021', 2): (62.8, 2.67, 138.3, 2.70,  0.030),
    ('l1d_20261021', 0): (60.2, 2.66, 132.0, 2.71,  0.049),
    ('l1d_20261021', 1): (58.1, 2.65, 136.1, 2.67,  0.022),
    ('l1d_20261021', 2): (39.9, 2.64,  99.3, 2.66,  0.025),
    ('l1e_20261021', 0): (55.1, 2.65, 116.4, 2.65,  0.003),
    ('l1e_20261021', 1): (52.8, 2.63, 115.6, 2.66,  0.035),
    ('l1e_20261021', 2): (39.9, 2.63,  97.8, 2.64,  0.018),
    ('l3_20261021',  0): (73.2, 2.75, 156.6, 2.75, -0.002),
    ('l3_20261021',  1): (50.1, 2.68, 117.5, 2.72,  0.037),
    ('l3_20261021',  2): (62.3, 271e-2, 134.9, 2.71,  0.002),
    ('t55k_20261020', 0): (28.9, 2.62,  35.2, 2.60, -0.013),
    ('t55k_20261020', 1): (29.6, 2.61,  34.9, 2.60, -0.006),
    ('t55k_20261020', 2): (29.6, 2.61,  34.8, 2.61, -0.0),
}

def safe_open(rel_parts, mode='rb', **kw):
    rp = os.path.normpath(os.path.abspath(os.path.join(BASE, *rel_parts)))
    if not (rp == BASE or rp.startswith(BASE + os.sep)):
        raise PermissionError('path outside BASE: ' + rp)
    return open(rp, mode, **kw)

out_lines = []
def P(s=''):
    out_lines.append(s)
    print(s)

def med(v):
    return statistics.median(v)

def upper_med(v):
    s = sorted(v); n = len(s)
    return s[n // 2] if n % 2 == 0 else s[(n - 1) // 2]

def lower_med(v):
    s = sorted(v); n = len(s)
    return s[(n - 1) // 2] if n % 2 == 0 else s[n // 2]

def main():
    per = {}
    for trip, w in WINDOWS:
        with safe_open(list(CORPUS_REL) + [trip, 'measure_w%d.json' % w]) as fh:
            d = json.loads(fh.read().decode('utf-8'))
        edges = d['frame_edges']
        groups = {}
        for fi, ti in zip(d['samples']['f'], d['samples']['t']):
            groups.setdefault(fi, []).append(ti)
        fids = [e[0] for e in edges]
        et = {e[0]: e[1] for e in edges}
        dur = {}
        mg = {}
        for i, fid in enumerate(fids):
            ts = sorted(groups.get(fid, []))
            if len(ts) >= 2:
                mg[fid] = max(ts[j + 1] - ts[j] for j in range(len(ts) - 1))
            if i + 1 < len(fids):
                dur[fid] = et[fids[i + 1]] - et[fid]
        per[(trip, w)] = dict(fids=fids, dur=dur, mg=mg, n=len(fids))

    def thirds_ids(r):
        ids = sorted([f for f in r['fids'] if f in r['dur'] and f in r['mg']],
                     key=lambda x: (r['dur'][x], x))
        k = len(ids) // 3
        return ids, k

    def evaluate(tag, fgf, sgf):
        gh = rh = dh = rdh = 0
        pos_dfg = neg_dsg = negdiff = 0
        devs = []
        for key in WINDOWS:
            td = TABLE[key]
            fg = fgf(key) * 1000.0
            sg = sgf(key) * 1000.0
            diff = sg - fg
            gh += abs(fg - td[1]) < 0.005
            gh += abs(sg - td[3]) < 0.005
            rh += round(fg, 2) == td[1]
            rh += round(sg, 2) == td[3]
            dh += abs(diff - td[4]) < 0.0005
            rdh += round(diff, 3) == td[4]
            pos_dfg += (td[1] - fg) > 0
            neg_dsg += (td[3] - sg) < 0
            negdiff += diff < 0
            devs.append(diff)
        P('  %-22s | 容差gap %2d/30 diff %2d/15 | round gap %2d/30 diff %2d/15 | Δfg>0:%2d Δsg<0:%2d 负diff:%2d | diff中位 %s'
          % (tag, gh, dh, rh, rdh, pos_dfg, neg_dsg, negdiff,
             ('+' if med(devs) >= 0 else '-') + '%.4f' % abs(med(devs))))

    P('[C8] 时间序错位挂接（gap 挂时间相邻帧；时长列仍 edge 三分）')
    mg_fwd = {}
    mg_bwd = {}
    for key in WINDOWS:
        r = per[key]
        tids = [f for f in r['fids'] if f in r['mg']]
        fwd = {}
        bwd = {}
        for i in range(len(tids) - 1):
            fwd[tids[i]] = r['mg'][tids[i + 1]]
            bwd[tids[i + 1]] = r['mg'][tids[i]]
        fwd[tids[-1]] = r['mg'][tids[-1]]
        bwd[tids[0]] = r['mg'][tids[0]]
        mg_fwd[key] = fwd
        mg_bwd[key] = bwd

    def c8(key, m):
        ids, k = thirds_ids(per[key])
        n = len(ids)
        return med([m[i] for i in ids[:k]]), med([m[i] for i in ids[n - k:]])

    evaluate('C8a 挂时间后继',
             lambda k: c8(k, mg_fwd[k])[0],
             lambda k: c8(k, mg_fwd[k])[1])
    evaluate('C8b 挂时间前继',
             lambda k: c8(k, mg_bwd[k])[0],
             lambda k: c8(k, mg_bwd[k])[1])
    P('')

    P('[C9] 分组宽度网格（fast=前a / slow=后b；时长列仍三分）——稀释类能否给负 diff')
    grid = [('(k3,k3)', lambda n: n // 3, lambda n: n // 3),
            ('(k2,k2)', lambda n: n // 2, lambda n: n // 2),
            ('(2k3,2k3)', lambda n: 2 * (n // 3), lambda n: 2 * (n // 3)),
            ('(k3,k2)', lambda n: n // 3, lambda n: n // 2),
            ('(k2,k3)', lambda n: n // 2, lambda n: n // 3),
            ('(k2,2k3)', lambda n: n // 2, lambda n: 2 * (n // 3)),
            ('(2k3,k2)', lambda n: 2 * (n // 3), lambda n: n // 2),
            ('(5k6,5k6)', lambda n: 5 * n // 6, lambda n: 5 * n // 6)]
    for tag, fa, fb in grid:
        def fgf(key, fa=fa):
            r = per[key]
            ids, _ = thirds_ids(r)
            a = min(fa(len(ids)), len(ids))
            return med([r['mg'][i] for i in ids[:a]])
        def sgf(key, fb=fb):
            r = per[key]
            ids, _ = thirds_ids(r)
            b = min(fb(len(ids)), len(ids))
            return med([r['mg'][i] for i in ids[len(ids) - b:]])
        evaluate('C9 ' + tag, fgf, sgf)
    P('')

    P('[C9d] 逐窗 diff：(k2,k2) 与 (2k3,2k3)（负 diff 存在性检验）')
    for tag, fa, fb in (('(k2,k2)', lambda n: n // 2, lambda n: n // 2),
                        ('(2k3,2k3)', lambda n: 2 * (n // 3), lambda n: 2 * (n // 3))):
        ds = []
        for key in WINDOWS:
            r = per[key]
            ids, _ = thirds_ids(r)
            n = len(ids)
            a = min(fa(n), n)
            b = min(fb(n), n)
            fg = med([r['mg'][i] for i in ids[:a]]) * 1000.0
            sg = med([r['mg'][i] for i in ids[n - b:]]) * 1000.0
            ds.append(sg - fg)
        P('  %-10s diffs: %s  负窗=%d'
          % (tag, ' '.join(('+' if x >= 0 else '-') + '%.4f' % abs(x) for x in ds),
             sum(1 for x in ds if x < 0)))
    P('')

    P('[C10] 中位算子偶数处理量化（|Δ| 量级 vs 需要 0.05 级）')
    mx_u = 0.0
    mx_l = 0.0
    for key in WINDOWS:
        r = per[key]
        ids, k = thirds_ids(r)
        n = len(ids)
        fq = [r['mg'][i] for i in ids[:k]]
        sq = [r['mg'][i] for i in ids[n - k:]]
        for lst in (fq, sq):
            mx_u = max(mx_u, abs(upper_med(lst) - med(lst)))
            mx_l = max(mx_l, abs(lower_med(lst) - med(lst)))
    P('  max|upper−median| = %.4f ms   max|lower−median| = %.4f ms' % (mx_u * 1000.0, mx_l * 1000.0))
    P('')

    P('[C11] k±1 边界 off-by-one 量化')
    mx_p = 0.0
    mx_m = 0.0
    for key in WINDOWS:
        r = per[key]
        ids, k = thirds_ids(r)
        n = len(ids)
        for kk, tag in ((k + 1, '+1'), (max(k - 1, 1), '-1')):
            d1 = abs(med([r['mg'][i] for i in ids[:kk]]) - med([r['mg'][i] for i in ids[:k]]))
            d2 = abs(med([r['mg'][i] for i in ids[n - kk:]]) - med([r['mg'][i] for i in ids[n - k:]]))
            if tag == '+1':
                mx_p = max(mx_p, d1, d2)
            else:
                mx_m = max(mx_m, d1, d2)
    P('  max|k+1 − k| = %.4f ms   max|k−1 − k| = %.4f ms' % (mx_p * 1000.0, mx_m * 1000.0))
    P('')

    P('[C12] maxgap 时间序 lag-1 自相关 + 各候选 diff 逐窗对照')
    P('  window            | lag1acf | 真值diff | C8a diff | C8b diff | 台账diff')
    for key in WINDOWS:
        r = per[key]
        tids = [f for f in r['fids'] if f in r['mg']]
        gs = [r['mg'][f] for f in tids]
        mg_mean = sum(gs) / len(gs)
        num = sum((gs[i] - mg_mean) * (gs[i + 1] - mg_mean) for i in range(len(gs) - 1))
        den = sum((g - mg_mean) ** 2 for g in gs)
        acf = num / den if den else float('nan')
        ids, k = thirds_ids(r)
        n = len(ids)
        td = TABLE[key]
        c8a_d = (med([mg_fwd[key][i] for i in ids[n - k:]]) - med([mg_fwd[key][i] for i in ids[:k]])) * 1000.0
        c8b_d = (med([mg_bwd[key][i] for i in ids[n - k:]]) - med([mg_bwd[key][i] for i in ids[:k]])) * 1000.0
        trued = (med([r['mg'][i] for i in ids[n - k:]]) - med([r['mg'][i] for i in ids[:k]])) * 1000.0
        P('  %-16s | %+.3f | %s | %s | %s | %+7.3f'
          % (key[0] + '/w' + str(key[1]), acf,
             ('+' if trued >= 0 else '-') + '%.4f' % abs(trued),
             ('+' if c8a_d >= 0 else '-') + '%.4f' % abs(c8a_d),
             ('+' if c8b_d >= 0 else '-') + '%.4f' % abs(c8b_d), td[4]))
    P('')
    P('[_sg_probe_shift] END')

    with safe_open(OUT_REL, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(out_lines) + '\n')
    print('WRITTEN: ' + os.path.join(BASE, *OUT_REL))

if __name__ == '__main__':
    main()
