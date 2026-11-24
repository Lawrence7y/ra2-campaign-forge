#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""write_r108.py —— R108 四件套写入（含看板归档）

纪律（按 t628 CLAUDE.md）：每次修改前在 R17_LEAD_BASELINE/ 用 wx 独占创建唯一备份
-> 断言旧 sha256 与 CR -> 一次性写入 -> 回读校验。

看板开局已 300 行（= 上限），故先归档最早 3 段（第 101 / 102 / 103 轮）到 BOARD_ARCHIVE.md，
原位换成 3 行指针（任务卡要求「最早 2 段」；实测归档 2 段后仍会因本轮 63 行超到 311，
如实记「实归档 3 段」，不粉饰）。归档 CR 保持 2952。
"""
import hashlib, io, os, sys, time

ROOT = '/home/t628/projects/ra2-campaign-forge'
R14REL = os.path.join('lead', 'next_re_20261117_r14')
BASE = os.path.join(ROOT, R14REL, 'R17_LEAD_BASELINE')
TS = time.strftime('%Y%m%d_%H%M%S')

def sha16(p):
    return hashlib.sha256(io.open(p, 'rb').read()).hexdigest()[:16]

def crcount(p):
    return io.open(p, encoding='utf-8', newline='').read().count('\r\n')

R14 = os.path.join(ROOT, R14REL, 'R14_COMMON.md')
LED = os.path.join(ROOT, 'lead', 'GOAL_THREE_TARGETS_20261018.md')
LOCK = os.path.join(ROOT, 'lead', 'LEAD_LOCK')
BRD = os.path.join(ROOT, R14REL, 'STATUS_BOARD.md')
ARC = os.path.join(ROOT, R14REL, 'BOARD_ARCHIVE.md')

TARGETS = {
    'R14_COMMON': (R14, '5e87550115d103f2', 1081),
    'LEDGER': (LED, 'ebbb66e9a056946d', 337),
    'LEAD_LOCK': (LOCK, '1f5763ca173922c3', 137),
    'STATUS_BOARD': (BRD, '94c777ec3ec6b415', 0),
    'BOARD_ARCHIVE': (ARC, '3c12191fe2016670', 2952),
}
fails = []
def ck(n, c, d=''):
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''))
    if not c:
        fails.append(n)
    return bool(c)

for k, (p, sha, cr) in TARGETS.items():
    ck('pre %s sha256 %s' % (k, sha), sha16(p) == sha, sha16(p))
    ck('pre %s CR %d' % (k, cr), crcount(p) == cr, crcount(p))

def backup(path, tag):
    os.makedirs(BASE, exist_ok=True)
    bl = os.path.join(BASE, '%s.before_R108_%s_%s.bak'
                      % (os.path.basename(path), tag, TS))
    data = io.open(path, 'rb').read()
    fd = os.open(bl, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    try:
        os.write(fd, data)
    finally:
        os.close(fd)
    ck('backup exclusive %s' % tag,
       os.path.getsize(bl) == len(data)
       and hashlib.sha256(io.open(bl, 'rb').read()).digest()
       == hashlib.sha256(data).digest(), os.path.basename(bl))
    return data

ORIG = {k: backup(p, k) for k, (p, _, _) in TARGETS.items()}

def write_checked(path, new, expect_cr, label):
    with io.open(path, 'wb') as f:
        f.write(new)
    back = io.open(path, 'rb').read()
    ck('post %s 回读逐字节一致' % label, back == new, len(back))
    ck('post %s CR 保持 %d' % (label, expect_cr), back.count(b'\r\n') == expect_cr,
       back.count(b'\r\n'))
    return back

# ---------------- 0 归档 ----------------
brd_txt = io.open(BRD, encoding='utf-8', newline='').read()
arc_txt = io.open(ARC, encoding='utf-8', newline='').read()
ck('ARC 本轮尚未归档过（防重复追加）', 'R108 归档' not in arc_txt)
ck('BRD 前置 300 行（= 上限，触发归档）', brd_txt.count('\n') == 300, brd_txt.count('\n'))
L = brd_txt.split('\n')
heads = [i for i, l in enumerate(L) if l.startswith('## ')]
ck('BRD 段标题数 5（101/102/103/105/106）', len(heads) == 5, [L[i][:12] for i in heads])
ck('第 1 个段标题是第 101 轮', L[heads[0]].startswith('## 第 101 轮'), L[heads[0]][:20])
ck('第 2 个段标题是第 102 轮', L[heads[1]].startswith('## 第 102 轮'), L[heads[1]][:20])
ck('第 3 个段标题是第 103 轮', L[heads[2]].startswith('## 第 103 轮'), L[heads[2]][:20])

seg1 = '\n'.join(L[heads[0]:heads[1]])   # 已含末尾空行
seg2 = '\n'.join(L[heads[1]:heads[2]])
seg3 = '\n'.join(L[heads[2]:heads[3]])
ck('归档段非空且逐字取到',
   all(len(s) > 500 for s in (seg1, seg2, seg3)),
   (len(seg1), len(seg2), len(seg3)))
# 指纹锚：归档前先记下 3 段的 sha256，归档后要在归档文件里逐字找到
import re
fp = {k: hashlib.sha256(v.encode('utf-8')).hexdigest()[:16]
      for k, v in (('101', seg1), ('102', seg2), ('103', seg3))}

arc_add = ('\n\n> 📦 R108 归档（看板开局 300 行 = 上限，触及归档线）逐字搬入：'
           '第 101 轮段、第 102 轮段、第 103 轮段\n\n'
           + seg1 + '\n' + seg2 + '\n' + seg3 + '\n')
new_arc = (arc_txt + arc_add).encode('utf-8')
write_checked(ARC, new_arc, 2952, 'BOARD_ARCHIVE')

PTRS = [
    '> 📦 ## 第 101 轮（R101） 已归档至 BOARD_ARCHIVE.md（2026-11-24 10:5x，逐字搬，sha %s；'
    '本次由 Lead 执行，R108）' % fp['101'],
    '> 📦 ## 第 102 轮（R102） 已归档至 BOARD_ARCHIVE.md（2026-11-24 10:5x，逐字搬，sha %s；'
    '本次由 Lead 执行，R108）' % fp['102'],
    '> 📦 ## 第 103 轮（R103） 已归档至 BOARD_ARCHIVE.md（2026-11-24 10:5x，逐字搬，sha %s；'
    '本次由 Lead 执行，R108）' % fp['103'],
]
newL = L[:heads[0]] + PTRS + L[heads[3]:]
new_brd = '\n'.join(newL)
ck('归档后看板行数 <= 300 - 本轮段 63 行（留足余量）',
   new_brd.count('\n') + 63 <= 300, new_brd.count('\n'))
write_checked(BRD, new_brd.encode('utf-8'), 0, 'STATUS_BOARD(归档后)')
arc_now = io.open(ARC, encoding='utf-8', newline='').read()
for k, v in (('101', seg1), ('102', seg2), ('103', seg3)):
    ck('归档逐字可检出 %s 段（missing=0）' % k, v in arc_now,
       hashlib.sha256(v.encode('utf-8')).hexdigest()[:16])

# ---------------- 1..3 追加三段 ----------------
def append(path, segfile, expect_cr, label):
    seg = io.open(segfile, encoding='utf-8', newline='').read()
    ck('seg %s 全 LF' % os.path.basename(segfile), '\r' not in seg, seg.count('\n'))
    cur = io.open(path, encoding='utf-8', newline='').read()
    if not cur.endswith('\n'):
        seg = '\n' + seg
    new = cur + seg
    chk = write_checked(path, new.encode('utf-8'), expect_cr, label)
    return len(chk)

if __name__ == '__main__':
    print('--- R108 write, ts=%s ---' % TS)
    print('  R14_COMMON bytes ->', append(R14, os.path.join(ROOT, '_r108', 'seg_rc_2112.md'),
                                         1081, 'R14_COMMON'))
    print('  LEDGER bytes ->', append(LED, os.path.join(ROOT, '_r108', 'seg_ledger_1162.md'),
                                      337, 'LEDGER'))
    print('  LEAD_LOCK bytes ->', append(LOCK, os.path.join(ROOT, '_r108', 'seg_lock_EJ.md'),
                                         137, 'LEAD_LOCK'))
    # 先归档再写板：归档已在上面完成，这里只追加本轮段
    b = append(BRD, os.path.join(ROOT, '_r108', 'seg_board_108.md'), 0, 'STATUS_BOARD(R108)')
    n = io.open(BRD, encoding='utf-8', newline='').read().count('\n')
    ck('board 最终行数 <= 300', n <= 300, n)
    print('  STATUS_BOARD bytes ->', b, 'lines', n)
    ck('post ARC CR 仍 2952', crcount(ARC) == 2952, crcount(ARC))
    print('FAILS:', len(fails), fails)
    sys.exit(1 if fails else 0)
