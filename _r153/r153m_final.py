#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R153 M：终态校验 + 登记 S-383（一条假 FAIL）。

S-383：r153l 的断言 `s.count("GATE_VER = 'R152'") == 1` 计数时**把注释行也算进去了** ——
check_disc.py 第 532 行的说明文字里 `grep=(?m)^GATE_VER = 'R152'` 含同一子串，
故实测计数 2、断言假 FAIL。但那次 `str.replace` 是**全量替换**，两处都被改成 R153，
结果反而是正确的（第 33 行常量 + 第 532 行说明同步）。⇒ 断言写窄了，不是数据错。
本脚本用「行首锚定」的正确判据复核。
"""
import hashlib
import os
import re
import subprocess
import sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
D = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
G = os.path.join(D, 'check_disc.py')
RC = os.path.join(D, 'R14_COMMON.md')
LED = os.path.join(ROOT, 'lead/GOAL_THREE_TARGETS_20261018.md')
LOCK = os.path.join(ROOT, 'lead/LEAD_LOCK')
BRD = os.path.join(D, 'STATUS_BOARD.md')
ARC = os.path.join(D, 'BOARD_ARCHIVE.md')
V542 = os.path.join(D, 'R17_R114_FACTINDEX_V542', 'FACT_INDEX.tsv')
DR = os.path.join(D, 'DISC_RECHECK.tsv')
DU = os.path.join(D, 'DISC_UNVERIFIABLE.tsv')

fail = []


def ck(n, c, d=''):
    ok = bool(c)
    print(('  PASS ' if ok else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not ok:
        fail.append(n)
    return ok


print('=== S-383：用行首锚定复核 GATE_VER ===')
gs = open(G, encoding='utf-8').read()
m = re.findall(r"(?m)^GATE_VER = '(R\d+)'", gs)
ck('行首 GATE_VER 恰 1 处且 = R153', m == ['R153'], m)
naive = gs.count("GATE_VER = 'R152'")
ck('S-383 复现：朴素子串计数对旧值是 0、说明替换已全量完成', naive == 0, naive)
naive_new = gs.count("GATE_VER = 'R153'")
ck('S-383 复现：朴素计数对新值是 2（常量 1 + 注释 1）—— 这就是假 FAIL 的根因',
   naive_new == 2, naive_new)
ck('注释行也已同步到 R153', "live 写 `grep=(?m)^GATE_VER = 'R153'`" in gs)

print('\n=== 五项 CR 不变量 ===')
FILES = {
    'R14_COMMON': (RC, 1081),
    'LEAD_LOCK': (LOCK, 137),
    'LEDGER': (LED, 337),
    'STATUS_BOARD': (BRD, 0),
    'BOARD_ARCHIVE': (ARC, 2952),
}
for k, (p, want) in FILES.items():
    b = open(p, 'rb').read()
    ck('%s CR == %d' % (k, want), b.count(b'\r') == want, b.count(b'\r'))

print('\n=== 产物钉值 ===')
for name, p in (('V542', V542), ('check_disc', G), ('DISC_RECHECK', DR),
                ('DISC_UNVERIFIABLE', DU)):
    b = open(p, 'rb').read()
    print('  %-18s %9d B  CR=%-5d sha=%s'
          % (name, len(b), b.count(b'\r'), hashlib.sha256(b).hexdigest()[:16]))

print('\n=== 看板行数 ===')
bl = [l for l in open(BRD, encoding='utf-8', newline='').read().split('\n') if l]
print('  非空行 = %d（阈值 260，硬上限 300）' % (len(bl) - 1))
ck('看板非空行 <= 260', len(bl) - 1 <= 260, len(bl) - 1)

print('\n=== 门禁终态 ===')
r = subprocess.run([sys.executable, 'check_disc.py'], cwd=D, capture_output=True, text=True,
                   timeout=600)
ck('门禁 exit 0', r.returncode == 0, r.returncode)
for ln in r.stdout.split('\n'):
    if re.search(r'C10 self|C15 |C16 |C16d|C7d|C12 |C12b|PASS  structure', ln):
        print('  ' + ln.strip())

print('\n=== 无孤儿进程 ===')
# S-384：初版判据 `grep -E '_r153/|check_disc'` 会命中本会话自己的 claude 命令行
# （其 prompt 正文里含 check_disc 字样），故实测得 4 而非 0 —— 假 FAIL。
# 改为只认「python3 解释器 + _r153 脚本路径」这一进程形态。
# S-385：上一步把判据改窄后仍得 1 —— 那个 1 就是**本脚本自己**（python3 跑 _r153/r153m_final.py）。
# 正确判据必须排除自身 PID。
ps = subprocess.run(['bash', '-c',
                     "ps -eo pid,comm,args | awk -v me=%d '$1 != me && $2 ~ /^python3?$/ "
                     "&& $0 ~ /_r153\\//' | wc -l" % os.getpid()],
                    capture_output=True, text=True)
ck('无残留 r153 脚本进程（已排除本脚本自身 PID）',
   ps.stdout.strip() == '0', ps.stdout.strip())
ps2 = subprocess.run(['bash', '-c',
                      "ps -eo comm,args | awk '$1 ~ /^python3?$/ && $0 ~ /check_disc\\.py/' | wc -l"],
                     capture_output=True, text=True)
ck('无残留 check_disc.py 进程', ps2.stdout.strip() == '0', ps2.stdout.strip())

print('\n=== 本轮产物清单 ===')
for f in sorted(os.listdir(os.path.join(ROOT, '_r153'))):
    p = os.path.join(ROOT, '_r153', f)
    print('  %-32s %8d B' % (f, os.path.getsize(p)))

print('\nFAIL %d：%s' % (len(fail), fail))
sys.exit(1 if fail else 0)
