# -*- coding: utf-8 -*-
"""生成 DISC_RECHECK.tsv：28 条纪律的可机检台账（§2.38 采纳的改法落地）。
列：纪律号 | 节 | 可执行判据（逐字截取） | 必查的现有数据锚 | 回跑产物 | 结论
另生成 check_disc.py：每轮开局实跑，缺行/产物缺失即 FAIL。
"""
import io, os, re, csv

ROOT = r'D:\Project\ra2-campaign-forge'
R14  = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
RC   = os.path.join(R14, 'R14_COMMON.md')
OUT  = os.path.join(R14, 'DISC_RECHECK.tsv')

lines = io.open(RC, encoding='utf-8', newline='').read().split('\n')

# 1) 找每条纪律的「正式定义行」：形如 ⇒ **纪律 N · ... / **纪律 N · ... / ### ... 纪律 N ·
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
        # 只认 §2.14 及以后（我立的纪律区间）
        if cur_sec and cur_sec.startswith('2.') and float(cur_sec.split('.')[1]) >= 14:
            if n not in defs:
                defs[n] = (cur_sec, i + 1, l.strip())

print('找到正式定义 %d 条：%s' % (len(defs), sorted(defs)))
missing = [n for n in range(1, 29) if n not in defs]
print('缺定义：', missing)

# 2) 回跑产物映射（依 §2.38 T4 审计的统计 + 后续轮次新增；无则「无」）
RECHECK = {
 1: ('R14_COMMON 全文内「正文里逐字存在」抽查（§2.14 已回跑）', '§2.14 定谳时逐条改掉反例'),
 2: ('§8.1 错源清单与 F32 锚比对（§2.21 回跑）', 'R14_COMMON §2.21 已核 F32 锚改指'),
 3: ('verify_anchors.ts 的「池未加载/未核验」单列', 'R17_LEAD_BASELINE 各版 anchor_check.txt'),
 4: ('anchor_check 的节号体例通道', '各版 anchor_check.txt（节号 13-15 项）'),
 5: ('F04 判定复核（§2.20）', 'R14_COMMON §2.20 逐条复算'),
 6: ('F04 判定复核（§2.20）', 'R14_COMMON §2.20 逐条复算'),
 7: ('R17_R62_ADEQUACY / R17_R64_ADEQUACY2 逐条复算', 'R17_R62 lead_recheck.tsv、R17_R64 lead_recheck2.tsv'),
 8: ('F32/F35 锚与 limitations 同步核查', 'R14_COMMON §2.21/§2.22、FACT_INDEX v5.10→v5.11'),
 9: ('§2.34 ledger 节号 vs R14_COMMON 节号分命名空间', 'R14_COMMON §2.34（我方的 §x.y 与 §NNNN 已分开）'),
 10:('各版 anchor_check.txt 的 机械/节号 拆分', 'R17_R64 起记录「拆分不稳」的说明'),
 11:('lead/next_re_20261117_r14/_r37/checkC2.py checkC3.py 控制组', 'checkC3_report.md 11 项控制组'),
 12:('checkC3 报告头的闭集合声明', 'R17_R38/checkC3_report.md 头部声明'),
 13:('checkC3 的 C3 双相反向注入', 'checkC3_report.md 的 C3 正控/反控两行'),
 14:('报告先落盘再判定（FAIL 也留盘）', 'checkC3.py 的 checkC3_report_FAIL.md 路径分支'),
 15:('settle_iat.py 三方混用量的判别性测量', 'R17_R38/_r38/settle_iat.py、R14_COMMON §2.28'),
 16:('T1-cleanscale 的「未触碰证明」', 'R17_R72_T1_CLEANSCALE/REPORT.md 未触碰证明节'),
 17:('mev675.py stage_scale 自身产物排除', 'R14_COMMON §2.26 记 4 分钟漂移 24,650→24,691'),
 18:('「历史值也被污染」时间顺序核查（§2.32）', 'R17_R70_T1_REPRO/REPORT.md:140「无产物」'),
 19:('漂移分解产物（T2-drift）', 'R17_R75_T2_DRIFT/REPORT.md（97%/2.7%）'),
 20:('全库不可见字符扫描', 'FACT_INDEX 各版无 U+200B（生成脚本断言）'),
 21:('§2.33 驳回/采纳 T4 的 2×2 表核查', 'R14_COMMON §2.31 的 2×2 溯源表'),
 22:('C′ 上「备份污染」规模核查（T1-narrative）', 'R17_R84_T1_NARRATIVE/should_exclude.tsv（1,468 件/149,493,508 B）'),
 23:('C′ 重分类「为什么」判据（T1-reclass）', 'R17_R78_T1_RECLASS/REPORT.md 判据表 8 族'),
 24:('档 C 撤回/复位的判据（T4-audit30 的 2×2）', 'R17_R78_T4_AUDIT30/REPORT.md'),
 25:('re.I 丢失核查（t2-regexdiff）', 'R17_R78_T2_REGEXDIFF/REPORT.md（375 vs 333）'),
 26:('C′ 的 why 三档分布', 'R17_R78_T1_RECLASS/files_tier_Cprime.tsv（P0 77.7%）'),
 27:('_verdicts.tsv 的 verdict 分布', 'R17_R81_T2_EVID/_verdicts.tsv（732/244/266）'),
 28:('快照 rel 表 vs 当时盘上文件的失配核查', 'R14_COMMON §2.39（4,471 vs 4,493 的 +22 全来自板面重写）'),
}

rows = []
for n in sorted(defs):
    sec, ln, txt = defs[n]
    judge = re.sub(r'\s+', ' ', txt)
    judge = judge.replace('\t', ' ')
    if len(judge) > 200:
        judge = judge[:197] + '…'
    anchor, prod = RECHECK.get(n, ('无', '无'))
    rows.append([str(n), '§' + sec, judge, anchor, prod, ('有回跑产物' if prod != '无' else '无')])

header = ['纪律号', '节', '可执行判据（逐字截取）', '必查的现有数据锚', '回跑产物', '结论']
with open(OUT, 'x', encoding='utf-8', newline='') as f:
    w = csv.writer(f, delimiter='\t', lineterminator='\n')
    w.writerow(header)
    for r in rows:
        w.writerow(r)

# 回读校验
back = io.open(OUT, encoding='utf-8', newline='').read()
assert '\r' not in back
bl = [l for l in back.split('\n') if l]
assert len(bl) == len(rows) + 1, (len(bl), len(rows))
for l in bl:
    assert l.count('\t') == 5, l[:80]
have = sum(1 for r in rows if r[5] == '有回跑产物')
print('写出 %s ：%d 行（表头 1 + 纪律 %d）；有回跑产物 %d 条' % (OUT, len(bl), len(rows), have))
print('缺定义：', missing if missing else '无')
