#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R139 主会话：F35 的三个真断言 vs 一个伪断言，逐条机械判定。

为什么要做这一步：R138 把「proved_strict 定义缺一手权威」写进了 FACT_INDEX v5.33 的
F35 limitations，但现盘其实有**代码级**权威实现。这条必须拆成四个可分别判真假的主张：

  P1  定义在现盘有一手代码权威（strict_panel.py:78，逐字带方括号）
  P2  另有 3 处同判据的独立实现（M59-MERGE 的 precheck/simulate/verify）
  P3  F35 的 evidence_paths 只引 PANEL.md 一条（单点证据）—— 这条是真的
  P4  该脚本的两个输入（coverage.tsv / function_atlas.tsv）都不在现盘 —— 这条也是真的

所以正确的表述是「定义在盘、数据与面板不在盘」，不是「定义缺一手权威」。
本脚本输出 4 条判定的实测值，并给出「P1 与 R138 的表述互斥」这一形式判据。
"""
import os
import json

ROOT = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
SP = os.path.join(R14, 'RULING_R15_20261119', 'work', 'strict_panel.py')
M59 = os.path.join(R14, '_cards', 'M59-MERGE')
F533 = os.path.join(R14, 'R17_R105_FACTINDEX_V533', 'FACT_INDEX.tsv')

res = {}
fails = []


def ck(name, cond, detail=''):
    print(('  PASS ' if cond else '  FAIL ') + name + (('  ' + str(detail)) if detail else ''))
    if not cond:
        fails.append(name)


print('=== P1 定义有现盘一手代码权威 ===')
sp = open(SP, encoding='utf-8').read()
L = sp.split('\n')
res['p1_line78'] = L[77].strip()
res['p1_docstring14'] = L[13].strip()
ck('P1.1 判据行逐字 == if "[未证]" not in sem:', L[77].strip() == 'if "[未证]" not in sem:')
ck('P1.2 docstring 同条件散文措辞带方括号', '不含 [未证]' in L[13])
ck('P1.3 全文件不含裸子串口径写法（即无 if 未证 not in sem）',
   'if 未证 not in sem' not in sp)

print('\n=== P2 其余同判据实现 ===')
# 用逐字串匹配（不用正则），列全所有命中文件
targets = ['precheck.py', 'simulate.py', 'verify.py', 'merge_panel.py']
seen = {}
for f in targets:
    p = os.path.join(M59, f)
    if not os.path.exists(p):
        continue
    txt = open(p, encoding='utf-8').read()
    hits = [i for i, l in enumerate(txt.split('\n'), 1) if '"[未证]" not in' in l]
    if hits:
        seen[f] = hits
res['p2_indep_impls'] = seen
ck('P2.1 至少 3 个独立脚本含同一逐字判据', len(seen) >= 3, seen)
ck('P2.2 merge_panel.py 是 PANEL.md 的写入器，它本身**不含**该判据（口径来源不在这里）',
   'merge_panel.py' not in seen, sorted(seen))
# 反控：把判据换成裸子串，命中集合必须不同（否则方括号不承重）
loose = {}
for f in targets:
    p = os.path.join(M59, f)
    if not os.path.exists(p):
        continue
    txt = open(p, encoding='utf-8').read()
    hits = [i for i, l in enumerate(txt.split('\n'), 1) if '未证' in l]
    loose[f] = hits
ck('P2-N1 反控：裸子串命中集合与带方括号**不同**（方括号是承重判据）',
   loose != seen, {k: len(v) for k, v in loose.items()})

print('\n=== P3 evidence_paths 单点 ===')
r35 = [l.split('\t') for l in open(F533, encoding='utf-8').read().split('\n') if l.startswith('F35\t')][0]
ev = r35[3]
res['p3_evidence'] = ev
ck('P3.1 evidence_paths 只有一项（无分号）', ';' not in ev, ev)
ck('P3.2 该项是 PANEL.md', 'PANEL.md' in ev, ev)

print('\n=== P4 两个输入都不在现盘 ===')
COV = os.path.join(R14, 'COVERAGE', 'coverage.tsv')
ATL = os.path.join(ROOT, 'lead', 'next_re_20261112_r10', 'W130_atlas', 'function_atlas.tsv')
res['p4_cov_exists'] = os.path.exists(COV)
res['p4_atlas_exists'] = os.path.exists(ATL)
ck('P4.1 coverage.tsv 不在盘', not os.path.exists(COV))
ck('P4.2 function_atlas.tsv 不在盘', not os.path.exists(ATL))
ck('P4-P1 正控 exists() 对在盘文件 True', os.path.exists(SP))

print('\n=== 形式判据：R138 那句与 P1 互斥 ===')
lim = r35[4]
res['r138_sentence'] = '定义**只有二手转述**' in lim
ck('S1 v5.33 的 F35 limitations 断言「定义只有二手转述」', '定义**只有二手转述**' in lim)
ck('S2 该断言与 P1（现盘有代码级一手实现）互斥 => 该断言为伪', bool(seen) and res['r138_sentence'])
ck('S3 v5.33 未提 strict_panel.py（漏了现盘唯一的代码级权威）', 'strict_panel' not in lim)
ck('S4 v5.33 提了 PANEL.md/M52 不在盘（这一半是真的）',
   'PANEL.md' in lim and ('不在现盘' in lim or '不在现盘' in lim))

print('\n=== 汇总：%d FAIL ===' % len(fails))
res['fails'] = fails
open(os.path.join(ROOT, '_r139', 'r139c_f35_four.json'), 'w', encoding='utf-8').write(
    json.dumps(res, ensure_ascii=False, indent=1))
raise SystemExit(1 if fails else 0)
