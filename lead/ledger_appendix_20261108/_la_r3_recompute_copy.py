# -*- coding: utf-8 -*-
# _r3_recompute_gapdiff.py —— R3 第二方独立复算：§604 快/慢 1/3 空档差（不复用 N-8 实现，仅读语料）
# 口径（本脚本自定义，对应台账 :9703「每窗按帧时长排序，取最快 1/3 与最慢 1/3，各自算帧内最大空档的中位」）：
#   帧分组：samples.f 相同 = 同帧；帧内 t 排序后取相邻差的最大值 = 帧内最大空档（maxgap）。
#   帧时长主口径 = edge：frame_edges 相邻起点差 t[i+1]-t[i]（末帧无下沿，剔除）；敏感口径 = span：帧内 max(t)-min(t)。
#   三分：按帧时长升序，k = n//3（主）/ ceil（敏感），前 k = 快1/3，后 k = 慢1/3。
#   中位 = statistics.median（偶数取中间两值均值）。空档差 = 慢1/3 maxgap 中位 − 快1/3 maxgap 中位。
import json, hashlib, statistics, math, sys, io

BASE = 'D:/Project/ra2-campaign-forge'
CORPUS = BASE + '/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip'
OUT = BASE + '/lead/ledger_appendix_20261108/_la_r3_recompute_out.txt'
N8 = BASE + '/lead/slowwindow_n8_20261108/SLOW_WINDOW_LIMITS.md'
GOAL = BASE + '/lead/GOAL_THREE_TARGETS_20261018.md'

TRIPS = ['l1c_20261021', 'l1d_20261021', 'l1e_20261021', 'l3_20261021', 't55k_20261020']
WINDOWS = [(t, w) for t in TRIPS for w in (0, 1, 2)]

# 台账 :9706-9720 表值（fast_dur, fast_gap, slow_dur, slow_gap, diff），负号按显示值录入
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

def f3(x):  # 带符号四位小数（空档差用）
    s = '+' if x >= 0 else '-'
    return f'{s}{abs(x):.4f}'

def f2(x):
    s = '+' if x >= 0 else '-'
    return f'{s}{abs(x):.2f}'

def sha256_file(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()

out_lines = []
def P(s=''):
    out_lines.append(s)
    print(s)

def main():
    P('[_r3] R3 第二方独立复算 —— §604 快/慢 1/3 空档差（独立实现，仅读语料）')
    P('被核对象: ' + N8)
    P('被核对象 SHA256 = ' + sha256_file(N8) + '，字节数 = ' + str(len(open(N8, "rb").read())))
    P('台账(只读): ' + GOAL + ' SHA256 = ' + sha256_file(GOAL) +
      '，字节数 = ' + str(len(open(GOAL, "rb").read())))
    P('口径: 帧时长主口径=edge(t[i+1]-t[i])，敏感口径=span(帧内max-min)；三分 k=n//3 主 / ceil 敏感；'
      '帧内最大空档=帧内相邻采样 t 差最大值；中位=statistics.median；空档差=慢1/3中位-快1/3中位')
    P('')

    per_win = {}
    for trip, w in WINDOWS:
        path = f'{CORPUS}/{trip}/measure_w{w}.json'
        raw = open(path, 'rb').read()
        sha = hashlib.sha256(raw).hexdigest()
        d = json.loads(raw.decode('utf-8'))
        t = d['samples']['t']; f = d['samples']['f']
        edges = d['frame_edges']
        gate = d.get('gate') or {}; w1 = d.get('w1') or {}
        n_samp = len(t)
        mono_f = all(f[i] <= f[i + 1] for i in range(n_samp - 1))
        mono_t = all(t[i] <= t[i + 1] for i in range(n_samp - 1))
        extra_f = sorted(set(f) - {e[0] for e in edges})

        groups = {}
        for fi, ti in zip(f, t):
            groups.setdefault(fi, []).append(ti)
        frame_ids = [e[0] for e in edges]
        edge_t = {e[0]: e[1] for e in edges}
        n_frames = len(frame_ids)

        dur_edge = {}; dur_span = {}; maxgap = {}; n_no2 = 0
        for i, fid in enumerate(frame_ids):
            ts = groups.get(fid, [])
            if len(ts) >= 2:
                maxgap[fid] = max(ts[j + 1] - ts[j] for j in range(len(ts) - 1))
            else:
                n_no2 += 1
            dur_span[fid] = (max(ts) - min(ts)) if ts else None
            if i + 1 < n_frames:
                dur_edge[fid] = edge_t[frame_ids[i + 1]] - edge_t[fid]

        def thirds(dur_map, k_rule):
            ids = sorted([fid for fid in frame_ids if dur_map.get(fid) is not None],
                         key=lambda x: (dur_map[x], x))
            n = len(ids)
            k = n // 3 if k_rule == 'floor' else math.ceil(n / 3)
            fast, slow = ids[:k], ids[n - k:]
            # 语料 t 单位 = 秒 ⇒ ×1000 转 ms 后再统计（台账表值单位 = ms）
            fd = statistics.median([dur_map[i] for i in fast]) * 1000.0
            sd = statistics.median([dur_map[i] for i in slow]) * 1000.0
            fg = statistics.median([maxgap[i] for i in fast if i in maxgap]) * 1000.0
            sg = statistics.median([maxgap[i] for i in slow if i in maxgap]) * 1000.0
            return fd, fg, sd, sg, sg - fg, k, n

        variants = {}
        for dname, dmap in (('edge', dur_edge), ('span', dur_span)):
            for krule in ('floor', 'ceil'):
                variants[(dname, krule)] = thirds(dmap, krule)

        per_win[(trip, w)] = dict(path=path, sha=sha, gate=gate, w1=w1, hz=d.get('hz'),
                                  span_s=d.get('span_s'), n_samp=n_samp, n_frames=n_frames,
                                  mono_f=mono_f, mono_t=mono_t, extra_f=extra_f, n_no2=n_no2,
                                  med_edge_all=statistics.median([dur_edge[i] for i in dur_edge]),
                                  med_span_all=statistics.median([v for v in dur_span.values() if v is not None]),
                                  variants=variants)

    # —— [A] 语料体检 ——
    P('[A] 15 窗语料体检（gate/verdict/单调性/帧数/样本数/文件指纹）')
    for (trip, w), r in per_win.items():
        P(f"  {trip}/w{w}: hz={r['hz']} span_s={r['span_s']} n_samp={r['n_samp']} n_frames={r['n_frames']} "
          f"f单调={r['mono_f']} t单调={r['mono_t']} 无样本帧={r['n_no2']} f越界={len(r['extra_f'])} "
          f"gate.ok={r['gate'].get('ok')} w1.verdict={r['w1'].get('verdict')}/{r['w1'].get('valid')} "
          f"med_edge_all={r['med_edge_all']*1000:.2f}ms med_span_all={r['med_span_all']*1000:.2f}ms")
        P(f"    sha256={r['sha']} bytes={len(open(r['path'],'rb').read())}")
    P('')

    # —— [B] 主口径（edge+floor）逐窗结果 vs 台账 :9706-9720 逐格比对 ——
    P('[B] 主口径（edge + k=n//3）逐窗复算 vs 台账表值（容差: dur<0.05, gap<0.005, diff<0.0005）')
    P('  window            | 复算: 快dur/快gap/慢dur/慢gap/差          | 台账表值同序          | 命中(fd,fg,sd,sg,diff)')
    dur_hit = gap_hit = diff_hit = 0
    for key in WINDOWS:
        fd, fg, sd, sg, diff, k, n = per_win[key]['variants'][('edge', 'floor')]
        td = TABLE[key]
        hits = []
        for calc, ref, tol in ((fd, td[0], 0.05), (fg, td[1], 0.005), (sd, td[2], 0.05),
                               (sg, td[3], 0.005), (diff, td[4], 0.0005)):
            hits.append(abs(calc - ref) < tol)
        dur_hit += hits[0] + hits[2]; gap_hit += hits[1] + hits[3]; diff_hit += hits[4]
        P(f'  {key[0]}/w{key[1]}'.ljust(20) +
          f'| {fd:7.4f} {fg:6.4f} {sd:7.4f} {sg:6.4f} {f3(diff)} '.ljust(50) +
          f'| {td[0]:6.1f} {td[1]:5.2f} {td[2]:6.1f} {td[3]:5.2f} {f3(td[4])} '.ljust(38) +
          f'| {hits[0]},{hits[1]},{hits[2]},{hits[3]},{hits[4]}')
    P(f'  计数: 时长列命中 {dur_hit}/30, 空档列命中 {gap_hit}/30, 空档差列命中 {diff_hit}/15')
    P('')

    # —— [B2] 舍入到台账显示精度后判等（dur 1 位/gap 2 位/diff 3 位小数 round 后相等） ——
    P('[B2] 舍入判等（round(复算,显示位数) == 台账表值）')
    rd = rg = rdiff = 0
    for key in WINDOWS:
        fd, fg, sd, sg, diff, k, n = per_win[key]['variants'][('edge', 'floor')]
        td = TABLE[key]
        rd += round(fd, 1) == td[0]; rd += round(sd, 1) == td[2]
        rg += round(fg, 2) == td[1]; rg += round(sg, 2) == td[3]
        rdiff += round(diff, 3) == td[4]
    P(f'  round 判等: 时长列 {rd}/30, 空档列 {rg}/30, 空档差列 {rdiff}/15')
    P('')

    # —— [C] 敏感性：4 组口径下的空档差逐窗值 ——
    P('[C] 敏感性（4 组口径 × 15 窗空档差）')
    for combo in (('edge', 'floor'), ('edge', 'ceil'), ('span', 'floor'), ('span', 'ceil')):
        diffs = [per_win[k]['variants'][combo][4] for k in WINDOWS]
        P(f"  {combo[0]}+{combo[1]}: " + ' '.join(f3(x) for x in diffs))
    P('')

    # —— [D] 汇总：主口径空档差的分布、:9724/:9725 判定 ——
    diffs = [per_win[k]['variants'][('edge', 'floor')][4] for k in WINDOWS]
    dmed = statistics.median(diffs)
    P('[D] 主口径汇总（15 窗空档差）')
    P(f'  中位 = {f3(dmed)}  最小 = {f3(min(diffs))}  最大 = {f3(max(diffs))}')
    P(f'  严格 <0 窗数 = {sum(1 for x in diffs if x < 0)}   <=0（含 -0.000 级零值）窗数 = '
      f'{sum(1 for x in diffs if x <= 0)}   落在 [+0.003,+0.049] 内窗数 = '
      f'{sum(1 for x in diffs if 0.0025 <= x <= 0.0495)}')
    tbl_diffs = [TABLE[k][4] for k in WINDOWS]
    P(f'  台账表值列: 中位 = {f3(statistics.median(tbl_diffs))}  最小 = {f3(min(tbl_diffs))}  '
      f'最大 = {f3(max(tbl_diffs))}')
    P(f'  台账表值严格 <0 窗数 = {sum(1 for x in tbl_diffs if x < 0)}   '
      f'含 -0.000（<=0）窗数 = {sum(1 for x in tbl_diffs if x <= 0)}   '
      f'落在 [+0.003,+0.049] 内窗数 = {sum(1 for x in tbl_diffs if 0.0025 <= x <= 0.0495)}')
    P('')

    # —— [E] :9723 倍率读法 ——
    P('[E] :9723 倍率核验（慢1/3 时长 / 快1/3 时长）')
    ratios_c = {}
    for key in WINDOWS:
        fd, fg, sd, sg, diff, k, n = per_win[key]['variants'][('edge', 'floor')]
        ratios_c[key] = sd / fd
    ratios_t = {k: TABLE[k][2] / TABLE[k][0] for k in WINDOWS}
    mc = max(ratios_c, key=ratios_c.get); mt = max(ratios_t, key=ratios_t.get)
    P(f'  实算: 中位 = {statistics.median(sorted(ratios_c.values())):.4f}  '
      f'最大 = {ratios_c[mc]:.4f} @ {mc[0]}/w{mc[1]}  最小 = {min(ratios_c.values()):.4f}')
    P(f'  表值: 中位 = {statistics.median(sorted(ratios_t.values())):.4f}  '
      f'最大 = {ratios_t[mt]:.4f} @ {mt[0]}/w{mt[1]}  最小 = {min(ratios_t.values()):.4f}')
    P(f'  表内 l3/w0 = {ratios_t[("l3_20261021",0)]:.4f}（:9723 括号称 2.14）; '
      f'实算 l3/w0 = {ratios_c[("l3_20261021",0)]:.4f}')
    slow_abs_max_c = max(WINDOWS, key=lambda k: per_win[k]['variants'][('edge', 'floor')][2])
    slow_abs_max_t = max(WINDOWS, key=lambda k: TABLE[k][2])
    P(f'  「慢1/3 时长绝对值最大」读法: 实算 = {slow_abs_max_c[0]}/w{slow_abs_max_c[1]} '
      f'({per_win[slow_abs_max_c]["variants"][("edge","floor")][2]:.1f} ms); 表值 = '
      f'{slow_abs_max_t[0]}/w{slow_abs_max_t[1]} ({TABLE[slow_abs_max_t][2]:.1f} ms)')
    P('')

    # —— [F] :9724 区间断言判定 ——
    P('[F] :9724「空档差 = +0.003 ~ +0.049 ms」判定')
    in_range = sum(1 for x in diffs if 0.0025 <= x <= 0.0495)
    P(f'  主口径实算 15 窗: 落在区间内 {in_range}/15; 低于 +0.003 的窗 '
      f'{sum(1 for x in diffs if x < 0.0025)}; 高于 +0.049 的窗 {sum(1 for x in diffs if x > 0.0495)}')
    tbl_in = sum(1 for x in tbl_diffs if 0.0025 <= x <= 0.0495)
    P(f'  台账自家表值 15 窗: 落在区间内 {tbl_in}/15（区间为全正断言 vs 表含负值/零值）')
    P('')

    # —— [G] 与 N-8 报告对照（其自报语料标准口径: 中位 +0.0550, 范围 +0.0065..+0.1080, 负值 0/15） ——
    P('[G] 与 N-8 自报「语料标准口径」数字对照（N-8 SLOW_WINDOW_LIMITS.md:85/:145）')
    P(f'  本轮独立实算: 中位 {f3(dmed)}, 范围 {f3(min(diffs))}..{f3(max(diffs))}, '
      f'负值窗 {sum(1 for x in diffs if x < 0)}/15')
    P('  （口径细节与 N-8 实现是否同一是另一回事——本轮只对数，未读其脚本）')
    P('')
    P('[_r3] END')

    with open(OUT, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(out_lines) + '\n')
    print('WRITTEN: ' + OUT)

if __name__ == '__main__':
    main()
