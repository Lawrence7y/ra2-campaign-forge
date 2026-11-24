# -*- coding: utf-8 -*-
# _exv_rebuild.py —— 排他性复核·独立重建 C8a 基准（复核员独立实现，不复用撰写人/上一轮代码）
# 独立性要点：
#   (a) TABLE 不采信任何转写常量，直接从台账 §604 表行（GOAL_THREE_TARGETS_20261018.md :9706-9720）解析；
#   (b) 算法口径按台账 :9702-9703 文本 + R3 蓝本注释自行实现；
#   (c) 15 个 diff 值的锚 = 保护区在盘件 _sg_probe_shift_out.txt [C12] 列（上一轮实跑输出，本轮实读转录）。
# 只读语料；唯一写域 = lead/s604_exclusive_20261109/（本件输出 _exv_rebuild_out.txt）。
# 零真机、零采样代码。python -I -X utf8
import json, os, re, statistics
from bisect import bisect_right

BASE = os.path.normpath('D:/Project/ra2-campaign-forge')
CORPUS_REL = ('out', 're_work', 'work_chain', 'CONTINUE_20261003', 'lead', 'qc161_u0400_trip')
OUT_REL = ('lead', 's604_exclusive_20261109', '_exv_rebuild_out.txt')
LEDGER_REL = ('lead', 'GOAL_THREE_TARGETS_20261018.md')

TRIPS = ['l1c_20261021', 'l1d_20261021', 'l1e_20261021', 'l3_20261021', 't55k_20261020']
WINDOWS = [(t, w) for t in TRIPS for w in (0, 1, 2)]

# R3 蓝本 _r3_recompute_gapdiff.py:20-36 的 TABLE 常量（本轮实读转录，作解析交叉核对用）
R3_TABLE = {
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
# 上一轮在盘输出 _sg_probe_shift_out.txt [C12] 的 C8a 列 15 值（本轮实读转录，作 diff 锚）
C12_ANCHOR = [0.0315, 0.0275, 0.0300, 0.0490, 0.0220, 0.0245, 0.0030, 0.0350, 0.0180,
              -0.0020, 0.0370, 0.0020, -0.0130, -0.0060, -0.0005]

out_lines = []
def P(s=''):
    out_lines.append(s)
    print(s)

def f4(x):
    return ('+' if x >= 0 else '-') + ('%.4f' % abs(x))

def safe_open(rel_parts, mode='rb', **kw):
    rp = os.path.normpath(os.path.abspath(os.path.join(BASE, *rel_parts)))
    if not (rp == BASE or rp.startswith(BASE + os.sep)):
        raise PermissionError('path outside BASE: ' + rp)
    return open(rp, mode, **kw)

def parse_ledger_table():
    """从台账原文解析 §604 表值（:9700-9725 区间内、形如 | `trip/wN` | … 的行）。"""
    with safe_open(LEDGER_REL, 'r', encoding='utf-8') as fh:
        lines = fh.read().splitlines()
    tbl = {}
    rows = []
    for i, ln in enumerate(lines):
        if not (9700 <= i + 1 <= 9725):
            continue
        m = re.match(r'^\|\s*`([A-Za-z0-9_]+)/w([0-2])`\s*\|', ln)
        if not m:
            continue
        cells = [c.strip() for c in ln.split('|')[1:-1]]
        if len(cells) != 6:
            continue
        def num(c):
            c = c.replace('**', '').replace('`', '').replace('ms', '').strip()
            c = c.replace('\u2212', '-')          # U+2212 → ASCII -
            if c.startswith('+'):
                c = c[1:]
            return float(c)
        key = (m.group(1), int(m.group(2)))
        tbl[key] = (num(cells[1]), num(cells[2]), num(cells[3]), num(cells[4]), num(cells[5]))
        rows.append(i + 1)
    return tbl, rows

def med(v):
    return statistics.median(v)

def main():
    TABLE, row_lines = parse_ledger_table()
    P('[0] 台账 §604 表值直读（解析自 GOAL_THREE_TARGETS_20261018.md :9706-9720 表行）')
    P('    解析到行号: %s' % row_lines)
    n_eq = sum(1 for k in WINDOWS if TABLE[k] == R3_TABLE[k])
    P('    与 R3 蓝本常量逐键相等: %d/15 （U+2212 归一为 ASCII -）' % n_eq)
    P('')

    # ---- 载入语料，独立实现逐帧统计 ----
    win = {}
    for trip, w in WINDOWS:
        rel = list(CORPUS_REL) + [trip, 'measure_w%d.json' % w]
        with safe_open(rel, 'rb') as fh:
            d = json.loads(fh.read().decode('utf-8'))
        edges = d['frame_edges']
        fids = [e[0] for e in edges]
        et = [e[1] for e in edges]
        tlist = d['samples']['t']
        flist = d['samples']['f']
        groups = {}
        for fi, ti in zip(flist, tlist):
            groups.setdefault(fi, []).append(ti)
        dur, mg, nsamp = {}, {}, {}
        for i, fid in enumerate(fids):
            ts = sorted(groups.get(fid, []))
            nsamp[fid] = len(ts)
            if len(ts) >= 2:
                mg[fid] = max(ts[j + 1] - ts[j] for j in range(len(ts) - 1))
            if i + 1 < len(fids):
                dur[fid] = et[i + 1] - et[i]
        fwd = {}
        for i in range(len(fids) - 1):
            fwd[fids[i]] = mg[fids[i + 1]]
        fwd[fids[-1]] = mg[fids[-1]]                    # wrap（末帧本被 dur 过滤出局）
        ids = sorted([f for f in fids if f in dur and f in mg], key=lambda x: (dur[x], x))
        win[(trip, w)] = dict(fids=fids, et=et, dur=dur, mg=mg, nsamp=nsamp, fwd=fwd, ids=ids,
                              n_samp=len(tlist), tlist=tlist, flist=flist)

    def agg(key, gmap, medop=None, kf=None, ks=None, durmap=None, swap=False):
        r = win[key]
        ids = r['ids']
        n = len(ids)
        k = n // 3
        kf = k if kf is None else kf
        ks = k if ks is None else ks
        medop = med if medop is None else medop
        dm = r['dur'] if durmap is None else durmap
        fd = medop([dm[i] for i in ids[:kf]]) * 1000.0
        sd = medop([dm[i] for i in ids[n - ks:]]) * 1000.0
        fg = medop([gmap[i] for i in ids[:kf]]) * 1000.0
        sg = medop([gmap[i] for i in ids[n - ks:]]) * 1000.0
        if swap:
            return sd, sg, fd, fg, fg - sg
        return fd, fg, sd, sg, sg - fg

    def score75(rows, label):
        rd = rg = rdiff = gh = dh = 0
        bad = []
        for key in WINDOWS:
            fd, fg, sd, sg, diff = rows[key]
            td = TABLE[key]
            if round(fd, 1) != td[0]: bad.append('%s/w%d:fd' % (key[0][:4], key[1]))
            if round(fg, 2) != td[1]: bad.append('%s/w%d:fg' % (key[0][:4], key[1]))
            if round(sd, 1) != td[2]: bad.append('%s/w%d:sd' % (key[0][:4], key[1]))
            if round(sg, 2) != td[3]: bad.append('%s/w%d:sg' % (key[0][:4], key[1]))
            if round(diff, 3) != td[4]: bad.append('%s/w%d:diff' % (key[0][:4], key[1]))
            rd += round(fd, 1) == td[0]; rd += round(sd, 1) == td[2]
            rg += round(fg, 2) == td[1]; rg += round(sg, 2) == td[3]
            rdiff += round(diff, 3) == td[4]
            gh += abs(fg - td[1]) < 0.005; gh += abs(sg - td[3]) < 0.005
            dh += abs(diff - td[4]) < 0.0005
        P('  %-24s | round: dur %2d/30 gap %2d/30 diff %2d/15 (合%2d/75) | 容差: gap %2d/30 diff %2d/15 | 失败格: %s'
          % (label, rd, rg, rdiff, rd + rg + rdiff, gh, dh, ' '.join(bad) if bad else '无'))
        return rd + rg + rdiff

    # ---- [1] 真值基线 ----
    P('[1] 真值基线（正确配对；fd/fg/sd/sg/diff，单位 ms）')
    true_rows = {key: agg(key, win[key]['mg']) for key in WINDOWS}
    for key in WINDOWS:
        fd, fg, sd, sg, diff = true_rows[key]
        P('  %-16s fd=%7.4f fg=%6.4f sd=%7.4f sg=%6.4f diff=%s' % (key[0] + '/w' + str(key[1]), fd, fg, sd, sg, f4(diff)))
    score75(true_rows, 'C0 真值(正确配对)')
    P('')

    # ---- [2] C8a-wrap ----
    P('[2] C8a（每帧挂时间后继帧 maxgap，末帧回绕；时长列仍 edge 三分）')
    c8a_rows = {key: agg(key, win[key]['fwd']) for key in WINDOWS}
    for key in WINDOWS:
        fd, fg, sd, sg, diff = c8a_rows[key]
        P('  %-16s fd=%7.4f fg=%6.4f sd=%7.4f sg=%6.4f diff=%s' % (key[0] + '/w' + str(key[1]), fd, fg, sd, sg, f4(diff)))
    P('')

    # ---- [3] 15 个 diff 值 vs 上轮在盘锚（_sg_probe_shift_out.txt [C12] C8a 列） ----
    P('[3] C8a diff vs 上轮在盘锚 15 值（[C12] 列）')
    n_match = 0
    for idx, key in enumerate(WINDOWS):
        diff = c8a_rows[key][4]
        ok = abs(diff - C12_ANCHOR[idx]) < 0.00005
        n_match += ok
        P('  %-16s 本轮=%s 锚=%+.4f %s' % (key[0] + '/w' + str(key[1]), f4(diff), C12_ANCHOR[idx],
          'MATCH' if ok else 'MISMATCH'))
    P('  15 值核对: %d/15' % n_match)
    P('')

    # ---- [4] 75 格判定 ----
    P('[4] 75 格判定')
    score75(c8a_rows, 'C8a-wrap')
    P('')

    # ---- [5] zip 截断变体 vs wrap 逐位 ----
    P('[5] C8a-zip（帧0..n-2 配帧1..n-1 的 mg，末帧出局）vs C8a-wrap 逐位比较')
    all_same = True
    for key in WINDOWS:
        r = win[key]
        fids = r['fids']; n = len(fids)
        zdur = {fids[i]: r['dur'][fids[i]] for i in range(n - 1)}
        zmg = {fids[i]: r['mg'][fids[i + 1]] for i in range(n - 1)}
        zids = sorted(zdur.keys(), key=lambda x: (zdur[x], x))
        m = len(zids); zk = m // 3
        zfd = med([zdur[i] for i in zids[:zk]]) * 1000.0
        zsd = med([zdur[i] for i in zids[m - zk:]]) * 1000.0
        zfg = med([zmg[i] for i in zids[:zk]]) * 1000.0
        zsg = med([zmg[i] for i in zids[m - zk:]]) * 1000.0
        wfd, wfg, wsd, wsg, wdiff = c8a_rows[key]
        same = (zfd == wfd and zfg == wfg and zsd == wsd and zsg == wsg and (zsg - zfg) == wdiff)
        all_same = all_same and same
        P('  %-16s zip≡wrap 逐位相同=%s' % (key[0] + '/w' + str(key[1]), same))
    P('  全 15 窗逐位相同: %s' % all_same)
    P('')

    # ---- [6] 方向签名 ----
    P('[6] 方向签名')
    a = sum(1 for key in WINDOWS if TABLE[key][1] - c8a_rows[key][1] > 0)
    b = sum(1 for key in WINDOWS if TABLE[key][3] - c8a_rows[key][3] < 0)
    c = sum(1 for key in WINDOWS if c8a_rows[key][4] < 0)
    a2 = sum(1 for key in WINDOWS if TABLE[key][1] - true_rows[key][1] > 0)
    b2 = sum(1 for key in WINDOWS if TABLE[key][3] - true_rows[key][3] < 0)
    P('  对 C8a: 台账快列>C8a快列 %d/15, 台账慢列<C8a慢列 %d/15, C8a 负diff %d 窗' % (a, b, c))
    P('  对真值: 台账快列>真值 %d/15, 台账慢列<真值 %d/15' % (a2, b2))
    P('')

    # ---- [7] -114.8 指纹 ----
    P('[7] -114.8 指纹（x=(窗名,fd,fg,sd,sg) 读法 → median(sg-sd)）')
    v_true = med([true_rows[k][3] - true_rows[k][2] for k in WINDOWS])
    v_tbl = med([TABLE[k][3] - TABLE[k][2] for k in WINDOWS])
    P('  真值基线: median(sg-sd) = %.4f' % v_true)
    P('  台账表值: median(sg-sd) = %.4f' % v_tbl)
    P('')

    # ---- [8] C13c 同类码形：样本→帧归属 bisect_right-2 重推导 ----
    P('[8] C13c 码形（不用语料 f：j = bisect_right(et, t) - 2；组 j = 帧 j+1 样本）')
    all13 = True
    for key in WINDOWS:
        r = win[key]
        et = r['et']
        g = {}
        for t in r['tlist']:
            g.setdefault(bisect_right(et, t) - 2, []).append(t)
        mg13 = {}
        for j, ts in g.items():
            if j < 0:
                continue
            ts = sorted(ts)
            if len(ts) >= 2:
                mg13[j] = max(ts[q + 1] - ts[q] for q in range(len(ts) - 1))
        # 组 j 应恰为帧 j+1 的全体样本；帧 0 样本应落入组 -1
        fids = r['fids']; n = len(fids)
        byf = {}
        for ff, tt in zip(r['flist'], r['tlist']):
            byf.setdefault(ff, []).append(tt)
        grp_ok = True
        for j in range(0, n - 1):
            if sorted(g.get(j, [])) != sorted(byf[fids[j + 1]]):
                grp_ok = False
                break
        n0 = len(byf[fids[0]])
        grp_m1 = (len(g.get(-1, [])) == n0)
        # 帧序取组值：帧 fids[i] 的组 = 组 i（= 帧 i+1 的样本）⇒ 挂接值 = 后继帧 mg（与 C8a 同一映射）
        gmap13 = {fids[i]: mg13[i] for i in range(n) if i in mg13}
        fd, fg, sd, sg, diff = agg(key, gmap13)
        wr = c8a_rows[key]
        same = (fd == wr[0] and fg == wr[1] and sd == wr[2] and sg == wr[3] and diff == wr[4])
        all13 = all13 and same and grp_ok and grp_m1
        P('  %-16s 组=后继帧全体样本=%s 帧0样本入组-1=%s 五元组逐位相同=%s' % (key[0] + '/w' + str(key[1]), grp_ok, grp_m1, same))
    P('  全 15 窗: %s' % all13)
    P('')

    # ---- [9] 语料结构事实（候选构造依据） ----
    P('[9] 语料结构事实（独立实测）')
    for key in WINDOWS:
        r = win[key]
        fids = r['fids']
        consec = all(fids[i + 1] - fids[i] == 1 for i in range(len(fids) - 1))
        et_sorted = all(r['et'][i] <= r['et'][i + 1] for i in range(len(r['et']) - 1))
        ids = r['ids']; n = len(ids); k = n // 3; dm = r['dur']
        tie_fast = dm[ids[k - 1]] == dm[ids[k]]
        tie_slow = dm[ids[n - k - 1]] == dm[ids[n - k]]
        nsv = sorted(r['nsamp'].values())
        P('  %-16s n_ids=%3d k=%3d fid连续=%s edges按t升序=%s 快边界dur并列=%s 慢边界dur并列=%s 帧样本数min/med/max=%d/%d/%d'
          % (key[0] + '/w' + str(key[1]), n, k, consec, et_sorted, tie_fast, tie_slow,
             nsv[0], nsv[len(nsv) // 2], nsv[-1]))
    P('')
    P('[_exv_rebuild] END')

    with safe_open(OUT_REL, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(out_lines) + '\n')
    print('WRITTEN: ' + OUT_REL[-1])

if __name__ == '__main__':
    main()
