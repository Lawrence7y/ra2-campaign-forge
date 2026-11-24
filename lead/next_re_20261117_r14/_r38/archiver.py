# -*- coding: utf-8 -*-
"""可复用归档器：把看板若干轮段逐字搬入 BOARD_ARCHIVE，各换 1 行指针。
不变量：BOARD_ARCHIVE CRLF=2952 / STATUS_BOARD CRLF=0。
断言纪律（R36 踩过的坑）：不要断言「标题不出现」——指针行本身含标题；要断言**段体**已移走且**逐字**进 archive。
用法: python archiver.py 33 34 --tag H6667
"""
import io, os, sys, hashlib, datetime

ROOT = r'D:\Project\ra2-campaign-forge'
R14  = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
BRD  = os.path.join(R14, 'STATUS_BOARD.md')
ARC  = os.path.join(R14, 'BOARD_ARCHIVE.md')
BK   = os.path.join(R14, 'R17_LEAD_BASELINE')

def read(p): return io.open(p, encoding='utf-8', newline='').read()

def main(rounds, tag):
    brd, arc = read(BRD), read(ARC)
    assert brd.count('\r\n') == 0
    assert arc.count('\r\n') == 2952, arc.count('\r\n')
    bl = brd.split('\n')

    def bounds(prefix):
        s = None
        for i, x in enumerate(bl):
            if x.startswith(prefix):
                s = i; break
        assert s is not None, 'not found: ' + prefix
        e = len(bl)
        for j in range(s + 1, len(bl)):
            if bl[j].startswith('## '):
                e = j; break
        b = bl[s:e]
        while b and b[-1].strip() == '':
            b.pop()
        return s, e, b

    segs = []
    for r in rounds:
        s, e, b = bounds('## 🔴 R17 第 %d 轮' % r)
        assert len(b) >= 8, (r, len(b))
        segs.append((r, s, e, b))
        print('round %d: L%d..L%d = %d 行' % (r, s + 1, s + len(b), len(b)))

    ts = datetime.datetime.now().strftime('%H%M%S')
    for srcp, name in ((BRD, 'STATUS_BOARD'), (ARC, 'BOARD_ARCHIVE')):
        bk = os.path.join(BK, '%s.before_%s_%s.md' % (name, tag, ts))
        with open(bk, 'xb') as f:
            f.write(io.open(srcp, 'rb').read())
        assert hashlib.sha256(io.open(bk, 'rb').read()).digest() == \
               hashlib.sha256(io.open(srcp, 'rb').read()).digest()

    new_arc = arc
    for r, s, e, b in segs:
        seg = '\n'.join(b)
        assert '\r' not in seg
        sep = '' if new_arc.endswith('\n') else '\n'
        new_arc = (new_arc + sep + '\n'
                   + '<details><summary>归档原文（%s · 逐字）</summary>\n\n' % tag
                   + seg + '\n\n</details>\n')
    assert new_arc.count('\r\n') == 2952

    new_bl = list(bl)
    for r, s, e, b in reversed(segs):
        ptr = ('> 📦 %s 已归档至 BOARD_ARCHIVE.md（2026-11-22 12:0x，逐字搬，missing=0；'
               '本次由 Lead 执行，卫生员 %s）' % (b[0], tag))
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
    assert b2.count('\r\n') == 0 and a2.count('\r\n') == 2952

    # 严格校验：整段逐字在 archive；段体（第2行起前3行）不在看板
    for r, s, e, b in segs:
        seg = '\n'.join(b)
        assert seg in a2, 'round %d 未逐字进 archive' % r
        body = '\n'.join(b[1:4])
        assert body not in b2, 'round %d 段体仍留在看板' % r
        assert body in a2, 'round %d 段体未进 archive' % r

    bl2 = b2.split('\n')
    n2 = len(bl2) - (1 if bl2 and bl2[-1] == '' else 0)
    print('BOARD: 280 -> %d 行 ; ARCHIVE: %d -> %d B, CRLF %d'
          % (n2, len(arc.encode()), len(a2.encode()), a2.count('\r\n')))
    print('OK')

if __name__ == '__main__':
    ours = [int(x) for x in sys.argv[1:] if x.isdigit()]
    tag = [x for x in sys.argv[1:] if not x.isdigit()]
    main(ours, tag[0] if tag else 'HXX')
