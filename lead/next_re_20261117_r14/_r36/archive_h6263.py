# -*- coding: utf-8 -*-
"""H62/H63 归档：把看板第 29、30 两轮段逐字搬入 BOARD_ARCHIVE，各换 1 行指针。
不变量：BOARD_ARCHIVE CRLF=2952、STATUS_BOARD CRLF=0。新增内容必须全 LF。
"""
import io, os, hashlib, datetime

ROOT = r'D:\Project\ra2-campaign-forge'
R14  = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
BRD  = os.path.join(R14, 'STATUS_BOARD.md')
ARC  = os.path.join(R14, 'BOARD_ARCHIVE.md')
BK   = os.path.join(R14, 'R17_LEAD_BASELINE')

def read(p): return io.open(p, encoding='utf-8', newline='').read()

brd, arc = read(BRD), read(ARC)
assert brd.count('\r\n') == 0
assert arc.count('\r\n') == 2952, arc.count('\r\n')

bl = brd.split('\n')

def bounds(prefix):
    s = None
    for i, x in enumerate(bl):
        if x.startswith(prefix):
            s = i; break
    assert s is not None, prefix
    e = len(bl)
    for j in range(s + 1, len(bl)):
        if bl[j].startswith('## '):
            e = j; break
    b = bl[s:e]
    while b and b[-1].strip() == '':
        b.pop()
    return s, e, b

segs = []
for rnd in (29, 30):
    s, e, b = bounds('## 🔴 R17 第 %d 轮' % rnd)
    assert len(b) >= 10, (rnd, len(b))
    segs.append((rnd, s, e, b))
    print('round %d: L%d..L%d = %d lines' % (rnd, s + 1, s + len(b), len(b)))

# 从后往前替换，避免索引位移
ts = datetime.datetime.now().strftime('%H%M%S')
bk_b = os.path.join(BK, 'STATUS_BOARD.before_H6263_%s.md' % ts)
bk_a = os.path.join(BK, 'BOARD_ARCHIVE.before_H6263_%s.md' % ts)
for srcp, dstp in ((BRD, bk_b), (ARC, bk_a)):
    with open(dstp, 'xb') as f:
        f.write(io.open(srcp, 'rb').read())
    assert hashlib.sha256(io.open(dstp, 'rb').read()).digest() == hashlib.sha256(io.open(srcp, 'rb').read()).digest()
print('backups ok')

# 归档：逐段逐字追加
new_arc = arc
for rnd, s, e, b in segs:
    seg_txt = '\n'.join(b)
    assert '\r' not in seg_txt
    sep = '' if new_arc.endswith('\n') else '\n'
    new_arc = (new_arc + sep + '\n'
               + '<details><summary>归档原文（H62/H63 · 逐字）</summary>\n\n'
               + seg_txt + '\n\n</details>\n')
assert new_arc.count('\r\n') == 2952, new_arc.count('\r\n')

# 看板：倒序替换为指针
new_bl = list(bl)
for rnd, s, e, b in reversed(segs):
    title = b[0]
    ptr = ('> 📦 %s 已归档至 BOARD_ARCHIVE.md（2026-11-22 11:3x，逐字搬，missing=0；'
           '本次由 Lead 执行，卫生员 H62/H63）' % title)
    assert '\r' not in ptr
    new_bl = new_bl[:s] + [ptr] + new_bl[e:]
new_brd = '\n'.join(new_bl)
assert new_brd.count('\r\n') == 0

with open(ARC, 'wb') as f:
    f.write(new_arc.encode('utf-8'))
with open(BRD, 'wb') as f:
    f.write(new_brd.encode('utf-8'))

b2, a2 = read(BRD), read(ARC)
assert b2 == new_brd and a2 == new_arc
assert b2.count('\r\n') == 0
assert a2.count('\r\n') == 2952
for rnd, s, e, b in segs:
    assert '\n'.join(b) in a2, 'round %d segment not verbatim in archive' % rnd
    assert b[0] not in b2, 'round %d title still in board' % rnd

bl2 = b2.split('\n')
n2 = len(bl2) - (1 if bl2 and bl2[-1] == '' else 0)
print('BOARD lines: 296 -> %d' % n2)
print('ARCHIVE bytes: %d -> %d, CRLF %d' % (len(arc.encode()), len(a2.encode()), a2.count('\r\n')))
print('OK')
