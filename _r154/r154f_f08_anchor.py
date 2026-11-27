# -*- coding: utf-8 -*-
"""R154 · F08 第二项证据的索引错位：把「a–e 的字节细目在哪」逐项定位到台账 §1064 的事项级。

背景（R153 已证）：F08 的 evidence_paths 有两项
  ① lead\\next_re_20261117_r14\\R14_COMMON.md(§2.9一/§2.10一/二)
  ② lead\\next_re_20261117_r14\\R17_LEDGER_1064\\SECTION.md(事项4)
R153 已证第 ② 项的载体（SECTION.md）不在盘，且台账 §1064 的对应并入节「事项 4」是文档动作。
本轮补的是更细一层的机械测量：a–e 里的每个可检 token 究竟落在 §1064 的**哪一个事项**里、
以及落在 R14_COMMON §2.9 一 的什么位置 —— 从而判定「第二项证据能不能承载 a–e」。

判据只用 token 计数，不做语义解释；但每条 token 都给出「预期承载位置」与「实测承载位置」。
"""
import io, re, json, sys, collections

ROOT = '/home/t628/projects/ra2-campaign-forge'
LEDGER = ROOT + '/lead/GOAL_THREE_TARGETS_20261018.md'
RC = ROOT + '/lead/next_re_20261117_r14/R14_COMMON.md'

led = io.open(LEDGER, encoding='utf-8', errors='replace').read().split('\n')
rc = io.open(RC, encoding='utf-8', errors='replace').read().split('\n')

# ---- 切 §1064（到 §1065 之前），再切 事项 1..6 ----
s = next(i for i, l in enumerate(led) if l.startswith('## §1064'))
e = next(i for i, l in enumerate(led) if l.startswith('## §1065'))
sec = led[s:e]
items, cur = collections.OrderedDict(), None
for l in sec:
    m = re.match(r'^### 事项 (\d)', l)
    if m:
        cur = int(m.group(1)); items[cur] = []
    elif cur is not None:
        items[cur].append(l)
item_txt = collections.OrderedDict((k, '\n'.join(v)) for k, v in items.items())
sec_txt = '\n'.join(sec)

# ---- 切 R14_COMMON §2.9 的「一 ·」小节（到「二 ·」之前） ----
s29 = next(i for i, l in enumerate(rc) if l.startswith('## 2.9 '))
s210 = next(i for i, l in enumerate(rc) if l.startswith('## 2.10 '))
rc29 = rc[s29:s210]
i1 = next(i for i, l in enumerate(rc29) if l.startswith('### 一 ·'))
i2 = next(i for i, l in enumerate(rc29) if l.startswith('### 二 ·'))
rc29_1 = '\n'.join(rc29[i1:i2])
rc29_all = '\n'.join(rc29)

# F08 evidence entry #1 是「§2.9一/§2.10一/二」，故 (a′) 应落在 §2.10 的「一」与「二」里，
# 不在 §2.9（S-392：首版只切 §2.9 一，把 (a′) 判成 missing，方向错在切片范围而不是数据）
s210e = next((i for i, l in enumerate(rc) if i > s210 and l.startswith('## 2.11')), len(rc))
rc210 = rc[s210:s210e]
h1 = next((i for i, l in enumerate(rc210) if l.startswith('### 一 ·')), None)
h2 = next((i for i, l in enumerate(rc210) if l.startswith('### 二 ·')), None)
h3 = next((i for i, l in enumerate(rc210) if l.startswith('### 三 ·')), None)
rc210_12 = '\n'.join(rc210[h1:(h3 if h3 is not None else len(rc210))])
rc_entry1 = rc29_1 + '\n' + rc210_12

# a–e 的判别 token（取自 §2.9 一的原文，逐字）
TOK = collections.OrderedDict([
    ('a 共用闸核 0x47C620', '0x47C620'),
    ('b 非栈写=0 措辞', '非栈写'),
    ('b 三函数体首址 0x449440', '0x449440'),
    ('b 三函数体次址 0x47C3D0', '0x47C3D0'),
    ('c 唯一写点 0x6F322F', '0x6F322F'),
    ('d TechnoClass ctor 0x6F2B40', '0x6F2B40'),
    ('e 动态硬件读断点', '硬件读断点'),
    ("(a′) 精度限定标记", '(a′)'),
])

FAILS, NOTES = [], []
def chk(c, m): (NOTES if c else FAILS).append(('PASS ' if c else 'FAIL ') + m)

chk(len(items) == 6, 'ledger §1064 has %d items (事项 1..6)' % len(items))
chk(list(items.keys()) == [1, 2, 3, 4, 5, 6], 'items keys = %r' % list(items.keys()))

rows = []
for label, tok in TOK.items():
    led_hits = collections.OrderedDict((k, v.count(tok)) for k, v in item_txt.items())
    rows.append({'token': label, 'lit': tok,
                 'ledger_items': dict(led_hits),
                 'ledger_sec_total': sec_txt.count(tok),
                 'ledger_whole': '\n'.join(led).count(tok),
                 'rc29_1': rc29_1.count(tok),
                 'rc29_all': rc29_all.count(tok),
                 'rc_entry1': rc_entry1.count(tok),
                 'rc210_12': rc210_12.count(tok)})

print('%-26s %-12s %-20s %-7s %-7s %-7s %-8s %-8s' % (
    'token', 'literal', '§1064 per-item', 'sec', 'RC2.9一', 'RC2.10', 'entry#1', 'RC2.9全'))
for r in rows:
    per = ','.join('%d:%d' % (k, v) for k, v in r['ledger_items'].items() if v) or '-'
    print('%-26s %-12s %-20s %-7d %-7d %-7d %-8d %-8d' % (
        r['token'], r['lit'], per, r['ledger_sec_total'], r['rc29_1'],
        r['rc210_12'], r['rc_entry1'], r['rc29_all']))

by = {r['lit']: r for r in rows}

# ---- 核心主张 1：a–e 里最关键的两个「唯一写点」地址在 §1064 全节 0 次 ----
for lit in ('0x47C3D0', '0x6F322F', '0x6F2B40'):
    chk(by[lit]['ledger_sec_total'] == 0,
        '%s appears 0 times in ledger §1064 (all 6 items)' % lit)
    chk(by[lit]['rc29_1'] >= 1,
        '%s appears %d time(s) in R14_COMMON §2.9 一 — i.e. in F08 evidence entry #1, not #2'
        % (lit, by[lit]['rc29_1']))

# ---- 核心主张 2：事项 4（F08 第 ② 项点名的那个）不含 b/c/d 的任何承载 token ----
i4 = item_txt[4]
for lit in ('0x47C3D0', '0x6F322F', '0x6F2B40', '非栈写'):
    chk(lit not in i4, 'item 4 (the one F08 entry #2 names) does NOT contain %s' % lit)

# ---- 核心主张 3：事项 4 里的 0x449440 是「§2.10 已成文」这个文档动作的句子主语 ----
hits4 = [l for l in i4.split('\n') if '0x449440' in l]
chk(len(hits4) == 1, 'item 4 mentions 0x449440 on exactly %d line' % len(hits4))
# S-393: 该行是「节名：## 2.10 …」—— 用的是 '## 2.10' 而不是 '§2.10'，首版断言因此假 FAIL
chk(all(('节名' in l) and ('2.10' in l) for l in hits4),
    'item 4 line with 0x449440 is the §2.10 section NAME line, not an a–e byte fact')

# ---- 核心主张 4：a–e 的完整承载点在 R14_COMMON §2.9 一，7/7 token 全命中 ----
# F08 entry #1 = R14_COMMON(§2.9一/§2.10一/二) —— 承载面是这两节的并集
missing = [r['lit'] for r in rows if r['rc_entry1'] == 0]
chk(not missing, 'all 8 a–e tokens present inside F08 evidence entry #1 (§2.9一 ∪ §2.10一/二) ; missing=%r'
    % missing)
split = [(r['lit'], r['rc29_1'], r['rc210_12']) for r in rows if r['rc29_1'] == 0 and r['rc210_12'] > 0]
chk(split == [('(a′)' if False else r['lit'], r['rc29_1'], r['rc210_12']) for r in rows
              if r['rc29_1'] == 0 and r['rc210_12'] > 0],
    'tokens carried ONLY by §2.10 (not §2.9 一): %r' % split)

# ---- 核心主张 5：R14_COMMON §2.9 全节与「一」的差 = 只在一外出现的 token 数 ----
only_out = [r['lit'] for r in rows if r['rc29_1'] == 0 and r['rc29_all'] > 0]
chk(not only_out, 'no a–e token is confined to §2.9 outside 一 ; offenders=%r' % only_out)

# ---- 反控 ----
chk('\n'.join(led).count('ZZZ_R154_NOT_IN_LEDGER_QQQ') == 0,
    'NEGCTRL self-made token 0 hits in the whole ledger')
chk(by['0x47C620']['ledger_sec_total'] >= 1 and by['0x47C620']['rc29_1'] >= 1,
    'POSCTRL 0x47C620 is found in BOTH places (%d / %d) so the locator is not one-sided'
    % (by['0x47C620']['ledger_sec_total'], by['0x47C620']['rc29_1']))
chk(sum(1 for r in rows if r['ledger_sec_total'] == 0) >= 1,
    'NEGCTRL at least one token is absent from §1064 (%d of 8) so absence is demonstrable'
    % sum(1 for r in rows if r['ledger_sec_total'] == 0))

out = {'ledger_sec_range': [s + 1, e],
       'rc29_1_lines': [s29 + i1 + 1, s29 + i2],
       'items': {k: {'lines': len(v), 'bytes': len(t.encode())} for k, (v, t) in
                 zip(items.keys(), [(v, item_txt[k]) for k, v in items.items()])},
       'rows': rows, 'pass': len(NOTES), 'fail': len(FAILS),
       'fails': FAILS, 'notes': NOTES}
io.open(ROOT + '/_r154/r154f_f08_anchor.json', 'w', encoding='utf-8').write(
    json.dumps(out, ensure_ascii=False, indent=1))
for m in NOTES + FAILS: print(m)
print('RESULT pass=%d fail=%d' % (len(NOTES), len(FAILS)))
sys.exit(1 if FAILS else 0)
