#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R148 K：§2.153 正文因补记 S-345/S-346 变长 ⇒ 该节 floor 必须重算重钉。
这是 r148j 之后的第二遍重钉，必须**单独落脚本**（不能手改），且重钉前先用现表复现当前钉。
本脚本可幂等重跑：若表内值已等于目标值，只校验不写。
"""
import hashlib, io, json, os, re, sys, time

BASE = '/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14'
BL = os.path.join(BASE, 'R17_LEAD_BASELINE')
GATE = os.path.join(BASE, 'check_disc.py')
FAILS = []


def ck(n, c, d=''):
    print(('  PASS ' if c else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not c:
        FAILS.append(n)


def rd(p):
    return io.open(p, encoding='utf-8', newline='').read()


rc = rd(os.path.join(BASE, 'R14_COMMON.md'))
cur, buf, sizes = None, [], {}
for l in rc.split('\n'):
    m = re.match(r'^##\s+2\.(\d+)\b', l)
    if m:
        if cur is not None:
            sizes[cur] = len('\n'.join(buf).encode('utf-8'))
        cur = int(m.group(1))
        buf = [l]
    elif cur is not None:
        buf.append(l)
if cur is not None:
    sizes[cur] = len('\n'.join(buf).encode('utf-8'))
ck('1 §2.153 在盘', 153 in sizes, sorted(sizes)[-2:])
target = sizes[153] - 21

g = rd(GATE)


def sha(t):
    return hashlib.sha256('\n'.join('%d:%d' % (k, t[k]) for k in sorted(t)).encode()).hexdigest()


m = re.search(r'C16_FLOORS = \{(.*?)\n\}', g, re.S)
tbl = {int(a): int(b) for a, b in re.findall(r'(\d+):\s*(\d+)', m.group(1))}
oldpin = re.search(r"C16_FLOORS_SHA256 = '([0-9a-f]{64})'", g).group(1)
ck('2 现表复现当前钉（算法一致）', sha(tbl) == oldpin, (sha(tbl)[:16], oldpin[:16]))
ck('3 表 147 项', len(tbl) == 147, len(tbl))
ck('4 目标 floor = §2.153 实测 %d − 21 = %d' % (sizes[153], target), target == sizes[153] - 21)

if tbl.get(153) == target:
    print('  幂等：表内 153 已 == 目标值，不写盘')
    ck('5 现钉仍是自洽的', sha(tbl) == oldpin, '')
else:
    ck('5 旧值 != 目标值（确实需要重钉）', tbl.get(153) != target, (tbl.get(153), target))
    tbl[153] = target
    newpin = sha(tbl)
    ck('6 新钉 != 旧钉', newpin != oldpin, [oldpin[:16], newpin[:16]])
    lines = ['C16_FLOORS = {']
    keys = sorted(tbl)
    row = []
    for i, k in enumerate(keys):
        row.append('%d: %d' % (k, tbl[k]))
        if len(row) == 5 or i == len(keys) - 1:
            lines.append('    ' + ', '.join(row) + ',')
            row = []
    lines.append('}')
    g1 = re.sub(r'C16_FLOORS = \{(.*?)\n\}', '\n'.join(lines), g, count=1, flags=re.S)
    g1 = g1.replace("C16_FLOORS_SHA256 = '%s'" % oldpin, "C16_FLOORS_SHA256 = '%s'" % newpin)
    src = open(GATE, 'rb').read()
    bakp = os.path.join(BL, 'check_disc.py.before_r148_repin153_%s.bak'
                        % time.strftime('%Y%m%d_%H%M%S'))
    with io.open(bakp, 'xb') as f:
        f.write(src)
    ck('7 备份 wx 且逐字节相同', open(bakp, 'rb').read() == src, os.path.basename(bakp))
    io.open(GATE, 'w', encoding='utf-8', newline='').write(g1)
    gb = rd(GATE)
    m2 = re.search(r'C16_FLOORS = \{(.*?)\n\}', gb, re.S)
    T2 = {int(a): int(b) for a, b in re.findall(r'(\d+):\s*(\d+)', m2.group(1))}
    ck('8 回读表 == 目标表', T2 == tbl, len(T2))
    ck('9 回读新钉 == 现算', newpin == sha(T2) == re.search(
        r"C16_FLOORS_SHA256 = '([0-9a-f]{64})'", gb).group(1), newpin[:16])
    ck('10 回读 CR == 0', gb.count('\r') == 0, gb.count('\r'))
    print('  钉 %s -> %s ; floor153 = %d' % (oldpin[:16], newpin[:16], target))

print('=== FAILS: %d ===' % len(FAILS))
json.dump(dict(fails=FAILS, sec153_bytes=sizes[153], floor153=target),
          open('/home/t628/projects/ra2-campaign-forge/_r148/r148k_repin153.json', 'w',
               encoding='utf-8'), ensure_ascii=False, indent=1)
sys.exit(1 if FAILS else 0)
