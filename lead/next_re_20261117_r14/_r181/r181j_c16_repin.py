#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r181j_c16_repin.py —— C16 重钉：185 -> 3910，186 -> 3512（= 各节实测正文字节的一半）。
fail-closed：旧表复算必须命中旧 C16_FLOORS_SHA256（110cd3e8…）才允许改。三反控都使 sha 变。
"""
import ast, hashlib, io, os, re, sys

GATE = 'check_disc.py'
BASE = 'R17_LEAD_BASELINE'
OLD_PIN = '110cd3e88853a6c609f5aa09e36e529bae42e56692e0ad26fd0f63dc97364e8a'
fails = []
def ck(n, c, d=''):
    print(('  PASS  ' if c else '  FAIL  ') + n + (('  ' + str(d)) if d else ''))
    if not c: fails.append(n)

src = io.open(GATE, encoding='utf-8', newline='').read()
SHA = hashlib.sha256(src.encode('utf-8')).hexdigest()
ck('P1 CR=0', src.count('\r') == 0, src.count('\r'))

m = re.search(r'C16_FLOORS = \{\n(.*?)\n\}', src, re.S)
ck('P2 C16_FLOORS 表可定位', bool(m))
floors = dict((int(a), int(b)) for a, b in re.findall(r'(\d+):\s*(\d+),', m.group(1)))
ck('P3 旧表 178 条', len(floors) == 178, len(floors))
norm = '\n'.join('%d:%d' % (k, floors[k]) for k in sorted(floors))
cur_pin = hashlib.sha256(norm.encode()).hexdigest()
ck('P4 旧表复算命中旧 pin（fail-closed 硬闸）', cur_pin == OLD_PIN, cur_pin[:16])
ck('P5 表中尚无 185/186', 185 not in floors and 186 not in floors, (185 in floors, 186 in floors))

# 实测两节正文字节（按 check_disc 同一算法）
rc = io.open('R14_COMMON.md', encoding='utf-8', newline='').read()
_b = []; _cur = None; _buf = []
for l in rc.split('\n'):
    mm = re.match(r'^##\s+2\.(\d+)\b', l)
    if mm:
        if _cur is not None: _b.append((_cur, len('\n'.join(_buf).encode('utf-8'))))
        _cur = int(mm.group(1)); _buf = [l]
    elif _cur is not None:
        _buf.append(l)
if _cur is not None: _b.append((_cur, len('\n'.join(_buf).encode('utf-8'))))
d = dict(_b)
B185, B186 = d[185], d[186]
ck('P6 §2.185 实测正文 7,821 B', B185 == 7821, B185)
ck('P7 §2.186 实测正文 7,025 B', B186 == 7025, B186)
F185, F186 = B185 // 2, B186 // 2
ck('P8 门槛=实测的一半：3,910 / 3,512', (F185, F186) == (3910, 3512), (F185, F186))

new_floors = dict(floors); new_floors[185] = F185; new_floors[186] = F186
new_norm = '\n'.join('%d:%d' % (k, new_floors[k]) for k in sorted(new_floors))
NEW_PIN = hashlib.sha256(new_norm.encode()).hexdigest()
ck('C1 新表 180 条', len(new_floors) == 180, len(new_floors))
ck('C2 新 pin 与旧 pin 不同', NEW_PIN != OLD_PIN, NEW_PIN[:16])

# 三反控：任一处改动都必须使 sha 变
t1 = dict(new_floors); t1[185] += 1
ck('R1 反控：185 门槛 +1 ⇒ sha 变',
   hashlib.sha256(('\n'.join('%d:%d' % (k, t1[k]) for k in sorted(t1))).encode()).hexdigest() != NEW_PIN)
t2 = dict(new_floors); del t2[186]
ck('R2 反控：删掉 186 ⇒ sha 变',
   hashlib.sha256(('\n'.join('%d:%d' % (k, t2[k]) for k in sorted(t2))).encode()).hexdigest() != NEW_PIN)
t3 = dict(new_floors); t3[184] += 1
ck('R3 反控：改既有的 184 ⇒ sha 变',
   hashlib.sha256(('\n'.join('%d:%d' % (k, t3[k]) for k in sorted(t3))).encode()).hexdigest() != NEW_PIN)

# 构造新表文本：在 184: 3637, 之后插入两行（保持既有缩进 4 空格）
old_tail = '   184: 3637,\n}'
ck('C3 表尾锚点唯一', src.count(old_tail) == 1, src.count(old_tail))
new_tail = ('   184: 3637,\n'
            '   185: %d,\n'
            '   186: %d,\n}' % (F185, F186))
new = src.replace(old_tail, new_tail)
ck('C4 旧 C16_FLOORS_SHA256 出现恰 1 次', src.count(OLD_PIN) == 1, src.count(OLD_PIN))
new = new.replace(OLD_PIN, NEW_PIN)
ck('C5 新文件含新 pin', NEW_PIN in new)
ck('C6 新文件 ast 可解析', (lambda: (ast.parse(new), True)[1])())
# 复算新表 sha 与新 pin 一致
m2 = re.search(r'C16_FLOORS = \{\n(.*?)\n\}', new, re.S)
f2 = dict((int(a), int(b)) for a, b in re.findall(r'(\d+):\s*(\d+),', m2.group(1)))
n2 = '\n'.join('%d:%d' % (k, f2[k]) for k in sorted(f2))
ck('C7 新表复算 == 新 pin', hashlib.sha256(n2.encode()).hexdigest() == NEW_PIN, len(f2))

if fails:
    print('拒绝写盘'); print('[exit 1] %d FAIL' % len(fails)); sys.exit(1)

import datetime
ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
bak = os.path.join(BASE, 'check_disc.py.before_r181_c16_%s.bak' % ts)
fd = os.open(bak, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
os.write(fd, src.encode('utf-8')); os.close(fd)
ck('W1 备份等于旧文件', open(bak, 'rb').read() == src.encode('utf-8'), os.path.basename(bak))
ck('W2 写前 sha 未变', hashlib.sha256(open(GATE, 'rb').read()).hexdigest() == SHA)
io.open(GATE, 'w', encoding='utf-8', newline='\n').write(new)
rb = open(GATE, 'rb').read()
ck('W3 回读 CR=0', rb.count(b'\r') == 0)
ck('W4 回读含新 pin', NEW_PIN.encode() in rb)
print('bytes %d -> %d' % (len(src.encode()), len(rb)))
print('OLD_PIN=%s' % OLD_PIN)
print('NEW_PIN=%s' % NEW_PIN)
print('SHA=%s' % hashlib.sha256(rb).hexdigest())
print('fails=%d' % len(fails))
if fails: print(repr(fails)); sys.exit(1)
print('[exit 0]')
