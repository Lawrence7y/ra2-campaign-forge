# -*- coding: utf-8 -*-
# _ex_candidates.py —— 排他性检验·第二步：构造第 8..N 个机理候选并逐一实跑
# 候选选取标准 = 机理上合理（实现错误/口径误用的真实码形），不是容易证伪。
# 评分与上一轮同口径：容差 gap<0.005/diff<0.0005；round 判等 dur 1位/gap 2位/diff 3位。
# 写域 = lead/s604_exclusive_20261109/。零真机、零采样代码。python -I -X utf8
import json, os, statistics, bisect

BASE = os.path.normpath('D:/Project/ra2-campaign-forge')
CORPUS_REL = ('out', 're_work', 'work_chain', 'CONTINUE_20261003', 'lead', 'qc161_u0400_trip')
OUT_REL = ('lead', 's604_exclusive_20261109', '_ex_candidates_out.txt')

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

def mean(v):
    return sum(v) / len(v)

def maxgap_of(ts):
    ts = sorted(ts)
    return max(ts[j + 1] - ts[j] for j in range(len(ts) - 1)) if len(ts) >= 2 else None

def maxgap2_of(ts):
    ts = sorted(ts)
    if len(ts) < 3:
        return None
    gaps = sorted((ts[j + 1] - ts[j] for j in range(len(ts) - 1)), reverse=True)
    return gaps[1]

def medgap_of(ts):
    ts = sorted(ts)
    if len(ts) < 2:
        return None
    return statistics.median([ts[j + 1] - ts[j] for j in range(len(ts) - 1)])

def main():
    # ================= 语料装载 + 逐窗原料 =================
    mat = {}
    for trip, w in WINDOWS:
        with safe_open(list(CORPUS_REL) + [trip, 'measure_w%d.json' % w]) as fh:
            d = json.loads(fh.read().decode('utf-8'))
        edges = d['frame_edges']
        fids = [e[0] for e in edges]
        et = [e[1] for e in edges]
        t_arr = d['samples']['t']
        f_arr = d['samples']['f']
        n = len(fids)
        groups = {}
        for fi, ti in zip(f_arr, t_arr):
            groups.setdefault(fi, []).append(ti)
        dur = {fids[i]: et[i + 1] - et[i] for i in range(n - 1)}
        mg = {}; mg2 = {}; medg = {}; mingap = {}; span = {}
        for i, fid in enumerate(fids):
            ts = sorted(groups.get(fid, []))
            if len(ts) >= 2:
                gs = [ts[j + 1] - ts[j] for j in range(len(ts) - 1)]
                mg[fid] = max(gs)
                medg[fid] = statistics.median(gs)
                mingap[fid] = min(gs)
                span[fid] = ts[-1] - ts[0]
            if len(ts) >= 3:
                mg2[fid] = sorted(gs, reverse=True)[1]
        # 全局样本序里的每帧样本下标（t 单调 ⇒ 连续）
        first_idx = {}
        for idx, fi in enumerate(f_arr):
            if fi not in first_idx:
                first_idx[fi] = idx
        mat[(trip, w)] = dict(fids=fids, et=et, dur=dur, mg=mg, mg2=mg2, medg=medg,
                              mingap=mingap, span=span, t_arr=t_arr, f_arr=f_arr,
                              first_idx=first_idx, n=n, groups=groups)

    def fwd_map(key, lag=1):
        """时间后继 lag 帧的 mg（末帧回绕自身）"""
        r = mat[key]; fids = r['fids']
        out = {}
        for i in range(len(fids)):
            j = i + lag
            out[fids[i]] = r['mg'][fids[j]] if j < len(fids) else r['mg'][fids[i]]
        return out

    def bwd_map(key, lag=1):
        r = mat[key]; fids = r['fids']
        out = {}
        for i in range(len(fids)):
            j = i - lag
            out[fids[i]] = r['mg'][fids[j]] if j >= 0 else r['mg'][fids[i]]
        return out

    def thirds_g(key, gmap, durmap=None, ids_override=None, k_override=None):
        r = mat[key]
        dm = durmap if durmap is not None else r['dur']
        if ids_override is None:
            ids = sorted([f for f in r['fids'] if f in dm and f in gmap], key=lambda x: (dm[x], x))
        else:
            ids = sorted(ids_override, key=lambda x: (dm[x], x))
        n = len(ids)
        k = k_override if k_override is not None else n // 3
        fd = med([dm[i] for i in ids[:k]]) * 1000.0
        sd = med([dm[i] for i in ids[n - k:]]) * 1000.0
        fg = med([gmap[i] for i in ids[:k]]) * 1000.0
        sg = med([gmap[i] for i in ids[n - k:]]) * 1000.0
        return fd, fg, sd, sg, sg - fg, n, k

    def score_rows(rows):
        gh = dh = rd = rg = rdiff = 0
        pos_dfg = neg_dsg = negdiff = 0
        mxf = mxs = mxd = 0.0
        for key in WINDOWS:
            fd, fg, sd, sg, diff = rows[key][:5]
            td = TABLE[key]
            gh += abs(fg - td[1]) < 0.005; gh += abs(sg - td[3]) < 0.005
            dh += abs(diff - td[4]) < 0.0005
            rd += round(fd, 1) == td[0]; rd += round(sd, 1) == td[2]
            rg += round(fg, 2) == td[1]; rg += round(sg, 2) == td[3]
            rdiff += round(diff, 3) == td[4]
            pos_dfg += (td[1] - fg) > 0
            neg_dsg += (td[3] - sg) < 0
            negdiff += diff < 0
            mxf = max(mxf, abs(fg - td[1]), abs(sg - td[3]))
            mxd = max(mxd, abs(diff - td[4]))
        return gh, dh, rd, rg, rdiff, pos_dfg, neg_dsg, negdiff, mxf, mxd

    RESULTS = {}
    def run(tag, rows):
        gh, dh, rd, rg, rdiff, pos_dfg, neg_dsg, negdiff, mxf, mxd = score_rows(rows)
        RESULTS[tag] = (rd + rg + rdiff, rd, rg, rdiff)
        P('  %-26s | round: dur %2d/30 gap %2d/30 diff %2d/15 (合%2d/75) | 容差 gap %2d/30 diff %2d/15 | Δfg>0:%2d Δsg<0:%2d 负diff:%2d | max|Δgap|=%.4f max|Δdiff|=%.4f'
          % (tag, rd, rg, rdiff, rd + rg + rdiff, gh, dh, pos_dfg, neg_dsg, negdiff, mxf, mxd))
        return rows

    P('[候选总表] 每行 = 一种机理；75 格 = 时长列 round1 30 + 空档列 round2 30 + 差列 round3 15')
    P('')

    # ---- 基准行 ----
    true_rows = {}; c8a_rows = {}; c8b_rows = {}
    for key in WINDOWS:
        true_rows[key] = thirds_g(key, mat[key]['mg'])
        c8a_rows[key] = thirds_g(key, fwd_map(key))
        c8b_rows[key] = thirds_g(key, bwd_map(key))
    P('[基准]')
    run('C0 真值(正确配对)', true_rows)
    run('C8a 挂时间后继(上轮筛入)', c8a_rows)
    run('C8b 挂时间前继(上轮证伪)', c8b_rows)
    P('')

    # ================= C13 bisect 边界变体（样本→帧归属重推导 off-by-one） =================
    P('[C13] bisect 边界变体：不用语料 f，而用 t 对 edge 起点重推导帧归属（自然 off-by-one 码形）')
    for key in WINDOWS:
        r = mat[key]
        edge_ts = r['et']
        gA = {}; gB = {}; gC = {}; gD = {}
        for ti in r['t_arr']:
            ia = bisect.bisect_left(edge_ts, ti) - 1
            ib = bisect.bisect_left(edge_ts, ti)
            ic = bisect.bisect_right(edge_ts, ti) - 2
            idd = bisect.bisect_right(edge_ts, ti)
            gA.setdefault(ia, []).append(ti)
            gB.setdefault(ib, []).append(ti)
            gC.setdefault(ic, []).append(ti)
            gD.setdefault(idd, []).append(ti)
        fids = r['fids']; n = r['n']
        r['mgA'] = {}; r['mgB'] = {}; r['mgC'] = {}; r['mgD'] = {}
        for j in range(n):
            fid = fids[j]
            for gname, g in (('mgA', gA), ('mgB', gB), ('mgC', gC), ('mgD', gD)):
                v = maxgap_of(g.get(j, []))
                if v is not None:
                    r[gname][fid] = v
    rowsA = {}; rowsB = {}; rowsC = {}; rowsD = {}
    for key in WINDOWS:
        r = mat[key]
        rowsA[key] = thirds_g(key, r['mgA'])
        rowsB[key] = thirds_g(key, r['mgB'])
        rowsC[key] = thirds_g(key, r['mgC'])
        rowsD[key] = thirds_g(key, r['mgD'])
    run('C13a bisect_left-1(混内+j+1首)', rowsA)
    run('C13b bisect_left(混j-1内+首)', rowsB)
    run('C13c bisect_right-2(整体后移)', rowsC)
    run('C13d bisect_right(整体前移)', rowsD)
    # C13c 与 C8a 逐位比较
    sameC = all(rowsC[k][:5] == c8a_rows[k][:5] for k in WINDOWS)
    P('  C13c vs C8a 五元组逐位相同: %s' % sameC)
    P('')

    # ================= C14 状态机边界样本变体（用语料 f 分组但挪边界样本） =================
    P('[C14] 状态机边界样本变体：晚一拍/早一拍 flush 的真实数值含义')
    rowsE = {}; rowsF = {}
    for key in WINDOWS:
        r = mat[key]
        fids = r['fids']; n = r['n']; groups = r['groups']; t_arr = r['t_arr']; fi_map = r['first_idx']
        # C14a: 帧 j 组 = 自身样本 + 帧 j+1 的首样本（晚一拍 flush）
        gE = {}
        for j in range(n):
            fid = fids[j]
            lst = list(groups.get(fid, []))
            if j + 1 < n:
                lst.append(t_arr[fi_map[fids[j + 1]]])
            gE[fid] = lst
        # C14b: 帧 j 组 = 帧 j-1 的末样本 + 自身样本去末（早一拍截断）
        gF = {}
        for j in range(n):
            fid = fids[j]
            lst = list(groups.get(fid, []))[:-1]
            if j >= 1:
                prev_ts = sorted(groups.get(fids[j - 1], []))
                if prev_ts:
                    lst = [prev_ts[-1]] + lst
            gF[fid] = lst
        mgE = {fid: maxgap_of(gE[fid]) for fid in fids if maxgap_of(gE[fid]) is not None}
        mgF = {fid: maxgap_of(gF[fid]) for fid in fids if maxgap_of(gF[fid]) is not None}
        rowsE[key] = thirds_g(key, mgE)
        rowsF[key] = thirds_g(key, mgF)
    run('C14a 晚一拍(含j+1首样本)', rowsE)
    run('C14b 早一拍(含j-1末样本)', rowsF)
    P('')

    # ================= C15 两帧错位 =================
    P('[C15] 两帧错位（gap ← i±2）')
    rows15a = {}; rows15b = {}
    for key in WINDOWS:
        rows15a[key] = thirds_g(key, fwd_map(key, 2))
        rows15b[key] = thirds_g(key, bwd_map(key, 2))
    run('C15a 挂后继×2', rows15a)
    run('C15b 挂前继×2', rows15b)
    P('')

    # ================= C16 平滑半错位（插值补偿类） =================
    P('[C16] 平滑/插值类：相邻帧 mg 平均')
    rows16a = {}; rows16b = {}; rows16c = {}
    for key in WINDOWS:
        r = mat[key]; fids = r['fids']; n = r['n']; mg = r['mg']
        s16a = {}; s16b = {}; s16c = {}
        for i in range(n - 1):
            s16a[fids[i]] = (mg[fids[i]] + mg[fids[i + 1]]) / 2.0
        for i in range(n - 2):
            s16b[fids[i]] = (mg[fids[i + 1]] + mg[fids[i + 2]]) / 2.0
        for i in range(1, n):
            s16c[fids[i]] = (mg[fids[i - 1]] + mg[fids[i]]) / 2.0
        rows16a[key] = thirds_g(key, s16a)
        rows16b[key] = thirds_g(key, s16b)
        rows16c[key] = thirds_g(key, s16c)
    run('C16a (mg_i+mg_i+1)/2', rows16a)
    run('C16b (mg_i+1+mg_i+2)/2', rows16b)
    run('C16c (mg_i-1+mg_i)/2', rows16c)
    P('')

    # ================= C17 跨帧 gap 混入（全局差分切片 off-by-one） =================
    P('[C17] 跨帧间隔混入：mg\' = max(mg, 边界间隔)')
    rows17a = {}; rows17b = {}
    for key in WINDOWS:
        r = mat[key]
        fids = r['fids']; n = r['n']; t_arr = r['t_arr']; fi_map = r['first_idx']; mg = r['mg']
        s17a = {}; s17b = {}
        for j in range(n):
            fid = fids[j]
            base = mg[fid]
            if j >= 1:
                entry = t_arr[fi_map[fid]] - t_arr[fi_map[fid] - 1]
                s17a[fid] = max(base, entry)
            else:
                s17a[fid] = base
            if j + 1 < n:
                nxt = fids[j + 1]
                exitg = t_arr[fi_map[nxt]] - t_arr[fi_map[nxt] - 1]
                s17b[fid] = max(base, exitg)
            else:
                s17b[fid] = base
        rows17a[key] = thirds_g(key, s17a)
        rows17b[key] = thirds_g(key, s17b)
    run('C17a 混入入口间隔', rows17a)
    run('C17b 混入出口间隔', rows17b)
    P('')

    # ================= C18 时长键错位（空档正确、排序键错一帧） =================
    P('[C18] 时长排序键错一帧（空档配对正确）')
    rows18a = {}; rows18b = {}
    for key in WINDOWS:
        r = mat[key]
        fids = r['fids']; n = r['n']; et = r['et']
        d18a = {fids[i]: et[i + 2] - et[i + 1] for i in range(n - 2)}
        d18b = {}
        for i in range(n):
            d18b[fids[i]] = (et[i] - et[i - 1]) if i >= 1 else (et[1] - et[0])
        rows18a[key] = thirds_g(key, r['mg'], durmap=d18a)
        rows18b[key] = thirds_g(key, r['mg'], durmap=d18b)
    run('C18a 键=E[i+2]-E[i+1]', rows18a)
    run('C18b 键=E[i]-E[i-1]', rows18b)
    P('')

    # ================= C19 单侧错位（copy-paste bug） =================
    P('[C19] 单侧错位：fast 分支错位 slow 正确（及反向）')
    rows19a = {}; rows19b = {}
    fwd_all = {key: fwd_map(key) for key in WINDOWS}
    for key in WINDOWS:
        r = mat[key]
        dm = r['dur']
        ids = sorted([f for f in r['fids'] if f in dm], key=lambda x: (dm[x], x))
        n = len(ids); k = n // 3
        mixA = {}; mixB = {}
        for f in ids:
            mixA[f] = fwd_all[key][f]
            mixB[f] = r['mg'][f]
        fdA = med([dm[i] for i in ids[:k]]) * 1000.0
        sdA = med([dm[i] for i in ids[n - k:]]) * 1000.0
        fgA = med([mixA[i] for i in ids[:k]]) * 1000.0
        sgA = med([mixB[i] for i in ids[n - k:]]) * 1000.0
        rows19a[key] = (fdA, fgA, sdA, sgA, sgA - fgA, n, k)
        fgB = med([mixB[i] for i in ids[:k]]) * 1000.0
        sgB = med([mixA[i] for i in ids[n - k:]]) * 1000.0
        rows19b[key] = (fdA, fgB, sdA, sgB, sgB - fgB, n, k)
    run('C19a fast错位/slow正确', rows19a)
    run('C19b fast正确/slow错位', rows19b)
    P('')

    # ================= C20 末帧特殊处理 × C8a =================
    P('[C20] 末帧特殊处理 × C8a（末帧补 dur / 首帧出局）')
    rows20a = {}; rows20z = {}; rows20c = {}
    for key in WINDOWS:
        r = mat[key]
        fids = r['fids']; n = r['n']; et = r['et']
        d20 = dict(r['dur']); d20[fids[n - 1]] = et[n - 1] - et[n - 2]
        fwd = fwd_all[key]
        rows20a[key] = thirds_g(key, fwd, durmap=d20)
        fwd0 = dict(fwd); fwd0[fids[n - 1]] = 0.0
        rows20z[key] = thirds_g(key, fwd0, durmap=d20)
        ids_c = r['fids'][1:n - 1]
        rows20c[key] = thirds_g(key, fwd, ids_override=ids_c)
    run('C20a 末帧dur=前条重复', rows20a)
    run('C20z 末帧dur重复+gap=0', rows20z)
    run('C20c 首帧出局+C8a', rows20c)
    P('')

    # ================= C21 元组序排序（按空档排序再三分） =================
    P('[C21] 记录元组 = (mg, dur) 直接 sort（按空档排序再三分，时长列被迫跟着错）')
    rows21 = {}
    for key in WINDOWS:
        r = mat[key]
        dm = r['dur']
        ids = [f for f in r['fids'] if f in dm]
        recs = sorted(((r['mg'][f], dm[f], f) for f in ids))
        k = len(recs) // 3
        fast = recs[:k]; slow = recs[len(recs) - k:]
        fd = med([x[1] for x in fast]) * 1000.0
        sd = med([x[1] for x in slow]) * 1000.0
        fg = med([x[0] for x in fast]) * 1000.0
        sg = med([x[0] for x in slow]) * 1000.0
        rows21[key] = (fd, fg, sd, sg, sg - fg, len(recs), k)
    run('C21 sort按(mg,dur)', rows21)
    P('')

    # ================= C22 中位/均值算子混合 =================
    P('[C22] 算子混合：一列 median 一列 mean（correct 配对）')
    rows22a = {}; rows22b = {}
    for key in WINDOWS:
        r = mat[key]
        dm = r['dur']
        ids = sorted([f for f in r['fids'] if f in dm and f in r['mg']], key=lambda x: (dm[x], x))
        n = len(ids); k = n // 3
        fq = [r['mg'][i] for i in ids[:k]]; sq = [r['mg'][i] for i in ids[n - k:]]
        fd = med([dm[i] for i in ids[:k]]) * 1000.0
        sd = med([dm[i] for i in ids[n - k:]]) * 1000.0
        fgA = med(fq) * 1000.0; sgA = mean(sq) * 1000.0
        rows22a[key] = (fd, fgA, sd, sgA, sgA - fgA, n, k)
        fgB = mean(fq) * 1000.0; sgB = med(sq) * 1000.0
        rows22b[key] = (fd, fgB, sd, sgB, sgB - fgB, n, k)
    run('C22a fg=med sg=mean', rows22a)
    run('C22b fg=mean sg=med', rows22b)
    P('')

    # ================= C23 相邻帧池化 max =================
    P('[C23] 相邻帧池化：mg\' = max(mg_i, mg_i+1)')
    rows23 = {}
    for key in WINDOWS:
        r = mat[key]
        fids = r['fids']; n = r['n']; mg = r['mg']
        s23 = {}
        for i in range(n - 1):
            s23[fids[i]] = max(mg[fids[i]], mg[fids[i + 1]])
        s23[fids[n - 1]] = mg[fids[n - 1]]
        rows23[key] = thirds_g(key, s23)
    run('C23 max(mg_i,mg_i+1)', rows23)
    P('')

    # ================= C24 时长序 rank 错位（C3 的未测反方向） =================
    P('[C24] 时长序 rank 错位：rank j 挂 rank j+1 的 mg（上轮 C3 只测了 j-1 方向）')
    rows24a = {}; rows24b = {}
    for key in WINDOWS:
        r = mat[key]
        dm = r['dur']
        ids = sorted([f for f in r['fids'] if f in dm], key=lambda x: (dm[x], x))
        m = len(ids); k = m // 3
        mgs_rank = [r['mg'][f] for f in ids]
        # a: wrap（末 rank 回绕自身）
        sh_a = mgs_rank[1:] + mgs_rank[-1:]
        # b: drop（末 rank 出局，ids 少一个）
        sh_b = mgs_rank[1:]
        ids_b = ids[:-1]
        fga = med(sh_a[:k]) * 1000.0; sga = med(sh_a[m - k:]) * 1000.0
        fd = med([dm[i] for i in ids[:k]]) * 1000.0; sd = med([dm[i] for i in ids[m - k:]]) * 1000.0
        rows24a[key] = (fd, fga, sd, sga, sga - fga, m, k)
        mb = len(ids_b); kb = mb // 3
        fgb = med(sh_b[:kb]) * 1000.0; sgb = med(sh_b[mb - kb:]) * 1000.0
        fdb = med([dm[i] for i in ids_b[:kb]]) * 1000.0; sdb = med([dm[i] for i in ids_b[mb - kb:]]) * 1000.0
        rows24b[key] = (fdb, fgb, sdb, sgb, sgb - fgb, mb, kb)
    run('C24a rank←rank+1(wrap)', rows24a)
    run('C24b rank←rank+1(drop)', rows24b)
    P('')

    # ================= C25 行序错位誊写 =================
    P('[C25] 行序错位誊写：表行 w 显示 C8a 行 w±1（trip 内循环）')
    def run_row_shift(shift):
        rg2 = rdiff2 = 0
        for key in WINDOWS:
            trip, w = key
            w2 = (w + shift) % 3
            fd, fg, sd, sg, diff = c8a_rows[(trip, w2)][:5]
            td = TABLE[key]
            rg2 += round(fg, 2) == td[1]; rg2 += round(sg, 2) == td[3]
            rdiff2 += round(diff, 3) == td[4]
        P('  %-26s | round gap %2d/30 diff %2d/15' % ('C25 行错位 %+d' % shift, rg2, rdiff2))
    run_row_shift(1)
    run_row_shift(-1)
    P('')

    # ================= C26 单位混用 bisect =================
    P('[C26] 单位混用：t(秒) 对 edge 起点(毫秒) 做 bisect（漏换算）')
    key0 = ('l1c_20261021', 0)
    r0 = mat[key0]
    edge_ms = [x * 1000.0 for x in r0['et']]
    idxs = set(bisect.bisect_left(edge_ms, ti) - 1 for ti in r0['t_arr'][:2000])
    P('  l1c/w0 前 2000 样本的归属帧索引集合 = %s（全部落入 ≤1 个组 ⇒ 30 格空档列无从产生，结构性不可能）'
      % sorted(idxs)[:5])
    P('')

    # ================= C27 次大 × 错位复合 =================
    P('[C27] 复合：次大 gap × 时间后继错位（57 组合扫描未覆盖「定义×错位」交叉）')
    rows27 = {}
    for key in WINDOWS:
        r = mat[key]
        fids = r['fids']; n = r['n']; mg2 = r['mg2']
        s27 = {}
        for i in range(n - 1):
            if fids[i + 1] in mg2:
                s27[fids[i]] = mg2[fids[i + 1]]
        rows27[key] = thirds_g(key, s27)
    run('C27 次大×后继错位', rows27)
    P('')

    # ================= C28 帧内中位 gap（定义替换的 level 探针） =================
    P('[C28] 空档定义替换：帧内相邻差「中位」(非最大)、min、span（level 探针，correct 配对）')
    rows28a = {}; rows28b = {}; rows28c = {}
    for key in WINDOWS:
        r = mat[key]
        rows28a[key] = thirds_g(key, r['medg'])
        rows28b[key] = thirds_g(key, r['mingap'])
        rows28c[key] = thirds_g(key, r['span'])
    run('C28a 帧内中位gap', rows28a)
    run('C28b 帧内mingap', rows28b)
    run('C28c 帧内span', rows28c)
    P('')

    # ================= C29 k 用全帧数 =================
    P('[C29] k 分母错位：k = 全帧数//3（含无 dur 末帧）')
    rows29a = {}; rows29b = {}
    for key in WINDOWS:
        r = mat[key]
        nf = r['n']
        k29 = nf // 3
        rows29a[key] = thirds_g(key, r['mg'], k_override=k29)
        rows29b[key] = thirds_g(key, fwd_all[key], k_override=k29)
    run('C29a k=全帧数//3 正确配对', rows29a)
    run('C29b k=全帧数//3 + C8a', rows29b)
    P('')

    # ================= C30 跨窗记录泄漏 =================
    P('[C30] 跨窗泄漏：窗 w 记录列表混入 w-1 末条 / 丢自家首条（correct 配对）')
    rows30a = {}; rows30b = {}
    for trip in TRIPS:
        for w in (0, 1, 2):
            key = (trip, w)
            r = mat[key]
            dm = r['dur']
            ids = sorted([f for f in r['fids'] if f in dm], key=lambda x: (dm[x], x))
            if w > 0:
                rprev = mat[(trip, w - 1)]
                fprev = rprev['fids']
                foreign = fprev[len(fprev) - 2]
                ids2 = [foreign] + ids
                dm2 = dict(dm); dm2[foreign] = rprev['dur'][foreign]
                g2 = dict(r['mg']); g2[foreign] = rprev['mg'][foreign]
                rows30a[key] = thirds_g(key, g2, durmap=dm2, ids_override=ids2)
            else:
                rows30a[key] = thirds_g(key, r['mg'])
            ids3 = ids[1:]
            rows30b[key] = thirds_g(key, r['mg'], ids_override=ids3)
    run('C30a 混入w-1末条', rows30a)
    run('C30b 丢自家首条', rows30b)
    P('')

    # ================= C31 groups dict 未重置（跨窗/跨趟键共享合并） =================
    P('[C31] groups dict 未重置：全局 fid 键在窗/趟间共享 ⇒ 共享帧样本合并（mg 被跨窗间隔毒化）')
    rows31a = {}; rows31b = {}
    # a: trip 内三窗共用一个 dict
    for trip in TRIPS:
        acc = {}
        for w in (0, 1, 2):
            key = (trip, w)
            r = mat[key]
            for fi, ti in zip(r['f_arr'], r['t_arr']):
                acc.setdefault(fi, []).append(ti)
            mg31 = {}
            for fid in r['fids']:
                v = maxgap_of(acc.get(fid, []))
                if v is not None:
                    mg31[fid] = v
            rows31a[key] = thirds_g(key, mg31)
    # b: 15 窗共用一个 dict
    acc = {}
    for trip, w in WINDOWS:
        key = (trip, w)
        r = mat[key]
        for fi, ti in zip(r['f_arr'], r['t_arr']):
            acc.setdefault(fi, []).append(ti)
        mg31 = {}
        for fid in r['fids']:
            v = maxgap_of(acc.get(fid, []))
            if v is not None:
                mg31[fid] = v
        rows31b[key] = thirds_g(key, mg31)
    run('C31a trip内dict不重置', rows31a)
    run('C31b 全局dict不重置', rows31b)
    P('')

    # ================= C33 丢首帧正确配对（稳健性探针） =================
    P('[C33] 稳健性探针：correct 配对但帧集丢首帧（时长列对 ±1 帧是否敏感）')
    rows33 = {}
    for key in WINDOWS:
        r = mat[key]
        ids = r['fids'][1:r['n'] - 1]
        rows33[key] = thirds_g(key, r['mg'], ids_override=ids)
    run('C33 丢首帧+correct', rows33)
    P('')

    # ================= C35 浮点累积（cumsum）类 =================
    P('[C35] 浮点累积类：时长键累计值 / 空档用帧内跨度')
    rows35a = {}; rows35b = {}
    for key in WINDOWS:
        r = mat[key]
        fids = r['fids']; n = r['n']; et = r['et']
        dcum = {fids[i]: et[i + 1] - et[0] for i in range(n - 1)}
        rows35a[key] = thirds_g(key, r['mg'], durmap=dcum)
        rows35b[key] = thirds_g(key, r['span'])
    run('C35a dur=累计值键', rows35a)
    run('C35b gap=帧内span', rows35b)
    P('')

    # ================= 诊断 =================
    P('[诊断1] 时长排序在 k 边界是否存在精确并列（tie-break 自由度）')
    any_tie = 0
    for key in WINDOWS:
        r = mat[key]
        dm = r['dur']
        ids = sorted([f for f in r['fids'] if f in dm], key=lambda x: (dm[x], x))
        k = len(ids) // 3
        tie_lo = dm[ids[k - 1]] == dm[ids[k]]
        tie_hi = dm[ids[len(ids) - k - 1]] == dm[ids[len(ids) - k]]
        any_tie += tie_lo or tie_hi
    P('  k 边界存在精确 dur 并列的窗数 = %d/15' % any_tie)
    P('')
    P('[诊断2] C8a 与正确配对的逐帧挂接差异量（错位是否「全帧生效」）')
    for key in WINDOWS[:3]:
        r = mat[key]
        fwd = fwd_all[key]
        diff_frames = sum(1 for f in r['fids'] if fwd[f] != r['mg'][f])
        P('  %-16s 挂接值 ≠ 自身值的帧数 = %d/%d' % (key[0] + '/w' + str(key[1]), diff_frames, r['n']))
    P('')
    P('[_ex_candidates] END')

    with safe_open(OUT_REL, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(out_lines) + '\n')

if __name__ == '__main__':
    main()
