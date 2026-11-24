# -*- coding: utf-8 -*-
"""修正 DISC_RECHECK.tsv：把「立条当轮自带产物」与「立条之后某轮回跑」分开。
诚实口径：只有「后续轮次回头按该纪律查过既有数据」才算回跑。
"""
import io, os, re, csv

ROOT = r'D:\Project\ra2-campaign-forge'
R14  = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
RC   = os.path.join(R14, 'R14_COMMON.md')
OUT  = os.path.join(R14, 'DISC_RECHECK.tsv')

lines = io.open(RC, encoding='utf-8', newline='').read().split('\n')
CANON = re.compile(r'(?:⇒\s*)?\*{0,2}纪律\s*(\d+)\s*·')
defs = {}
cur_sec = None
for i, l in enumerate(lines):
    m = re.match(r'^##\s*(\d+(?:\.\d+)*)', l)
    if m:
        cur_sec = m.group(1)
    mm = CANON.search(l)
    if mm:
        n = int(mm.group(1))
        if cur_sec and cur_sec.startswith('2.') and float(cur_sec.split('.')[1]) >= 14:
            if n not in defs:
                defs[n] = (cur_sec, i + 1, l.strip())

# (锚, 产物, 类型)
# 类型：L = 立条之后某轮回头按它查过既有数据（真回跑）
#       S = 立条当轮即产出该纪律要求的产物（自带，不算回跑）
#       N = 无产物
M = {
 1:  ('§8.1 错源清单 / F32 锚',            'R14_COMMON §2.21 核 F32 锚改指',            'L'),
 2:  ('§8.1 第 ⑲ 项 vs F32 主张',          'R14_COMMON §2.21 落 §2.21 更正',            'L'),
 3:  ('verify_anchors 六分类计数',           'R14_COMMON §2.17 的 v5.8 基线（人工 0）',    'L'),
 4:  ('anchor_check 的 15 项节号体例锚',     'R14_COMMON §2.17 逐条列名',                 'L'),
 5:  ('F04 的锚集合',                        'R14_COMMON §2.20 复算驳回',                 'L'),
 6:  ('F04「在自己的锚里找到」',              'R14_COMMON §2.20 复算驳回',                 'L'),
 7:  ('R17_R62/R64 adequacy 的 13 条 PARTIAL','R14_COMMON §2.20 全量复算（驳回 9）',       'L'),
 8:  ('F32/F35 锚 vs limitations',           'R14_COMMON §2.21/§2.22 两处修',             'L'),
 9:  ('台账 §NNNN vs R14_COMMON §x.y',       'R14_COMMON §2.34 分命名空间后 0 误报',      'L'),
 10: ('各版 anchor_check 的机械/节号拆分',   'R14_COMMON §2.22 定位 F40 翻类',            'L'),
 11: ('checkC2 的 C3 控制组',                'checkC3.py 11 项控制组（C3 双相反向注入）', 'S'),
 12: ('checkC3 报告头的闭集合声明',          'checkC3_report.md 头三行',                  'S'),
 13: ('C3 正控/反控两行',                    'checkC3_report.md 控制组 11 项',            'S'),
 14: ('checkC3.py 的 FAIL 分支',             'checkC3.py 落盘先于判定（FAIL 也留盘）',    'S'),
 15: ('三方混用的量（ILT/IAT/槽内容）',       'settle_iat.py 三件各 339/339',              'S'),
 16: ('R16_MEASURE_EVID675 三文件',          'T1-cleanscale 开工/收工 mtime 对比',        'S'),
 17: ('mev675.py stage_scale 排除项',        'R14_COMMON §2.26 记 4 分钟漂移',            'S'),
 18: ('「历史值也被污染」这条断言',          'R14_COMMON §2.32 查 REPORT.md:140「无产物」','L'),
 19: ('漂移分解产物',                        'R17_R75_T2_DRIFT（97%/2.7%，逐字节闭合）',  'S'),
 20: ('全库不可见字符',                      'R39 从手写卡清除 U+200B；生成脚本断言',      'L'),
 21: ('T4 的 2×2 溯源表',                    'R14_COMMON §2.31 逐格复算',                 'S'),
 22: ('C′ 内备份副本占比',                   'R17_R84_T1_NARRATIVE should_exclude.tsv',   'L'),
 23: ('C′ 重分类判据',                       'R17_R78_T1_RECLASS 判据表 8 族',            'S'),
 24: ('档 C 撤回是否过正',                    'R17_R78_T4_AUDIT30 2×2 表',                 'L'),
 25: ('re.I 是否丢失',                       'R17_R78_T2_REGEXDIFF（375 vs 333）',        'L'),
 26: ('C′ 的 why 分布',                      'R14_COMMON §2.34 引 P0 77.7%',              'S'),
 27: ('_verdicts.tsv 的 verdict 列',         'R14_COMMON §2.36 数出 732/244/266',         'L'),
 28: ('快照 rel 表 vs 当轮盘上内容',          'R14_COMMON §2.39 查 4,471 vs 4,493',        'L'),
}
# 明确「无回跑」的（T4 审计点名 7/9/10/12/13/20/25/27/28 中未后来回跑者）；此处按证据判定：
NO_RECHECK = set()   # 若某条只有 S 无 L，则「回跑=无」

rows = []
for n in sorted(defs):
    sec, ln, txt = defs[n]
    judge = re.sub(r'\s+', ' ', txt).replace('\t', ' ')
    if len(judge) > 200:
        judge = judge[:197] + '…'
    anchor, prod, typ = M.get(n, ('无', '无', 'N'))
    later = '有（后续轮回跑）' if typ == 'L' else ('无（仅立条当轮自带）' if typ == 'S' else '无')
    rows.append([str(n), '§' + sec, judge, anchor, prod, later])

header = ['纪律号', '节', '可执行判据（逐字截取）', '必查的现有数据锚', '产物', '立条之后是否回跑过']
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
    assert l.count('\t') == 5, l[:80]
L = sum(1 for r in rows if r[5].startswith('有'))
S = sum(1 for r in rows if r[5].startswith('无（仅'))
N = sum(1 for r in rows if r[5] == '无')
print('纪律 %d 条：后续轮回跑 %d / 仅立条当轮自带 %d / 无 %d' % (len(rows), L, S, N))
os.replace(tmp, OUT)
print('写出', OUT, 'bytes=', os.path.getsize(OUT))
