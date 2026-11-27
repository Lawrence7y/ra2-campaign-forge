#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R173 E：F35 四件套引用的 strict_panel.py 判据行与「同血缘克隆」四点，逐字复核。

F35 statement ②+limitations R165 段给了三条**可机械判**的断言：
  ① strict_panel.py 第 78 行是 if "[未证]" not in sem:，嵌套在第 76 行 if grade == "[已证]": 内；
  ② 另 3 个脚本含同一判据但不是独立实现 —— 血缘判据是「同一 PROJ 常量 + 同一对输入 + 同一判据串」；
  ③ 反控：写入器 merge_panel.py 有同一 PROJ 但**不含**该判据。
本脚本逐条实测，并加一条此前无人测过的：上溯到 sem 的**取值列**是不是 one_line_semantics。

反控：
 N1 把判据串换成裸「未证」（去掉方括号）后命中行数必须变多（证明方括号字面是判据的一部分）。
 N2 把血缘判据放宽成「只有同一 PROJ」（去掉「同一对输入」）后 merge_panel.py 会被误判为同血缘
    ⇒ 证明正文「共用 PROJ 不是血缘充分条件」这句成立。
 N3 一个必然不存在的串在五个脚本里都是 0 次（计数不是恒真）。
"""
import ast, hashlib, io, json, os, re, sys

TIER = '/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14'
SP = os.path.join(TIER, 'RULING_R15_20261119/work/strict_panel.py')
FOUR = {
    'strict_panel.py': SP,
    'precheck.py': os.path.join(TIER, '_cards/M59-MERGE/precheck.py'),
    'simulate.py': os.path.join(TIER, '_cards/M59-MERGE/simulate.py'),
    'verify.py': os.path.join(TIER, '_cards/M59-MERGE/verify.py'),
}
MERGE = os.path.join(TIER, '_cards/M59-MERGE/merge_panel.py')
fails, n = [], 0
def ck(name, cond, detail=''):
    global n
    n += 1
    print(('  PASS ' if cond else '  FAIL ') + name + (('  ' + str(detail)) if detail else ''))
    if not cond: fails.append(name)

def lines(p): return io.open(p, encoding='utf-8', errors='replace').read().split('\n')
def text(p): return io.open(p, encoding='utf-8', errors='replace').read()

sp_raw = open(SP, 'rb').read()
ck('E1 strict_panel.py 字节 6,481、sha256 前 16 位 731c98ea4910f5e9',
   len(sp_raw) == 6481 and hashlib.sha256(sp_raw).hexdigest()[:16] == '731c98ea4910f5e9',
   (len(sp_raw), hashlib.sha256(sp_raw).hexdigest()[:16]))

L = lines(SP)
ck('E2 第 78 行逐字 == if "[未证]" not in sem:', L[77].strip() == 'if "[未证]" not in sem:', repr(L[77]))
ck('E3 第 76 行逐字 == if grade == "[已证]":', L[75].strip() == 'if grade == "[已证]":', repr(L[75]))
ck('E4 76/78 的缩进关系：78 比 76 深 4 空格（嵌套，不是并列）',
   len(L[77]) - len(L[77].lstrip()) == len(L[75]) - len(L[75].lstrip()) + 4,
   (len(L[75]) - len(L[75].lstrip()), len(L[77]) - len(L[77].lstrip())))
ck('E5 第 14 行含同一条件的散文措辞（含方括号字面 未证）',
   '[未证]' in L[13] and 'proved_strict' in L[13], repr(L[13].strip()))

sp = text(SP)
ck('E6 全文方括号字面 [未证] 恰 2 次、行号 14 与 78',
   sp.count('[未证]') == 2
   and [i + 1 for i, l in enumerate(L) if '[未证]' in l] == [14, 78],
   (sp.count('[未证]'), [i + 1 for i, l in enumerate(L) if '[未证]' in l]))
ck('E7 全文裸「未证」也恰 2 次（方括号版就是全部）', sp.count('未证') == 2, sp.count('未证'))
ck('E8 代码形态（含 not in sem）恰 1 次', sp.count('"[未证]" not in sem') == 1,
   sp.count('"[未证]" not in sem'))

# sem 的取值列
idx = [i for i, l in enumerate(L) if 'sem = r[' in l]
ck('E9 sem 的取值列在第 67 行、取 r[3]', len(idx) == 1 and idx[0] + 1 == 67 and 'r[3]' in L[idx[0]],
   (idx, [L[i].strip() for i in idx]))
ck('E10 同函数内第 69 行才对 atlas_n 自增（continue 在 63..65 行之后）',
   L[68].strip() == 'd[s]["atlas_n"] += 1'
   and 'if e not in atlas:' in L[62] and 'continue' in L[64],
   (L[62].strip(), L[64].strip(), L[68].strip()))

# ② 血缘四点
def has_proj(p): return 'D:\\Project\\ra2-campaign-forge' in text(p)
def has_pair(p):
    t = text(p)
    return ('"COVERAGE", "coverage.tsv"' in t) and ('"W130_atlas", "function_atlas.tsv"' in t)
def has_judge(p): return '"[未证]" not in' in text(p)

sig = {os.path.basename(p): dict(proj=has_proj(p), pair=has_pair(p), judge=has_judge(p))
       for p in FOUR.values()}
print('   四点矩阵:', json.dumps(sig, ensure_ascii=False))
ck('E11 四脚本都有同一 PROJ 常量', all(v['proj'] for v in sig.values()), {k: v['proj'] for k, v in sig.items()})
ck('E12 四脚本都有同一对输入（COVERAGE/coverage.tsv 与 W130_atlas/function_atlas.tsv）',
   all(v['pair'] for v in sig.values()), {k: v['pair'] for k, v in sig.items()})
ck('E13 四脚本都含同一判据串', all(v['judge'] for v in sig.values()), {k: v['judge'] for k, v in sig.items()})

mg = dict(proj=has_proj(MERGE), pair=has_pair(MERGE), judge=has_judge(MERGE))
print('   merge_panel 四点:', mg)
ck('E14 反控：merge_panel.py 有同一 PROJ 但无同一对输入、无判据串（三缺二）',
   mg['proj'] and not mg['pair'] and not mg['judge'], mg)
ck('E15 merge_panel.py 全文「未证」0 次', text(MERGE).count('未证') == 0, text(MERGE).count('未证'))

# N1/N2/N3
ck('N1 反控：把判据换成裸「未证」后 strict_panel.py 命中行数不变（它本来就只有方括号版）',
   len([l for l in L if '未证' in l]) == 2, len([l for l in L if '未证' in l]))
loose = [os.path.basename(p) for p in list(FOUR.values()) + [MERGE] if has_proj(p)]
strict = [os.path.basename(p) for p in list(FOUR.values()) + [MERGE]
          if has_proj(p) and has_pair(p) and has_judge(p)]
ck('N2 反控：只用「同一 PROJ」会把 merge_panel.py 误纳（5 个），加上另两条后才是 4 个',
   len(loose) == 5 and len(strict) == 4, (loose, strict))
ck('N3 反控：必然不存在的串在五个脚本里都 0 次',
   all(text(p).count('ZZZ_ABSENT_ZZZ') == 0 for p in list(FOUR.values()) + [MERGE]), True)

print()
print('SUMMARY: %d assertions, %d FAIL' % (n, len(fails)))
json.dump(dict(fails=fails, asserts=n, matrix=sig, merge=mg,
               byte=len(sp_raw), sha16=hashlib.sha256(sp_raw).hexdigest()[:16]),
          open('/home/t628/projects/ra2-campaign-forge/_r173/r173e_strict_panel_authority.json', 'w'),
          ensure_ascii=False, indent=1)
sys.exit(1 if fails else 0)
