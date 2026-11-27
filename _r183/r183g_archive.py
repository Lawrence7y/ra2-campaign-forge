# -*- coding: utf-8 -*-
"""R183 G：看板 279 行 >= 260 ⇒ 搬最早两段（R172 + R173）到 BOARD_ARCHIVE.md。
fail-closed：旧 sha 硬闸 + CR 不变量 + 逐字节闭合（搬走字节数 ==  архив 增量）。"""
import hashlib, io, os, sys, time

ROOT = '/home/t628/projects/ra2-campaign-forge'
TIER = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
BL = os.path.join(TIER, 'R17_LEAD_BASELINE')
BRD = os.path.join(TIER, 'STATUS_BOARD.md')
ARC = os.path.join(TIER, 'BOARD_ARCHIVE.md')
stamp = time.strftime('%Y%m%d_%H%M%S')
fails, n = [], 0
def ck(name, cond, detail=''):
    global n
    n += 1
    print(('  PASS ' if cond else '  FAIL ') + name + (('  ' + str(detail)) if detail else ''))
    if not cond: fails.append(name)

braw = open(BRD, 'rb').read(); araw = open(ARC, 'rb').read()
# S-183g1：初版把「279」当行数（实为 split 后含末尾空串的元素数），实测 count(b'\n') == 278
ck('A1 看板 %d 行 >= 260（触发归档）' % braw.count(b'\n'), braw.count(b'\n') >= 260, braw.count(b'\n'))
ck('A2 看板 CR == 0', braw.count(b'\r') == 0, braw.count(b'\r'))
ck('A3 归档 CR == 2952', araw.count(b'\r') == 2952, araw.count(b'\r'))

btxt = braw.decode('utf-8'); atxt = araw.decode('utf-8')
lines = btxt.split('\n')
heads = [(i, l) for i, l in enumerate(lines) if l.startswith('## ')]
ck('A4 段头 11 个', len(heads) == 11, len(heads))
ck('A5 第 2 段是 R172', '第 172 轮' in heads[1][1], heads[1][1][:40])
ck('A6 第 3 段是 R173', '第 173 轮' in heads[2][1], heads[2][1][:40])
s = heads[1][0]          # R172 起（0-based）
e = heads[3][0]          # R173 结束处（R174 段头）
moved = '\n'.join(lines[s:e]) + '\n'
rest = '\n'.join(lines[:s] + lines[e:])
ck('A7 搬走两段行数 = %d' % (e - s), (e - s) == 56, e - s)
ck('A8 搬走文本含 R172 + R173 两个段头',
   '第 172 轮' in moved and '第 173 轮' in moved and '第 174 轮' not in moved)
ck('A9 剩余文本不含 R172/R173 段头', '第 172 轮' not in rest and '第 173 轮' not in rest)
ck('A10 CR 均不变', moved.count('\r') == 0 and rest.count('\r') == 0)

newarc = atxt + moved
ck('B1 归档字节增量 == 搬走文本字节（逐字节闭合）',
   len(newarc.encode()) - len(araw) == len(moved.encode()),
   (len(newarc.encode()) - len(araw), len(moved.encode())))
ck('B2 归档只追加（旧文是新文前缀）', newarc.startswith(atxt))
ck('B3 归档 CR 仍 2952', newarc.count('\r') == 2952, newarc.count('\r'))
ck('B4 看板行数 = %d < 260' % rest.count('\n'), rest.count('\n') < 260, rest.count('\n'))
ck('B5 看板 CR 仍 0', rest.count('\r') == 0, rest.count('\r'))
ck('B6 字节守恒：旧看板 + 旧归档 == 新看板 + 新归档',
   len(braw) + len(araw) == len(rest.encode()) + len(newarc.encode()),
   (len(braw) + len(araw), len(rest.encode()) + len(newarc.encode())))

if fails:
    print('★ fail-closed：%d 条未过，不写盘' % len(fails)); sys.exit(1)

print('== 写盘 ==')
def wr(path, oldraw, newtxt, tag):
    o = hashlib.sha256(oldraw).hexdigest()
    bak = os.path.join(BL, '%s.before_r183_%s_%s.bak' % (os.path.basename(path), tag, stamp))
    fd = os.open(bak, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, 'wb') as f: f.write(oldraw)
    assert hashlib.sha256(open(bak, 'rb').read()).hexdigest() == o
    io.open(path, 'w', encoding='utf-8', newline='').write(newtxt)
    back = open(path, 'rb').read()
    ck('C %s 回读一致' % os.path.basename(path),
       hashlib.sha256(back).hexdigest() == hashlib.sha256(newtxt.encode()).hexdigest())
    print('   %-20s %d -> %d B' % (os.path.basename(path), len(oldraw), len(back)))
wr(ARC, araw, newarc, 'arc')
wr(BRD, braw, rest, 'brd')
b2 = open(BRD, 'rb').read(); a2 = open(ARC, 'rb').read()
ck('D1 终态看板 CR 0 / 行数 %d' % b2.count(b'\n'), b2.count(b'\r') == 0 and b2.count(b'\n') < 260)
ck('D2 终态归档 CR 2952', a2.count(b'\r') == 2952, a2.count(b'\r'))
print('\n== %d 断言, %d FAIL ==' % (n, len(fails)))
sys.exit(1 if fails else 0)
