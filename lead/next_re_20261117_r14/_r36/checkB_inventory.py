# -*- coding: utf-8 -*-
"""R36 Check B：statement 列里所有引用型 token 的清点（不判，只列）。
grade 列一并确认无可引对象。
"""
import io, os, re, json, collections

ROOT = r'D:\Project\ra2-campaign-forge'
R14  = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
FI   = os.path.join(R14, 'R17_R66_FACTINDEX_V511', 'FACT_INDEX.tsv')
OUT  = os.path.join(R14, '_r36', 'checkB_inventory.md')
os.makedirs(os.path.dirname(OUT), exist_ok=True)

raw = io.open(FI, encoding='utf-8', newline='').read()
lines = raw.split('\n')
header = lines[0].split('\t')
rows = [dict(zip(header, l.split('\t'))) for l in lines[1:] if l.strip()]
assert len(rows) == 54

# grade 列取值分布（确认其中无可引对象）
gc = collections.Counter(r['grade'] for r in rows)
print('grade values =', dict(gc))

PATTERNS = [
    ('SECTION',  re.compile(r'§\s*\d+(?:\.\d+)*')),
    ('FACT',     re.compile(r'(?<![\w])F(\d{2})(?![\d])')),
    ('MITEM',    re.compile(r'(?<![\w])M(\d{1,3})(?![\d])')),
    ('CARD',     re.compile(r'(?<![\w])(?:R1[4-7]_[A-Za-z0-9_]+|NAMED_PUSH_AUDIT\d{1,2}|NAMED_PUSH_S\d\w*)')),
    ('BARECARD', re.compile(r'(?<![\w])(?:PANEL|LEAD_LOCK|COVERAGE|BOARD_ARCHIVE|DELIVERY_SUMMARY|VERDICT|SECTION|REPORT|PANEL\.md)')),
    ('FILE',     re.compile(r'[A-Za-z0-9_\-]+\.(?:tsv|md|json|py|txt|exe)')),
    ('DECIDE',   re.compile(r'(?<![\w])(D-\d+)(?![\d])')),
    ('CLS',      re.compile(r'(?<![\w])(C-\d+)(?![\d])')),
    ('ADDR',     re.compile(r'0x[0-9A-Fa-f]{4,8}')),
]

buf = ['# R36 Check B · `statement` 列引用清点\n',
       '共 %d 条；`grade` 取值仅有 %s —— 该列无可引对象，不参与本检查。\n' % (len(rows), sorted(gc))]

tot = collections.Counter()
per_fact = {}
for r in rows:
    st = r['statement']
    found = collections.OrderedDict()
    for name, pat in PATTERNS:
        for m in pat.finditer(st):
            tok = m.group(0)
            found.setdefault(name, []).append(tok)
    if not found:
        continue
    # 去掉 ADDR（纯地址不是引用对象），保留其余
    refs = {k: sorted(set(v)) for k, v in found.items() if k != 'ADDR'}
    addrs = sorted(set(found.get('ADDR', [])))
    if not refs:
        continue
    per_fact[r['fact_id']] = {'refs': refs, 'addrs': addrs, 'ev': r['evidence_paths'], 'grade': r['grade']}
    for k, v in refs.items():
        tot[k] += len(v)
    buf.append('## %s [%s]' % (r['fact_id'], r['grade']))
    buf.append('- statement: %s' % st)
    buf.append('- evidence_paths: %s' % r['evidence_paths'])
    for k, v in refs.items():
        buf.append('  - %-9s %s' % (k, ' | '.join(v)))
    if addrs:
        buf.append('  - ADDR(n=%d)  %s%s' % (len(addrs), ' '.join(addrs[:8]), ' …' if len(addrs) > 8 else ''))
    buf.append('')

buf.insert(2, '含非 ADDR 引用的行数 = %d；各类 token 计数 = %s\n' % (len(per_fact), dict(tot)))
io.open(OUT, 'w', encoding='utf-8').write('\n'.join(buf))
print('rows with refs =', len(per_fact), 'kinds =', dict(tot))
print('wrote', OUT)
