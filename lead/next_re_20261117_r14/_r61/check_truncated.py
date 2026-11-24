import io, os, csv, json

ROOT = r'D:\Project\ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
REJ = os.path.join(R14, r'R17_R92_T1_REJUDGE\rejudge1242.tsv')

rows = list(csv.reader(io.open(REJ, encoding='utf-8', errors='replace'), delimiter='\t'))
h, d = rows[0], rows[1:]
ri, bi, ni, ti, oi = h.index('rel'), h.index('bytes'), h.index('new_verdict'), h.index('truncated'), h.index('old_verdict')

tr = [r for r in d if r[ti].strip().upper() == 'Y']
print('truncated=Y 共 %d 件' % len(tr))
print()
for r in tr:
    print('%-58s %10s B  旧=%-6s 新=%-6s' % (r[ri][-56:], r[bi], r[oi], r[ni]))
print()

# 对这 4 件「判为过程输出」的，检查它们是否真的 > 1 MiB（若是，截断可能影响判定）
LIMIT = 1024 * 1024
print('=== 逐件核：大小 vs 1 MiB 阈值，及是否真被截断 ===')
for r in tr:
    b = int(r[bi])
    over = b > LIMIT
    print('%-56s %10d B  超 1 MiB=%s' % (r[ri][-54:], b, 'YES' if over else 'no'))

print()
print('=== 若某件 > 1 MiB 且判为过程，需要复核其前 1 MiB 之后的尾部 ===')
for r in tr:
    rel = r[ri].replace('/', '\\')
    ap = os.path.join(ROOT, 'lead', rel) if not os.path.isabs(rel) else rel
    if not os.path.isfile(ap):
        # 试 lead\ 下搜
        bn = os.path.basename(rel)
        found = None
        for dp, _, fs in os.walk(os.path.join(ROOT, 'lead')):
            if bn in fs:
                found = os.path.join(dp, bn); break
        ap = found
    if not ap or not os.path.isfile(ap):
        print('  MISSING: %s' % r[ri][-56:]); continue
    size = os.path.getsize(ap)
    if size <= LIMIT:
        print('  %-52s %9d B  整件都读到了 ⇒ 截断不影响判定  OK' % (os.path.basename(ap), size))
    else:
        print('  %-52s %9d B  超 1 MiB ⇒ 尾部未读，判定可能受影响' % (os.path.basename(ap), size))
