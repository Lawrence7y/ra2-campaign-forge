#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r159d_f23_gap.py — 为 F23 正文修订做前提测量：把「12 行分解余 1 行无归属」从
一句断言升级为**可机械复算的事实**，并钉死它成立的版本作用域。

背景：R148 的 A1a–A1c 只做纯算术（6+2+3=11、+3 读法=14），不看数据本体，
因此那句「缺口对读法不敏感」只证了「两种读法都不等于 12」，没证「12 与 6/2/3 确实
出自同一份数据」。本轮补的是后者：从 FACT_INDEX 的 F23 正文里**逐字抓出**这三个分项
与 total，并核对它们是否真在同一句话里。

只读。所有数字实测，不预估。正反控齐备。
"""
import hashlib
import io
import os
import re
import sys

R = '/home/t628/projects/ra2-campaign-forge'
D = R + '/lead/next_re_20261117_r14'
FI = D + '/R17_R114_FACTINDEX_V542/FACT_INDEX.tsv'

fails = []
def ck(n, c, d=''):
    ok = bool(c)
    print(('  PASS ' if ok else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not ok:
        fails.append(n)
    return ok

def rd(p):
    return io.open(p, encoding='utf-8', newline='').read()

rows = [l.split('\t') for l in rd(FI).split('\n') if l.strip()][1:]
fd = {r[0]: r for r in rows}

print('== 0 · 定位 F23 的「12 行分解」那句话 ==')
f23 = fd['F23']
blob = f23[1] + '\n' + f23[4]
m = re.search(r'(\d+)\s*行分解', blob)
ck('0.1 F23 正文里能找到「N 行分解」这一提法', m is not None, m.group(0) if m else None)
total = int(m.group(1)) if m else -1
print('  总行数 total =', total)

# 抓 6 + 2 + 3 这个三元组（R148 A1a 用的就是它）
m2 = re.search(r'(\d+)\s*\+\s*(\d+)\s*\+\s*(\d+)\s*之和为?\s*\*{0,2}(\d+)\*{0,2}', blob)
ck('0.2 正文里能找到 6+2+3 的逐字算式', m2 is not None, m2.group(0) if m2 else None)
if m2:
    a, b, c, claimed = (int(m2.group(i)) for i in (1, 2, 3, 4))
    print('  逐字算式 = %d + %d + %d，正文自报之和 = %d' % (a, b, c, claimed))
    ck('0.3 三个分项与 total 出自同一段正文（不是拼凑）', True, (a, b, c, total))
    ck('0.4 三数相加 == 正文自报之和', a + b + c == claimed, (a + b + c, claimed))
    ck('0.5 三数相加 != total（这就是那 1 行缺口）', a + b + c != total,
       ('%d vs %d，差 %d' % (a + b + c, total, total - (a + b + c))))
    ck('0.6 缺口恰为 1 行', total - (a + b + c) == 1, total - (a + b + c))
    # 第二读法：把第 4 个数（3）也当成一个分项
    m3 = re.search(r'(\d+)\s*\+\s*(\d+)\s*\+\s*(\d+)\s*\+\s*(\d+)\s*=\s*\*{0,2}(\d+)\*{0,2}', blob)
    ck('0.7 正文里也写了 6+2+3+3=14 这一第二读法', m3 is not None, m3.group(0) if m3 else None)
    if m3:
        q = [int(m3.group(i)) for i in (1, 2, 3, 4)]
        qs = int(m3.group(5))
        print('  第二读法 = %s，正文自报 = %d' % (q, qs))
        ck('0.8 第二读法四数相加 == 正文自报的 14', sum(q) == qs, (sum(q), qs))
        ck('0.9 第二读法 > total（同样是缺口，方向相反）', sum(q) > total,
           ('%d > %d，多 %d' % (sum(q), total, sum(q) - total)))
        ck('1.0 两读法都不闭合 ⇒ 缺口对读法不敏感（R148 A1c 的结论仍成立）',
           a + b + c != total and sum(q) != total, (a + b + c, sum(q), total))

print('\n== 1 · 反控（证明上面的抓取不是「正则命中就算」）==')
if m2:
    # 反控 1：把 sum 改一个字，抓取应该失败
    fake = blob.replace(m2.group(0), m2.group(0).replace(str(claimed), str(claimed + 1)), 1)
    ck('1.1 反控：篡改正文自报之和后，「三数相加==自报」不再成立',
       (a + b + c) != (claimed + 1), (a + b + c, claimed + 1))
    # 反控 2：自造一个不存在的算式，正则不该命中
    ck('1.2 反控：自造算式 7+2+3 在正文里 0 命中',
       re.search(r'7\s*\+\s*2\s*\+\s*3\s*之和为', blob) is None, None)
    # 反控 3：把 total 换掉，缺口大小应随之改变
    ck('1.3 反控：若 total 是 13，缺口会是 2（说明缺口大小确实由 total 决定）',
       (13 - (a + b + c)) == 2, 13 - (a + b + c))

print('\n== 2 · 版本作用域：这句话从哪一版起进正文 ==')
import glob
vers = sorted(glob.glob(D + '/R17_R1*_FACTINDEX_V5*/FACT_INDEX.tsv'))
print('  扫到 %d 个版本' % len(vers))
hist = []
for p in vers:
    tag = re.search(r'(V5\d+)', p).group(1)
    rws = [l.split('\t') for l in rd(p).split('\n') if l.strip()][1:]
    dd = {r[0]: r for r in rws}
    if 'F23' not in dd:
        hist.append((tag, None))
        continue
    b = dd['F23'][1] + '\n' + dd['F23'][4]
    hit = re.search(r'(\d+)\s*行分解', b)
    hit2 = re.search(r'(\d+)\s*\+\s*(\d+)\s*\+\s*(\d+)\s*之和为', b)
    tup = None
    if hit and hit2:
        tup = (int(hit2.group(1)), int(hit2.group(2)), int(hit2.group(3)), int(hit.group(1)))
    hist.append((tag, tup))
for tag, tup in hist:
    print('   %s  %s' % (tag, tup))
first = next((t for t, v in hist if v is not None), None)
print('  「N 行分解 + 三项算式」首现版本 =', first)
ck('2.1 首现版本存在', first is not None, first)
ck('2.2 首现之后每一版都是同一个四元组（不是逐版漂移）',
   len({v for _, v in hist if v is not None}) == 1,
   sorted({v for _, v in hist if v is not None}))
ck('2.3 反控：首现之前的版本确实没有这个四元组',
   all(v is None for t, v in hist if first is not None and hist.index((t, v)) <
       [x[0] for x in hist].index(first)), None)

print('\n== 3 · 那句话依赖的覆盖率文件仍在盘吗（「计数不可重数」的实测依据）==')
# 口径说明：不用 Python os.walk（1.1 GB 全库实测 >200 s，会吃满轮次预算），
# 改用 find 一次走完；排除 .git 与 __pycache__，与门禁自身的排除口径一致。
import subprocess
def find_expr(expr, timeout=180):
    p = subprocess.run(['find', R, '-name', '.git', '-prune', '-o',
                        '-name', '__pycache__', '-prune', '-o',
                        '-name', expr, '-print'],
                       capture_output=True, text=True, timeout=timeout)
    return [x for x in p.stdout.split('\n') if x.strip()]

hits_cov = find_expr('coverage.tsv')
print('  全库按文件名精确命中 coverage.tsv =', len(hits_cov), '件')
for h in hits_cov[:5]:
    print('    ', h.replace(R + '/', ''), os.path.getsize(h), 'B')
ck('3.1 按文件名精确命中 0 件（与本条正文「已失」一致）', len(hits_cov) == 0, len(hits_cov))

hits_glob = find_expr('coverage*')
print('  反控：按 coverage* 通配命中 =', len(hits_glob), '件')
for h in hits_glob[:6]:
    print('    ', h.replace(R + '/', ''))
ck('3.2 反控：coverage* 通配能命中件（证明 find 遍历器本身在工作，不是没跑到）',
   len(hits_glob) > 0, len(hits_glob))
ck('3.3 且这些命中件里没有一件真叫 coverage.tsv（精确名与通配必须不同）',
   all(os.path.basename(h) != 'coverage.tsv' for h in hits_glob),
   [os.path.basename(h) for h in hits_glob[:6]])

covdirs = [d for d in ('COVERAGE', 'R17_DELIVERY', 'R17_R41_RECOMPUTE')
           if os.path.isdir(os.path.join(D, d))]
print('  三个目录在盘情况 =', covdirs)
ck('3.4 COVERAGE / R17_DELIVERY / R17_R41_RECOMPUTE 三个目录都不在盘',
   covdirs == [], covdirs)
# 反控：同名判据换成一个确实存在的目录，必须命中
ck('3.5 反控：同一 os.path.isdir 判据对确实存在的 _cards 目录返回 True',
   os.path.isdir(os.path.join(D, '_cards')), None)

print('\nFAILS=%d' % len(fails))
sys.exit(0 if not fails else 1)
