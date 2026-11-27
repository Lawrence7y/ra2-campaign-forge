#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R156 A：FACT_INDEX 里 17 个指向 R17_LEDGER_*/SECTION.md 的证据项，**逐项承载性**首测。

R155 只证了「事项号在台账正文存在」（13/17）。本轮问的是更强的问题：
该证据项点名的那个事项，**到底承不承载 statement 里的可核对象**？

双轴判据（statement 侧取值 → 被指事项侧查在）：
  · 地址轴：statement 中所有 0xXXXX / 8 位大写十六进制 → 归一到整数集合
  · 数字轴：statement 中所有 >=3 位的十进制整数（排除紧邻字母/小数点的）
三个作用域对照（区分「承载在点名事项」与「承载在别处」）：
  · named  = 证据项点名的事项切片之并集
  · others = 同节内除点名事项外的其余切片之并集
  · whole  = 整节

锚点解析（R155 的解析器只认「事项N」，故 3 项被判 NO_ITEM_ANCHOR —— 那是解析器缺陷，不是盘上事实）：
  1) 「事项 N」/「事项 N/M」→ 按 ### 标题里的编号定位
  2) 其余 → 主题串，去反引号后与各 ### 标题做双向包含匹配
每个环节都带正控与反控。
"""
import os, re, json, sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
LED  = ROOT + '/lead/GOAL_THREE_TARGETS_20261018.md'
IDX  = ROOT + '/lead/next_re_20261117_r14/R17_R114_FACTINDEX_V542/FACT_INDEX.tsv'
OUT  = ROOT + '/_r156/r156a_carrying.json'

fails = []
def ck(name, cond, detail=''):
    print(('  PASS ' if cond else '  FAIL ') + name + (('  ' + str(detail)) if detail else ''))
    if not cond: fails.append(name)

t = open(LED, encoding='utf-8').read()

# ---------- 0 · 台账节索引 ----------
secpos = {}
for m in re.finditer(r'(?m)^## §(\d+[A-Za-z]?) ·', t):
    secpos.setdefault(m.group(1), []).append(m.start())
ck('0.1 台账节数 > 500', len(secpos) > 500, len(secpos))
ck('0.2 §1062/1063/1064/1065 各恰好 1 节',
   all(len(secpos.get(n, [])) == 1 for n in ('1062', '1063', '1064', '1065')),
   {n: len(secpos.get(n, [])) for n in ('1062', '1063', '1064', '1065')})
ck('0.3 反控：§9999 不存在', '9999' not in secpos)

def sec(num):
    p = secpos[num][0]
    nxt = re.search(r'(?m)^## §', t[p + 10:])
    return t[p:p + 10 + nxt.start()] if nxt else t[p:]

# ---------- 1 · 节内 ### 子标题编号（items） ----------
def heads(num):
    """返回 [(item_no 或 None, heading, slice)]。item_no 取标题首部「事项 N」或「N.」/「N·」。"""
    s = sec(num); hs = []
    for m in re.finditer(r'(?m)^###\s+(.*)$', s):
        h = m.group(1)
        mm = re.match(r'(?:事项\s*)?([1-9])\s*[\.·、]', h)
        hs.append((m.start(), int(mm.group(1)) if mm else None, h))
    out = []
    for i, (p, n, h) in enumerate(hs):
        e = hs[i + 1][0] if i + 1 < len(hs) else len(s)
        out.append((n, h, s[p:e]))
    return out

NUM_ITEMS = {n: sorted(x[0] for x in heads(n)) for n in ('1062', '1063', '1064', '1065')}
print('  节内 ### 编号:', NUM_ITEMS)
ck('1.1 §1062 编号 {1..7}', NUM_ITEMS['1062'] == [1, 2, 3, 4, 5, 6, 7], NUM_ITEMS['1062'])
ck('1.2 §1063 编号 {1..7}', NUM_ITEMS['1063'] == [1, 2, 3, 4, 5, 6, 7], NUM_ITEMS['1063'])
ck('1.3 §1064 编号 {1..6}', NUM_ITEMS['1064'] == [1, 2, 3, 4, 5, 6], NUM_ITEMS['1064'])
ck('1.4 §1065 编号 {1..5}', NUM_ITEMS['1065'] == [1, 2, 3, 4, 5], NUM_ITEMS['1065'])
# 反控：不存在第 8 项、第 7 项在 §1064 里也不存在
ck('1.5 反控：§1062 无第 8 项', 8 not in NUM_ITEMS['1062'])
ck('1.6 反控：§1064 无第 7 项', 7 not in NUM_ITEMS['1064'])

# ---------- 2 · 双轴取值 ----------
def addr_set(s):
    """地址归一：0xNNNN.. 与 8 位裸十六进制，都归一成 int。"""
    out = set()
    for m in re.finditer(r'(?<![0-9A-Za-z])0x([0-9A-Fa-f]{3,8})(?![0-9A-Za-z])', s):
        out.add(int(m.group(1), 16))
    for m in re.finditer(r'(?<![0-9A-Za-z])([0-9A-Fa-f]{8})(?![0-9A-Za-z])', s):
        out.add(int(m.group(1), 16))
    return out

def num_set(s):
    """数字归一：先抹平千位逗号（4,063,232 -> 4063232），再把 §NNNN 节号剔出去（节号不是数据值）。"""
    s = re.sub(r'(?<![0-9A-Za-z.])(\d{1,3}(?:,\d{3})+)', lambda m: ' %s ' % m.group(1).replace(',', ''), s)
    s = re.sub(r'§\s*\d+', ' §SEC ', s)
    return set(int(x) for x in re.findall(r'(?<![0-9A-Za-z.])(\d{3,7})(?![0-9A-Za-z])', s))

# 正控：两种书写形式归一到同一值
ck('2.1 正控：0x5A5020 与 005A5020 归一到同一 int',
   addr_set('0x5A5020') == addr_set('005A5020') == {0x5A5020})
# 反控：不该被吃进来的形态
ck('2.2 反控：0x12（2 位）不进地址集', addr_set('0x12') == set())
ck('2.3 反控：42（2 位十进制）不进数字集', num_set('42 个') == set())
ck('2.4 反控：3.14 的小数部分不进数字集', 14 not in num_set('3.14'))
# 正控：千位逗号与节号两种书写形态
ck('2.5 正控：4,063,232 归一为 4063232', num_set('.text 4,063,232 B') == {4063232})
ck('2.6 反控：§1062 是节引用、不进数字集', 1062 not in num_set('已被 §1062 第三版取代'))
ck('2.7 正控：14,044 归一为 14044', num_set('约 14,044 个槽值') == {14044})

# ---------- 3 · 证据项抽取与锚点解析 ----------
rows = [l.split('\t') for l in open(IDX, encoding='utf-8').read().split('\n') if l.count('\t') == 4]
data = {r[0]: r for r in rows[1:]}
ck('3.0 数据行 54', len(data) == 54, len(data))

RE_ITEM = re.compile(r'R17_LEDGER_([0-9A-Za-z]+)[\\/]+(SECTION\.md|SUPERSEDED\.md)(?:\(([^)]*)\))?')

def norm_topic(x): return x.replace('`', '').strip()

def resolve(d, topic):
    """topic → (命中的 item_no 列表, 说明)。事项形式优先，其余走主题双向包含。"""
    tp = norm_topic(topic or '')
    hs = heads(d)
    mm = re.search(r'事项\s*([0-9](?:\s*/\s*[0-9])*)', tp)
    if mm:
        nums = [int(x) for x in re.split(r'\s*/\s*', mm.group(1))]
        return [n for n in nums if n in [h[0] for h in hs]], 'ITEM_NO'
    # 主题串：可能被「 / 」并列
    parts = [p.strip() for p in tp.split('/') if p.strip()]
    if not parts: return [], 'EMPTY'
    picked = []
    for p in parts:
        for n, h, sl in hs:
            nh = norm_topic(h)
            if p and (p in nh or nh in p):
                picked.append(n)
    return sorted(set(x for x in picked if x is not None)), 'TOPIC'

items = []
for f, r in data.items():
    for it in r[3].split(';'):
        m = RE_ITEM.search(it)
        if not m: continue
        d, fn, topic = m.group(1), m.group(2), m.group(3)
        rec = dict(fid=f, dir=d, file=fn, topic=topic, raw=it.strip())
        if fn != 'SECTION.md':
            rec.update(status='NON_SECTION', picked=[])
        elif d not in secpos:
            rec.update(status='NO_LEDGER_SECTION', picked=[])
        else:
            picked, how = resolve(d, topic)
            rec.update(status='RESOLVED' if picked else 'UNRESOLVED', picked=picked, how=how)
        items.append(rec)

ck('3.1 证据项总数 17', len(items) == 17, len(items))
from collections import Counter
st = Counter(x['status'] for x in items)
print('  状态分布:', dict(st))
ck('3.2 仅有 1 项是非 SECTION.md（SUPERSEDED.md）', st.get('NON_SECTION', 0) == 1, st.get('NON_SECTION'))
ck('3.3 仅 F15 的 1063R 没同名节', st.get('NO_LEDGER_SECTION', 0) == 1, st.get('NO_LEDGER_SECTION'))
# 关键：R155 报的 3 个 NO_ITEM_ANCHOR 在这里必须全部解析出来（解析器缺陷，不是盘上事实）
r155_noanchor = [(x['fid'], x['dir']) for x in items if x['status'] == 'UNRESOLVED']
ck('3.4 主题型锚点全部可解析（R155 的 NO_ITEM_ANCHOR=3 是解析器缺陷）',
   len(r155_noanchor) == 0, r155_noanchor)

# 逐条打印解析结果，供人工核
print('  --- 锚点解析 ---')
for x in items:
    print('    %-4s §%-6s %-13s picked=%-9s how=%-8s topic=%s'
          % (x['fid'], x['dir'].replace('R17_LEDGER_', ''), x['file'],
             x['picked'], x.get('how', '-'), (x['topic'] or '')[:44]))

# ---------- 4 · 承载性三元对照 ----------
res = []
for f in sorted(set(x['fid'] for x in items)):
    A = addr_set(data[f][1]); N = num_set(data[f][1])
    named, others, whole = '', '', ''
    dirs = []
    for x in items:
        if x['fid'] != f: continue
        if x['dir'] in secpos:
            dirs.append(x['dir']); whole += sec(x['dir'])
            hs = heads(x['dir'])
            n = [h for h in hs if h[0] in x['picked']]
            named += ''.join(h[2] for h in n)
            others += ''.join(h[2] for h in hs if h[0] not in x['picked'])
    na, oa, wa = addr_set(named), addr_set(others), addr_set(whole)
    nn, on, wn = num_set(named), num_set(others), num_set(whole)
    row = dict(fid=f, dirs=dirs,
               addr_total=len(A), addr_named=len(A & na), addr_others=len(A & oa), addr_whole=len(A & wa),
               num_total=len(N), num_named=len(N & nn), num_others=len(N & on), num_whole=len(N & wn),
               addr_miss_named=sorted('%X' % v for v in A - na),
               num_miss_named=sorted(N - nn),
               merged_total=len(A) + len(N),
               merged_named=len(A & na) + len(N & nn))
    row['carry_rate'] = (100.0 * row['merged_named'] / row['merged_total']) if row['merged_total'] else None
    res.append(row)

print('  --- 承载矩阵（named = 点名事项并集） ---')
print('   %-4s %-12s %-18s %-18s %s' % ('fid', 'dirs', 'addr named/total', 'num named/total', 'rate'))
for r in res:
    print('   %-4s %-12s %2d/%-2d              %2d/%-2d              %s'
          % (r['fid'], ','.join(d.replace('R17_LEDGER_', '') for d in r['dirs']),
             r['addr_named'], r['addr_total'], r['num_named'], r['num_total'],
             ('%.1f%%' % r['carry_rate']) if r['carry_rate'] is not None else 'n/a'))

# 分档
def grade(r):
    if r['merged_total'] == 0: return 'NO_ANCHOR_VALUE'
    if r['merged_named'] == r['merged_total']: return 'FULL'
    if r['merged_named'] > 0: return 'PARTIAL'
    return 'NONE'
for r in res: r['grade'] = grade(r)
gr = Counter(r['grade'] for r in res)
print('  档位:', dict(gr))
ck('4.1 分档闭合（四档之和 = 12 个 fid）', sum(gr.values()) == 12, sum(gr.values()))
ck('4.2 至少有一个 fid 是 PARTIAL 或 NONE（否则本判据无鉴别力）',
   gr.get('PARTIAL', 0) + gr.get('NONE', 0) >= 1, dict(gr))
ck('4.3 至少有一个 fid 是 FULL（否则判据恒假）', gr.get('FULL', 0) >= 1, dict(gr))

# F08 必须是 PARTIAL 且缺的正是 R155 那三个地址（跨轮一致性）
f08 = [r for r in res if r['fid'] == 'F08'][0]
ck('4.4 F08 为 PARTIAL', f08['grade'] == 'PARTIAL', f08['grade'])
ck('4.5 F08 缺的三个地址正是 R155 报的那三个',
   set(f08['addr_miss_named']) == {'47C3D0', '6F322F', '6F2B40'}, f08['addr_miss_named'])
ck('4.6 F08 的缺口在整节里也补不上（whole 与 named 同值）',
   f08['addr_whole'] == f08['addr_named'], (f08['addr_whole'], f08['addr_named']))

# 反控：把一个绝不相关的节当 named，承载率必须塌到 0
ctl = addr_set(sec('1065')) & A if False else None
ctrl_named = addr_set(heads('1065')[4][2])  # §1065 第 5 项（方法学记录）
ck('4.7 反控：拿 §1065 第 5 项冒充 F08 的点名事项，承载数必须为 0',
   len(f08a := addr_set(data['F08'][1]) & ctrl_named) == 0, len(f08a))

# ---------- 5 · 反向核查：承载内容是否只落在 named ----------
cross = [r for r in res if r['addr_others'] > r['addr_named'] or r['num_others'] > r['num_named']]
print('  交叉承载（别处比点名处更多）的 fid:', [r['fid'] for r in cross])
for r in cross:
    print('    %s: addr named=%d others=%d whole=%d | num named=%d others=%d whole=%d'
          % (r['fid'], r['addr_named'], r['addr_others'], r['addr_whole'],
             r['num_named'], r['num_others'], r['num_whole']))

json.dump(dict(items=items, matrix=res, status=dict(st), grades=dict(gr), fails=fails),
          open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('  写出 %s' % OUT)
print('  === 断言 %d 条，FAIL %d ===' % (len(fails) + 0, len(fails)))
sys.exit(0 if not fails else 1)
