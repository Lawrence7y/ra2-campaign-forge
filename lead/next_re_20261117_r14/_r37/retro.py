# -*- coding: utf-8 -*-
"""R37 Check C 回溯测试：把 C1/C2/C3 跑遍全部 19 个历史版本，
看这套检查器「过去能抓到什么」——用于自证它不是弱检查。
"""
import io, os, re, importlib.util, sys

ROOT = r'D:\Project\ra2-campaign-forge'
R14  = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')

spec = importlib.util.spec_from_file_location('checkC', os.path.join(R14, '_r37', 'checkC.py'))
# 不能直接 import（脚本会跑主流程并 exit），故复制其函数：改为按源码 exec 到受限命名空间
src = io.open(os.path.join(R14, '_r37', 'checkC.py'), encoding='utf-8').read()
# 截掉「判别力自证」之后的主流程
cut = src.index('# ---------- 判别力自证 ----------')
ns = {'__name__': 'cc'}
exec(compile(src[:cut], 'checkC_core', 'exec'), ns)
load, check_C1, check_C2, check_C3 = ns['load'], ns['check_C1'], ns['check_C2'], ns['check_C3']

DIRS = [
    ('v1?',  'R17_R34_FACT_INDEX'),
    ('v1b',  'R17_R38_FACTINDEX_FIX'),
    ('v3',   'R17_R40_FACTINDEX_V3'),
    ('F23',  'R17_R42_F23_FIX'),
    ('v3.2', 'R17_R44_FACTINDEX_V32'),
    ('v4',   'R17_R45_FACTINDEX_V4'),
    ('v5',   'R17_R46_FACTINDEX_V5'),
    ('grade','R17_R47_GRADE_NORM'),
    ('v5.2', 'R17_R51_FACTINDEX_V52'),
    ('v5.3', 'R17_R56_FACTINDEX_V53'),
    ('v5.4', 'R17_R57_FACTINDEX_V54'),
    ('v5.5', 'R17_R58_FACTINDEX_V55'),
    ('v5.6', 'R17_R59_FACTINDEX_V56'),
    ('v5.7', 'R17_R60_FACTINDEX_V57'),
    ('v5.8', 'R17_R61_FACTINDEX_V58'),
    ('v5.9', 'R17_R63_FACTINDEX_V59'),
    ('v5.10','R17_R65_FACTINDEX_V510'),
    ('v5.11','R17_R66_FACTINDEX_V511'),
    ('v5.12','R17_R67_FACTINDEX_V512'),
]

print('%-7s %-24s %4s %4s %4s   %s' % ('ver', 'dir', 'rows', 'C1', 'C2', 'C3 / 命中明细'))
print('-' * 110)
rows_out = []
for ver, d in DIRS:
    p = os.path.join(R14, d, 'FACT_INDEX.tsv')
    if not os.path.exists(p):
        print('%-7s %-24s (missing)' % (ver, d)); continue
    try:
        rows = load(p)
    except Exception as e:
        print('%-7s %-24s LOAD-ERR %s' % (ver, d, e)); continue
    c1 = c2 = c3 = 0
    det = []
    for r in rows:
        a, b, c = check_C1(r), check_C2(r), check_C3(r)
        if a:
            c1 += 1; det.append('C1:%s%s' % (r['fact_id'], [t for t, _ in a]))
        if b:
            c2 += 1; det.append('C2:%s%s' % (r['fact_id'], [w for w, _ in b]))
        if c:
            c3 += 1; det.append('C3:%s%s' % (r['fact_id'], c))
    print('%-7s %-24s %5d %4d %4d %4d   %s' % (ver, d, len(rows), c1, c2, c3, '; '.join(det[:6])))
    rows_out.append((ver, d, len(rows), c1, c2, c3, det))

print()
print('=== 汇总 ===')
tot = [r for r in rows_out if r[3] or r[4] or r[5]]
print('有命中的版本数 = %d / %d' % (len(tot), len(rows_out)))
for r in tot:
    print('  %s %s  C1=%d C2=%d C3=%d' % (r[0], r[1], r[3], r[4], r[5]))
io.open(os.path.join(R14, '_r37', 'checkC_retro.txt'), 'w', encoding='utf-8').write(
    '\n'.join('%s\t%s\t%d\t%d\t%d' % (r[0], r[1], r[3], r[4], r[5]) for r in rows_out))
