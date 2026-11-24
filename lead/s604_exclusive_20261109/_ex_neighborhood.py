# -*- coding: utf-8 -*-
# _ex_neighborhood.py —— 排他性检验·第二步补充：C8a 邻域自由度收口 + 近失候选逐窗差异
# 收口四个自由度：tie-break / 中位偶数处理 / k 规则 / 排序遗漏复合；
# 并对近失候选（C18b/C20a/C20z/C29b/C19）输出逐窗失败格，给出精确证伪依据。
# 写域 = lead/s604_exclusive_20261109/。零真机、零采样代码。python -I -X utf8
import json, os, statistics

BASE = os.path.normpath('D:/Project/ra2-campaign-forge')
CORPUS_REL = ('out', 're_work', 'work_chain', 'CONTINUE_20261003', 'lead', 'qc161_u0400_trip')
OUT_REL = ('lead', 's604_exclusive_20261109', '_ex_neighborhood_out.txt')

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
    ('l3_20261021',  2): (62.3, 2.71, 134.9, 2.71,  0.002),
    ('t55k_20261020', 0): (28.9, 2.62,  35.2, 2.60, -0.013),
    ('t55k_20261020', 1): (29.6, 2.61,  34.9, 2.60, -0.006),
    ('t55k_20261020', 2): (29.6, 2.61,  34.8, 2.61, -0.000),
}

out_lines = []
def P(s=''):
    out_lines.append(s)
    print(s)

def f3(x):
    return ('+' if x >= 0 else '-') + ('%.4f' % abs(x))

def safe_open(rel_parts, mode='rb', **kw):
    rp = os.path.normpath(os.path.abspath(os.path.join(BASE, *rel_parts)))
    if not (rp == BASE or rp.startswith(BASE + os.sep)):
        raise PermissionError('path outside BASE: ' + rp)
    return open(rp, mode, **kw)

def med(v):
    return statistics.median(v)

def upper_med(v):
    s = sorted(v); n = len(s)
    return s[n // 2] if n % 2 == 0 else s[(n - 1) // 2]

def lower_med(v):
    s = sorted(v); n = len(s)
    return s[(n - 1) // 2] if n % 2 == 0 else s[n // 2]

def main():
    mat = {}
    for trip, w in WINDOWS:
        with safe_open(list(CORPUS_REL) + [trip, 'measure_w%d.json' % w]) as fh:
            d = json.loads(fh.read().decode('utf-8'))
        edges = d['frame_edges']
        fids = [e[0] for e in edges]
        et = [e[1] for e in edges]
        groups = {}
        for fi, ti in zip(d['samples']['f'], d['samples']['t']):
            groups.setdefault(fi, []).append(ti)
        dur = {fids[i]: et[i + 1] - et[i] for i in range(len(fids) - 1)}
        mg = {}
        for fid in fids:
            ts = sorted(groups.get(fid, []))
            if len(ts) >= 2:
                mg[fid] = max(ts[j + 1] - ts[j] for j in range(len(ts) - 1))
        fwd = {}
        for i in range(len(fids) - 1):
            fwd[fids[i]] = mg[fids[i + 1]]
        fwd[fids[-1]] = mg[fids[-1]]
        mat[(trip, w)] = dict(fids=fids, et=et, dur=dur, mg=mg, fwd=fwd)

    def compute(key, gmap, med_op=med, k_rule='floor', tie_key=None):
        r = mat[key]
        dm = r['dur']
        if tie_key is None:
            ids = sorted([f for f in r['fids'] if f in dm and f in gmap], key=lambda x: (dm[x], x))
        else:
            ids = sorted([f for f in r['fids'] if f in dm and f in gmap], key=tie_key)
        n = len(ids)
        k = n // 3 if k_rule == 'floor' else -(-n // 3)
        fd = med_op([dm[i] for i in ids[:k]]) * 1000.0
        sd = med_op([dm[i] for i in ids[n - k:]]) * 1000.0
        fg = med_op([gmap[i] for i in ids[:k]]) * 1000.0
        sg = med_op([gmap[i] for i in ids[n - k:]]) * 1000.0
        return fd, fg, sd, sg, sg - fg, n, k, ids

    def score(rows_by_key, label):
        rd = rg = rdiff = 0
        bad = []
        for key in WINDOWS:
            fd, fg, sd, sg, diff = rows_by_key[key][:5]
            td = TABLE[key]
            h = []
            if round(fd, 1) != td[0]: h.append('fd')
            if round(fg, 2) != td[1]: h.append('fg')
            if round(sd, 1) != td[2]: h.append('sd')
            if round(sg, 2) != td[3]: h.append('sg')
            if round(diff, 3) != td[4]: h.append('diff')
            rd += 'fd' not in h and 'sd' not in h
            rg += 'fg' not in h and 'sg' not in h
            rdiff += 'diff' not in h
            if h:
                bad.append('%s/w%d:%s' % (key[0][:4], key[1], ','.join(h)))
        P('  %-30s | dur %2d/30 gap %2d/30 diff %2d/15 (合%2d/75) | 失败格: %s'
          % (label, rd, rg, rdiff, rd + rg + rdiff, (' '.join(bad) if bad else '无')))
        return rd + rg + rdiff

    P('[N1] C8a 邻域自由度收口（每个都是 C8a + 一个微观自由度）')
    rows_base = {}; rows_tie = {}; rows_up = {}; rows_low = {}; rows_ceil = {}
    for key in WINDOWS:
        rows_base[key] = compute(key, mat[key]['fwd'])
        r = mat[key]
        rows_tie[key] = compute(key, r['fwd'], tie_key=lambda x, r=r: (r['dur'][x], r['mg'][x], x))
        rows_up[key] = compute(key, r['fwd'], med_op=upper_med)
        rows_low[key] = compute(key, r['fwd'], med_op=lower_med)
        rows_ceil[key] = compute(key, r['fwd'], k_rule='ceil')
    score(rows_base, 'C8a 基准(默认tie/floor/median)')
    score(rows_tie, 'C8a + tie-break=(dur,mg,fid)')
    score(rows_up, 'C8a + upper median')
    score(rows_low, 'C8a + lower median')
    score(rows_ceil, 'C8a + k=ceil(n/3)')
    P('')

    P('[N2] 排序遗漏 × 错位复合：fwd 空档但按时序切片（未按 dur 重排）')
    rows_t3 = {}; rows_t2 = {}
    for key in WINDOWS:
        r = mat[key]
        tids = [f for f in r['fids'] if f in r['dur']]
        n = len(tids)
        k3 = n // 3; k2 = n // 2
        fd = med([r['dur'][i] for i in tids[:k3]]) * 1000.0   # 时长列仍按 dur 序（另一条代码路径）
        fd_d = sorted([f for f in tids], key=lambda x: r['dur'][x])
        fd = med([r['dur'][i] for i in fd_d[:k3]]) * 1000.0
        sd = med([r['dur'][i] for i in fd_d[n - k3:]]) * 1000.0
        fg = med([r['fwd'][i] for i in tids[:k3]]) * 1000.0
        sg = med([r['fwd'][i] for i in tids[n - k3:]]) * 1000.0
        rows_t3[key] = (fd, fg, sd, sg, sg - fg, n, k3, tids)
        fg2 = med([r['fwd'][i] for i in tids[:k2]]) * 1000.0
        sg2 = med([r['fwd'][i] for i in tids[n - k2:]]) * 1000.0
        rows_t2[key] = (fd, fg2, sd, sg2, sg2 - fg2, n, k2, tids)
    score(rows_t3, 'fwd+时序三分(k=n//3)')
    score(rows_t2, 'fwd+时序halves(k=n//2)')
    P('')

    P('[N3] 近失候选逐窗失败格（精确证伪依据）')
    # C18b: 键=E[i]-E[i-1]
    rows18b = {}
    for key in WINDOWS:
        r = mat[key]
        fids = r['fids']; n = len(fids); et = r['et']
        d18b = {fids[i]: (et[i] - et[i - 1] if i >= 1 else et[1] - et[0]) for i in range(n)}
        rows18b[key] = compute(key, r['mg'], tie_key=lambda x, d=d18b: (d[x], x))
    score(rows18b, 'C18b 键=E[i]-E[i-1]')
    # C18b 的 fd/sd 实际值（说明其时长列报的是「前一区间」键值）
    P('  C18b 时长列实值 vs 台账（前 5 窗）:')
    for key in WINDOWS[:5]:
        fd, fg, sd, sg, diff = rows18b[key][:5]
        td = TABLE[key]
        P('    %-16s fd=%7.4f (台账%5.1f)  sd=%7.4f (台账%6.1f)  diff=%s (台账%+.3f)'
          % (key[0] + '/w' + str(key[1]), fd, td[0], sd, td[2], f3(diff), td[4]))
    # C20a/z
    rows20a = {}; rows20z = {}
    for key in WINDOWS:
        r = mat[key]
        fids = r['fids']; n = len(fids); et = r['et']
        d20 = dict(r['dur']); d20[fids[n - 1]] = et[n - 1] - et[n - 2]
        rows20a[key] = compute(key, r['fwd'], tie_key=lambda x, d=d20: (d[x], x))
        fwd0 = dict(r['fwd']); fwd0[fids[n - 1]] = 0.0
        rows20z[key] = compute(key, fwd0, tie_key=lambda x, d=d20: (d[x], x))
    score(rows20a, 'C20a 末帧dur重复')
    score(rows20z, 'C20z 末帧dur重复+gap=0')
    # C29b
    rows29b = {}
    for key in WINDOWS:
        r = mat[key]
        k29 = r['fids'].__len__() // 3
        rows29b[key] = compute(key, r['fwd'], k_rule='floor')  # 占位
        # 手工：ids=n-1 帧，k=全帧数//3
        dm = r['dur']
        ids = sorted([f for f in r['fids'] if f in dm], key=lambda x: (dm[x], x))
        k = len(r['fids']) // 3
        fd = med([dm[i] for i in ids[:k]]) * 1000.0
        sd = med([dm[i] for i in ids[len(ids) - k:]]) * 1000.0
        fg = med([r['fwd'][i] for i in ids[:k]]) * 1000.0
        sg = med([r['fwd'][i] for i in ids[len(ids) - k:]]) * 1000.0
        rows29b[key] = (fd, fg, sd, sg, sg - fg, len(ids), k, ids)
    score(rows29b, 'C29b k=全帧数//3 + C8a')
    # C19a
    rows19a = {}
    for key in WINDOWS:
        r = mat[key]
        dm = r['dur']
        ids = sorted([f for f in r['fids'] if f in dm], key=lambda x: (dm[x], x))
        n = len(ids); k = n // 3
        fd = med([dm[i] for i in ids[:k]]) * 1000.0
        sd = med([dm[i] for i in ids[n - k:]]) * 1000.0
        fg = med([r['fwd'][i] for i in ids[:k]]) * 1000.0
        sg = med([r['mg'][i] for i in ids[n - k:]]) * 1000.0
        rows19a[key] = (fd, fg, sd, sg, sg - fg, n, k, ids)
    score(rows19a, 'C19a fast错位/slow正确')
    P('')

    P('[N4] C8a 与台账逐窗距离（全部 ≤ 显示半格）')
    for key in WINDOWS:
        fd, fg, sd, sg, diff = rows_base[key][:5]
        td = TABLE[key]
        P('  %-16s Δfg=%+.4f Δsg=%+.4f Δdiff=%+.4f' % (key[0] + '/w' + str(key[1]),
          fg - td[1], sg - td[3], diff - td[4]))
    P('')
    P('[_ex_neighborhood] END')

    with safe_open(OUT_REL, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(out_lines) + '\n')

if __name__ == '__main__':
    main()
