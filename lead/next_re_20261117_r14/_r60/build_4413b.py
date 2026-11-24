import io, os, csv, hashlib

ROOT = r'D:\Project\ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
SRC = os.path.join(R14, r'R17_R96_TIER_FINAL_4413\tier_final_4413.tsv')
OUT_DIR = os.path.join(R14, 'R17_R97_TIER_FINAL_4413B')
os.makedirs(OUT_DIR, exist_ok=True)
OUT = os.path.join(OUT_DIR, 'tier_final_4413b.tsv')

BOUNDS = 16711118        # a2_sites.json 的 bounds 段（纯地址清单，86.19% 无字节对应）
A2 = 'a2_sites.json'

rows = list(csv.reader(io.open(SRC, encoding='utf-8', errors='replace'), delimiter='\t'))
h, d = rows[0], rows[1:]
ri, bi, si, wi = h.index('rel'), h.index('bytes'), h.index('source'), h.index('why_content')
assert len(d) == 4413

out = []
changed = 0
for r in d:
    rel, b, src, why = r[ri], int(r[bi]), r[si], r[wi]
    if rel.endswith(A2):
        nb = b - BOUNDS
        assert nb > 0
        out.append([rel, str(nb), src, why + ' | R59剔除bounds段(纯地址清单,86.19%无字节对应)'])
        print('a2_sites: %d -> %d B (剔除 bounds %d B)' % (b, nb, BOUNDS))
        changed += 1
    else:
        out.append([rel, str(b), src, why])
assert changed == 1

n = len(out)
tot = sum(int(r[1]) for r in out)
print('新清单 = %d 件 / %d B' % (n, tot))
assert n == 4413
assert tot == 727461721, tot
assert 744172839 - BOUNDS == tot

HDR = h
with open(OUT, 'x', encoding='utf-8', newline='') as f:
    w = csv.writer(f, delimiter='\t', lineterminator='\n')
    w.writerow(HDR)
    for r in out:
        w.writerow(r)

back = io.open(OUT, encoding='utf-8', newline='').read()
assert '\r' not in back
bl = [l for l in back.split('\n') if l]
assert len(bl) - 1 == 4413
for l in bl:
    assert l.count('\t') == len(HDR) - 1
tot2 = sum(int(l.split('\t')[1]) for l in bl[1:])
assert tot2 == 727461721, tot2

print()
print('wrote', OUT, os.path.getsize(OUT), 'B')
print('sum(bytes) readback = %d  OK' % tot2)
print('GB(10^9) = %.6f ; GiB(2^30) = %.6f' % (tot2/1e9, tot2/1024**3))
print('sha256 =', hashlib.sha256(back.encode()).hexdigest().upper())
