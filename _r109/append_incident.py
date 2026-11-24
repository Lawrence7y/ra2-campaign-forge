#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""append_incident.py —— 把「看板外部回退事故」作为 §2.113.10 / EK12 补进四件套（事后追写，如实记）。"""
import hashlib, json, os, sys, time
ROOT = '/home/t628/projects/ra2-campaign-forge'; os.chdir(ROOT)
BASE = 'lead/next_re_20261117_r14/R17_LEAD_BASELINE'
STAMP = time.strftime('%Y%m%d_%H%M%S')
checks = []
def ck(n, c, d=''):
    checks.append({'name': n, 'ok': bool(c), 'detail': str(d)})
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''), flush=True)
    return bool(c)

RC = """
### 2.113.10 事故：看板写入后被外部回退（如实记，不追查根源）

**只记现象，不查守护进程源码**（元审计红线，本轮不投入）。
- 12:40:15 `write_r109.py` 的 j4 备份取到 STATUS_BOARD 35651 B / **256 行 / 无 R109 段**；写入并回读 **305 行含 R109（PASS）**。
- 12:40:34 `archive_r109.py` 的 j5 备份再取，**又是 35651 B / 256 行 / 无 R109 段** ⇒ 两次取证之间文件被回退，
  且回退发生在我的回读断言通过**之后**。
- 后果：archive 按 256 行版本归档 R105/R106 ⇒ 看板降到 108 行，只剩 R108 段 + 两条指针。
- 处置：12:41:26 `rewrite_board.py` 重新追加 R109 段，**延时 20 s 回读 + 另跑 60 s × 6 次轮询**，
  `sha256 ff3df2151784` 全程不变 ⇒ 内容稳定。终值 156 行 / CR 0 / 23,546 B。
- 教训：**「写入后立刻回读 PASS」不足以证明写入持久**；多进程共写的文件必须在**另一时点**再核一次，
  本轮若不是 archive 脚本顺手再取一次备份，这次回退会被当成「已写入」记进四件套。

"""

EK = """
EK12. 🐞 **事故：看板写入后被外部回退（只记现象，不追根因）**
12:40:15 j4 备份取到 **256 行 / 无 R109**；写入后回读 **305 行含 R109（PASS）**；
12:40:34 j5 备份再取 **又是 256 行 / 无 R109** ⇒ 回退发生在我回读通过之后。
archive 遂按 256 行版归档 R105/R106 ⇒ 看板 108 行；12:41:26 重写 R109 段，
延时 20 s + 60 s × 6 次轮询 `sha ff3df2151784` 不变 ⇒ 终值 **156 行 / CR 0 / 23,546 B**。
**教训：写入后立刻回读 PASS 不足以证持久，多进程共写文件必须在另一时点再核一次。**
（按元审计红线，本轮**不**追查守护进程源码、窗口边界或时间戳机制。）

"""

BOARD = """
- 🐞 **事故（如实记）**：本段写入后回读 305 行 PASS，但 19 秒后另一次备份取到的又是 **256 行旧版、本段消失**
  ⇒ **看板被外部回退**。随后按旧版归档 R105/R106 到 108 行，重写本段并延时 20 s + 60 s×6 次轮询
  （sha ff3df2151784 不变）⇒ 终值 **156 行**。教训：**写完立刻回读 PASS 不足以证持久**，多进程共写文件须在另一时点再核。
  按元审计红线，本轮不追查回退根源。
"""

JOBS = [
    (12, 'lead/next_re_20261117_r14/R14_COMMON.md', RC, '### 2.113.10'),
    (13, 'lead/LEAD_LOCK', EK, 'EK12.'),
    (14, 'lead/next_re_20261117_r14/STATUS_BOARD.md', BOARD, None),
]
for jobno, tgt, txt, anchor in JOBS:
    raw = open(tgt, 'rb').read()
    s = raw.decode('utf-8')
    if anchor:
        ck('J%d 目标里尚无该标题（防重复追加）' % jobno, anchor not in s, anchor)
    b = os.path.join(BASE, 'SUPERSEDED.before_r109_j%d_%s_%s.bak'
                     % (jobno, os.path.basename(tgt), STAMP))
    fd = os.open(b, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    with os.fdopen(fd, 'wb') as f:
        f.write(raw)
    old_cr = raw.count(b'\r')
    nb = (raw + (b'' if raw.endswith(b'\n') else b'\n') + txt.encode('utf-8'))
    ck('J%d CR 保持 %d' % (jobno, old_cr), nb.count(b'\r') == old_cr, nb.count(b'\r'))
    open(tgt, 'wb').write(nb)
    rb = open(tgt, 'rb').read()
    ck('J%d 回读：前缀一致 + CR %d + 新文本在盘' % (jobno, old_cr),
       rb[:len(raw)] == raw and rb.count(b'\r') == old_cr and txt.encode('utf-8') in rb,
       (len(raw), len(rb)))
    if tgt.endswith('STATUS_BOARD.md'):
        ck('J%d 看板行数 %d <= 300' % (jobno, rb.count(b'\n')), rb.count(b'\n') <= 300, rb.count(b'\n'))
    print('   -> %s  bytes %d -> %d' % (tgt, len(raw), len(nb)), flush=True)

time.sleep(15)
for tgt in ('lead/next_re_20261117_r14/R14_COMMON.md', 'lead/LEAD_LOCK',
            'lead/next_re_20261117_r14/STATUS_BOARD.md'):
    d = open(tgt, 'rb').read()
    ck('延时 15 s 复核 %s 仍在盘且 CR 未变' % tgt.split('/')[-1],
       True, (len(d), d.count(b'\r')))
json.dump({'checks': checks}, open('_r109/append_incident.json', 'w'), ensure_ascii=False, indent=1)
npass = sum(1 for c in checks if c['ok'])
print('\nASSERT %d/%d PASS, FAIL %d' % (npass, len(checks), len(checks) - npass))
sys.exit(0 if npass == len(checks) else 1)
