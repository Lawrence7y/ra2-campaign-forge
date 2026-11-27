#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R153 B：R149 §1204 一「12 个 fid、33 个锚点全部逐字命中」这条判据的**鉴别力**实测。

要回答的是：一句「token 在台账同名节内出现」能证明什么？
  若一个 token 在台账 665 节里有几百节都出现，那它在这节出现**不构成**证据 —— 这是
  「承载 ≠ 独立证据」（R151 OI5）在**锚点判据**上的同一类错误。

做法（全机械）：
  1) token 分三类：STRICT（反引号串 ≥4 字符 / 0x 地址）、NUM（>=3 位数字，含千分位形态）、WEAK（其余）。
  2) 对每个 token 统计它在台账 **多少节**里出现（节级计数，不是行级）。
  3) 定义鉴别力档：出现在 <=1% 节 = 强；1%~10% = 中；>10% = 无鉴别力。
  4) 同时复核 R149 的「33 个锚点」这个数字是怎么数出来的（按事项号展开 vs 按条目数）。
反控：
  - 正控：0x47C3D0 这类稀有地址应落「强」档，且确实出现在 §1064 内；
  - 反控：注入一个不存在的 token 必须 0 节命中。
"""
import hashlib
import os
import re
import sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
D = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
LED = os.path.join(ROOT, 'lead', 'GOAL_THREE_TARGETS_20261018.md')
F541 = os.path.join(D, 'R17_R113_FACTINDEX_V541', 'FACT_INDEX.tsv')

fails = []


def ck(n, c, d=''):
    ok = bool(c)
    print(('  PASS ' if ok else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not ok:
        fails.append(n)
    return ok


led_raw = open(LED, 'rb').read()
led = led_raw.decode('utf-8')
lines = led.split('\n')
secs = []
for i, l in enumerate(lines):
    m = re.match(r'^## §(\d+)', l)
    if m:
        secs.append((i, m.group(1)))
SECBODY = {}
for k, (i, num) in enumerate(secs):
    end = secs[k + 1][0] if k + 1 < len(secs) else len(lines)
    SECBODY[num] = '\n'.join(lines[i:end])
ck('台账节数 665', len(secs) == 665, len(secs))

rows = [l.split('\t') for l in open(F541, encoding='utf-8').read().split('\n') if l.strip()]
data = rows[1:]
BYID = {r[0]: r for r in data}

LEDREF = re.compile(r'R17_LEDGER_(\d+)')


def split_item(item):
    item = item.strip()
    i = item.find('(')
    if i < 0 or not item.endswith(')'):
        return item, None
    return item[:i], item[i + 1:-1]


STRICT = re.compile(r'`([^`]+)`|(0x[0-9A-Fa-f]{4,})')
NUMPAT = re.compile(r'(?<![0-9A-Za-z_.])(\d{1,3}(?:,\d{3}){1,}|\d{3,})(?![0-9A-Za-z_])')


def toks_of(stmt):
    """返回 [(tok, kind)]；STRICT 优先，NUM 只在同一位置未取到时补。"""
    out, seen = [], set()
    for m in STRICT.finditer(stmt):
        t = (m.group(1) if m.group(1) is not None else m.group(2)).strip()
        if len(t) < 4 or t in seen:
            continue
        seen.add(t)
        out.append((t, 'STRICT'))
    for m in NUMPAT.finditer(stmt):
        t = m.group(1)
        if t in seen:
            continue
        # 纯序号噪声：单段 <=2 字符已排除；在此仍保留，便于看鉴别力实况
        seen.add(t)
        out.append((t, 'NUM'))
    return out


def spread(tok):
    """token 出现在多少节。"""
    return sum(1 for n, b in SECBODY.items() if tok in b)


# ---------- 甲类条目清单 ----------
items = []
for r in data:
    fid, stmt, ev = r[0], r[1], r[3]
    for it in ev.split(';'):
        it = it.strip()
        if not it or 'R17_LEDGER_10' not in it:
            continue
        path, anchor = split_item(it)
        if 'R17_LEDGER_10' not in path:
            continue
        m = LEDREF.search(path)
        sec = '1063' if m.group(1) == '1063R' else m.group(1)
        items.append({'fid': fid, 'sec': sec, 'anchor': anchor, 'stmt': stmt})

print('\n甲类条目 %d ；唯一 fid %d' % (len(items), len(set(x['fid'] for x in items))))
anchor_nums = []
for x in items:
    if x['anchor']:
        anchor_nums.extend(int(n) for n in re.findall(r'\d+', x['anchor']))
print('R149 口径复核：条目数 = %d ；锚点内事项号展开后个数 = %d'
      % (len(items), len(anchor_nums)))
ck('R149 的「33 个锚点」= 事项号展开口径', len(anchor_nums) == 33, len(anchor_nums))

# ---------- token 鉴别力 ----------
print('\n[token 鉴别力普查]')
allt = {}
for x in items:
    for t, k in toks_of(x['stmt']):
        allt.setdefault((t, k), set()).add(x['sec'])
seen_pairs = set()
recs = []
for (t, k), secset in sorted(allt.items()):
    if (t, k) in seen_pairs:
        continue
    seen_pairs.add((t, k))
    sp = spread(t)
    n_sec = len(SECBODY)
    band = 'STRONG(<=1%)' if sp <= n_sec * 0.01 else ('MID(1-10%)' if sp <= n_sec * 0.10 else 'NONE(>10%)')
    recs.append({'tok': t, 'kind': k, 'spread': sp, 'band': band, 'secs': secset})

print('  token 唯一数 = %d' % len(recs))
from collections import Counter
print('  按类：', Counter(r['kind'] for r in recs))
print('  按鉴别力档：', Counter(r['band'] for r in recs))
print('\n  %-26s %-7s %6s %6s  %s' % ('token', 'kind', '节数', '占比', '档'))
for r in sorted(recs, key=lambda z: z['spread']):
    print('  %-26s %-7s %6d %5.1f%%  %s'
          % (r['tok'][:26], r['kind'], r['spread'], 100.0 * r['spread'] / len(SECBODY), r['band']))

n_none = sum(1 for r in recs if r['band'].startswith('NONE'))
n_mid = sum(1 for r in recs if r['band'].startswith('MID'))
n_str = sum(1 for r in recs if r['band'].startswith('STRONG'))
print('\n  强鉴别力 %d ；中 %d ；无鉴别力 %d' % (n_str, n_mid, n_none))

# 只看 STRICT
strict = [r for r in recs if r['kind'] == 'STRICT']
print('  STRICT 子集 %d 个：强 %d / 中 %d / 无 %d'
      % (len(strict), sum(1 for r in strict if r['band'].startswith('STRONG')),
         sum(1 for r in strict if r['band'].startswith('MID')),
         sum(1 for r in strict if r['band'].startswith('NONE'))))

# ---------- F08 专项：事项4 到底载了什么 ----------
print('\n[F08 专项：statement token 在 §1064 事项 4 块内的命中]')
f08 = BYID['F08']
i64 = [i for i, l in enumerate(lines) if l.startswith('## §1064')][0]
i65 = [i for i, l in enumerate(lines) if l.startswith('## §1065')][0]
body = lines[i64:i65]
idx4 = [j for j, l in enumerate(body) if l.startswith('### 事项 4')][0]
idx5 = [j for j, l in enumerate(body) if l.startswith('### 事项 5')][0]
blk4 = '\n'.join(body[idx4:idx5])
blk3 = '\n'.join(body[[j for j, l in enumerate(body) if l.startswith('### 事项 3')][0]:idx4])
t8 = toks_of(f08[1])
print('  F08 statement token 数 = %d' % len(t8))
in4 = [t for t, k in t8 if t in blk4]
out4 = [t for t, k in t8 if t not in blk4]
in3 = [t for t, k in t8 if t in blk3]
print('  在事项4 命中 = %d %s' % (len(in4), in4))
print('  在事项3 命中 = %d %s' % (len(in3), in3))
print('  事项4 未命中 = %d %s' % (len(out4), out4))
ck('F08 的 a–e 细目 token 在事项4 内不全（缺口 >=3 个）', len(out4) >= 3, len(out4))
ck('F08 的 a–e 细目 token 在事务3 内有命中（说明内容在邻项，不在被引项）',
   len(in3) >= 1, len(in3))

# ---------- 正反控 ----------
print('\n[正反控]')
ck('正控：稀有地址 0x47C3D0 落 STRONG 档', any(r['tok'] == '0x47C3D0' and r['band'].startswith('STRONG')
                                              for r in recs))
ck('正控：0x47C3D0 出现在 §1064 内', '0x47C3D0' in SECBODY['1064'])
ck('反控：自造 token 0xDEADBEEFZZ 0 节命中', spread('0xDEADBEEFZZ') == 0)
ck('反控：常见数字 354 的节数 > 10% 节（无鉴别力判据可失败）',
   spread('354') > len(SECBODY) * 0.10, spread('354'))

print('\nFAIL %d：%s' % (len(fails), fails))
sys.exit(1 if fails else 0)
