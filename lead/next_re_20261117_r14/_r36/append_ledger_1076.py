# -*- coding: utf-8 -*-
"""台账追加 §1076。不变量：CRLF 保持 337。路径写死（不用字符串替换）。"""
import io, os, hashlib, datetime, re

ROOT = r'D:\Project\ra2-campaign-forge'
LED  = os.path.join(ROOT, 'lead', 'GOAL_THREE_TARGETS_20261018.md')
SEC  = os.path.join(ROOT, 'lead', 'next_re_20261117_r14', '_r36', 'ledger_1076.md')
BK   = os.path.join(ROOT, 'lead', 'next_re_20261117_r14', 'R17_LEAD_BASELINE')

assert os.path.exists(SEC), SEC
before = io.open(LED, encoding='utf-8', newline='').read()
crlf0 = before.count('\r\n'); bytes0 = os.path.getsize(LED)
assert crlf0 == 337, crlf0
sha0 = hashlib.sha256(io.open(LED, 'rb').read()).hexdigest().upper()
print('BEFORE bytes=%d CRLF=%d sha=%s' % (bytes0, crlf0, sha0))

secs = [int(m) for m in re.findall(r'(?m)^##\s*§(\d{4})', before)]
assert max(secs) == 1075, max(secs)
assert 1076 not in secs
print('max before = §%d, sections=%d' % (max(secs), len(secs)))

sec = io.open(SEC, encoding='utf-8', newline='').read()
assert '\r' not in sec
assert sec.lstrip().startswith('## §1076')

ts = datetime.datetime.now().strftime('%H%M%S')
bk = os.path.join(BK, 'LEDGER.before_1076_%s.md' % ts)
with open(bk, 'xb') as f:
    f.write(io.open(LED, 'rb').read())
assert hashlib.sha256(io.open(bk, 'rb').read()).hexdigest().upper() == sha0
print('backup', os.path.basename(bk))

sep = '' if before.endswith('\n') else '\n'
new = before + sep + '\n' + sec.rstrip('\n') + '\n'
assert new.count('\r\n') == 337, new.count('\r\n')

with open(LED, 'wb') as f:
    f.write(new.encode('utf-8'))

back = io.open(LED, encoding='utf-8', newline='').read()
assert back == new
assert back.count('\r\n') == 337
assert back.startswith(before[:3000])
secs2 = [int(m) for m in re.findall(r'(?m)^##\s*§(\d{4})', back)]
assert max(secs2) == 1076
assert secs2.count(1076) == 1
print('AFTER  bytes=%d CRLF=%d max=§%d' % (os.path.getsize(LED), back.count('\r\n'), max(secs2)))
print('delta bytes = +%d' % (os.path.getsize(LED) - bytes0))
print('OK')
