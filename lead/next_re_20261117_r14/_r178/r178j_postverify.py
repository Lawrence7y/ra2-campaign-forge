# -*- coding: utf-8 -*-
"""r178j：收口校验 —— 五 CR 不变量、三段门禁实跑、看板行数、母本未动、无孤儿进程。

另外把 r178d 那条方向写错的断言（C1.559）补一条**正控**：V560 的 csv 回环逐字节复现，
V559 的 csv 回环必然**不复现**（因为 V559 不带引号）—— 两条都断言，方向不再含糊。
"""
import glob, hashlib, os, re, subprocess, sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
TIER = os.path.join(ROOT, 'lead/next_re_20261117_r14')
RC = os.path.join(TIER, 'R14_COMMON.md')
LED = os.path.join(ROOT, 'lead/GOAL_THREE_TARGETS_20261018.md')
LOCK = os.path.join(ROOT, 'lead/LEAD_LOCK')
BRD = os.path.join(TIER, 'STATUS_BOARD.md')
ARC = os.path.join(TIER, 'BOARD_ARCHIVE.md')
FI = os.path.join(TIER, 'R17_R129_FACTINDEX_V561/FACT_INDEX.tsv')
PASS = FAIL = 0


def ck(n, c, d=''):
    global PASS, FAIL
    if c:
        PASS += 1; print('PASS %s  %s' % (n, d))
    else:
        FAIL += 1; print('FAIL %s  %s' % (n, d))


def cr(p):
    return open(p, 'rb').read().count(b'\r')


print('=== 1. 五项 CR 不变量 ===')
for name, p, want in (('R14_COMMON', RC, 1081), ('台账', LED, 337), ('LEAD_LOCK', LOCK, 137),
                      ('STATUS_BOARD', BRD, 0), ('BOARD_ARCHIVE', ARC, 2952)):
    got = cr(p)
    ck('CR %s == %d' % (name, want), got == want, got)

print()
print('=== 2. FACT_INDEX V561 ===')
raw = open(FI, 'rb').read()
ck('V561 bytes 133317', len(raw) == 133317, len(raw))
ck('V561 CR=0', raw.count(b'\r') == 0, raw.count(b'\r'))
ck('V561 LF=55', raw.count(b'\n') == 55, raw.count(b'\n'))
ck('V561 sha dd2c55c6',
   hashlib.sha256(raw).hexdigest() == 'dd2c55c6f8aeadf3195bf1dc7fc9bf39ce70ed5ad771c76d52b80e86fe25fee7')

print()
print('=== 3. 看板行数与归档 ===')
nb = open(BRD, 'rb').read().count(b'\n')
ck('看板行数 <= 300', nb <= 300, nb)
ck('看板行数 < 260（未触发归档）', nb < 260, nb)
ck('看板含第 178 轮恰 1', open(BRD, encoding='utf-8').read().count('第 178 轮') == 1)

print()
print('=== 4. 四件套新段在位 ===')
t = open(RC, encoding='utf-8').read()
ck('R14_COMMON §2.183 恰 1', t.count('## 2.183') == 1, t.count('## 2.183'))
ck('R14_COMMON §2.182 仍 1', t.count('## 2.182') == 1)
t = open(LED, encoding='utf-8').read()
ck('台账 §1233 恰 1', t.count('## §1233') == 1, t.count('## §1233'))
ck('台账 §1232 仍 1', t.count('## §1232') == 1)
t = open(LOCK, encoding='utf-8').read()
ck('LEAD_LOCK PI 段恰 1', t.count('\nPI · ') == 1, t.count('\nPI · '))
ck('LEAD_LOCK PH 段仍 1', t.count('\nPH · ') == 1)
t = open(BRD, encoding='utf-8').read()
ck('看板全 LF（无 CR）', '\r' not in t, t.count('\r'))

print()
print('=== 5. 三段门禁实跑 ===')
for cmd, tag, must in (
        ([sys.executable, 'check_disc.py'], 'check_disc', 'PASS  structure'),
        ([sys.executable, os.path.join(ROOT, '_r160/facts_floors.py')], 'facts_floors', 'PASS  structure'),
        ([sys.executable, os.path.join(ROOT, '_r161/gate_runner.py')], 'gate_runner', 'G1=ok  G2=ok  G3=ok')):
    r = subprocess.run(cmd, cwd=TIER, capture_output=True, text=True)
    ok = r.returncode == 0 and must in r.stdout
    ck('%s exit 0 且含 %r' % (tag, must), ok, r.returncode)
    for line in r.stdout.split('\n'):
        if 'sections measured' in line or 'G1=' in line or ('FAIL' in line and line.strip()):
            print('    ' + line.strip()[:120])

print()
print('=== 6. 反向验证：显式传 V560 必须三红 ===')
r = subprocess.run([sys.executable, os.path.join(ROOT, '_r160/facts_floors.py'),
                    os.path.join(TIER, 'R17_R128_FACTINDEX_V560/FACT_INDEX.tsv')],
                   cwd=TIER, capture_output=True, text=True)
reds = [l for l in r.stdout.split('\n') if l.strip().startswith('FAIL')]
ck('V560 反向验证 exit != 0', r.returncode != 0, r.returncode)
ck('V560 反向验证恰 3 条 FAIL', len(reds) == 3, len(reds))
ck('含 D0 / D6 / D8 三红',
   any('D0' in l for l in reds) and any('D6' in l for l in reds) and any('D8' in l for l in reds),
   [l.strip()[:60] for l in reds])

print()
print('=== 7. r178d C1.559 方向订正的正控 ===')
import csv, io
def roundtrip(p):
    txt = open(p, 'rb').read().decode('utf-8')
    rows = list(csv.reader(io.StringIO(txt), delimiter='\t'))
    buf = io.StringIO()
    csv.writer(buf, delimiter='\t', lineterminator='\n').writerows(rows)
    return buf.getvalue() == txt
ck('V560 csv 回环逐字节复现（正控）', roundtrip(os.path.join(TIER, 'R17_R128_FACTINDEX_V560/FACT_INDEX.tsv')))
ck('V559 csv 回环**不**复现（反控，因它不带引号）',
   not roundtrip(os.path.join(TIER, 'R17_R128_FACTINDEX_V559/FACT_INDEX.tsv')))

print()
print('=== 8. 母本与备份 ===')
BASE = os.path.join(TIER, 'R17_LEAD_BASELINE')
for tag, cur in (('R14_COMMON', RC), ('GOAL_THREE_TARGETS', LED), ('LEAD_LOCK', LOCK),
                 ('STATUS_BOARD', BRD), ('FACT_INDEX_CURRENT.md', os.path.join(TIER, 'FACT_INDEX_CURRENT.md')),
                 ('facts_floors.py', os.path.join(ROOT, '_r160/facts_floors.py')),
                 ('gate_runner.py', os.path.join(ROOT, '_r161/gate_runner.py')),
                 ('check_disc.py', os.path.join(TIER, 'check_disc.py'))):
    # r178g 用 '<tag>.before_r178.bak'；r178h 的 C16 备份另用了 'check_disc.py.before_r178_C16.bak'
    bak = os.path.join(BASE, tag + '.before_r178.bak')
    if not os.path.exists(bak):
        bak = os.path.join(BASE, tag + '.before_r178_C16.bak')
    ck('备份存在 %s' % tag, os.path.exists(bak), bak)
    if os.path.exists(bak):
        ck('备份与现盘不同（确实被改过）%s' % tag,
           hashlib.sha256(open(bak, 'rb').read()).hexdigest()
           != hashlib.sha256(open(cur, 'rb').read()).hexdigest())

print()
print('=== 9. 无孤儿进程 ===')
# S-611..S-613 / S-650 同族：不能把「正在跑本脚本的自己」「外层 bash -c」「主会话 claude -p」
# 算成孤儿。做法：从自身 pid 沿 PPid 回溯出整条祖先链，链上任何进程都不算孤儿；
# 只报「调用了 r178 脚本、但既不是我自己也不是我的祖先、也不是 ps/grep 本身」的进程。
me = os.getpid()
psout = subprocess.run(['ps', '-eo', 'pid,ppid,cmd'], capture_output=True, text=True).stdout
parent = {}
cmdof = {}
for line in psout.split('\n')[1:]:
    parts = line.split(None, 2)
    if len(parts) < 3: continue
    try:
        pid, ppid = int(parts[0]), int(parts[1])
    except ValueError:
        continue
    parent[pid] = ppid
    cmdof[pid] = parts[2]
ancestors = set()
cur = me
while cur in parent and cur != 0:
    ancestors.add(cur)
    cur = parent[cur]
ancestors.add(cur)
print('  自身祖先链（%d 个 pid，均不算孤儿）' % len(ancestors))
orph = []
for pid, cmd in cmdof.items():
    if pid in ancestors: continue
    if 'r178' not in cmd: continue
    if cmd.startswith('ps ') or 'grep' in cmd or 'ps -eo' in cmd: continue
    orph.append((pid, cmd[:80]))
ck('无 r178 孤儿进程（已排除自身祖先链）', orph == [], orph[:3])

print()
print('---- %d PASS / %d FAIL ----' % (PASS, FAIL))
sys.exit(0 if FAIL == 0 else 1)
