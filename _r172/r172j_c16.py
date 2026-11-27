# -*- coding: utf-8 -*-
"""R172 J：C16 逐节 floor 重钉（170 -> 171 节），随 §2.177 落盘。

反控：旧表复算必须命中旧常量 141afe4431a71eb5；原 170 条逐条不变；GATE_VER / C7_TEXT / C14_TEXT / FREEZE 一字未动；
      把 id 177 的 floor 调大 1 必 FAIL。
"""
import datetime, hashlib, io, json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..'))
CD = os.path.join(ROOT, 'lead', 'next_re_20261117_r14', 'check_disc.py')
RC = os.path.join(ROOT, 'lead', 'next_re_20261117_r14', 'R14_COMMON.md')
BAK = os.path.join(ROOT, 'lead', 'next_re_20261117_r14', 'R17_LEAD_BASELINE',
                   'check_disc.py.before_r172_C16_%s.bak' % datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))

FAIL, N = [], [0]
def ck(n, c, d=''):
    N[0] += 1
    print(('PASS  ' if c else 'FAIL  ') + '%02d. %s' % (N[0], n) + (('  :: ' + str(d)) if d and not c else ''))
    if not c: FAIL.append(n)

src = io.open(CD, 'rb').read(); text = src.decode('utf-8')
print('  改前 check_disc.py = %d B / sha %s' % (len(src), hashlib.sha256(src).hexdigest()[:16]))
m = re.search(r'^C16_FLOORS = \{(.*?)^\}', text, re.S | re.M)
tbl = dict((int(a), int(b)) for a, b in re.findall(r'^\s{4}(\d+): (\d+),', m.group(1), re.M))
OLD_SHA = '141afe4431a71eb50616b1762662204fdaa8966e9bf23a9d63c4fbd2ae44aec8'
norm = lambda d: '\n'.join('%d:%d' % (k, d[k]) for k in sorted(d))
ck('N1 旧表复算命中旧 C16_FLOORS_SHA256 141afe44…（硬闸，未命中不写盘）',
   hashlib.sha256(norm(tbl).encode()).hexdigest() == OLD_SHA,
   hashlib.sha256(norm(tbl).encode()).hexdigest()[:16])
ck('N1b 旧表 170 条、id 7..176', len(tbl) == 170 and min(tbl) == 7 and max(tbl) == 176, (len(tbl), min(tbl), max(tbl)))
ck('N1c 177 尚不在表内', 177 not in tbl)
if FAIL:
    print('\n!! 硬闸未过 —— fail-closed，不写盘'); sys.exit(1)

s = io.open(RC, encoding='utf-8', newline='').read()
i = s.find('## 2.177 ·')
j = s.find('\n## ', i + 10)
sec = s[i:j if j > 0 else len(s)]
sz = len(sec.encode('utf-8'))
floor = sz // 2
print('  §2.177 实测 %d B（字符 %d）⇒ floor %d' % (sz, len(sec), floor))
ck('P1 §2.177 字节 %d >= 2777（邻节 floor）' % sz, sz >= 2777, sz)

new_tbl = dict(tbl); new_tbl[177] = floor
NEW_SHA = hashlib.sha256(norm(new_tbl).encode()).hexdigest()
print('  新 C16_FLOORS_SHA256 = %s' % NEW_SHA)
anchor = '    176: 2777,\n}'
ck('P2 插入锚 176:2777 行尾恰 1 处', text.count(anchor) == 1)
new = text.replace(anchor, '    176: 2777,\n    177: %d,\n}' % floor, 1)
ck('P2b 插入后 177 行恰 1 处', new.count('\n    177: %d,' % floor) == 1)
new = new.replace("C16_FLOORS_SHA256 = '%s'" % OLD_SHA, "C16_FLOORS_SHA256 = '%s'" % NEW_SHA, 1)
ck('P3 新 sha 串写入恰 1 处', new.count(NEW_SHA) == 1)
for tok in ("GATE_VER = 'R166'", 'C7_TEXT_SHA256', 'C14_TEXT_SHA256', 'FREEZE_SHA256'):
    name = tok.split(' =')[0]
    ck('P4 %s 一字未动' % name,
       re.search(r'%s\s*=\s*(\S+)' % re.escape(name), new).group(1) == re.search(r'%s\s*=\s*(\S+)' % re.escape(name), text).group(1))
ck('P4b 原 170 条逐条不变',
   all(new_tbl[k] == tbl[k] for k in tbl) and set(new_tbl) - set(tbl) == {177})

with io.open(BAK, 'xb') as f: f.write(src)
ck('P5 备份独占创建', os.path.isfile(BAK) and io.open(BAK, 'rb').read() == src)
io.open(CD, 'wb').write(new.encode('utf-8'))
ck('P5b 回读逐字节 == 待写', io.open(CD, 'rb').read() == new.encode('utf-8'))

import difflib
ops = [t for t in difflib.SequenceMatcher(None, text.split('\n'), new.split('\n')).get_opcodes() if t[0] != 'equal']
print('  opcodes: %s' % [(t[0], t[1], t[2], t[3], t[4]) for t in ops])
ck('N2 变化恰 2 个 op（1 insert 新 floor 行 + 1 replace sha 常量）',
   len(ops) == 2 and ops[0][0] == 'insert' and ops[1][0] == 'replace', ops)

def run(a, t=900):
    r = subprocess.run([sys.executable] + a, capture_output=True, text=True, timeout=t); return r.returncode, r.stdout + r.stderr
rc, out = run([CD])
ck('N3 check_disc exit 0', rc == 0, out[-600:])
ck('N3b 无行首 FAIL', not any(l.strip().startswith('FAIL') for l in out.split('\n')),
   [l for l in out.split('\n') if l.strip().startswith('FAIL')])
ck('N3c NOTE 逐字 171 sections measured (pinned 171) … unpinned 0',
   '171 sections measured (pinned 171), hollow/deficient 0, missing 0, unpinned 0' in out,
   [l for l in out.split('\n') if 'C16 per-section' in l])
ck('N3d C16d 打印新 sha 且 OK', NEW_SHA[:16] in out, [l for l in out.split('\n') if 'C16d' in l])

tmp = os.path.join(HERE, '_cd_mut177.py')
io.open(tmp, 'w', encoding='utf-8').write(new)
rc2, _ = run([tmp]); ck('N4 正控：未改副本 exit 0', rc2 == 0)
mut = new.replace('    177: %d,\n}' % floor, '    177: %d,\n}' % (floor + 1), 1)
io.open(tmp, 'w', encoding='utf-8').write(mut)
rc3, o3 = run([tmp]); ck('N5 反控：177 的 floor 调大 1 必 FAIL', rc3 == 1, o3[-300:])
os.remove(tmp)

io.open(os.path.join(HERE, 'r172j_c16.json'), 'w', encoding='utf-8').write(json.dumps(
    {'cd_sha_before': hashlib.sha256(src).hexdigest(), 'cd_sha_after': hashlib.sha256(io.open(CD, 'rb').read()).hexdigest(),
     'bak': os.path.relpath(BAK, ROOT), 'sec_2177_bytes': sz, 'floor177': floor,
     'c16_sha_old': OLD_SHA, 'c16_sha_new': NEW_SHA, 'entries': len(new_tbl)}, indent=1))
print('\n=== %d 断言，%d FAIL ===' % (N[0], len(FAIL)))
for f in FAIL: print('  FAILED:', f)
sys.exit(1 if FAIL else 0)
