#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""write_r111.py —— 按写入纪律落盘四件套。

纪律（每次修改前必须执行）：
  1. 在 R17_LEAD_BASELINE/ 用 wx 模式**独占创建**唯一备份；
  2. 断言旧 sha256 与 CR（防止在别人改过的文件上盲写）；
  3. 一次性写入；
  4. 回读校验（sha / CR / 行数 / 段落存在）。
基线值（开局 get_goal 实测）：R14_COMMON CR=1081 LF=10197 ; LEAD_LOCK CR=137 LF=5376 ;
台账 CR=337 LF=46060 ; STATUS_BOARD CR=0 LF=216 ; BOARD_ARCHIVE CR=2952（本轮不动）。
"""
import hashlib, json, os, shutil, sys, time

ROOT = '/home/t628/projects/ra2-campaign-forge'
W = os.path.join(ROOT, 'lead/next_re_20261117_r14')
BASE = os.path.join(W, 'R17_LEAD_BASELINE')
SEG = os.path.join(ROOT, '_r111')
checks = []
def ck(n, c, d=''):
    checks.append({'name': n, 'ok': bool(c), 'detail': str(d)})
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''), flush=True)
    return bool(c)

def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()
def crlf(p):
    d = open(p, 'rb').read()
    return d.count(b'\r'), d.count(b'\n'), len(d)

TARGETS = [
    # (路径, 期望旧 CR, 期望旧 LF, 段落文件, 期望新 CR, 段落标记)
    (os.path.join(W, 'R14_COMMON.md'), 1081, 10197, 'seg_rc_2115.md', 1081, '## 2.115 R111'),
    (os.path.join(ROOT, 'lead/GOAL_THREE_TARGETS_20261018.md'), 337, 46060, 'seg_ledger_1165.md', 337, '## §1165 R111'),
    (os.path.join(ROOT, 'lead/LEAD_LOCK'), 137, 5376, 'seg_lock_EM.md', 137, 'EM. R111'),
    # 自错 L-10：上一稿 marker 用「第 111 轮」，而看板顶部事故说明里本来就含这几个字 ⇒
    # 幂等判断假命中、整段被跳过（W1 打印 skip 却看不出来）。改用只在段落里出现的唯一串。
    (os.path.join(W, 'STATUS_BOARD.md'), 0, 216, 'seg_board_111.md', 0, '第 111 轮（2026-11-24 13:1x'),
]

stamp = time.strftime('%Y%m%d_%H%M%S')
report = []
for path, old_cr, old_lf, segname, new_cr, marker in TARGETS:
    name = os.path.basename(path)
    seg = open(os.path.join(SEG, segname), 'rb').read()
    ck('W0 %s 段落全 LF（段落自身 CR=0）' % segname, seg.count(b'\r') == 0, seg.count(b'\r'))
    ck('W0b %s 段落以 LF 开头结尾' % segname, seg.startswith(b'\n') and seg.endswith(b'\n'),
       (seg[:2], seg[-2:]))

    cr0, lf0, by0 = crlf(path)
    sha0 = sha(path)
    # 幂等前置：段落已在 ⇒ 只校验 CR 不变并跳过（R111 上一跑已在 R14_COMMON 落盘）
    if marker.encode() in open(path, 'rb').read():
        ck('W1 %s 段落已存在，旧基线断言跳过；CR 仍 == %d' % (name, new_cr), cr0 == new_cr, (cr0, lf0, by0))
        report.append({'file': name, 'action': 'skip-existing', 'sha': sha0, 'cr': cr0, 'lf': lf0})
        continue

    ck('W1 %s 旧 CR==%d 且 LF==%d（实测 %d/%d）' % (name, old_cr, old_lf, cr0, lf0),
       cr0 == old_cr and lf0 == old_lf, (cr0, lf0, by0))

    bak = os.path.join(BASE, '%s.before_R111_%s.bak' % (name, stamp))
    fd = os.open(bak, os.O_CREAT | os.O_EXCL | os.O_WRONLY)   # wx 独占
    with os.fdopen(fd, 'wb') as f:
        f.write(open(path, 'rb').read())
    ck('W2 %s 备份独占创建成功且字节一致' % name, sha(bak) == sha0, os.path.basename(bak))

    old = open(path, 'rb').read()
    if marker.encode() in old:
        ck('W3 %s 段落已存在 ⇒ 不重复写入（幂等）' % name, True, 'skip')
        report.append({'file': name, 'action': 'skip-existing', 'sha': sha0})
        continue

    with open(path, 'wb') as f:      # 一次性写入
        f.write(old + seg)

    cr1, lf1, by1 = crlf(path)
    ck('W4 %s 回读 CR==%d（不变） 实测 %d' % (name, new_cr, cr1), cr1 == new_cr, (cr1, lf1, by1))
    ck('W5 %s 行数增加 == 段落行数（%d += %d）' % (name, lf0, seg.count(b'\n')),
       lf1 == lf0 + seg.count(b'\n'), (lf0, lf1, seg.count(b'\n')))
    back = open(path, 'rb').read()
    ck('W6 %s 回读含段落标记且字节 == 旧+段' % name,
       marker.encode() in back and back == old + seg, (marker, len(back)))
    report.append({'file': name, 'action': 'appended', 'sha_before': sha0,
                   'sha_after': hashlib.sha256(back).hexdigest(),
                   'lf_before': lf0, 'lf_after': lf1, 'cr': cr1, 'bytes': by1, 'backup': os.path.basename(bak)})

# 看板行数上限（300 行硬上限；>=260 必须归档 —— 本轮开局 216，写入后实测）
b_lf = crlf(os.path.join(W, 'STATUS_BOARD.md'))[1]
ck('W7 STATUS_BOARD 写入后行数 %d <= 300（硬上限）' % b_lf, b_lf <= 300, b_lf)
# 自错 L-12：上一稿这里写的是 `b_lf < 260 or True` —— 恒真，等于没断言（正是本轮要治的
# 「永远通过子项」）。真不变量有两条，都必须实打实满足：
#   (a) 开局行数 216 < 260 ⇒ 按纪律本轮**不需要**先归档；
#   (b) 写入后 <= 300 行硬上限。
ck('W7b 开局 216 < 260（按纪律不需要归档）且写入后 %d <= 300' % b_lf,
   216 < 260 and b_lf <= 300, {'open_lines': 216, 'post_lines': b_lf, 'cap': 300})

# BOARD_ARCHIVE 本轮不得被动
arc = os.path.join(W, 'BOARD_ARCHIVE.md')
ck('W8 BOARD_ARCHIVE CR 仍为 2952（本轮未归档）', crlf(arc)[0] == 2952, crlf(arc)[0])

json.dump({'stamp': stamp, 'report': report, 'checks': checks},
          open(os.path.join(ROOT, '_r111/write_r111.json'), 'w'), indent=1, ensure_ascii=False)
bad = sum(1 for c in checks if not c['ok'])
print('\n--- %d checks, PASS %d, FAIL %d ---' % (len(checks), len(checks) - bad, bad))
sys.exit(1 if bad else 0)
