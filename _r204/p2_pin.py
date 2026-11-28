#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R204 p2：C16_FLOORS 重钉（纳入新节 209），并重算 C16_FLOORS_SHA256。
实测 2.209 节字节 = 10626，floor = 10626//2 = 5313。
"""
import hashlib, os, re, time
P = '/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14/check_disc.py'
BASE = '/home/t628/projects/ra2-campaign-forge/R17_LEAD_BASELINE'
src = open(P, 'rb').read()
old_sha = hashlib.sha256(src).hexdigest()
print('OLD check_disc.py sha=%s bytes=%d' % (old_sha[:16], len(src)))
b = src.decode('utf-8')
OLD_BLOCK = """    206: 3707,
    207: 5538,
    208: 3885,
}"""
NEW_BLOCK = """    206: 3707,
    207: 5538,
    208: 3885,
    209: 5313,
}"""
assert b.count(OLD_BLOCK) == 1, b.count(OLD_BLOCK)
m0 = re.search(r'C16_FLOORS = \{(.*?)\n\}', b, re.S)
n0 = len([l for l in m0.group(1).split('\n') if l.strip() and not l.strip().startswith('#')])
print('OLD floors entries=%d' % n0)
b2 = b.replace(OLD_BLOCK, NEW_BLOCK)
m = re.search(r'C16_FLOORS = \{(.*?)\n\}', b2, re.S)
floors = {}
for line in m.group(1).split('\n'):
    line = line.strip()
    if not line or line.startswith('#'): continue
    k, v = line.rstrip(',').split(':')
    floors[int(k)] = int(v)
norm = '\n'.join('%d:%d' % (k, floors[k]) for k in sorted(floors))
newsha = hashlib.sha256(norm.encode()).hexdigest()
olds = re.search(r"C16_FLOORS_SHA256 = '([0-9a-f]{64})'", b2).group(1)
assert b2.count(olds) == 1
b2 = b2.replace(olds, newsha)
assert len(floors) == n0 + 1, (len(floors), n0)
assert floors[209] == 5313
STAMP = time.strftime('%Y%m%d_%H%M%S')
bak = '%s/check_disc.py.%s.bak' % (BASE, STAMP)
fd = os.open(bak, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
os.write(fd, src); os.close(fd)
assert hashlib.sha256(open(bak, 'rb').read()).hexdigest() == old_sha
open(P, 'wb').write(b2.encode('utf-8'))
rb = open(P, 'rb').read()
assert hashlib.sha256(rb) != old_sha
print('NEW sha=%s floors=%d 209=%d pin %s -> %s' % (
    hashlib.sha256(rb).hexdigest()[:16], len(floors), floors[209], olds[:16], newsha[:16]))
print('OK')
