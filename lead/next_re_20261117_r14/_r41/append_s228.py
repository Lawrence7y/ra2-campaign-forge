# -*- coding: utf-8 -*-
"""把 _r40\s228_DRAFT_not_appended.md 里的 `## 2.28` 段追加进 R14_COMMON.md。
纪律：从草稿里剥掉状态说明头；备份 wx 独占；断言旧 sha；CRLF 保持 1081；回读校验。
"""
import io, os, hashlib, datetime

ROOT = r'D:\Project\ra2-campaign-forge'
R14  = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
TGT  = os.path.join(R14, 'R14_COMMON.md')
DRAFT = os.path.join(R14, '_r40', 's228_DRAFT_not_appended.md')
BK   = os.path.join(R14, 'R17_LEAD_BASELINE')

draft = io.open(DRAFT, encoding='utf-8', newline='').read()
assert '\r' not in draft
lines = draft.split('\n')
start = None
for i, l in enumerate(lines):
    if l.startswith('## 2.28'):
        start = i
        break
assert start is not None, 'section 2.28 not found in draft'
sec = '\n'.join(lines[start:])
# 去掉草稿末尾可能残留的元信息（本段是最后一节，无需裁剪）
assert '## 2.' not in sec[3:], 'draft contains a later section?'
print('section lines =', len(sec.split('\n')), ' bytes =', len(sec.encode()))

before = io.open(TGT, encoding='utf-8', newline='').read()
crlf0 = before.count('\r\n'); bytes0 = os.path.getsize(TGT)
assert crlf0 == 1081, crlf0
sha0 = hashlib.sha256(io.open(TGT, 'rb').read()).hexdigest().upper()
print('BEFORE bytes=%d CRLF=%d sha=%s' % (bytes0, crlf0, sha0))
assert '## 2.28' not in before, 'section 2.28 already present'

ts = datetime.datetime.now().strftime('%H%M%S')
bk = os.path.join(BK, 'R14_COMMON.before_s228_%s.md' % ts)
with open(bk, 'xb') as f:
    f.write(io.open(TGT, 'rb').read())
assert hashlib.sha256(io.open(bk, 'rb').read()).hexdigest().upper() == sha0
print('backup', os.path.basename(bk))

sep = '' if before.endswith('\n') else '\n'
new = before + sep + '\n' + sec.rstrip('\n') + '\n'
assert new.count('\r\n') == 1081, new.count('\r\n')
assert len([1 for l in new.split('\n') if l.startswith('## 2.28')]) == 1
for ch in ('\u200b', '\u200c', '\u200d', '\ufeff', '\u2060', '\u00a0'):
    assert ch not in sec, 'invisible char U+%04X in section' % ord(ch)

with open(TGT, 'wb') as f:
    f.write(new.encode('utf-8'))

back = io.open(TGT, encoding='utf-8', newline='').read()
assert back == new
assert back.count('\r\n') == 1081
assert back.startswith(before[:4000])
print('AFTER  bytes=%d CRLF=%d (+%d)' % (os.path.getsize(TGT), back.count('\r\n'), os.path.getsize(TGT) - bytes0))
print('OK')
