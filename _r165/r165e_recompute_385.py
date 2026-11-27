#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R165-e · 复算跨家族审计员 #385 的三条判定（规则 D：逐条亲自复算，不采信结论）

审计员三条原文要点（摘）：
  D1 成立    ：F35 同一行 col2 有「不是独立实现/同血缘/克隆」，col5 有「独立脚本」；
               col5 里用来抵消的字样 0/5 种；V540..V544 五版逐版复现。
  D2 成立    ：F29 的「6 个不同桩体」本行 2 次（col2 1 + col5 1）；
               「不在本条正文任何一列」只在 col5；col2 另有同义变体「不在本条任何一列」。
  D3 部分成立：逐版 15 版的计数与 R159 自述 13/13 一致（不是虚构）；
               缺失在作用域上限停在 V542 而 V543/V544 已是 3 次；
               **但「把『该串每版 1 次』当作已核事实」这一措辞在原文里不逐字存在（count=0）**，
               原文只断言出现与否，未断言每版计数 ⇒ 该措辞需要收窄。

D3 这条打的是**我自己刚写进 V545 的转述**（r165b 的 ADD23 写了「把出现次数钉在 1 次/版」）。
若复算成立，就必须改口 —— 本轮不能把审计员的收窄当成「已消化」。
"""
import io
import json
import os
import re
import sys

R = '/home/t628/projects/ra2-campaign-forge'
T = os.path.join(R, 'lead/next_re_20261117_r14')
V544 = os.path.join(T, 'R17_R116_FACTINDEX_V544/FACT_INDEX.tsv')
V545 = os.path.join(T, 'R17_R117_FACTINDEX_V545/FACT_INDEX.tsv')
OUT = os.path.join(R, '_r165/r165e_recompute_385.json')

FAILS = []
RES = []


def ck(n, c, d=''):
    ok = bool(c)
    print(('  PASS ' if ok else '  FAIL ') + n + (('  :: ' + str(d)[:300]) if d else ''))
    RES.append({'n': n, 'ok': ok, 'd': str(d)[:300]})
    if not ok:
        FAILS.append(n)
    return ok


def rows(p):
    return {l.split('\t')[0]: l.split('\t') for l in io.open(p, encoding='utf-8').read().split('\n') if l}


# 只取 V530..V545 这一段（更早的 V5xx 目录不在 FACT_INDEX_CURRENT.md 声明的 V530..V545 连续段内，
# 混进来会让「逐版 15 版」这个分母变错 —— 这是 S-514，同 R162 S-473 的「分母未限定」同族）。
V = sorted([d for d in os.listdir(T)
            if re.search(r'_FACTINDEX_V5\d\d$', d) and 530 <= int(d.rsplit('_V', 1)[1]) <= 545],
           key=lambda d: int(d.rsplit('_V', 1)[1]))
ck('D0.1 版本段恰 16 个目录（V530..V545）', len(V) == 16, [d.rsplit('_V', 1)[1] for d in V])
ck('D0.2 反控：不设界会多纳入更早目录（证明限定是必需的）',
   len([d for d in os.listdir(T) if re.search(r'_FACTINDEX_V5\d\d$', d)]) > 16,
   len([d for d in os.listdir(T) if re.search(r'_FACTINDEX_V5\d\d$', d)]))

print('== D1 · F35 同列互斥措辞（复算审计员第 1 条）==')
r = rows(V544)
f = r['F35']
ck('D1.1 col2 含「不是独立实现」= 1', f[1].count('不是独立实现') == 1, f[1].count('不是独立实现'))
ck('D1.2 col2 含「同血缘」= 1', f[1].count('同血缘') == 1, f[1].count('同血缘'))
ck('D1.3 col2 含「克隆」= 1', f[1].count('克隆') == 1, f[1].count('克隆'))
ck('D1.4 col5 含「独立脚本」= 1', f[4].count('独立脚本') == 1, f[4].count('独立脚本'))
COMP = ['同血缘', '不是独立实现', '克隆', '非独立', '独立实现']
comp = {w: f[4].count(w) for w in COMP}
ck('D1.5 col5 里五种抵消字样合计 0（审计员说 0/5 ⇒ 复算一致）', sum(comp.values()) == 0, comp)
# 逐版复现
rep = {}
for d in V:
    ver = int(d.rsplit('_V', 1)[1])
    g = rows(os.path.join(T, d, 'FACT_INDEX.tsv'))['F35']
    rep[ver] = {'st_no': g[1].count('不是独立实现'), 'st_b': g[1].count('同血缘'),
                'lim_ind': g[4].count('独立脚本'),
                'lim_comp': sum(g[4].count(w) for w in COMP)}
    print('   V%d  不是独立实现=%d 同血缘=%d 独立脚本(限)=%d 抵消字样(限)=%d'
          % (ver, rep[ver]['st_no'], rep[ver]['st_b'], rep[ver]['lim_ind'], rep[ver]['lim_comp']))
ck('D1.6 V540..V544 五版逐版复现且抵消字样恒 0',
   all(rep[v]['st_no'] == 1 and rep[v]['st_b'] == 1 and rep[v]['lim_ind'] == 1 and rep[v]['lim_comp'] == 0
       for v in range(540, 545)),
   {v: rep[v] for v in range(540, 545)})
# S-515：三串不是同时首现 —— 「独立脚本」(lim) 首现于 V534（R139 段），
# 「不是独立实现/同血缘」(st) 首现于 V540（R159 段前后）。上一版把三者当同一批 ⇒ 假 FAIL。
ck('D1.7 反控：「独立脚本」(lim) 在 V533 为 0、V534 起为 1（首现于 V534）',
   rep[533]['lim_ind'] == 0 and all(rep[v]['lim_ind'] == 1 for v in range(534, 546)),
   {v: rep[v]['lim_ind'] for v in range(533, 546)})
ck('D1.7b 反控：「不是独立实现/同血缘」(st) 在 V539 为 0、V540 起为 1（首现于 V540，晚 6 版）',
   all(rep[v]['st_no'] == 0 and rep[v]['st_b'] == 0 for v in range(530, 540))
   and all(rep[v]['st_no'] == 1 and rep[v]['st_b'] == 1 for v in range(540, 546)),
   {v: (rep[v]['st_no'], rep[v]['st_b']) for v in (533, 539, 540, 545)})
ck('D1.7c 【互斥窗口】两处并存只在 V540..V544 这 5 版（V545 已回收）',
   all(rep[v]['lim_comp'] == 0 for v in range(530, 545)) and rep[545]['lim_comp'] > 0,
   {v: rep[v]['lim_comp'] for v in (544, 545)})

print()
print('== D2 · F29 自指句（复算审计员第 2 条）==')
g = r['F29']
per = {i + 1: g[i].count('6 个不同桩体') for i in range(5)}
print('   逐列「6 个不同桩体」:', per)
ck('D2.1 col2 = 1 且 col5 = 1，其余三列 0（合计 2）',
   per[2] == 1 and per[5] == 1 and sum(per.values()) == 2, per)
ck('D2.2 「不在本条正文任何一列」只在 col5（col5=1，col2=0）',
   g[4].count('不在本条正文任何一列') == 1 and g[1].count('不在本条正文任何一列') == 0,
   (g[1].count('不在本条正文任何一列'), g[4].count('不在本条正文任何一列')))
ck('D2.3 col2 另有同义变体「不在本条任何一列」= 1 次（审计员指出的更直接反例）',
   g[1].count('不在本条任何一列') == 1 and g[4].count('不在本条任何一列') == 0,
   (g[1].count('不在本条任何一列'), g[4].count('不在本条任何一列')))
ck('D2.4 【自指为假成立】该串本行 2 次全在本行内 ⇒「不在任何一列」不成立',
   sum(per.values()) == 2, sum(per.values()))
ck('D2.5 反控：全表 54 条只有 F29 命中该族自指（不是普遍现象）',
   sum(1 for k, c in r.items() if k.startswith('F')
       and ('不在本条任何一列' in c[1] or '不在本条正文任何一列' in c[4])) == 1,
   [k for k, c in r.items() if k.startswith('F')
    and ('不在本条任何一列' in c[1] or '不在本条正文任何一列' in c[4])])

print()
print('== D3 · R159 作用域（复算审计员第 3 条：部分成立 → 我的转述过强）==')
i159 = g and None
v544f = r['F23']
lim = v544f[4]
i = lim.index('【R159 补·12 行分解的缺口与作用域】')
seg = lim[i:]
print('   R159 段全文长度 =', len(seg))
# 审计员的关键指控：原文里到底有没有「每版 1 次」这类「逐版计数」断言
PAT = ['每版', '1 次/版', '逐版各 1', '各 1 次', '每版 1 次', '每版各']
hit = {p: seg.count(p) for p in PAT}
print('   R159 段内「逐版计数型」措辞命中:', hit)
ck('D3.1 【审计员成立】R159 段内不含「每版」「1 次/版」「各 1 次」「每版各」等逐版计数措辞',
   sum(hit.values()) == 0, hit)
ck('D3.2 原文只断言「出现与否 + 首现版 + 延续版」三件事（不含逐版计数）',
   ('V539 及以前共 0 版命中' in seg) and ('首现于 V540' in seg) and ('V541/V542 逐字延续' in seg),
   'ok')
ck('D3.3 原文的出现次数「1」是该串在**单版内**的行内计数（不是跨版每版计数）',
   '「N 行分解 + 三项算式」在 **V539 及以前共 0 版命中**' in seg, 'ok')
# R159 自述的 13 版范围与实测是否一致
cnt = {}
for d in V:
    ver = int(d.rsplit('_V', 1)[1])
    gg = rows(os.path.join(T, d, 'FACT_INDEX.tsv'))['F23']
    cnt[ver] = (gg[1].count('12 行分解') + gg[4].count('12 行分解'))
ck('D3.4 R159 自述的 V530..V542 范围内 13/13 与实测一致（⇒ 它不是虚构）',
   all(cnt[v] == 0 for v in range(530, 540)) and cnt[540] == 1 and cnt[541] == 1 and cnt[542] == 1,
   {v: cnt[v] for v in range(530, 543)})
ck('D3.5 【真正缺口】V543/V544 已各为 3 次，超出 R159 自述上限 V542',
   cnt[543] == 3 and cnt[544] == 3, (cnt[543], cnt[544]))
# 我自己的转述：V545 的 ADD23 里写了什么
g5 = rows(V545)['F23']
seg5 = g5[4][g5[4].index('【R165 补·R159 作用域已过期】'):]
print()
print('   我在 V545 追加段里的写法命中检查:')
for p in ('1 次/版', '每版 1 次', '钉在'):
    print('      %-8s -> %d' % (p, seg5.count(p)))
ck('D3.6 【自错 S-513】我在 V545 追加段写了「把出现次数钉在 1 次/版」——'
   '原 R159 段并不逐字这样说（审计员 #385 D3 的收窄）',
   '1 次/版' in seg5, seg5.count('1 次/版'))
ck('D3.7 该转述属于「我加的措辞」，不是原文摘引（原文段内该串 0 次）',
   sum(hit.values()) == 0 and '1 次/版' in seg5)

res = {'D1_rep': rep, 'D2_per_col': per, 'D3_counts': cnt,
       'D3_r159_pat': hit, 'fails': FAILS, 'assertions': RES}
json.dump(res, open(OUT, 'w'), ensure_ascii=False, indent=1)
print()
print('=== FAILS: %d ===' % len(FAILS))
for f_ in FAILS:
    print('   -', f_)
sys.exit(1 if FAILS else 0)
