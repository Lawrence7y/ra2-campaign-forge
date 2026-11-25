# -*- coding: utf-8 -*-
"""R128s：按 R124-R127 既有做法把新增的 2.132 纳进 C16_FLOORS 并重钉摘要。

半量规则：floor = 实测正文字节数的一半（向下取整）。
本轮 2.132 实测 11997 B -> 5998。
"""
import io, os, sys, hashlib
ROOT = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
BK = os.path.join(R14, 'R17_LEAD_BASELINE')
GATE = os.path.join(R14, 'check_disc.py')
RC = os.path.join(R14, 'R14_COMMON.md')
TS = '20261125_r128_pin'

# 实测
s = io.open(RC, encoding='utf-8').read()
i = s.index('## 2.132')
j = s.find('\n## 2.', i + 5)
sec_bytes = len(s[i:j].encode('utf-8'))
floor = sec_bytes // 2
print('  2.132 bytes=%d -> floor=%d' % (sec_bytes, floor))
assert sec_bytes == 11997 and floor == 5998, 'measure drift'

old = io.open(GATE, 'rb').read()
src = old.decode('utf-8')
OLD_TAIL = '    127: 3932, 128: 4001, 129: 3629, 130: 3722, 131: 5958\n'
NEW_TAIL = '    127: 3932, 128: 4001, 129: 3629, 130: 3722, 131: 5958,\n    132: %d\n' % floor
assert OLD_TAIL in src, 'floor table tail not found'
new = src.replace(OLD_TAIL, NEW_TAIL, 1)

# 重算表摘要：逐 id:floor 规范化串
import re
m = re.search(r'C16_FLOORS = \{(.*?)\n\}', new, re.S)
body = m.group(1)
pairs = {}
for mm in re.finditer(r'(\d+):\s*(\d+)', body):
    pairs[int(mm.group(1))] = int(mm.group(2))
norm = '\n'.join('%d:%d' % (k, pairs[k]) for k in sorted(pairs))
new_sha = hashlib.sha256(norm.encode('utf-8')).hexdigest()
print('  entries=%d new_sha=%s' % (len(pairs), new_sha[:16]))

OLD_SHA = 'a87a240c10947077edd5c9d9965c7874f401fd988591c1bd7040a61c5154dc43'
assert OLD_SHA in new, 'old sha constant not found'
new = new.replace(OLD_SHA, new_sha, 1)

# 备份 + 写入
dst = os.path.join(BK, 'r128_pin_check_disc.py.%s.bak' % TS)
fd = os.open(dst, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
try: os.write(fd, old)
finally: os.close(fd)
print('  backup ->', os.path.basename(dst))

nb = new.encode('utf-8')
io.open(GATE, 'wb').write(nb)
rb = io.open(GATE, 'rb').read()
assert rb == nb, 'readback mismatch'
assert rb.count(b'\r') == old.count(b'\r'), 'CR drifted'
print('  WROTE check_disc.py %s -> %s (%d -> %d bytes)'
      % (hashlib.sha256(old).hexdigest()[:16], hashlib.sha256(rb).hexdigest()[:16],
         len(old), len(rb)))
