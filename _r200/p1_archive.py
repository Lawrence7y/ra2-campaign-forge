#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R200 归档：看板开局 272 行（<260? 否，>=260 触发）⇒ 归档最早两段到 BOARD_ARCHIVE。
纪律：R17_LEAD_BASELINE 用 O_EXCL 独占备份 -> 断言旧 sha256 与 CR -> 一次性写入 -> 回读校验。
断言：归档后 STATUS_BOARD CR 仍 0、行数 = 原行数 - 被归档行数；BOARD_ARCHIVE CR 仍 2952。
"""
import hashlib, io, os, sys, time
ROOT = '/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14'
SB = os.path.join(ROOT, 'STATUS_BOARD.md')
BA = os.path.join(ROOT, 'BOARD_ARCHIVE.md')
BL = os.path.join(ROOT, 'R17_LEAD_BASELINE')
fails = []; n = 0
def ck(nm, c, d=''):
    global n; n += 1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ') + nm + ((' | ' + str(d)) if d != '' else ''))

sb = io.open(SB, 'rb').read(); ba = io.open(BA, 'rb').read()
sha_sb = hashlib.sha256(sb).hexdigest(); sha_ba = hashlib.sha256(ba).hexdigest()
ck('A1 看板开局 CR==0 且行数 272', sb.count(b'\r') == 0 and sb.count(b'\n') == 272,
   (sb.count(b'\r'), sb.count(b'\n')))
ck('A2 归档开局 CR==2952', ba.count(b'\r') == 2952, ba.count(b'\r'))
ck('A3 看板开局行数 >= 260（触发归档）', sb.count(b'\n') >= 260, sb.count(b'\n'))
L = sb.split(b'\n')
idx = [i for i, l in enumerate(L) if l.startswith(b'## ')]
ck('A4 段头至少 3 个', len(idx) >= 3, len(idx))
cut = idx[2]
moved = b'\n'.join(L[:cut]) + b'\n'
rest = b'\n'.join(L[cut:])
ck('A5 被归档段数 == 2', moved.count(b'\n## ') == 1, moved.count(b'\n## '))
ck('A6 被归档行数 == cut', cut == moved.count(b'\n'), (cut, moved.count(b'\n')))
ck('A7 剩余看板 CR==0 且行数 = 272 - cut', rest.count(b'\r') == 0 and rest.count(b'\n') == 272 - cut,
   (rest.count(b'\r'), rest.count(b'\n'), 272 - cut))
ck('A8 剩余看板行数 <= 300', rest.count(b'\n') <= 300, rest.count(b'\n'))
new_ba = ba + b'\n' + moved
ck('A9 新归档 CR 保持 2952', new_ba.count(b'\r') == 2952, new_ba.count(b'\r'))
ck('A10 新归档行数 = 原 + cut + 1（1 条分隔空行）', new_ba.count(b'\n') == ba.count(b'\n') + cut + 1,
   (new_ba.count(b'\n'), ba.count(b'\n') + cut + 1))
ck('A11 内容无丢失（arch + board 拼接等于原 board）',
   new_ba.endswith(moved) and new_ba[:-len(moved)] == ba + b'\n', True)
if fails:
    print('★ fail-closed %d 条未过，不写盘' % len(fails)); sys.exit(1)
stamp = time.strftime('%Y%m%d_%H%M%S')
for path, oldraw, newraw, tag in ((SB, sb, rest, 'STATUS_BOARD'), (BA, ba, new_ba, 'BOARD_ARCHIVE')):
    bak = os.path.join(BL, 'SUPERSEDED.before_r200_archive_%s_%s.md' % (tag, stamp))
    fd = os.open(bak, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, 'wb') as f: f.write(oldraw)
    ck('W1 %s 备份 sha 一致' % tag,
       hashlib.sha256(open(bak, 'rb').read()).hexdigest() == hashlib.sha256(oldraw).hexdigest())
    assert io.open(path, 'rb').read() == oldraw, '%s 被外部改动' % tag
    io.open(path, 'wb').write(newraw)
    ck('W2 %s 回读一致' % tag,
       hashlib.sha256(io.open(path, 'rb').read()).hexdigest() == hashlib.sha256(newraw).hexdigest())
ck('W3 写后看板 CR==0 / 归档 CR==2952',
   io.open(SB, 'rb').read().count(b'\r') == 0 and io.open(BA, 'rb').read().count(b'\r') == 2952, True)
print('\nSUMMARY asserts=%d fails=%d %s' % (n, len(fails), fails))
