# -*- coding: utf-8 -*-
"""R154 · 把本轮目标清单 ①–④/⑥ 与 V542 现盘正文做机械比对。
目的：分清「还没写」和「已写了但目标是旧口径」——这两件事的处置完全不同
（前者=补写，后者=裁定/改目标文本）。所有判据只用「子串是否出现 + 出现位置是否落在
撤回语境窗口内」，不做语义判断。
"""
import csv, io, re, json, sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
FI = ROOT + '/lead/next_re_20261117_r14/R17_R114_FACTINDEX_V542/FACT_INDEX.tsv'
rows = list(csv.reader(io.open(FI, encoding='utf-8'), delimiter='\t'))
d = {r[0]: r for r in rows[1:]}
STMT, LIM = 1, 4

FAILS, NOTES = [], []
def chk(c, m): (NOTES if c else FAILS).append(('PASS ' if c else 'FAIL ') + m)

def ctx(txt, tok, win=160):
    out = []
    for m in re.finditer(re.escape(tok), txt):
        out.append(txt[max(0, m.start() - win):m.end() + win])
    return out

RETRACT = ('撤下', '撤销', '已撤回', '撤回', '作废', '不得再写')

# ---------- 目标 ①-a : F23 补「12 行分解余 1 行无归属」 ----------
f23s, f23l = d['F23'][STMT], d['F23'][LIM]
chk('12 行分解' in f23s, 'F23 statement contains 12 行分解 (goal ①-a)')
chk('1 行无归属' in f23s or '1 行**无归属**' in f23s or '没有归属' in f23s,
    'F23 statement states the leftover row has no attribution')
chk('6 + 2 + 3' in f23s and '11' in f23s, 'F23 statement carries the 6+2+3=11 arithmetic')
chk('14' in f23s and '不闭合' in f23s, 'F23 statement carries the alternative 6+2+3+3=14 reading')
chk('12 行分解' in f23l or '分解不闭合' in f23l, 'F23 limitations also carries the non-closure (R138 补)')

# ---------- 目标 ①-b : F23 补「计数依赖 coverage.tsv 4,147,334 B 已失」 ----------
chk('4,147,334' in f23s and '已失' in f23s, 'F23 statement carries 4,147,334 B + 已失')
chk('4,147,334' in f23l, 'F23 limitations carries 4,147,334 B')
chk('不能重数' in f23s or '不可重数' in f23l, 'F23 states the counts cannot be recounted')

# ---------- 目标 ①-c : F35 补「proved_strict 定义缺一手权威」 ----------
f35s, f35l = d['F35'][STMT], d['F35'][LIM]
chk('缺一手权威' in f35l, 'F35 limitations literally contains 缺一手权威 (goal ①-c as written)')
# 但同一 limitations 里还有 R139 更正，声明该句为伪
chk('R139 更正' in f35l and '撤回' in f35l, 'F35 limitations ALSO carries the R139 retraction of that very sentence')
chk('已撤回，不得再写' in f35s, 'F35 statement explicitly forbids writing 缺一手权威 again')
# S-391: 首版要求「每一处 缺一手权威 都在撤回窗口内」，实测该字面只在 R138 段标题里出现 1 次，
# 撤回在**另一段**（R139 更正）里，相隔约 900 字符 —— 这不是「没撤回」，是「撤回不在同一句」。
# 正确判据是结构性的三条：① R138 段原文在 ② R139 撤回段也在且点名该句为伪 ③ R139 段位置在 R138 之后。
i138 = f35l.find('【R138 补·定义缺一手权威】')
i139 = f35l.find('【R139 更正')
chk(i138 >= 0 and i139 > i138,
    'F35 limitations: R138 claim at %d, R139 retraction at %d (retraction must come after)'
    % (i138, i139))
chk(i139 > 0 and '为伪' in f35l[i139:i139 + 400],
    'R139 section explicitly calls the R138 sentence 为伪: %r' % f35l[i139:i139 + 120])
seg139 = f35l[i139:] if i139 > 0 else ''
chk(any(k in seg139 for k in RETRACT), 'R139 section itself uses a retraction verb')
chk('已撤回，不得再写' in f35s,
    'F35 statement carries the forward prohibition 已撤回，不得再写')

# ---------- 目标 ② : F24 86.19% 撤下 ----------
f24s, f24l = d['F24'][STMT], d['F24'][LIM]
occ = len(re.findall(r'86\.19', f24s)) + len(re.findall(r'86\.19', f24l))
ret = [c for t in (f24s, f24l) for c in ctx(t, '86.19') if any(k in c for k in RETRACT)]
chk(occ > 0 and len(ret) == occ,
    'all %d occurrences of 86.19 in F24 sit inside a retraction window (%d retracted)' % (occ, len(ret)))
chk('99.992' in f24s and '99.992' in f24l, '99.992 replacement present in both columns')
chk('单列地址' in f24s and '第二列' in f24s, 'structural criterion 单列地址/第二列 retained separately')

# ---------- 目标 ③ : F24 语料值失效期标注 ----------
chk('2026-11-22 快照值' in f24s, 'F24 statement labels the corpus value as 2026-11-22 快照值')
chk('2026-11-22 快照值' in f24l, 'F24 limitations labels it too')
chk('4,417' in f24s and '737,517,286' in f24s, 'corpus totals present')
chk('65 件' in f24s and '44,470,975' in f24s, 'current-disk counterpart 65 件 / 44,470,975 B present in statement')

# ---------- 目标 ④ : F29 四处作用域 ----------
f29s, f29l = d['F29'][STMT], d['F29'][LIM]
chk('80 次' in f29s and '两份拷贝' in f29s, 'F29 (1) 两份拷贝 scoped to 80 occurrences (statement)')
chk('DLL 内' in f29s and 'idx=**62' in f29s.replace('idx=62', 'idx=**62'), 'F29 (2) idx=62 scoped to DLL-internal')
chk('非因果' in f29s, 'F29 (4) 40 vs 63/77 non-causality present')
chk('40 次' in f29s and '不是「40 个桩函数」' in f29s, 'F29 (3) 40 is byte-occurrence count, not stub-function count')
# (3) 目标写的是「6 桩体=63 表内口径」；现盘 statement 写「不采用、不需补作用域」，
#     limitations 的 R141 段另有「63 只用到 6 个桩」——两者是不同处置，必须分开登记。
chk('6 个不同桩体' in f29s, 'F29 statement mentions R135 的 6 个不同桩体 and rejects it')
chk('63 只用到 6 个桩' in f29l, 'F29 limitations R141 section states 63 uses only 6 stubs (the 表内口径)')
six_stmt_reject = '不采用' in f29s and '不需补作用域' in f29s
chk(six_stmt_reject, 'F29 statement disposition for 6 桩体 is 不采用/不需补作用域 (NOT the goal wording 63 表内口径)')

# ---------- 目标 ⑥ : C7 死分支（引用 r154c/d 的实测，不重复测） ----------
j = json.load(io.open(ROOT + '/_r154/r154c_c7_natural.json', encoding='utf-8'))
chk(j['fail'] == 0, 'r154c had 0 FAIL (%d)' % j['fail'])
k = json.load(io.open(ROOT + '/_r154/r154d_c7_candidates.json', encoding='utf-8'))
chk(k['A'] == [], 'C7: A-tier (>=2 observations AND constant bytes) is EMPTY -> no natural bytes= row')
chk(len(k['B']) == 27, 'C7: B-tier (single observation only) = %d' % len(k['B']))
chk(len(k['C']) == 4, 'C7: C-tier (observed drift) = %d -> %r'
    % (len(k['C']), [x['file'] for x in k['C']]))
chk(j['census'].get('exists', 0) == 0 and j['census'].get('bytes=', 0) == 0,
    'C7 census: exists=0, bytes==0 measured independently of check_disc')

# ---------- 反控 ----------
chk('ZZZ_NOT_IN_V542_QQQ' not in f29s and 'ZZZ_NOT_IN_V542_QQQ' not in f35l,
    'NEGCTRL self-made token absent from both rows (substring test has power)')
chk('4,147,334' in d['F23'][STMT] and '4,147,334' not in d['F29'][STMT],
    'POSCTRL/NEGCTRL pair: token found in F23, absent in F29 (per-row isolation works)')

out = {'pass': len(NOTES), 'fail': len(FAILS), 'fails': FAILS, 'notes': NOTES,
       'six_claim_goal_vs_disk': {
           'goal_wording': '6 桩体=63 表内口径',
           'disk_statement': '6 个不同桩体 不在本条任何一列、不采用、不需补作用域',
           'disk_limitations_R141': '63 只用到 6 个桩',
           'verdict': 'two distinct "6" are conflated by the goal text; disk disposes them separately'}}
io.open(ROOT + '/_r154/r154e_goal_vs_disk.json', 'w', encoding='utf-8').write(
    json.dumps(out, ensure_ascii=False, indent=1))
for m in NOTES + FAILS: print(m)
print('RESULT pass=%d fail=%d' % (len(NOTES), len(FAILS)))
sys.exit(1 if FAILS else 0)
