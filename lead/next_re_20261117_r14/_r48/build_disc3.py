# -*- coding: utf-8 -*-
"""DISC_RECHECK.tsv v2：把「产物」列从描述变成可机械校验的（路径 + 校验式）。
新增两列：产物路径（repo 相对，空=文档内锚）、校验式（exists / bytes=N / rows=N / none）。
建表时**当场验证**每一条；不通过的降级为 none 并记入报告，绝不写成通过。
"""
import io, os, re, csv

ROOT = r'D:\Project\ra2-campaign-forge'
R14  = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
RC   = os.path.join(R14, 'R14_COMMON.md')
OUT  = os.path.join(R14, 'DISC_RECHECK.tsv')

lines = io.open(RC, encoding='utf-8', newline='').read().split('\n')
CANON = re.compile(r'(?:⇒\s*)?\*{0,2}纪律\s*(\d+)\s*·')
defs = {}
cur = None
for i, l in enumerate(lines):
    m = re.match(r'^##\s*(\d+(?:\.\d+)*)', l)
    if m: cur = m.group(1)
    mm = CANON.search(l)
    if mm:
        n = int(mm.group(1))
        if cur and cur.startswith('2.') and float(cur.split('.')[1]) >= 14 and n not in defs:
            defs[n] = (cur, i + 1, l.strip())

# (产物路径, 校验式, 回跑类型 L/S, 锚描述)
M = {
 1: (r'lead\next_re_20261117_r14\R14_COMMON.md', 'exists', 'L', '§8.1 错源清单 / F32 锚（§2.21 已核改指）'),
 2: (r'lead\next_re_20261117_r14\R14_COMMON.md', 'exists', 'L', '§8.1 第 ⑲ 项 vs F32 主张（§2.21 落更正）'),
 3: (r'lead\next_re_20261117_r14\R17_R61_FACTINDEX_V58\anchor_check.txt', 'exists', 'L', 'v5.8 基线：人工核验类 0'),
 4: (r'lead\next_re_20261117_r14\R17_R61_FACTINDEX_V58\anchor_check.txt', 'exists', 'L', '节号体例锚逐条列名'),
 5: (r'lead\next_re_20261117_r14\R17_R64_ADEQUACY2\lead_recheck2.tsv', 'exists', 'L', 'F04 的锚集合复算'),
 6: (r'lead\next_re_20261117_r14\R17_R64_ADEQUACY2\lead_recheck2.tsv', 'exists', 'L', 'F04「在自己的锚里找到」复算'),
 7: (r'lead\next_re_20261117_r14\R17_R62_ADEQUACY\lead_recheck.tsv', 'exists', 'L', '13 条 PARTIAL 全量复算（驳回 9）'),
 8: (r'lead\next_re_20261117_r14\R17_R66_FACTINDEX_V511\CHANGES.md', 'exists', 'L', 'F32/F35 锚 vs limitations 两处修'),
 9: (r'lead\next_re_20261117_r14\R14_COMMON.md', 'exists', 'L', '台账 §NNNN vs §x.y 分命名空间后 0 误报'),
 10:(r'lead\next_re_20261117_r14\R17_R66_FACTINDEX_V511\CHANGES.md', 'exists', 'L', '定位 F40 锚翻类'),
 11:(r'lead\next_re_20261117_r14\_r38\checkC3_report.md', 'exists', 'S', 'C3 双相反向注入'),
 12:(r'lead\next_re_20261117_r14\_r38\checkC3_report.md', 'exists', 'S', '报告头闭集合声明'),
 13:(r'lead\next_re_20261117_r14\_r38\checkC3.py', 'exists', 'S', 'C3 正控/反控两行'),
 14:(r'lead\next_re_20261117_r14\_r38\checkC3.py', 'exists', 'S', 'FAIL 也留盘'),
 15:(r'lead\next_re_20261117_r14\_r38\settle_iat.py', 'exists', 'S', '三方混用量 339/339'),
 16:(r'lead\next_re_20261117_r14\R17_R72_T1_CLEANSCALE\REPORT.md', 'exists', 'S', 'R16 三文件未触碰证明'),
 17:(r'lead\next_re_20261117_r14\R16_MEASURE_EVID675\mev675.py', 'exists', 'S', 'stage_scale 排除项'),
 18:(r'lead\next_re_20261117_r14\R17_R70_T1_REPRO\REPORT.md', 'exists', 'L', '「无产物」时间顺序核查'),
 19:(r'lead\next_re_20261117_r14\R17_R75_T2_DRIFT\REPORT.md', 'exists', 'S', '漂移分解 97%/2.7% 逐字节闭合'),
 20:(r'lead\next_re_20261117_r14\check_disc.py', 'exists', 'L', '生成脚本禁不可见字符断言'),
 21:(r'lead\next_re_20261117_r14\R17_R78_T4_AUDIT30\REPORT.md', 'exists', 'S', '2×2 溯源表逐格复算'),
 22:(r'lead\next_re_20261117_r14\R17_R84_T1_NARRATIVE\should_exclude.tsv', 'rows=1468', 'L', 'C′ 内备份副本 1,468 件 / 149,493,508 B'),
 23:(r'lead\next_re_20261117_r14\R17_R78_T1_RECLASS\REPORT.md', 'exists', 'S', '重分类判据表 8 族'),
 24:(r'lead\next_re_20261117_r14\R17_R78_T4_AUDIT30\REPORT.md', 'exists', 'L', '档 C 撤回是否过正（2×2）'),
 25:(r'lead\next_re_20261117_r14\R17_R78_T2_REGEXDIFF\REPORT.md', 'exists', 'L', 're.I 丢失：375 vs 333'),
 26:(r'lead\next_re_20261117_r14\R17_R78_T1_RECLASS\files_tier_Cprime.tsv', 'rows=18712', 'S', 'C′ 的 why 分布 P0 77.7%'),
 27:(r'lead\next_re_20261117_r14\R17_R81_T2_EVID\_verdicts.tsv', 'rows=1242', 'L', '_verdicts 的 verdict 分布'),
 28:(r'lead\next_re_20261117_r14\R17_R88_T1_SEMDEF\tier_final.tsv', 'rows=4518', 'L', '快照 rel 表 vs 当轮盘上内容'),
}

def check(path, expr):
    """返回 (ok, detail)。ok=False 时 detail 说明原因。"""
    ap = os.path.join(ROOT, path.replace('\\', '/'))
    if not os.path.isfile(ap):
        return False, 'FILE_MISSING'
    if expr == 'exists':
        return True, '%d B' % os.path.getsize(ap)
    m = re.fullmatch(r'bytes=(\d+)', expr)
    if m:
        want = int(m.group(1)); got = os.path.getsize(ap)
        return (got == want), 'bytes %d vs %d' % (got, want)
    m = re.fullmatch(r'rows=(\d+)', expr)
    if m:
        want = int(m.group(1))
        n = 0
        with io.open(ap, encoding='utf-8', errors='replace') as f:
            for i, _ in enumerate(f):
                n += 1
        got = n - 1  # 去表头
        return (got == want), 'rows %d vs %d' % (got, want)
    return False, 'BAD_EXPR'

rows, downgraded = [], []
for n in sorted(defs):
    sec, ln, txt = defs[n]
    judge = re.sub(r'\s+', ' ', txt).replace('\t', ' ')
    if len(judge) > 180:
        judge = judge[:177] + '…'
    path, expr, typ, anchor = M.get(n, ('', 'none', 'N', '无'))
    if path:
        ok, detail = check(path, expr)
        if not ok:
            downgraded.append((n, expr, detail))
            expr = 'none'
        else:
            expr = '%s ✓(%s)' % (expr, detail)
    later = '有（后续轮回跑）' if typ == 'L' else ('无（仅立条当轮自带）' if typ == 'S' else '无')
    rows.append([str(n), '§' + sec, judge, anchor, path or '（文档内锚）', expr, later])

header = ['纪律号', '节', '可执行判据（逐字截取）', '必查的现有数据锚', '产物路径', '校验式', '立条之后是否回跑过']
tmp = OUT + '.tmp'
with open(tmp, 'w', encoding='utf-8', newline='') as f:
    w = csv.writer(f, delimiter='\t', lineterminator='\n')
    w.writerow(header)
    for r in rows:
        w.writerow(r)

back = io.open(tmp, encoding='utf-8', newline='').read()
assert '\r' not in back
bl = [l for l in back.split('\n') if l]
assert len(bl) == 29, len(bl)
for l in bl:
    assert l.count('\t') == 6, (l.count('\t'), l[:90])
os.replace(tmp, OUT)

ok_cnt = sum(1 for r in rows if '✓' in r[5])
L = sum(1 for r in rows if r[6].startswith('有'))
S = sum(1 for r in rows if r[6].startswith('无（仅'))
print('纪律 %d 条；校验式实测通过 %d 条；回跑 有 %d / 仅自带 %d' % (len(rows), ok_cnt, L, S))
if downgraded:
    print('降级为 none 的：')
    for n, e, d in downgraded:
        print('   纪律 %-3d %-12s %s' % (n, e, d))
else:
    print('无降级项')
print('写出', OUT, os.path.getsize(OUT), 'B ; 7 列 x %d 行' % len(bl))
