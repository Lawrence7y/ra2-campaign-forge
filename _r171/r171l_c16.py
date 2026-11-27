# -*- coding: utf-8 -*-
"""R171 L：C16 逐节 floor 重钉（169 -> 170 节），随 §2.176 落盘。

反控：旧表必须命中旧常量 bb7fe832；原 169 条逐条不变；GATE_VER / C7_TEXT / C14_TEXT / FREEZE 一字未动。
"""
import hashlib, io, json, os, re, subprocess, sys, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..'))
CD = os.path.join(ROOT, 'lead', 'next_re_20261117_r14', 'check_disc.py')
RC = os.path.join(ROOT, 'lead', 'next_re_20261117_r14', 'R14_COMMON.md')
BAK = os.path.join(ROOT, 'lead', 'next_re_20261117_r14', 'R17_LEAD_BASELINE',
                   'check_disc.py.before_r171_C16_%s.bak' % datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))

FAIL, N = [], [0]
def ck(n, c, d=''):
    N[0] += 1
    print(('PASS  ' if c else 'FAIL  ') + '%02d. %s' % (N[0], n) + (('  :: ' + str(d)) if d and not c else ''))
    if not c: FAIL.append(n)

src = io.open(CD, 'rb').read()
text = src.decode('utf-8')
CK_OLD = hashlib.sha256(src).hexdigest()
print('  改前 check_disc.py = %d B / sha %s' % (len(src), CK_OLD[:16]))

# ---- 1. 用「旧表」复算，必须命中旧常量 ---- 
m = re.search(r'^C16_FLOORS = \{(.*?)^\}', text, re.S | re.M)
tbl = dict((int(a), int(b)) for a, b in re.findall(r'^\s{4}(\d+): (\d+),', m.group(1), re.M))
OLD_SHA = 'bb7fe832464c7352bc3c3a3bd27d20d8b004c2b602e325f79f67b4f8887a23d7'
norm = lambda d: '\n'.join('%d:%d' % (k, d[k]) for k in sorted(d))
ck('N1 旧表复算命中旧 C16_FLOORS_SHA256 bb7fe832…（算法同法，硬闸）',
   hashlib.sha256(norm(tbl).encode()).hexdigest() == OLD_SHA,
   hashlib.sha256(norm(tbl).encode()).hexdigest()[:16])
ck('N1b 旧表 169 条、id 7..175（170..175 已在表内，本轮新增的是 **176**）',
   len(tbl) == 169 and min(tbl) == 7 and max(tbl) == 175, (len(tbl), min(tbl), max(tbl)))
ck('N1c 176 尚不在表内（本轮要加的就是它）', 176 not in tbl)
if FAIL:
    print('\n!! 硬闸未过，不写盘'); sys.exit(1)

# ---- 2. 量 §2.176 实际字节 ----
s = io.open(RC, encoding='utf-8', newline='').read()
i = s.find('## 2.176 ·')
j = s.find('\n## ', i + 10)
sec = s[i:j if j > 0 else len(s)]
sz = len(sec.encode('utf-8'))
print('  §2.176 实测 %d B（字符 %d）' % (sz, len(sec)))
floor = sz // 2
ck('P1 §2.176 字节 %d >= 3353（邻节最小 floor），且 floor=%d 为其一半' % (sz, floor), sz >= 3353, sz)

new = dict(tbl)
new[176] = floor
NEW_SHA = hashlib.sha256(norm(new).encode()).hexdigest()
print('  新 floor=%-6d 新 C16_FLOORS_SHA256 = %s' % (floor, NEW_SHA))

# ---- 3. 写表 ----
add = '    176: %d,\n' % floor
anchor = '    175: 3353,\n}'
ck('P2 插入锚 175:3353 行尾恰 1 处', text.count(anchor) == 1, text.count(anchor))
new = text.replace(anchor, '    175: 3353,\n' + add + '}', 1)
ck('P2b 插入后 176: 行恰 1 处', new.count('\n    176: %d,' % floor) == 1)

# 注意：C16_FLOORS 是字典字面量，键序不影响 sorted()，但插入位置要在 } 前
new = new.replace("C16_FLOORS_SHA256 = 'bb7fe832464c7352bc3c3a3bd27d20d8b004c2b602e325f79f67b4f8887a23d7'",
                  "C16_FLOORS_SHA256 = '%s'" % NEW_SHA, 1)
ck('P3 新 sha 串写入恰 1 处', new.count(NEW_SHA) == 1)

# ---- 4. 其他 pinned 常量必须一字未动 ----
for tok in ("GATE_VER = 'R166'", 'C7_TEXT_SHA256', 'C14_TEXT_SHA256', 'FREEZE_SHA256'):
    ck('P4 %s 一字未动' % tok,
       new.count(tok) == text.count(tok) and
       re.search(r'%s\s*=\s*(\S+)' % re.escape(tok.split(' =')[0]), new).group(1) ==
       re.search(r'%s\s*=\s*(\S+)' % re.escape(tok.split(' =')[0]), text).group(1))

# ---- 5. 备份 + 写 ----
with io.open(BAK, 'xb') as f:
    f.write(src)
ck('P5 备份独占创建', os.path.isfile(BAK) and io.open(BAK, 'rb').read() == src)
io.open(CD, 'wb').write(new.encode('utf-8'))
ck('P5b 回读逐字节 == 待写', io.open(CD, 'rb').read() == new.encode('utf-8'))

import difflib
_k = [t for t in difflib.SequenceMatcher(None, text.split('\n'), new.split('\n')).get_opcodes()
      if t[0] != 'equal']
print('  opcodes: %s' % [(t[0], t[1], t[2], t[3], t[4]) for t in _k])
ck('N2 变化恰 2 个 op（1 处 insert 新 floor 行 + 1 处 replace sha 常量）',
   len(_k) == 2 and _k[0][0] == 'insert' and _k[1][0] == 'replace', _k)

# ---- 6. 实跑 ----
p = subprocess.run([sys.executable, CD], capture_output=True, text=True, timeout=900)
out = p.stdout + p.stderr
ck('N3 check_disc exit 0', p.returncode == 0, out[-800:])
ck('N3b 无行首 FAIL（NOTE 里含 FAIL 字样不算）',
   not any(l.strip().startswith('FAIL') for l in out.split('\n')),
   [l for l in out.split('\n') if l.strip().startswith('FAIL')])
ck('N3c NOTE 逐字 170 sections measured (pinned 170), ... unpinned 0',
   '170 sections measured (pinned 170), hollow/deficient 0, missing 0, unpinned 0' in out,
   [l for l in out.split('\n') if 'C16 per-section' in l])
ck('N3d C16d 打印新 sha 且 OK', NEW_SHA[:16] in out and 'C16d floor-table pin' in out,
   [l for l in out.split('\n') if 'C16d' in l])

# ---- 7. 反向控：把新节删掉/改小必须 FAIL（用临时副本）----
tmp = os.path.join(HERE, '_cd_mut.py')
io.open(tmp, 'w', encoding='utf-8').write(new)
rc2 = subprocess.run([sys.executable, tmp], capture_output=True, text=True, timeout=900)
ck('N4 正控：未改副本 exit 0', rc2.returncode == 0)
# 破坏：把 170 的 floor 调大 1
mut = new.replace('    176: %d,\n}' % floor, '    176: %d,\n}' % (floor + 1), 1)
io.open(tmp, 'w', encoding='utf-8').write(mut)
rc3 = subprocess.run([sys.executable, tmp], capture_output=True, text=True, timeout=900)
ck('N5 反控：floor 改大 1 必须 FAIL（TAMPERED 或 deficient）', rc3.returncode == 1,
   (rc3.stdout + rc3.stderr)[-300:])
io.open(tmp, 'w', encoding='utf-8').write(new)
os.remove(tmp)

io.open(os.path.join(HERE, 'r171l_c16.json'), 'w', encoding='utf-8').write(json.dumps(
    {'cd_sha_before': CK_OLD, 'cd_sha_after': hashlib.sha256(io.open(CD, 'rb').read()).hexdigest(),
     'bak': os.path.relpath(BAK, ROOT), 'section_2176_bytes': sz, 'floor176': floor,
     'c16_sha_new': NEW_SHA}, indent=1))
print('\n=== %d 断言，%d FAIL ===' % (N[0], len(FAIL)))
for f in FAIL: print('  FAILED:', f)
sys.exit(1 if FAIL else 0)
