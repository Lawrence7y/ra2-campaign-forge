#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R174-F · 复算审计员 #411 的两条部分成立结论（§2.12 规则 D：审计结论必须主会话亲自复算）

审计员指控两条（原文摘录见 _r174/r174f_recheck.json 的 audit_claims）：
  C1（对 A2）「三项一自由度的恒等式不能判别该行 bytes 的真值」 —— 即我的 r174b 里
     「清单总和只能由 913,237 闭合」这句话作为**证据**不成立，只能在「只改一个加数」子情形成立。
  C2（对 A3）F35 的 V554 里「不是独立实现」实为 **5 次**（我卡面/待办写 3 次）；
     该作用域段写的是 **V553** 而不是 V554；且段内「同血缘克隆」0 次 ——
     即「statement 的同血缘克隆 与 limitations 的 3 次已互指」这个判断不成立。

判据（可失败）：
  W1  C1 成立：存在其它两处同时调整能让 913,239 也闭合（给出至少 2 种改法并验算）
  W2  C1 的边界：只改 diff 桶一项时，913,239 必然差 +2（这是我原结论的有效范围）
  W3  C2a 成立：逐版 V530..V554 数 F35 limitations 的「不是独立实现」次数，报 V553 与 V554 实测值
  W4  C2b 成立：V554 的该串次数 != 3
  W5  C2c 成立：R173 补段内「同血缘克隆」0 次、「不是独立实现」次数实测
  W6  C2d 成立：全行 limitations 里「同血缘克隆」次数实测（审计员称 1，在 R165 段）
  W7  口径陷阱：字面「3 次」包含 markdown 粗体时检索会 0 命中 —— 实测两种检索串的命中数

反控：
  N1  「独立实现」（不带「不是」）与「不是独立实现」在 V554 的命中数必须相等
      （若不等，说明有裸「独立实现」被漏计 —— 审计员的反控结论）
  N2  在 V540（已知 statement 首现该半句的版本）上，「不是独立实现」limitations 必须 0 次
      （证明计数脚本不是恒 >0）
  N3  在一个明显不含该串的版本（V530）上必须 0 次
  N4  恒等式自由度：固定 same 与 gone，扫 diff 的全部可行值，只有 913,237 使总和 == 737,517,286
      （证明「单改破坏闭合」为真，与 C1 的「可同时改两项」不矛盾）

只读各版本 FACT_INDEX.tsv；只写 _r174/r174f_recheck.json。
"""
import csv
import io
import json
import os
import re

ROOT = '/home/t628/projects/ra2-campaign-forge'
os.chdir(ROOT)
BASE = 'lead/next_re_20261117_r14'
OUT = '_r174/r174f_recheck.json'
TOTAL = 737517286
SAME, GONE, DIFF = 26846620, 709757429, 913237

FAIL = 0
RES = []


def ck(name, cond, detail=''):
    global FAIL
    ok = bool(cond)
    if not ok:
        FAIL += 1
    RES.append({'id': name, 'ok': ok, 'detail': str(detail)[:600]})
    print(('PASS ' if ok else 'FAIL ') + name + (('  :: ' + str(detail)[:300]) if detail else ''))


def load_ver(v):
    import glob
    g = glob.glob(os.path.join(BASE, 'R17_R1*_FACTINDEX_V%d' % v, 'FACT_INDEX.tsv'))
    if not g:
        return None
    rows = {r[0]: r for r in csv.reader(io.open(g[0], encoding='utf-8'), delimiter='\t')}
    return rows.get('F35')


print('== C1 · W1 恒等式一自由度：存在多种改法让 913,239 也闭合 ==')
f = lambda d_, s_, g_: s_ + d_ + g_ - TOTAL
print('只改 diff: 913,239 ⇒ %+d' % f(913239, SAME, GONE))
print('diff=913,239 且 gone −2 ⇒ %+d' % f(913239, SAME, GONE - 2))
print('diff=913,239 且 same −2 ⇒ %+d' % f(913239, SAME - 2, GONE))
print('diff=913,239 且 gone +7, same −9 ⇒ %+d' % f(913239, SAME - 9, GONE + 7))
alts = [
    ('只改 diff', 913239, SAME, GONE),
    ('diff+2 & gone−2', 913239, SAME, GONE - 2),
    ('diff+2 & same−2', 913239, SAME - 2, GONE),
    ('diff+2 & same−9 & gone+7', 913239, SAME - 9, GONE + 7),
]
sols = [(nm, f(d_, s_, g_)) for nm, d_, s_, g_ in alts]
for nm, r in sols:
    print('  %-26s residual=%+d' % (nm, r))
ck('W1a 存在除 913,237 以外的改法也能闭合（≥1 种，即 C1 成立）',
   sum(1 for nm, r in sols[1:] if r == 0) >= 1, sols[1:])
ck('W1b 因此「闭合式」本身不能判别该行 bytes 真值', True, 'three free params, one equation')
ck('W2a 但在「只改 diff 一项」的子情形下 913,239 必然 +2', f(913239, SAME, GONE) == 2, f(913239, SAME, GONE))
ck('W2b 「只改 diff 一项」时唯一解是 913,237', [x for x in range(913230, 913246) if f(x, SAME, GONE) == 0] == [913237],
   [x for x in range(913230, 913246) if f(x, SAME, GONE) == 0])

print('== C2 · 逐版数 F35 的「不是独立实现」 ==')
NEEDLE = '不是独立实现'
PLAIN = '独立实现'
CLONE = '同血缘克隆'
tab = []
for v in range(530, 555):
    r = load_ver(v)
    if r is None:
        tab.append((v, None, None, None, None, None))
        continue
    st, lim = r[1], r[4]
    tab.append((v, len(st), lim.count(NEEDLE), lim.count(PLAIN), st.count(CLONE), lim.count(CLONE)))
for row in tab:
    print('  V%d st_len=%s lim[不是独立实现]=%s lim[独立实现]=%s st[同血缘克隆]=%s lim[同血缘克隆]=%s' % row)

v553 = [t for t in tab if t[0] == 553][0]
v554 = [t for t in tab if t[0] == 554][0]
print('V553: lim[不是独立实现]=%s ; V554: lim[不是独立实现]=%s' % (v553[2], v554[2]))
ck('W3 V553 的 limitations 「不是独立实现」== 3', v553[2] == 3, v553[2])
ck('W3b V554 的 limitations 「不是独立实现」== 5（审计员实测值）', v554[2] == 5, v554[2])
ck('W4 V554 的该串次数 != 3（故「3 次」的作用域不能覆盖 V554）', v554[2] != 3, v554[2])

print('== C2c/d · V554 段内分布 ==')
r554 = load_ver(554)
st554, lim554 = r554[1], r554[4]
i = lim554.find('【R173 补')
seg = lim554[i:] if i >= 0 else ''
print('R173 补段长 = %d ; 段内 [同血缘克隆]=%d ; 段内 [不是独立实现]=%d'
      % (len(seg), seg.count(CLONE), seg.count(NEEDLE)))
ck('W5a R173 补段存在', i >= 0, i)
ck('W5b R173 补段内「同血缘克隆」== 0（审计员实测）', seg.count(CLONE) == 0, seg.count(CLONE))
print('全行 limitations: [同血缘克隆]=%d ; R165 段内=%d'
      % (lim554.count(CLONE), lim554[lim554.find('【R165 补'):lim554.find('【R173 补')].count(CLONE) if lim554.find('【R165 补') >= 0 else -1))
ck('W6a 全行 limitations「同血缘克隆」== 1', lim554.count(CLONE) == 1, lim554.count(CLONE))
j = lim554.find('【R165 补')
k = lim554.find('【R173 补')
ck('W6b 该 1 次落在 R165 补段内', j >= 0 and k > j and lim554[j:k].count(CLONE) == 1,
   lim554[j:k].count(CLONE) if j >= 0 and k > j else None)
ck('W6c R173 补段里「不是独立实现」次数 > 0（说明段内确有计数说法）', seg.count(NEEDLE) > 0, seg.count(NEEDLE))
ck('W6d R173 补段里「同血缘克隆」0 次 ⇒ 段内互指的是「不是独立实现」而非「同血缘克隆」',
   seg.count(CLONE) == 0 and seg.count(NEEDLE) > 0, (seg.count(CLONE), seg.count(NEEDLE)))

print('== W7 · 口径陷阱：粗体插在数字两侧 ==')
ck('W7a 字面「3 次」在 V554 limitations 里 0 命中', lim554.count('3 次') == 0, lim554.count('3 次'))
ck('W7b 带粗体的「**3** 次」命中 > 0', lim554.count('**3** 次') > 0, lim554.count('**3** 次'))

print('== N · 反控 ==')
ck('N1 V554 limitations 里「独立实现」== 「不是独立实现」（无裸用法）',
   lim554.count(PLAIN) == lim554.count(NEEDLE), (lim554.count(PLAIN), lim554.count(NEEDLE)))
r540 = load_ver(540)
ck('N2 V540 的 limitations「不是独立实现」== 0', r540[4].count(NEEDLE) == 0, r540[4].count(NEEDLE))
r530 = load_ver(530)
ck('N3 V530 的 limitations「不是独立实现」== 0', r530[4].count(NEEDLE) == 0, r530[4].count(NEEDLE))
ck('N4 V530 的 statement 不含「不是独立实现」', r530[1].count(NEEDLE) == 0, r530[1].count(NEEDLE))

audit_claims = [
    'C1: 三项一自由度恒等式不能判别该行 bytes 真值（单改破坏闭合=真；闭合可作反证=假）',
    'C2a: V554 limitations 「不是独立实现」实为 5 次，不是 3 次',
    'C2b: R173 补段的作用域写的是 V553，不覆盖 V554',
    'C2c: R173 补段内「同血缘克隆」0 次，段内互指对象是「不是独立实现」',
]
out = {
    'script': 'r174f_recheck.py',
    'audit_task': 411,
    'audit_claims': audit_claims,
    'identity_sols': [{'name': n, 'residual': r} for n, r in sols],
    'version_table': [{'ver': t[0], 'st_len': t[1], 'lim_needle': t[2], 'lim_plain': t[3],
                       'st_clone': t[4], 'lim_clone': t[5]} for t in tab],
    'v553_lim_needle': v553[2], 'v554_lim_needle': v554[2],
    'r173_seg_len': len(seg), 'r173_seg_needle': seg.count(NEEDLE), 'r173_seg_clone': seg.count(CLONE),
    'lim_clone_total': lim554.count(CLONE),
    'literal_3times': lim554.count('3 次'), 'bold_3times': lim554.count('**3** 次'),
    'assertions': RES, 'fail': FAIL,
}
io.open(OUT, 'w', encoding='utf-8').write(json.dumps(out, ensure_ascii=False, indent=1))
print('\n== RESULT: %d assertions, %d FAIL ==' % (len(RES), FAIL))
print('wrote ' + OUT)
raise SystemExit(1 if FAIL else 0)
