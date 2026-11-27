#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R153 D：两处「数字与它自己的脚本输出不一致」的机械核验。

D1「33 个锚点」
  三份写入件（台账 §1204 一、看板归档 L8297 段、COMPACT_STATE R149 摘要）都写
  「12 个 fid、33 个锚点全部逐字命中」，而生成它的脚本 `_r146/r149a_lostpath.py`
  的 ANCHOR 表逐 fid 相加 = 27，脚本自己的输出 `_r146/r149a_lostpath.json` 的
  `anchor[*].anchors` 也合计 27。本脚本：
    - 从**源脚本 AST 里读出 ANCHOR 表**（不硬编码，避免抄错）；
    - 从 **json 输出**里读每 fid 的 anchors 长度；
    - 统计 "33 个锚点" 字面在四件里的传播行数；
    - 穷举 10 种口径看有没有一种等于 33。

D2「事项级 vs 节级」
  对 12 个 fid 的**每一个**台账锚点条目，按 evidence_paths 里点名的「事项N」定位到
  台账同名节的第 N 个子项块，判 statement token 是否落在**那个块**里。
  这直接回答 R152 看板待办 4（F08 锚点粒度）到底是「F08 一条」还是「一类」。

反控：正控/反控各至少两条，且都必须是可失败的。
"""
import ast
import json
import os
import re
import sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
D = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
LED = os.path.join(ROOT, 'lead', 'GOAL_THREE_TARGETS_20261018.md')
LOCK = os.path.join(ROOT, 'lead', 'LEAD_LOCK')
RC = os.path.join(D, 'R14_COMMON.md')
ARC = os.path.join(D, 'BOARD_ARCHIVE.md')
CS = os.path.join(D, 'COMPACT_STATE.md')
BRD = os.path.join(D, 'STATUS_BOARD.md')
S149A = os.path.join(ROOT, '_r146/r149a_lostpath.py')
J149A = os.path.join(ROOT, '_r146/r149a_lostpath.json')
F541 = os.path.join(D, 'R17_R113_FACTINDEX_V541', 'FACT_INDEX.tsv')

fails = []


def ck(n, c, d=''):
    ok = bool(c)
    print(('  PASS ' if ok else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not ok:
        fails.append(n)
    return ok


# ================= D1 =================
print('=== D1 「33 个锚点」 vs 脚本实测 ===')
src = open(S149A, encoding='utf-8').read()
tree = ast.parse(src)
ANCHOR = None
for node in tree.body:
    if isinstance(node, ast.Assign) and getattr(node.targets[0], 'id', None) == 'ANCHOR':
        ANCHOR = ast.literal_eval(node.value)
ck('从 AST 读到 r149a 的 ANCHOR 表（12 项）', ANCHOR is not None and len(ANCHOR) == 12,
   len(ANCHOR) if ANCHOR else None)
per = {k: len(v[1]) for k, v in ANCHOR.items()}
print('  逐 fid 锚点数：%s' % per)
n_ast = sum(per.values())
print('  AST 口径合计 = %d' % n_ast)

j = json.load(open(J149A, encoding='utf-8'))
n_json = sum(len(v['anchors']) for v in j['anchor'].values())
print('  r149a 自己的 JSON 输出合计 = %d' % n_json)
ck('AST 与 JSON 两个口径相同（27）', n_ast == n_json == 27, (n_ast, n_json))
ck('「33」在 r149a 脚本与 json 里都不成立', n_ast != 33 and n_json != 33, (n_ast, n_json))

# 穷举口径
rows = [l.split('\t') for l in open(F541, encoding='utf-8').read().split('\n') if l.strip()]
data = rows[1:]
led_lines = open(LED, encoding='utf-8', newline='').read().split('\n')
secs = [(i, re.match(r'^## §(\d+)', l).group(1)) for i, l in enumerate(led_lines)
        if re.match(r'^## §\d+', l)]
SEC = {}
for k, (i, num) in enumerate(secs):
    end = secs[k + 1][0] if k + 1 < len(secs) else len(led_lines)
    SEC[num] = (i, end)


def split_item(it):
    it = it.strip()
    i = it.find('(')
    if i < 0 or not it.endswith(')'):
        return it, None
    return it[:i], it[i + 1:-1]


leditems = []
for r in data:
    for it in r[3].split(';'):
        it = it.strip()
        if 'R17_LEDGER_10' not in it:
            continue
        path, anchor = split_item(it)
        if 'R17_LEDGER_10' not in path:
            continue
        m = re.search(r'R17_LEDGER_(\d+)', path)
        sec = '1063' if m.group(1) == '1063R' else m.group(1)
        nums = [int(x) for x in re.findall(r'事项\s*(\d+)', anchor or '')]
        leditems.append({'fid': r[0], 'sec': sec, 'nums': nums, 'anchor': anchor})

cands = {
    'A 甲类证据条目数': len(leditems),
    'B (fid,节) 去重': len(set((x['fid'], x['sec']) for x in leditems)),
    'C (fid,节,事项) 三元组': len(set((x['fid'], x['sec'], n) for x in leditems
                                  for n in (x['nums'] or [-1]))),
    'D R149 ANCHOR 表合计': n_ast,
    'E R149 ANCHOR 表 + 事项号个数': n_ast + sum(len(x['nums']) for x in leditems),
    'F 甲类 fid 数': len(set(x['fid'] for x in leditems)),
    'G 全部 evidence 项数': sum(len([y for y in r[3].split(';') if y.strip()]) for r in data),
    'H 甲类条目数 + fid 数': len(leditems) + len(set(x['fid'] for x in leditems)),
    'I 5 节 + 17 条 + 12 fid − 1': 5 + len(leditems) + len(set(x['fid'] for x in leditems)) - 1,
    'J ANCHOR 表合计 + 6': n_ast + 6,
}
print('\n  口径穷举（只报数，不挑答案）：')
for k, v in cands.items():
    print('    %-30s = %d%s' % (k, v, '   <== 等于 33' if v == 33 else ''))
eq33 = [k for k, v in cands.items() if v == 33]
print('    等于 33 的机械口径：%s' % (eq33 if eq33 else '无'))

print('\n  字面「33 个锚点」传播面：')
for name, p in (('台账', LED), ('看板归档', ARC), ('COMPACT_STATE', CS),
                ('R14_COMMON', RC), ('LEAD_LOCK', LOCK), ('看板', BRD)):
    t = open(p, encoding='utf-8', newline='').read().split('\n')
    hit = [i + 1 for i, l in enumerate(t) if '33 个锚点' in l]
    print('    %-14s %d 行 %s' % (name, len(hit), hit[:6]))
# 允许的写死口径：ANCHOR 表 27
ck('传播面至少 3 处（台账 / 归档 / COMPACT_STATE）',
   all('33 个锚点' in open(p, encoding='utf-8', newline='').read()
       for p in (LED, ARC, CS)))

# ================= D2 =================
print('\n=== D2 事项级落位（evidence_paths 点名的事项块内）===')


def block(sec, item):
    i, e = SEC[sec]
    body = led_lines[i:e]
    st = []
    for jj, l in enumerate(body):
        m = re.match(r'^###\s*(?:事项\s*)?(\d+)', l)
        if m:
            st.append((jj, int(m.group(1))))
    for idx, (jj, k) in enumerate(st):
        if k == item:
            end = st[idx + 1][0] if idx + 1 < len(st) else len(body)
            return '\n'.join(body[jj:end])
    return ''


TOK = re.compile(r'`([^`]+)`|(0x[0-9A-Fa-f]{4,})'
                 r'|(?<![0-9A-Za-z_.])(\d{1,3}(?:,\d{3}){1,}|\d{3,})(?![0-9A-Za-z_])')


def toks(stmt):
    out, seen = [], set()
    for m in TOK.finditer(stmt):
        t = next(g for g in m.groups() if g is not None)
        if t in seen:
            continue
        seen.add(t)
        out.append(t)
    return out


BYID = {r[0]: r for r in data}
print('  %-4s %-6s %-9s %-10s %-27s %s' % ('fid', '节', '事项', '锚形态', '块内命中/总 token', '未命中'))
recs = []
for x in leditems:
    stmt = BYID[x['fid']][1]
    T = toks(stmt)
    full = '\n'.join(led_lines[SEC[x['sec']][0]:SEC[x['sec']][1]])
    sec_hit = [t for t in T if t in full]
    if x['nums']:
        uni = '\n'.join(block(x['sec'], n) for n in x['nums'])
        kind = '事项' + '/'.join(str(n) for n in x['nums'])
    else:
        uni = ''
        kind = 'freetext'
    item_hit = [t for t in T if uni and t in uni]
    miss = [t for t in T if t not in (uni or '')]
    recs.append({'fid': x['fid'], 'sec': x['sec'], 'kind': kind, 'n': len(T),
                 'sec': x['sec'], 'sec_hit': len(sec_hit), 'item_hit': len(item_hit),
                 'miss': miss, 'nums': x['nums']})
    print('  %-4s §%-5s %-9s %-10s %2d/%-3d -> %2d/%-3d  %s'
          % (x['fid'], x['sec'], kind, 'tokens', len(sec_hit), len(T), len(item_hit), len(T),
             (','.join(miss)[:56] if miss else '')))

n_have_nums = sum(1 for r in recs if r['nums'])
n_item_full = sum(1 for r in recs if r['nums'] and r['item_hit'] == r['n'])
n_item_part = sum(1 for r in recs if r['nums'] and 0 < r['item_hit'] < r['n'])
n_item_zero = sum(1 for r in recs if r['nums'] and r['item_hit'] == 0)
print('\n  带「事项N」锚的条目 = %d ；块内全命中 = %d ；部分 = %d ；零 = %d'
      % (n_have_nums, n_item_full, n_item_part, n_item_zero))
print('  节级全命中条目 = %d / %d'
      % (sum(1 for r in recs if r['sec_hit'] == r['n']), len(recs)))

# 逐 fid 汇总：是否存在「节级全中但事项级不全」
fid_bad = sorted(set(r['fid'] for r in recs if r['nums'] and r['item_hit'] < r['n']))
print('  事项级不全的 fid = %d %s' % (len(fid_bad), fid_bad))
ck('F08 在事项级不全（R152 待办 4 的对象）', 'F08' in fid_bad, fid_bad)

# ================= 正反控 =================
print('\n=== 正反控 ===')
ck('反控：自造串 ZZZ_R153_QQQ 在台账 0 命中', 'ZZZ_R153_QQQ' not in
   open(LED, encoding='utf-8', newline='').read())
b4 = block('1064', 4)
b3 = block('1064', 3)
ck('正控：§1064 事项4 含 a′ 且不含「不得升格」',
   'a′' in b4 and '不得升格' not in b4, ('a′' in b4, '不得升格' in b4))
ck('反控：§1064 事项3 含「不得升格」（说明两块确实被切开）', '不得升格' in b3)
ck('正控：F04 的 11 个 token 在 §1062 事项1 块内全命中',
   [r for r in recs if r['fid'] == 'F04'][0]['item_hit'] ==
   [r for r in recs if r['fid'] == 'F04'][0]['n'])
ck('反控：把 F04 token 之一改末位，块内不再命中',
   '0x43F181' not in block('1062', 1))

print('\nFAIL %d：%s' % (len(fails), fails))
sys.exit(1 if fails else 0)
