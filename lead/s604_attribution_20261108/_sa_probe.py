# -*- coding: utf-8 -*-
# _sa_probe.py —— 归因裁定员辅助探针（只读语料与台账常量；写域 = lead/s604_attribution_20261108/）
# 目的：
#   [L]  独立复算 S604 §2 双锚点（l1c/w0 med_edge/med_span，对台账 :9613/:9535）
#   [S]  主口径（edge+k=n//3+maxgap+median）逐窗重算，给逐窗偏离方向/偏离量
#   [VAR] 「三分法(k) × 空档定义 × 中位/均值算子 × 分组键」变体扫描：能否命中台账空档列/空档差列
#   [INT] 台账表内「空档差列 vs 自家两空档列之差」的算术自洽性
# 纪律：零真机、零采样代码（只读静态 JSON）；保护区只读；不 commit、不 push。
import json, math, statistics, hashlib, os, io, sys

BASE = os.path.normpath(os.path.abspath('D:/Project/ra2-campaign-forge'))
CORPUS_REL = ('out', 're_work', 'work_chain', 'CONTINUE_20261003', 'lead', 'qc161_u0400_trip')
OUT_REL = ('lead', 's604_attribution_20261108', '_sa_probe_out.txt')
GOAL_REL = ('lead', 'GOAL_THREE_TARGETS_20261018.md')

def safe_open(rel_parts, mode='rb', **kw):
    """规范化并校验路径必须落在 BASE 内（Mimosa 建议：禁止路径穿越）。"""
    rp = os.path.normpath(os.path.abspath(os.path.join(BASE, *rel_parts)))
    if not (rp == BASE or rp.startswith(BASE + os.sep)):
        raise PermissionError('path outside BASE: ' + rp)
    return open(rp, mode, **kw)

def f3(x):
    return ('+' if x >= 0 else '-') + ('%.4f' % abs(x))

TRIPS = ['l1c_20261021', 'l1d_20261021', 'l1e_20261021', 'l3_20261021', 't55k_20261020']
WINDOWS = [(t, w) for t in TRIPS for w in (0, 1, 2)]

# 台账 :9706-9720 表值（快dur, 快gap, 慢dur, 慢gap, diff）——本人实读台账 :9706-9720 录入
TABLE = {
    ('l1c_20261021', 0): (65.8, 2.70, 147.9, 2.73, 0.032),
    ('l1c_20261021', 1): (64.3, 2.68, 154.8, 2.71, 0.028),
    ('l1c_20261021', 2): (62.8, 2.67, 138.3, 2.70, 0.030),
    ('l1d_20261021', 0): (60.2, 2.66, 132.0, 2.71, 0.049),
    ('l1d_20261021', 1): (58.1, 2.65, 136.1, 2.67, 0.022),
    ('l1d_20261021', 2): (39.9, 2.64, 99.3, 2.66, 0.025),
    ('l1e_20261021', 0): (55.1, 2.65, 116.4, 2.65, 0.003),
    ('l1e_20261021', 1): (52.8, 2.63, 115.6, 2.66, 0.035),
    ('l1e_20261021', 2): (39.9, 2.63, 97.8, 2.64, 0.018),
    ('l3_20261021', 0): (73.2, 2.75, 156.6, 2.75, -0.002),
    ('l3_20261021', 1): (50.1, 2.68, 117.5, 2.72, 0.037),
    ('l3_20261021', 2): (62.3, 2.71, 134.9, 2.71, 0.002),
    ('t55k_20261020', 0): (28.9, 2.62, 35.2, 2.6, -0.013),
    ('t55k_20261020', 1): (29.6, 2.61, 34.9, 2.6, -0.006),
    ('t55k_20261020', 2): (29.6, 2.61, 34.8, 2.61, -0.0),
}

out_lines = []
def P(s=''):
    out_lines.append(s)
    print(s)

def gap_maps(ts_list):
    """帧内空档四种定义（gaps 升序）"""
    gaps = sorted(ts_list[j + 1] - ts_list[j] for j in range(len(ts_list) - 1))
    return {
        'maxgap': gaps[-1],
        'excl_first': gaps[-1] if len(gaps) == 1 else max(gaps[1:]),
        'excl_last': gaps[-1] if len(gaps) == 1 else max(gaps[:-1]),
        'gap2': gaps[-2] if len(gaps) >= 2 else gaps[-1],
    }

def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

    # —— 语料装载 ——
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
        dur_edge = {}
        gm = {g: {} for g in ('maxgap', 'excl_first', 'excl_last', 'gap2')}
        for i, fid in enumerate(fids):
            ts = groups.get(fid, [])
            if len(ts) >= 2:
                m = gap_maps(ts)
                for g in gm:
                    gm[g][fid] = m[g]
            if i + 1 < len(fids):
                dur_edge[fid] = et[fids[i + 1]] - et[fid]
        per[(trip, w)] = (fids, dur_edge, gm)

    def kpick(n, rule):
        return {'floor3': n // 3, 'ceil3': math.ceil(n / 3), 'floor2': n // 2,
                'ceil2': math.ceil(n / 2), 'floor4': n // 4, 'ceil4': math.ceil(n / 4),
                'floor10': n // 10}[rule]

    def run_variant(krule, gname, op, gap_sorted):
        fg_l, sg_l, d_l = [], [], []
        for key in WINDOWS:
            fids, dur_edge, gm = per[key]
            gmap = gm[gname]
            ids = [fid for fid in fids if dur_edge.get(fid) is not None and fid in gmap]
            keyf = (lambda x: (gmap[x], x)) if gap_sorted else (lambda x: (dur_edge[x], x))
            ids = sorted(ids, key=keyf)
            n = len(ids)
            k = kpick(n, krule)
            fast, slow = ids[:k], ids[n - k:]
            agg = statistics.median if op == 'median' else statistics.mean
            fg = agg([gmap[i] for i in fast]) * 1000.0
            sg = agg([gmap[i] for i in slow]) * 1000.0
            fg_l.append(fg); sg_l.append(sg); d_l.append(sg - fg)
        return fg_l, sg_l, d_l

    # —— [L] 双锚点独立复算（l1c/w0）——
    with safe_open(list(CORPUS_REL) + ['l1c_20261021', 'measure_w0.json']) as fh:
        d = json.loads(fh.read().decode('utf-8'))
    edges = d['frame_edges']
    groups = {}
    for fi, ti in zip(d['samples']['f'], d['samples']['t']):
        groups.setdefault(fi, []).append(ti)
    fids = [e[0] for e in edges]
    et = {e[0]: e[1] for e in edges}
    de = [et[fids[i + 1]] - et[fids[i]] for i in range(len(fids) - 1)]
    dsp = [max(groups[f]) - min(groups[f]) for f in fids if f in groups]
    P('[L] 双锚点独立复算：l1c_20261021/w0 全帧中位（对台账 :9613/:9535）')
    P('  med_edge_all = %.4f ms   med_span_all = %.4f ms   n_frames = %d'
      % (statistics.median(de) * 1000, statistics.median(dsp) * 1000, len(fids)))
    P('  台账 :9613 该行 = 「l1c_20261021/w0  103.2  230  100.8  2.7 …」；:9535 = 「… 100.8 ms …」')
    P('')

    # —— [S] 主口径逐窗重算 + 偏离方向 ——
    P('[S] 主口径（edge + k=n//3 + maxgap + median）逐窗重算 vs 台账（Δ = 台账 − 复算）')
    main_diff = []
    P('  window            | 复算 fg/sg/diff               | 台账 fg/sg/diff         | Δfg      Δsg      Δdiff    | 方向')
    for key in WINDOWS:
        fids, dur_edge, gm = per[key]
        gmap = gm['maxgap']
        ids = sorted([fid for fid in fids if dur_edge.get(fid) is not None and fid in gmap],
                     key=lambda x: (dur_edge[x], x))
        k = len(ids) // 3
        fast, slow = ids[:k], ids[len(ids) - k:]
        fg = statistics.median([gmap[i] for i in fast]) * 1000.0
        sg = statistics.median([gmap[i] for i in slow]) * 1000.0
        diff = sg - fg
        main_diff.append(diff)
        td = TABLE[key]
        if td[4] > 0 and diff > 0:
            direction = '同号(复算更大)' if diff > td[4] else '同号(复算更小)'
        elif td[4] < 0 and diff > 0:
            direction = '符号相反'
        elif td[4] == 0 or diff == 0:
            direction = '零值vs非零'
        else:
            direction = '同号(复算更小)'
        P('  %-16s | %6.4f %6.4f %s | %5.2f %5.2f %+7.3f | %8.4f %8.4f %8.4f | %s'
          % (key[0] + '/w' + str(key[1]), fg, sg, f3(diff), td[1], td[3], td[4],
             td[1] - fg, td[3] - sg, td[4] - diff, direction))
    dev = [main_diff[i] - TABLE[key][4] for i, key in enumerate(WINDOWS)]
    P('  复算 diff 高于台账 diff 的窗数 = %d/15；复算−台账 diff：中位 %s、最小 %s、最大 %s'
      % (sum(1 for x in dev if x > 0), f3(statistics.median(dev)), f3(min(dev)), f3(max(dev))))
    P('  复算 diff: 中位 %s 最小 %s 最大 %s 严格<0 窗数 %d'
      % (f3(statistics.median(main_diff)), f3(min(main_diff)), f3(max(main_diff)),
         sum(1 for x in main_diff if x < 0)))
    P('')

    # —— [VAR] 变体扫描 ——
    P('[VAR] 变体扫描（57 组合 = 三分法k×7 × 空档定义×4 × 算子×2，+按空档排序分组 1）：能否命中台账两列？')
    results = []
    combos = []
    for krule in ('floor3', 'ceil3', 'floor2', 'ceil2', 'floor4', 'ceil4', 'floor10'):
        for gname in ('maxgap', 'excl_first', 'excl_last', 'gap2'):
            for op in ('median', 'mean'):
                combos.append((krule, gname, op, False))
    combos.append(('floor3', 'maxgap', 'median', True))
    for krule, gname, op, gs in combos:
        fg_l, sg_l, d_l = run_variant(krule, gname, op, gs)
        gh = sum(abs(fg_l[i] - TABLE[key][1]) < 0.005 for i, key in enumerate(WINDOWS)) + \
             sum(abs(sg_l[i] - TABLE[key][3]) < 0.005 for i, key in enumerate(WINDOWS))
        dh = sum(abs(d_l[i] - TABLE[key][4]) < 0.0005 for i, key in enumerate(WINDOWS))
        rgh = sum(round(fg_l[i], 2) == TABLE[key][1] for i, key in enumerate(WINDOWS)) + \
              sum(round(sg_l[i], 2) == TABLE[key][3] for i, key in enumerate(WINDOWS))
        rdh = sum(round(d_l[i], 3) == TABLE[key][4] for i, key in enumerate(WINDOWS))
        neg = sum(1 for x in d_l if x < 0)
        results.append((gh, dh, rgh, rdh, neg, krule, gname, op, gs, min(d_l), max(d_l)))
    results.sort(reverse=True)
    P('  前 12 名（按容差空档格命中排序）')
    P('  k / 空档定义 / 算子 / 按gap排序 | 容差命中 gap格/30 diff格/15 | round命中 gap/30 diff/15 | 负窗 | diff范围')
    for r in results[:12]:
        P('    %-7s %-10s %-6s %-5s | %2d/30  %2d/15 | %2d/30  %2d/15 | %2d | %s..%s'
          % (r[5], r[6], r[7], r[8], r[0], r[1], r[2], r[3], r[4], f3(r[9]), f3(r[10])))
    best = results[0]
    P('  最优组合：空档格 %d/30、空档差格 %d/15（列全中需 30/15）' % (best[0], best[1]))
    P('  全部 %d 组合中：空档格命中≥28 者 %d 组；diff格命中≥10 者 %d 组；能产生负 diff 者 %d 组'
      % (len(results), sum(1 for r in results if r[0] >= 28),
         sum(1 for r in results if r[1] >= 10), sum(1 for r in results if r[4] > 0)))
    P('')

    # —— [INT] 台账表内自洽 ——
    P('[INT] 台账表内自洽：diff列 − (慢gap−快gap)，显示舍入上限 0.010')
    mx = 0.0
    for key in WINDOWS:
        td = TABLE[key]
        delta = td[4] - (td[3] - td[1])
        mx = max(mx, abs(delta))
        P('  %-16s diff列 %+0.3f vs 表内差 %+0.3f → Δ %+0.4f'
          % (key[0] + '/w' + str(key[1]), td[4], td[3] - td[1], delta))
    P('  max|Δ| = %.4f' % mx)
    P('[_sa_probe] END')

    with safe_open(list(OUT_REL), 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(out_lines) + '\n')
    print('WRITTEN: ' + os.path.join(BASE, *OUT_REL))

if __name__ == '__main__':
    main()
