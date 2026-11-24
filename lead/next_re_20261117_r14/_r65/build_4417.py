import io, os, csv, hashlib

R14 = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
SRC = os.path.join(R14, r'R17_R99_TIER_FINAL_4416\tier_final_4416.tsv')
OUT_DIR = os.path.join(R14, 'R17_R101_TIER_FINAL_4417')
os.makedirs(OUT_DIR, exist_ok=True)
OUT = os.path.join(OUT_DIR, 'tier_final_4417.tsv')

ADD = ('next_re_20261117_r14/S21_DIRECT/_audit/EVIDENCE/scan_mine.json', 1365365,
       'R64重判_对象侧(calls 68,253 对 + 元数据；calls 与另3份重复，见 §2.71 口径)')

rows = list(csv.reader(io.open(SRC, encoding='utf-8', errors='replace'), delimiter='\t'))
h, d = rows[0], rows[1:]
ri, bi, si, wi = h.index('rel'), h.index('bytes'), h.index('source'), h.index('why_content')
assert len(d) == 4416, len(d)
assert ADD[0] not in set(r[ri] for r in d)

out = [[r[ri], r[bi], r[si], r[wi]] for r in d]
out.append([ADD[0], str(ADD[1]), 'R64_重判对象侧', ADD[2]])

n = len(out)
tot = sum(int(r[1]) for r in out)
assert n == 4417, n
assert tot == 737517286, tot
assert 736151921 + 1365365 == 737517286

with open(OUT, 'x', encoding='utf-8', newline='') as f:
    w = csv.writer(f, delimiter='\t', lineterminator='\n')
    w.writerow(h)
    for r in out:
        w.writerow(r)

back = io.open(OUT, encoding='utf-8', newline='').read()
assert '\r' not in back
bl = [l for l in back.split('\n') if l]
assert len(bl) - 1 == 4417, len(bl) - 1
for l in bl:
    assert l.count('\t') == len(h) - 1
tot2 = sum(int(l.split('\t')[1]) for l in bl[1:])
assert tot2 == 737517286, tot2

print('wrote', OUT, os.path.getsize(OUT), 'B ; 4417 rows ; sum readback =', tot2)
print('GB(10^9)=%.6f ; GiB(2^30)=%.6f' % (tot2/1e9, tot2/1024**3))
print('sha256 =', hashlib.sha256(back.encode()).hexdigest().upper())
