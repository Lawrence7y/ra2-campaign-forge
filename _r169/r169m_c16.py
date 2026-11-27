#!/usr/bin/env python3
"""R169 M：C16 下界重钉（新增 §2.174 一节）。

§2.174 是本轮新增，check_disc 报 unpinned=1；按「落盘实测字节的一半」取下界，并重钉 C16_FLOORS_SHA256。
不做 GATE_VER 升版（本轮未改 DISC_RECHECK / DISC_UNVERIFIABLE 任何一行 ⇒ C7/C14/FREEZE 必须一字不动，立为反控）。
"""
import ast, hashlib, json, re, os, py_compile
ROOT = '/home/t628/projects/ra2-campaign-forge'
CD = ROOT + '/lead/next_re_20261117_r14/check_disc.py'
RC = ROOT + '/lead/next_re_20261117_r14/R14_COMMON.md'
BAKDIR = ROOT + '/lead/next_re_20261117_r14/R17_LEAD_BASELINE'

def sha(b): return hashlib.sha256(b).hexdigest()
b0 = open(CD, 'rb').read()
bak = os.path.join(BAKDIR, 'check_disc.py.before_r169_C16.bak')
fd = os.open(bak, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
with os.fdopen(fd, 'wb') as f: f.write(b0)
assert sha(open(bak, 'rb').read()) == sha(b0)

txt = open(RC, 'rb').read().decode('utf-8')
segs = []
cur = None; buf = []
for line in txt.split('\n'):
    m = re.match(r'^##\s+2\.(\d+)\b', line)
    if m:
        if cur is not None:
            segs.append((cur, len('\n'.join(buf).encode('utf-8'))))
        cur = int(m.group(1)); buf = [line]
    elif cur is not None:
        buf.append(line)
if cur is not None:
    segs.append((cur, len('\n'.join(buf).encode('utf-8'))))
d = dict(segs)
sz174 = d[174]; f174 = sz174 // 2
print('§2.174 = %d B -> floor %d' % (sz174, f174))

src = open(CD, encoding='utf-8').read()
m = re.search(r'^C16_FLOORS = \{(.*?)^\}', src, re.M | re.S)
assert m
tbl_src = m.group(0)
ns = {}
exec(tbl_src, ns)
FLOORS = dict(ns['C16_FLOORS'])
old_len = len(FLOORS)
old_sha_c = re.search(r"^C16_FLOORS_SHA256 = '([0-9a-f]{64})'", src, re.M).group(1)
norm_old_full = '\n'.join('%d:%d' % (k, ns['C16_FLOORS'][k]) for k in sorted(ns['C16_FLOORS']))
sha_old_recomputed = hashlib.sha256(norm_old_full.encode()).hexdigest()
FLOORS[174] = f174
norm_new = '\n'.join('%d:%d' % (k, FLOORS[k]) for k in sorted(FLOORS))
sha_new = hashlib.sha256(norm_new.encode()).hexdigest()

if '174:' not in tbl_src:
    new_tbl = tbl_src.replace('\n}', "\n    174: %d,\n}" % f174)
else:
    new_tbl = tbl_src
src2 = src.replace(tbl_src, new_tbl, 1)
src2 = src2.replace("C16_FLOORS_SHA256 = '%s'" % old_sha_c, "C16_FLOORS_SHA256 = '%s'" % sha_new, 1)
open(CD, 'w', encoding='utf-8', newline='').write(src2)
py_compile.compile(CD, doraise=True)
src3 = open(CD, encoding='utf-8').read()
ns2 = {}
exec(re.search(r'^C16_FLOORS = \{(.*?)^\}', src3, re.M | re.S).group(0), ns2)
F2 = ns2['C16_FLOORS']
sha2_c = re.search(r"^C16_FLOORS_SHA256 = '([0-9a-f]{64})'", src3, re.M).group(1)

A = []
def chk(i, cond, detail):
    A.append({'id': i, 'ok': bool(cond), 'detail': str(detail)})

chk('M0 旧表重算 sha 命中旧常量（同法自证）', sha_old_recomputed == old_sha_c, old_sha_c[:16])
chk('M1 表条目 +1（新增 174），且原有逐条不变',
    len(F2) == old_len + 1 and all(F2[k] == ns['C16_FLOORS'][k] for k in ns['C16_FLOORS']),
    '%d -> %d' % (old_len, len(F2)))
chk('M2 新条目下界 == 实测字节的一半', F2[174] == f174, {'floor': F2[174], 'measured': sz174})
chk('M3 C16_FLOORS_SHA256 常量 == 由表重算', sha2_c == sha_new, sha2_c[:16])
chk('M4 反控：GATE_VER 未动（仍 R166）', re.search(r"^GATE_VER = 'R166'", src3, re.M) is not None, 'R166')
chk('M5 反控：C7_TEXT_SHA256 / C14_TEXT_SHA256 / FREEZE_SHA256 一字未动',
    "C7_TEXT_SHA256 = 'b07f46981eb34a22cd31ceb1b9019b7f3c7718fe69b9e3a348a1fa9fb3bc1d59'" in src3
    and "C14_TEXT_SHA256 = 'a740bcc9add4e6073071e5d6b693d213b4711ee2f3df8ab3c1db32e1a153975f'" in src3
    and "FREEZE_SHA256 = '5fc21cfece52f1e44525d9510c4cd2a6a08172c2b134be4686008355c4bf7f61'" in src3, 'ok')

out = {'sz174': sz174, 'floor174': f174, 'sections': len(F2), 'old_c16_sha': old_sha_c,
       'new_c16_sha': sha2_c, 'cd_sha': sha(open(CD, 'rb').read()),
       'assertions': A, 'fail': sum(1 for a in A if not a['ok'])}
json.dump(out, open(ROOT + '/_r169/r169m_c16.json', 'w'), ensure_ascii=False, indent=1)
for a in A:
    print(('PASS ' if a['ok'] else 'FAIL ') + a['id'] + ' :: ' + a['detail'][:200])
print('FAIL count =', out['fail'])
print('C16 sections %d, sha %s' % (len(F2), sha2_c[:16]))
