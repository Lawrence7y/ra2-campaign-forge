# -*- coding: utf-8 -*-
# _ex_compound.py —— 排他性检验·补口：定义×错位 交叉扫描的剩余合理复合
# 57 组合扫描（上轮）测过「定义×k×算子」但无错位；C8a = maxgap×后继错位；C27 = 次大×后继错位。
# 本件补：mean(maxgap)×错位、去首×错位、帧内中位gap×错位（level 关卡先验弱，但仍实跑留证）。
# 写域 = lead/s604_exclusive_20261109/。零真机、零采样代码。python -I -X utf8
import json, os, statistics

BASE = os.path.normpath('D:/Project/ra2-campaign-forge')
CORPUS_REL = ('out', 're_work', 'work_chain', 'CONTINUE_20261003', 'lead', 'qc161_u0400_trip')
OUT_REL = ('lead', 's604_exclusive_20261109', '_ex_compound_out.txt')

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

def safe_open(rel_parts, mode='rb', **kw):
    rp = os.path.normpath(os.path.abspath(os.path.join(BASE, *rel_parts)))
    if not (rp == BASE or rp.startswith(BASE + os.sep)):
        raise PermissionError('path outside BASE: ' + rp)
    return open(rp, mode, **kw)

def med(v):
    return statistics.median(v)

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
        mg = {}; mgmean = {}; mgexf = {}; mgmed = {}
        for fid in fids:
            ts = sorted(groups.get(fid, []))
            if len(ts) >= 2:
                gs = [ts[j + 1] - ts[j] for j in range(len(ts) - 1)]
                mg[fid] = max(gs)
                mgmean[fid] = sum(gs) / len(gs)
                mgexf[fid] = max(gs[1:]) if len(gs) >= 2 else None
                mgmed[fid] = statistics.median(gs)
        mat[(trip, w)] = dict(fids=fids, dur=dur, mg=mg, mgmean=mgmean, mgexf=mgexf, mgmed=mgmed)

    def run(tag, defmap_name):
        rd = rg = rdiff = 0
        neg = 0
        mxd = 0.0
        for key in WINDOWS:
            r = mat[key]
            fids = r['fids']; n = len(fids)
            dm = r['dur']; src = r[defmap_name]
            gmap = {}
            for i in range(n - 1):
                if fids[i + 1] in src and src[fids[i + 1]] is not None:
                    gmap[fids[i]] = src[fids[i + 1]]
            ids = sorted([f for f in fids if f in dm and f in gmap], key=lambda x: (dm[x], x))
            n2 = len(ids); k = n2 // 3
            fd = med([dm[i] for i in ids[:k]]) * 1000.0
            sd = med([dm[i] for i in ids[n2 - k:]]) * 1000.0
            fg = med([gmap[i] for i in ids[:k]]) * 1000.0
            sg = med([gmap[i] for i in ids[n2 - k:]]) * 1000.0
            diff = sg - fg
            td = TABLE[key]
            rd += round(fd, 1) == td[0]; rd += round(sd, 1) == td[2]
            rg += round(fg, 2) == td[1]; rg += round(sg, 2) == td[3]
            rdiff += round(diff, 3) == td[4]
            neg += diff < 0
            mxd = max(mxd, abs(fg - td[1]), abs(sg - td[3]))
        P('  %-28s | round: dur %2d/30 gap %2d/30 diff %2d/15 (合%2d/75) | 负diff:%2d | max|Δgap|=%.4f'
          % (tag, rd, rg, rdiff, rd + rg + rdiff, neg, mxd))

    P('[X2] 定义×后继错位 交叉（补 57 组合扫描无错位、C27 只测次大的缺口）')
    run('mean(maxgap)×后继错位', 'mgmean')
    run('去首(excl_first)×后继错位', 'mgexf')
    run('帧内中位gap×后继错位', 'mgmed')
    P('')
    P('[_ex_compound] END')

    with safe_open(OUT_REL, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(out_lines) + '\n')

if __name__ == '__main__':
    main()
