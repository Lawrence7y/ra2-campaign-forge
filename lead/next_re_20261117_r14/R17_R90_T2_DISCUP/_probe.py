# -*- coding: utf-8 -*-
"""候选提取式验证：只读取产物，测试正则命中次数，不写任何既有文件。"""
import io, os, re
ROOT = r'D:\Project\ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')

def read(rel):
    return io.open(os.path.join(ROOT, rel.replace('\\','/')), encoding='utf-8', errors='replace').read()

# (纪律, 产物相对路径, 描述, [(kind, pattern, want)])
C = [
 (3, r'lead\next_re_20261117_r14\R17_R61_FACTINDEX_V58\anchor_check.txt', '未核验单列为0',
     [('grep', r'池未加载\(未核验\)\s+0', None), ('grep', r'MISS\s+0', None), ('grep', r'\[exit 0\]', None)]),
 (4, r'lead\next_re_20261117_r14\R17_R61_FACTINDEX_V58\anchor_check.txt', '节号体例通过',
     [('grep', r'节号体例通过\s+15', None), ('grep', r'PASS\s+D 节号体例', None)]),
 (5, r'lead\next_re_20261117_r14\R17_R64_ADEQUACY2\lead_recheck2.tsv', '并集REFUTED4条',
     [('grepcount', r'REFUTED', 4), ('rows', None, 4)]),
 (6, r'lead\next_re_20261117_r14\R17_R64_ADEQUACY2\lead_recheck2.tsv', '自己锚里找到',
     [('grep', r'evidence_paths', None), ('grep', r'REFUTED', None)]),
 (7, r'lead\next_re_20261117_r14\R17_R62_ADEQUACY\lead_recheck.tsv', '13条复核',
     [('grepcount', r'REFUTED', None), ('rows', None, 19), ('grep', r'REFUTED-OVERSTRICT', None)]),
 (11, r'lead\next_re_20261117_r14\_r38\checkC3_report.md', '控制组PASS',
     [('grep', r'控制组总判定：\*\*PASS —— 后续结论可读\*\*', None), ('grepcount', r'^- PASS ', 11)]),
 (12, r'lead\next_re_20261117_r14\_r38\checkC3_report.md', '闭集合声明',
     [('grep', r'闭集合声明（纪律 12①）', None), ('grep', r'均不可穷尽', None)]),
 (13, r'lead\next_re_20261117_r14\_r38\checkC3.py', '四子检查控制组',
     [('grep', r'控制组（四个子检查全都要）', None), ('grepcount', r'^\s*ok\(', None)]),
 (14, r'lead\next_re_20261117_r14\_r38\checkC3.py', 'FAIL也留盘',
     [('grep', r'报告先落盘', None), ('grep', r'FAIL 也留盘', None), ('grep', r'checkC3_report_FAIL\.md', None)]),
 (15, r'lead\next_re_20261117_r14\_r38\settle_iat.py', '三方分离',
     [('grepcount', r'所在节分布', 3), ('grep', r'339 全在', None)]),
 (16, r'lead\next_re_20261117_r14\R17_R72_T1_CLEANSCALE\REPORT.md', '三文件未触碰',
     [('grepcount', r'\*\*相同\*\*', 3), ('grep', r'未触碰证明', None)]),
 (17, r'lead\next_re_20261117_r14\R16_MEASURE_EVID675\mev675.py', '排除自身产物',
     [('grep', r'SELFREF_NAME', None), ('grep', r'out_excl', None), ('grepcount', r'out_excl', 2)]),
 (18, r'lead\next_re_20261117_r14\R17_R70_T1_REPRO\REPORT.md', '无产物时间顺序',
     [('grep', r'无产物', None), ('grep', r'当时那一刻', None)]),
 (19, r'lead\next_re_20261117_r14\R17_R75_T2_DRIFT\REPORT.md', '逐字节闭合',
     [('grep', r'逐字节闭合', None), ('grep', r'3,441,605\+95,965=3,537,570', None)]),
 (21, r'lead\next_re_20261117_r14\R17_R78_T4_AUDIT30\REPORT.md', '2x2溯源',
     [('grep', r'2×2 溯源表', None), ('grep', r're\.I', None)]),
 (23, r'lead\next_re_20261117_r14\R17_R78_T1_RECLASS\REPORT.md', '8族判据',
     [('grep', r'为什么该在一边', None), ('grep', r'E1\.\.E6 排除', None)]),
 (24, r'lead\next_re_20261117_r14\R17_R78_T4_AUDIT30\REPORT.md', '构成性限定语',
     [('grep', r'构成性.*限定语', None), ('grep', r'附注性限定语', None)]),
 (25, r'lead\next_re_20261117_r14\R17_R78_T2_REGEXDIFF\REPORT.md', 're.I丢失',
     [('grep', r'丢 re\.I', None), ('grep', r'375 / 184,618,279', None)]),
]

for num, path, desc, tests in C:
    txt = read(path)
    print('=== 纪律 %s | %s | %s' % (num, os.path.basename(path), desc))
    for kind, pat, want in tests:
        if kind == 'grep':
            n = len(re.findall(pat, txt))
            print('    grep  %-45r hits=%d %s' % (pat, n, '' if n>=1 else '<<NO MATCH'))
        elif kind == 'grepcount':
            n = len(re.findall(pat, txt))
            print('    gc    %-45r hits=%d want=%s %s' % (pat, n, want, '' if (want is None or n==want) else '<<MISMATCH'))
        elif kind == 'rows':
            lines = txt.split('\n')
            data = len(lines)-1 if txt.endswith('\n') else len(lines)-1
            print('    rows  data=%d want=%s' % (data, want))
