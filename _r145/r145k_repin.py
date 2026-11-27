#!/usr/bin/env python3
"""R145 K：C16 重钉（纳 §2.150）+ GATE_VER R144→R145。纪律同 r144q：
① 新节必须显式入表；② 重钉前先用现表重算复现旧钉；③ 下界 = 实测 − 21。
本脚本只做 pin 与版本号；两张 TSV 的同步另由 r145l 做。
"""
import hashlib, io, json, os, re, time
BASE = '/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14'
GATE = os.path.join(BASE, 'check_disc.py')
BL = os.path.join(BASE, 'R17_LEAD_BASELINE')
cc = []
def ck(n, c, d=''):
    print(('  PASS ' if c else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not c: cc.append(n)

src = open(GATE, 'rb').read(); txt = src.decode('utf-8')
m = re.search(r'C16_FLOORS = \{(.*?)\n\}', txt, re.S)
ck('B0 找到 C16_FLOORS', m is not None)
d = dict((int(a), int(b)) for a, b in re.findall(r'(\d+):\s*(\d+)', m.group(1)))
old_sha = re.search(r"C16_FLOORS_SHA256 = '([0-9a-f]+)'", txt).group(1)
ck('B1 表项 143 条', len(d) == 143, len(d))
ck('B2 旧钉 = 05b54f35', old_sha.startswith('05b54f35'), old_sha[:16])
norm = lambda dd: '\n'.join('%d:%d' % (k, dd[k]) for k in sorted(dd))
ck('B3 方法可复现旧钉', hashlib.sha256(norm(d).encode()).hexdigest() == old_sha)
ck('B4 表里尚无 150', 150 not in d)

rc = open(os.path.join(BASE, 'R14_COMMON.md'), 'rb').read().decode('utf-8')
lines = rc.split('\n'); sec = []; cur = None
for l in lines:
    mm = re.match(r'^##\s+2\.(\d+)\b', l)
    if mm:
        if cur == 150: break
        cur = int(mm.group(1)); sec = [l]
    elif cur == 150:
        sec.append(l)
size = len('\n'.join(sec).encode('utf-8'))
ck('B5 §2.150 按 C16 口径测得字节数 > 8000（本轮长节）', size > 8000, size)
floor = size - 21
ck('B6 下界 = 实测 − 21', floor == size - 21, (size, floor))
d2 = dict(d); d2[150] = floor
new_sha = hashlib.sha256(norm(d2).encode()).hexdigest()
ck('B7 新钉 != 旧钉', new_sha != old_sha)

dst = os.path.join(BL, 'check_disc.py.before_r145_repin_%s.bak' % time.strftime('%Y%m%d_%H%M%S'))
with io.open(dst, 'xb') as f: f.write(src)
ck('B8 备份 wx 独占且逐字节相同', open(dst, 'rb').read() == src, os.path.basename(dst))

t2 = txt.replace("148: 8403, 149: 9026,", "148: 8403, 149: 9026, 150: %d," % floor)
ck('B9 已插入 150 项', ('150: %d,' % floor) in t2 and t2 != txt)
t2 = t2.replace("C16_FLOORS_SHA256 = '%s'" % old_sha, "C16_FLOORS_SHA256 = '%s'" % new_sha)
ck('B10 常量已换新钉', new_sha in t2)
t2 = t2.replace("GATE_VER = 'R144'", "GATE_VER = 'R145'")
ck('B11 GATE_VER 已改 R145', "GATE_VER = 'R145'" in t2)
open(GATE, 'wb').write(t2.encode('utf-8'))
new = open(GATE, 'rb').read()
ck('B12 回读含新钉与新版本号', new_sha.encode() in new and b"GATE_VER = 'R145'" in new)
json.dump({'fails': cc, 'sec150_bytes': size, 'floor': floor, 'old_sha': old_sha, 'new_sha': new_sha},
          io.open('/home/t628/projects/ra2-campaign-forge/_r145/r145k_repin.json', 'w'), indent=1)
print('\n=== C16 重钉：FAIL %d  150: %d ===' % (len(cc), floor))
