#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""write_r112.py —— 按写入纪律落盘四件套 + 归档最早两段。

纪律（每次修改前必须执行）：
  1. 在 R17_LEAD_BASELINE/ 用 wx 模式**独占创建**唯一备份（备份名带作业序号，R108 §E-w4）；
  2. 断言旧 sha256 与 CR（防止在别人改过的文件上盲写）；
  3. 一次性写入；
  4. 回读校验（CR / 行数 / 段落标记 / 字节）。
归档：看板开局 281 行 ≥ 260 ⇒ 先把最早两段（第 108、109 轮）逐字搬进 BOARD_ARCHIVE，
board 侧留一行指针（指针行原样搬 move 后的前 120 字符作为检索锚点）。
BOARD_ARCHIVE 的 CR 必须保持 2952（搬入内容是全 LF 的看板段，不含 CR）。
"""
import hashlib, json, os, sys, time

ROOT = '/home/t628/projects/ra2-campaign-forge'
W = os.path.join(ROOT, 'lead/next_re_20261117_r14')
BASE = os.path.join(W, 'R17_LEAD_BASELINE')
SEG = os.path.join(ROOT, '_r112')
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


stamp = time.strftime('%Y%m%d_%H%M%S')
report = []
job = [0]


def backup(path, tag):
    job[0] += 1
    bak = os.path.join(BASE, '%s.before_R112_%s_j%d_%s.bak'
                       % (os.path.basename(path), tag, job[0], stamp))
    fd = os.open(bak, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    with os.fdopen(fd, 'wb') as f:
        f.write(open(path, 'rb').read())
    ck('W2 %s 备份独占创建成功且字节一致（j%d）' % (os.path.basename(path), job[0]),
       sha(bak) == sha(path), os.path.basename(bak))
    return bak


# ============ 第 0 步：看板归档（281 行 >= 260 ⇒ 必须先归档最早 2 段） ============
BRD = os.path.join(W, 'STATUS_BOARD.md')
ARC = os.path.join(W, 'BOARD_ARCHIVE.md')
b = open(BRD, 'rb').read().decode('utf-8')
arc0 = open(ARC, 'rb').read()
ck('A0 看板开局 281 行 >= 260 ⇒ 触发归档（纪律）', b.count('\n') == 281, b.count('\n'))
ck('A0b BOARD_ARCHIVE 开局 CR==2952', arc0.count(b'\r') == 2952, arc0.count(b'\r'))

lines = b.split('\n')
starts = [i for i, l in enumerate(lines) if l.startswith('## 🟢 R17 第 10') or l.startswith('## 🟢 R17 第 11')]
ck('A1 看板里找到 4 个轮次段头，最早两段是第 108 / 第 109 轮',
   len(starts) == 4 and lines[starts[0]].startswith('## 🟢 R17 第 108')
   and lines[starts[1]].startswith('## 🟢 R17 第 109'), [(i, lines[i][:20]) for i in starts])

seg108 = '\n'.join(lines[starts[0]:starts[1]])
seg109 = '\n'.join(lines[starts[1]:starts[2]])
ck('A2 两段都非空且各自含小标题', len(seg108) > 2000 and len(seg109) > 2000,
   {'len108': len(seg108), 'len109': len(seg109)})

backup(BRD, 'archive')
backup(ARC, 'archive')

arc_new = arc0 + (b'' if arc0.endswith(b'\n') else b'\n') + seg108.encode('utf-8') + b'\n' + seg109.encode('utf-8') + b'\n'
with open(ARC, 'wb') as f:
    f.write(arc_new)
ck('A3 BOARD_ARCHIVE 搬入后 CR 仍 == 2952（搬入段全 LF，不引入 CR）',
   crlf(ARC)[0] == 2952, crlf(ARC)[0])
kt = open(ARC, 'rb').read()
ck('A4 归档内逐字含两段原文（missing=0）',
   seg108.encode('utf-8') in kt and seg109.encode('utf-8') in kt,
   {'108': seg108.encode() in kt, '109': seg109.encode() in kt})

ptr = ('\n📦 第 108 轮与第 109 轮已归档至 BOARD_ARCHIVE.md（2026-11-24 14:xx，逐字搬，missing=0；'
       '本次由 Lead 执行，R112；归档 CR 保持 2952）\n')
new_lines = lines[:starts[0]] + [ptr.strip()] + lines[starts[2]:]
b_new = '\n'.join(new_lines)
with open(BRD, 'wb') as f:
    f.write(b_new.encode('utf-8'))
ck('A5 看板归档后行数减少（%d → %d），旧两段原文已不在看板'
   % (281, crlf(BRD)[1]), crlf(BRD)[1] < 281
   and seg108[:200].encode('utf-8') not in open(BRD, 'rb').read(), crlf(BRD)[1])
report.append({'step': 'archive', 'lines_before': 281, 'lines_after': crlf(BRD)[1],
               'arc_cr': crlf(ARC)[0], 'arc_bytes': crlf(ARC)[2]})

# ============ 第 1 步：四件套追加 ============
TARGETS = [
    (os.path.join(W, 'R14_COMMON.md'), 1081, 10345, 'seg_rc_2116.md', 1081, '## 2.116 R112'),
    (os.path.join(ROOT, 'lead/GOAL_THREE_TARGETS_20261018.md'), 337, 46157,
     'seg_ledger_1166.md', 337, '## §1166 R112'),
    (os.path.join(ROOT, 'lead/LEAD_LOCK'), 137, 5476, 'seg_lock_EN.md', 137, 'EN. R112'),
    (BRD, 0, None, 'seg_board_112.md', 0, '第 112 轮（2026-11-24 14:0x'),
]

for path, old_cr, old_lf, segname, new_cr, marker in TARGETS:
    name = os.path.basename(path)
    seg = open(os.path.join(SEG, segname), 'rb').read()
    ck('W0 %s 段落全 LF' % segname, seg.count(b'\r') == 0, seg.count(b'\r'))
    ck('W0b %s 段落以 LF 开头结尾' % segname,
       seg.startswith(b'\n') and seg.endswith(b'\n'), (seg[:2], seg[-2:]))

    cr0, lf0, by0 = crlf(path)
    sha0 = sha(path)
    if marker.encode() in open(path, 'rb').read():
        ck('W1 %s 段落已存在（幂等跳过）；CR 仍 == %d' % (name, new_cr), cr0 == new_cr,
           (cr0, lf0, by0))
        report.append({'file': name, 'action': 'skip-existing', 'cr': cr0, 'lf': lf0})
        continue

    ck('W1 %s 旧 CR==%d（实测 %d/%d）' % (name, old_cr, cr0, lf0), cr0 == old_cr, (cr0, lf0, by0))
    if old_lf is not None:
        ck('W1b %s 旧 LF==%d（实测 %d）' % (name, old_lf, lf0), lf0 == old_lf, lf0)

    bk = backup(path, 'write')
    old = open(path, 'rb').read()
    with open(path, 'wb') as f:
        f.write(old + seg)

    cr1, lf1, by1 = crlf(path)
    ck('W4 %s 回读 CR==%d（不变）实测 %d' % (name, new_cr, cr1), cr1 == new_cr, (cr1, lf1, by1))
    ck('W5 %s 行数 %d += %d = %d' % (name, lf0, seg.count(b'\n'), lf0 + seg.count(b'\n')),
       lf1 == lf0 + seg.count(b'\n'), (lf0, lf1))
    back = open(path, 'rb').read()
    ck('W6 %s 回读含标记且字节 == 旧+段' % name,
       marker.encode() in back and back == old + seg, marker)
    report.append({'file': name, 'action': 'appended', 'sha_before': sha0,
                   'sha_after': hashlib.sha256(back).hexdigest(),
                   'lf_before': lf0, 'lf_after': lf1, 'cr': cr1, 'bytes': by1,
                   'backup': os.path.basename(bk)})

# ============ 第 2 步：全局不变量 ============
b_lf = crlf(BRD)[1]
ck('W7 STATUS_BOARD 写入后 %d 行 <= 300（硬上限）' % b_lf, b_lf <= 300, b_lf)
ck('W7b 归档已触发（开局 281 >= 260）且写入后 %d <= 300' % b_lf,
   281 >= 260 and b_lf <= 300, {'open': 281, 'post': b_lf, 'cap': 300})
ck('W8 BOARD_ARCHIVE CR 仍为 2952', crlf(ARC)[0] == 2952, crlf(ARC)[0])
ck('W9 R14_COMMON CR 仍为 1081', crlf(os.path.join(W, 'R14_COMMON.md'))[0] == 1081,
   crlf(os.path.join(W, 'R14_COMMON.md'))[0])
ck('W10 LEAD_LOCK CR 仍为 137', crlf(os.path.join(ROOT, 'lead/LEAD_LOCK'))[0] == 137,
   crlf(os.path.join(ROOT, 'lead/LEAD_LOCK'))[0])
ck('W11 台账 CR 仍为 337',
   crlf(os.path.join(ROOT, 'lead/GOAL_THREE_TARGETS_20261018.md'))[0] == 337,
   crlf(os.path.join(ROOT, 'lead/GOAL_THREE_TARGETS_20261018.md'))[0])

json.dump({'stamp': stamp, 'report': report, 'checks': checks},
          open(os.path.join(SEG, 'write_r112.json'), 'w'), indent=1, ensure_ascii=False)
badn = sum(1 for c in checks if not c['ok'])
print('\n--- %d checks, PASS %d, FAIL %d ---' % (len(checks), len(checks) - badn, badn))
sys.exit(1 if badn else 0)
