# -*- coding: utf-8 -*-
# _ex_mc_and_cells.py —— 排他性检验·收尾量化：
#  [M] 随机置换基线：200 个随机 gap→帧 重挂接能到多少格（校准 75/75 的特殊性）
#  [X] 近失候选（battery 版 C18b/C20a/C20z/C20c/C29b）的精确失败格清单
# 写域 = lead/s604_exclusive_20261109/。零真机、零采样代码。python -I -X utf8
import json, os, statistics, random

BASE = os.path.normpath('D:/Project/ra2-campaign-forge')
CORPUS_REL = ('out', 're_work', 'work_chain', 'CONTINUE_20261003', 'lead', 'qc161_u0400_trip')
OUT_REL = ('lead', 's604_exclusive_20261109', '_ex_mc_and_cells_out.txt')

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
        mg = {}
        for fid in fids:
            ts = sorted(groups.get(fid, []))
            if len(ts) >= 2:
                mg[fid] = max(ts[j + 1] - ts[j] for j in range(len(ts) - 1))
        ids = sorted([f for f in fids if f in dur], key=lambda x: (dur[x], x))
        k = len(ids) // 3
        mat[(trip, w)] = dict(fids=fids, dur=dur, mg=mg, ids=ids, k=k)

    def cells_for(gmap_by_key):
        """返回 (命中格数, 失败格清单)"""
        hits = 0
        bad = []
        for key in WINDOWS:
            r = mat[key]; gmap = gmap_by_key[key]
            ids = r['ids']; k = r['k']; n = len(ids)
            fd = med([r['dur'][i] for i in ids[:k]]) * 1000.0
            sd = med([r['dur'][i] for i in ids[n - k:]]) * 1000.0
            fg = med([gmap[i] for i in ids[:k]]) * 1000.0
            sg = med([gmap[i] for i in ids[n - k:]]) * 1000.0
            diff = sg - fg
            td = TABLE[key]
            ok = True
            if round(fd, 1) != td[0]: ok = False; bad.append(key[0][:4] + '/w%d:fd' % key[1])
            if round(fg, 2) != td[1]: ok = False; bad.append(key[0][:4] + '/w%d:fg' % key[1])
            if round(sd, 1) != td[2]: ok = False; bad.append(key[0][:4] + '/w%d:sd' % key[1])
            if round(sg, 2) != td[3]: ok = False; bad.append(key[0][:4] + '/w%d:sg' % key[1])
            if round(diff, 3) != td[4]: ok = False; bad.append(key[0][:4] + '/w%d:diff' % key[1])
            hits += 0 if bad and bad[-1].startswith(key[0][:4]) else 0
        # 重新按格计数
        hits = 75 - len(bad)
        return hits, bad

    # ---- [M] 随机置换基线 ----
    P('[M] 随机置换基线：每窗把 mg 值随机重挂接到帧（时长列固定正确），200 次')
    random.seed(20261109)
    dist = []
    best = -1; best_perm = None
    for trial in range(200):
        gmap_by_key = {}
        for key in WINDOWS:
            r = mat[key]
            vals = [r['mg'][f] for f in r['fids']]
            perm = vals[:]
            random.shuffle(perm)
            gmap_by_key[key] = dict(zip(r['fids'], perm))
        hits, _ = cells_for(gmap_by_key)
        dist.append(hits)
        if hits > best:
            best = hits; best_perm = trial
    dist.sort()
    P('  200 次随机重挂接的 75 格命中数分布: min=%d p25=%d 中位=%d p75=%d max=%d'
      % (dist[0], dist[len(dist) // 4], dist[len(dist) // 2], dist[3 * len(dist) // 4], dist[-1]))
    P('  最高命中 = %d/75（试验 #%d）——没有任何随机挂接接近 75' % (best, best_perm))
    # 时长列固定正确 ⇒ 每次基线 = 30 格；随机部分满分 45 格
    rand_part = sorted(h - 30 for h in dist)
    P('  扣除固定时长列 30 格后的随机部分（满分 45）: 中位=%d max=%d/45' % (rand_part[len(rand_part) // 2], rand_part[-1]))
    P('')

    # ---- [X] 近失候选精确失败格（battery 语义） ----
    P('[X] 近失候选精确失败格（round 判等）')
    # C18b battery 版：ids 按键=E[i]-E[i-1] 排序（全帧），fd/sd 报键值，gap=自身 mg
    rows18b = {}
    for key in WINDOWS:
        r = mat[key]
        fids = r['fids']; n = len(fids); et = [e for e in [x for x in r['dur']] and []] or None
        # 重建 et
        # dur 由 et 派生；此处直接从 dur 反推键：键(i)=dur(i-1)，键(0)=dur(0)
        d18b = {}
        fl = r['fids']
        durs = r['dur']
        d18b[fl[0]] = durs[fl[0]]
        for i in range(1, len(fl)):
            d18b[fl[i]] = durs[fl[i - 1]] if fl[i - 1] in durs else durs[fl[i]]
        ids = sorted([f for f in fl if f in d18b and f in r['mg']], key=lambda x: (d18b[x], x))
        n2 = len(ids); k = n2 // 3
        fd = med([d18b[i] for i in ids[:k]]) * 1000.0
        sd = med([d18b[i] for i in ids[n2 - k:]]) * 1000.0
        fg = med([r['mg'][i] for i in ids[:k]]) * 1000.0
        sg = med([r['mg'][i] for i in ids[n2 - k:]]) * 1000.0
        rows18b[key] = (fd, fg, sd, sg, sg - fg, n2, k)
    hits, bad = [], []
    hits18 = 75; bad18 = []
    for key in WINDOWS:
        fd, fg, sd, sg, diff = rows18b[key][:5]
        td = TABLE[key]
        if round(fd, 1) != td[0]: bad18.append('%s/w%d:fd' % (key[0][:4], key[1]))
        if round(fg, 2) != td[1]: bad18.append('%s/w%d:fg' % (key[0][:4], key[1]))
        if round(sd, 1) != td[2]: bad18.append('%s/w%d:sd' % (key[0][:4], key[1]))
        if round(sg, 2) != td[3]: bad18.append('%s/w%d:sg' % (key[0][:4], key[1]))
        if round(diff, 3) != td[4]: bad18.append('%s/w%d:diff' % (key[0][:4], key[1]))
    P('  C18b 键=前一区间: %d/75  失败格: %s' % (75 - len(bad18), ' '.join(bad18) if bad18 else '无'))

    # C20a / C20z battery 版
    for tag, zero_gap in (('C20a 末帧dur=前条重复', False), ('C20z 末帧dur重复+gap=0', True)):
        bad20 = []
        for key in WINDOWS:
            r = mat[key]
            fl = r['fids']; n = len(fl)
            d20 = dict(r['dur'])
            d20[fl[n - 1]] = r['dur'][fl[n - 2]]
            ids = sorted([f for f in fl if f in d20 and f in r['mg']], key=lambda x: (d20[x], x))
            n2 = len(ids); k = n2 // 3
            fd = med([d20[i] for i in ids[:k]]) * 1000.0
            sd = med([d20[i] for i in ids[n2 - k:]]) * 1000.0
            fg = med([r['mg'].get(fl[i + 1], r['mg'][fl[i]] if i == n - 1 else None) if i < n - 1 else (0.0 if zero_gap else r['mg'][fl[i]]) for i in [fl.index(x) for x in ids[:k]]]) if False else None
            # 直接按位置建 fwd
            pos = {f: i for i, f in enumerate(fl)}
            fwd = {}
            for i in range(n - 1):
                fwd[fl[i]] = r['mg'][fl[i + 1]]
            fwd[fl[n - 1]] = 0.0 if zero_gap else r['mg'][fl[n - 1]]
            fg = med([fwd[i] for i in ids[:k]]) * 1000.0
            sg = med([fwd[i] for i in ids[n2 - k:]]) * 1000.0
            diff = sg - fg
            td = TABLE[key]
            if round(fd, 1) != td[0]: bad20.append('%s/w%d:fd' % (key[0][:4], key[1]))
            if round(fg, 2) != td[1]: bad20.append('%s/w%d:fg' % (key[0][:4], key[1]))
            if round(sd, 1) != td[2]: bad20.append('%s/w%d:sd' % (key[0][:4], key[1]))
            if round(sg, 2) != td[3]: bad20.append('%s/w%d:sg' % (key[0][:4], key[1]))
            if round(diff, 3) != td[4]: bad20.append('%s/w%d:diff' % (key[0][:4], key[1]))
        P('  %s: %d/75  失败格: %s' % (tag, 75 - len(bad20), ' '.join(bad20) if bad20 else '无'))

    # C20c battery 版（首帧出局 + fwd）
    bad20c = []
    for key in WINDOWS:
        r = mat[key]
        fl = r['fids']; n = len(fl)
        ids = sorted([fl[i] for i in range(1, n - 1)], key=lambda x: (r['dur'][x], x))
        n2 = len(ids); k = n2 // 3
        fd = med([r['dur'][i] for i in ids[:k]]) * 1000.0
        sd = med([r['dur'][i] for i in ids[n2 - k:]]) * 1000.0
        fwd = {}
        for i in range(n - 1):
            fwd[fl[i]] = r['mg'][fl[i + 1]]
        fwd[fl[n - 1]] = r['mg'][fl[n - 1]]
        fg = med([fwd[i] for i in ids[:k]]) * 1000.0
        sg = med([fwd[i] for i in ids[n2 - k:]]) * 1000.0
        diff = sg - fg
        td = TABLE[key]
        if round(fd, 1) != td[0]: bad20c.append('%s/w%d:fd' % (key[0][:4], key[1]))
        if round(fg, 2) != td[1]: bad20c.append('%s/w%d:fg' % (key[0][:4], key[1]))
        if round(sd, 1) != td[2]: bad20c.append('%s/w%d:sd' % (key[0][:4], key[1]))
        if round(sg, 2) != td[3]: bad20c.append('%s/w%d:sg' % (key[0][:4], key[1]))
        if round(diff, 3) != td[4]: bad20c.append('%s/w%d:diff' % (key[0][:4], key[1]))
    P('  C20c 首帧出局+C8a: %d/75  失败格: %s' % (75 - len(bad20c), ' '.join(bad20c) if bad20c else '无'))
    P('')
    P('[_ex_mc_and_cells] END')

    with safe_open(OUT_REL, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(out_lines) + '\n')

if __name__ == '__main__':
    main()
