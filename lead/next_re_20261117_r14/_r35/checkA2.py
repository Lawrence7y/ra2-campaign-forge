# -*- coding: utf-8 -*-
"""Round 35 · Check A (v2): 逐条列出 limitations 中非 § 引用的所在句 + 本行 evidence_paths，
供人工判读「支撑声称 vs 引用义务」。同时机械判定 M 项所属卡是否在本行锚内。"""
import io, os, re, json, collections

ROOT = r'D:\Project\ra2-campaign-forge'
R14  = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
FI   = os.path.join(R14, 'R17_R65_FACTINDEX_V510', 'FACT_INDEX.tsv')
OUT  = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'checkA_report.md')

raw = io.open(FI, encoding='utf-8').read()
lines = raw.split('\n')
header = lines[0].split('\t')
rows = []
for l in lines[1:]:
    if not l.strip():
        continue
    c = l.split('\t')
    rows.append(dict(zip(header, c)))

fact_ids = set(r['fact_id'] for r in rows)

# M 项 → 卡（含 LEAD_LOCK）
panel_m = collections.defaultdict(set)
for name in sorted(os.listdir(R14)):
    p = os.path.join(R14, name)
    if not os.path.isdir(p):
        continue
    for dirpath, _, filenames in os.walk(p):
        for fn in filenames:
            if fn == 'PANEL.md':
                txt = io.open(os.path.join(dirpath, fn), encoding='utf-8', errors='replace').read()
                for m in re.finditer(r'(?<![\w])M(\d{1,3})(?![\d])', txt):
                    panel_m['M' + m.group(1)].add(os.path.basename(dirpath))
ll = io.open(os.path.join(ROOT, 'lead', 'LEAD_LOCK'), encoding='utf-8').read()
for m in re.finditer(r'(?<![\w])M(\d{1,3})(?![\d])', ll):
    panel_m['M' + m.group(1)].add('LEAD_LOCK')

CARD_RE  = re.compile(r'(?<![\w])(?:R1[4-7]_[A-Za-z0-9_]+|NAMED_PUSH_AUDIT\d{1,2}|NAMED_PUSH_S\d\w*)')
MITEM_RE = re.compile(r'(?<![\w])M(\d{1,3})(?![\d])')
FACT_RE  = re.compile(r'(?<![\w])F(\d{2})(?![\d])')

buf = []
buf.append('# Round 35 · Check A 明细：limitations 中非 § 引用\n')

tot = collections.Counter()
for r in rows:
    lim, ev, fid = r['limitations'], r['evidence_paths'], r['fact_id']
    cards = sorted(set(CARD_RE.findall(lim)))
    mitems = sorted(set('M' + x for x in MITEM_RE.findall(lim)))
    facts  = sorted(set('F' + x for x in FACT_RE.findall(lim)))
    if not (cards or mitems or facts):
        continue
    tot['facts_with_nonSec'] += 1
    buf.append('## %s [%s]' % (fid, r['grade']))
    buf.append('')
    buf.append('- limitations 原文：%s' % lim)
    buf.append('- evidence_paths：%s' % ev)
    if cards:
        for c in cards:
            incard = c.upper() in ev.upper()
            ok_dir = os.path.isdir(os.path.join(R14, c))
            buf.append('  - CARD `%s` : 目录存在=%s / 在本行 evidence_paths=%s' % (c, ok_dir, incard))
    if mitems:
        for mi in mitems:
            owners = sorted(panel_m.get(mi, []))
            inanchor = [o for o in owners if o.upper() in ev.upper()]
            buf.append('  - MITEM `%s` : 出现于卡=%s / 其中在本行锚内=%s' % (
                mi, ','.join(owners) or 'NONE', ','.join(inanchor) or 'NONE'))
    if facts:
        for f in facts:
            buf.append('  - FACT `%s` : 存在于索引=%s' % (f, f in fact_ids))
    buf.append('')

buf.insert(1, '共 %d 行 limitations 含非 § 引用。\n' % tot['facts_with_nonSec'])
io.open(OUT, 'w', encoding='utf-8').write('\n'.join(buf))
print('wrote', OUT, 'rows_with_nonsec=', tot['facts_with_nonSec'])
