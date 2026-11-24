# -*- coding: utf-8 -*-
# _exw_verify.py —— §604 C8a 排他性定稿轮（第三轮）独立回验
# 本脚本 = 撰写员第三实现的回验件：不复用前两轮代码，直读语料 JSON 与台账原文。
# 内容：[FP] 九件上游指纹；[TBL] 台账 :9706-9720 直读解析；[R] C8a 第三实现重建
#      （15 diff 逐值对照 + 30/30+30/30+15/15 + zip≡wrap + 方向签名 + -114.8）；
#      [N1] 断序族（复核定谳项）；[N2] 边界并列组全子集枚举；[N3] 中位算子；[N4] k 自由度；
#      [N5] C20 族；[N6] C13c 码形独立重推导；[N7] 诊断。
# 零真机、零采样代码。运行：python -I -X utf8 <本文件绝对路径>
import json, os, statistics, hashlib, bisect, itertools
from datetime import datetime

BASE = os.path.normpath('D:/Project/ra2-campaign-forge')
CORPUS_REL = ('out', 're_work', 'work_chain', 'CONTINUE_20261003', 'lead', 'qc161_u0400_trip')
OUT_REL = ('lead', 's604_exclusive_20261109', '_exw_verify_out.txt')
LEDGER_REL = ('lead', 'GOAL_THREE_TARGETS_20261018.md')

TRIPS = ['l1c_20261021', 'l1d_20261021', 'l1e_20261021', 'l3_20261021', 't55k_20261020']
WINDOWS = [(t, w) for t in TRIPS for w in (0, 1, 2)]

# 撰写轮 TABLE 常量（_ex_rebuild_c8a.py:16-32；仅用于与台账直读解析交叉核对）
WRITER_TABLE = {
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
# 上一轮在盘锚 15 个 diff 值（_sg_probe_shift_out.txt [C12]:27-41 的 C8a 列，本轮实读）
ANCHOR_DIFFS = [0.0315, 0.0275, 0.0300, 0.0490, 0.0220, 0.0245, 0.0030, 0.0350, 0.0180,
                -0.0020, 0.0370, 0.0020, -0.0130, -0.0060, -0.0005]

FP_FILES = [
    ('lead/s604_script_gap_20261109/S604_SCRIPT_GAP.md',
     '593c7a3ed3b1d1d47d6da5d8277f76c9323499aa04084a86e376ab5f9d2ab740', 20271),
    ('lead/s604_script_gap_20261109/_sg_FINDINGS.md',
     'a9f293bb296315b08c9417ff177a43c9222d07637a8a5678d48535941683ba92', 10925),
    ('lead/s604_script_gap_20261109/_sgv_final_out.txt',
     'eba311b175bf4071fb9dc7bf23ab01798a55e0aa07d0b4d7dafa15c5a99ba6ee', 1855),
    ('lead/s604_script_gap_20261109/_sg_probe_shift.py',
     '0fe4fb8f194cf082412ae90f19741c8b22276add2a0286f548dac63ed156d6fb', 10080),
    ('lead/s604_script_gap_20261109/_sg_probe_compression.py',
     '9d178bcf60eafccb1878cb292aa714db754157c5fce157d164c7a4093f23ddd3', 12708),
    ('lead/slowframe_r3_20261108/_r3_recompute_gapdiff.py',
     '9e27495232301018ec8e5b4f38c101d6ab4835feef514215a821be00ca459a78', 12659),
    ('lead/s604_attribution_20261108/S604_ATTRIBUTION.md',
     '8e9a606752ce2fd4c3d279ba5bb4a54eba99bc83f8974921f3f5601aa1008237', 27182),
    ('lead/GOAL_THREE_TARGETS_20261018.md',
     '2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede', 759518),
    ('lead/PENDING_DECISIONS.md',
     '3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7', 52419),
]

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
    return s[n // 2]

def lower_med(v):
    s = sorted(v); n = len(s)
    return s[(n - 1) // 2]

def f3(x):
    return ('+' if x >= 0 else '-') + ('%.4f' % abs(x))

def parse_ledger_rows():
    """直读台账 :9706-9720，解析 15 行表值（U+2212 归一为 ASCII -）。"""
    with safe_open(list(LEDGER_REL), 'rb') as fh:
        text = fh.read().decode('utf-8')
    lines = text.split('\n')
    rows = {}
    rownos = []
    for ln in range(9706, 9721):
        raw = lines[ln - 1]
        s = raw.replace('`', '').replace('**', '').replace('\u2212', '-').replace(' ms', '')
        parts = [p.strip() for p in s.split('|')]
        parts = [p for p in parts if p != '']
        name = parts[0]
        trip, w = name.split('/w')
        vals = [float(x) for x in parts[1:6]]
        rows[(trip, int(w))] = tuple(vals)
        rownos.append(ln)
    return rows, rownos

def main():
    # ---- [FP] 九件上游指纹 ----
    P('[FP] 上游九件指纹（python -I -X utf8 + hashlib，与编排方交付清单逐件比对）')
    ok = 0
    for rel, hexexp, bexp in FP_FILES:
        with safe_open(tuple(rel.split('/')), 'rb') as fh:
            b = fh.read()
        h = hashlib.sha256(b).hexdigest()
        m = (h == hexexp and len(b) == bexp)
        ok += m
        P('  %-46s %s…%s  %7d B  %s' % (rel.split('/')[-1], h[:8], h[-6:], len(b), 'MATCH' if m else 'MISMATCH'))
    P('  九件核对: %d/9 MATCH' % ok)
    P('')
    for rel in ('lead/GOAL_THREE_TARGETS_20261018.md', 'lead/PENDING_DECISIONS.md'):
        fp = os.path.normpath(os.path.join(BASE, rel))
        P('  mtime %-44s %s' % (rel, datetime.fromtimestamp(os.path.getmtime(fp)).isoformat()))
    P('  本轮运行时刻: %s' % datetime.now().isoformat())
    P('')

    # ---- [TBL] 台账表值直读解析 ----
    TABLE, rownos = parse_ledger_rows()
    P('[TBL] 台账 :9706-9720 直读解析（U+2212→ASCII-）')
    P('  解析行号恰为 9706..9720: %s；解析行数 = %d' % (rownos == list(range(9706, 9721)), len(rownos)))
    tmatch = sum(1 for k in WINDOWS if TABLE[k] == WRITER_TABLE[k])
    P('  与撰写轮 TABLE 常量（_ex_rebuild_c8a.py:16-32）逐键相等: %d/15' % tmatch)
    P('')

    # ---- 语料载入 + 逐帧统计（第三实现）----
    win = {}
    for trip, w in WINDOWS:
        with safe_open(list(CORPUS_REL) + [trip, 'measure_w%d.json' % w]) as fh:
            d = json.loads(fh.read().decode('utf-8'))
        edges = d['frame_edges']
        fids = [e[0] for e in edges]
        et = [e[1] for e in edges]
        sf = list(d['samples']['f'])
        st = list(d['samples']['t'])
        groups = {}
        for fi, ti in zip(sf, st):
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
        win[(trip, w)] = dict(fids=fids, et=et, sf=sf, st=st, groups=groups,
                              dur=dur, mg=mg, nsamp=nsamp, fwd=fwd, ids=ids)

    def row_of(key, gmap, ids=None, dm=None, mfd=None, mfg=None, msd=None, msg=None, kf=None, ks=None):
        r = win[key]
        ids = r['ids'] if ids is None else ids
        dm = r['dur'] if dm is None else dm
        n = len(ids)
        k0 = n // 3
        kf = k0 if kf is None else kf
        ks = k0 if ks is None else ks
        mfd = mfd or med; mfg = mfg or med; msd = msd or med; msg = msg or med
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
            row = rows[key]; td = TABLE[key]
            if round(row[0], 1) != td[0]: bad.append('%s/w%d:fd' % (key[0][:4], key[1]))
            if round(row[1], 2) != td[1]: bad.append('%s/w%d:fg' % (key[0][:4], key[1]))
            if round(row[2], 1) != td[2]: bad.append('%s/w%d:sd' % (key[0][:4], key[1]))
            if round(row[3], 2) != td[3]: bad.append('%s/w%d:sg' % (key[0][:4], key[1]))
            if round(row[4], 3) != td[4]: bad.append('%s/w%d:diff' % (key[0][:4], key[1]))
        return bad

    def report(label, rows):
        bad = failcells(rows)
        P('  %-36s | %2d/75 | 失败格: %s' % (label, 75 - len(bad), ' '.join(bad) if bad else '无'))
        return 75 - len(bad)

    # ---- [R] 基准重建 ----
    P('[R1] 真值基线 C0（正确配对；第三实现）')
    rows_c0 = {key: row_of(key, win[key]['mg']) for key in WINDOWS}
    rows_c8a = {key: row_of(key, win[key]['fwd']) for key in WINDOWS}
    for key in WINDOWS:
        fd, fg, sd, sg, diff = rows_c0[key]
        P('  %-16s fd=%7.4f fg=%6.4f sd=%7.4f sg=%6.4f diff=%s' % (key[0] + '/w' + str(key[1]), fd, fg, sd, sg, f3(diff)))
    P('')
    P('[R2] C8a-wrap（帧 i ← mg(帧 i+1)，末帧回绕自身；时长列仍 edge 三分）')
    for key in WINDOWS:
        fd, fg, sd, sg, diff = rows_c8a[key]
        P('  %-16s fd=%7.4f fg=%6.4f sd=%7.4f sg=%6.4f diff=%s' % (key[0] + '/w' + str(key[1]), fd, fg, sd, sg, f3(diff)))
    P('')

    P('[R3] C8a 15 个 diff 值逐值对照（4 位小数；锚 = 上一轮在盘 _sg_probe_shift_out.txt [C12] C8a 列）')
    nm = 0
    for idx, key in enumerate(WINDOWS):
        diff = rows_c8a[key][4]
        okc = abs(diff - ANCHOR_DIFFS[idx]) < 0.00005
        nm += okc
        P('  %-16s 本轮=%s 锚=%s %s  (台账 %+.3f)' % (key[0] + '/w' + str(key[1]), f3(diff), f3(ANCHOR_DIFFS[idx]),
          'MATCH' if okc else 'MISMATCH', TABLE[key][4]))
    P('  15 值核对: %d/15' % nm)
    P('')

    P('[R4] 75 格判定（round 判等：dur 1 位/gap 2 位/diff 3 位，对台账直读表值）')
    rd = rg = rdiff = 0; gh = dh = 0
    for key in WINDOWS:
        fd, fg, sd, sg, diff = rows_c8a[key]
        td = TABLE[key]
        rd += round(fd, 1) == td[0]; rd += round(sd, 1) == td[2]
        rg += round(fg, 2) == td[1]; rg += round(sg, 2) == td[3]
        rdiff += round(diff, 3) == td[4]
        gh += abs(fg - td[1]) < 0.005; gh += abs(sg - td[3]) < 0.005
        dh += abs(diff - td[4]) < 0.0005
    P('  round 判等: 时长列 %d/30, 空档列 %d/30, 空档差列 %d/15  → 75 格合计 %d/75' % (rd, rg, rdiff, rd + rg + rdiff))
    P('  容差判等: 空档列 %d/30, 差列 %d/15' % (gh, dh))
    P('')

    P('[R5] C8a-zip（帧0..n-2 时长配帧1..n-1 maxgap，末帧出局）vs C8a-wrap 逐位比较')
    allsame = True
    for key in WINDOWS:
        r = win[key]; fids = r['fids']; n = len(fids)
        zdur = {fids[i]: r['dur'][fids[i]] for i in range(n - 1)}
        zmg = {fids[i]: r['mg'][fids[i + 1]] for i in range(n - 1)}
        zids = sorted(zdur.keys(), key=lambda x: (zdur[x], x))
        zk = len(zids) // 3; m = len(zids)
        zfd = med([zdur[i] for i in zids[:zk]]) * 1000.0
        zsd = med([zdur[i] for i in zids[m - zk:]]) * 1000.0
        zfg = med([zmg[i] for i in zids[:zk]]) * 1000.0
        zsg = med([zmg[i] for i in zids[m - zk:]]) * 1000.0
        same = (zfd, zfg, zsd, zsg, zsg - zfg) == rows_c8a[key]
        allsame = allsame and same
        P('  %-16s zip≡wrap 逐位相同=%s' % (key[0] + '/w' + str(key[1]), same))
    P('  全 15 窗逐位相同: %s' % allsame)
    P('')

    P('[R6] 方向签名')
    a = b = c = 0
    for key in WINDOWS:
        td = TABLE[key]
        a += (td[1] - rows_c8a[key][1]) > 0
        b += (td[3] - rows_c8a[key][3]) < 0
        c += rows_c8a[key][4] < 0
    a2 = b2 = 0
    for key in WINDOWS:
        td = TABLE[key]
        a2 += (td[1] - rows_c0[key][1]) > 0
        b2 += (td[3] - rows_c0[key][3]) < 0
    P('  对 C8a: 台账快列>C8a快列 %d/15, 台账慢列<C8a慢列 %d/15, C8a 负diff %d 窗' % (a, b, c))
    P('  对真值: 台账快列>真值快列 %d/15, 台账慢列<真值慢列 %d/15' % (a2, b2))
    P('')

    P('[R7] -114.8 指纹（x=(窗名,fd,fg,sd,sg) 读法，median(sg-sd)）')
    P('  真值基线: median(sg-sd) = %.4f' % med([rows_c0[k][3] - rows_c0[k][2] for k in WINDOWS]))
    P('  台账表值: median(sg-sd) = %.4f' % med([TABLE[k][3] - TABLE[k][2] for k in WINDOWS]))
    P('')

    # ---- [N1] 断序族（复核对撰写轮『断序被钉死』的推翻项）----
    P('[N1] 断序规则族（×C8a 挂接；复核轮裁决项回验：75/75 成员、74/75 成员与空转成员）')
    t0map = {key: dict(zip(win[key]['fids'], win[key]['et'])) for key in WINDOWS}
    rules = [
        ('(dur,mg,fid)',    lambda key: (lambda x: (win[key]['dur'][x], win[key]['mg'][x], x))),
        ('(dur,-mg,fid)',   lambda key: (lambda x: (win[key]['dur'][x], -win[key]['mg'][x], x))),
        ('(dur,nsamp,fid)', lambda key: (lambda x: (win[key]['dur'][x], win[key]['nsamp'][x], x))),
        ('(dur,-nsamp,fid)', lambda key: (lambda x: (win[key]['dur'][x], -win[key]['nsamp'][x], x))),
        ('(dur,t0,fid)',    lambda key: (lambda x: (win[key]['dur'][x], t0map[key][x], x))),
        ('(dur,-t0,fid)',   lambda key: (lambda x: (win[key]['dur'][x], -t0map[key][x], x))),
        ('(dur,-fid)',      lambda key: (lambda x: (win[key]['dur'][x], -x))),
    ]
    for tag, mk in rules:
        rows_t = {}; diffwins = []; bit = True
        for key in WINDOWS:
            r = win[key]
            ids_t = sorted([f for f in r['fids'] if f in r['dur'] and f in r['mg']], key=mk(key))
            rows_t[key] = row_of(key, r['fwd'], ids=ids_t)
            if ids_t != r['ids']:
                diffwins.append(key[0][:4] + '/w%d' % key[1])
            if rows_t[key] != rows_c8a[key]:
                bit = False
        report('C8a+tie=' + tag, rows_t)
        P('        排序与默认不同的窗: %s；五元组与C8a逐位相同: %s'
          % (','.join(diffwins) if diffwins else '无（空转规则）', bit))
    P('')

    # ---- [N2] 边界并列组全子集枚举 ----
    P('[N2] 断序空间收口：k 边界并列 dur 组全部子集划分枚举（确定性断序规则只能诱导其中一种）')
    for key in WINDOWS:
        r = win[key]
        ids = r['ids']; n = len(ids); k = n // 3; dm = r['dur']
        for bname, (i1, i2) in (('快边界', (k - 1, k)), ('慢边界', (n - k - 1, n - k))):
            if dm[ids[i1]] != dm[ids[i2]]:
                continue
            lo, hi = i1, i2
            while lo - 1 >= 0 and dm[ids[lo - 1]] == dm[ids[i1]]:
                lo -= 1
            while hi + 1 < n and dm[ids[hi + 1]] == dm[ids[i2]]:
                hi += 1
            block = ids[lo:hi + 1]; g = len(block)
            m = (k - lo) if bname == '快边界' else (hi - (n - k) + 1)
            side_first = (bname == '快边界')
            nsub = 1
            for q in range(m):
                nsub = nsub * (g - q) // (q + 1)
            hits = 0; nondefault = 0; tried = 0; default_hit = False
            default = tuple(ids[lo:lo + m]) if side_first else tuple(ids[hi + 1 - m:hi + 1])
            for combo in itertools.combinations(block, m):
                tried += 1
                cs = set(combo)
                rest = [f for f in block if f not in cs]
                if side_first:
                    new_ids = ids[:lo] + list(combo) + rest + ids[hi + 1:]
                else:
                    new_ids = ids[:lo] + rest + list(combo) + ids[hi + 1:]
                if hits5(key, row_of(key, r['fwd'], ids=new_ids)):
                    hits += 1
                    if tuple(combo) == default:
                        default_hit = True
                    else:
                        nondefault += 1
            P('  %-16s %s 并列组 g=%d（位 %d..%d），侧内成员 m=%d，子集数 C(%d,%d)=%d'
              % (key[0] + '/w' + str(key[1]), bname, g, lo, hi, m, g, m, nsub))
            P('      实测子集 %d 个，全 5 格命中子集 %d 个（其中非默认划分 %d 个）；默认划分命中=%s'
              % (tried, hits, nondefault, default_hit))
    P('')

    # ---- [N3] 中位算子自由度 ----
    P('[N3] 中位算子自由度（对台账直读表值）')
    report('C8a+upper median(全4列)', {key: row_of(key, win[key]['fwd'], mfd=upper_med, mfg=upper_med, msd=upper_med, msg=upper_med) for key in WINDOWS})
    report('C8a+lower median(全4列)', {key: row_of(key, win[key]['fwd'], mfd=lower_med, mfg=lower_med, msd=lower_med, msg=lower_med) for key in WINDOWS})
    for opname, op in (('upper', upper_med), ('lower', lower_med)):
        for col, cname in ((0, 'fd'), (1, 'fg'), (2, 'sd'), (3, 'sg')):
            kw = {'mfd': None, 'mfg': None, 'msd': None, 'msg': None}
            kw[['mfd', 'mfg', 'msd', 'msg'][col]] = op
            rows_v = {key: row_of(key, win[key]['fwd'], **kw) for key in WINDOWS}
            report('C8a+%s 仅%s列' % (opname, cname), rows_v)
    P('')

    # ---- [N4] k 自由度 ----
    P('[N4] k 规则自由度')
    report('C8a+k=ceil(n/3)', {key: row_of(key, win[key]['fwd'], kf=-(-len(win[key]['ids']) // 3), ks=-(-len(win[key]['ids']) // 3)) for key in WINDOWS})
    report('C29b k=全帧数//3 + C8a', {key: row_of(key, win[key]['fwd'], kf=len(win[key]['fids']) // 3, ks=len(win[key]['fids']) // 3) for key in WINDOWS})
    P('')

    # ---- [N5] C20 族（末帧/首帧边界 × C8a；成员过滤与排序键都打补丁）----
    P('[N5] 末帧/首帧边界处理 × C8a（正确打补丁实现，对照撰写轮 [N3] 空转缺陷）')
    rows20a = {}; rows20z = {}; rows20c = {}
    for key in WINDOWS:
        r = win[key]
        fids = r['fids']; n = len(fids)
        d20 = dict(r['dur']); d20[fids[n - 1]] = r['dur'][fids[n - 2]]
        ids20 = sorted([f for f in fids if f in d20 and f in r['mg']], key=lambda x: (d20[x], x))
        rows20a[key] = row_of(key, r['fwd'], ids=ids20, dm=d20)
        fwz = dict(r['fwd']); fwz[fids[n - 1]] = 0.0
        rows20z[key] = row_of(key, fwz, ids=ids20, dm=d20)
        idsc = sorted([f for f in fids[1:] if f in r['dur'] and f in r['mg']], key=lambda x: (r['dur'][x], x))
        rows20c[key] = row_of(key, r['fwd'], ids=idsc)
    report('C20a 末帧dur重复 + C8a', rows20a)
    report('C20z 末帧dur重复+gap=0 + C8a', rows20z)
    report('C20c 首帧出局 + C8a', rows20c)
    P('')

    # ---- [N6] C13c 码形：样本→帧归属 bisect 重推导（独立于语料 f 字段）----
    P('[N6] C13c 码形：j = bisect_right(et, t) - 2 归属重推导（组 j = 帧 j+1 全体样本；不用语料 f）')
    same13 = True
    for key in WINDOWS:
        r = win[key]
        et = r['et']; fids = r['fids']; n = len(fids)
        g13 = {}
        f0_dropped = True
        succ_equal = True
        for fi, ti in zip(r['sf'], r['st']):
            j = bisect.bisect_right(et, ti) - 2
            if j < 0:
                if fi == fids[0]:
                    pass  # 帧0样本落组 -1
                else:
                    f0_dropped = False
                continue
            g13.setdefault(j, []).append(ti)
        # 组 j 应恰为帧 j+1 的全体样本（多重集相等）
        for j in range(n - 1):
            if sorted(g13.get(j, [])) != sorted(r['groups'].get(fids[j + 1], [])):
                succ_equal = False
        mg13 = {}
        for j in range(n - 1):
            ts = sorted(g13[j])
            mg13[fids[j]] = max(ts[q + 1] - ts[q] for q in range(len(ts) - 1))
        d13 = {fids[i]: r['dur'][fids[i]] for i in range(n - 1)}
        ids13 = sorted(d13.keys(), key=lambda x: (d13[x], x))
        k13 = len(ids13) // 3
        fd13 = med([d13[i] for i in ids13[:k13]]) * 1000.0
        sd13 = med([d13[i] for i in ids13[len(ids13) - k13:]]) * 1000.0
        fg13 = med([mg13[i] for i in ids13[:k13]]) * 1000.0
        sg13 = med([mg13[i] for i in ids13[len(ids13) - k13:]]) * 1000.0
        same = (fd13, fg13, sd13, sg13, sg13 - fg13) == rows_c8a[key]
        same13 = same13 and same
        P('  %-16s 组=后继帧全体样本=%s 帧0样本落组-1=%s 五元组与C8a逐位相同=%s'
          % (key[0] + '/w' + str(key[1]), succ_equal, f0_dropped, same))
    P('  全 15 窗: %s' % same13)
    P('')

    # ---- [N7] 诊断 ----
    P('[N7] 诊断')
    nties = 0
    for key in WINDOWS:
        r = win[key]
        ids = r['ids']; n = len(ids); k = n // 3; dm = r['dur']
        bt = dm[ids[k - 1]] == dm[ids[k]]
        st = dm[ids[n - k - 1]] == dm[ids[n - k]]
        nties += (bt or st)
    P('  k 边界存在精确 dur 并列的窗数 = %d/15' % nties)
    for key in WINDOWS[:3]:
        r = win[key]
        cnt = sum(1 for i in range(len(r['fids']) - 1) if r['fwd'][r['fids'][i]] != r['mg'][r['fids'][i]])
        P('  %-16s C8a 挂接值 ≠ 自身值的帧数 = %d/%d' % (key[0] + '/w' + str(key[1]), cnt, len(r['fids']) - 1))
    P('')
    P('[_exw_verify] END')

    with safe_open(OUT_REL, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(out_lines) + '\n')

if __name__ == '__main__':
    main()
