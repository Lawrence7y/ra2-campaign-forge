# -*- coding: utf-8 -*-
"""看板追加：段自身行数 + 追加时文件行数（新记录法），占位符实测回填。"""
import io, os, hashlib, datetime, sys

BRD = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\STATUS_BOARD.md'
BK  = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R17_LEAD_BASELINE'

def append(section, marker, expect_crlf=0):
    brd = io.open(BRD, encoding='utf-8', newline='').read()
    assert brd.count('\r\n') == expect_crlf
    assert marker not in brd, 'already appended'
    sec = io.open(section, encoding='utf-8', newline='').read().rstrip('\n')
    assert '\r' not in sec
    seglines = len(sec.split('\n'))
    ts = datetime.datetime.now().strftime('%H%M%S')
    with open(os.path.join(BK, 'STATUS_BOARD.before_%s_%s.md' % (marker.strip('# ').replace(' ', ''), ts)), 'xb') as f:
        f.write(io.open(BRD, 'rb').read())
    sep = '' if brd.endswith('\n') else '\n'
    new = brd + sep + sec + '\n'
    bl = new.split('\n')
    n = len(bl) - (1 if bl and bl[-1] == '' else 0)
    assert n <= 300, n
    if '{{SEGLINES}}' in new:
        new = new.replace('{{SEGLINES}}', '%d' % seglines).replace('{{BOARDLINES}}', '%d' % n)
    assert '{{' not in new
    with open(BRD, 'wb') as f:
        f.write(new.encode('utf-8'))
    back = io.open(BRD, encoding='utf-8', newline='').read()
    assert back == new and back.count('\r\n') == expect_crlf
    assert len([1 for l in back.split('\n') if l.startswith(marker)]) == 1
    print('segment=%d lines ; board=%d lines ; bytes=%d' % (seglines, n, os.path.getsize(BRD)))
    print('sha256 =', hashlib.sha256(io.open(BRD, 'rb').read()).hexdigest().upper())

if __name__ == '__main__':
    append(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\_r41\board_r41.md', '## 🔴 R17 第 41 轮')
