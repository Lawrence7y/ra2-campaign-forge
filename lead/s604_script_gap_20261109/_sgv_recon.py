# -*- coding: utf-8 -*-
# _sgv_recon.py —— 复核员独立重建探针（不复用上轮代码，只读语料与台账）
# 目的：③核「可唯一重建」五项口径；⑤核候选证伪数据；④核 75/75 与 -114.8 指纹
# 零真机、零采样代码；只读；输出 _sgv_recon_out.txt
import json, statistics, math, random, hashlib, re, os

BASE = r'D:\Project\ra2-campaign-forge'
CORPUS = os.path.join(BASE, 'out', 're_work', 'work_chain', 'CONTINUE_20261003', 'lead', 'qc161_u0400_trip')
LEDGER = os.path.join(BASE, 'lead', 'GOAL_THREE_TARGETS_20261018.md')
OUT = os.path.join(BASE, 'lead', 's604_script_gap_20261109', '_sgv_recon_out.txt')

TRIPS = ['l1c_20261021', 'l1d_20261021', 'l1e_20261021', 'l3_20261021', 't55k_20261020']
WINDOWS = [(t, w) for t in TRIPS for w in (0, 1, 2)]

# R3 [A] 语料指纹（自 _r3_recompute_out.txt:9-37 抄录，用于输入完整性核对）
R3_SHA = {
    ('l1c_20261021', 0): ('9464cac4387ec4e0b1a02cce8f4c63755c5e08b51fd12352cd362fdaa867556f', 257797),
    ('l1c_20261021', 1): ('edf4ed136c011494c954c32cd3253337b01d8a82f227c02fd54fdc4211009b7a', 260075),
    ('l1c_20261021', 2): ('654f3bc44c74e6400c0248a978a124c3fe95449c698176f62f9c6eaca52da726', 260507),
    ('l1d_20261021', 0): ('b3dc3a9abc76c4fdfd223e405964a4935fdf573fe8c4bcb1c122afabd9f04e22', 260734),
    ('l1d_20261021', 1): ('36f59371e61cbe8a18265c70adeaee0e4aababf1a3cd88537c1dbf46f3648ad0', 260644),
    ('l1d_20261021', 2): ('7e994c7cd6ca0bf6d5554611b0748d967bb94986c09b543292ade46823cb8097', 262470),
    ('l1e_20261021', 0): ('b106bd6d3eb30a1910d1e84182a4cfd260ee5d26563b978232019e040c5637e9', 261506),
    ('l1e_20261021', 1): ('3919288d2b172e0d4571f36f412b2cc48df3460a2e416b408245bfba722d40af', 261855),
    ('l1e_20261021', 2): ('043654033d384b4713be18abd1b05dc2c0d97cb4eaa3296ff4d88a524639cd86', 263067),
    ('l3_20261021',  0): ('e86029187da3482385313034322a66a8d9f0a7846c4f9b541834df309e03473e', 247450),
    ('l3_20261021',  1): ('273869c17fcc67e580131284775c44896cf029a15f536de96ab2def5cd8f0739', 249000),
    ('l3_20261021',  2): ('a71d3318a81da871f2c0568ca3411d9f76fe439ebfd7969a307200b71c4bd81a', 256142),
    ('t55k_20261020', 0): ('30c5a6e68e26e02de6014f31ac3b5a6d3fa821436fd6ec02f0a78777aa4bfaf6', 272285),
    ('t55k_20261020', 1): ('3302b2bb0f357516bddecd6b2b2bf323da8ba98e3457573b8a4ba5b14b92a7e4', 272141),
    ('t55k_20261020', 2): ('3cb933142b1abfd8653b1a63902b73ca609824ca1133655ef4b43b09dfe68b84', 272095),
}
# R3 [B] 主口径四值（fd,fg,sd,sg），自 _r3_recompute_out.txt:41-55 抄录——逐位一致性对照用
R3_B = {
    ('l1c_20261021', 0): (65.8435, 2.6725, 147.9440, 2.7805),
    ('l1c_20261021', 1): (64.3315, 2.6445, 154.8135, 2.7235),
    ('l1c_20261021', 2): (62.7950, 2.6590, 138.3240, 2.7260),
    ('l1d_20261021', 0): (60.2460, 2.6450, 131.9510, 2.7090),
    ('l1d_20261021', 1): (58.0880, 2.6370, 136.0740, 2.6750),
    ('l1d_20261021', 2): (39.9075, 2.6210, 99.2820, 2.6760),
    ('l1e_20261021', 0): (55.1340, 2.6390, 116.4170, 2.6710),
    ('l1e_20261021', 1): (52.7910, 2.6210, 115.6420, 2.6690),
    ('l1e_20261021', 2): (39.9270, 2.6200, 97.8200, 2.6540),
    ('l3_20261021',  0): (73.2380, 2.7070, 156.5720, 2.7950),
    ('l3_20261021',  1): (50.0590, 2.6580, 117.5360, 2.7540),
    ('l3_20261021',  2): (62.2960, 2.6610, 134.8770, 2.7640),
    ('t55k_20261020', 0): (28.9245, 2.5975, 35.2140, 2.6235),
    ('t55k_20261020', 1): (29.5830, 2.5950, 34.8800, 2.6205),
    ('t55k_20261020', 2): (29.6290, 2.6090, 34.8445, 2.6155),
}

out_lines = []
def P(s=''):
    out_lines.append(s)
    print(s)

def num(tok):
    tok = tok.replace('*', '').replace('ms', '').replace('−', '-').strip()
    return float(tok)

def parse_ledger_table():
    # 从台账 :9706-9720 运行时解析表值（不信任手录常量）
    with open(LEDGER, 'rb') as fh:
        lines = fh.read().decode('utf-8').splitlines()
    table = {}
    pat = re.compile(r'^\|\s*`(\w+)/w(\d)`\s*\|')
    for ln in lines[9705:9720]:
        m = pat.match(ln)
        if not m:
            raise RuntimeError('ledger row parse fail: ' + ln)
        cells = [c for c in ln.split('|')[1:-1]]
        trip, w = m.group(1), int(m.group(2))
        fd = num(cells[1]); fg = num(cells[2]); sd = num(cells[3]); sg = num(cells[4])
        df = num(cells[5])
        table[(trip, w)] = (fd, fg, sd, sg, df)
    if len(table) != 15:
        raise RuntimeError('ledger table rows != 15')
    return table

def main():
    random.seed(20261109)
    TAB = parse_ledger_table()
    P('[T] 台账 :9706-9720 运行时解析 15 行 OK（含 U+2212 负号与 -0.000）')
    P('    l1c/w0=%r' % (TAB[('l1c_20261021', 0)],))
    P('    t55k/w2=%r' % (TAB[('t55k_20261020', 2)],))
    P('')

    per = {}
    sha_ok = 0
    for key in WINDOWS:
        trip, w = key
        path = os.path.join(CORPUS, trip, 'measure_w%d.json' % w)
        raw = open(path, 'rb').read()
        sha = hashlib.sha256(raw).hexdigest()
        exp = R3_SHA[key]
        ok = (sha == exp[0] and len(raw) == exp[1])
        sha_ok += ok
        if not ok:
            P('[S!] SHA 抄录不匹配（区分我手误 vs 语料漂移）: %s/w%d' % (trip, w))
            P('     mine=%s %dB' % (sha, len(raw)))
            P('     R3抄=%s %dB' % (exp[0], exp[1]))
        d = json.loads(raw.decode('utf-8'))
        t = d['samples']['t']; f = d['samples']['f']
        edges = d['frame_edges']
        groups = {}
        for fi, ti in zip(f, t):
            groups.setdefault(fi, []).append(ti)
        fids = [e[0] for e in edges]
        et = {e[0]: e[1] for e in edges}
        n = len(fids)
        dur = {}; mg = {}; mg2 = {}; n_lt2 = 0
        for i, fid in enumerate(fids):
            ts = sorted(groups.get(fid, []))
            if len(ts) >= 2:
                gaps = [ts[j + 1] - ts[j] for j in range(len(ts) - 1)]
                mg[fid] = max(gaps)
                if len(gaps) >= 2:
                    mg2[fid] = sorted(gaps)[-2]
            else:
                n_lt2 += 1
            if i + 1 < n:
                dur[fid] = et[fids[i + 1]] - et[fid]
        # span 时长
        dur_span = {}
        for fid in fids:
            ts = groups.get(fid, [])
            if ts:
                dur_span[fid] = max(ts) - min(ts)
        # C8a：挂时间后继（末帧无 dur，自然出局；无需 wrap——但为对照也算 wrap 值）
        fwd = {}; bwd = {}
        for i, fid in enumerate(fids):
            if fid in mg:
                if i + 1 < n and fids[i + 1] in mg:
                    fwd[fid] = mg[fids[i + 1]]
                else:
                    fwd[fid] = mg[fid]           # wrap（仅末帧可达此分支）
                if i - 1 >= 0 and fids[i - 1] in mg:
                    bwd[fid] = mg[fids[i - 1]]
                else:
                    bwd[fid] = mg[fid]
        nmod3 = len([x for x in dur if x in mg]) % 3
        per[key] = dict(fids=fids, dur=dur, dur_span=dur_span, mg=mg, mg2=mg2,
                        fwd=fwd, bwd=bwd, n=n, n_lt2=n_lt2, nmod3=nmod3)
    P('[S] 语料完整性：15/15 SHA256+bytes 与 R3 [A] 一致 = %d/15' % sha_ok)
    P('    每窗 <2样本帧数: %s' % ' '.join(str(per[k]['n_lt2']) for k in WINDOWS))
    P('    每窗参算帧数 n(有dur且有mg) mod 3: %s' % ' '.join(str(per[k]['nmod3']) for k in WINDOWS))
    P('')

    def ids_of(r, durmap):
        return sorted([x for x in r['fids'] if x in durmap and x in r['mg']],
                      key=lambda x: (durmap[x], x))

    def stats(r, ids, durmap, mgmap):
        k = len(ids) // 3
        n = len(ids)
        fast, slow = ids[:k], ids[n - k:]
        fd = statistics.median([durmap[i] for i in fast]) * 1000.0
        sd = statistics.median([durmap[i] for i in slow]) * 1000.0
        fg = statistics.median([mgmap[i] for i in fast]) * 1000.0
        sg = statistics.median([mgmap[i] for i in slow]) * 1000.0
        return fd, fg, sd, sg

    def evaluate(tag, valf):
        gh = rh = dh = rdh = dh1 = 0
        pos_dfg = neg_dsg = negdiff = 0
        raws = {}
        for key in WINDOWS:
            td = TAB[key]
            fd, fg, sd, sg = valf(key)
            diff = sg - fg
            raws[key] = (fd, fg, sd, sg, diff)
            dh1 += round(fd, 1) == td[0]; dh1 += round(sd, 1) == td[2]
            rh += round(fg, 2) == td[1]; rh += round(sg, 2) == td[3]
            rdh += round(diff, 3) == td[4]
            pos_dfg += (td[1] - fg) > 0
            neg_dsg += (td[3] - sg) < 0
            negdiff += diff < 0
        P('  %-26s | 时长round1 %2d/30 | gap round2 %2d/30 | diff round3 %2d/15 | Δfg>0:%2d Δsg<0:%2d 负diff:%2d'
          % (tag, dh1, rh, rdh, pos_dfg, neg_dsg, negdiff))
        return raws

    # [R] 真值基线：与 R3 [B] 逐位对照
    P('[R] 真值基线（edge+floor+maxgap+median）vs R3 [B] 抄录值（四重重建之第 5 重）')
    mx = 0.0
    truth = {}
    for key in WINDOWS:
        r = per[key]
        ids = ids_of(r, r['dur'])
        fd, fg, sd, sg = stats(r, ids, r['dur'], r['mg'])
        truth[key] = (fd, fg, sd, sg)
        rb = R3_B[key]
        mx = max(mx, abs(fd - rb[0]), abs(fg - rb[1]), abs(sd - rb[2]), abs(sg - rb[3]))
    P('    max| mine − R3[B] | = %.6f  （0 ⇒ 逐位一致）' % mx)
    evaluate('真值', lambda k: truth[k])
    P('')

    # [C8] 时间后继/前继错位
    P('[C8] 错位挂接候选（时长列仍 edge 三分）')
    c8a = {}
    c8b = {}
    for key in WINDOWS:
        r = per[key]
        ids = ids_of(r, r['dur'])
        c8a[key] = stats(r, ids, r['dur'], r['fwd'])
        c8b[key] = stats(r, ids, r['dur'], r['bwd'])
    raws_a = evaluate('C8a 挂时间后继', lambda k: c8a[k])
    raws_b = evaluate('C8b 挂时间前继', lambda k: c8b[k])
    P('    C8a 逐窗 fg/sg/diff vs 台账：')
    for key in WINDOWS:
        td = TAB[key]
        fd, fg, sd, sg = c8a[key]
        P('      %-16s calc %6.2f %6.2f %+8.4f | ledger %5.2f %5.2f %+7.3f'
          % (key[0] + '/w' + str(key[1]), fg, sg, sg - fg, td[1], td[3], td[4]))
    P('    t55k/w2 原始 diff = %.6f（报告称 -0.0005，负号保留）' % (c8a[('t55k_20261020', 2)][3] - c8a[('t55k_20261020', 2)][1],))
    P('    l3/w0   原始 diff = %.6f（报告称 -0.002）' % (c8a[('l3_20261021', 0)][3] - c8a[('l3_20261021', 0)][1],))
    P('')

    # [K] k 规则与时长口径钉死检验（ceil / span 的时长列命中）
    P('[K] 口径钉死：ceil 与 span 的时长列 round1 命中（钉 floor+edge 的数据证据）')
    kceil_hits = kspan_hits = 0
    for key in WINDOWS:
        r = per[key]
        td = TAB[key]
        ids_c = sorted([x for x in r['fids'] if x in r['dur'] and x in r['mg']],
                       key=lambda x: (r['dur'][x], x))
        n = len(ids_c); k = math.ceil(n / 3)
        fast, slow = ids_c[:k], ids_c[n - k:]
        fd = statistics.median([r['dur'][i] for i in fast]) * 1000.0
        sd = statistics.median([r['dur'][i] for i in slow]) * 1000.0
        kceil_hits += round(fd, 1) == td[0]; kceil_hits += round(sd, 1) == td[2]
        ids_s = sorted([x for x in r['fids'] if x in r['dur_span'] is not None and x in r['mg']],
                       key=lambda x: (r['dur_span'][x], x)) if False else sorted(
                       [x for x in r['fids'] if x in r['dur_span'] and x in r['mg']],
                       key=lambda x: (r['dur_span'][x], x))
        n = len(ids_s); k = n // 3
        fast, slow = ids_s[:k], ids_s[n - k:]
        fd = statistics.median([r['dur_span'][i] for i in fast]) * 1000.0
        sd = statistics.median([r['dur_span'][i] for i in slow]) * 1000.0
        kspan_hits += round(fd, 1) == td[0]; kspan_hits += round(sd, 1) == td[2]
    P('    k=ceil 时长列 round1 = %d/30 ; span 时长列 round1 = %d/30 （对照组：floor+edge = 30/30）' % (kceil_hits, kspan_hits))
    P('')

    # [F1] 次大而非最大
    P('[F1] 次大（第二大山）候选：gap=帧内次大相邻差，edge 三分')
    c_g2 = {}
    for key in WINDOWS:
        r = per[key]
        ids2 = sorted([x for x in r['fids'] if x in r['dur'] and x in r['mg2']],
                      key=lambda x: (r['dur'][x], x))
        n = len(ids2); k = n // 3
        fg = statistics.median([r['mg2'][i] for i in ids2[:k]]) * 1000.0
        sg = statistics.median([r['mg2'][i] for i in ids2[n - k:]]) * 1000.0
        c_g2[key] = (fg, sg)
    evaluate('次大非最大', lambda k: (truth[k][0], c_g2[k][0], truth[k][2], c_g2[k][1]))
    P('')

    # [F2] 全去相关：C2a 时间序切片 / C7 随机置换
    P('[F2] 全去相关候选')
    c2a = {}
    for key in WINDOWS:
        r = per[key]
        tids = [x for x in r['fids'] if x in r['mg']]
        n = len(tids); k3 = len([x for x in r['fids'] if x in r['dur'] and x in r['mg']]) // 3
        fg = statistics.median([r['mg'][i] for i in tids[:k3]]) * 1000.0
        sg = statistics.median([r['mg'][i] for i in tids[n - k3:]]) * 1000.0
        c2a[key] = (fg, sg)
    evaluate('C2a 时间序切片', lambda k: (truth[k][0], c2a[k][0], truth[k][2], c2a[k][1]))
    c7 = {}
    for key in WINDOWS:
        r = per[key]
        ids = ids_of(r, r['dur'])
        n = len(ids); k = n // 3
        fgs = []; sgs = []
        for _ in range(3):
            perm = ids[:]
            random.shuffle(perm)
            fgs.append(statistics.median([r['mg'][i] for i in perm[:k]]) * 1000.0)
            sgs.append(statistics.median([r['mg'][i] for i in perm[n - k:]]) * 1000.0)
        c7[key] = (statistics.mean(fgs), statistics.mean(sgs))
    evaluate('C7 随机置换(seed20261109,3均)', lambda k: (truth[k][0], c7[k][0], truth[k][2], c7[k][1]))
    P('')

    # [F3] 加宽稀释网格
    P('[F3] 加宽分组网格（8 宽度 × 15 窗，负 diff 存在性）')
    grid = [('(k3,k3)', lambda n: n // 3, lambda n: n // 3),
            ('(k2,k2)', lambda n: n // 2, lambda n: n // 2),
            ('(2k3,2k3)', lambda n: 2 * (n // 3), lambda n: 2 * (n // 3)),
            ('(k3,k2)', lambda n: n // 3, lambda n: n // 2),
            ('(k2,k3)', lambda n: n // 2, lambda n: n // 3),
            ('(k2,2k3)', lambda n: n // 2, lambda n: 2 * (n // 3)),
            ('(2k3,k2)', lambda n: 2 * (n // 3), lambda n: n // 2),
            ('(5k6,5k6)', lambda n: 5 * n // 6, lambda n: 5 * n // 6)]
    for tag, fa, fb in grid:
        neg = 0; ds = []
        for key in WINDOWS:
            r = per[key]
            ids = ids_of(r, r['dur'])
            n = len(ids)
            a = min(fa(n), n); b = min(fb(n), n)
            fg = statistics.median([r['mg'][i] for i in ids[:a]]) * 1000.0
            sg = statistics.median([r['mg'][i] for i in ids[n - b:]]) * 1000.0
            ds.append(sg - fg); neg += (sg - fg) < 0
        P('    %-9s 负diff窗=%2d  diff范围 %+.4f..%+.4f' % (tag, neg, min(ds), max(ds)))
    P('')

    # [F4] 中位偶数处理 / k±1 量化
    P('[F4] 自由度量化')
    def upper_med(v):
        s = sorted(v); n = len(s)
        return s[n // 2] if n % 2 == 0 else s[(n - 1) // 2]
    def lower_med(v):
        s = sorted(v); n = len(s)
        return s[(n - 1) // 2] if n % 2 == 0 else s[n // 2]
    mxu = mxl = mxk = 0.0
    for key in WINDOWS:
        r = per[key]
        ids = ids_of(r, r['dur'])
        n = len(ids); k = n // 3
        for lst in ([r['mg'][i] for i in ids[:k]], [r['mg'][i] for i in ids[n - k:]]):
            mxu = max(mxu, abs(upper_med(lst) - statistics.median(lst)))
            mxl = max(mxl, abs(lower_med(lst) - statistics.median(lst)))
        for kk in (k + 1, max(k - 1, 1)):
            d1 = abs(statistics.median([r['mg'][i] for i in ids[:kk]]) - statistics.median([r['mg'][i] for i in ids[:k]]))
            d2 = abs(statistics.median([r['mg'][i] for i in ids[n - kk:]]) - statistics.median([r['mg'][i] for i in ids[n - k:]]))
            mxk = max(mxk, d1, d2)
    P('    max|upper/lower − median| = %.4f / %.4f ms ；max|k±1 − k| = %.4f ms（需 0.05 级才有影响）' % (mxu * 1000, mxl * 1000, mxk * 1000))
    P('')

    # [FP] -114.8 指纹 + 中心塌缩
    P('[FP] -114.8 指纹（台账 :9754 自认 x[4]-x[3]）')
    a = statistics.median([truth[k][3] - truth[k][2] for k in WINDOWS])
    b = statistics.median([TAB[k][3] - TAB[k][2] for k in WINDOWS])
    P('    median(sg−sd) 实算 = %.4f ; 表值 = %.4f （两者应都舍入为 -114.8）' % (a, b))
    P('[FP2] 中心塌缩：|pop − 台账fg/sg| 与 |pop − 真值fg/sg|（pop=全体帧 maxgap 中位）')
    mx_led = 0.0; mx_true = 0.0
    mx_led_ids = 0.0; mx_true_ids = 0.0
    rho_min, rho_max = 1e9, -1e9
    for key in WINDOWS:
        r = per[key]
        tids = [x for x in r['fids'] if x in r['mg']]
        ids = ids_of(r, r['dur'])
        pop_all = statistics.median([r['mg'][i] for i in tids]) * 1000.0
        pop_ids = statistics.median([r['mg'][i] for i in ids]) * 1000.0
        td = TAB[key]
        mx_led = max(mx_led, abs(pop_all - td[1]), abs(pop_all - td[3]))
        mx_true = max(mx_true, abs(pop_all - truth[key][1]), abs(pop_all - truth[key][3]))
        mx_led_ids = max(mx_led_ids, abs(pop_ids - td[1]), abs(pop_ids - td[3]))
        mx_true_ids = max(mx_true_ids, abs(pop_ids - truth[key][1]), abs(pop_ids - truth[key][3]))
        durs = [r['dur'][i] for i in ids_of(r, r['dur'])]
        mgs = [r['mg'][i] for i in ids_of(r, r['dur'])]
        def rank(v):
            order = sorted(range(len(v)), key=lambda i: v[i])
            rk = [0.0] * len(v); i = 0
            while i < len(order):
                j = i
                while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
                    j += 1
                avg = (i + j) / 2.0 + 1.0
                for t2 in range(i, j + 1):
                    rk[order[t2]] = avg
                i = j + 1
            return rk
        rd_, rm_ = rank(durs), rank(mgs)
        md = statistics.mean(rd_); mm = statistics.mean(rm_)
        num = sum((x - md) * (y - mm) for x, y in zip(rd_, rm_))
        den = math.sqrt(sum((x - md) ** 2 for x in rd_) * sum((y - mm) ** 2 for y in rm_))
        rho = num / den if den else float('nan')
        rho_min = min(rho_min, rho); rho_max = max(rho_max, rho)
    P('    pop=全体有mg帧:  max|pop−台账列| = %.4f ms ; max|pop−真值列| = %.4f ms' % (mx_led, mx_true))
    P('    pop=参算帧(ids): max|pop−台账列| = %.4f ms（上轮口径，报告称 ≤0.026） ; max|pop−真值列| = %.4f ms（报告称 0.056）' % (mx_led_ids, mx_true_ids))
    P('    rho(时长,maxgap) 范围 = %.3f..%.3f（报告称 0.05-0.48）' % (rho_min, rho_max))
    P('')
    P('[_sgv_recon] END')

    with open(OUT, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(out_lines) + '\n')
    print('WRITTEN: ' + OUT)

if __name__ == '__main__':
    main()
