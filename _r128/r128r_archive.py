# -*- coding: utf-8 -*-
"""R128r：看板写入后达 284 行，超 300 行上限，必须先归档最早两段到 BOARD_ARCHIVE。

不变量：BOARD_ARCHIVE 的 CR 必须保持 2952、STATUS_BOARD 的 CR 必须保持 0。
做法：把最早两段按纯 LF 追加到归档末尾（不引入任何 CR），再从看板删掉。
"""
import io, os, hashlib, datetime
ROOT = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
BK = os.path.join(R14, 'R17_LEAD_BASELINE')
BRD = os.path.join(R14, 'STATUS_BOARD.md')
ARC = os.path.join(R14, 'BOARD_ARCHIVE.md')
TS = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

def sha16(b): return hashlib.sha256(b).hexdigest()[:16]

brd_old = io.open(BRD, 'rb').read()
arc_old = io.open(ARC, 'rb').read()
print('before: board %d bytes / %d lines / CR=%d ; archive %d bytes / %d lines / CR=%d'
      % (len(brd_old), brd_old.count(b'\n'), brd_old.count(b'\r'),
         len(arc_old), arc_old.count(b'\n'), arc_old.count(b'\r')))
assert brd_old.count(b'\r') == 0, 'board must be LF-only'
assert arc_old.count(b'\r') == 2952, 'archive CR must be 2952, got %d' % arc_old.count(b'\r')

for path, tag in ((BRD, 'STATUS_BOARD.md'), (ARC, 'BOARD_ARCHIVE.md')):
    dst = os.path.join(BK, 'r128_archive_%s.%s.bak' % (tag, TS))
    fd = os.open(dst, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
    try: os.write(fd, io.open(path, 'rb').read())
    finally: os.close(fd)
    print('  backup ->', os.path.basename(dst))

txt = brd_old.decode('utf-8')
lines = txt.split('\n')
hdr_idx = [i for i, l in enumerate(lines) if l.startswith('## 🟢 R17 第')]
assert len(hdr_idx) == 4, 'expect 4 round segments, got %d' % len(hdr_idx)
print('  segments at lines', [i + 1 for i in hdr_idx])

cut = hdr_idx[2]
moved = lines[hdr_idx[0]:cut]
kept = lines[cut:]
print('  moving %d lines (2 segments), keeping %d lines' % (len(moved), len(kept)))

moved_txt = '\n'.join(moved).rstrip('\n')
kept_txt = '\n'.join(kept)

arc_txt = arc_old.decode('utf-8').rstrip('\n')
arc_new = arc_txt + '\n\n' + moved_txt + '\n'
arc_nb = arc_new.encode('utf-8')
brd_nb = (kept_txt.rstrip('\n') + '\n').encode('utf-8')

io.open(ARC, 'wb').write(arc_nb)
io.open(BRD, 'wb').write(brd_nb)

a = io.open(ARC, 'rb').read()
b = io.open(BRD, 'rb').read()
assert a == arc_nb, 'archive readback mismatch'
assert b == brd_nb, 'board readback mismatch'
assert a.count(b'\r') == 2952, 'archive CR drifted: %d' % a.count(b'\r')
assert b.count(b'\r') == 0, 'board CR drifted: %d' % b.count(b'\r')
nlines = b.count(b'\n')
print('after: board %d bytes / %d lines / CR=%d ; archive %d bytes / %d lines / CR=%d'
      % (len(b), nlines, b.count(b'\r'), len(a), a.count(b'\n'), a.count(b'\r')))
assert nlines <= 300, 'board still over limit: %d' % nlines
print('  OK: board %d lines (<= 300), archive CR still 2952' % nlines)
print('  sha board %s -> %s ; archive %s -> %s'
      % (sha16(brd_old), sha16(b), sha16(arc_old), sha16(a)))
