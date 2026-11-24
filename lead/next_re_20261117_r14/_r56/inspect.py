import io, re
V = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\recheck_verify.py'
L = io.open(V, encoding='utf-8').read().split('\n')
print('total lines', len(L))
print()
print('=== R1 / line_count related ===')
for i, l in enumerate(L, 1):
    if 'line_count' in l or 'must be 1' in l or 'DISC_RECHECK discipline' in l or 'prefix' in l:
        print('  L%-4d %s' % (i, l.rstrip()[:125]))
print()
print('=== window table entries ===')
pat = re.compile(r"\((\d+), '(\d{6})', '(\d{6})'")
for i, l in enumerate(L, 1):
    m = pat.search(l)
    if m:
        print('  r%-3s %s -> %s   (L%d)' % (m.group(1), m.group(2), m.group(3), i))
