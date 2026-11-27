#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R153 A（v2）：FACT_INDEX 甲类 5 目录的「台账同名节」核验，**节级 vs 事项级**分开测。

上一版（v1）的错：从 anchor 里取内容 token。实测 17 个甲类条目里 15 个锚点形如「事项N」，
本身**不含任何内容 token** ⇒ v1 得出「item 级全命中 = 17/17」是分母为空导致的假命中（S-3xx 同族）。
本版改法：token 取自 **statement**（R149 §1204 一 的原话就是「逐 fid 锚点取自 statement 自身地址与数字」），
并对每一条分别判两级：
  - 节级：token 是否出现在台账同名节（§10NN）内任意位置；
  - 事项级：token 是否出现在该节 **被点名的那一个事项块**内。

事项块定位（三种盘上形态，必须分开处理）：
  - §1063 / §1064：`### 事项 N · …` 显式编号；
  - §1062 / §1065：`### 1. …` / `### 2. …` 裸数字编号（需按编号取，不是按出现顺序猜）；
  - §1066：无任何子项标题。
锚点里的「事项N」按上述形态解析；解析不出即判 **unlocatable**，不算命中、也不算未命中，单独计。
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
led_lines = led.split('\n')
secs = []
for i, l in enumerate(led_lines):
    m = re.match(r'^## §(\d+)', l)
    if m:
        secs.append((i, m.group(1)))
SEC = {}
for k, (i, num) in enumerate(secs):
    end = secs[k + 1][0] if k + 1 < len(secs) else len(led_lines)
    SEC[num] = {'start': i, 'end': end, 'body': '\n'.join(led_lines[i:end]),
                'lines': led_lines[i:end]}

ck('台账 CR = 337', led_raw.count(b'\r') == 337, led_raw.count(b'\r'))
ck('台账节数 665', len(secs) == 665, len(secs))

# ---------- 子项块解析 ----------
def items_of(num):
    """返回 [(label_int, text)]，label 取「事项 N」或「### N.」的 N。"""
    out = []
    body = SEC[num]['lines']
    cur, buf = None, []
    for l in body:
        m1 = re.match(r'^###\s*事项\s*(\d+)', l)
        m2 = re.match(r'^###\s*(\d+)\.', l)
        if m1 or m2:
            if cur is not None:
                out.append((cur, '\n'.join(buf)))
            cur = int((m1 or m2).group(1))
            buf = [l]
        elif cur is not None:
            buf.append(l)
    if cur is not None:
        out.append((cur, '\n'.join(buf)))
    return out


ITEMS = {n: items_of(n) for n in ('1062', '1063', '1064', '1065', '1066')}
print('\n[台账 5 节子项块形态]')
for n in ('1062', '1063', '1064', '1065', '1066'):
    labels = [x[0] for x in ITEMS[n]]
    style = ('事项N' if '### 事项' in SEC[n]['body'] else
             ('数字N.' if labels else '无子项'))
    print('  §%s 形态=%-6s 子项数=%d 编号=%s' % (n, style, len(ITEMS[n]), labels))

# ---------- FACT_INDEX ----------
fraw = open(F541, 'rb').read()
rows = [l.split('\t') for l in fraw.decode('utf-8').split('\n') if l.strip()]
hdr, data = rows[0], rows[1:]
ck('v5.41 数据行 54', len(data) == 54, len(data))
print('v5.41 bytes=%d sha256=%s' % (len(fraw), hashlib.sha256(fraw).hexdigest()))
BYID = {r[0]: r for r in data}


def split_item(item):
    item = item.strip()
    i = item.find('(')
    if i < 0 or not item.endswith(')'):
        return item, None
    return item[:i], item[i + 1:-1]


def derive_section(path):
    m = re.search(r'R17_LEDGER_(\d+)', path)
    if not m:
        return None
    n = m.group(1)
    return '1063' if n == '1063R' else n


STOK = re.compile(r'`([^`]+)`|(0x[0-9A-Fa-f]{4,})')


def stmt_tokens(stmt):
    """从 statement 取内容 token：反引号串（>=4 字符）与 0x 地址。去重保序。"""
    out, seen = [], set()
    for m in STOK.finditer(stmt):
        t = (m.group(1) if m.group(1) is not None else m.group(2)).strip()
        if len(t) < 4:
            continue
        if t in seen:
            continue
        seen.add(t)
        out.append(t)
    return out


print('\n[甲类逐项：节级 vs 事项级]')
recs = []
for r in data:
    fid, stmt, ev = r[0], r[1], r[3]
    for item in ev.split(';'):
        item = item.strip()
        if 'R17_LEDGER_10' not in item:
            continue
        path, anchor = split_item(item)
        if 'R17_LEDGER_10' not in path:
            continue
        sec = derive_section(path)
        toks = stmt_tokens(stmt)
        body = SEC[sec]['body'] if sec in SEC else ''
        sec_hit = [t for t in toks if t in body]
        want = None
        if anchor:
            m = re.match(r'^事项\s*(\d+)', anchor.strip())
            if m:
                want = int(m.group(1))
        blk, item_status = None, ('no-anchor' if not anchor else 'unlocatable')
        if want is not None:
            for lab, txt in ITEMS.get(sec, []):
                if lab == want:
                    blk, item_status = txt, 'located'
                    break
        item_hit = [t for t in toks if blk is not None and t in blk]
        recs.append({'fid': fid, 'sec': sec, 'anchor': anchor, 'want': want,
                     'item_status': item_status, 'toks': toks,
                     'sec_hit': sec_hit, 'item_hit': item_hit})

print('  甲类条目 %d ；fid %d' % (len(recs), len(set(x['fid'] for x in recs))))
for x in recs:
    print('  %-4s §%-5s %-18s %-11s token=%-3d 节级命中=%-3d 事项级命中=%-3d'
          % (x['fid'], x['sec'], str(x['anchor'])[:18], x['item_status'],
             len(x['toks']), len(x['sec_hit']), len(x['item_hit'])))

n_located = sum(1 for x in recs if x['item_status'] == 'located')
n_sec_any = sum(1 for x in recs if x['sec_hit'])
n_item_any = sum(1 for x in recs if x['item_hit'])
sec_only = [x for x in recs if x['sec_hit'] and not x['item_hit']]
print('\n  可定位事项块 = %d / %d' % (n_located, len(recs)))
print('  节级有命中 = %d' % n_sec_any)
print('  事项级有命中 = %d' % n_item_any)
print('  节级命中但事项级 0 命中 = %d  %s'
      % (len(sec_only), [(x['fid'], '§' + x['sec'], x['anchor']) for x in sec_only]))

print('\n[fid 级（R149 §1204 一的「12 个 fid」口径）]')
fids = sorted(set(x['fid'] for x in recs))
fid_sec = [f for f in fids if any(x['sec_hit'] for x in recs if x['fid'] == f)]
fid_item = [f for f in fids if any(x['item_hit'] for x in recs if x['fid'] == f)]
fid_seconly = [f for f in fids if f in fid_sec and f not in fid_item]
print('  fid 级节级有命中 = %d / %d' % (len(fid_sec), len(fids)))
print('  fid 级事项级有命中 = %d / %d' % (len(fid_item), len(fids)))
print('  只有节级命中（事项级无一项命中）= %d %s' % (len(fid_seconly), fid_seconly))
ck('§1204 的「12 个 fid 全部命中」在**节级**成立', len(fid_sec) == 12, len(fid_sec))

# ---------- 正反控 ----------
print('\n[正反控]')
ck('反控：自造串 ZZZ_R153_NOT_IN_LEDGER_QQQ 在台账 0 命中',
   'ZZZ_R153_NOT_IN_LEDGER_QQQ' not in led)
f04 = [x for x in recs if x['fid'] == 'F04'][0]
ck('正控：F04 → §1062 事项1 可定位（该节是「### 1.」数字形态）',
   f04['item_status'] == 'located' and f04['want'] == 1, (f04['item_status'], f04['want']))
ck('正控：F04 token 非空（从 statement 取到内容 token）', len(f04['toks']) > 0, len(f04['toks']))
f08 = [x for x in recs if x['fid'] == 'F08'][0]
ck('F08 → §1064 事项4：节级有命中、事项级 0 命中（就是 R149 §1204 六 登记的那条）',
   bool(f08['sec_hit']) and not f08['item_hit'],
   (len(f08['sec_hit']), len(f08['item_hit'])))
f15a = [x for x in recs if x['fid'] == 'F15' and x['sec'] == '1063' and x['anchor']]
ck('正控：F15 → §1063 事项4 可定位', f15a and f15a[0]['item_status'] == 'located',
   f15a[0]['item_status'] if f15a else None)
# 可失败性：把 F04 一个 token 末位改掉，节级必须变未命中
t0 = f04['toks'][0]
mut = t0[:-1] + ('0' if t0[-1] != '0' else '1')
ck('反控：F04 token 末位改一位后节级不再命中（判据可失败）',
   mut not in SEC['1062']['body'], mut)
# 事项块确实被切开：§1064 事项4 里不得含事项3 的 token
i3 = dict(ITEMS['1064'])[3]
i4 = dict(ITEMS['1064'])[4]
ck('反控：§1064 事项3 与事项4 的块文本不相等且事项4 不含「A3」「M1」',
   i3 != i4 and ('A3' not in i4) and ('M1' not in i4))
ck('解析：1063R 落到 §1063', derive_section('lead\\x\\R17_LEDGER_1063R\\SECTION.md') == '1063')
ck('解析：嵌套括号锚点不被剥坏',
   split_item('lead\\x.md(§2.10 / 一 / (a′))')[1] == '§2.10 / 一 / (a′)')

print('\nFAIL %d：%s' % (len(fails), fails))
sys.exit(1 if fails else 0)
