# -*- coding: utf-8 -*-
"""生成 FACT_INDEX v5.12：只改 F14 的 evidence_paths（加台账本体锚 §1060/§1061/§1062）。
纪律：读 v5.11 → 逐行断言只有 F14 变化 → wx 独占创建 → 回读校验。
"""
import io, os, hashlib

ROOT = r'D:\Project\ra2-campaign-forge'
R14  = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
SRC  = os.path.join(R14, 'R17_R66_FACTINDEX_V511')
DST  = os.path.join(R14, 'R17_R67_FACTINDEX_V512')
os.makedirs(DST, exist_ok=True)

raw = io.open(os.path.join(SRC, 'FACT_INDEX.tsv'), encoding='utf-8', newline='').read()
assert '\r' not in raw
lines = raw.split('\n')
assert lines[0].split('\t') == ['fact_id', 'statement', 'grade', 'evidence_paths', 'limitations']
data = [l for l in lines[1:] if l.strip()]
assert len(data) == 54

LEDGER_ANCHOR = r'lead\GOAL_THREE_TARGETS_20261018.md(§1060 / §1061 / §1062)'

out_rows, changed = [], []
for l in data:
    c = l.split('\t')
    assert len(c) == 5
    if c[0] == 'F14':
        old = c[3]
        assert 'GOAL_THREE_TARGETS_20261018.md' not in old, 'already has ledger anchor'
        c[3] = old + ';' + LEDGER_ANCHOR
        changed.append(('F14', 'evidence_paths', old, c[3]))
    out_rows.append('\t'.join(c))
assert len(changed) == 1

out = '\n'.join([lines[0]] + out_rows) + '\n'
assert '\r' not in out
dst = os.path.join(DST, 'FACT_INDEX.tsv')
assert not os.path.exists(dst), 'v5.12 already exists'
with open(dst, 'x', encoding='utf-8', newline='') as f:
    f.write(out)

back = io.open(dst, encoding='utf-8', newline='').read()
assert back == out
assert back.count('\n') == 55
assert back.count('\t') == 55 * 4
backrows = [l for l in back.split('\n')[1:] if l.strip()]
assert len(backrows) == 54
for a, b in zip(data, backrows):
    fa = a.split('\t')[0]
    assert fa == b.split('\t')[0]
    if fa != 'F14':
        assert a == b, 'unexpected change in ' + fa

dist = {}
for b in backrows:
    g = b.split('\t')[2]
    dist[g] = dist.get(g, 0) + 1
assert dist.get('[已证]') == 27 and dist.get('[静态推断]') == 1 and dist.get('未取得') == 2 and dist.get('[流程]') == 24

print('OK', dst)
print('bytes =', os.path.getsize(dst))
print('sha256 =', hashlib.sha256(back.encode()).hexdigest().upper())
print('grade dist =', dist)
print()
print('--- F14.evidence_paths ---')
print('OLD:', changed[0][2])
print('NEW:', changed[0][3])
