# -*- coding: utf-8 -*-
"""台账追加 §1075。不变量：台账 CRLF 必须保持 337。
纪律：备份 wx 独占 + 唯一名 → 断言旧 sha → 一次性写入 → 回读校验。
"""
import io, os, hashlib, datetime

ROOT = r'D:\Project\ra2-campaign-forge'
LED  = os.path.join(ROOT, 'lead', 'GOAL_THREE_TARGETS_20261018.md')
SEC  = os.path.join(ROOT, 'lead', 'next_re_20261117_r14', '_r35', 'ledger_1075.md')
BK   = os.path.join(ROOT, 'lead', 'next_re_20261117_r14', 'R17_LEAD_BASELINE')

def read(p): return io.open(p, encoding='utf-8', newline='').read()

before = read(LED)
crlf0 = before.count('\r\n')
bytes0 = os.path.getsize(LED)
assert crlf0 == 337, crlf0
sha0 = hashlib.sha256(io.open(LED, 'rb').read()).hexdigest().upper()
print('BEFORE bytes=%d CRLF=%d sha=%s' % (bytes0, crlf0, sha0))

# 台账 max 必须仍是 §1074
import re
secs = [int(m) for m in re.findall(r'(?m)^##\s*§(\d{4})', before)]
assert max(secs) == 1074, max(secs)
assert 1075 not in secs
print('max section before = §%d, sections=%d' % (max(secs), len(secs)))

sec = read(SEC)
assert '\r' not in sec
assert '## §1075' in sec

ts = datetime.datetime.now().strftime('%H%M%S')
bk = os.path.join(BK, 'LEDGER.before_1075_%s.md' % ts)
with open(bk, 'xb') as f:
    f.write(io.open(LED, 'rb').read())
sha_bk = hashlib.sha256(io.open(bk, 'rb').read()).hexdigest().upper()
assert sha_bk == sha0
print('backup', os.path.basename(bk), os.path.getsize(bk))

sep = '' if before.endswith('\n') else '\n'
new = before + sep + '\n' + sec.rstrip('\n') + '\n'
assert new.count('\r\n') == 337, new.count('\r\n')

with open(LED, 'wb') as f:
    f.write(new.encode('utf-8'))

back = read(LED)
assert back == new, 'readback mismatch'
assert back.count('\r\n') == 337
assert back.startswith(before[:3000])
secs2 = [int(m) for m in re.findall(r'(?m)^##\s*§(\d{4})', back)]
assert max(secs2) == 1075, max(secs2)
assert secs2.count(1075) == 1
print('AFTER  bytes=%d CRLF=%d max=§%d' % (os.path.getsize(LED), back.count('\r\n'), max(secs2)))
print('delta bytes = +%d' % (os.path.getsize(LED) - bytes0))
print('OK')
