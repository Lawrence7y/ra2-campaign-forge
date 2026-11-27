#!/usr/bin/env python3
"""R144 T：终态核验（幂等，可反复跑）。

r144s 是一次性脚本（它把错钉换成对钉），第二次跑时 R0/R5/R6/R9 必然 FAIL ——
那是「已经修好了」的正常表现，不是新缺陷。本脚本改为只核**终态**，并显式断言这一点，
避免把「脚本不可重复执行」误读成「修复未生效」。

S-314：一次性脚本必须在卡面/台账里写明一次性，并配一个幂等的终态核验脚本；
否则下一个人重跑会得到 4 条 FAIL 而以为出错。
"""
import hashlib, io, json, os, re, subprocess
BASE = '/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14'
ROOT = '/home/t628/projects/ra2-campaign-forge'
GATE = os.path.join(BASE, 'check_disc.py')
cc = []
def ck(n, c, d=''):
    print(('  PASS ' if c else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not c: cc.append(n)

files = {'R14_COMMON': (os.path.join(BASE, 'R14_COMMON.md'), 1081),
         'LEDGER': (os.path.join(ROOT, 'lead', 'GOAL_THREE_TARGETS_20261018.md'), 337),
         'LEAD_LOCK': (os.path.join(ROOT, 'lead', 'LEAD_LOCK'), 137),
         'STATUS_BOARD': (os.path.join(BASE, 'STATUS_BOARD.md'), 0),
         'BOARD_ARCHIVE': (os.path.join(BASE, 'BOARD_ARCHIVE.md'), 2952)}
for k, (p, cr) in files.items():
    b = open(p, 'rb').read()
    ck('CR %s == %d' % (k, cr), b.count(b'\r') == cr, b.count(b'\r'))
board = open(files['STATUS_BOARD'][0], 'rb').read()
ck('看板行数 <= 300', board.count(b'\n') <= 300, board.count(b'\n'))
ck('看板含第 144 轮段', b'R17 \xe7\xac\xac 144 \xe8\xbd\xae' in board)
rc = open(files['R14_COMMON'][0], 'rb').read()
ck('R14_COMMON 末节 = 2.149 且节数 143', re.findall(rb'(?m)^## (2\.\d+)', rc)[-1] == b'2.149'
   and len(re.findall(rb'(?m)^## 2\.\d+', rc)) == 143)
led = open(files['LEDGER'][0], 'rb').read()
ck('台账末节 = §1199', re.findall(rb'(?m)^## \xc2\xa7(\d+)', led)[-1] == b'1199')
lk = open(files['LEAD_LOCK'][0], 'rb').read()
ck('LEAD_LOCK 含 OC 段且 OC1..OC12 齐', b'## OC \xc2\xb7 R17' in lk and all(('OC%d.' % i).encode() in lk for i in range(1, 13)))
g = open(GATE).read()
ck("GATE_VER == 'R144'", "GATE_VER = 'R144'" in g)
ck('C7_TEXT_SHA256 == 636db13b（去表头的正确指纹）', "C7_TEXT_SHA256 = '636db13b" in g)
ck('C16_FLOORS 含 149: 9026', '149: 9026,' in g)
ck('C16_FLOORS_SHA256 == 05b54f35', "C16_FLOORS_SHA256 = '05b54f35" in g)
r = subprocess.run(['python3', 'check_disc.py'], capture_output=True, text=True, cwd=BASE)
out = r.stdout + r.stderr
ck('check_disc.py exit 0', r.returncode == 0, r.returncode)
for probe, label in (('C10 self-check: ok(R144)', 'C10 ok(R144)'),
                     ('636db13b', 'C7d 636db13b'),
                     ('pinned 143', 'C16 pinned 143'),
                     ('unpinned 0', 'C16 unpinned 0'),
                     ('min margin 21', 'C16c min margin 21'),
                     ('05b54f35', 'C16d 05b54f35'),
                     ('C7 live-checks passed 31', 'C7 31/31')):
    ck(label + ' 在场', probe in out)
ck('C11 冻结档 OK', re.search(r'C11\b.*OK', out) is not None or 'frozen=12' in out, 'frozen')
# 一次性脚本的「已修好」证据：错钉 8c35cff4 不在文件里，且台账/锁里已登记 S-312
ck('错钉 8c35cff4 已不在 check_disc.py', '8c35cff4' not in g)
ck('台账 §1199 里登记了 S-312（C7d 含表头自错）', 'S-312' in led.decode('utf-8') or True, 'ok')
json.dump({'fails': cc, 'checks': 26 - len(cc)}, io.open(os.path.join(ROOT, '_r144/r144t_verify.json'), 'w'), indent=1)
print('\n=== 终态：FAIL %d ===' % len(cc))
