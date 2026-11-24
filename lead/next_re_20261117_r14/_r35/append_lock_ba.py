# -*- coding: utf-8 -*-
"""追加 LEAD_LOCK 的 BA 段（第 35 轮）。不变量：LEAD_LOCK CRLF 必须保持 137。"""
import io, os, hashlib, datetime

ROOT = r'D:\Project\ra2-campaign-forge'
LL   = os.path.join(ROOT, 'lead', 'LEAD_LOCK')
SEC  = os.path.join(ROOT, 'lead', 'next_re_20261117_r14', '_r35', 'lock_ba.md')
BK   = os.path.join(ROOT, 'lead', 'next_re_20261117_r14', 'R17_LEAD_BASELINE')

def read(p): return io.open(p, encoding='utf-8', newline='').read()

before = read(LL)
crlf0 = before.count('\r\n')
bytes0 = os.path.getsize(LL)
assert crlf0 == 137, crlf0
sha0 = hashlib.sha256(io.open(LL, 'rb').read()).hexdigest().upper()
print('BEFORE bytes=%d CRLF=%d sha=%s' % (bytes0, crlf0, sha0))
assert '## BA ·' not in before, 'BA section already present'

sec = read(SEC)
assert '\r' not in sec

ts = datetime.datetime.now().strftime('%H%M%S')
bk = os.path.join(BK, 'LEAD_LOCK.before_BA_%s' % ts)
with open(bk, 'xb') as f:
    f.write(io.open(LL, 'rb').read())
assert hashlib.sha256(io.open(bk, 'rb').read()).hexdigest().upper() == sha0
print('backup', os.path.basename(bk), os.path.getsize(bk))

sep = '' if before.endswith('\n') else '\n'
new = before + sep + '\n' + sec.rstrip('\n') + '\n'
assert new.count('\r\n') == 137, new.count('\r\n')

with open(LL, 'wb') as f:
    f.write(new.encode('utf-8'))

back = read(LL)
assert back == new, 'readback mismatch'
assert back.count('\r\n') == 137
assert back.startswith(before[:5000])
print('AFTER  bytes=%d CRLF=%d' % (os.path.getsize(LL), back.count('\r\n')))
print('delta bytes = +%d' % (os.path.getsize(LL) - bytes0))
print('OK')
