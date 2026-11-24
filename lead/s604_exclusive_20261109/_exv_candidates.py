# -*- coding: utf-8 -*-
# _exv_candidates.py —— 排他性复核·第三步：复核员自构新候选 + 撰写人近失主张独立回验
# 原则：候选构造标准 = 机理上合理，不是容易证伪。
# 写域 = lead/s604_exclusive_20261109/（输出 _exv_candidates_out.txt）。零真机、零采样代码。
import json, os, random, statistics, itertools
from decimal import Decimal, ROUND_HALF_UP

BASE = os.path.normpath('D:/Project/ra2-campaign-forge')
CORPUS_REL = ('out', 're_work', 'work_chain', 'CONTINUE_20261003', 'lead', 'qc161_u0400_trip')
OUT_REL = ('lead', 's604_exclusive_20261109', '_exv_candidates_out.txt')

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

def upper_med(v):
    s = sorted(v); n = len(s)
    return s[n // 2] if n % 2 == 0 else s[(n - 1) // 2]

def lower_med(v):
    s = sorted(v); n = len(s)
    return s[(n - 1) // 2] if n % 2 == 0 else s[n // 2]

def main():
    # ---- 语料 ----
    win = {}
    for trip, w in WINDOWS:
        with safe_open(list(CORPUS_REL) + [trip, 'measure_w%d.json' % w]) as fh:
            d = json.loads(fh.read().decode('utf-8'))
        edges = d['frame_edges']
        fids = [e[0] for e in edges]
        et = [e[1] for e in edges]
        groups = {}
        for fi, ti in zip(d['samples']['f'], d['samples']['t']):
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
        fwd[fids[-1]] = mg[fids[-1]]
        ids = sorted([f for f in fids if f in dur and f in mg], key=lambda x: (dur[x], x))
        win[(trip, w)] = dict(fids=fids, et=et, dur=dur, mg=mg, nsamp=nsamp, fwd=fwd, ids=ids)

    def row_of(key, gmap, ids=None, k=None, dm=None, medop=med, medops=None, kf=None, ks=None):
        r = win[key]
        ids = r['ids'] if ids is None else ids
        n = len(ids)
        k0 = n // 3
        kf = k0 if kf is None else kf
        ks = k0 if ks is None else ks
        dm = r['dur'] if dm is None else dm
        mfd, mfg, msd, msg = medop, medop, medop, medop
        if medops:
            mfd, mfg, msd, msg = medops
        fd = mfd([dm[i] for i in ids[:kf]]) * 1000.0
        sd = msd([dm[i] for i in ids[n - ks:]]) * 1000.0
        fg = mfg([gmap[i] for i in ids[:kf]]) * 1000.0
        sg = msg([gmap[i] for i in ids[n - ks:]]) * 1000.0
        return fd, fg, sd, sg, sg - fg

    def hits5(key, row):
        td = TABLE[key]
        return (round(row[0], 1) == td[0] and round(row[1], 2) == td[1] and
                round(row[2], 1) == td[2] and round(row[3], 2) == td[3] and
                round(row[4], 3) == td[4])

    def failcells(rows):
        bad = []
        for key in WINDOWS:
            row = rows[key]
            td = TABLE[key]
            if round(row[0], 1) != td[0]: bad.append('%s/w%d:fd' % (key[0][:4], key[1]))
            if round(row[1], 2) != td[1]: bad.append('%s/w%d:fg' % (key[0][:4], key[1]))
            if round(row[2], 1) != td[2]: bad.append('%s/w%d:sd' % (key[0][:4], key[1]))
            if round(row[3], 2) != td[3]: bad.append('%s/w%d:sg' % (key[0][:4], key[1]))
            if round(row[4], 3) != td[4]: bad.append('%s/w%d:diff' % (key[0][:4], key[1]))
        return bad

    def report(label, rows):
        bad = failcells(rows)
        P('  %-34s | %2d/75 | 失败格: %s' % (label, 75 - len(bad), ' '.join(bad) if bad else '无'))
        return 75 - len(bad)

    # ---- [W] 撰写人近失主张独立回验（我自己的实现） ----
    P('[W] 撰写人关键候选独立回验（复核员自有实现，非复用其代码）')
    rows_c8a = {key: row_of(key, win[key]['fwd']) for key in WINDOWS}
    report('C8a 基准', rows_c8a)
    rows_c0 = {key: row_of(key, win[key]['mg']) for key in WINDOWS}
    report('C0 真值(正确配对)', rows_c0)
    # tie-break (dur,mg,fid)
    rows_tie = {}
    for key in WINDOWS:
        r = win[key]
        ids = sorted([f for f in r['fids'] if f in r['dur'] and f in r['mg']],
                     key=lambda x: (r['dur'][x], r['mg'][x], x))
        rows_tie[key] = row_of(key, r['fwd'], ids=ids)
    report('C8a+tie=(dur,mg,fid)', rows_tie)
    # upper / lower / ceil
    report('C8a+upper median', {key: row_of(key, win[key]['fwd'], medop=upper_med) for key in WINDOWS})
    report('C8a+lower median', {key: row_of(key, win[key]['fwd'], medop=lower_med) for key in WINDOWS})
    rows_ceil = {key: row_of(key, win[key]['fwd'], kf=-(-len(win[key]['ids']) // 3),
                             ks=-(-len(win[key]['ids']) // 3)) for key in WINDOWS}
    report('C8a+k=ceil(n/3)', rows_ceil)
    # C29b: k = 全帧数(edges)//3
    rows29 = {}
    for key in WINDOWS:
        r = win[key]
        k29 = len(r['fids']) // 3
        rows29[key] = row_of(key, r['fwd'], kf=k29, ks=k29)
    report('C29b k=edges//3 + C8a', rows29)
    # C18b battery：键=E[i]-E[i-1]（帧0键=自身dur），fd/sd 报键值；gap=自身mg
    rows18 = {}
    for key in WINDOWS:
        r = win[key]
        fids = r['fids']; et = r['et']; n = len(fids)
        d18 = {fids[i]: (et[i] - et[i - 1] if i >= 1 else et[1] - et[0]) for i in range(n)}
        ids = sorted([f for f in fids if f in d18 and f in r['mg']], key=lambda x: (d18[x], x))
        n2 = len(ids); k = n2 // 3
        fd = med([d18[i] for i in ids[:k]]) * 1000.0
        sd = med([d18[i] for i in ids[n2 - k:]]) * 1000.0
        fg = med([r['mg'][i] for i in ids[:k]]) * 1000.0
        sg = med([r['mg'][i] for i in ids[n2 - k:]]) * 1000.0
        rows18[key] = (fd, fg, sd, sg, sg - fg)
    report('C18b 键后移一帧,fd/sd报键值', rows18)
    # C18b-own：同键，fd/sd 报自身 dur（末帧无 dur → 出局，与撰写人 [N3] 语义一致）
    rows18o = {}
    for key in WINDOWS:
        r = win[key]
        fids = r['fids']; et = r['et']; n = len(fids)
        d18 = {fids[i]: (et[i] - et[i - 1] if i >= 1 else et[1] - et[0]) for i in range(n)}
        ids = sorted([f for f in fids if f in d18 and f in r['mg'] and f in r['dur']],
                     key=lambda x: (d18[x], x))
        rows18o[key] = row_of(key, r['mg'], ids=ids, dm=r['dur'])
    report('C18b 键后移,fd/sd报自身时长', rows18o)
    # C18 缺格：键前移（E[i+2]-E[i+1]），fd/sd 报自身 dur
    rows18f = {}
    for key in WINDOWS:
        r = win[key]
        fids = r['fids']; et = r['et']; n = len(fids)
        d18f = {fids[i]: et[i + 2] - et[i + 1] for i in range(n - 2)}
        ids = sorted([f for f in fids if f in d18f and f in r['mg'] and f in r['dur']],
                     key=lambda x: (d18f[x], x))
        rows18f[key] = row_of(key, r['mg'], ids=ids, dm=r['dur'])
    report('C18a 键前移,fd/sd报自身时长', rows18f)
    # C20a/C20z battery：末帧补 dur=前帧 dur，末帧入组；gap=fwd（末帧 wrap 自身 / 0）
    for tag, zero in (('C20a 末帧dur重复+C8a', False), ('C20z 末帧dur重复+gap0+C8a', True)):
        rows20 = {}
        for key in WINDOWS:
            r = win[key]
            fids = r['fids']; n = len(fids)
            d20 = dict(r['dur']); d20[fids[n - 1]] = r['dur'][fids[n - 2]]
            ids = sorted([f for f in fids if f in d20 and f in r['mg']], key=lambda x: (d20[x], x))
            fw = dict(r['fwd'])
            if zero:
                fw[fids[n - 1]] = 0.0
            rows20[key] = row_of(key, fw, ids=ids, dm=d20)
        report(tag, rows20)
    # C20c：首帧出局 + C8a
    rows20c = {}
    for key in WINDOWS:
        r = win[key]
        fids = r['fids']; n = len(fids)
        ids = sorted(fids[1:n - 1], key=lambda x: (r['dur'][x], x))
        rows20c[key] = row_of(key, r['fwd'], ids=ids)
    report('C20c 首帧出局+C8a', rows20c)
    P('')

    # ---- 去首 mg 重算（独立一段） ----
    mgx_by_key = {}
    for trip, w in WINDOWS:
        with safe_open(list(CORPUS_REL) + [trip, 'measure_w%d.json' % w]) as fh:
            d = json.loads(fh.read().decode('utf-8'))
        groups = {}
        for fi, ti in zip(d['samples']['f'], d['samples']['t']):
            groups.setdefault(fi, []).append(ti)
        mgx = {}
        for fid, ts in groups.items():
            ts = sorted(ts)
            if len(ts) >= 3:
                mgx[fid] = max(ts[j + 1] - ts[j] for j in range(1, len(ts) - 1))
            elif len(ts) == 2:
                mgx[fid] = 0.0
        mgx_by_key[(trip, w)] = mgx
    rows_xf2 = {}
    for key in WINDOWS:
        r = win[key]
        mgx = mgx_by_key[key]
        fw = {}
        fids = r['fids']
        for i in range(len(fids) - 1):
            fw[fids[i]] = mgx.get(fids[i + 1], 0.0)
        fw[fids[-1]] = mgx.get(fids[-1], 0.0)
        rows_xf2[key] = row_of(key, fw)
    report('去首(excl_first)×后继错位', rows_xf2)
    P('')

    # ---- [N] 复核员自构新候选 ----
    P('[N] 复核员自构新候选（撰写人 51 候选清单之外）')

    # N1 断序规则族 × C8a（撰写人只测了 (dur,mg,fid)）
    P('  [N1] 断序规则族（全部 × C8a 挂接；仅在 k 边界并列窗有实际作用）')
    t0map = {key: dict(zip(win[key]['fids'], win[key]['et'])) for key in WINDOWS}
    tie_rules = [
        ('(dur,-mg,fid)', lambda r: lambda x: (r['dur'][x], -r['mg'][x], x)),
        ('(dur,nsamp,fid)', lambda r: lambda x: (r['dur'][x], r['nsamp'][x], x)),
        ('(dur,-nsamp,fid)', lambda r: lambda x: (r['dur'][x], -r['nsamp'][x], x)),
        ('(dur,t0,fid)', lambda k_: (lambda r: lambda x: (r['dur'][x], t0map[k_][x], x))),
        ('(dur,-t0,fid)', lambda k_: (lambda r: lambda x: (r['dur'][x], -t0map[k_][x], x))),
        ('(dur,-fid)', lambda r: lambda x: (r['dur'][x], -x)),
    ]
    for tag, kf_ in tie_rules:
        rows_t = {}
        diffwins = []
        bit_ident = True
        for key in WINDOWS:
            r = win[key]
            if tag.startswith('(dur,t0') or tag.startswith('(dur,-t0'):
                keyf = kf_(key)(r)
            else:
                keyf = kf_(r)
            ids = sorted([f for f in r['fids'] if f in r['dur'] and f in r['mg']], key=keyf)
            rows_t[key] = row_of(key, r['fwd'], ids=ids)
            if ids != r['ids']:
                diffwins.append(key[0][:4] + '/w%d' % key[1])
            if rows_t[key] != rows_c8a[key]:
                bit_ident = False
        sc = report('C8a+tie=' + tag, rows_t)
        P('      排序与默认不同的窗: %s；五元组与C8a逐位相同: %s'
          % (','.join(diffwins) if diffwins else '无（空转规则）', bit_ident))

    # N2 断序空间决定性收口：边界并列组的全部子集枚举
    P('  [N2] 断序空间收口：k 边界并列 dur 组的【全部子集划分】枚举（任何确定性断序规则只能诱导其中一种）')
    for key in WINDOWS:
        r = win[key]
        ids = r['ids']; n = len(ids); k = n // 3; dm = r['dur']
        for bname, bidx in (('快边界', (k - 1, k)), ('慢边界', (n - k - 1, n - k))):
            i1, i2 = bidx
            if dm[ids[i1]] != dm[ids[i2]]:
                continue
            lo, hi = i1, i2
            while lo - 1 >= 0 and dm[ids[lo - 1]] == dm[ids[i1]]:
                lo -= 1
            while hi + 1 < n and dm[ids[hi + 1]] == dm[ids[i2]]:
                hi += 1
            block = ids[lo:hi + 1]
            g = len(block)
            if bname == '快边界':
                m = k - lo                       # 落入快段（位 lo..k-1）的成员数
                side_first = True
            else:
                m = hi - (n - k) + 1             # 落入慢段（位 n-k..hi）的成员数
                side_first = False
            nsub = 1
            for q in range(m):
                nsub = nsub * (g - q) // (q + 1)
            P('    %-16s %s 并列组大小 g=%d（位 %d..%d），侧内成员 m=%d，子集数 C(%d,%d)=%d'
              % (key[0] + '/w' + str(key[1]), bname, g, lo, hi, m, g, m, nsub))
            hit_subsets = []
            tried = 0
            default = tuple(ids[lo:lo + m]) if side_first else tuple(ids[hi + 1 - m:hi + 1])
            def try_combo(combo):
                cs = set(combo)
                rest = [f for f in block if f not in cs]
                if side_first:
                    new_ids = ids[:lo] + list(combo) + rest + ids[hi + 1:]
                else:
                    new_ids = ids[:lo] + rest + list(combo) + ids[hi + 1:]
                return hits5(key, row_of(key, r['fwd'], ids=new_ids))
            if nsub <= 200000:
                for combo in itertools.combinations(block, m):
                    tried += 1
                    if try_combo(combo):
                        hit_subsets.append(combo)
            else:
                rng = random.Random(20261110)
                seen = set()
                for _ in range(200000):
                    combo = tuple(rng.sample(block, m))
                    if combo in seen:
                        continue
                    seen.add(combo)
                    tried += 1
                    if try_combo(combo):
                        hit_subsets.append(combo)
                        if len(hit_subsets) > 50:
                            break
            hit_nondefault = [h for h in hit_subsets if h != default]
            P('      实测子集 %d 个，全 5 格命中子集 %d 个（其中非默认划分 %d 个）；默认划分命中=%s'
              % (tried, len(hit_subsets), len(hit_nondefault), default in hit_subsets))
    P('')

    # N3 样本级（按帧样本数加权）中位
    P('  [N3] 样本级加权中位（每样本携带其帧的 dur/gap，展开为样本多重集后取 median）')
    for gtag, gsel in (('gap加权', True), ('gap不加权', False)):
        for ptag, psel in (('dur加权', True), ('dur不加权', False)):
            for mtag, gm in (('×C8a', 'fwd'), ('×正确', 'mg')):
                rows_w = {}
                for key in WINDOWS:
                    r = win[key]
                    ids = r['ids']; n = len(ids); k = n // 3
                    gmap = r['fwd'] if gm == 'fwd' else r['mg']
                    fdv = []
                    for f in ids[:k]:
                        fdv += [r['dur'][f]] * (r['nsamp'][f] if psel else 1)
                    sdv = []
                    for f in ids[n - k:]:
                        sdv += [r['dur'][f]] * (r['nsamp'][f] if psel else 1)
                    fgv = []
                    for f in ids[:k]:
                        fgv += [gmap[f]] * (r['nsamp'][f] if gsel else 1)
                    sgv = []
                    for f in ids[n - k:]:
                        sgv += [gmap[f]] * (r['nsamp'][f] if gsel else 1)
                    fd = med(fdv) * 1000.0; sd = med(sdv) * 1000.0
                    fg = med(fgv) * 1000.0; sg = med(sgv) * 1000.0
                    rows_w[key] = (fd, fg, sd, sg, sg - fg)
                report('加权中位 %s+%s %s' % (ptag, gtag, mtag), rows_w)
    P('')

    # N4 单列中位算子变体（两路径 bug：只有一列用了不同偶数处理）
    P('  [N4] 单列中位算子变体（×C8a；撰写人只测了全局 upper/lower）')
    ops = {'upper': upper_med, 'lower': lower_med}
    for opname, op in ops.items():
        for col in ('fd', 'fg', 'sd', 'sg'):
            idx = {'fd': 0, 'fg': 1, 'sd': 2, 'sg': 3}[col]
            def mk(idx=idx, op=op):
                base = [med, med, med, med]
                base[idx] = op
                return base
            rows_o = {}
            for key in WINDOWS:
                r = win[key]
                ids = r['ids']; n = len(ids); k = n // 3
                mfd, mfg, msd, msg = mk()
                fd = mfd([r['dur'][i] for i in ids[:k]]) * 1000.0
                sd = msd([r['dur'][i] for i in ids[n - k:]]) * 1000.0
                fg = mfg([r['fwd'][i] for i in ids[:k]]) * 1000.0
                sg = msg([r['fwd'][i] for i in ids[n - k:]]) * 1000.0
                rows_o[key] = (fd, fg, sd, sg, sg - fg)
            report('C8a+%s仅%s列' % (opname, col), rows_o)
    P('')

    # N5 单侧 k±1（两路径 off-by-one：只有一组切片差 1）
    P('  [N5] 单侧 k±1（×C8a；撰写人 C11 只量化了双侧幅度 0.0045ms，未打 75 格分）')
    for tag, dk, gk in (('k+1仅时长侧', 1, 0), ('k-1仅时长侧', -1, 0),
                        ('k+1仅空档侧', 0, 1), ('k-1仅空档侧', 0, -1)):
        rows_k = {}
        for key in WINDOWS:
            r = win[key]
            ids = r['ids']; n = len(ids); k = n // 3
            rows_k[key] = row_of(key, r['fwd'], kf=k + dk, ks=k + gk)
        report('C8a+' + tag, rows_k)
    P('')

    # N6 显示层舍入模式探针（C8a 值是否恰落在半格 → 舍入自由度是否被数据钉死）
    P('  [N6] 显示层舍入模式探针（round / %%.Nf / Decimal(repr)HALF_UP / Decimal(真值)HALF_UP）')
    from decimal import Decimal as Dc
    split_cells = 0
    mode_match = {'round': 0, 'fmt': 0, 'repr_halfup': 0, 'true_halfup': 0}
    split_detail = []
    for key in WINDOWS:
        row = rows_c8a[key]
        td = TABLE[key]
        for name, x, d, ref in (('fd', row[0], 1, td[0]), ('fg', row[1], 2, td[1]),
                                ('sd', row[2], 1, td[2]), ('sg', row[3], 2, td[3]),
                                ('diff', row[4], 3, td[4])):
            q = Dc(1).scaleb(-d)
            cands = {
                'round': round(x, d),
                'fmt': float('%.*f' % (d, x)),
                'repr_halfup': float(Dc(repr(x)).quantize(q, rounding=ROUND_HALF_UP)),
                'true_halfup': float(Dc(x).quantize(q, rounding=ROUND_HALF_UP)),
            }
            vals = set(cands.values())
            if len(vals) > 1:
                split_cells += 1
                agree = [m for m, v in cands.items() if v == ref]
                split_detail.append('%s/w%d:%s 值=%r 各模式=%s 表值=%s 命中模式=%s'
                                    % (key[0][:4], key[1], name, x,
                                       {m: repr(v) for m, v in cands.items()}, ref, agree))
                for m in agree:
                    mode_match[m] += 1
    P('    75 格中各舍入模式结果不一致的格数 = %d' % split_cells)
    for line in split_detail:
        P('      ' + line)
    if split_cells == 0:
        P('    ⇒ 舍入模式自由度空转（所有模式给出同一显示值，无需数据裁决）')
    P('')

    # N7 全列快慢互换（台账自认曾把分组标签写反）
    P('  [N7] 全列快慢互换 × C8a（台账 :9752 自认的标签写反史）')
    rows_sw = {}
    for key in WINDOWS:
        fd, fg, sd, sg, diff = rows_c8a[key]
        rows_sw[key] = (sd, sg, fd, fg, fg - sg)
    report('C8a+全列互换', rows_sw)
    P('')

    # N8 fid+1 数值后继（fid 窗内连续 ⇒ 应与时间后继逐位同一，等价性探针）
    P('  [N8] fid+1 数值后继 vs 时间后继（fid 连续时应逐位同一）')
    allfid = True
    for key in WINDOWS:
        r = win[key]
        fids = r['fids']
        okc = all(fids[i + 1] - fids[i] == 1 for i in range(len(fids) - 1))
        fwd2 = {f: r['mg'][f + 1] for f in fids if (f + 1) in r['mg']}
        same = okc and fwd2 == {k: v for k, v in r['fwd'].items() if k in fwd2}
        allfid = allfid and same
    P('    全 15 窗 fid+1 后继映射 ≡ fwd 逐位相同: %s' % allfid)
    P('')

    # N9 每帧值先舍入到显示网格再中位（先舍入后统计的两路径 bug）
    P('  [N9] 先按显示网格舍入帧值再取中位（dur→0.1ms, gap→0.01ms）× {C8a, 正确}')
    for mtag, gm in (('×C8a', 'fwd'), ('×正确', 'mg')):
        rows_r = {}
        for key in WINDOWS:
            r = win[key]
            ids = r['ids']; n = len(ids); k = n // 3
            gmap = r['fwd'] if gm == 'fwd' else r['mg']
            fd = med([round(r['dur'][i] * 1000.0, 1) for i in ids[:k]])
            sd = med([round(r['dur'][i] * 1000.0, 1) for i in ids[n - k:]])
            fg = med([round(gmap[i] * 1000.0, 2) for i in ids[:k]])
            sg = med([round(gmap[i] * 1000.0, 2) for i in ids[n - k:]])
            rows_r[key] = (fd, fg, sd, sg, sg - fg)
        report('先舍入再中位 ' + mtag, rows_r)
    P('')

    # N10 三元复合：错位 × k 混合 × 断序
    P('  [N10] 三元复合（错位 × k × 断序）')
    rows_tr = {}
    for key in WINDOWS:
        r = win[key]
        ids = sorted([f for f in r['fids'] if f in r['dur'] and f in r['mg']],
                     key=lambda x: (r['dur'][x], r['mg'][x], x))
        k29 = len(r['fids']) // 3
        rows_tr[key] = row_of(key, r['fwd'], ids=ids, kf=k29, ks=k29)
    report('C8a+tie(mg,fid)+k=edges//3', rows_tr)
    rows_tr2 = {}
    for key in WINDOWS:
        r = win[key]
        ids = r['ids']; n = len(ids)
        kc = -(-n // 3)
        rows_tr2[key] = row_of(key, r['fwd'], kf=kc, ks=kc, medop=upper_med)
    report('C8a+upper+k=ceil', rows_tr2)
    P('')

    # [MC] 复核员自己的随机置换基线（种子独立于撰写人）
    P('[MC] 随机重挂接基线（100 次，seed=20261110，与撰写人实验独立）')
    random.seed(20261110)
    dist = []
    for trial in range(100):
        rows_m = {}
        for key in WINDOWS:
            r = win[key]
            vals = [r['mg'][f] for f in r['fids']]
            perm = vals[:]
            random.shuffle(perm)
            gmap = dict(zip(r['fids'], perm))
            rows_m[key] = row_of(key, gmap)
        bad = failcells(rows_m)
        dist.append(75 - len(bad))
    dist.sort()
    P('  100 次分布: min=%d p25=%d 中位=%d p75=%d max=%d' %
      (dist[0], dist[len(dist) // 4], dist[len(dist) // 2], dist[3 * len(dist) // 4], dist[-1]))
    P('')
    P('[_exv_candidates] END')

    with safe_open(OUT_REL, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(out_lines) + '\n')

if __name__ == '__main__':
    main()
