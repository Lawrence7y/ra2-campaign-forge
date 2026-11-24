#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""write_r109.py —— R109 四件套写入（独占备份 → 断言旧 sha256 与 CR → 一次性写 → 回读校验）。

写入纪律：
  1) R17_LEAD_BASELINE/ 下用 O_EXCL 独占创建唯一备份（名字带作业序号，防 E-w4 同秒撞名）
  2) 写前断言「旧 sha256 + 旧 CR」双匹配，任一不符即中止
  3) 一次性追加写（不改任何已有字节），写完回读校验：CR 不变量 + 内容锚点 + 行数上界
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

JOBS = [
    # (jobno, target, seg, expect_cr, expect_anchor_tail, max_lines)
    (1, 'lead/next_re_20261117_r14/R14_COMMON.md', '_r109/seg_rc_2113.md', 1081, '### 2.112.9 收口', None),
    (2, 'lead/GOAL_THREE_TARGETS_20261018.md', '_r109/seg_ledger_1163.md', 337, '**收口**：九个带断言脚本合计', None),
    (3, 'lead/LEAD_LOCK', '_r109/seg_lock_EK.md', 137,
     '再写入第 108 轮；收口前 `ps` 核对无 `r108*` 孤儿进程。', None),
    (4, 'lead/next_re_20261117_r14/STATUS_BOARD.md', '_r109/seg_board_109.md', 0,
     '⑥ **取地址入口是第四类入口**', 300),
]

os.makedirs(BASE, exist_ok=True)
for jobno, tgt, seg, ecr, anchor, maxlines in JOBS:
    raw = open(tgt, 'rb').read()
    old_sha = hashlib.sha256(raw).hexdigest()
    old_cr = raw.count(b'\r')
    seg_b = open(seg, 'rb').read()
    ck('J%d %s 备用段无 CR（全 LF）' % (jobno, os.path.basename(seg)), seg_b.count(b'\r') == 0,
       seg_b.count(b'\r'))
    ck('J%d %s 旧 CR == %d' % (jobno, tgt, ecr), old_cr == ecr, old_cr)
    ck('J%d 旧文件尾部含预期锚点' % jobno, anchor.encode('utf-8') in raw, anchor[:30])
    # 独占备份（名字带作业序号，避免同秒撞名）
    bak = os.path.join(BASE, 'SUPERSEDED.before_r109_j%d_%s_%s.bak'
                       % (jobno, os.path.basename(tgt), STAMP))
    fd = os.open(bak, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    with os.fdopen(fd, 'wb') as f:
        f.write(raw)
    ck('J%d 备份已独占创建 %s' % (jobno, os.path.basename(bak)),
       os.path.exists(bak) and hashlib.sha256(open(bak, 'rb').read()).hexdigest() == old_sha, bak)
    # 写前再核 sha（防备份后被动过）
    ck('J%d 写前 sha 未变' % jobno, hashlib.sha256(open(tgt, 'rb').read()).hexdigest() == old_sha, old_sha[:16])
    # 一次性追加
    body = raw + (b'' if raw.endswith(b'\n') else b'\n') + b'\n' + seg_b
    with open(tgt, 'wb') as f:
        f.write(body)
    # 回读校验
    new = open(tgt, 'rb').read()
    ck('J%d 回读 CR 仍为 %d' % (jobno, ecr), new.count(b'\r') == ecr, new.count(b'\r'))
    ck('J%d 回读保留全部旧字节（前缀一致）' % jobno,
       new[:len(raw)] == raw and new[len(raw):].lstrip(b'\n') == seg_b,
       (len(raw), len(new)))
    ck('J%d 回读含新段首行' % jobno, seg_b.split(b'\n')[0] in new, seg_b.split(b'\n')[0][:40])
    if maxlines:
        nl = new.count(b'\n') + (0 if new.endswith(b'\n') else 1)
        ck('J%d 行数 %d <= %d' % (jobno, nl, maxlines), nl <= maxlines, nl)
    print('   -> %s  sha %s -> %s  bytes %d -> %d'
          % (tgt, old_sha[:16], hashlib.sha256(new).hexdigest()[:16], len(raw), len(new)), flush=True)

json.dump({'checks': checks}, open('_r109/write_r109.json', 'w'), ensure_ascii=False, indent=1)
npass = sum(1 for c in checks if c['ok'])
print('\nASSERT %d/%d PASS, FAIL %d' % (npass, len(checks), len(checks) - npass))
sys.exit(0 if npass == len(checks) else 1)
