# -*- coding: utf-8 -*-
"""R126j: 把本轮的两处门禁改动补进四件套（第四节收口）。

既有 r126h 写的段里只写了「本轮不改门禁」，那是写那段时的状态；随后我在收口时
真的改了门禁（C16 重钉 + GATE_VER 升版）。按「如实记录」纪律，不回头改那一段，
而是追加一小段「收口期追加」，把改动、依据与反控一并写清。

同样纪律：wx 备份 -> 断言旧 sha 与 CR -> 断言新文本零反引号 -> 单次写入 -> 回读。
"""
import io, os, hashlib, datetime

ROOT = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
BK = os.path.join(R14, 'R17_LEAD_BASELINE')
RC = os.path.join(R14, 'R14_COMMON.md')
LED = os.path.join(ROOT, 'lead', 'GOAL_THREE_TARGETS_20261018.md')
LOCK = os.path.join(ROOT, 'lead', 'LEAD_LOCK')
BRD = os.path.join(R14, 'STATUS_BOARD.md')

EXPECT = {
    RC:  ('7951e620a6c8604b', 1081),
    LED: ('9569b581d4896398', 337),
    LOCK: ('64737be1219c69d7', 137),
    BRD: ('27184aa1271d87f1', 0),
}
TS = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

def sha16(b):
    return hashlib.sha256(b).hexdigest()[:16]

def do(path, tag, new_text, want_cr, sep='\n'):
    assert '`' not in new_text, '%s 新文本含反引号' % tag
    old = io.open(path, 'rb').read()
    dst = os.path.join(BK, 'r126_%s_%s.bak' % (tag, TS))
    fd = os.open(dst, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
    try:
        os.write(fd, old)
    finally:
        os.close(fd)
    want_sha, want_cr = EXPECT[path]
    assert sha16(old) == want_sha, '%s 旧 sha %s != %s' % (tag, sha16(old), want_sha)
    assert old.count(b'\r') == want_cr, '%s 旧 CR %d != %d' % (tag, old.count(b'\r'), want_cr)
    new = old.decode('utf-8').rstrip('\n') + '\n' + new_text
    nb = new.encode('utf-8')
    with io.open(path, 'wb') as f:
        f.write(nb)
    rb = io.open(path, 'rb').read()
    assert rb == nb, '%s 回读不一致' % tag
    assert rb.count(b'\r') == want_cr, '%s 新 CR %d != %d' % (tag, rb.count(b'\r'), want_cr)
    print('  WROTE %-10s sha %s -> %s CR=%d bytes %d -> %d'
          % (tag, sha16(old), sha16(rb), rb.count(b'\r'), len(old), len(rb)))


ADD_RC = '''
**十 · 收口期追加：本轮确实改了门禁，两处，都带反控**

上面第八节写「本轮不改门禁」时是当时的真实状态。随后在收口发现两件事，改了两处，如实补记，不改上文。

改动一 · C16_FLOORS 重钉。新增 2.129 与 2.130 两节后，表外未钉节数正好顶到上限 2。门禁当时仍 exit 0，但那意味着下一轮再加一节就会撞上限。按既有 50% 规则补钉 130 节（实测 2.129 = 7258 B 取 3629、2.130 = 7445 B 取 3722），表从 122 条到 124 条，摘要常量从 689f9c12 改为 eb8cc052。重钉后 unpinned 2 到 0、hollow 0、missing 0。

改动二 · GATE_VER 从 R124 升到 R126，并同步 DISC_RECHECK 第 20 行的登记式。依据是 C10 门自检：登记行里的版本标记必须与脚本里的 GATE_VER 相等，而我本轮确实动了门禁脚本，不升版会让该行指向一个已不存在的脚本状态。

反控（r126i，7 项全 PASS）。这里有一条我自己先踩的坑（S-161）：第一版把门禁脚本拷到临时目录再跑，可它读文档用的是写死的绝对路径，于是临时副本仍在读原目录的文档，三条反控的 exit 都是 1 却全是脚本报错，不是我想要的 FAIL。改成「把正本改名藏起来、把改过的副本放到正本路径上跑、finally 里恢复并断言 sha」之后才真生效：

1) 正控：不做任何修改必须 PASS（exit 0）。
2) 把 2.130 正文清空到只剩标题，必须 FAIL 且命中 C16 —— 实测 exit 1、命中 C16，证明 130:3722 这道下界真的在约束。
3) 只把 GATE_VER 改成 R999 而不动第 20 行，必须 FAIL 且命中 C10 —— 实测 exit 1、命中 C10。
4) 把 C16_FLOORS 里 130 的 3722 改成 3700 而不改摘要常量，必须 FAIL 且命中 C16d —— 实测 exit 1、命中 C16d。
5) 收尾断言三个正本（check_disc.py、DISC_RECHECK.tsv、R14_COMMON.md）的字节与开工时一致，证明反控没有污染正本。

结论：这两处改动都是把门禁收紧（补钉 = 增加被约束的节数；升版 = 让 C10 继续有效），不是放松。终态 check_disc.py exit 0，C10 显示 ok(R126)。
'''

ADD_LED = '''
**收口期追加 · 门禁两处改动（带反控）**：一，C16_FLOORS 从 122 条补钉到 124 条（新增 2.129 = 3629、2.130 = 3722，按实测字节的一半），摘要常量 689f9c12 改为 eb8cc052；重钉后表外未钉节数 2 到 0。二，GATE_VER 由 R124 升到 R126 并同步 DISC_RECHECK 第 20 行。反控（r126i，7 项全 PASS，本轮自错 S-161）：第一版把门禁脚本拷到临时目录跑无效，因为它读文档用写死的绝对路径，临时副本仍读原目录；改为「正本改名藏起、改过的副本放到正本路径、finally 恢复并断言 sha」后生效。四条结果：正控 exit 0；清空 2.130 正文 exit 1 且命中 C16；只改 GATE_VER 不同步第 20 行 exit 1 且命中 C10；改表不改摘要 exit 1 且命中 C16d。三份正本字节与开工时一致。两处改动方向都是收紧，不是放松。
'''

ADD_LOCK = '''
GL. 收口期追加（如实记，不改上文）：本轮确实动了门禁，两处。其一 C16_FLOORS 从 122 条补钉到 124 条（2.129 实测 7258 B 取 3629、2.130 实测 7445 B 取 3722，按半量规则），摘要常量 689f9c12 改为 eb8cc052，重钉后 unpinned 2 到 0、hollow 0、missing 0。其二 GATE_VER 由 R124 升到 R126，并同步 DISC_RECHECK 第 20 行的登记式，依据是 C10 门自检要求登记行版本与脚本一致，而我本轮确实动了门禁脚本。

GM. 反控 r126i 共 7 项全 PASS，过程中踩到自错 S-161：第一版把 check_disc.py 拷到临时目录跑，但它读文档用的是写死的绝对路径，于是临时副本仍在读原目录文档，三条反控的 exit 都是 1 却全是脚本报错而非我要的 FAIL。改为「正本改名藏起、把改过的副本放到正本路径上跑、finally 恢复并断言 sha」后真生效：正控 exit 0；清空 2.130 正文 exit 1 命中 C16；只改 GATE_VER 不同步第 20 行 exit 1 命中 C10；改 C16_FLOORS 一个数不改摘要 exit 1 命中 C16d。收尾断言 check_disc.py、DISC_RECHECK.tsv、R14_COMMON.md 三个正本字节与开工时一致。两处改动方向都是收紧而非放松；终态 check_disc.py exit 0，C10 显示 ok(R126)。
'''

ADD_BOARD = '''
### 十 · 收口期追加：本轮确实改了门禁（两处，均带反控）

上节写「本轮不改门禁」时是当时状态。收口时改了两处并补记。

一，C16_FLOORS 重钉：新增 2.129 与 2.130 后表外未钉节数正好顶到上限 2，下一轮再加节就会撞线。按半量规则补钉 130 节（实测 2.129 = 7258 B 取 3629、2.130 = 7445 B 取 3722），表 122 到 124 条，摘要常量 689f9c12 改为 eb8cc052；重钉后 unpinned 2 到 0。

二，GATE_VER 从 R124 升到 R126，并同步 DISC_RECHECK 第 20 行登记式 —— C10 门自检要求二者一致，而本轮确实动了门禁脚本。

反控 r126i 共 7 项全 PASS。这里我先踩了一个坑（S-161）：第一版把门禁脚本拷到临时目录跑，可它读文档用写死的绝对路径，临时副本仍在读原目录，三条反控的 exit 都是 1 但全是脚本报错、不是我想要的 FAIL。改成「正本改名藏起、改过的副本放到正本路径跑、finally 恢复并断言 sha」之后才生效：正控 exit 0；清空 2.130 正文 exit 1 命中 C16；只改 GATE_VER 不同步第 20 行 exit 1 命中 C10；改表不改摘要 exit 1 命中 C16d；三份正本字节与开工时一致。两处改动方向都是收紧，终态 check_disc.py exit 0、C10 显示 ok(R126)。
'''

do(RC, 'R14_COMMON', ADD_RC, 1081)
do(LED, 'LEDGER', ADD_LED, 337)
do(LOCK, 'LEAD_LOCK', ADD_LOCK, 137)
do(BRD, 'BOARD', ADD_BOARD, 0)
print('DONE')
