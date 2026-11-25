# -*- coding: utf-8 -*-
"""R129g：GATE_VER R128 -> R129，并同步 DISC_RECHECK 第 20 行的登记式。

依据：C10 门自检要求「登记行里的版本标记」与本脚本的 GATE_VER 一致；本轮确实改了
check_disc.py（r129e 新判据），故必须升版本，否则 C10 会认为门没被改过。
两处改动方向都是收紧：新判据让 claims-none 行多一道可失败检查。

写入纪律：wx 独占备份 -> 断言旧 sha -> 一次性写入 -> 回读校验 -> 断言 CR 不变。
"""
import io, os, sys, hashlib, datetime
ROOT = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
BK = os.path.join(R14, 'R17_LEAD_BASELINE')
GATE = os.path.join(R14, 'check_disc.py')
DR = os.path.join(R14, 'DISC_RECHECK.tsv')
TS = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

ck = []
def add(n, ok, d=''):
    ck.append((n, bool(ok), d))

def sha(b): return hashlib.sha256(b).hexdigest()

# --- 1. GATE_VER ---
old = io.open(GATE, 'rb').read()
add('G0 check_disc.py 是 r129e 之后的字节（sha b6cec4a610f062ed）', sha(old).startswith('b6cec4a610f062ed'), sha(old)[:16])
assert old.decode('utf-8').count("GATE_VER = 'R128'") == 1
nb = old.decode('utf-8').replace("GATE_VER = 'R128'", "GATE_VER = 'R129'").encode('utf-8')
dst = os.path.join(BK, 'r129_check_disc_gatever.%s.bak' % TS)
fd = os.open(dst, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
try: os.write(fd, old)
finally: os.close(fd)
add('G1 wx 备份已建', os.path.isfile(dst))
with io.open(GATE, 'wb') as f: f.write(nb)
rb = io.open(GATE, 'rb').read()
add('G2 回读 == 写入', rb == nb)
add('G3 回读 CR 不变（0）', rb.count(b'\r') == old.count(b'\r'), rb.count(b'\r'))
add('G4 回读含 GATE_VER = R129', b"GATE_VER = 'R129'" in rb)

# --- 2. DISC_RECHECK 第 20 行 ---
old2 = io.open(DR, 'rb').read()
t2 = old2.decode('utf-8')
add('G5 DISC_RECHECK CR 数为 0（LF-only）', '\r' not in t2)
assert t2.count("grep=(?m)^GATE_VER = 'R128'") == 1, t2.count("GATE_VER = 'R128'")
n2 = t2.replace("grep=(?m)^GATE_VER = 'R128'", "grep=(?m)^GATE_VER = 'R129'")
dst2 = os.path.join(BK, 'r129_disc_recheck_gatever.%s.bak' % TS)
fd = os.open(dst2, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
try: os.write(fd, old2)
finally: os.close(fd)
add('G6 wx 备份已建（tsv）', os.path.isfile(dst2))
with io.open(DR, 'wb') as f: f.write(n2.encode('utf-8'))
rb2 = io.open(DR, 'rb').read()
add('G7 回读 == 写入（tsv）', rb2 == n2.encode('utf-8'))
add('G8 回读 CR 仍 0', rb2.count(b'\r') == 0, rb2.count(b'\r'))
add('G9 回读含 GATE_VER = R129 登记式', b"grep=(?m)^GATE_VER = 'R129'" in rb2)

bad = [c for c in ck if not c[1]]
for n, ok, d in ck:
    print(('  PASS ' if ok else '  FAIL ') + n + (('  | ' + str(d)) if d != '' else ''))
print('%d/%d PASS' % (len(ck) - len(bad), len(ck)))
sys.exit(1 if bad else 0)
