#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R175 B：把「三个宽度两两差 2 B」这句被 r175a 测反的话，在全部落盘件里逐处定位（只读）。

判据（可失败）：r175a 已实测 值跨度 16,711,104 / 成员 16,711,116 / 算术差 16,711,118，
相邻差是 **12** 与 **2**，不是「2 与 2」。故任何写「两两差 2 B / 两两相差 2 B 与 2 B」的
文本都是**假句**，须逐处登记并逐个定性（是「整句假」还是「相邻差 12 那半句真」）。

反控：
  N1 正控串「恰为被剔的 bounds 段」必须在 F24 statement 命中 1 次（证明扫描器能命中真串）。
  N2 伪串「两两差 3 B」必须 0 命中（证明不是任意串都命中）。
  N3 同一文件里「12 B」与「2 B」各自单独出现很多次 ⇒ 只登记**同句内**同时含三种宽度的那句。
"""
import hashlib, io, json, os, re, sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
TIER = os.path.join(ROOT, 'lead/next_re_20261117_r14')
OUT = os.path.join(ROOT, '_r175/r175b_false2b_copies.json')
TARGETS = [
    ('FACT_INDEX_V556', os.path.join(TIER, 'R17_R128_FACTINDEX_V556/FACT_INDEX.tsv')),
    ('R14_COMMON', os.path.join(TIER, 'R14_COMMON.md')),
    ('STATUS_BOARD', os.path.join(TIER, 'STATUS_BOARD.md')),
    ('BOARD_ARCHIVE', os.path.join(TIER, 'BOARD_ARCHIVE.md')),
    ('LEDGER', os.path.join(ROOT, 'lead/GOAL_THREE_TARGETS_20261018.md')),
    ('LEAD_LOCK', os.path.join(ROOT, 'lead/LEAD_LOCK')),
    ('FACT_INDEX_CURRENT', os.path.join(TIER, 'FACT_INDEX_CURRENT.md')),
]
PATTERNS = {
    'two_by_two_2B': re.compile(r'两两(?:相差|差) ?\*{0,2}2 ?B'),
    'each_12B': re.compile(r'12 ?B'),
    'delta_118': re.compile(r'16,711,118'),
    'span_104': re.compile(r'16,711,104'),
    'member_116': re.compile(r'16,711,116'),
}
fails, n, res = [], 0, {}
def ck(name, cond, detail=''):
    global n
    n += 1
    print(('  PASS ' if cond else '  FAIL ') + name + (('  ' + str(detail)) if detail else ''))
    if not cond: fails.append(name)
    res[name] = {'pass': bool(cond), 'detail': str(detail)}

texts = {}
for tag, p in TARGETS:
    raw = io.open(p, 'rb').read()
    txt = raw.decode('utf-8', 'replace')
    texts[tag] = txt
    res.setdefault('files', {})[tag] = {'bytes': len(raw), 'sha16': hashlib.sha256(raw).hexdigest()[:16],
                                        'cr': raw.count(b'\r'), 'lf': raw.count(b'\n')}

# ---------- N1/N2 扫描器反控 ----------
hits = {}
for tag, txt in texts.items():
    for k, rx in PATTERNS.items():
        hits.setdefault(tag, {})[k] = [m.start() for m in rx.finditer(txt)]
ck('N1 正控：F24 statement 里「恰为被剔的 bounds 段」命中 1 次（扫描器可用）',
   texts['FACT_INDEX_V556'].count('恰为被剔的 `bounds` 段') == 1,
   texts['FACT_INDEX_V556'].count('恰为被剔的 `bounds` 段'))
ck('N2 反控：伪串「两两差 3 B」在全库 0 命中', sum(t.count('两两差 3 B') for t in texts.values()) == 0,
   sum(t.count('两两差 3 B') for t in texts.values()))

print('\n== 逐文件命中计数 ==')
for tag in [t for t, _ in TARGETS]:
    h = hits.get(tag, {})
    print('   %-18s bytes=%-9d 两两差2B=%d  16,711,118=%d  16,711,104=%d  16,711,116=%d' %
          (tag, res['files'][tag]['bytes'],
           len(h.get('two_by_two_2B', [])), len(h.get('delta_118', [])),
           len(h.get('span_104', [])), len(h.get('member_116', []))))

# ---------- 逐处上下文（假句必须带三种宽度同句） ----------
print('\n== 「两两差 2 B」逐处上下文 ==')
ctx = []
for tag, txt in texts.items():
    for off in hits.get(tag, {}).get('two_by_two_2B', []):
        s = txt[max(0, off-260):off+200].replace('\n', '\\n')
        ctx.append({'file': tag, 'off': off, 'ctx': s})
        print('   [%s @%d] ...%s...' % (tag, off, s))
res['two_by_two_contexts'] = ctx

# ---------- F24 单元格内定点 ----------
import csv
d = texts['FACT_INDEX_V556']
rows = list(csv.reader(io.StringIO(d), delimiter='\t'))
rec = {r[0]: r for r in rows[1:]}
st, lim = rec['F24'][1], rec['F24'][4]
in_st = [m.start() for m in PATTERNS['two_by_two_2B'].finditer(st)]
in_lim = [m.start() for m in PATTERNS['two_by_two_2B'].finditer(lim)]
res['f24_st_off'] = in_st
res['f24_lim_off'] = in_lim
ck('D1 F24 statement 内假句 0 处', len(in_st) == 0, in_st)
ck('D2 F24 limitations 内假句恰 2 处（cell 内偏移）', len(in_lim) == 2, in_lim)
# ★ 自错 S-627：原先把 label 写成条件表达式，label 里带「== 2」的应然数而断言用实测 —— 已改为纯 label + 实测值。
ck('D3 全库假句总数（F24 limitations 2 + R14_COMMON 1 + LEAD_LOCK 1）', len(ctx) == 4, len(ctx))
res['per_file_two_by_two'] = {tag: len(hits.get(tag, {}).get('two_by_two_2B', [])) for tag, _ in TARGETS}

out = {'fails': fails, 'n': n, 'res': res}
io.open(OUT, 'w', encoding='utf-8').write(json.dumps(out, ensure_ascii=False, indent=1))
print('\n== %d 断言, %d FAIL ==' % (n, len(fails)))
sys.exit(1 if fails else 0)
