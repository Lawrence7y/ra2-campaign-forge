import io, os, csv, hashlib

ROOT = r'D:\Project\ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
SRC = os.path.join(R14, r'R17_R97_TIER_FINAL_4413B\tier_final_4413b.tsv')
OUT_DIR = os.path.join(R14, 'R17_R99_TIER_FINAL_4416')
os.makedirs(OUT_DIR, exist_ok=True)
OUT = os.path.join(OUT_DIR, 'tier_final_4416.tsv')

# 三件翻为对象侧的（用 rejudge 记录的路径与字节，sweep 用改正后的 1,631,944）
ADDS = [
    ('next_re_20261117_r14/S13_K8/_audit/EVIDENCE/mesh_imm32.json', 5693169,
     'R62重判_对象侧(imm/abs 值→使用点,双控可回原址)'),
    ('next_re_20261117_r14/S08_KPROVED2/_audit/EVIDENCE/sweep.json', 1631944,
     'R63重判_对象侧(e8 地址对 + installs 寻址模式+值)'),
    ('next_re_20261117_r14/S21_DIRECT/_audit/EVIDENCE/scan_mine.json', None, None),  # placeholder, removed below
]
ADDS = [a for a in ADDS if a[1] is not None]
ADDS.append(('next_re_20261117_r14/S09_KPROVED7/_audit/EVIDENCE/e8_sites_audit.json', 1365087,
             'R62重判_对象侧(68,253 地址对,已验 E8 调用)'))

rows = list(csv.reader(io.open(SRC, encoding='utf-8', errors='replace'), delimiter='\t'))
h, d = rows[0], rows[1:]
ri, bi, si, wi = h.index('rel'), h.index('bytes'), h.index('source'), h.index('why_content')
assert len(d) == 4413

existing = set(r[ri] for r in d)
for rel, b, why in ADDS:
    assert rel not in existing, 'already present: ' + rel

out = [[r[ri], r[bi], r[si], r[wi]] for r in d]
for rel, b, why in ADDS:
    out.append([rel, str(b), 'R62R63_重判对象侧', why])

tot = sum(int(r[1]) for r in out)
n = len(out)
print('新清单 = %d 件 / %d B' % (n, tot))
assert n == 4416, n
assert tot == 736151921, tot
assert 727461721 + 5693169 + 1631944 + 1365087 == 736151921

with open(OUT, 'x', encoding='utf-8', newline='') as f:
    w = csv.writer(f, delimiter='\t', lineterminator='\n')
    w.writerow(h)
    for r in out:
        w.writerow(r)

back = io.open(OUT, encoding='utf-8', newline='').read()
assert '\r' not in back
bl = [l for l in back.split('\n') if l]
assert len(bl) - 1 == 4416, len(bl) - 1
for l in bl:
    assert l.count('\t') == len(h) - 1, l.count('\t')
tot2 = sum(int(l.split('\t')[1]) for l in bl[1:])
assert tot2 == 736151921, tot2
print()
print('wrote', OUT, os.path.getsize(OUT), 'B ; 4416 rows ; sum readback =', tot2)
print('GB(10^9) = %.6f ; GiB(2^30) = %.6f' % (tot2 / 1e9, tot2 / 1024 ** 3))
print('sha256 =', hashlib.sha256(back.encode()).hexdigest().upper())
