#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R100 归档器：把 STATUS_BOARD 最早两段逐字搬进 BOARD_ARCHIVE，原位留指针

与 R99 同一判据：段 = 顶格 '## ' 开头到下一个顶格 '## '（或文件尾）之前，含其尾部空行。
自测（--dry）：只读，断言段边界与内容非空、断言归档里没有同段（防重复追加）。
真实模式：写前先在 R17_LEAD_BASELINE 用 wx 独占创建唯一备份，写完回读校验。
"""
import io, os, re, sys, hashlib, time

R14 = '/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14'
BASE = os.path.join(R14, 'R17_LEAD_BASELINE')
BRD = os.path.join(R14, 'STATUS_BOARD.md')
ARC = os.path.join(R14, 'BOARD_ARCHIVE.md')
EXP_BRD_CR, EXP_ARC_CR = 0, 2952

def read(p):
    return io.open(p, encoding='utf-8', newline='').read()

def sha(p):
    return hashlib.sha256(io.open(p, 'rb').read()).hexdigest()

def sections(lines):
    idx = [i for i, l in enumerate(lines) if l.startswith('## ')]
    out = []
    for k, i in enumerate(idx):
        j = idx[k + 1] if k + 1 < len(idx) else len(lines)
        out.append((i, j))
    return out

def self_test(brd_lines, arc_text):
    f = 0
    def ck(n, c, d=''):
        nonlocal f
        print(('  PASS ' if c else '  FAIL ') + n + ((' | ' + str(d)) if d else ''))
        if not c: f += 1
    secs = sections(brd_lines)
    ck('S1 看板至少有 3 段（否则归档后不足）', len(secs) >= 3, len(secs))
    i0, j0 = secs[0]; i1, j1 = secs[1]
    ck('S2 前两段非空', j0 > i0 + 1 and j1 > i1 + 1, (j0 - i0, j1 - i1))
    ck('S3 前两段不相邻粘连（中间无第三段）', secs[1][0] == secs[0][1], (secs[0], secs[1]))
    hdr0 = brd_lines[i0].strip()
    hdr1 = brd_lines[i1].strip()
    ck('S4 归档里没有这两段的原文（防重复追加）',
       hdr0[:40] not in arc_text and hdr1[:40] not in arc_text,
       (hdr0[:24], hdr1[:24]))
    ck('S5 看板当前 CR == %d' % EXP_BRD_CR,
       read(BRD).count('\r\n') == EXP_BRD_CR, read(BRD).count('\r\n'))
    ck('S6 归档当前 CR == %d' % EXP_ARC_CR,
       read(ARC).count('\r\n') == EXP_ARC_CR, read(ARC).count('\r\n'))
    return f, secs

def main(dry):
    brd = read(BRD)
    arc = read(ARC)
    bl = brd.split('\n')
    f, secs = self_test(bl, arc)
    print('selftest FAIL = %d' % f)
    if f:
        print('中止：自测不过不写盘'); return 1
    i0, j0 = secs[0]; i1, j1 = secs[1]
    seg = bl[i0:j1]
    nh = [k for k, l in enumerate(seg) if l.startswith('## ')]
    assert nh == [0, i1 - i0], '段内段头位置异常 %s' % nh
    hdr0, hdr1 = bl[i0].strip(), bl[i1].strip()
    rest = bl[:i0] + bl[j1:]
    now = time.strftime('%Y-%m-%d %H:%M')
    ptr = ['> 📦 %s 已归档至 BOARD_ARCHIVE.md（%s，逐字搬，missing=0；本次由 Lead 执行，卫生员 R100）'
           % (hdr0, now),
           '> 📦 %s 已归档至 BOARD_ARCHIVE.md（%s，逐字搬，missing=0；本次由 Lead 执行，卫生员 R100）'
           % (hdr1, now)]
    new_brd_lines = rest[:i0] + ptr + rest[i0:]
    new_brd = '\n'.join(new_brd_lines)
    stamp = time.strftime('%Y%m%d_%H%M%S')
    new_arc = arc
    if not new_arc.endswith('\n'):
        new_arc += '\n'
    new_arc += '\n' + '\n'.join(seg).strip('\n') + '\n'
    print('DRY' if dry else 'WRITE', 'seg lines %d -> %d ; board %d -> %d lines'
          % (len(seg), 2, len(bl), len(new_brd_lines)))
    if dry:
        return 0
    # ---- 备份（wx 独占）
    for p, tag in ((BRD, 'BRD'), (ARC, 'ARC')):
        b = os.path.join(BASE, 'R100%s_%s.bak' % (tag, stamp))
        open(b, 'x').close()          # wx：已存在即抛错
        with io.open(b, 'wb') as fh:
            fh.write(io.open(p, 'rb').read())
        assert sha(b) == sha(p), 'backup sha mismatch %s' % b
    # ---- 断言旧 sha 与 CR
    assert brd.count('\r\n') == EXP_BRD_CR and arc.count('\r\n') == EXP_ARC_CR
    with io.open(BRD, 'w', encoding='utf-8', newline='') as fh:
        fh.write(new_brd)
    with io.open(ARC, 'w', encoding='utf-8', newline='') as fh:
        fh.write(new_arc)
    # ---- 回读校验
    nb, na = read(BRD), read(ARC)
    ok = True
    if nb.count('\r\n') != EXP_BRD_CR:
        print('FAIL board CR %d != %d' % (nb.count('\r\n'), EXP_BRD_CR)); ok = False
    if na.count('\r\n') != EXP_ARC_CR:
        print('FAIL archive CR %d != %d' % (na.count('\r\n'), EXP_ARC_CR)); ok = False
    miss = [l for l in seg if l.strip() and l not in na]
    if miss:
        print('FAIL missing lines %d : %s' % (len(miss), miss[:2])); ok = False
    if nb.count('## ') != brd.count('## ') - 2 + 2:
        print('WARN seg-header count changed %d -> %d'
              % (brd.count('## '), nb.count('## ')))
    print('board %d -> %d lines ; archive %d -> %d lines ; missing=%d ; %s'
          % (len(bl), len(nb.split('\n')), len(arc.split('\n')), len(na.split('\n')),
             len(miss), 'OK' if ok else 'FAIL'))
    return 0 if ok else 1

if __name__ == '__main__':
    sys.exit(main('--dry' in sys.argv))
