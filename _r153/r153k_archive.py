#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R153 K：看板归档（第 150 / 151 轮两段搬入 BOARD_ARCHIVE，逐字不改）。

纪律：BOARD_ARCHIVE CR 必须保持 2952、STATUS_BOARD CR 必须保持 0；
      两段从看板删除后，看板行数必须回到 <= 260（新轮段仍在）。
反控：搬入前后的拼接触发的字节必须与「原文删除两段后」逐字节相同。
"""
import hashlib
import os
import sys
import time

ROOT = '/home/t628/projects/ra2-campaign-forge'
D = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
BRD = os.path.join(D, 'STATUS_BOARD.md')
ARC = os.path.join(D, 'BOARD_ARCHIVE.md')
BAKDIR = os.path.join(D, 'R17_LEAD_BASELINE')

fails = []


def ck(n, c, d=''):
    ok = bool(c)
    print(('  PASS ' if ok else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not ok:
        fails.append(n)
    return ok


raw_b = open(BRD, 'rb').read()
raw_a = open(ARC, 'rb').read()
ck('看板 CR = 0', raw_b.count(b'\r') == 0, raw_b.count(b'\r'))
ck('归档 CR = 2952', raw_a.count(b'\r') == 2952, raw_a.count(b'\r'))
blines = raw_b.decode('utf-8').split('\n')
n_b = len([l for l in blines if l]) - 1
print('看板逻辑行（去掉末尾空段）= %d' % n_b)

# 段边界
segs = [(i, l) for i, l in enumerate(blines) if l.startswith('## ') and '第 1' in l]
print('看板段标题：')
for i, l in segs:
    print('  L%-4d %s' % (i + 1, l[:56]))
ck('看板恰 4 段（150/151/152/153）', len(segs) == 4, len(segs))

i150 = segs[0][0]
i152 = [i for i, l in segs if '第 152 轮' in l][0]
move = '\n'.join(blines[i150:i152])
rest = '\n'.join(blines[:0]) + '\n'.join(blines[i152:])
print('\n待搬两段 %d 段 / %d B' % (i152 - i150, len(move.encode('utf-8'))))
ck('待搬段非空', len(move) > 1000, len(move))

# 反控：拼接可逆 —— move + rest 重新拼回原文
rebuild = move + '\n' + rest
ck('反控：move + 换行 + rest 逐字节复现看板原文',
   rebuild.encode('utf-8') == raw_b, (len(rebuild.encode('utf-8')), len(raw_b)))

# 归档追加：保持既有风格（原 CR 段落不动，新段用 LF，与归档尾部现有 LF 段一致）
arc_txt = raw_a.decode('utf-8')
marker = '## 📦 H44 归档（2026-11-27，R153 Lead 执行）：看板第 150–151 轮'
ck('归档幂等：marker 尚未存在', marker not in arc_txt)
tail = arc_txt if arc_txt.endswith('\n') else arc_txt + '\n'
block = ('\n' + marker + '\n\n'
         '> 来源：`STATUS_BOARD.md` 第 %d–%d 行（搬走前的位置）。以下**逐字搬入**，未改一字；'
         '归档 CR 保持 2952（本段全 LF）。\n\n' % (i150 + 1, i152)
         + move + '\n')
new_arc = tail + block
new_arc_raw = new_arc.encode('utf-8')
ck('新归档 CR 仍 = 2952', new_arc_raw.count(b'\r') == 2952, new_arc_raw.count(b'\r'))
ck('新归档含两段原文', move in new_arc)

new_brd = rest
new_brd_raw = new_brd.encode('utf-8')
ck('新看板 CR = 0', new_brd_raw.count(b'\r') == 0, new_brd_raw.count(b'\r'))
n_b2 = len([l for l in new_brd.split('\n') if l]) - 1
print('新看板行数 = %d' % n_b2)
ck('新看板 <= 260 行', n_b2 <= 260, n_b2)
ck('新看板仍含 152 / 153 两段',
   '第 152 轮' in new_brd and '第 153 轮' in new_brd)
ck('新看板不再含 150 / 151 两段',
   '第 150 轮' not in new_brd and '第 151 轮' not in new_brd)

# 备份 + 写入
for p, tag in ((ARC, 'archive'), (BRD, 'board')):
    bak = os.path.join(BAKDIR, os.path.basename(p) + '.before_r153_%s_%s.bak'
                       % (tag, time.strftime('%Y%m%d_%H%M%S')))
    fd = os.open(bak, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, 'wb') as f:
        f.write(open(p, 'rb').read())
    ck('备份 wx %s' % os.path.basename(bak), os.path.exists(bak))

open(ARC, 'wb').write(new_arc_raw)
ck('归档回读一致', open(ARC, 'rb').read() == new_arc_raw)
open(BRD, 'wb').write(new_brd_raw)
ck('看板回读一致', open(BRD, 'rb').read() == new_brd_raw)

raw_a2 = open(ARC, 'rb').read()
raw_b2 = open(BRD, 'rb').read()
ck('终态 归档 CR = 2952', raw_a2.count(b'\r') == 2952, raw_a2.count(b'\r'))
ck('终态 看板 CR = 0', raw_b2.count(b'\r') == 0, raw_b2.count(b'\r'))
print('\n终态：归档 %d B / 看板 %d B' % (len(raw_a2), len(raw_b2)))
print('归档 sha %s' % hashlib.sha256(raw_a2).hexdigest()[:16])
print('看板 sha %s' % hashlib.sha256(raw_b2).hexdigest()[:16])

print('\nFAIL %d：%s' % (len(fails), fails))
sys.exit(1 if fails else 0)
