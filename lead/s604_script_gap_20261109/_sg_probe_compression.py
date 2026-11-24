# -*- coding: utf-8 -*-
# _sg_probe_compression.py —— §604 脚本缺口调查：候选实现错误能否产生 15/15 单向压缩
# 只读语料（out/re_work/.../qc161_u0400_trip/measure_w*.json）与台账表值常量；
# 唯一写域 = lead/s604_script_gap_20261109/。零真机、零采样代码。
# 候选（全部为「实现错误」而非口径选择；时长列一律固定 edge+k=n//3 —— 该列 30/30 已被 N-8/R3 双重复现）：
#   C0 真值基线：时长三分 + 帧内 maxgap 中位（= R3 主口径）
#   C1 空档列用「时长排序的 halves」(k2=n//2 / ceil2)——列间 k 不一致
#   C2 空档列用「时间序切片」(未重排的 gap 列表直接切前/后 k)——典型 sort 遗漏 bug
#   C3 空档列用「时长序循环移位 1」的 maxgap——边界错位
#   C4 两列都取「中间 1/3」——预期 fg=sg，证伪用
#   C5 组内池化相邻差中位——预期 ≈2.0ms，证伪用
#   C6 gap 列表独立升序排序后切片——预期水平错，证伪用
#   C7 随机置换对照（固定种子）——全去相关基线，看符号分布
# 另：[-114.8 指纹] 台账 :9754 自认 x[4]-x[3] 荒谬值，检验 x=(窗名,fd,fg,sd,sg) 读法下
#   median(sg-sd) 能否用主口径实算值/台账表值/span 口径复现 -114.8。
import json, statistics, math, random, os

BASE = 'D:/Project/ra2-campaign-forge'
CORPUS = BASE + '/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip'
OUT = BASE + '/lead/s604_script_gap_20261109/_sg_probe_compression_out.txt'

TRIPS = ['l1c_20261021', 'l1d_20261021', 'l1e_20261021', 'l3_20261021', 't55k_20261020']
WINDOWS = [(t, w) for t in TRIPS for w in (0, 1, 2)]

# 台账 :9706-9720 表值（快dur, 快gap, 慢dur, 慢gap, diff）——与 _sa_probe.py:30-46 同源录入
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

def main():
    random.seed(20261109)
    per = {}
    for trip, w in WINDOWS:
        with open(f'{CORPUS}/{trip}/measure_w{w}.json', 'rb') as fh:
            d = json.loads(fh.read().decode('utf-8'))
        edges = d['frame_edges']
        groups = {}
        for fi, ti in zip(d['samples']['f'], d['samples']['t']):
            groups.setdefault(fi, []).append(ti)
        fids = [e[0] for e in edges]           # 时间序（frame_edges 本身按时间）
        et = {e[0]: e[1] for e in edges}
        dur_edge = {}
        maxgap = {}
        pooled = {}                            # 组内池化相邻差备用：逐帧存全部相邻差
        for i, fid in enumerate(fids):
            ts = sorted(groups.get(fid, []))
            if len(ts) >= 2:
                gaps = [ts[j + 1] - ts[j] for j in range(len(ts) - 1)]
                maxgap[fid] = max(gaps)
                pooled[fid] = gaps
            if i + 1 < len(fids):
                dur_edge[fid] = et[fids[i + 1]] - et[fid]
        per[(trip, w)] = dict(fids=fids, dur=dur_edge, mg=maxgap, pooled=pooled,
                              n=len(fids))

    # ---- [0] 基线自检：主口径 vs R3 [B]（抽 3 窗）----
    P('[0] 基线自检（edge + k=n//3 + maxgap + median，对 R3 _r3_recompute_out.txt [B]）')
    def split_thirds(dur_map, ids_sorted):
        k = len(ids_sorted) // 3
        return ids_sorted[:k], ids_sorted[k:len(ids_sorted) - k], ids_sorted[len(ids_sorted) - k:]

    res = {}
    for key in WINDOWS:
        r = per[key]
        ids = sorted([f for f in r['fids'] if f in r['dur'] and f in r['mg']],
                     key=lambda x: (r['dur'][x], x))
        n = len(ids)
        fast, mid, slow = split_thirds(r['dur'], ids)
        fd = statistics.median([r['dur'][i] for i in fast]) * 1000.0
        sd = statistics.median([r['dur'][i] for i in slow]) * 1000.0
        k3 = n // 3
        base = dict(fd=fd, sd=sd, n=n, k=k3, ids=ids)
        # C0 真值
        base['fg'] = statistics.median([r['mg'][i] for i in fast]) * 1000.0
        base['sg'] = statistics.median([r['mg'][i] for i in slow]) * 1000.0
        # C1 halves（floor/ceil）
        k2f = n // 2; k2c = math.ceil(n / 2)
        base['fg_h2f'] = statistics.median([r['mg'][i] for i in ids[:k2f]]) * 1000.0
        base['sg_h2f'] = statistics.median([r['mg'][i] for i in ids[n - k2f:]]) * 1000.0
        base['fg_h2c'] = statistics.median([r['mg'][i] for i in ids[:k2c]]) * 1000.0
        base['sg_h2c'] = statistics.median([r['mg'][i] for i in ids[n - k2c:]]) * 1000.0
        # C2 时间序切片（gap 列表未随时长重排——时间序 = r['fids'] 顺序）
        tids = [f for f in r['fids'] if f in r['mg']]
        base['fg_t3'] = statistics.median([r['mg'][i] for i in tids[:k3]]) * 1000.0
        base['sg_t3'] = statistics.median([r['mg'][i] for i in tids[n - k3:]]) * 1000.0
        k2 = n // 2
        base['fg_t2'] = statistics.median([r['mg'][i] for i in tids[:k2]]) * 1000.0
        base['sg_t2'] = statistics.median([r['mg'][i] for i in tids[n - k2:]]) * 1000.0
        # C3 时长序循环移位 1（maxgap 值整体错一位）
        mg_seq = [r['mg'][i] for i in ids]
        mg_shift = mg_seq[-1:] + mg_seq[:-1]   # 右移一位
        base['fg_sh'] = statistics.median(mg_shift[:k3]) * 1000.0
        base['sg_sh'] = statistics.median(mg_shift[n - k3:]) * 1000.0
        # C4 中间 1/3（两列同组）
        base['fg_mid'] = statistics.median([r['mg'][i] for i in mid]) * 1000.0
        # C5 组内池化相邻差
        pf = [g for i in fast for g in r['pooled'][i]]
        ps = [g for i in slow for g in r['pooled'][i]]
        base['fg_pool'] = statistics.median(pf) * 1000.0
        base['sg_pool'] = statistics.median(ps) * 1000.0
        # C6 gap 独立排序
        gs = sorted(r['mg'][i] for i in ids)
        base['fg_so'] = statistics.median(gs[:k3]) * 1000.0
        base['sg_so'] = statistics.median(gs[n - k3:]) * 1000.0
        # C7 随机置换（固定种子，3 次平均）
        fgs, sgs = [], []
        for _ in range(3):
            perm = ids[:]
            random.shuffle(perm)
            fgs.append(statistics.median([r['mg'][i] for i in perm[:k3]]) * 1000.0)
            sgs.append(statistics.median([r['mg'][i] for i in perm[n - k3:]]) * 1000.0)
        base['fg_rnd'] = statistics.mean(fgs)
        base['sg_rnd'] = statistics.mean(sgs)
        # 全体帧 maxgap 中位（去相关时的中心）
        base['pop'] = statistics.median([r['mg'][i] for i in ids]) * 1000.0
        # 时长-maxgap 秩相关（Spearman，手算）
        durs = [r['dur'][i] for i in ids]; mgs = [r['mg'][i] for i in ids]
        def rank(v):
            order = sorted(range(len(v)), key=lambda i: v[i])
            rk = [0.0] * len(v)
            i = 0
            while i < len(order):
                j = i
                while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
                    j += 1
                avg = (i + j) / 2.0 + 1.0
                for t in range(i, j + 1):
                    rk[order[t]] = avg
                i = j + 1
            return rk
        rd_, rm_ = rank(durs), rank(mgs)
        md = statistics.mean(rd_); mm = statistics.mean(rm_)
        num = sum((a - md) * (b - mm) for a, b in zip(rd_, rm_))
        den = math.sqrt(sum((a - md) ** 2 for a in rd_) * sum((b - mm) ** 2 for b in rm_))
        base['rho'] = num / den if den else float('nan')
        res[key] = base

    P('  l1c/w0: %.4f %.4f %.4f %.4f (R3: 65.8435 2.6725 147.9440 2.7805)'
      % (res[('l1c_20261021', 0)]['fd'], res[('l1c_20261021', 0)]['fg'],
         res[('l1c_20261021', 0)]['sd'], res[('l1c_20261021', 0)]['sg']))
    P('  l3/w0 : %.4f %.4f %.4f %.4f (R3: 73.2380 2.7070 156.5720 2.7950)'
      % (res[('l3_20261021', 0)]['fd'], res[('l3_20261021', 0)]['fg'],
         res[('l3_20261021', 0)]['sd'], res[('l3_20261021', 0)]['sg']))
    P('  t55k/w2: %.4f %.4f %.4f %.4f (R3: 29.6290 2.6090 34.8445 2.6155)'
      % (res[('t55k_20261020', 2)]['fd'], res[('t55k_20261020', 2)]['fg'],
         res[('t55k_20261020', 2)]['sd'], res[('t55k_20261020', 2)]['sg']))
    P('')

    # ---- [1] 各候选 vs 台账：逐格命中 + 方向签名 ----
    P('[1] 候选筛选：空档两列 round2 命中 /30、diff round3 命中 /15、Δfg>0 窗数、Δsg<0 窗数、负diff窗数')
    P('    （台账形态 = 快列抬高 15/15 + 慢列压低 13/15 + 负/零 diff 4 窗；完整解释需三列同时高命中）')
    cands = [
        ('C0 真值(时长三分)      ', 'fg', 'sg'),
        ('C1a 空档=时长序halves_f ', 'fg_h2f', 'sg_h2f'),
        ('C1b 空档=时长序halves_c ', 'fg_h2c', 'sg_h2c'),
        ('C2a 空档=时间序三分     ', 'fg_t3', 'sg_t3'),
        ('C2b 空档=时间序halves   ', 'fg_t2', 'sg_t2'),
        ('C3  空档=时长序移位1    ', 'fg_sh', 'sg_sh'),
        ('C4  两列=中间1/3        ', 'fg_mid', 'fg_mid'),
        ('C5  组内池化相邻差      ', 'fg_pool', 'sg_pool'),
        ('C6  gap独立排序切片     ', 'fg_so', 'sg_so'),
        ('C7  随机置换(3均)       ', 'fg_rnd', 'sg_rnd'),
    ]
    for name, fk, sk in cands:
        gh = rh = dh = rdh = 0
        pos_dfg = neg_dsg = negdiff = 0
        for key in WINDOWS:
            b = res[key]; td = TABLE[key]
            fg = b[fk]; sg = b[sk]; diff = sg - fg
            gh += abs(fg - td[1]) < 0.005  # 容差同 _sa_probe: |calc-ref|<0.005
            gh += abs(sg - td[3]) < 0.005
            rh += round(fg, 2) == td[1]; rh += round(sg, 2) == td[3]
            dh += abs(diff - td[4]) < 0.0005
            rdh += round(diff, 3) == td[4]
            pos_dfg += (td[1] - fg) > 0
            neg_dsg += (td[3] - sg) < 0
            negdiff += diff < 0
        P('  %s | 容差gap %2d/30 diff %2d/15 | round gap %2d/30 diff %2d/15 | Δfg>0:%2d Δsg<0:%2d 负diff:%2d'
          % (name, gh, dh, rh, rdh, pos_dfg, neg_dsg, negdiff))
    P('')

    # ---- [2] 最有希望候选的逐窗明细 ----
    P('[2] 逐窗明细（台账 vs C2a 时间序三分 / C1a 时长序halves）：fg/sg/diff')
    P('  window            | 台账  fg   sg   diff     | C2a  fg   sg   diff     | C1a  fg   sg   diff     | 真值fg   sg')
    for key in WINDOWS:
        b = res[key]; td = TABLE[key]
        P('  %-16s | %5.2f %5.2f %+7.3f | %5.2f %5.2f %+7.3f | %5.2f %5.2f %+7.3f | %5.2f %5.2f'
          % (key[0] + '/w' + str(key[1]), td[1], td[3], td[4],
             b['fg_t3'], b['sg_t3'], b['sg_t3'] - b['fg_t3'],
             b['fg_h2f'], b['sg_h2f'], b['sg_h2f'] - b['fg_h2f'],
             b['fg'], b['sg']))
    P('')

    # ---- [3] 去相关中心检验：台账两列是否 ≈ 全体帧 maxgap 中位 ----
    P('[3] 中心检验：全体帧 maxgap 中位(pop) vs 台账 fg/sg（|pop−台账| 与 |pop−真值| 对比）')
    P('  window            |   pop   | 台账fg  台账sg | 真值fg   真值sg | rho(时长,maxgap)')
    for key in WINDOWS:
        b = res[key]; td = TABLE[key]
        P('  %-16s | %7.4f | %5.2f %5.2f | %6.4f %6.4f | %.3f'
          % (key[0] + '/w' + str(key[1]), b['pop'], td[1], td[3], b['fg'], b['sg'], b['rho']))
    P('')

    # ---- [4] -114.8 指纹 ----
    P('[4] 台账 :9754 自认「x[4]-x[3] 得 -114.8 ms」：检验 x=(窗名,fd,fg,sd,sg) 读法下 median(sg-sd)')
    a = statistics.median([res[k]['sg'] - res[k]['sd'] for k in WINDOWS])
    b_ = statistics.median([TABLE[k][3] - TABLE[k][2] for k in WINDOWS])
    P('  主口径实算值: median(sg-sd) = %.4f' % a)
    P('  台账表值    : median(sg-sd) = %.4f' % b_)
    P('  （若某读法 ≈ -114.8 ⇒ 内联脚本的 sd 与该口径一致 + 元组结构 (名,fd,fg,sd,sg) 成立）')
    P('')
    P('[_sg_probe] END')

    with open(OUT, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(out_lines) + '\n')
    print('WRITTEN: ' + OUT)

if __name__ == '__main__':
    main()
