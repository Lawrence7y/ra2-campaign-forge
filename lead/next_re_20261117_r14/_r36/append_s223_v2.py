# -*- coding: utf-8 -*-
"""把 §2.23 追加到 R14_COMMON.md（路径写死，不做字符串替换——上一版因此重复追加了 §2.22）。
额外断言：§2.22 恰 1 次、§2.23 恰 1 次（追加后）、CRLF 保持 1081。
"""
import io, os, hashlib, datetime

ROOT = r'D:\Project\ra2-campaign-forge'
R14  = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
TGT  = os.path.join(R14, 'R14_COMMON.md')
SEC  = os.path.join(R14, '_r36', 's223.md')
BK   = os.path.join(R14, 'R17_LEAD_BASELINE')

assert os.path.exists(SEC), SEC
before = io.open(TGT, encoding='utf-8', newline='').read()
crlf0 = before.count('\r\n')
bytes0 = os.path.getsize(TGT)
assert crlf0 == 1081, crlf0
sha0 = hashlib.sha256(io.open(TGT, 'rb').read()).hexdigest().upper()
print('BEFORE bytes=%d CRLF=%d sha=%s' % (bytes0, crlf0, sha0))

# 前置断言：当前只该有 1 个 §2.22、0 个 §2.23
n222 = len([1 for l in before.split('\n') if l.startswith('## 2.22')])
n223 = len([1 for l in before.split('\n') if l.startswith('## 2.23')])
assert n222 == 1, n222
assert n223 == 0, n223
print('pre-check: §2.22=%d §2.23=%d' % (n222, n223))

sec = io.open(SEC, encoding='utf-8', newline='').read()
assert '\r' not in sec
assert sec.lstrip().startswith('## 2.23'), sec[:60]

ts = datetime.datetime.now().strftime('%H%M%S')
bk = os.path.join(BK, 'R14_COMMON.before_s223_%s.md' % ts)
with open(bk, 'xb') as f:
    f.write(io.open(TGT, 'rb').read())
assert hashlib.sha256(io.open(bk, 'rb').read()).hexdigest().upper() == sha0
print('backup', os.path.basename(bk))

sep = '' if before.endswith('\n') else '\n'
new = before + sep + '\n' + sec.rstrip('\n') + '\n'
assert new.count('\r\n') == 1081, new.count('\r\n')

# 后置断言（写盘前）
assert len([1 for l in new.split('\n') if l.startswith('## 2.22')]) == 1
assert len([1 for l in new.split('\n') if l.startswith('## 2.23')]) == 1
# 追加内容必须只有 §2.23 那一份（用开头摘要反查）
assert new.count('### 一 · 结果：15 行含引用') == 1

with open(TGT, 'wb') as f:
    f.write(new.encode('utf-8'))

back = io.open(TGT, encoding='utf-8', newline='').read()
assert back == new, 'readback mismatch'
assert back.count('\r\n') == 1081
assert back.startswith(before[:3000])
assert len([1 for l in back.split('\n') if l.startswith('## 2.22')]) == 1
assert len([1 for l in back.split('\n') if l.startswith('## 2.23')]) == 1
print('AFTER  bytes=%d CRLF=%d' % (os.path.getsize(TGT), back.count('\r\n')))
print('delta bytes = +%d' % (os.path.getsize(TGT) - bytes0))
print('OK')
