#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fix_board_note.py —— 修正四件套里已过期的「看板不归档」表述，并如实记入外部回退事故。

事实链（只记现象，不查守护进程源码 —— 元审计红线）：
  12:40:15 j4 备份取到 256 行（无 R109）；写入后回读 305 行含 R109（PASS）；
  12:40:34 j5 备份再取，**又是 35651 B / 256 行 / 无 R109** ⇒ 两次取证之间文件被回退；
  随后按 256 行版归档 R105/R106 ⇒ 看板 108 行；12:41:26 重写 R109 段后延时 20 s + 60 s 连续 6 次
  回读内容稳定（23356 B / 156 行 / sha ff3df2151784 不变）。
故四件套里「开局 256 行 < 260 ⇒ 不归档」这句**已过期**，必须改成实际发生的两步。
"""
import hashlib, io, json, os, sys, time

ROOT = '/home/t628/projects/ra2-campaign-forge'
os.chdir(ROOT)
BASE = 'lead/next_re_20261117_r14/R17_LEAD_BASELINE'
STAMP = time.strftime('%Y%m%d_%H%M%S')
checks = []
def ck(n, c, d=''):
    checks.append({'name': n, 'ok': bool(c), 'detail': str(d)})
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''), flush=True)
    return bool(c)

OLD_RC = '看板开局 256 行 < 260 ⇒ **本轮不归档**，写入后仍 ≤ 300。'
NEW_RC = ('看板开局 256 行 < 260（按纪律不归档），但写入 R109 段后实测 **305 行 > 300** 上限，'
          '故**仍须归档**：把 R105 / R106 两段逐字搬进 BOARD_ARCHIVE（missing=0，归档 CR 保持 2952），'
          '看板降到 **108 行**。归档随后发现**外部回退事故**（见 2.113.10）：12:40:15 与 12:40:34 两次备份'
          '取到的都是 256 行旧版本、R109 段消失；重写后延时 20 s + 60 s 连续 6 次回读稳定'
          '（23,356 B / 156 行 / sha ff3df2151784），最终看板 **156 行 ≤ 300**、CR 0。')

OLD_LED = '`check_disc.py` exit 0；五项 CR 全绿；看板 256 行 < 260 **不归档**；\n收口前 `ps` 核对无 `r109*` 孤儿进程。'
NEW_LED = ('`check_disc.py` exit 0；五项 CR 全绿（1081 / 137 / 337 / 0 / 2952）；'
           '看板开局 256 行虽 < 260，但写入后 **305 行 > 300** ⇒ 归档 R105/R106（missing=0，归档 CR 2952）到 108 行；'
           '归档后发现**外部回退**（两次备份均为 256 行旧版、R109 段消失），重写后连续 6 次延时回读稳定 ⇒ 终值 **156 行**；\n'
           '收口前 `ps` 核对无 `r109*` 孤儿进程。')

OLD_LOCK = ('`check_disc.py` **exit 0**；五项 CR 全绿（1081 / 137 / 337 / 0 / 2952）；\n'
            '看板开局 **256 行 < 260 ⇒ 本轮不归档**，写入后仍 ≤ 300；收口前 `ps` 核对无 `r109*` 孤儿进程。')
NEW_LOCK = ('`check_disc.py` **exit 0**；五项 CR 全绿（1081 / 137 / 337 / 0 / 2952）；\n'
            '看板开局 **256 行 < 260**（按纪律不归档），但写入 R109 段后实测 **305 行 > 300** ⇒ **仍须归档**：\n'
            'R105/R106 逐字搬入 BOARD_ARCHIVE（missing=0，归档 CR 保持 2952）降到 108 行；\n'
            '归档后又抓到**外部回退**（12:40:15 / 12:40:34 两次备份都是 256 行旧版、R109 段消失），\n'
            '重写并延时 20 s + 60 s 连续 6 次回读稳定 ⇒ 终值 **156 行**、CR 0；收口前 `ps` 核对无 `r109*` 孤儿进程。')

OLD_BOARD = '看板开局 **256 行 < 260 ⇒ 不归档**，写入后 ≤ 300；无 `r109*` 孤儿进程。'
NEW_BOARD = ('看板开局 256 行 < 260，但写入本段后 **305 行 > 300** ⇒ **仍归档** R105/R106 到 108 行；'
             '归档后抓到**外部回退**（两次备份均 256 行旧版、本段消失），重写后连续 6 次延时回读稳定 ⇒ 终值 **156 行**；'
             '无 `r109*` 孤儿进程。')

JOBS = [
    (8, 'lead/next_re_20261117_r14/R14_COMMON.md', OLD_RC, NEW_RC),
    (9, 'lead/GOAL_THREE_TARGETS_20261018.md', OLD_LED, NEW_LED),
    (10, 'lead/LEAD_LOCK', OLD_LOCK, NEW_LOCK),
    (11, 'lead/next_re_20261117_r14/STATUS_BOARD.md', OLD_BOARD, NEW_BOARD),
]
for jobno, tgt, old, new in JOBS:
    raw = open(tgt, 'rb').read()
    s = raw.decode('utf-8')
    ck('J%d 旧表述存在且唯一' % jobno, s.count(old) == 1, s.count(old))
    b = os.path.join(BASE, 'SUPERSEDED.before_r109_j%d_%s_%s.bak'
                     % (jobno, os.path.basename(tgt), STAMP))
    fd = os.open(b, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    with os.fdopen(fd, 'wb') as f:
        f.write(raw)
    old_cr = raw.count(b'\r')
    s2 = s.replace(old, new, 1)
    nb = s2.encode('utf-8')
    ck('J%d 新文本无 CR 且 CR 不变量保持 %d' % (jobno, old_cr), nb.count(b'\r') == old_cr, nb.count(b'\r'))
    open(tgt, 'wb').write(nb)
    rb = open(tgt, 'rb').read().decode('utf-8')
    ck('J%d 回读：旧表述已不存在、新表述存在 1 次' % jobno,
       old not in rb and rb.count(new) == 1, (old in rb, rb.count(new)))
    print('   -> %s  CR %d  bytes %d -> %d' % (tgt, rb.encode().count(b'\r'), len(raw), len(nb)), flush=True)

json.dump({'checks': checks}, open('_r109/fix_board_note.json', 'w'), ensure_ascii=False, indent=1)
npass = sum(1 for c in checks if c['ok'])
print('\nASSERT %d/%d PASS, FAIL %d' % (npass, len(checks), len(checks) - npass))
sys.exit(0 if npass == len(checks) else 1)
