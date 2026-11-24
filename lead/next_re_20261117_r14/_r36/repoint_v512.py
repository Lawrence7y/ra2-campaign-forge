# -*- coding: utf-8 -*-
"""把 17 份 FACT_INDEX 标记重指向 v5.12，并为 v5.11 目录新建标记。
只改「指向 v5.11」的那处字符串，其余字节不动（回读逐字断言）。
"""
import io, os, hashlib, datetime

ROOT = r'D:\Project\ra2-campaign-forge'
R14  = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
BK   = os.path.join(R14, 'R17_LEAD_BASELINE')
OLD, NEW = 'R17_R66_FACTINDEX_V511', 'R17_R67_FACTINDEX_V512'

targets = []
for dirpath, _, files in os.walk(R14):
    if 'SUPERSEDED.md' not in files:
        continue
    p = os.path.join(dirpath, 'SUPERSEDED.md')
    t = io.open(p, encoding='utf-8', newline='').read()
    if NEW in t:
        continue
    if OLD in t:
        targets.append((p, t))
print('markers to rewrite =', len(targets))
assert len(targets) == 17, len(targets)

ts = datetime.datetime.now().strftime('%H%M%S')
for p, old_txt in targets:
    name = 'SUPERSEDED.before_v512_%s_%s' % (os.path.basename(os.path.dirname(p)), ts)
    b = os.path.join(BK, name)
    with open(b, 'xb') as f:
        f.write(io.open(p, 'rb').read())
    new_txt = old_txt.replace(OLD, NEW)
    assert new_txt != old_txt
    assert new_txt.count('\r\n') == old_txt.count('\r\n')
    with open(p, 'wb') as f:
        f.write(new_txt.encode('utf-8'))
    back = io.open(p, encoding='utf-8', newline='').read()
    assert back == new_txt
    assert back.replace(NEW, OLD) == old_txt
print('rewrote =', len(targets))

# v5.11 目录新建标记
v511 = os.path.join(R14, OLD, 'SUPERSEDED.md')
if not os.path.exists(v511):
    mark = """# 本目录已作废 —— 请勿引用

**当前权威版本：(v5.12) `R17_R67_FACTINDEX_V512`**

- 作废原因：v5.12 修了 `F14` 的 `evidence_paths`（加台账锚 `§1060 / §1061 / §1062`）——
  `F14` 的三个断言内容均属实，但原三锚不含它们，读者无法核对。
- 本目录内容**字节未动**，仅作历史留存。
- 引用本目录的任何数字时，须同时说明其为 v5.11 历史快照。
"""
    with open(v511, 'x', encoding='utf-8', newline='') as f:
        f.write(mark)
    print('created marker for v5.11')

# 总复核
rows = []
for dirpath, _, files in os.walk(R14):
    if 'SUPERSEDED.md' not in files:
        continue
    p = os.path.join(dirpath, 'SUPERSEDED.md')
    t = io.open(p, encoding='utf-8', newline='').read()
    d = os.path.basename(dirpath)
    if d.startswith('R17_R') and ('FACTINDEX' in d.upper() or 'FACT_INDEX' in d.upper()) or d in ('R17_R42_F23_FIX', 'R17_R47_GRADE_NORM'):
        rows.append((d, NEW in t))
print('FACT_INDEX-family markers =', len(rows))
stale = [d for d, ok in rows if not ok]
print('stale =', stale)
assert not stale, stale
print('OK')
