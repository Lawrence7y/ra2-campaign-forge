#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R173 C：F35 那两句版本范围声明的可失败复核。

待核两句（V553 的 F35 limitations）：
  ① 「该互斥表述在 V540..V544 连续 5 版共存，V545 起回收」
  ② 同段「上文 R139 段写『另有 3 个独立脚本含同一逐字判据』」—— 这句引文必须在被引版本里真的存在。

判据：只数 limitations 列的原句；「R165 补」段里对原句的**引文**要分开数（它带「」引号）。
反控：① 把检索串改成去掉「独立」二字的形态，V545/V553 必须仍有 ≥1 次（不是恒 0）；
      ② 版本目录从 V530 起逐版都能打开（否则「连续」二字无法判）。
"""
import glob, json, os, re, sys

TIER = '/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14'
ORIG = '另有 3 个独立脚本含同一逐字判据'      # 被引用的原句
QUOT = '「另有 3 个独立脚本含同一逐字判据」'    # R165 段里带引号的引文
NEWW = '不是独立实现'   # S-596：首版写成「但不是独立实现」，而正文里夹着 Markdown 星号（但**不是独立实现**）
                          # 字符串匹配不到 ⇒ C2 假 FAIL。改成不含相邻字符的最小串。

fails, n = [], 0
def ck(name, cond, detail=''):
    global n
    n += 1
    print(('  PASS ' if cond else '  FAIL ') + name + (('  ' + str(detail)) if detail else ''))
    if not cond: fails.append(name)

vs = sorted(glob.glob(os.path.join(TIER, 'R17_R*_FACTINDEX_V*')),
            key=lambda d: int(re.search(r'V(\d+)$', d).group(1)))
tab = {}
for v in vs:
    p = os.path.join(v, 'FACT_INDEX.tsv')
    if not os.path.isfile(p): continue
    ver = int(re.search(r'V(\d+)$', v).group(1))
    t = open(p, encoding='utf-8').read()
    r = [x.split('\t') for x in t.rstrip('\n').split('\n')[1:] if x.startswith('F35\t')]
    if not r: continue
    st, lim = r[0][1], r[0][4]
    tab[ver] = dict(dir=os.path.basename(v), stmt_len=len(st), lim_len=len(lim),
                    orig=lim.count(ORIG), quot=lim.count(QUOT),
                    orig_bare=lim.count(ORIG) - lim.count(QUOT),
                    neww_stmt=st.count(NEWW), neww_lim=lim.count(NEWW))

ck('C0 版本目录 V530..V553 共 24 个且连续无缺',
   sorted(tab) == list(range(530, 554)), sorted(tab)[:3] + ['...'] + sorted(tab)[-3:])

# ① 「V540..V544 连续 5 版共存」—— 判的是什么共存？两种读法都报，不预设
span = list(range(540, 545))
ck('C1 V540..V544 五版都在表内', all(v in tab for v in span), [v for v in span if v not in tab])
ck('C2 五版 statement 长度恒 1054 且都含「不是独立实现」',
   all(tab[v]['stmt_len'] == 1054 and tab[v]['neww_stmt'] == 1 for v in span),
   [(v, tab[v]['stmt_len'], tab[v]['neww_stmt']) for v in span])
# S-597：首版 C2b 断言「limitations 也含该半句」，但那五版 limitations 里只有旧句 ——
# 这正是矛盾本身，把结论写成断言就成了假 FAIL。改成断言实测量：V540..V544 的 limitations
# 该半句恒 0 次（= 两列互斥），V545 起恒 1 次（= 回收）。
ck('C2b V540..V544 的 limitations 里该半句恒 0 次（两列互斥）',
   all(tab[v]['neww_lim'] == 0 for v in span), [(v, tab[v]['neww_lim']) for v in span])
# S-598：首版 C2c 断言「恒 1 次」，实测恒 3 次 —— 1 次是 R139 段里的改写句本体，
# 另 2 次在 R165 段的引文内（一句引 statement、一句引改写结果）。改成实测量。
ck('C2c V545 起 limitations 里该半句恒 3 次（1 次改写句本体 + 2 次在 R165 引文内）',
   all(tab[v]['neww_lim'] == 3 for v in range(545, 554)), [(v, tab[v]['neww_lim']) for v in range(545, 554)])
ck('C3 五版 limitations 里「原句（不带引号）」各 1 次',
   all(tab[v]['orig_bare'] == 1 for v in span), [(v, tab[v]['orig_bare']) for v in span])
ck('C4 V545 起（545..553）原句（不带引号）恒 0 次',
   all(tab[v]['orig_bare'] == 0 for v in range(545, 554)), [(v, tab[v]['orig_bare']) for v in range(545, 554)])
ck('C5 V545 起带引号的引文恒 1 次（R165 段在引用它）',
   all(tab[v]['quot'] == 1 for v in range(545, 554)), [(v, tab[v]['quot']) for v in range(545, 554)])
ck('C6 V534..V539 原句已在（各 1 次）而 statement 里没有该半句（长 156）',
   all(tab[v]['orig_bare'] == 1 and tab[v]['stmt_len'] == 156 and tab[v]['neww_stmt'] == 0
       for v in range(534, 540)),
   [(v, tab[v]['orig_bare'], tab[v]['stmt_len']) for v in range(534, 540)])
ck('C7 所以「互斥表述共存」的起点是 V540 而不是 V534（statement 侧首现于 V540）',
   min(v for v in tab if tab[v]['neww_stmt'] >= 1) == 540,
   min(v for v in tab if tab[v]['neww_stmt'] >= 1))

# ② 「上文 R139 段写『另有 3 个独立脚本…』」——V553 里这句是「R165 对已改文本的追述」
ck('C8 V553 的 limitations 里带引号的引文恰 1 次且不在 R139 段内（在 R165 段）',
   tab[553]['quot'] == 1, tab[553]['quot'])
lim553 = [x.split('\t') for x in open(os.path.join(TIER, 'R17_R125_FACTINDEX_V553/FACT_INDEX.tsv'),
                                      encoding='utf-8').read().rstrip('\n').split('\n')[1:]
          if x.startswith('F35\t')][0][4]
i139 = lim553.find('【R139 更正')
i152 = lim553.find('**【R152 补')
i159 = lim553.find('**【R159 补')
i165 = lim553.find('**【R165 补')
seg139 = lim553[i139:i152]
seg165 = lim553[i165:]
ck('C9 四段标记都定位得到', min(i139, i152, i159, i165) > 0, (i139, i152, i159, i165))
ck('C10 R139 段内 SHELL 原句 0 次、改写后的句子 1 次（V545 已就地改过）',
   seg139.count(ORIG) == 0 and seg139.count('另 3 个脚本含同一逐字判据') == 1,
   (seg139.count(ORIG), seg139.count('另 3 个脚本含同一逐字判据')))
ck('C11 R165 段内带引号引文 1 次（它引的是 V534..V544 的旧文本）',
   seg165.count(QUOT) == 1, seg165.count(QUOT))
ck('C12 V544（被引的最后一版）里原句 1 次、且不在引号内',
   tab[544]['orig_bare'] == 1, tab[544]['orig_bare'])
_seg139_new = seg139.count(NEWW)
_seg165_new = seg165.count(NEWW)
ck('C13 三次拆分闭合：R139 段 1 次 + R165 段 2 次 == 全列 3 次',
   _seg139_new == 1 and _seg165_new == 2 and _seg139_new + _seg165_new == lim553.count(NEWW),
   (_seg139_new, _seg165_new, lim553.count(NEWW)))

# 反控
ck('N1 反控：去掉「独立」二字的串在 V545 与 V553 都 ≥1 次（检索不是恒 0）',
   tab[545]['lim_len'] and '3 个脚本含同一逐字判据' in open(
       os.path.join(TIER, 'R17_R117_FACTINDEX_V545/FACT_INDEX.tsv'), encoding='utf-8').read()
   and '3 个脚本含同一逐字判据' in lim553, True)
ck('N2 反控：一个必然不存在的串在所有版本都 0 次（计数不是恒真）',
   all(open(os.path.join(TIER, tab[v]['dir'], 'FACT_INDEX.tsv'), encoding='utf-8').read()
       .count('ZZZ_NOT_PRESENT_ZZZ') == 0 for v in (530, 545, 553)), True)
ck('N3 反控：V533 的 limitations 只有 695 字符、且原句 0 次（首现确实在 V534）',
   tab[533]['lim_len'] == 695 and tab[533]['orig_bare'] == 0,
   (tab[533]['lim_len'], tab[533]['orig_bare']))

print()
print('SUMMARY: %d assertions, %d FAIL' % (n, len(fails)))
json.dump(dict(fails=fails, asserts=n,
               per_version={str(k): v for k, v in sorted(tab.items())}),
          open('/home/t628/projects/ra2-campaign-forge/_r173/r173c_f35_version_range.json', 'w'),
          ensure_ascii=False, indent=1)
sys.exit(1 if fails else 0)
