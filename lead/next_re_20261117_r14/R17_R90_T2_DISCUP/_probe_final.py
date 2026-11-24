# -*- coding: utf-8 -*-
"""最终提取式验证（只读产物）。表达式均不含字面空格，使用 \\s 代替。"""
import io, os, re
ROOT = r'D:\Project\ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
def read(rel):
    return io.open(os.path.join(ROOT, rel.replace('\\','/')), encoding='utf-8', errors='replace').read()

FINAL = [
 (3,  r'lead\next_re_20261117_r14\R17_R61_FACTINDEX_V58\anchor_check.txt', r'grep=池未加载\(未核验\)\s+0'),
 (4,  r'lead\next_re_20261117_r14\R17_R61_FACTINDEX_V58\anchor_check.txt', r'grep=节号体例通过\s+15'),
 (5,  r'lead\next_re_20261117_r14\R17_R64_ADEQUACY2\lead_recheck2.tsv', r'grep=复合条目的锚是并集'),
 (6,  r'lead\next_re_20261117_r14\R17_R64_ADEQUACY2\lead_recheck2.tsv', r'grep=审计把「在锚里」说成「不在锚里」'),
 (7,  r'lead\next_re_20261117_r14\R17_R62_ADEQUACY\lead_recheck.tsv', r'grep=REFUTED-OVERSTRICT'),
 (8,  r'lead\next_re_20261117_r14\R17_R66_FACTINDEX_V511\CHANGES.md', r'grep=列与列之间没有同步'),
 (10, r'lead\next_re_20261117_r14\R17_R66_FACTINDEX_V511\CHANGES.md', r'grep=当不变量用的只有'),
 (11, r'lead\next_re_20261117_r14\_r38\checkC3_report.md', r'grep=控制组总判定：\*\*PASS'),
 (12, r'lead\next_re_20261117_r14\_r38\checkC3_report.md', r'grep=闭集合声明（纪律 12①）'),
 (13, r'lead\next_re_20261117_r14\_r38\checkC3.py', r'grep=控制组（四个子检查全都要）'),
 (14, r'lead\next_re_20261117_r14\_r38\checkC3.py', r'grep=checkC3_report_FAIL\.md'),
 (15, r'lead\next_re_20261117_r14\_r38\settle_iat.py', r'grepcount=所在节分布=3'),
 (16, r'lead\next_re_20261117_r14\R17_R72_T1_CLEANSCALE\REPORT.md', r'grepcount=\*\*相同\*\*=3'),
 (17, r'lead\next_re_20261117_r14\R16_MEASURE_EVID675\mev675.py', r'grepcount=out_excl=2'),
 (18, r'lead\next_re_20261117_r14\R17_R70_T1_REPRO\REPORT.md', r'grep=12:07.*无产物'),
 (19, r'lead\next_re_20261117_r14\R17_R75_T2_DRIFT\REPORT.md', r'grep=逐字节闭合'),
 (21, r'lead\next_re_20261117_r14\R17_R78_T4_AUDIT30\REPORT.md', r'grep=2×2\s*溯源表'),
 (23, r'lead\next_re_20261117_r14\R17_R78_T1_RECLASS\REPORT.md', r'grep=为什么该在一边'),
 (24, r'lead\next_re_20261117_r14\R17_R78_T4_AUDIT30\REPORT.md', r'grep=附注性限定语'),
 (25, r'lead\next_re_20261117_r14\R17_R78_T2_REGEXDIFF\REPORT.md', r'grep=丢\s*re\.I'),
]

def parse(e):
    if e.startswith('grepcount='):
        body=e[len('grepcount='):]; pat,want=body.rsplit('=',1); return 'gc',pat,int(want)
    pat=e[len('grep='):]; return 'g',pat,None

allok=True
for num,path,expr in FINAL:
    t=read(path); kind,pat,want=parse(expr); n=len(re.findall(pat,t))
    if kind=='g': ok = n>=1; detail='hits=%d'%n
    else: ok = n==want; detail='hits=%d want=%d'%(n,want)
    allok &= ok
    print('D%-3s %-4s %-3s %-52r %s %s' % (num,'OK' if ok else 'BAD',kind,pat,detail, '' if ok else '<<<<'))
print('ALL OK' if allok else 'SOME BAD')
