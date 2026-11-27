#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R148 G：看板归档（写前 286 行 >= 260 且 286 + 本轮段 > 300 ⇒ 必须归档最早 2 段）。
沿用 R138F 的口径：BOARD_ARCHIVE 尾部是 LF，追加用 LF；CR 必须保持 2952。
"""
import hashlib, io, json, os, sys, time

ROOT = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
BASE = os.path.join(R14, 'R17_LEAD_BASELINE')
BRD = os.path.join(R14, 'STATUS_BOARD.md')
ARC = os.path.join(R14, 'BOARD_ARCHIVE.md')
ARC_CR = 2952
fails = []


def ck(n, c, d=''):
    print(('  PASS ' if c else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not c:
        fails.append(n)


br_b = open(BRD, 'rb').read()
arc_b = open(ARC, 'rb').read()
ck('1 看板旧 CR == 0', br_b.count(b'\r') == 0, br_b.count(b'\r'))
ck('2 归档旧 CR == %d' % ARC_CR, arc_b.count(b'\r') == ARC_CR, arc_b.count(b'\r'))
ck('3 看板旧行数 == 286', br_b.count(b'\n') == 286, br_b.count(b'\n'))
br = br_b.decode('utf-8')
arc = arc_b.decode('utf-8')
lines = br.split('\n')
ck('4 看板以单个 LF 结尾', lines[-1] == '')
starts = [i for i, l in enumerate(lines) if l.startswith('## ')]
ck('5 看板恰 4 段', len(starts) == 4, [i + 1 for i in starts])
ck('6 首段是第 144 轮', '第 144 轮' in lines[starts[0]], lines[starts[0]][:40])

cut_from, cut_to = starts[0], starts[2]
moved = lines[cut_from:cut_to]
keep = lines[:cut_from] + lines[cut_to:]
ck('7 搬走的两段为 144 / 145', '第 144 轮' in moved[0] and any('第 145 轮' in l for l in moved),
   moved[0][:30])
ck('8 搬后首段是第 146 轮', '第 146 轮' in keep[0] if keep else False, keep[0][:40] if keep else '')
ck('9 第 147 轮未被搬走', any('第 147 轮' in l for l in keep) and not any('第 147 轮' in l for l in moved))
ck('10 搬走后看板仍剩 2 段', sum(1 for l in keep if l.startswith('## ')) == 2,
   sum(1 for l in keep if l.startswith('## ')))

new_br = '\n'.join(keep)
if not new_br.endswith('\n'):
    new_br += '\n'
br_nb = new_br.encode('utf-8')
ck('11 新看板 CR 仍 0', br_nb.count(b'\r') == 0, br_nb.count(b'\r'))
ck('12 看板缩短', br_nb.count(b'\n') < br_b.count(b'\n'), (br_b.count(b'\n'), br_nb.count(b'\n')))

moved_txt = '\n'.join(moved).rstrip('\n')
ck('13 搬走段不含 CR', '\r' not in moved_txt, moved_txt.count('\r'))
sep = '' if arc.endswith('\n') else '\n'
new_arc = arc + sep + moved_txt
if not new_arc.endswith('\n'):
    new_arc += '\n'
arc_nb = new_arc.encode('utf-8')
ck('14 新归档 CR 仍 == %d' % ARC_CR, arc_nb.count(b'\r') == arc_b.count(b'\r'),
   (arc_b.count(b'\r'), arc_nb.count(b'\r')))
expect_add = moved_txt.count('\n') + 1 + (1 if sep else 0)
ck('15 归档行数 == 旧 + 追加', arc_nb.count(b'\n') == arc_b.count(b'\n') + expect_add,
   (arc_b.count(b'\n'), arc_nb.count(b'\n'), expect_add))
ck('16 归档里第 144/145 轮各出现恰 1 次',
   new_arc.count('## 🟢 R17 第 144 轮') == 1 and new_arc.count('## 🟢 R17 第 145 轮') == 1,
   (new_arc.count('## 🟢 R17 第 144 轮'), new_arc.count('## 🟢 R17 第 145 轮')))
print('  看板 %d -> %d 行；归档 CR %d（不变）' % (br_b.count(b'\n'), br_nb.count(b'\n'),
                                          arc_nb.count(b'\r')))

if '--dry' in sys.argv:
    print('  [DRY] 不写盘')
else:
    TS = time.strftime('%Y%m%d_%H%M%S')
    for path, old_b, tag in ((BRD, br_b, 'archive_board'), (ARC, arc_b, 'archive_arc')):
        p = os.path.join(BASE, os.path.basename(path) + '.before_R148_%s_%s.bak' % (tag, TS))
        fd = os.open(p, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
        with os.fdopen(fd, 'wb') as f:
            f.write(old_b)
        ck('备份 wx %s' % os.path.basename(p), open(p, 'rb').read() == old_b)
    for path, new_b in ((BRD, br_nb), (ARC, arc_nb)):
        tmp = path + '.tmp_r148g'
        fd = os.open(tmp, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
        with os.fdopen(fd, 'wb') as f:
            f.write(new_b)
        os.replace(tmp, path)
    rb = open(BRD, 'rb').read()
    ra = open(ARC, 'rb').read()
    ck('回读看板 sha 一致', hashlib.sha256(rb).hexdigest() == hashlib.sha256(br_nb).hexdigest())
    ck('回读归档 sha 一致', hashlib.sha256(ra).hexdigest() == hashlib.sha256(arc_nb).hexdigest())
    ck('回读看板 CR == 0', rb.count(b'\r') == 0, rb.count(b'\r'))
    ck('回读归档 CR == %d' % ARC_CR, ra.count(b'\r') == ARC_CR, ra.count(b'\r'))
    ck('回读看板 2 段', sum(1 for l in rb.decode('utf-8').split('\n') if l.startswith('## ')) == 2)

json.dump(dict(fails=fails, board_before=br_b.count(b'\n'), board_after=br_nb.count(b'\n'),
               arc_cr=arc_nb.count(b'\r')), open(os.path.join(ROOT, '_r148', 'r148g_archive.json'),
                                                 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('=== FAILS: %d ===' % len(fails))
for f in fails:
    print('  ' + f)
