import io, os, re, shutil
V = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\recheck_verify.py'
v = io.open(V, encoding='utf-8').read()
shutil.copy2(V, V + '.bakR56b')

OLD = """    hits = [l for l in txt.splitlines() if l.startswith(_PREFIX)]
    if len(hits) != 1:
        return _fail('R1 line_count=%d (must be 1)' % len(hits))
    line = hits[0]"""
NEW = """    # R56 修（缺陷 3）：原为「该产物里 DISC_RECHECK 行必须恰好 1 条」——
    # 但纪律 3 与 4 共用同一产物 anchor_check.txt，各写一条 ⇒ 永远满足不了。
    # 正确语义：**本纪律**的行必须恰好 1 条（同产物可含其它纪律的行）。
    allh = [l for l in txt.splitlines() if l.startswith(_PREFIX)]
    hits = []
    for _l in allh:
        _m = re.search(r'\\bdiscipline=(\\d+)\\b', _l)
        if _m and int(_m.group(1)) == N:
            hits.append(_l)
    if len(hits) != 1:
        return _fail('R1 line_count_for_discipline_%d=%d (must be 1; product has %d DISC_RECHECK lines total)'
                     % (N, len(hits), len(allh)))
    line = hits[0]"""
assert OLD in v, 'R1 block not found'
v = v.replace(OLD, NEW, 1)
io.open(V, 'w', encoding='utf-8').write(v)
print('defect3 fixed: R1 now counts lines for THIS discipline, not all lines in product')
print('  (同产物可含其它纪律的行；本纪律仍必须恰好 1 条)')
