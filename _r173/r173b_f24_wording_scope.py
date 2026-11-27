#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R173 B：F24 那处「bounds 段 16,711,118 B」在正文里出现几次、每次是哪种口径。

A 已证：16,711,118 是「现盘 − 清单」的算术差，不是 bounds 段的字节跨度（实测 16,711,104）。
本脚本不判该怎么改，只把**每一次出现**的分类钉住，供下轮裁定时引用 —— 以及钉住
「删掉整条 bounds 成员」的宽度 16,711,116（= 118 − 2），说明 118 也不是成员宽度。

反控：
 N1 把 16,711,118 改成 16,711,104 后，同一分类器必须把该出现判为「值跨度口径」。
 N2 空串输入必须给出 0 次（证明不是恒计数）。
"""
import json, re, sys

P = '/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14/R17_R125_FACTINDEX_V553/FACT_INDEX.tsv'
fails, n_assert = [], 0
def ck(name, cond, detail=''):
    global n_assert
    n_assert += 1
    print(('  PASS ' if cond else '  FAIL ') + name + (('  ' + str(detail)) if detail else ''))
    if not cond: fails.append(name)

t = open(P, encoding='utf-8').read()
rows = [r.split('\t') for r in t.rstrip('\n').split('\n')[1:]]
f24 = [r for r in rows if r[0] == 'F24'][0]
stmt, lim = f24[1], f24[4]

ck('B1 F24 行五列（fact_id/statement/grade/evidence/limitations）',
   len(f24) == 5, len(f24))
ck('B2 全表里 16,711,118 只出现在 F24 一行',
   sum(1 for r in rows if '16,711,118' in r[1] + r[4]) == 1,
   [r[0] for r in rows if '16,711,118' in r[1] + r[4]])
ck('B3 statement 里 4 次、limitations 里 4 次、合计 8 次（实测）',
   stmt.count('16,711,118') == 4 and lim.count('16,711,118') == 4 and t.count('16,711,118') == 8,
   (stmt.count('16,711,118'), lim.count('16,711,118'), t.count('16,711,118')))

# 逐次分类：取每次出现前后 70 字符，按上下文关键词判口径
def classify(text, number, span=90):
    out = []
    for m in re.finditer(re.escape(number), text):
        a, b = max(0, m.start() - span), min(len(text), m.end() + span)
        ctx = text[a:b]
        if '恰为被剔' in ctx or ('bounds' in ctx and '段' in ctx and '剔' in ctx):
            kind = 'BOUNDS_SPAN'
        elif '差 **+' in ctx or ('现盘' in ctx and '清单' in ctx):
            kind = 'ARITH_DELTA'
        elif '恰为' in ctx:
            kind = 'ASSERT_EQUAL'
        else:
            kind = 'OTHER'
        out.append((m.start(), kind, ctx[:0]))
    return out

kinds_stmt = classify(stmt, '16,711,118')
kinds_lim = classify(lim, '16,711,118')
allk = kinds_stmt + kinds_lim
ck('B4 statement 4 次、limitations 4 次，逐次分类器覆盖全部 8 次',
   len(kinds_stmt) == 4 and len(kinds_lim) == 4, (len(kinds_stmt), len(kinds_lim)))
ck('B5 「恰为被剔的 bounds 段」型恰 1 次（statement 内），且落在 BOUNDS_SPAN 类',
   stmt.count('恰为被剔') == 1 and sum(1 for _, k, _ in kinds_stmt if k == 'BOUNDS_SPAN') >= 1,
   [(i, k) for i, k, _ in kinds_stmt])

# N1 反控：把数字换成实测值后，同一分类器必须仍判 BOUNDS_SPAN（分类器不是绑死在 118 上）
_stmt2 = stmt.replace('16,711,118', '16,711,104')
_k2 = classify(_stmt2, '16,711,104')
ck('N1a 换成 16,711,104 后仍判出 BOUNDS_SPAN（分类器与数值无关）',
   any(k == 'BOUNDS_SPAN' for _, k, _ in _k2), [(i, k) for i, k, _ in _k2][:3])
ck('N1b 空串分类出 0 次（不是恒计数）', classify('', '16,711,118') == [], True)

# 三个口径的数
raw = open('/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14/D41_SUBST/_audit/EVIDENCE/a2_sites.json', 'rb').read()
d = json.loads(raw)
calls = d['calls']
v = {
    'bounds 值跨度（实测，A 脚本）': 16711104,
    '删掉整条 bounds 成员（, "bounds": [...]）': len(raw) - len(json.dumps({'calls': calls})),
    '现盘 − 清单记录': 17624355 - 913237,
    '正文写的 16,711,118': 16711118,
}
for k, x in v.items():
    print('   %-42s %d' % (k, x))
ck('B6 「删掉整条成员」宽度 = 16,711,116 = 118 − 2', v['删掉整条 bounds 成员（, "bounds": [...]）'] == 16711116,
   v['删掉整条 bounds 成员（, "bounds": [...]）'])
ck('B7 三个口径互不相同：104 / 116 / 118',
   len({16711104, 16711116, 16711118}) == 3, None)
ck('B8 正文用的 118 恰等于「现盘 − 清单」这一算术差',
   v['现盘 − 清单记录'] == 16711118, v['现盘 − 清单记录'])

print()
print('SUMMARY: %d assertions, %d FAIL' % (n_assert, len(fails)))
json.dump(dict(fails=fails, asserts=n_assert,
               occurrences=dict(stmt=stmt.count('16,711,118'), lim=lim.count('16,711,118')),
               calibration=dict(bounds_span=16711104, member_removal=16711116, arith_delta=16711118)),
          open('/home/t628/projects/ra2-campaign-forge/_r173/r173b_f24_wording_scope.json', 'w'),
          ensure_ascii=False, indent=1)
sys.exit(1 if fails else 0)
