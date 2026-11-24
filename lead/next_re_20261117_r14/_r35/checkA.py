# -*- coding: utf-8 -*-
"""Round 35 · Check A: limitations 列中非 § 形式引用的可解析性与锚内性。

口径（沿用 §2.20/round-34 两步法与 §2.21 纪律 9）：
  步骤1  可解析：被引对象在磁盘上真实存在（fact_id / M 项 / 卡目录 / 裸文件）
  步骤2  锚内性：若该句声称「X 支撑本行某事」（support 动词），则 X 必须落在本行 evidence_paths 里；
                 若该句只是「引用义务」（须同引/同看/必须与…同引），则不要求在锚内。
"""
import io, os, re, sys, json, collections

ROOT = r'D:\Project\ra2-campaign-forge'
R14  = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
FI   = os.path.join(R14, 'R17_R65_FACTINDEX_V510', 'FACT_INDEX.tsv')

raw = io.open(FI, encoding='utf-8').read()
lines = [l for l in raw.split('\n')]
header = lines[0].split('\t')
rows = []
for l in lines[1:]:
    if not l.strip():
        continue
    c = l.split('\t')
    assert len(c) == 5, (len(c), c[0])
    rows.append(dict(zip(header, c)))
print('rows =', len(rows))

# ---------- 索引：可解析对象池 ----------
fact_ids = set(r['fact_id'] for r in rows)

card_dirs = {}
for name in os.listdir(R14):
    p = os.path.join(R14, name)
    if os.path.isdir(p):
        card_dirs[name.upper()] = p
print('card dirs =', len(card_dirs))

# 找所有 PANEL.md，建 M 项 → 卡目录 映射
panel_m = collections.defaultdict(list)   # M key -> [card names]
panel_files = []
for name in os.listdir(R14):
    p = os.path.join(R14, name)
    if not os.path.isdir(p):
        continue
    for dirpath, _, filenames in os.walk(p):
        for fn in filenames:
            if fn == 'PANEL.md':
                panel_files.append(os.path.join(dirpath, fn))
print('PANEL.md files =', len(panel_files))
for pf in panel_files:
    txt = io.open(pf, encoding='utf-8', errors='replace').read()
    for m in re.finditer(r'(?<![\w])M(\d{1,3})(?![\d])', txt):
        card = os.path.basename(os.path.dirname(pf))
        panel_m['M' + m.group(1)].append(card)

# LEAD_LOCK 也含 M 项
ll = io.open(os.path.join(ROOT, 'lead', 'LEAD_LOCK'), encoding='utf-8').read()
for m in re.finditer(r'(?<![\w])M(\d{1,3})(?![\d])', ll):
    panel_m['M' + m.group(1)].append('LEAD_LOCK')

# ---------- 抽取 limitations 里的非 § 引用 ----------
PATTERNS = [
    ('FACT',   re.compile(r'(?<![\w])F(\d{2})(?![\d])')),
    ('MITEM',  re.compile(r'(?<![A-Za-z\w])M(\d{1,3})(?![\d])')),
    ('CARD',   re.compile(r'(?<![\w])((?:R17|R16|R15|R14|R1\d)_[A-Za-z0-9_]+|NAMED_PUSH_AUDIT\d+|NAMED_PUSH_S\d\w*)')),
    ('DECIDE', re.compile(r'(?<![\w])(D-\d+)(?![\d])')),
    ('CLS',    re.compile(r'(?<![\w])(C-\d+)(?![\d])')),
    ('BARE',   re.compile(r'(?<![\w/\\])([a-z][a-z0-9_]*\.(?:tsv|md|json|py))')),
]

out = []
for r in rows:
    lim = r['limitations']
    ev  = r['evidence_paths']
    evup = ev.upper()
    # 按句切分，保留上下文
    sents = re.split(r'[；;]', lim)
    for pat_name, pat in PATTERNS:
        for m in pat.finditer(lim):
            tok = m.group(1) if pat.groups else m.group(0)
            if pat_name == 'FACT':
                tok = 'F' + m.group(1)
            elif pat_name == 'MITEM':
                tok = 'M' + m.group(1)
            out.append(dict(fact=r['fact_id'], kind=pat_name, token=tok,
                            pos=m.start(), ev=ev))

# 去重（同一 fact 同一 token 只记一次）
seen = set(); uniq = []
for o in out:
    k = (o['fact'], o['kind'], o['token'])
    if k in seen:
        continue
    seen.add(k); uniq.append(o)
print('raw refs (unique per fact) =', len(uniq))

# ---------- 可解析性 ----------
for o in uniq:
    t = o['token']
    if o['kind'] == 'FACT':
        o['resolvable'] = t in fact_ids
        o['where'] = 'FACT_INDEX'
    elif o['kind'] == 'MITEM':
        o['resolvable'] = t in panel_m
        o['where'] = ','.join(sorted(set(panel_m.get(t, [])))) or '-'
    elif o['kind'] == 'CARD':
        o['resolvable'] = t.upper() in card_dirs
        o['where'] = card_dirs.get(t.upper(), '-')
        if o['resolvable']:
            o['where'] = os.path.basename(o['where'])
    elif o['kind'] in ('DECIDE', 'CLS'):
        # 在 R14_COMMON / 台账 / 看板全文里搜
        o['resolvable'] = None
        o['where'] = 'see-text-search'
    else:
        o['resolvable'] = None
        o['where'] = 'see-text-search'

print()
print('=== 不可解析 ===')
bad = [o for o in uniq if o['resolvable'] is False]
for o in bad:
    print('  %s  %-6s %-32s' % (o['fact'], o['kind'], o['token']))
print('  count =', len(bad))

print()
print('=== 可解析但需看锚内性（CARD / MITEM 声称支撑时）===')
for o in uniq:
    if o['resolvable'] and o['kind'] in ('CARD', 'MITEM'):
        inan = o['token'].upper() in o['ev'].upper() or (o['kind']=='MITEM' and o['token'].upper() in o['ev'].upper())
        print('  %s  %-6s %-34s in_anchor=%s' % (o['fact'], o['kind'], o['token'], inan))

json.dump(uniq, io.open(os.path.join(os.path.dirname(__file__), 'refsA.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print()
print('wrote refsA.json')
