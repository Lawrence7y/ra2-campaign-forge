# -*- coding: utf-8 -*-
"""结构探针：把 ④ 文本里的十六进制/数字换成 H8/N 后打印，看骨架与并表先例。"""
import io, re, sys
sys.dont_write_bytecode = True

R14 = r"D:/Project/ra2-campaign-forge/lead/next_re_20261117_r14"
COV = R14 + "/COVERAGE/coverage.tsv"
B4 = R14 + "/R16_F1_B4/delta.tsv"
W = '④ 活表槽位见证'


def norm(s):
    s = re.sub(r'[0-9A-F]{8}', 'H8', s)
    s = re.sub(r'\d+', 'N', s)
    return s


rows = {}
for ln in io.open(COV, encoding='utf-8-sig'):
    c = ln.rstrip('\r\n').split('\t')
    if len(c) < 8:
        continue
    rows[c[0].strip().upper()] = c

mode = sys.argv[1]

if mode == 'prec':
    for e in ('00464AC0', '004DE630', '004F42F0'):
        c4 = rows[e][3]
        i = c4.find(W)
        print('### %s  (n④=%d)' % (e, c4.count('④')))
        print('SKEL:', norm(c4[i:]) if i >= 0 else '(no witness)')
        print()

elif mode == 'merged':
    # 已并表的 SLOTN 行：含 ④ 活表槽位见证 的行，挑每张 vt 一张
    n = 0
    for e, c in rows.items():
        c4 = c[3]
        if W in c4 and c4.count('④') >= 2:
            i = c4.find(W)
            print('### %s name=%s n④=%d' % (e, c[2], c4.count('④')))
            print('TAIL:', norm(c4[i:]))
            n += 1
            if n >= 8:
                break

elif mode == 'old4':
    for e in ('00749F30', '0074BA30'):
        c4 = rows[e][3]
        print('### %s  n④=%d  len=%d' % (e, c4.count('④'), len(c4)))
        print('OLD4:', norm(c4))
        print()

elif mode == 'b4skel':
    for n, ln in enumerate(io.open(B4, encoding='utf-8-sig')):
        if n == 0:
            continue
        c = ln.rstrip('\r\n').split('\t')
        c4 = c[3]
        old = rows[c[0].strip().upper()][3]
        app = c4[len(old):]
        i = app.find(W)
        print('### %s' % c[0])
        print('SKEL:', norm(app[i:]) if i >= 0 else '(missing witness)')
