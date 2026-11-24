# -*- coding: utf-8 -*-
# _ex_rebuild_c8a.py —— 排他性检验·第一步：独立重建 C8a 并核对 15 diff + 75 格
# 独立实现（不复用上一轮探针代码）：直读语料 JSON，按台账 :9702-9703 口径 + 数据钉死项（edge 时长、k=n//3、median）。
# C8a 定义：每帧挂接其时间后继帧的帧内最大空档（= 时长列表与 maxgap 列表错一帧对齐），时长列仍 edge 三分。
# 写域 = lead/s604_exclusive_20261109/。零真机、零采样代码。python -I -X utf8
import json, os, statistics

BASE = os.path.normpath('D:/Project/ra2-campaign-forge')
CORPUS_REL = ('out', 're_work', 'work_chain', 'CONTINUE_20261003', 'lead', 'qc161_u0400_trip')
OUT_REL = ('lead', 's604_exclusive_20261109', '_ex_rebuild_c8a_out.txt')

TRIPS = ['l1c_20261021', 'l1d_20261021', 'l1e_20261021', 'l3_20261021', 't55k_20261020']
WINDOWS = [(t, w) for t in TRIPS for w in (0, 1, 2)]

# 台账 :9706-9720 表值（快dur, 快gap, 慢dur, 慢gap, diff）——本任务自台账实读转写（U+2212 归一为 ASCII -）
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

# 任务书给出的上一轮 C8a diff 值（15 个，4 位小数）
TASK_DIFFS = [0.0315, 0.0275, 0.0300, 0.0490, 0.0220, 0.0245, 0.0030, 0.0350, 0.0180,
              -0.0020, 0.0370, 0.0020, -0.0130, -0.0060, -0.0005]

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

def main():
    # ---- 载入语料，独立实现逐帧统计 ----
    per = {}
    for trip, w in WINDOWS:
        with safe_open(list(CORPUS_REL) + [trip, 'measure_w%d.json' % w]) as fh:
            d = json.loads(fh.read().decode('utf-8'))
        edges = d['frame_edges']
        fids = [e[0] for e in edges]                      # 时间序
        et = [e[1] for e in edges]
        groups = {}
        for fi, ti in zip(d['samples']['f'], d['samples']['t']):
            groups.setdefault(fi, []).append(ti)
        dur = {}                                          # edge 口径：E[i+1]-E[i]，末帧无
        mg = {}                                           # 帧内相邻 t 差最大值
        for i, fid in enumerate(fids):
            if i + 1 < len(fids):
                dur[fid] = et[i + 1] - et[i]
            ts = sorted(groups.get(fid, []))
            if len(ts) >= 2:
                gaps = [ts[j + 1] - ts[j] for j in range(len(ts) - 1)]
                mg[fid] = max(gaps)
        per[(trip, w)] = dict(fids=fids, dur=dur, mg=mg)

    def thirds(key, gmap):
        """按 (edge 时长, fid) 升序取 k=n//3 前/后段；gmap 给每帧的空档值。返回 (fd,fg,sd,sg,diff) 单位 ms。"""
        r = per[key]
        ids = sorted([f for f in r['fids'] if f in r['dur'] and f in gmap],
                     key=lambda x: (r['dur'][x], x))
        n = len(ids); k = n // 3
        fd = med([r['dur'][i] for i in ids[:k]]) * 1000.0
        sd = med([r['dur'][i] for i in ids[n - k:]]) * 1000.0
        fg = med([gmap[i] for i in ids[:k]]) * 1000.0
        sg = med([gmap[i] for i in ids[n - k:]]) * 1000.0
        return fd, fg, sd, sg, sg - fg

    # ---- [1] 真值基线（正确配对）----
    P('[1] 真值基线（edge + k=n//3 + maxgap + median，独立实现）')
    true_rows = {}
    for key in WINDOWS:
        fd, fg, sd, sg, diff = thirds(key, per[key]['mg'])
        true_rows[key] = (fd, fg, sd, sg, diff)
    for key in WINDOWS:
        fd, fg, sd, sg, diff = true_rows[key]
        P('  %-16s fd=%7.4f fg=%6.4f sd=%7.4f sg=%6.4f diff=%s' % (key[0] + '/w' + str(key[1]), fd, fg, sd, sg, f3(diff)))
    P('')

    # ---- [2] C8a wrap 变体：每帧挂时间后继的 mg，末帧回绕自身 ----
    P('[2] C8a-wrap（帧 i ← mg(帧 i+1)，末帧回绕自身）')
    c8a_rows = {}
    for key in WINDOWS:
        r = per[key]
        tids = r['fids']
        fwd = {}
        for i in range(len(tids) - 1):
            fwd[tids[i]] = r['mg'][tids[i + 1]]
        fwd[tids[-1]] = r['mg'][tids[-1]]
        fd, fg, sd, sg, diff = thirds(key, fwd)
        c8a_rows[key] = (fd, fg, sd, sg, diff)
    for key in WINDOWS:
        fd, fg, sd, sg, diff = c8a_rows[key]
        P('  %-16s fd=%7.4f fg=%6.4f sd=%7.4f sg=%6.4f diff=%s' % (key[0] + '/w' + str(key[1]), fd, fg, sd, sg, f3(diff)))
    P('')

    # ---- [3] 与任务书 15 个 diff 值逐个核对（4 位小数）----
    P('[3] C8a-wrap diff vs 任务书 15 值')
    n_match = 0
    for idx, key in enumerate(WINDOWS):
        diff = c8a_rows[key][4]
        ok = abs(diff - TASK_DIFFS[idx]) < 0.00005
        n_match += ok
        P('  %-16s 本轮=%.4f 任务书=%+.4f %s' % (key[0] + '/w' + str(key[1]), diff, TASK_DIFFS[idx],
          'MATCH' if ok else 'MISMATCH'))
    P('  15 值核对: %d/15' % n_match)
    P('')

    # ---- [4] 75 格判定（时长列 round1 30 + 空档列 round2 30 + 差列 round3 15）----
    P('[4] C8a-wrap 75 格判定（round 判等：dur 1 位 / gap 2 位 / diff 3 位小数）+ 容差判等')
    rd = rg = rdiff = 0
    gh = dh = 0
    for key in WINDOWS:
        fd, fg, sd, sg, diff = c8a_rows[key]
        td = TABLE[key]
        rd += round(fd, 1) == td[0]; rd += round(sd, 1) == td[2]
        rg += round(fg, 2) == td[1]; rg += round(sg, 2) == td[3]
        rdiff += round(diff, 3) == td[4]
        gh += abs(fg - td[1]) < 0.005; gh += abs(sg - td[3]) < 0.005
        dh += abs(diff - td[4]) < 0.0005
    P('  round 判等: 时长列 %d/30, 空档列 %d/30, 空档差列 %d/15  → 75 格合计 %d/75' % (rd, rg, rdiff, rd + rg + rdiff))
    P('  容差判等: 空档列 %d/30, 差列 %d/15' % (gh, dh))
    P('')

    # ---- [5] C8a-zip 变体（帧0..n-2 的时长配帧1..n-1 的 maxgap，末帧整体出局）与 wrap 逐位比较 ----
    P('[5] C8a-zip（zip 截断：末帧出局）vs C8a-wrap 逐位比较')
    all_same = True
    for key in WINDOWS:
        r = per[key]
        fids = r['fids']
        n = len(fids)
        ids = sorted([fids[i] for i in range(n - 1) if fids[i] in r['mg']],
                     key=lambda x: (r['dur'][x], x))
        k = len(ids) // 3
        # zip 语义：帧 i 的记录 = (dur(fids[i]), mg(fids[i+1]))，i=0..n-2；末帧无记录
        zdur = {fids[i]: r['dur'][fids[i]] for i in range(n - 1)}
        zmg = {fids[i]: r['mg'][fids[i + 1]] for i in range(n - 1)}
        zids = sorted(zdur.keys(), key=lambda x: (zdur[x], x))
        zk = len(zids) // 3
        m = len(zids)                                # 截断后记录数（n-1），切片须用 m 而非 n
        zfd = med([zdur[i] for i in zids[:zk]]) * 1000.0
        zsd = med([zdur[i] for i in zids[m - zk:]]) * 1000.0
        zfg = med([zmg[i] for i in zids[:zk]]) * 1000.0
        zsg = med([zmg[i] for i in zids[m - zk:]]) * 1000.0
        wfd, wfg, wsd, wsg, wdiff = c8a_rows[key]
        same = (zfd == wfd and zfg == wfg and zsd == wsd and zsg == wsg and (zsg - zfg) == wdiff)
        all_same = all_same and same
        P('  %-16s zip-vs-wrap 逐位相同=%s  zip diff=%s' % (key[0] + '/w' + str(key[1]), same, f3(zsg - zfg)))
    P('  全 15 窗逐位相同: %s' % all_same)
    P('')

    # ---- [6] 方向签名（对真值）----
    P('[6] 方向签名（台账两列相对真值）')
    pos_dfg = neg_dsg = negdiff = 0
    for key in WINDOWS:
        td = TABLE[key]
        fd, fg, sd, sg, diff = c8a_rows[key]
        pos_dfg += (td[1] - fg) > 0
        neg_dsg += (td[3] - sg) < 0
        negdiff += diff < 0
    P('  台账快列 > C8a快列: %d/15   台账慢列 < C8a慢列: %d/15   C8a 负diff 窗数: %d' % (pos_dfg, neg_dsg, negdiff))
    pos_dfg_t = neg_dsg_t = 0
    for key in WINDOWS:
        td = TABLE[key]
        fd, fg, sd, sg, diff = true_rows[key]
        pos_dfg_t += (td[1] - fg) > 0
        neg_dsg_t += (td[3] - sg) < 0
    P('  台账快列 > 真值快列: %d/15   台账慢列 < 真值慢列: %d/15' % (pos_dfg_t, neg_dsg_t))
    P('')

    # ---- [7] -114.8 指纹 ----
    P('[7] -114.8 指纹（x=(窗名,fd,fg,sd,sg) 读法，median(sg-sd)）')
    a = med([true_rows[k][3] - true_rows[k][2] for k in WINDOWS])
    b = med([TABLE[k][3] - TABLE[k][2] for k in WINDOWS])
    P('  主口径实算值: median(sg-sd) = %.4f' % a)
    P('  台账表值    : median(sg-sd) = %.4f' % b)
    P('')
    P('[_ex_rebuild_c8a] END')

    with safe_open(OUT_REL, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(out_lines) + '\n')

if __name__ == '__main__':
    main()
