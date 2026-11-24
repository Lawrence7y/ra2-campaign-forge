# -*- coding: utf-8 -*-
"""追加 LEAD_LOCK 的 BB 段（第 36 轮）。不变量：CRLF 保持 137。路径写死。"""
import io, os, hashlib, datetime

ROOT = r'D:\Project\ra2-campaign-forge'
LL   = os.path.join(ROOT, 'lead', 'LEAD_LOCK')
SEC  = os.path.join(ROOT, 'lead', 'next_re_20261117_r14', '_r36', 'lock_bb.md')
BK   = os.path.join(ROOT, 'lead', 'next_re_20261117_r14', 'R17_LEAD_BASELINE')

assert os.path.exists(SEC), SEC
before = io.open(LL, encoding='utf-8', newline='').read()
crlf0 = before.count('\r\n'); bytes0 = os.path.getsize(LL)
assert crlf0 == 137, crlf0
sha0 = hashlib.sha256(io.open(LL, 'rb').read()).hexdigest().upper()
print('BEFORE bytes=%d CRLF=%d sha=%s' % (bytes0, crlf0, sha0))
assert '## BB ·' not in before

sec = io.open(SEC, encoding='utf-8', newline='').read()
assert '\r' not in sec
assert sec.lstrip().startswith('## BB ·')

ts = datetime.datetime.now().strftime('%H%M%S')
bk = os.path.join(BK, 'LEAD_LOCK.before_BB_%s' % ts)
with open(bk, 'xb') as f:
    f.write(io.open(LL, 'rb').read())
assert hashlib.sha256(io.open(bk, 'rb').read()).hexdigest().upper() == sha0
print('backup', os.path.basename(bk))

sep = '' if before.endswith('\n') else '\n'
new = before + sep + '\n' + sec.rstrip('\n') + '\n'
assert new.count('\r\n') == 137, new.count('\r\n')

with open(LL, 'wb') as f:
    f.write(new.encode('utf-8'))

back = io.open(LL, encoding='utf-8', newline='').read()
assert back == new
assert back.count('\r\n') == 137
assert back.startswith(before[:5000])
assert len([1 for l in back.split('\n') if l.startswith('## BB ·')]) == 1
print('AFTER  bytes=%d CRLF=%d' % (os.path.getsize(LL), back.count('\r\n')))
print('delta bytes = +%d' % (os.path.getsize(LL) - bytes0))
print('OK')
