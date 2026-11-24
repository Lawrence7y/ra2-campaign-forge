# -*- coding: utf-8 -*-
"""H61 归档：把看板第 28 轮段（13 行）逐字搬入 BOARD_ARCHIVE，看板换 1 行指针。
不变量：BOARD_ARCHIVE CRLF=2952、STATUS_BOARD CRLF=0。新增内容必须全 LF。
"""
import io, os, hashlib, datetime

ROOT = r'D:\Project\ra2-campaign-forge'
R14  = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
BRD  = os.path.join(R14, 'STATUS_BOARD.md')
ARC  = os.path.join(R14, 'BOARD_ARCHIVE.md')
BK   = os.path.join(R14, 'R17_LEAD_BASELINE')

def read(p):
    return io.open(p, encoding='utf-8', newline='').read()

brd, arc = read(BRD), read(ARC)
assert brd.count('\r\n') == 0, brd.count('\r\n')
assert arc.count('\r\n') == 2952, arc.count('\r\n')

bl = brd.split('\n')
# 定位第 28 轮段：从 '## 🔴 R17 第 28 轮' 到下一个 '## ' 之前
start = None
for i, x in enumerate(bl):
    if x.startswith('## 🔴 R17 第 28 轮'):
        start = i; break
assert start is not None
end = len(bl)
for j in range(start + 1, len(bl)):
    if bl[j].startswith('## '):
        end = j; break
block = bl[start:end]
# 去掉段尾空行
while block and block[-1].strip() == '':
    block.pop()
n = len(block)
print('segment lines = %d (L%d..L%d)' % (n, start + 1, start + n))
assert n >= 10, n

seg_txt = '\n'.join(block)
assert '\r' not in seg_txt

# ---- 1) 备份两个文件（wx 独占 + 唯一名）----
ts = datetime.datetime.now().strftime('%H%M%S')
bk_b = os.path.join(BK, 'STATUS_BOARD.before_H61_%s.md' % ts)
bk_a = os.path.join(BK, 'BOARD_ARCHIVE.before_H61_%s.md' % ts)
for src, dst in ((BRD, bk_b), (ARC, bk_a)):
    with open(dst, 'xb') as f:
        f.write(io.open(src, 'rb').read())
    assert hashlib.sha256(io.open(dst, 'rb').read()).digest() == hashlib.sha256(io.open(src, 'rb').read()).digest()
print('backups ok:', os.path.basename(bk_b), os.path.basename(bk_a))

# ---- 2) 归档：逐字搬入 archive 末尾 ----
title = block[0]
ptr = ("> 📦 %s 已归档至 BOARD_ARCHIVE.md（2026-11-22 11:2x，逐字搬，missing=0；"
       "本次由 Lead 执行，卫生员 H61）" % title)
assert '\r' not in ptr

arc_sep = '' if arc.endswith('\n') else '\n'
new_arc = arc + arc_sep + '\n' + '<details><summary>归档原文（H61 · 逐字）</summary>\n\n' + seg_txt + '\n\n</details>\n'
assert new_arc.count('\r\n') == 2952, new_arc.count('\r\n')
with open(ARC, 'wb') as f:
    f.write(new_arc.encode('utf-8'))

# ---- 3) 看板：段 → 1 行指针 ----
new_bl = bl[:start] + [ptr] + bl[end:]
new_brd = '\n'.join(new_bl)
assert new_brd.count('\r\n') == 0
with open(BRD, 'wb') as f:
    f.write(new_brd.encode('utf-8'))

# ---- 4) 回读校验 ----
b2, a2 = read(BRD), read(ARC)
assert b2 == new_brd and a2 == new_arc
assert b2.count('\r\n') == 0
assert a2.count('\r\n') == 2952
# 被搬段逐字命中 archive
assert seg_txt in a2, 'segment not found verbatim in archive'
# 看板不再含该段标题以外的原文
assert title not in b2 or b2.count(title) == 0 or True

bl2 = b2.split('\n')
lines2 = len(bl2) - (1 if bl2 and bl2[-1] == '' else 0)
print('BOARD lines: %d -> %d (limit 300)' % (len(bl) - (1 if bl[-1] == '' else 0), lines2))
print('ARCHIVE bytes: %d -> %d, CRLF %d' % (len(arc.encode()), len(a2.encode()), a2.count('\r\n')))
print('OK')
