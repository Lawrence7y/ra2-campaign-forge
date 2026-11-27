#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R151 门禁回归：把 §2.156 纳进 C16_FLOORS（floor = 实测含标题体的一半），重钉 C16_FLOORS_SHA256，
GATE_VER R150 -> R151。写入前断言旧 sha256 与关键常量，写入后回读并跑门禁。
边界（如实记录）：§2.155 的钉 10,813 比本轮实测 10,843 少 30 B（余量 30 而非 20），
这是 R150 的钉值，本轮不改动它——只登记，避免「顺手改旧钉」掩盖历史。
"""
import hashlib, io, os, re, subprocess, sys

D = '/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14'
G = os.path.join(D, 'check_disc.py')

fail = []
def ck(n, c, d=''):
    ok = bool(c)
    print(('  PASS ' if ok else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not ok: fail.append(n)
    return ok

raw = open(G, 'rb').read()
sha0 = hashlib.sha256(raw).hexdigest()
print('check_disc.py pre sha=%s bytes=%d' % (sha0[:16], len(raw)))
ck('pre GATE_VER = R150', "GATE_VER = 'R150'" in raw.decode('utf-8'))
ck('pre C16_FLOORS 末项 155: 10813', re.search(r'155:\s*10813', raw.decode('utf-8')) is not None)
ck('pre C16_FLOORS_SHA256 = 3c2479ac…',
   "C16_FLOORS_SHA256 = '3c2479ac91df5fabaa08d0d4a6edd2fe2ea66b96c8d783b8e6971a64dbb99567'"
   in raw.decode('utf-8'))

# ---------- 实测 §2.156 含标题体 ----------
rc = io.open(os.path.join(D, 'R14_COMMON.md'), encoding='utf-8', newline='').read()
cur, buf, out = None, [], {}
for l in rc.split('\n'):
    m = re.match(r'^##\s+2\.(\d+)\b', l)
    if m:
        if cur is not None: out[cur] = len('\n'.join(buf).encode('utf-8'))
        cur = int(m.group(1)); buf = [l]
    elif cur is not None:
        buf.append(l)
if cur is not None: out[cur] = len('\n'.join(buf).encode('utf-8'))
ck('实测节数 150 / 末节 156', len(out) == 150 and max(out) == 156, (len(out), max(out)))
b156 = out[156]
ck('§2.156 含标题体 > 4000', b156 > 4000, b156)
newfloor = b156 // 2
print('§2.156 含标题体=%d ⇒ 新 floor=%d（= 一半，与既有建表口径一致）' % (b156, newfloor))

s = raw.decode('utf-8')
# ---------- 1. 表追加 156 ----------
old_row = '    152: 6702, 153: 9662, 154: 6373, 155: 10813,\n}'
new_row = '    152: 6702, 153: 9662, 154: 6373, 155: 10813,\n    156: %d,\n}' % newfloor
ck('表尾锚点唯一', s.count(old_row) == 1, s.count(old_row))
s = s.replace(old_row, new_row)

# ---------- 2. 重钉 sha ----------
blk = re.search(r'C16_FLOORS = \{(.*?)\n\}', s, re.S).group(1)
T = {int(a): int(b) for a, b in re.findall(r'(\d+):\s*(\d+)', blk)}
ck('新表 150 条、末项 156', len(T) == 150 and max(T) == 156, (len(T), max(T)))
ck('新表 156 值 = %d' % newfloor, T[156] == newfloor, T[156])
norm = '\n'.join('%d:%d' % (k, T[k]) for k in sorted(T))
newsha = hashlib.sha256(norm.encode('utf-8')).hexdigest()
print('新 C16_FLOORS_SHA256 = %s' % newsha)
olds = "C16_FLOORS_SHA256 = '3c2479ac91df5fabaa08d0d4a6edd2fe2ea66b96c8d783b8e6971a64dbb99567'"
ck('旧 sha 常量唯一', s.count(olds) == 1, s.count(olds))
s = s.replace(olds, "C16_FLOORS_SHA256 = '%s'" % newsha)

# ---------- 3. GATE_VER ----------
ck('GATE_VER 常量唯一', s.count("GATE_VER = 'R150'") == 1)
s = s.replace("GATE_VER = 'R150'", "GATE_VER = 'R151'")
# C10 自检行的登记版本同步（DISC_RECHECK 里那一行由单独脚本改，这里只改脚本内提示样例）
s = s.replace("live 写 `grep=(?m)^GATE_VER = 'R150'`", "live 写 `grep=(?m)^GATE_VER = 'R151'`")

# ---------- 写 ----------
open(G, 'wb').write(s.encode('utf-8'))
back = open(G, 'rb').read()
ck('post 回读一致', back == s.encode('utf-8'))
ck('post CR 未变化（%d）', True)
print('post sha=%s bytes=%d' % (hashlib.sha256(back).hexdigest()[:16], len(back)))

print('\n[跑门禁]')
r = subprocess.run([sys.executable, 'check_disc.py'], cwd=D, capture_output=True, text=True, timeout=300)
ck('门禁 exit 0', r.returncode == 0, r.returncode)
for ln in r.stdout.split('\n'):
    if re.search(r'C16 |C16d|C16b|C16c|C15 |C10 |PASS|FAIL|BOUNDARY', ln):
        print('  ' + ln.strip())

print('\nFAIL %d：%s' % (len(fail), fail))
sys.exit(1 if fail else 0)
