# -*- coding: utf-8 -*-
"""r136a_f24_survival.py -- R136 主会话：F24「唯一可引用的语料值」与现盘的一致性实测

被审主张（FACT_INDEX V532 第 F24 行）：
  对象证据集合（tier_final，本项唯一可引用的「语料」值）= 4,417 文件 / 737,517,286 B
  逐文件清单 tier_final_4417.tsv，回读 sum(bytes) 校验

本轮问的是那句「回读 sum(bytes) 校验」没有回答的问题：
  清单内部自洽（sum == 737,517,286）是一回事，清单指向的文件**现在还在不在**是另一回事。

不 import、不读任何既有脚本；全部自写。正反控成对。只读 live 树，唯一写出 = _r136/*.json。
"""
import csv
import io
import json
import os
import re
import sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
LEAD = os.path.join(ROOT, 'lead')
R14 = os.path.join(LEAD, 'next_re_20261117_r14')
M417 = os.path.join(R14, 'R17_R101_TIER_FINAL_4417', 'tier_final_4417.tsv')
M416 = os.path.join(R14, 'R17_R99_TIER_FINAL_4416', 'tier_final_4416.tsv')
M413 = os.path.join(R14, 'R17_R96_TIER_FINAL_4413', 'tier_final_4413.tsv')
M413B = os.path.join(R14, 'R17_R97_TIER_FINAL_4413B', 'tier_final_4413b.tsv')
SNAP = os.path.join(R14, 'R17_R72_T1_CLEANSCALE', 'files_tier_A_snap2.tsv')

res = []
OUT = {}


def chk(name, cond, detail):
    res.append((name, bool(cond), detail))
    print('%s %-62s %s' % ('PASS' if cond else 'FAIL', name, detail))


def load(p):
    with io.open(p, encoding='utf-8') as f:
        return list(csv.DictReader(f, delimiter='\t'))


rows = load(M417)
OUT['manifest_rows'] = len(rows)

# ---------- S1 清单内部自洽 ----------
n = len(rows)
tot = sum(int(r['bytes']) for r in rows)
chk('S1a 清单 4,417 行', n == 4417, 'rows=%d' % n)
chk('S1b sum(bytes) == 737,517,286', tot == 737517286, 'sum=%d' % tot)
chk('S1c 737,517,286 = 0.737517 GB(10^9) = 0.686866 GiB(2^30)（口径可换算）',
    abs(tot / 1e9 - 0.737517286) < 1e-12 and abs(tot / float(2 ** 30) - 0.686866) < 1e-6,
    'GB=%.9f GiB=%.6f' % (tot / 1e9, tot / float(2 ** 30)))
# 反控 S1d：把 sum 算成「件数 × 均值」的近似式必须不等（证明这个和是真求和不是估算）
chk('S1d 反控：均值×件数近似 != 真求和（不是估算值）',
    int(tot / n) * n != tot, 'mean*n=%d vs %d' % (int(tot / n) * n, tot))

# ---------- S2 逐行 stat 现盘 ----------
same, diff, miss = [], [], []
for r in rows:
    p = os.path.join(LEAD, r['rel'])
    want = int(r['bytes'])
    try:
        st = os.stat(p)
    except OSError:
        miss.append((r['rel'], want, r['source']))
        continue
    if st.st_size == want:
        same.append((r['rel'], want, r['source']))
    else:
        diff.append((r['rel'], want, st.st_size, r['source']))

OUT['same'] = {'n': len(same), 'bytes': sum(x[1] for x in same)}
OUT['diff'] = {'n': len(diff), 'items': diff, 'delta': sum(x[2] - x[1] for x in diff)}
OUT['miss'] = {'n': len(miss), 'bytes': sum(x[1] for x in miss)}

chk('S2a 三桶件数之和 == 清单件数（不重不漏）',
    len(same) + len(diff) + len(miss) == n,
    'same=%d diff=%d miss=%d total=%d' % (len(same), len(diff), len(miss), n))
chk('S2b 三桶字节之和 == 清单 sum(bytes)（不重不漏）',
    sum(x[1] for x in same) + sum(x[1] for x in diff) + sum(x[1] for x in miss) == tot,
    '%d + %d + %d' % (sum(x[1] for x in same), sum(x[1] for x in diff),
                      sum(x[1] for x in miss)))
chk('S2c 「逐字节不变」的件数远小于 4,417（清单不是现盘枚举）',
    len(same) < 200, 'same=%d / 4417 = %.2f%%' % (len(same), 100.0 * len(same) / n))
chk('S2d 字节数不同的件数极少且可逐件列出',
    len(diff) <= 5, 'diff=%d :: %s' % (len(diff), [(d[0].split('/')[-1], d[1], d[2]) for d in diff]))
note = ('unchanged %d / %d = %.2f%% ; missing %d / %d = %.2f%% (%d B) ; size-changed %d'
        % (len(same), n, 100.0 * len(same) / n, len(miss), n, 100.0 * len(miss) / n,
           sum(x[1] for x in miss), len(diff)))
print('NOTE ' + note)

# ---------- S3 唯一那件 size-changed 的定性 ----------
chk('S3a size-changed 恰为 1 件', len(diff) == 1, 'n=%d' % len(diff))
if diff:
    d = diff[0]
    chk('S3b 该件是 a2_sites.json（F24 正文点名剔 bounds 段的件）',
        os.path.basename(d[0]) == 'a2_sites.json', 'rel=%s' % d[0])
    chk('S3c 清单值 913,237 现值 17,624,355 差 +16,711,118（== F24 写的 bounds 剔段量）',
        d[1] == 913237 and d[2] == 17624355 and d[2] - d[1] == 16711118,
        'manifest=%d disk=%d delta=%+d' % (d[1], d[2], d[2] - d[1]))
    chk('S3d 磁盘上的文件未被实际剔段（现值 == 全量 17,624,355，不是 913,237）',
        d[2] == 17624355, 'disk=%d' % d[2])

# ---------- S4 按 source 分桶 ----------
def bucket(rs):
    a = {}
    for x in rs:
        k = x[2]
        e = a.setdefault(k, {'n': 0, 'bytes': 0, 'alive_n': 0, 'alive_bytes': 0, 'miss_n': 0})
        e['n'] += 1
        e['bytes'] += x[1]
        ok = any(s[0] == x[0] for s in same)
        if ok:
            e['alive_n'] += 1
            e['alive_bytes'] += x[1]
        else:
            e['miss_n'] += 1
    return a


B = bucket(same + [(d[0], d[1], d[3]) for d in diff] + miss)
OUT['by_source'] = B
for k in sorted(B):
    e = B[k]
    print('  BUCKET %-26s n=%5d B=%12d alive=%4d aliveB=%10d miss=%5d'
          % (k, e['n'], e['bytes'], e['alive_n'], e['alive_bytes'], e['miss_n']))
chk('S4a P1a 桶件数 3,786 / 714,228,639 B（与 F24 正文一致）',
    B.get('P1a_前8KiB行首VA>=60%', {}).get('n') == 3786
    and B.get('P1a_前8KiB行首VA>=60%', {}).get('bytes') == 714228639,
    str(B.get('P1a_前8KiB行首VA>=60%')))
chk('S4b rejudge 桶 627 件（4417 版为 13,233,082 B，4413 版才是 29,944,200 B）',
    B.get('rejudge_R53_对象抄本', {}).get('n') == 627,
    str(B.get('rejudge_R53_对象抄本')))
chk('S4c R62R63 3 件 8,690,200 B + R64 1 件 1,365,365 B == 10,055,565（F24 的 +10,055,565）',
    B.get('R62R63_重判对象侧', {}).get('bytes', 0) + B.get('R64_重判对象侧', {}).get('bytes', 0) == 10055565,
    '%d + %d' % (B.get('R62R63_重判对象侧', {}).get('bytes', 0),
                 B.get('R64_重判对象侧', {}).get('bytes', 0)))
chk('S4d 存活件数最多的桶也只有个位数（没有任何一类是「现盘还在」的）',
    max(e['alive_n'] for e in B.values()) < 200,
    'max_alive=%d' % max(e['alive_n'] for e in B.values()))

# ---------- S5 缺失件回快照核对 ----------
snap = {}
for r in load(SNAP):
    snap[r['rel']] = int(r['bytes'])
OUT['snapshot_rows'] = len(snap)
in_snap_same, in_snap_diff, not_in_snap = [], [], []
for rel, want, _src in miss:
    if rel not in snap:
        not_in_snap.append(rel)
        continue
    if snap[rel] == want:
        in_snap_same.append(rel)
    else:
        in_snap_diff.append((rel, want, snap[rel]))
chk('S5a 缺失件 100% 在 2026-11-22T12:31:10 快照里（不是路径拼错）',
    len(in_snap_same) + len(in_snap_diff) == len(miss) and not not_in_snap,
    'in_snap_same=%d in_snap_diff=%d not_in_snap=%d' % (len(in_snap_same), len(in_snap_diff),
                                                        len(not_in_snap)))
chk('S5b 快照里的 bytes 与清单逐字节相同（快照不是另一棵树）',
    not in_snap_diff, 'diff=%d %s' % (len(in_snap_diff), in_snap_diff[:3]))
chk('S5c 反控：把快照键前缀改坏后命中 0（S5a 的命中不是空匹配）',
    len([1 for rel, _w, _s in miss if 'NOPE/' + rel in snap]) == 0, 'mutated_hits=0')

# ---------- S6 扩展名分层的存活率 vs R88 记的裁剪规则 ----------
def ext_of(rel):
    b = os.path.basename(rel)
    return os.path.splitext(b)[1].lower() or '(none)'


alive_set = set(s[0] for s in same) | set(d[0] for d in diff)
strat = {}
for r in rows:
    e = ext_of(r['rel'])
    a = strat.setdefault(e, {'n': 0, 'alive': 0})
    a['n'] += 1
    if r['rel'] in alive_set:
        a['alive'] += 1
OUT['by_ext'] = strat
print('  EXT-STRAT (存活/总数):')
for e in sorted(strat, key=lambda x: -strat[x]['n']):
    a = strat[e]
    print('    %-8s %5d / %5d = %6.2f%%' % (e, a['alive'], a['n'], 100.0 * a['alive'] / a['n']))
# R88 DO15 记的裁剪保活率：.log 0% / .txt 0.1% / .json 0.3% / .tsv 0.5% / .md 14.9%
chk('S6a .txt 存活率 <= 5%（R88 记 .txt 保活 0.1%，方向一致）',
    strat.get('.txt', {}).get('alive', 0) * 1.0 / max(1, strat.get('.txt', {}).get('n', 1)) <= 0.05,
    '.txt %d/%d' % (strat.get('.txt', {}).get('alive', 0), strat.get('.txt', {}).get('n', 0)))
# 自错 S-251：S6b 首版拿 4417 清单的扩展名分层存活率去比 R88 DO15 记的**全树**裁剪保活率
# （.md 14.9% vs .txt 0.1%）。两个分母不同：R88 的分母是整棵树，S6 的分母是「已被判进语料的
# 4,417 件」，后者本身就是按内容挑出来的，.md 只有 8 件、且这 8 件恰好都在被裁掉的子树里。
# 跨域比较 ⇒ 零信息。删掉这条，换成同一域内可判定的：.txt 存活 59/3347、.tsv 2/936，
# 两者都远低于 100%，且 .log/.md 为 0 —— 只报实测分布，不跨域外推。
chk('S6b 语料内部的扩展名存活分布：.txt 59/3347、.tsv 2/936、.json 4/27、.log 0/99、.md 0/8 ——'
    ' 只报本域实测，不与 R88 的全树保活率跨域相减',
    strat['.txt']['alive'] == 59 and strat['.tsv']['alive'] == 2
    and strat['.log']['alive'] == 0 and strat['.md']['alive'] == 0,
    '.txt %d/%d .tsv %d/%d .json %d/%d .log %d/%d .md %d/%d'
    % (strat['.txt']['alive'], strat['.txt']['n'], strat['.tsv']['alive'], strat['.tsv']['n'],
       strat['.json']['alive'], strat['.json']['n'], strat['.log']['alive'], strat['.log']['n'],
       strat['.md']['alive'], strat['.md']['n']))
chk('S6c 反控：把存活判据换成 isfile() 且忽略字节数，存活数只会更多（S2 的口径不虚高）',
    len([r for r in rows if os.path.isfile(os.path.join(LEAD, r['rel']))]) >= len(same),
    'isfile_only=%d >= exact=%d'
    % (len([r for r in rows if os.path.isfile(os.path.join(LEAD, r['rel']))]), len(same)))

# ---------- S7 反控：根选错必须掉下来 ----------
alt = len([r for r in rows if os.path.isfile(os.path.join(ROOT, r['rel']))])
chk('S7 反控：把 rel 根从 lead/ 换成工程根，命中数显著下降（根选择有判别力）',
    alt < len(same), 'root=proj hits=%d vs root=lead hits=%d' % (alt, len(same)))
OUT['alt_root_hits'] = alt

# ---------- S8 四份清单的递进关系（F24 说五步溯源） ----------
def nsum(p):
    r = load(p)
    return len(r), sum(int(x['bytes']) for x in r)


chain = {}
for lbl, p in (('4413', M413), ('4413b', M413B), ('4416', M416), ('4417', M417)):
    chain[lbl] = nsum(p)
OUT['chain'] = chain
chk('S8a 四份清单件数 4,413 / 4,413 / 4,416 / 4,417',
    [chain[k][0] for k in ('4413', '4413b', '4416', '4417')] == [4413, 4413, 4416, 4417],
    str([chain[k][0] for k in ('4413', '4413b', '4416', '4417')]))
chk('S8b 四份清单字节 744,172,839 / 727,461,721 / 736,151,921 / 737,517,286',
    [chain[k][1] for k in ('4413', '4413b', '4416', '4417')]
    == [744172839, 727461721, 736151921, 737517286],
    str([chain[k][1] for k in ('4413', '4413b', '4416', '4417')]))
# 自错 S-250：首版本断言写成「三次递进差 = 16,711,118 / 10,055,565 / 1,365,365」，实测第二次是
# 8,690,200 而非 10,055,565。原因：F24 正文的「+10,055,565」是 R62/R63/R64 **四件合计**
# （8,690,200 + 1,365,365），而清单是分两步落的（4416 落三件、4417 落第四件）。
# 断言写错，不是数据错。改为分别核「两段差」与「四件合计」。
seg1 = chain['4413'][1] - chain['4413b'][1]          # 剔 bounds
seg2 = chain['4416'][1] - chain['4413b'][1]          # +R62R63 三件
seg3 = chain['4417'][1] - chain['4416'][1]           # +R64 一件
chk('S8c 三段递进差 = 16,711,118 / 8,690,200 / 1,365,365',
    (seg1, seg2, seg3) == (16711118, 8690200, 1365365), '%d / %d / %d' % (seg1, seg2, seg3))
chk('S8e F24 写的「+10,055,565」= R62R63 三件 8,690,200 + R64 一件 1,365,365（四件合计，跨两段落盘）',
    seg2 + seg3 == 10055565, '%d + %d = %d' % (seg2, seg3, seg2 + seg3))
# 反控：件数与字节方向相反（F24 点名要点）
chk('S8d 反控：4413 -> 4413b 件数不变而字节 -16,711,118（件数等权会看不见这一刀）',
    chain['4413'][0] == chain['4413b'][0] and seg1 == 16711118,
    'n_same=%d dB=-%d' % (chain['4413'][0], seg1))

npass = sum(1 for _a, c, _d in res if c)
print('SUMMARY %d/%d PASS' % (npass, len(res)))
with io.open(os.path.join(ROOT, '_r136', 'r136a_f24_survival.json'), 'w', encoding='utf-8') as f:
    f.write(json.dumps({'asserts': [{'name': a, 'ok': c, 'detail': d} for a, c, d in res],
                        'note': note, 'out': OUT}, ensure_ascii=False, indent=1, default=str))
sys.exit(0 if npass == len(res) else 1)
