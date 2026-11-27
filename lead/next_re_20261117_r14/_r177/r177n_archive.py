# -*- coding: utf-8 -*-
"""R177：看板 261 行 >= 260 ⇒ 归档最早的 2 段（文件顺序最早 = 166、165）。
纪律：BOARD_ARCHIVE CR 保持 2952；STATUS_BOARD CR 保持 0；两文件均只做「搬走/追加」。"""
import hashlib, os, re, sys
P = F = 0
def ck(n, c, d=''):
    global P, F
    if c: P += 1; print('PASS', n, d)
    else: F += 1; print('FAIL', n, d)

B = 'STATUS_BOARD.md'; A = 'BOARD_ARCHIVE.md'
braw = open(B, 'rb').read(); araw = open(A, 'rb').read()
bt = braw.decode('utf-8'); at = araw.decode('utf-8')
ck('A1 board CR=0', braw.count(b'\r') == 0)
ck('A2 board 行数 261', braw.count(b'\n') == 261, braw.count(b'\n'))
ck('A3 archive CR=2952', araw.count(b'\r') == 2952, araw.count(b'\r'))
ck('A4 archive LF=9570', araw.count(b'\n') == 9570, araw.count(b'\n'))

heads = [(m.start(), m.group(0)) for m in re.finditer(r'(?m)^## .*$', bt)]
ck('B1 段数 10', len(heads) == 10, len(heads))
# 搬走「文件顺序最早两段」= heads[0], heads[1]
cut_start = heads[0][0]
cut_end = heads[2][0]
moved = bt[cut_start:cut_end]
kept = bt[:cut_start] + bt[cut_end:]
ck('B2 被搬走两段 = 166 与 165',
   heads[0][1].startswith('## 🟢 R17 第 166 轮') and heads[1][1].startswith('## 🟢 R17 第 165 轮'))
# S-649：heads 的 offset 是**字符**偏移，我先前把它当字节数写死成 6896，实测字节 11,556。
# 两种口径都写死，避免再用「字符偏移 ≈ 字节数」这种外形假设。
ck('B3 搬走字符数 = 6,896（= 段 2 的字符偏移）', len(moved) == 6896, len(moved))
ck('B3b 搬走字节数 = 11,556（UTF-8 实测，不是上面那个字符数）', len(moved.encode()) == 11556, len(moved.encode()))
ck('B4 剩下的段数 8', len(re.findall(r'(?m)^## ', kept)) == 8, len(re.findall(r'(?m)^## ', kept)))
ck('B5 第 177 轮仍在', kept.count('## 🟢 R17 第 177 轮') == 1)
ck('B6 1444 段顺序未变（相邻关系）', kept.find('第 164 轮') < kept.find('第 171 轮') < kept.find('第 177 轮'))
nl_kept = kept.count('\n')
print('  归档后 board 行数 =', nl_kept)
ck('B7 行数 < 260', nl_kept < 260, nl_kept)

# 归档：追加（保持 CR 2952 —— 被搬走段里的 CR 数必须为 0，否则 CR 会变）
moved_cr = moved.count('\r')
ck('C1 被搬走段内 CR = 0（否则归档 CR 会漂）', moved_cr == 0, moved_cr)
newat = at
if not newat.endswith('\n'):
    newat += '\n'
newat = newat + moved
ck('C2 archive CR 保持 2952', newat.count('\r') == 2952, newat.count('\r'))
ck('C3 archive 前缀逐字保留', newat.startswith(at))
ck('C4 archive 新增行数 = 搬走行数', newat.count('\n') - at.count('\n') == moved.count('\n'),
   newat.count('\n') - at.count('\n'))
print('  archive 行数 %d -> %d' % (at.count('\n'), newat.count('\n')))
ck('C5 archive 里 166/165 各 1 次', newat.count('## 🟢 R17 第 166 轮') == 1 and newat.count('## 🟢 R17 第 165 轮') == 1,
   (newat.count('## 🟢 R17 第 166 轮'), newat.count('## 🟢 R17 第 165 轮')))

if F:
    print('ABORT %d FAIL' % F); sys.exit(1)
with open(B, 'wb') as f: f.write(kept.encode('utf-8'))
with open(A, 'wb') as f: f.write(newat.encode('utf-8'))
rb = open(B, 'rb').read(); ra = open(A, 'rb').read()
ck('D1 board 回读', rb == kept.encode('utf-8'))
ck('D2 archive 回读', ra == newat.encode('utf-8'))
ck('D3 board CR=0', rb.count(b'\r') == 0)
ck('D4 archive CR=2952', ra.count(b'\r') == 2952, ra.count(b'\r'))
print('board = %d B / %d 行 / cr=%d' % (len(rb), rb.count(b'\n'), rb.count(b'\r')))
print('archive = %d B / %d 行 / cr=%d' % (len(ra), ra.count(b'\n'), ra.count(b'\r')))
print('---- %d PASS / %d FAIL ----' % (P, F))
