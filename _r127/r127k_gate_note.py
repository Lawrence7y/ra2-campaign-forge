# -*- coding: utf-8 -*-
"""R127k：把「本轮不改门禁」的旧表述改成实况（本轮改了门禁两处）。

要改的四处（都是本轮自己写的文字，不是历史段）：
  R14_COMMON  2.131 第八节末句「check_disc.py exit 0（GATE_VER 仍 R126，本轮不改门禁）。」
  LEDGER      §1181 第六节同句
  LEAD_LOCK   GV 段同句
  STATUS_BOARD 第 127 轮第八节同句

每处追加一句「收口期追加」的实测记录，指向 r127j 的 10 项与三条反控。
纪律：wx 独占备份 -> 断言旧 sha 与 CR -> 逐处 replace 且断言命中次数恰 1 -> 写入 ->
回读校验（sha 变化、CR 不变、新句存在）。
"""
import io, os, sys, hashlib, datetime

ROOT = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
BK = os.path.join(R14, 'R17_LEAD_BASELINE')
RC = os.path.join(R14, 'R14_COMMON.md')
LED = os.path.join(ROOT, 'lead', 'GOAL_THREE_TARGETS_20261018.md')
LOCK = os.path.join(ROOT, 'lead', 'LEAD_LOCK')
BRD = os.path.join(R14, 'STATUS_BOARD.md')

TS = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

OLD = 'check_disc.py exit 0（GATE_VER 仍 R126，本轮不改门禁）。'
OLD_BRD = 'check_disc.py exit 0，GATE_VER 仍 R126（本轮不改门禁）。'

NEW_TAIL = ('check_disc.py exit 0。**收口期追加（如实记）**：本轮确实改了门禁两处，'
            '都带反控（r127j，10 项全 PASS）。其一 C16_FLOORS 从 124 条补钉到 125 条 —— '
            '新增 2.131 实测 11916 B，按半量规则取 5958，摘要常量 eb8cc052 改为 a87a240c，'
            '重钉后 unpinned 1 到 0、hollow 0、missing 0、min margin 1155。其二 GATE_VER '
            '由 R126 升到 R127 并同步 DISC_RECHECK 第 20 行登记式（C10 门自检要求二者一致，'
            '而本轮确实动了门禁脚本）。反控三条：正控 exit 0；清空 2.131 正文 exit 1 命中 '
            'C16 并报 (131, 15, 5958)；只改 GATE_VER 不改登记行 exit 1 命中 C7 id 20 与 '
            'C10；改 131 的下界不改摘要 exit 1 命中 C16d；收尾断言三个正本字节与改动完成时'
            '一致。两处改动方向都是收紧。终态 check_disc.py exit 0、C10 显示 ok(R127)。')

TARGETS = [
    (RC,   'R14_COMMON',    1081, OLD,     None),
    (LED,  'LEDGER',         337, OLD,     None),
    (LOCK, 'LEAD_LOCK',      137, OLD,     None),
    (BRD,  'STATUS_BOARD',     0, OLD_BRD, None),
]


def sha16(b):
    return hashlib.sha256(b).hexdigest()[:16]


def one(path, tag, want_cr, old_s, new_s):
    old_b = io.open(path, 'rb').read()
    dst = os.path.join(BK, 'r127k_%s.%s.bak' % (tag, TS))
    fd = os.open(dst, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
    try:
        os.write(fd, old_b)
    finally:
        os.close(fd)
    assert old_b.count(b'\r') == want_cr, '%s 旧 CR %d != %d' % (
        tag, old_b.count(b'\r'), want_cr)
    t = old_b.decode('utf-8')
    n = t.count(old_s)
    assert n == 1, '%s 要替换的句子出现 %d 次（应为 1）' % (tag, n)
    assert '`' not in new_s, '%s 新句含反引号' % tag
    t2 = t.replace(old_s, new_s, 1)
    nb = t2.encode('utf-8')
    with io.open(path, 'wb') as f:
        f.write(nb)
    rb = io.open(path, 'rb').read()
    assert rb == nb, '%s 回读不一致' % tag
    assert rb.count(b'\r') == want_cr, '%s 新 CR %d != %d' % (
        tag, rb.count(b'\r'), want_cr)
    assert new_s.encode('utf-8') in rb, '%s 回读未见新句' % tag
    print('  WROTE %-12s sha %s -> %s  CR=%d  bytes %d -> %d'
          % (tag, sha16(old_b), sha16(rb), rb.count(b'\r'), len(old_b), len(rb)))


def main():
    for path, tag, cr, old_s, _ in TARGETS:
        one(path, tag, cr, old_s, NEW_TAIL)
    print('DONE')


if __name__ == '__main__':
    main()
