import io, os, csv, hashlib

ROOT = r'D:\Project\ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
SEM = os.path.join(R14, r'R17_R88_T1_SEMDEF\tier_final.tsv')
REJ = os.path.join(R14, r'R17_R92_T1_REJUDGE\rejudge1242.tsv')
OUT_DIR = os.path.join(R14, 'R17_R96_TIER_FINAL_4413')
os.makedirs(OUT_DIR, exist_ok=True)
OUT = os.path.join(OUT_DIR, 'tier_final_4413.tsv')

def read_tsv(p):
    rows = list(csv.reader(io.open(p, encoding='utf-8', errors='replace'), delimiter='\t'))
    return rows[0], rows[1:]

# ---- 旧 tier_final（跳过 DISC_RECHECK 自述行）----
h, d = read_tsv(SEM)
ri, bi, wi = h.index('rel'), h.index('bytes'), h.index('why_content')
d = [r for r in d if len(r) == len(h) and not r[0].startswith('DISC_RECHECK')]
print('旧 tier_final 有效数据行 = %d（已跳过自述行）' % len(d))
assert len(d) == 4518, len(d)

p1a = [r for r in d if r[wi].startswith('有内容证据=前8KiB')]
old_obj = [r for r in d if not r[wi].startswith('有内容证据=前8KiB')]
p1a_n, p1a_b = len(p1a), sum(int(r[bi]) for r in p1a)
oo_n, oo_b = len(old_obj), sum(int(r[bi]) for r in old_obj)
print('  P1a          = %d / %d B' % (p1a_n, p1a_b))
print('  旧逐件对象   = %d / %d B' % (oo_n, oo_b))
assert p1a_n + oo_n == 4518

# ---- rejudge 的新对象集（627）----
h2, d2 = read_tsv(REJ)
r2, n2, b2 = h2.index('rel'), h2.index('new_verdict'), h2.index('bytes')
new_obj = [r for r in d2 if r[n2] == '对象抄本']
new_obj_bytes = sum(int(r[b2]) for r in new_obj)
print('  rejudge 新对象 = %d / %d B' % (len(new_obj), new_obj_bytes))
assert len(new_obj) == 627 and new_obj_bytes == 29944200

# ---- 校验：627 与 P1a 无交集（627 全在 C′ 外、P1a 全在 C′ 内）----
p1a_rel = set(r[ri] for r in p1a)
new_obj_rel = set(r[r2] for r in new_obj)
inter = p1a_rel & new_obj_rel
print('  P1a ∩ 新对象 = %d（应为 0）' % len(inter))
assert len(inter) == 0

# ---- 组装 4,413 ----
# 新 tier_final = P1a ∪ 新对象627
out_rows = []
for r in p1a:
    out_rows.append([r[ri], r[bi], 'P1a_前8KiB行首VA>=60%', r[wi]])
for r in new_obj:
    out_rows.append([r[r2], r[b2], 'rejudge_R53_对象抄本', r[n2]])

n = len(out_rows)
b = sum(int(r[1]) for r in out_rows)
print()
print('新 tier_final = %d 件 / %d B' % (n, b))
assert n == 4413, n
assert b == 744172839, b
# 两式互核
assert 3786 + 627 == n
assert 714228639 + 29944200 == b
print('  两式互核: 3786+627=%d ; 714,228,639+29,944,200=%d  OK' % (n, b))

# ---- 写盘 ----
HDR = ['rel', 'bytes', 'source', 'why_content']
with open(OUT, 'x', encoding='utf-8', newline='') as f:
    w = csv.writer(f, delimiter='\t', lineterminator='\n')
    w.writerow(HDR)
    for r in out_rows:
        w.writerow(r)

back = io.open(OUT, encoding='utf-8', newline='').read()
assert '\r' not in back
bl = [l for l in back.split('\n') if l]
assert len(bl) - 1 == 4413, len(bl) - 1
for l in bl:
    assert l.count('\t') == 3, l.count('\t')
# 回读求和
tot = sum(int(l.split('\t')[1]) for l in bl[1:])
assert tot == 744172839, tot
print()
print('wrote', OUT, os.path.getsize(OUT), 'B ; 4413 rows x 4 cols ; sum(bytes)=%d' % tot)
print('sha256 =', hashlib.sha256(back.encode()).hexdigest().upper())
