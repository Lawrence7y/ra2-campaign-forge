# -*- coding: utf-8 -*-
"""通用追加器：把指定段追加到指定文件，保持 CRLF 不变量，路径写死不靠字符串替换。"""
import io, os, hashlib, datetime, sys

def append(target, section, expect_crlf, marker_prefix, backprefix):
    before = io.open(target, encoding='utf-8', newline='').read()
    crlf0 = before.count('\r\n'); bytes0 = os.path.getsize(target)
    sha0 = hashlib.sha256(io.open(target, 'rb').read()).hexdigest().upper()
    assert crlf0 == expect_crlf, 'CRLF=%d expected %d' % (crlf0, expect_crlf)
    n_before = len([1 for l in before.split('\n') if l.startswith(marker_prefix)])
    print('BEFORE %-22s bytes=%d CRLF=%d %s_count=%d' %
          (os.path.basename(target), bytes0, crlf0, marker_prefix, n_before))
    assert n_before == 0, 'section already present'

    sec = io.open(section, encoding='utf-8', newline='').read()
    assert '\r' not in sec
    assert sec.lstrip().startswith(marker_prefix), sec[:60]

    ts = datetime.datetime.now().strftime('%H%M%S')
    bk = os.path.join(os.path.dirname(section), '..', 'R17_LEAD_BASELINE',
                      '%s.before_%s_%s' % (backprefix, ts, '.bak'))
    bk = os.path.normpath(bk)
    with open(bk, 'xb') as f:
        f.write(io.open(target, 'rb').read())
    assert hashlib.sha256(io.open(bk, 'rb').read()).hexdigest().upper() == sha0

    sep = '' if before.endswith('\n') else '\n'
    new = before + sep + '\n' + sec.rstrip('\n') + '\n'
    assert new.count('\r\n') == expect_crlf, new.count('\r\n')
    assert len([1 for l in new.split('\n') if l.startswith(marker_prefix)]) == 1

    with open(target, 'wb') as f:
        f.write(new.encode('utf-8'))
    back = io.open(target, encoding='utf-8', newline='').read()
    assert back == new
    assert back.count('\r\n') == expect_crlf
    assert back.startswith(before[:3000])
    print('AFTER  %-22s bytes=%d CRLF=%d (+%d)' %
          (os.path.basename(target), os.path.getsize(target), back.count('\r\n'),
           os.path.getsize(target) - bytes0))
    print('OK', os.path.basename(target))

if __name__ == '__main__':
    append(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R14_COMMON.md',
           r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\_r37\s224.md',
           1081, '## 2.24', 'R14_COMMON')
