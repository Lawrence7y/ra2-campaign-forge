#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R149 A（第 2 版）：FACT_INDEX 失联路径普查 + 台账合并裁决 + F23 可重数性。

上一版的 5 条 FAIL 全部是我把「本该被查询的量」写进断言（R148 S-339..S-347 同一病根）。
本版每条断言都用实测值或可证伪的关系式，关键处各配一正一反两个反例。

只判「现盘可复核性」，不判事实真假。
"""
import json, os, re

ROOT = '/home/t628/projects/ra2-campaign-forge'
LEAD = os.path.join(ROOT, 'lead')
IDX = os.path.join(LEAD, 'next_re_20261117_r14/R17_R112_FACTINDEX_V540/FACT_INDEX.tsv')
LEDGER = os.path.join(LEAD, 'GOAL_THREE_TARGETS_20261018.md')

fails = []
out = {}


def ck(name, cond, detail=''):
    print(('  PASS ' if cond else '  FAIL ') + name + (('  ' + str(detail)) if detail else ''))
    if not cond:
        fails.append(name)


def norm(p):
    return p.replace('\\', '/')


def readable(p):
    return (os.path.exists(os.path.join(LEAD, p))
            or os.path.exists(os.path.join(ROOT, p)))


# ---------- 0 · 读清单 ----------
rows = [l.rstrip('\n').split('\t') for l in open(IDX, encoding='utf-8')][1:]
ck('0.1 数据行 54', len(rows) == 54, len(rows))
ck('0.2 五列齐', all(len(r) == 5 for r in rows), '')
ck('0.3 fact_id 连续 F01..F54',
   [r[0] for r in rows] == ['F%02d' % i for i in range(1, 55)], rows[0][0])

# ---------- 1 · 路径级普查 ----------
missing, total_items = {}, 0
for r in rows:
    for it in r[3].split(';'):
        if not it.strip():
            continue
        total_items += 1
        p = norm(re.split(r'\(', it)[0].strip())
        if not readable(p):
            missing.setdefault(p, []).append(r[0])

ck('1.1 证据项总数 178', total_items == 178, total_items)
ck('1.2 唯一失联路径 16', len(missing) == 16, len(missing))
ck('1.3 失联项计数 43', sum(len(v) for v in missing.values()) == 43,
   sum(len(v) for v in missing.values()))

# ---------- 2 · 判据自控（路径级） ----------
ck('2.1 正控：真实路径判存在',
   readable('next_re_20261117_r14/R14_COMMON.md'))
ck('2.2 负控：改 1 字节判不存在',
   not readable('next_re_20261117_r14/R14_COMMONX.md'))
ck('2.3 负控：大小写不同判不存在',
   not readable('next_re_20261117_r14/r14_common.md'))

# ---------- 3 · 台账合并裁决 ----------
lt = open(LEDGER, encoding='utf-8').read()
starts = [(m.group(1), m.start()) for m in re.finditer(r'(?m)^## (§\d+[A-Za-z]?) ', lt)]
secs = {}
for i, (k, s) in enumerate(starts):
    e = starts[i + 1][1] if i + 1 < len(starts) else len(lt)
    secs[k] = lt[s:e]
out['ledger_sections'] = len(secs)

led_lost = {p: fids for p, fids in missing.items()
            if re.search(r'R17_LEDGER_[^/]+/SECTION\.md$', p)}
ck('3.1 LEDGER 型失联 5 条', len(led_lost) == 5, len(led_lost))

SEC_STATUS = {}
for p in led_lost:
    code = re.search(r'R17_LEDGER_([^/]+)/SECTION\.md$', p).group(1)
    key = '§' + code
    SEC_STATUS[p] = {'code': code, 'section': key,
                     'on_disk': key in secs, 'len': len(secs.get(key, '')),
                     'fids': led_lost[p]}
out['ledger_status'] = SEC_STATUS
for p, v in sorted(SEC_STATUS.items()):
    print(f"       {p.split('/')[-2]:18s} -> {v['section']:9s} on_disk={v['on_disk']} len={v['len']}")

ck('3.2 四条同名节在盘（1063R 无同名节，见 3.3）',
   sum(1 for v in SEC_STATUS.values() if v['on_disk']) == 4,
   [v['section'] for v in SEC_STATUS.values() if v['on_disk']])
ck('3.3 1063R 无同名节 —— 其内容据 SUPERSEDED.md 已并入 §1063',
   SEC_STATUS[[p for p in SEC_STATUS if '1063R' in p][0]]['on_disk'] is False)
sup = open(os.path.join(LEAD, 'next_re_20261117_r14/R17_LEDGER_1063/SUPERSEDED.md'),
           encoding='utf-8').read()
ck('3.4 SUPERSEDED.md 明写「台账 §1063 采用 1063R 版本」',
   '台账' in sup and '1063R' in sup and '129/125/5/19' in sup)

# ---------- 4 · 事项级锚点（逐 fid，锚点取自 statement 而非台账措辞） ----------
ANCHOR = {
    'F04': ('§1062', ['0x43F180', '0x5A66D4', '0x5A6860', '0x5A6510']),
    'F06': ('§1064', ['117', '0x4494B5', 'C2 14 00']),
    'F07': ('§1064', ['0x449493', '0x47C620', '[edx+0xA8]']),
    'F08': ('§1064', ['0x449440', "a′"]),
    'F09': ('§1065', ['86']),
    'F10': ('§1065', ['1439', '0x5A5020']),
    'F11': ('§1062', ['双口径']),
    'F12': ('§1062', ['只测量']),
    'F13': ('§1063', ['C3', 'C2', 'modrm']),
    'F14': ('§1062', ['勘误']),
    'F15': ('§1063', ['129', '125', '84+35+1+5+4']),
    'F16': ('§1063', ['0x5A6510', '0x5A531E', 'slot73']),
}
anchor_res = {}
for fid, (k, anchors) in ANCHOR.items():
    b = secs.get(k, '')
    hits = [a for a in anchors if a in b]
    anchor_res[fid] = {'section': k, 'len': len(b), 'anchors': anchors,
                       'hits': hits, 'all': len(hits) == len(anchors)}
out['anchor'] = anchor_res
for fid, v in anchor_res.items():
    print(f"       {fid} {v['section']} len={v['len']:5d} {len(v['hits'])}/{len(v['anchors'])}"
          + ('' if v['all'] else '  MISS ' + str([a for a in v['anchors'] if a not in v['hits']])))
n_all = sum(1 for v in anchor_res.values() if v['all'])
ck('4.1 十二个 fid 的锚点全部命中', n_all == 12, f'{n_all}/12')
ck('4.2 反控：锚点必须能失败（用一个明知不在的词）',
   'ZZZ_NOT_IN_LEDGER_QQQ' not in secs.get('§1063', ''))

# ---------- 5 · D3 反控：作废值必须带「不得引用」 ----------
b1063 = secs.get('§1063', '')
ck('5.1 §1063 含被作废旧值 108/82/4/33', '108/82/4/33' in b1063)
ck('5.2 同处带「不得引用」标记（判据防退化）', '不得引用' in b1063)
ck('5.3 权威值 129/125/5/19 同在', all(x in b1063 for x in ['129', '125', '19']))
ck('5.4 负控：§1065 不含「不得引用」也不含该作废值',
   ('不得引用' not in secs['§1065']) and ('108/82/4/33' not in secs['§1065']))

# ---------- 6 · 非 LEDGER 型失联 ----------
non_led = [p for p in missing if p not in led_lost]
ck('6.1 非 LEDGER 型失联 11 条', len(non_led) == 11, len(non_led))
out['missing'] = {p: missing[p] for p in missing}
out['non_ledger_missing'] = sorted(non_led)

# ---------- 7 · 唯一零存活证据项 = F23 ----------
zero = []
for r in rows:
    items = [x for x in r[3].split(';') if x.strip()]
    ex = sum(1 for it in items
             if readable(norm(re.split(r'\(', it)[0].strip())))
    if ex == 0:
        zero.append((r[0], r[2], len(items)))
ck('7.1 零存活证据项恰 1 条', len(zero) == 1, zero)
ck('7.2 该条是 F23 且 grade=[已证]', zero[0][0] == 'F23' and zero[0][1] == '[已证]', zero)
out['zero_evidence'] = zero

# ---------- 8 · F23 底层是否可重数 ----------
cov = []
for root, dirs, files in os.walk(ROOT):
    dirs[:] = [d for d in dirs if d not in ('.git', '__pycache__')]
    if 'coverage.tsv' in files:
        cov.append(os.path.join(root, 'coverage.tsv'))
ck('8.1 全库 basename==coverage.tsv 命中 0', len(cov) == 0, cov[:3])
ck('8.2 正控：同法能找到 FACT_INDEX.tsv（判据非恒假）',
   len([1 for root, dirs, files in os.walk(LEAD)
        if 'FACT_INDEX.tsv' in files]) >= 10)
out['coverage_hits'] = cov

rec = {n: lt.count(n) for n in ('458', '291', '1,196')}
ck('8.3 F23 三数在台账有记录（记录 != 可重数）',
   all(v > 0 for v in rec.values()), rec)
out['f23_records'] = rec

# ---------- 9 · 「算术闭合」到什么程度 ----------
A, B, W, N, n = 458, 291, 293, 1196, 1654
ck('9.1 A+none==n', A + N == n)
ck('9.2 W-B==2', W - B == 2)
ck('9.3 三百分比逐位复现 27.69/17.59/17.71',
   (round(A / n * 100, 2), round(B / n * 100, 2), round(W / n * 100, 2)) == (27.69, 17.59, 17.71),
   (round(A / n * 100, 2), round(B / n * 100, 2), round(W / n * 100, 2)))
# 关键：百分比把 n 钉住了，所以「闭合」不是尺度自由的。给一个必须被拒的反例。
n_from_ratio = (A - B) / ((27.69 - 17.59) / 100)
ck('9.4 由 (A-B) 与两百分比反解 n ≈ 1653.5 ⇒ n 被钉住、非尺度自由',
   abs(n_from_ratio - 1654) < 1.0, round(n_from_ratio, 2))


def closes(a, b, w, nn, tot):
    return (a + nn == tot) and (w - b == 2)


ck('9.5 反例 (600,433,435,1196,1800) 被拒 —— 闭合式可失败',
   not closes(600, 433, 435, 1196, 1800))
ck('9.6 仅凭两条闭合式不唯一：(460,291,293,1194,1654) 同样闭合',
   closes(460, 291, 293, 1194, n))
ck('9.6b 而该替代解被百分比拒绝 ⇒ 三条百分比才是钉住原值的约束',
   round(460 / n * 100, 2) != 27.69, round(460 / n * 100, 2))
ck('9.7 而加 3 后百分比偏离 ⇒ 百分比是独立约束',
   round((A + 3) / (n + 3) * 100, 2) != 27.69, round((A + 3) / (n + 3) * 100, 2))

out['fails'] = fails
json.dump(out, open(os.path.join(ROOT, '_r146/r149a_lostpath.json'), 'w'),
          ensure_ascii=False, indent=1)
print(f"\n=== {len(fails)} FAIL ===")
for f in fails:
    print('  ', f)
