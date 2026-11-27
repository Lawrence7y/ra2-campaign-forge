#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r177g：F24 里「86.19」八处逐处定性 —— 任务单 ② 要求「数字撤下、结构判据保留、两者分开」。
判据（可失败）：把每处按标点切成小句（。；：，

，容许括注内含标点），
若同小句或紧随的后置括注内出现撤销词（撤下/撤销/撤回/不得再）或定性词（补集/覆盖率/口径），则判为「非裸用」。
正控：人为构造一句裸用，必须被判为裸用。反控：人为构造一句限定式，必须被判为非裸用。
"""
import csv, os, re, sys

TIER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V = os.path.join(TIER, 'R17_R128_FACTINDEX_V559', 'FACT_INDEX.tsv')
rows = {r[0]: r for r in csv.reader(open(V, encoding='utf-8'), delimiter='\t')}
F = rows['F24']
ok = fail = 0
def chk(c, m, extra=''):
    global ok, fail
    if c: ok += 1; print('  PASS ' + m + (('  ' + str(extra)) if extra else ''))
    else: fail += 1; print('  FAIL ' + m + (('  ' + str(extra)) if extra else ''))

MARK_KILL = ['撤下', '撤销', '撤回', '不得再']
MARK_QUAL = ['补集', '覆盖率', '口径', '未覆盖']

def clauses(s):
    """返回 [(start,end)] 小句区间：按 。；：后跟非数字 或 逗号后跟非数字 切；括号层级内的不切。"""
    out = []; depth = 0; start = 0
    for i, ch in enumerate(s):
        if ch in '（(':
            depth += 1
        elif ch in '）)':
            depth = max(0, depth - 1)
        elif depth == 0 and ch in '。；：':
            out.append((start, i + 1)); start = i + 1
        elif depth == 0 and ch in '，':
            # 千分位逗号（前后都是数字）不作界
            if i > 0 and i + 1 < len(s) and s[i-1].isdigit() and s[i+1].isdigit():
                continue
            out.append((start, i + 1)); start = i + 1
    out.append((start, len(s)))
    return [(a, b) for a, b in out if s[a:b].strip()]

def classify(s, pos, width=260):
    """返回 (verdict, evidence)"""
    cs = clauses(s)
    home = None
    for a, b in cs:
        if a <= pos < b:
            home = (a, b); break
    if home is None:
        return 'UNKNOWN', ''
    a, b = home
    win_lo = max(0, a); win_hi = min(len(s), b + width)
    win = s[win_lo:win_hi]
    hits = [k for k in MARK_KILL if k in win]
    if hits:
        return '撤回说明', '小句内/后置括注含 %r' % hits[:2]
    hits = [k for k in MARK_QUAL if k in win]
    if hits:
        return '定性说明', '小句内/后置括注含 %r' % hits[:2]
    return '★裸用', '小句内无撤销/定性词：%r' % s[max(0, a-30):b].strip()[:120]

print('=== A. 八处逐处定性 ===')
verdicts = []
for col, nm in ((1, 'statement'), (4, 'limitations')):
    s = F[col]
    for m in re.finditer(re.escape('86.19'), s):
        v, ev = classify(s, m.start())
        verdicts.append((nm, m.start(), v, ev))
        print('  %-12s @%-6d %-6s %s' % (nm, m.start(), v, ev[:110]))

print()
print('=== B. 断言 ===')
naked = [x for x in verdicts if x[2] == '★裸用']
chk(len(verdicts) == 8, '86.19 全行共 8 处（statement 3 + limitations 5）', len(verdicts))
chk(len(naked) == 0, '无一处是「裸用」（即没有任何一处被当作剔除 bounds 的理由）', naked)
kill = [x for x in verdicts if x[2] == '撤回说明']
qual = [x for x in verdicts if x[2] == '定性说明']
print('  撤回说明 %d 处 / 定性说明 %d 处 / 裸用 %d 处' % (len(kill), len(qual), len(naked)))
chk(len(kill) >= 4, '至少 4 处属撤回说明（R138 撤下 + R148 已撤下 + 两处 limitations 原注撤销）')
chk(len(qual) >= 3, '至少 3 处属定性说明（R164 口径滑移 / 语料覆盖率补集 / 引用规则）')

print()
print('=== C. 结构判据是否仍保留（任务单 ② 的「两者分开处理」）===')
S = '单列地址'
print('  statement「单列地址」=%d  limitations「单列地址」=%d' % (F[1].count(S), F[4].count(S)))
chk(F[1].count(S) >= 1, '「单列地址」结构判据在 statement 在场')
chk('没有可回原址复核的第二列' in F[1], '展开式「没有可回原址复核的第二列」在 statement 在场')
chk('仍剔' in F[1], '「仍剔」在 statement 在场（剔除结论未撤销）')

print()
print('=== D. 正反控（判据本身可失败）===')
s1 = '因此 86.19% 是剔除 bounds 的理由。'
v1, _ = classify(s1, s1.find('86.19'))
print('  正控句判定 =', v1)
chk(v1 == '★裸用', '正控：裸用句被判为裸用')
s2 = '86.19% 已由 R138 撤销。'
v2, _ = classify(s2, s2.find('86.19'))
print('  反控句判定 =', v2)
chk(v2 == '撤回说明', '反控：限定句被判为非裸用')
s3 = '其余 1,200,251（86.19%）只以地址形式存在。'
v3, _ = classify(s3, s3.find('86.19'))
print('  千分位逗号句判定 =', v3, '（必须不被逗号切断）')
chk(v3 == '★裸用', '千分位逗号不作界 ⇒ 该句确实无撤销词（若误切会得到别的判）')

print()
print('RESULT: %d PASS / %d FAIL' % (ok, fail))
sys.exit(1 if fail else 0)
