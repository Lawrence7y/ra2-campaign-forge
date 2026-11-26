#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r138f_archive.py —— R138 看板归档：把最早的 2 段搬进 BOARD_ARCHIVE。

判据（不是「当前行数 < 260」，那是 R137 犯错的地方 S-259）：
  **当前行数 + 本轮将追加的行数 <= 300** 才免归档。
  本轮 247 + 74 = 321 > 300 ⇒ 必须归档。

搬最早的 2 段（135 / 136），搬到 BOARD_ARCHIVE.md 尾部。
归档文件 CR 必须保持 2952（它是 CRLF 文件，追加的段也必须用 CRLF 落进去，
否则 CR 会变化 —— 这是本脚本最容易写错的地方，故显式断言）。

纪律：wx 备份 -> 断言旧 sha/CR -> 一次性写入 -> 回读校验。
"""
import os
import re
import sys
import time
import hashlib

ROOT = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
BASE = os.path.join(R14, 'R17_LEAD_BASELINE')
BRD = os.path.join(R14, 'STATUS_BOARD.md')
ARC = os.path.join(R14, 'BOARD_ARCHIVE.md')

DRY = '--dry' in sys.argv
TS = time.strftime('%Y%m%d_%H%M%S')
BOARD_CR = 0
ARC_CR = 2952

fails, buf = [], []


def W(s=''):
    print(s)
    buf.append(s)


def ck(n, c, d=''):
    W(('  PASS ' if c else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not c:
        fails.append(n)


def main():
    W('# R138 看板归档%s' % ('  [DRY]' if DRY else ''))
    br_b = open(BRD, 'rb').read()
    arc_b = open(ARC, 'rb').read()
    ck('看板旧 CR == 0', br_b.count(b'\r') == 0, br_b.count(b'\r'))
    ck('归档旧 CR == %d' % ARC_CR, arc_b.count(b'\r') == ARC_CR,
       arc_b.count(b'\r'))

    br = br_b.decode('utf-8')
    arc = arc_b.decode('utf-8')
    lines = br.split('\n')
    ck('看板以单个 LF 结尾', lines[-1] == '')

    starts = [i for i, l in enumerate(lines) if l.startswith('## ')]
    ck('看板恰 3 段', len(starts) == 3, len(starts))
    W('  段起始行（1-based）：%s' % [i + 1 for i in starts])

    # 搬最早的 2 段：lines[starts[0] : starts[2]]
    cut_from, cut_to = starts[0], starts[2]
    moved = lines[cut_from:cut_to]
    keep = lines[:cut_from] + lines[cut_to:]
    ck('搬走的行数 > 0', len(moved) > 0, len(moved))
    ck('搬走的段首为第 135 轮', u'第 135 轮' in moved[0], moved[0][:50])
    ck('搬走后第 1 段为第 137 轮', u'第 137 轮' in keep[0] if keep else False,
       keep[0][:50] if keep else 'empty')
    ck('第 137 轮段未被搬走',
       any(u'第 137 轮' in l for l in keep) and
       not any(u'第 137 轮' in l for l in moved))

    new_br = '\n'.join(keep)
    if not new_br.endswith('\n'):
        new_br += '\n'
    br_nb = new_br.encode('utf-8')
    ck('新看板 CR 仍 0', br_nb.count(b'\r') == 0, br_nb.count(b'\r'))
    W('  看板 %d 行 -> %d 行' % (br.count('\n'), br_nb.count(b'\n')))
    ck('看板缩短', br_nb.count(b'\n') < br_b.count(b'\n'),
       (br_b.count(b'\n'), br_nb.count(b'\n')))

    # 归档：**不假设**整个文件是纯 CRLF。实测 BOARD_ARCHIVE.md 是混合换行：
    # 7,249 行里 CRLF 行 2,952、纯 LF 行 4,297，且**文件尾部是纯 LF**。
    # 故 CR=2952 这个不变量是「历史内容带来的」，不是格式约束 ——
    # 追加必须沿用尾部既有约定（LF），CR 数才不变。若照抄 CRLF 追加，CR 会涨。
    moved_txt = '\n'.join(moved).rstrip('\n')
    sep = '' if arc.endswith('\n') else '\n'
    new_arc = arc + sep + moved_txt
    if not new_arc.endswith('\n'):
        new_arc += '\n'
    arc_nb = new_arc.encode('utf-8')
    ck('追加段 CR 数为 0（沿用文件尾部的 LF 约定）',
       moved_txt.count('\r') == 0, moved_txt.count('\r'))
    ck('新归档 CR == 旧 CR %d（不变）' % ARC_CR,
       arc_nb.count(b'\r') == arc_b.count(b'\r'),
       (arc_b.count(b'\r'), arc_nb.count(b'\r')))
    # 追加的 LF 数 = moved_txt 内的 LF 数 + 末尾补的 1 个 + sep 的 1 个（若加过）
    expect_add = moved_txt.count('\n') + 1 + (1 if sep else 0)
    ck('新归档行数 == 旧行数 + 追加行数',
       arc_nb.count(b'\n') == arc_b.count(b'\n') + expect_add,
       (arc_b.count(b'\n'), arc_nb.count(b'\n'), expect_add))
    W('  归档追加 %d 行（LF），CR 保持 %d' % (moved_txt.count('\n') + 1, ARC_CR))

    if DRY:
        W()
        W('--dry 不写盘：看板 %d -> %d 行，归档 CR %d -> %d'
          % (br_b.count(b'\n'), br_nb.count(b'\n'),
             arc_b.count(b'\r'), arc_nb.count(b'\r')))
        W('== %d PASS / %d FAIL ==' % (len(buf) - len(fails), len(fails)))
        for f in fails:
            W('  FAIL: ' + f)
        return 0 if not fails else 1

    # 备份 + 写入
    for path, old_b, tag in ((BRD, br_b, 'archive_board'),
                             (ARC, arc_b, 'archive_arc')):
        p = os.path.join(BASE, os.path.basename(path) + '.before_R138_%s_%s.bak'
                         % (tag, TS))
        fd = os.open(p, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
        try:
            os.write(fd, old_b)
        finally:
            os.close(fd)
        assert hashlib.sha256(open(p, 'rb').read()).hexdigest() == \
            hashlib.sha256(old_b).hexdigest()
        W('  备份 %s' % p)

    for path, new_b in ((BRD, br_nb), (ARC, arc_nb)):
        tmp = path + '.tmp_r138f'
        if os.path.exists(tmp):
            os.remove(tmp)
        fd = os.open(tmp, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
        try:
            os.write(fd, new_b)
        finally:
            os.close(fd)
        os.replace(tmp, path)

    rb = open(BRD, 'rb').read()
    ra = open(ARC, 'rb').read()
    ck('回读看板 sha 一致',
       hashlib.sha256(rb).hexdigest() == hashlib.sha256(br_nb).hexdigest())
    ck('回读归档 sha 一致',
       hashlib.sha256(ra).hexdigest() == hashlib.sha256(arc_nb).hexdigest())
    ck('回读看板 CR == 0', rb.count(b'\r') == 0, rb.count(b'\r'))
    ck('回读归档 CR 仍 == %d' % ARC_CR, ra.count(b'\r') == ARC_CR,
       ra.count(b'\r'))
    ck('回读看板 3 段变 1 段',
       sum(1 for l in rb.decode('utf-8').split('\n') if l.startswith('## ')) == 1)

    W()
    W('== %d PASS / %d FAIL ==' % (len(buf) - len(fails), len(fails)))
    W('看板 %d -> %d 行；归档 CR %d -> %d'
      % (br_b.count(b'\n'), rb.count(b'\n'), arc_b.count(b'\r'), ra.count(b'\r')))
    return 0 if not fails else 1


if __name__ == '__main__':
    sys.exit(main())
