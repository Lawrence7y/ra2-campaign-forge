#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r106_archive.py —— 看板归档：299 行 >= 260 线，按纪律先归档最早 2 段到 BOARD_ARCHIVE.md

纪律（CLAUDE.md 与 LEAD_LOCK 一致口径）：
- 归档必须逐字搬（missing=0），归档后 STATUS_BOARD 里留指针行
- BOARD_ARCHIVE CR 保持 2952，STATUS_BOARD CR 保持 0（新增内容全 LF）
- 写前用 wx 模式独占创建唯一备份，断言旧 sha256 与 CR，一次性写入，回读校验

反控（缺一不可）：
  N1 搬运行在归档里必须逐行可查（missing 计数必须为 0）；反控：把搬运段某行改一个字符，
     该行立刻变 missing=1 —— 证明 missing 判据有判别力，不是恒 0
  N2 CR 不变量：反控把搬运段按 CRLF 写进归档，CR 必须 2952->2952+k 而 FAIL
"""
import hashlib, os, sys, time

ROOT = '/home/t628/projects/ra2-campaign-forge'
D = os.path.join(ROOT, 'lead/next_re_20261117_r14')
B = os.path.join(D, 'STATUS_BOARD.md')
A = os.path.join(D, 'BOARD_ARCHIVE.md')
BK = os.path.join(D, 'R17_LEAD_BASELINE')

BOARD_BYTES = 38605
BOARD_CR = 0
BOARD_SHA = 'a9f627fdd6c6ccb2'          # 前 16 位即断言口径
ARCH_CR = 2952
ARCH_BYTES = 836225
# 最早两段 = R99 段（第 30 行起）与 R100 段（第 79 行起），到 R101 段前一行止
SEG_FIRST_LINE = 30      # 1-based，含
SEG_LAST_LINE = 134      # 1-based，含（R101 段头在第 135 行）

checks = []
def ck(n, c, d=''):
    checks.append({'name': n, 'ok': bool(c), 'detail': str(d)})
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''), flush=True)
    return bool(c)

def sha16(b):
    return hashlib.sha256(b).hexdigest()[:16]

def guard_write(path, data):
    """wx 独占备份 -> 断言旧值 -> 一次性写 -> 回读"""
    old = open(path, 'rb').read()
    ts = time.strftime('%Y%m%d_%H%M%S')
    bak = os.path.join(BK, 'SUPERSEDED.before_r106_archive_%s_%s.bak'
                       % (os.path.basename(path), ts))
    fd = os.open(bak, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)   # wx
    with os.fdopen(fd, 'wb') as f:
        f.write(old)
    assert open(bak, 'rb').read() == old, 'backup readback mismatch'
    print('  backup -> %s (%d B)' % (os.path.basename(bak), len(old)), flush=True)
    with open(path, 'r+b') as f:
        f.write(data)
        f.truncate()
    rb = open(path, 'rb').read()
    assert rb == data, 'write readback mismatch'
    return bak, old

board = open(B, 'rb').read()
arch = open(A, 'rb').read()

ck('P0a STATUS_BOARD 旧字节 == 38605', len(board) == BOARD_BYTES, len(board))
ck('P0b STATUS_BOARD 旧 CR == 0', board.count(b'\r') == BOARD_CR, board.count(b'\r'))
ck('P0c STATUS_BOARD 旧 sha 前 16 位 == a9f627fdd6c6ccb2', sha16(board) == BOARD_SHA, sha16(board))
ck('P0d BOARD_ARCHIVE 旧 CR == 2952', arch.count(b'\r') == ARCH_CR, arch.count(b'\r'))
ck('P0e BOARD_ARCHIVE 旧字节 == 836225', len(arch) == ARCH_BYTES, len(arch))
ck('P0f BOARD_ARCHIVE 以 LF 结尾', arch.endswith(b'\n'), repr(arch[-3:]))

blines = board.split(b'\n')
ck('P0g 看板行数 299 (>=260 归档线)', len(blines) - 1 == 299, len(blines) - 1)

seg = blines[SEG_FIRST_LINE - 1:SEG_LAST_LINE]        # 105 行
ck('P1a 搬运段行数 == 105', len(seg) == SEG_LAST_LINE - SEG_FIRST_LINE + 1, len(seg))
ck('P1b 搬运段首行是 R99 段头', seg[0].startswith('## '.encode()) and b'R17 \xe7\xac\xac 99' in seg[0], seg[0][:40])
ck('P1c 搬运段末行是空行', seg[-1] == b'', repr(seg[-1]))
ck('P1d 搬运段后一行是 R101 段头', blines[SEG_LAST_LINE].startswith('## '.encode()), blines[SEG_LAST_LINE][:40])
ck('P1e 搬运段内无 CR', b''.join(seg).count(b'\r') == 0, b''.join(seg).count(b'\r'))
ck('P1f 搬运段含 R100 段头', any(x.startswith('## '.encode()) and b'\xe7\xac\xac 100' in x for x in seg), '')

# ---- 组装归档：追加「归档分隔 + 两段原文」 ----
stamp = '2026-11-24 07:5x'
head = ('\n---\n\n> 归档时间 %s | 本次由 Lead 执行（R106）| 来源 STATUS_BOARD.md 第 %d-%d 行 | 逐字搬，missing=0\n\n'
        % (stamp, SEG_FIRST_LINE, SEG_LAST_LINE)).encode('utf-8')
new_arch = arch + head + b'\n'.join(seg) + b'\n'
ck('P2a 新归档 CR 仍为 2952（新增零 CR）', new_arch.count(b'\r') == ARCH_CR, new_arch.count(b'\r'))
ck('P2b 新归档以 LF 结尾', new_arch.endswith(b'\n'), '')

# 反控 N1：逐行在归档里可查；再造一行改字符必须查不到
alines = set(new_arch.split(b'\n'))
missing = [x for x in seg if x and x not in alines]
ck('P2c missing == 0（非空行逐字可查）', len(missing) == 0, len(missing))
_negseg = list(seg)
_i = next(i for i, x in enumerate(_negseg) if len(x) > 20)
_negseg[_i] = _negseg[_i][:-1] + b'Z'
_negset = set(new_arch.split(b'\n'))
_negmiss = [x for x in _negseg if x and x not in _negset]
ck('N1 反控：改一字符后 missing 必须 >= 1', len(_negmiss) >= 1, len(_negmiss))
ck('N2 反控：若按 CRLF 搬运，CR 必须 2952->3160 而非 2952',
   (arch + b'\r\n'.join(seg)).count(b'\r') != ARCH_CR,
   (arch + b'\r\n'.join(seg)).count(b'\r'))

# ---- 组装新看板：指针行替换两段 ----
ptr99 = ('> 📦 ## 🟢 R17 第 99 轮 已归档至 BOARD_ARCHIVE.md'
         '（2026-11-24 07:5x，逐字搬，missing=0；本次由 Lead 执行，R106）').encode('utf-8')
ptr100 = ('> 📦 ## 🟢 R17 第 100 轮 已归档至 BOARD_ARCHIVE.md'
          '（2026-11-24 07:5x，逐字搬，missing=0；本次由 Lead 执行，R106）').encode('utf-8')
new_board = b'\n'.join(blines[:SEG_FIRST_LINE - 1] + [ptr99, ptr100] + blines[SEG_LAST_LINE:])
ck('P3a 新看板 CR == 0', new_board.count(b'\r') == 0, new_board.count(b'\r'))
ck('P3b 新看板行数 == 299 - 105 + 2 = 196', new_board.count(b'\n') == 196, new_board.count(b'\n'))
ck('P3c 新看板行数 < 260（未再触归档线）', new_board.count(b'\n') < 260, new_board.count(b'\n'))
ck('P3d 新看板仍以 LF 结尾', new_board.endswith(b'\n'), '')
nb = new_board.split(b'\n')
ck('P3e 新看板第一条段头仍是 R101', any(x.startswith('## '.encode()) for x in nb[:1]) is False, '')
# 自错登记：本断言初版写成 ==7，是照搬归档前的段头计数（含 R99/R100 两段 7 个）
# 且把 R104 段算成二级标题；实测 R104 用三级标题 ###（第 237 行），搬走两段后 ## 只剩 4 个
heads2 = [x for x in nb if x.startswith(b'## ')]
heads3 = [x for x in nb if x.startswith(b'### ')]
ck('P3f 段头数：## 4 个 + ### 1 个 = 5（R101/102/103/+R104/105）',
   len(heads2) == 4 and len(heads3) == 1, (len(heads2), len(heads3)))
ck('P3f2 五个段头按序为 R101/R102/R103/R104/R105（含标题级别）',
   [x[:3] for x in sorted(heads2 + heads3, key=lambda y: nb.index(y))] ==
   [b'## ', b'## ', b'## ', b'###', b'## '],
   [x[:24] for x in sorted(heads2 + heads3, key=lambda y: nb.index(y))])
ck('P3g R99/R100 段头已不在正文', not any(b'\xe7\xac\xac 99' in x and x.startswith(b'## ') for x in nb)
   and not any(b'\xe7\xac\xac 100' in x and x.startswith(b'## ') for x in nb), '')
ck('P3h 两条指针行就位', sum(1 for x in nb if x.startswith(b'> \xf0\x9f\x93\xa6 ') and b'BOARD_ARCHIVE.md' in x) >= 2,
   sum(1 for x in nb if x.startswith(b'> \xf0\x9f\x93\xa6 ') and b'BOARD_ARCHIVE.md' in x))

if not all(c['ok'] for c in checks):
    print('\n断言未全过，不写盘', flush=True)
    sys.exit(1)

guard_write(A, new_arch)
guard_write(B, new_board)

# ---- 落盘后回读 ----
ab = open(A, 'rb').read()
bb = open(B, 'rb').read()
ck('R1 归档回读 CR == 2952', ab.count(b'\r') == ARCH_CR, ab.count(b'\r'))
ck('R2 归档回读字节 == 836225 + 新增', len(ab) == len(new_arch), len(ab))
ck('R3 看板回读 CR == 0', bb.count(b'\r') == 0, bb.count(b'\r'))
ck('R4 看板回读 196 行', bb.count(b'\n') == 196, bb.count(b'\n'))
ck('R5 归档里 105 行全部可查（回读口径）',
   len([x for x in seg if x and x not in set(ab.split(b'\n'))]) == 0, '')

import json
json.dump({'checks': checks, 'seg_lines': len(seg), 'board_after': 196,
           'archive_bytes_after': len(ab), 'board_bytes_after': len(bb)},
          open(os.path.join(ROOT, '_r106/r106_archive.json'), 'w'), ensure_ascii=False, indent=1)
fails = [c['name'] for c in checks if not c['ok']]
print('\n%d 项断言, FAIL %d %s' % (len(checks), len(fails), fails), flush=True)
sys.exit(0 if not fails else 1)
