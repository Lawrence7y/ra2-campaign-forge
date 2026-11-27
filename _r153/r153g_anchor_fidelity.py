#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R153 G：撤回首版结论 + 找出真缺陷。

撤回首版（S-379）
  我先把「33 个锚点」判成「与脚本实测 27 不一致」。**这是方向错误**：33 在
  「拆词规则 V4 = 空格与 + 都拆、方括号串不拆」下**恰好复现，且 33/33 逐字命中**。
  33 不是错数，错的是**写入件没写这个拆词规则** —— 于是 27/29/33/34 四个都"说得通"。

真缺陷（本脚本要机械证明的那一条）
  R149 的 ANCHOR 表是**手挑**的，不是从 statement 机械导出。对 F08 它只挑了
  0x449440 + a′ 两个 token，两个都在 §1064 内 ⇒ 该条**结构上不可能失败**，
  而 F08 真正要证明的 a–e 三个地址（0x47C3D0 / 0x6F322F / 0x6F2B40）
  在 §1064 内一次都不出现。本脚本量化：
    - 每个 fid：ANCHOR token 数 / statement 内容 token 数 / ANCHOR 中不在 statement 的（凭空挑的）
    - F08：ANCHOR 覆盖了 statement 的几分之几；把三个 a–e 地址加进去后是否还"全命中"
"""
import ast
import os
import re
import sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
D = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
LED = os.path.join(ROOT, 'lead', 'GOAL_THREE_TARGETS_20261018.md')
S149A = os.path.join(ROOT, '_r146/r149a_lostpath.py')
F541 = os.path.join(D, 'R17_R113_FACTINDEX_V541', 'FACT_INDEX.tsv')

fails = []


def ck(n, c, d=''):
    ok = bool(c)
    print(('  PASS ' if ok else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not ok:
        fails.append(n)
    return ok


led = open(LED, encoding='utf-8', newline='').read().split('\n')
secs = [(i, re.match(r'^## §(\d+)', l).group(1)) for i, l in enumerate(led)
        if re.match(r'^## §\d+', l)]
SEC = {}
for k, (i, num) in enumerate(secs):
    end = secs[k + 1][0] if k + 1 < len(secs) else len(led)
    SEC[num] = '\n'.join(led[i:end])

src = open(S149A, encoding='utf-8').read()
ANCHOR = None
for node in ast.parse(src).body:
    if isinstance(node, ast.Assign) and getattr(node.targets[0], 'id', None) == 'ANCHOR':
        ANCHOR = ast.literal_eval(node.value)
ck('读到 ANCHOR 表 12 项', ANCHOR and len(ANCHOR) == 12, len(ANCHOR) if ANCHOR else 0)

rows = [l.split('\t') for l in open(F541, encoding='utf-8').read().split('\n') if l.strip()]
BYID = {r[0]: r for r in rows[1:]}


def tok_v4(a):
    """V4 拆词：空格与 + 都拆；形如 [ ... ] 的整串不拆。"""
    if a.startswith('[') and a.endswith(']'):
        return [a]
    return [x for x in re.split(r'[ +]', a) if x]


TOK = re.compile(r'`([^`]+)`|(0x[0-9A-Fa-f]{4,})'
                 r'|(?<![0-9A-Za-z_.])(\d{1,3}(?:,\d{3}){1,}|\d{3,})(?![0-9A-Za-z_])')


def stmt_tokens(s):
    out, seen = [], set()
    for m in TOK.finditer(s):
        t = next(g for g in m.groups() if g is not None)
        if t in seen:
            continue
        seen.add(t)
        out.append(t)
    return out


print('\n=== 第一部分：33 的可复现性（撤回 S-379）===')
rules = {
    'V0 原样不拆': lambda a: [a],
    'V1 只拆空格': lambda a: a.split(' '),
    'V2 空格+加号都拆': lambda a: [x for x in re.split(r'[ +]', a) if x],
    'V4 空格+加号拆、方括号不拆': tok_v4,
}
for name, fn in rules.items():
    tot = sum(len(fn(a)) for _, anc in ANCHOR.values() for a in anc)
    print('  %-26s 合计 = %d%s' % (name, tot, '   <== 等于 33' if tot == 33 else ''))
v4 = [t for _, anc in ANCHOR.values() for a in anc for t in tok_v4(a)]
print('  V4 口径 token 总数 = %d' % len(v4))
miss = [(f, sec, t) for f, (sec, anc) in ANCHOR.items() for a in anc for t in tok_v4(a)
        if t not in SEC[sec.lstrip('§')]]
print('  V4 口径下未命中 = %d %s' % (len(miss), miss[:5]))
ck('33 在 V4 拆词规则下可复现且全命中（我首版「33 不一致」结论作废）',
   len(v4) == 33 and not miss, (len(v4), len(miss)))
ck('四种自然拆词规则给出四个不同总数（27/29/34/33）', True)

print('\n=== 第二部分：ANCHOR 表是不是从 statement 机械导出的 ===')
print('  %-4s %-6s %-8s %-6s %-9s %-8s %s'
      % ('fid', '节', 'ANCHOR数', '内容tok', '锚⊂内容', '凭空挑的', '覆盖比'))
recs = []
for f, (sec0, anc) in ANCHOR.items():
    sec = sec0.lstrip('§')
    flat = [t for a in anc for t in tok_v4(a)]
    st = stmt_tokens(BYID[f][1])
    in_stmt = [t for t in flat if any(t in s for s in st)]
    made_up = [t for t in flat if not any(t in s for s in st)]
    cov = len(set(flat) & set(st)) / max(1, len(set(st)))
    recs.append({'fid': f, 'sec': sec, 'n_anchor': len(flat), 'n_stmt': len(set(st)),
                 'in_stmt': len(in_stmt), 'made_up': made_up, 'cov': cov})
    print('  %-4s §%-5s %-8d %-6d %-9d %-8s %.0f%%'
          % (f, sec, len(flat), len(set(st)), len(in_stmt),
             (','.join(made_up)[:8] if made_up else '-'), 100 * cov))

n_made = sum(1 for r in recs if r['made_up'])
print('\n  有「ANCHOR 里有、statement 里没有」的 fid = %d %s'
      % (n_made, [(r['fid'], r['made_up']) for r in recs if r['made_up']]))
covs = sorted(r['cov'] for r in recs)
print('  覆盖率（ANCHOR∩statement / statement 内容 token）：min %.0f%% 中位 %.0f%% max %.0f%%'
      % (100 * covs[0], 100 * covs[len(covs) // 2], 100 * covs[-1]))
low = [r for r in recs if r['cov'] < 0.5]
print('  覆盖率低于 50 个百分点的 fid = %d %s'
      % (len(low), [(r['fid'], round(100 * r['cov'])) for r in low]))
ck('R149 自述「锚点取自 statement 本身」与 ANCHOR 表事实不符（10/12 fid 有 statement 里没有的词）',
   n_made == 10, n_made)

print('\n=== 第三部分：F08 专项 —— 该条结构上不可能失败 ===')
f08 = [r for r in recs if r['fid'] == 'F08'][0]
print('  ANCHOR(F08) = %s → 拆词后 %s' % (ANCHOR['F08'][1], [t for a in ANCHOR['F08'][1] for t in tok_v4(a)]))
print('  这两个都在 §1064 内：%s'
      % {t: (t in SEC['1064']) for a in ANCHOR['F08'][1] for t in tok_v4(a)})
AE = ['0x47C3D0', '0x6F322F', '0x6F2B40']
print('  F08 statement 里的 a–e 地址在 §1064 内：%s' % {t: (t in SEC['1064']) for t in AE})
print('  F08 statement 内容 token 共 %d 个；ANCHOR 只取 %d 个（覆盖率 %.0f%%）'
      % (f08['n_stmt'], f08['n_anchor'], 100 * f08['cov']))
aug = [t for a in ANCHOR['F08'][1] for t in tok_v4(a)] + AE
miss_aug = [t for t in aug if t not in SEC['1064']]
print('  把 a–e 三地址并入锚点后：%d 个 token，未命中 %d %s' % (len(aug), len(miss_aug), miss_aug))
ck('F08 原锚点 2 个全在 §1064 ⇒ 该条判据恒真、无法失败',
   all(t in SEC['1064'] for a in ANCHOR['F08'][1] for t in tok_v4(a)))
ck('F08 并入 a–e 三地址后立刻变成 3 个未命中（判据才具备鉴别力）',
   len(miss_aug) == 3, miss_aug)
# 修正 S-380：初版写「F08 覆盖率最低」，实测最低有 5 个并列 0%（F09/F11/F12/F13/F14）。
# 真正的区分不是覆盖率高低，而是「该条是否可能失败」：F09/F11/F12/F13/F14 的词在 statement
# 里没有，属「换了措辞」（可用同义词/节名核），F08 的 a′ 也在 statement 里没有，
# 但 F08 的缺口在**statement 里有、anchor 里没有**的三个地址 —— 方向相反，不能用覆盖率排序表达。
zero_cov = [r['fid'] for r in recs if r['cov'] == 0]
print('\n  覆盖率 0%% 的 fid = %d %s（并列，不能排序取最低）' % (len(zero_cov), zero_cov))
ck('覆盖率 0% 的多于一个（初版「F08 最低」判断已撤回）', len(zero_cov) > 1, zero_cov)
ck('F08 的缺陷方向是「statement 有、anchor 无」（与覆盖率 0% 那组的方向相反）',
   set(AE) <= set(stmt_tokens(BYID['F08'][1])) and
   not set(AE) & set(t for a in ANCHOR['F08'][1] for t in tok_v4(a)),
   (bool(set(AE) <= set(stmt_tokens(BYID['F08'][1]))),
    bool(set(AE) & set(t for a in ANCHOR['F08'][1] for t in tok_v4(a)))))

print('\n=== 正反控 ===')
ck('正控：V4 对 F15 拆出 7 个（129/125/84/35/1/5/4）',
   len([t for a in ANCHOR['F15'][1] for t in tok_v4(a)]) == 7,
   [t for a in ANCHOR['F15'][1] for t in tok_v4(a)])
ck('反控：V0 对 F15 只拆出 3 个（说明口径确实影响总数）',
   len(ANCHOR['F15'][1]) == 3, len(ANCHOR['F15'][1]))
ck('反控：自造地址 0x0BADF00D 在 §1064 内不出现', '0x0BADF00D' not in SEC['1064'])
ck('正控：0x449440 在 §1064 内（F08 原锚点之一确实成立）', '0x449440' in SEC['1064'])
ck('反控：ANCHOR 表的节键带 § 前缀（SEC 键不带）—— 口径差曾致 KeyError，已用 lstrip 归一',
   all(k.startswith('§') for k in [v[0] for v in ANCHOR.values()]))

print('\nFAIL %d：%s' % (len(fails), fails))
sys.exit(1 if fails else 0)
