# -*- coding: utf-8 -*-
"""补 v5.10 目录标记 + 总复核所有 FACT_INDEX 标记指向。"""
import io, os

R14  = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
OLD, NEW = 'R17_R65_FACTINDEX_V510', 'R17_R66_FACTINDEX_V511'
v510 = os.path.join(R14, OLD, 'SUPERSEDED.md')

if not os.path.exists(v510):
    mark = """# 本目录已作废 —— 请勿引用

**当前权威版本：(v5.11) `R17_R66_FACTINDEX_V511`**

- 作废原因：v5.11 修正了 `F15` / `F35` 两处 `limitations` 缺陷，并按跨家族审计结论修正 `F24` / `F29` 的 `statement` 正文
  （详见 `R17_R66_FACTINDEX_V511\\CHANGES.md`）。
- 本目录内容**字节未动**，仅作历史留存。
- 引用本目录的任何数字时，须同时说明其为 v5.10 历史快照。
"""
    with open(v510, 'x', encoding='utf-8', newline='') as f:
        f.write(mark)
    print('created R17_R65_FACTINDEX_V510\\SUPERSEDED.md')
else:
    print('v5.10 marker already exists')

# 总复核
rows = []
for dirpath, _, files in os.walk(R14):
    if 'SUPERSEDED.md' in files:
        p = os.path.join(dirpath, 'SUPERSEDED.md')
        t = io.open(p, encoding='utf-8', newline='').read()
        rows.append((os.path.basename(dirpath), NEW in t, OLD in t, 'FACTINDEX' in t.upper() or 'FACT_INDEX' in t.upper()))

fact = [r for r in rows if r[3]]
print('FACT_INDEX markers = %d' % len(fact))
stale = [r[0] for r in fact if not r[1]]
print('  still not pointing v5.11 = %d %s' % (len(stale), stale))
# 注意：v5.10 自己的标记必然同时含 OLD(自身目录名) 与 NEW，不算 stale
for r in sorted(fact):
    print('   %-24s -> v5.11=%s  mentions_old=%s' % (r[0], r[1], r[2]))
assert not stale, stale
print('OK')
