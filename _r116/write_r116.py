#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""write_r116.py —— R116 四件套落盘（写入纪律 + 看板归档）。

写入纪律（与 R108–R115 同一套）：
  1. R17_LEAD_BASELINE/ 用 os.O_EXCL 独占创建唯一备份；2. 断言旧 sha256 与 CR；
  3. 一次性写入 old+seg；4. 回读校验（CR/行数/标记/字节 == old+seg）。

看板：开局 254 行；本轮段落约 100 行 ⇒ 254+100=354 > 300 硬上限
      ⇒ **必须先归档**。可归档的实体段：R114 段（## 起、### 前，103 行）。
      归档后 254-103=151 行，再追加 ⇒ <= 300。
      归档逐字搬、missing=0，BOARD_ARCHIVE CR 必须保持 2952。
"""
import hashlib, json, os, sys, time

ROOT = '/home/t628/projects/ra2-campaign-forge'
W = os.path.join(ROOT, 'lead/next_re_20261117_r14')
BASE = os.path.join(W, 'R17_LEAD_BASELINE')
SEG = os.path.join(ROOT, '_r116')
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
report, job = [], [0]


def backup(path, tag):
    job[0] += 1
    bak = os.path.join(BASE, '%s.before_R116_%s_j%d_%s.bak'
                       % (os.path.basename(path), tag, job[0], stamp))
    fd = os.open(bak, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    with os.fdopen(fd, 'wb') as f:
        f.write(open(path, 'rb').read())
    ck('W2 %s 备份独占创建且字节一致（j%d）' % (os.path.basename(path), job[0]),
       sha(bak) == sha(path), os.path.basename(bak))
    return bak


BRD = os.path.join(W, 'STATUS_BOARD.md')
ARC = os.path.join(W, 'BOARD_ARCHIVE.md')
segp_b = os.path.join(SEG, 'seg_board_116.md')

# ============ 第 0 步：看板归档（R114 段）============
cr0, lf0, by0 = crlf(BRD)
seg_lines = open(segp_b, 'rb').read().count(b'\n')
ck('A0 看板开局 %d 行；本轮段落 %d 行 ⇒ 预计 %d 行 > 300 硬上限'
   % (lf0, seg_lines, lf0 + seg_lines), lf0 == 254 and lf0 + seg_lines > 300,
   {'lines': lf0, 'seg': seg_lines, 'projected': lf0 + seg_lines})
ck('A0b BOARD_ARCHIVE 开局 CR==2952', crlf(ARC)[0] == 2952, crlf(ARC)[0])

brd = open(BRD, 'rb').read()
lines = brd.split(b'\n')
starts = [i for i, l in enumerate(lines) if l.startswith(b'## ')]
ck('A1 看板 ## 实体段起点 %d 个' % len(starts), len(starts) == 1, starts)
starts2 = [i for i, l in enumerate(lines) if l.startswith(b'### ')]
ck('A1b 看板 ### 段（R115 段）起点 %d 个，首行 %d'
   % (len(starts2), starts2[0] if starts2 else -1), len(starts2) == 1, starts2)

cut = starts2[0]
archive_part = lines[starts[0]:cut]
keep_part = lines[cut:]
ck('A2 待归档 = R114 段（## 起、### 前），%d 行；保留 %d 行'
   % (len(archive_part), len(keep_part)),
   90 <= len(archive_part) <= 115, {'arch': len(archive_part), 'keep': len(keep_part)})

arc_old = open(ARC, 'rb').read()
arc_add = b'\n'.join(archive_part).rstrip(b'\n') + b'\n'
missing = [l for l in archive_part if l and l not in brd]
ck('A3 归档逐字搬：待归档 %d 行中在原文找不到的 = %d（missing 必须 0）'
   % (len(archive_part), len(missing)), not missing, {'missing': len(missing)})

brd_new = b'\n'.join(lines[:starts[0]] + keep_part)
ck('A4 新看板行数 %d - %d = %d' % (lf0, len(archive_part), brd_new.count(b'\n')),
   brd_new.count(b'\n') == lf0 - len(archive_part), brd_new.count(b'\n'))

backup(ARC, 'archive')
open(ARC, 'wb').write(arc_old + arc_add)
arc_new = open(ARC, 'rb').read()
ck('A5 BOARD_ARCHIVE 回读 == 旧 + 段（逐字节）', arc_new == arc_old + arc_add,
   {'old': len(arc_old), 'add': len(arc_add), 'new': len(arc_new)})
ck('A6 BOARD_ARCHIVE CR 仍为 2952', arc_new.count(b'\r') == 2952, arc_new.count(b'\r'))
ck('A6b BOARD_ARCHIVE LF 增量正确',
   arc_new.count(b'\n') == arc_old.count(b'\n') + arc_add.count(b'\n'), 'ok')

backup(BRD, 'archive')
open(BRD, 'wb').write(brd_new)
brd_back = open(BRD, 'rb').read()
ck('A7 STATUS_BOARD 回读 == 头 + 保留段（逐字节）', brd_back == brd_new,
   {'bytes': len(brd_back)})
ck('A7b STATUS_BOARD 归档后 %d 行' % brd_back.count(b'\n'), brd_back.count(b'\n') <= 300,
   brd_back.count(b'\n'))
ck('A7c STATUS_BOARD CR 仍为 0', brd_back.count(b'\r') == 0, brd_back.count(b'\r'))

# ============ 第 1 步：逐文件追加 ============
JOBS = [
    ('R14_COMMON.md', os.path.join(W, 'R14_COMMON.md'), os.path.join(SEG, 'seg_rc_2120.md'),
     b'## 2.120', 1081),
    ('GOAL_THREE_TARGETS_20261018.md', os.path.join(ROOT, 'lead/GOAL_THREE_TARGETS_20261018.md'),
     os.path.join(SEG, 'seg_ledger_1170.md'), b'## \xc2\xa71170 R116', 337),
    ('LEAD_LOCK', os.path.join(ROOT, 'lead/LEAD_LOCK'), os.path.join(SEG, 'seg_lock_ER.md'),
     b'ER. R116', 137),
    ('STATUS_BOARD.md', BRD, segp_b, '第 116 轮'.encode('utf-8'), 0),
]

for name, path, segp, marker, want_cr in JOBS:
    seg = open(segp, 'rb').read()
    ck('W0 %s 段落全 LF（CR==0）' % os.path.basename(segp), seg.count(b'\r') == 0,
       seg.count(b'\r'))
    ck('W0b %s 段落以 LF 开头、以 LF 结尾' % os.path.basename(segp),
       seg.startswith(b'\n') and seg.endswith(b'\n'), (seg[:2], seg[-2:]))
    cr_b, lf_b, by_b = crlf(path)
    s_b = sha(path)
    ck('W1 %s 旧 CR==%d（实测 %d / LF %d / %d B）' % (name, want_cr, cr_b, lf_b, by_b),
       cr_b == want_cr, (cr_b, lf_b, by_b))
    bak = backup(path, 'write')
    old = open(path, 'rb').read()
    open(path, 'wb').write(old + seg)
    back = open(path, 'rb').read()
    cr_a, lf_a, by_a = crlf(path)
    ck('W4 %s 回读 CR==%d（不变）实测 %d' % (name, want_cr, cr_a), cr_a == want_cr,
       (cr_a, lf_a, by_a))
    ck('W5 %s 行数 %d += %d = %d' % (name, lf_b, seg.count(b'\n'), lf_b + seg.count(b'\n')),
       lf_a == lf_b + seg.count(b'\n'), (lf_b, lf_a))
    ck('W6 %s 回读字节 == 旧 + 段（逐字节）且含标记 %s' % (name, marker.decode('utf-8')),
       back == old + seg and marker in back, 'ok')
    report.append({'file': name, 'sha_before': s_b, 'sha_after': hashlib.sha256(back).hexdigest(),
                   'lf_before': lf_b, 'lf_after': lf_a, 'cr': cr_a, 'bytes': by_a,
                   'backup': os.path.basename(bak)})

# ============ 第 2 步：全局不变量 ============
b_lf = crlf(BRD)[1]
ck('W7 STATUS_BOARD 写入后 %d 行 <= 300（硬上限）' % b_lf, b_lf <= 300, b_lf)
ck('W8 BOARD_ARCHIVE CR 仍为 2952', crlf(ARC)[0] == 2952, crlf(ARC)[0])
ck('W9 R14_COMMON CR 仍为 1081', crlf(os.path.join(W, 'R14_COMMON.md'))[0] == 1081,
   crlf(os.path.join(W, 'R14_COMMON.md'))[0])
ck('W10 LEAD_LOCK CR 仍为 137', crlf(os.path.join(ROOT, 'lead/LEAD_LOCK'))[0] == 137,
   crlf(os.path.join(ROOT, 'lead/LEAD_LOCK'))[0])
ck('W11 台账 CR 仍为 337',
   crlf(os.path.join(ROOT, 'lead/GOAL_THREE_TARGETS_20261018.md'))[0] == 337,
   crlf(os.path.join(ROOT, 'lead/GOAL_THREE_TARGETS_20261018.md'))[0])

# ============ 第 3 步：内容自检 ============
rc = open(os.path.join(W, 'R14_COMMON.md'), 'rb').read().decode('utf-8')
led = open(os.path.join(ROOT, 'lead/GOAL_THREE_TARGETS_20261018.md'), 'rb').read().decode('utf-8')
lk = open(os.path.join(ROOT, 'lead/LEAD_LOCK'), 'rb').read().decode('utf-8')
brd = open(BRD, 'rb').read().decode('utf-8')

ck('C1 四件套都含本轮核心事实（0x7f7c80 / OleSaveToStream）',
   all(('0x7f7c80' in t and 'OleSaveToStream' in t) for t in (rc, led, lk, brd)), 'ok')
ck('C2 四件套都写明 0x7f7c70 的语义**未定名**（L4 未证）',
   all(('L4' in t or '未证' in t) for t in (rc, led, lk, brd)), 'ok')
ck('C3 四件套都写明「R112 的不可区分结论在其域内仍成立」（范畴不越界）',
   all('不可区分' in t for t in (rc, led, lk, brd)), 'ok')
ck('C4 四件套都记了跨家族审计的实质意见并复算（hy4 判 C6 越界，主会话接受）',
   all(('hy4' in t and '越界' in t) for t in (rc, led, lk, brd)), 'ok')
ck('C5 四件套都登记自错 S-23..S-29（不粉饰）',
   all(('S-23' in t and 'S-24' in t) for t in (rc, led, lk, brd)), 'ok')
ck('C6 四件套都写明代码形状去重后独立证据只有 2 类',
   all(('2 类' in t or '2 种' in t) for t in (rc, led, lk, brd)), 'ok')
ck('C7 四件套都登记 exec(deepseek) [OVERTIME] 如实记录',
   all('[OVERTIME]' in t for t in (rc, led, lk, brd)), 'ok')
ck('C8 四件套都登记审计员次要数字不符（4.7e-07 vs 1.62e-08）并复算',
   all('4.7e-07' in t for t in (rc, led, lk, brd)), 'ok')

json.dump({'stamp': stamp, 'report': report, 'checks': checks,
           'archive': {'took_lines': len(archive_part),
                       'board_after_archive': lf0 - len(archive_part),
                       'board_final': b_lf}},
          open(os.path.join(SEG, 'write_r116.json'), 'w'), indent=1, ensure_ascii=False)
bad = sum(1 for c in checks if not c['ok'])
print('\n--- write_r116: %d checks, PASS %d, FAIL %d ---'
      % (len(checks), len(checks) - bad, bad))
sys.exit(1 if bad else 0)
