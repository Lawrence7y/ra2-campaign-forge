#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""write_r104.py —— R104 四件套写入器（写入纪律：唯一备份 -> 断言旧 sha/CR -> 一次性写 -> 回读校验）

四件套：
  R14_COMMON.md              新增 ## 2.108（全 LF；CR 保持 1081）
  GOAL_THREE_TARGETS_*.md    新增 ## §1158（CR 保持 337）
  LEAD_LOCK                  新增下一字母段 EF（CR 保持 137）
  STATUS_BOARD.md            新增第 104 轮记录（全 LF；CR 保持 0；<= 300 行）

本轮新增段落里所有「反引号」一律用全角引号代替（写作纪律）。
"""
import hashlib, io, os, sys, time

ROOT = '/home/t628/projects/ra2-campaign-forge'
os.chdir(ROOT)
R14 = 'lead/next_re_20261117_r14'
BAK = os.path.join(R14, 'R17_LEAD_BASELINE')
STAMP = time.strftime('%Y%m%d_%H%M%S')

TARGETS = [
    (os.path.join(R14, 'R14_COMMON.md'), 1081),
    ('lead/GOAL_THREE_TARGETS_20261018.md', 337),
    ('lead/LEAD_LOCK', 137),
    (os.path.join(R14, 'STATUS_BOARD.md'), 0),
]

def sha(b):
    return hashlib.sha256(b).hexdigest()

def backup(path, tag):
    os.makedirs(BAK, exist_ok=True)
    src = io.open(path, 'rb').read()
    dst = os.path.join(BAK, '%s.before_R104_%s_%s.bak' % (os.path.basename(path), tag, STAMP))
    fd = os.open(dst, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)   # wx 模式独占创建
    try:
        os.write(fd, src)
    finally:
        os.close(fd)
    assert io.open(dst, 'rb').read() == src, 'backup mismatch'
    return dst, sha(src), src

def write_once(path, old_sha, new_bytes, new_cr, tag):
    # 断言写前状态未变
    cur = io.open(path, 'rb').read()
    assert sha(cur) == old_sha, 'file changed under us: %s' % path
    with io.open(path, 'wb') as f:
        f.write(new_bytes)
    back = io.open(path, 'rb').read()
    assert sha(back) == sha(new_bytes), 'read-back sha mismatch %s' % path
    assert back.count(b'\r\n') == new_cr, 'CR mismatch %s: %d != %d' % (path, back.count(b'\r\n'), new_cr)
    print('WROTE %s (%d B, CR=%d)' % (path, len(back), back.count(b'\r\n')))

def append_lf(path, block, new_cr, tag):
    dst, old_sha, cur = backup(path, tag)
    assert cur.count(b'\r\n') == new_cr, 'pre-CR mismatch %s %d != %d' % (path, cur.count(b'\r\n'), new_cr)
    assert '`' not in block, 'block contains backtick'
    data = block.encode('utf-8')
    if not cur.endswith(b'\n'):
        cur = cur + b'\n'
    new = cur + data
    write_once(path, old_sha, new, new_cr, tag)
    return dst

def run():
    import pickle
    blocks = pickle.load(open('/tmp/r104_blocks.pkl', 'rb'))
    # 每个 block 必须以恰好一个换行开头、以恰好一个换行结尾（全 LF）
    for k in blocks:
        b = blocks[k]
        assert '\r' not in b and '`' not in b, k
        if not b.startswith('\n'):
            b = '\n' + b
        if not b.endswith('\n'):
            b = b + '\n'
        blocks[k] = b
    results = {}
    # 1) R14_COMMON：CR 保持 1081
    p = os.path.join(R14, 'R14_COMMON.md')
    pre = io.open(p, 'rb').read()
    assert pre.count(b'\r\n') == 1081, pre.count(b'\r\n')
    assert blocks['R14'].encode('utf-8') not in pre, 'block already present'
    results['R14_COMMON'] = append_lf(p, blocks['R14'], 1081, 'sec2108')
    # 2) ledger：CR 保持 337
    p = 'lead/GOAL_THREE_TARGETS_20261018.md'
    pre = io.open(p, 'rb').read()
    assert pre.count(b'\r\n') == 337, pre.count(b'\r\n')
    assert blocks['LEDGER'].encode('utf-8') not in pre
    results['LEDGER'] = append_lf(p, blocks['LEDGER'], 337, 'sec1158')
    # 3) LEAD_LOCK：CR 保持 137
    p = 'lead/LEAD_LOCK'
    pre = io.open(p, 'rb').read()
    assert pre.count(b'\r\n') == 137, pre.count(b'\r\n')
    assert blocks['LOCK'].encode('utf-8') not in pre
    results['LEAD_LOCK'] = append_lf(p, blocks['LOCK'], 137, 'segEF')
    # 4) STATUS_BOARD：CR 保持 0，且总行数 <= 300
    p = os.path.join(R14, 'STATUS_BOARD.md')
    pre = io.open(p, 'rb').read()
    assert pre.count(b'\r\n') == 0
    assert blocks['BOARD'].encode('utf-8') not in pre
    results['STATUS_BOARD'] = append_lf(p, blocks['BOARD'], 0, 'round104')
    post = io.open(p, 'rb').read()
    n_lines = post.count(b'\n') + (0 if post.endswith(b'\n') else 1)
    assert n_lines <= 300, 'board lines %d > 300' % n_lines
    print('BOARD lines now', n_lines)
    print('BACKUPS', json_stub(results))
    return results

def json_stub(d):
    import json
    return json.dumps(d, ensure_ascii=False, indent=1)

if __name__ == '__main__':
    print('STAMP', STAMP)
    run()
