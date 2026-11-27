# -*- coding: utf-8 -*-
"""R171 K：收口总检（全部当场实测，不引用旧输出）。"""
import hashlib, io, json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..'))
TIER = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
RC, BRD, ARC = (os.path.join(TIER, x) for x in ('R14_COMMON.md', 'STATUS_BOARD.md', 'BOARD_ARCHIVE.md'))
LED = os.path.join(ROOT, 'lead', 'GOAL_THREE_TARGETS_20261018.md')
LOCK = os.path.join(ROOT, 'lead', 'LEAD_LOCK')
V550 = os.path.join(TIER, 'R17_R122_FACTINDEX_V550', 'FACT_INDEX.tsv')
V551 = os.path.join(TIER, 'R17_R123_FACTINDEX_V551', 'FACT_INDEX.tsv')
CD = os.path.join(TIER, 'check_disc.py')
FF = os.path.join(ROOT, '_r160', 'facts_floors.py')
GR = os.path.join(ROOT, '_r161', 'gate_runner.py')

FAIL, N = [], [0]
def ck(n, c, d=''):
    N[0] += 1
    print(('PASS  ' if c else 'FAIL  ') + '%02d. %s' % (N[0], n) + (('  :: ' + str(d)) if d and not c else ''))
    if not c: FAIL.append(n)

R = lambda p: io.open(p, 'rb').read()
# ---- 五项 CR ----
for p, want in ((RC, 1081), (LED, 337), (LOCK, 137), (BRD, 0), (ARC, 2952)):
    ck('Q CR %s == %d' % (os.path.basename(p), want), R(p).count(b'\r\n') == want, R(p).count(b'\r\n'))
_bl = R(BRD).count(b'\n')
ck('Q 看板 %d 行：< 260（未触发归档）且 <= 300' % _bl, _bl < 260 and _bl <= 300, _bl)
ck('Q 归档字节未变 1,300,831', len(R(ARC)) == 1300831, len(R(ARC)))

# ---- 本轮四处新增各恰 1 处 ----
ck('Q §2.176 恰 1 处', R(RC).decode('utf-8').count('\n## 2.176 ·') == 1)
ck('Q §1226 恰 1 处', R(LED).decode('utf-8').count('## §1226 ·') == 1)
ck('Q ## PB · 恰 1 处', R(LOCK).decode('utf-8').count('\n## PB ·') == 1)
ck('Q 看板第 171 轮恰 1 段', R(BRD).decode('utf-8').count('## 🟢 R17 第 171 轮') == 1)
for i in range(1, 13):
    ck('Q PB%d. 行首锚定恰 1 处' % i,
       len(re.findall(r'(?m)^PB%d\. ' % i, R(LOCK).decode('utf-8'))) == 1)
ck('Q R170 的 PA1..PA14 仍各 1 处（未覆盖上一轮）',
   all(len(re.findall(r'(?m)^PA%d\. ' % i, R(LOCK).decode('utf-8'))) == 1 for i in range(1, 15)))

# ---- FACT_INDEX ----
s551 = R(V551)
ck('Q V551 = 120,540 B / 55 行 / CR 0', len(s551) == 120540 and s551.count(b'\n') == 55 and b'\r' not in s551,
   (len(s551), s551.count(b'\n')))
ck('Q V551 sha == 5d4981c8b40ecfb1…', hashlib.sha256(s551).hexdigest().startswith('5d4981c8b40ecfb1'),
   hashlib.sha256(s551).hexdigest()[:16])
ck('Q V550 一字未改（d85034b0… / 120,495 B）',
   hashlib.sha256(R(V550)).hexdigest().startswith('d85034b0b2e42fd3') and len(R(V550)) == 120495)

# ---- 指针 ----
fft = R(FF).decode('utf-8'); grt = R(GR).decode('utf-8')
ck('Q facts_floors 指向 V551、无 V550 残留',
   'R17_R123_FACTINDEX_V551' in fft and 'V550' not in fft)
ck('Q gate_runner 指向 V551、无 V550 残留',
   'R17_R123_FACTINDEX_V551' in grt and 'V550' not in grt)
ck('Q facts_floors 的 MASTER 是 2da2851e…', "MASTER_SHA256 = '2da2851e" in fft)
ck('Q facts_floors 的 TOTAL_BYTES = 120540', 'TOTAL_BYTES = 120540' in fft)

# ---- 三段实跑（当场）----
def run(cmd, timeout=900):
    p = subprocess.run([sys.executable] + cmd, capture_output=True, text=True, timeout=timeout)
    return p.returncode, p.stdout + p.stderr
rc1, o1 = run([CD])
ck('Q check_disc exit 0', rc1 == 0, o1[-500:])
ck('Q check_disc 无**行首** FAIL（NOTE 里含 FAIL 字样不算，如 can never FAIL）',
   not any(l.strip().startswith('FAIL') for l in o1.split('\n')),
   [l for l in o1.split('\n') if l.strip().startswith('FAIL')])
ck('Q check_disc C16 逐字 170 sections measured (pinned 170), hollow/deficient 0, missing 0, unpinned 0',
   '170 sections measured (pinned 170), hollow/deficient 0, missing 0, unpinned 0' in o1,
   [l for l in o1.split('\n') if 'C16 per-section' in l])
rc2, o2 = run([FF])
ck('Q facts_floors exit 0', rc2 == 0, o2[-400:])
ck('Q facts_floors D0 = 5d4981c8 / D8 120,540 / D9 2da2851e',
   'D0 sha=5d4981c8' in o2 and 'D8 total bytes: 120540' in o2 and 'D9 master pin: 2da2851e' in o2,
   [l for l in o2.split('\n') if l.startswith('  D')])
rc3, o3 = run([GR])
ck('Q gate_runner exit 0 且 G1=G2=G3=ok', rc3 == 0 and 'G1=ok' in o3 and 'G2=ok' in o3 and 'G3=ok' in o3,
   o3[-400:])
ck('Q GATE_VER 未升（仍 R166）', "GATE_VER = 'R166'" in R(CD).decode('utf-8'))

# ---- 孤儿进程（按 /proc/<pid>/cmdline，排除自身）----
orph = []
for pid in os.listdir('/proc'):
    if not pid.isdigit() or int(pid) == os.getpid():
        continue
    try:
        cl = io.open('/proc/%s/cmdline' % pid, 'rb').read().split(b'\0')
    except OSError:
        continue
    argv = [x.decode('utf-8', 'replace') for x in cl if x]
    if argv and 'python' in argv[0] and any('_r171/' in a for a in argv[1:]):
        orph.append((pid, argv[:3]))
ck('Q 无孤儿 r171 进程（排除自身、按 argv 判）', orph == [], orph)

print('\n  R14_COMMON %d B / 台账 %d B / LEAD_LOCK %d B / 看板 %d B / 归档 %d B'
      % (len(R(RC)), len(R(LED)), len(R(LOCK)), len(R(BRD)), len(R(ARC))))
print('\n=== %d 断言，%d FAIL ===' % (N[0], len(FAIL)))
for f in FAIL: print('  FAILED:', f)
sys.exit(1 if FAIL else 0)
