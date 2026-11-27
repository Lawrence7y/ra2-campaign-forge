# -*- coding: utf-8 -*-
"""R172 H：FACT_INDEX_CURRENT.md 指针 V550 -> V553（实测：指针被 R171 漏更新，落后 3 版）。

反控：旧指针 3 处旧值（目录号/sha/字节/轮次）必须命中后消失；举例句里的 V547 保留；
      新指针的 4 项必须与磁盘实测一致；CR 仍 0。
另含 M4b 的正确形态反控（S-590：上一版 M4b 一次改坏两个不变式，--ignore-pin 救不回来）。
"""
import hashlib, io, json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..'))
TIER = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
PTR = os.path.join(TIER, 'FACT_INDEX_CURRENT.md')
BAK = os.path.join(TIER, 'R17_LEAD_BASELINE')
FF = os.path.join(ROOT, '_r160', 'facts_floors.py')
V553 = os.path.join(TIER, 'R17_R125_FACTINDEX_V553', 'FACT_INDEX.tsv')
V550 = os.path.join(TIER, 'R17_R122_FACTINDEX_V550', 'FACT_INDEX.tsv')
V552 = os.path.join(TIER, 'R17_R124_FACTINDEX_V552', 'FACT_INDEX.tsv')

FAIL, N = [], [0]
def ck(n, c, d=''):
    N[0] += 1
    print(('PASS  ' if c else 'FAIL  ') + '%02d. %s' % (N[0], n) + (('  :: ' + str(d)) if d and not c else ''))
    if not c: FAIL.append(n)

raw = io.open(V553, 'rb').read(); SHA = hashlib.sha256(raw).hexdigest()
praw = io.open(PTR, 'rb').read(); p = praw.decode('utf-8')
ck('H0 指针改前 CR 0 且 1,858 B（与磁盘基线一致）', b'\r' not in praw and len(praw) == 1858, (len(praw), praw.count(b'\r')))
ck('H1 改前指针仍指 V550（复现「R171 漏更新」这一事实）',
   'R17_R122_FACTINDEX_V550' in p and 'd85034b0b2e42fd3' in p and '120495' in p and '| 声明轮次 | R170 |' in p)
ck('H1b 改前版本区间串是 V530..V550 / 21 个', 'V530..V550' in p and '21 个' in p)
cnt = len([d for d in os.listdir(TIER) if d.startswith('R17_R1') and '_FACTINDEX_V5' in d])
ck('H1c 现盘 FACT_INDEX 目录数 = %d（指针应覆盖 530..553 共 24 份）' % cnt, cnt == 24, cnt)

q = p
q = q.replace('R17_R122_FACTINDEX_V550', 'R17_R125_FACTINDEX_V553')
q = q.replace('d85034b0b2e42fd34e8140e37e1d27be22cefbc2198d455b0295ef662c58a386', SHA)
q = q.replace('| 字节数 | 120495 |', '| 字节数 | %d |' % len(raw))
q = q.replace('| 声明轮次 | R170 |', '| 声明轮次 | R172 |')
q = q.replace('版本号 530..550 连续无缺，V550 同时是', '版本号 530..553 连续无缺，V553 同时是')
q = q.replace('V530..V550 是 21 个可独立复核的快照', 'V530..V553 是 24 个可独立复核的快照')
q = q.replace('其目录序号 R121 为最大', '其目录序号 R125 为最大').replace('R121 下只有这一个', 'R125 下只有这一个')
ck('H2 新指针指 V553 / 新 sha / 新字节 / R172',
   'R17_R125_FACTINDEX_V553' in q and SHA in q and str(len(raw)) in q and '| 声明轮次 | R172 |' in q)
ck('H3 旧值全不残留（V550 目录 / 旧 sha / 120495 / R170 轮次）',
   'R17_R122_FACTINDEX_V550' not in q and 'd85034b0b2e42fd3' not in q and '| 字节数 | 120495 |' not in q and '| 声明轮次 | R170 |' not in q)
ck('H3b 举例句里的 V547 保留（说明用，不该删）', '补一个 V547 草稿' in q)
ck('H3c 新版本区间 V530..V553 / 24 个', 'V530..V553' in q and '24 个' in q)
ck('H3d V550 与 V552 母本均一字未改',
   hashlib.sha256(io.open(V550, 'rb').read()).hexdigest().startswith('d85034b0b2e42fd3')
   and hashlib.sha256(io.open(V552, 'rb').read()).hexdigest().startswith('28155d363b75de48'))

bak = os.path.join(BAK, 'FACT_INDEX_CURRENT.md.before_r172.bak')
if not os.path.exists(bak):
    with io.open(bak, 'xb') as f: f.write(praw)
ck('H4 备份独占创建且字节相同', os.path.isfile(bak) and io.open(bak, 'rb').read() == praw)
io.open(PTR, 'wb').write(q.encode('utf-8'))
back = io.open(PTR, 'rb').read()
ck('H4b 回读逐字节 == 待写 / CR 0', back == q.encode('utf-8') and b'\r' not in back)

# ---- M4b 正确形态反控（S-590：一次只改一个不变式）----
src = io.open(FF, 'rb').read().decode('utf-8')
tmp = os.path.join(HERE, '_ff_mut_onlysha.py')
mut = src.replace("CUR_SHA256 = '%s'" % SHA, "CUR_SHA256 = '0000000000000000000000000000000000000000000000000000000000000000'", 1)
ck('M5 反控构造：只改 CUR_SHA256 一处', mut != src and mut.count("CUR_SHA256 = '0000") == 1)
io.open(tmp, 'w', encoding='utf-8').write(mut)
def run(a, t=900):
    r = subprocess.run([sys.executable] + a, capture_output=True, text=True, timeout=t); return r.returncode, r.stdout + r.stderr
rc1, o1 = run([tmp]); ck('M5b 只改 sha（不带 --ignore-pin）必须 FAIL', rc1 == 1, o1[-200:])
rc2, o2 = run([tmp, '--ignore-pin']); ck('M5c 同一副本带 --ignore-pin exit 0', rc2 == 0, o2[-200:])
os.remove(tmp)
rc3, o3 = run([FF]); ck('M5d 正控：未改的生产副本 exit 0', rc3 == 0, o3[-200:])

print('\n  指针 = %d B / sha %s / CR 0' % (len(back), hashlib.sha256(back).hexdigest()[:16]))
io.open(os.path.join(HERE, 'r172h_pointer.json'), 'w', encoding='utf-8').write(json.dumps(
    {'ptr_bytes': len(back), 'ptr_sha256': hashlib.sha256(back).hexdigest(),
     'ptr_sha_before': hashlib.sha256(praw).hexdigest(),
     'v553_sha256': SHA, 'dirs': cnt, 'bak': os.path.relpath(bak, ROOT)}, indent=1))
print('\n=== %d 断言，%d FAIL ===' % (N[0], len(FAIL)))
for f in FAIL: print('  FAILED:', f)
sys.exit(1 if FAIL else 0)
