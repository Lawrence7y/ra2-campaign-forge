# -*- coding: utf-8 -*-
"""R129p：把新节 2.133 按半量规则纳进 C16_FLOORS，并换摘要常量。

规则（与 R119 起的历轮一致）：新节实测正文 N 字节，取 N//2 作下界；表条目 +1，
摘要 sha256 必须同步重算（否则 C16d 立刻 TAMPERED）。
GATE_VER 由 R129 升到 R129 不动（本轮已升过，此处只是同一轮的第二次改门禁，版本不变）。
"""
import io, os, sys, re, hashlib, datetime

ROOT = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
BK = os.path.join(R14, 'R17_LEAD_BASELINE')
GATE = os.path.join(R14, 'check_disc.py')
RC = os.path.join(R14, 'R14_COMMON.md')
TS = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
ck = []
def add(n, ok, d=''):
    ck.append((n, bool(ok), d))

rc = io.open(RC, 'rb').read()
add('P0 R14_COMMON CR 仍 1081', rc.count(b'\r') == 1081, rc.count(b'\r'))
txt = rc.decode('utf-8')
# 量 2.133 正文
m = re.search(r'(?m)^## 2\.133\b', txt)
assert m
start = m.start()
nxt = re.search(r'(?m)^## 2\.\d+\b', txt[m.end():])
end = m.end() + nxt.start() if nxt else len(txt)
body = txt[start:end].rstrip('\n')
size = len(body.encode('utf-8'))
add('P1 2.133 实测正文 %d B，取半 %d 作下界' % (size, size // 2), size > 400, {'bytes': size, 'floor': size // 2})
FLOOR = size // 2

g = io.open(GATE, 'rb').read()
gs = g.decode('utf-8')
add('P2 门禁当前 unpinned 应为 1（只差 2.133）', '132: 5998' in gs and '133:' not in gs)
old_tail = "    132: 5998\n\n}"
add('P3 C16_FLOORS 末尾形态与预期一致', gs.count(old_tail) == 1, gs[gs.index('132: 5998')-40:gs.index('132: 5998')+40])
new_tail = "    132: 5998, 133: %d\n\n}" % FLOOR
g2 = gs.replace(old_tail, new_tail)
assert g2 != gs

# 重算摘要
m2 = re.search(r'C16_FLOORS = \{(.*?)\n\}', g2, re.S)
pairs = re.findall(r'(\d+):\s*(\d+)', m2.group(1))
d = {int(a): int(b) for a, b in pairs}
norm = '\n'.join('%d:%d' % (k, d[k]) for k in sorted(d))
new_sha = hashlib.sha256(norm.encode('utf-8')).hexdigest()
add('P4 重算后的表条目 %d 个（126 -> 127）' % len(d), len(d) == 127, len(d))
old_sha = re.search(r"C16_FLOORS_SHA256 = '([0-9a-f]{64})'", g2).group(1)
add('P5 旧摘要 = 2c6db9b4...（与门禁当前输出一致）', old_sha.startswith('2c6db9b43151f7ff'), old_sha[:16])
g3 = g2.replace("C16_FLOORS_SHA256 = '%s'" % old_sha, "C16_FLOORS_SHA256 = '%s'" % new_sha)
add('P6 新摘要 %s（与旧不同）' % new_sha[:16], new_sha != old_sha)

# 落盘
dst = os.path.join(BK, 'r129_check_disc_c16.%s.bak' % TS)
fd = os.open(dst, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
try: os.write(fd, g)
finally: os.close(fd)
with io.open(GATE, 'wb') as f: f.write(g3.encode('utf-8'))
rb = io.open(GATE, 'rb').read()
add('P7 回读 == 写入 且 CR 不变', rb == g3.encode('utf-8') and rb.count(b'\r') == g.count(b'\r'))
add('P8 回读含 133 条目与新摘要', ('133: %d' % FLOOR).encode() in rb and new_sha.encode() in rb)

bad = [c for c in ck if not c[1]]
for n, ok, d in ck:
    print(('  PASS ' if ok else '  FAIL ') + n + (('  | ' + str(d)) if d != '' else ''))
print('%d/%d PASS' % (len(ck) - len(bad), len(ck)))
sys.exit(1 if bad else 0)
