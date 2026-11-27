# -*- coding: utf-8 -*-
"""r179j：收口后置核验（一次跑完全部不变量 + 正反控）。"""
import csv, hashlib, io, os, re, subprocess, sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
TIER = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
PASS = FAIL = 0


def ck(n, c, d=''):
    global PASS, FAIL
    if c:
        PASS += 1; print('PASS %s  %s' % (n, d))
    else:
        FAIL += 1; print('FAIL %s  %s' % (n, d))


def sha(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()

FILES = [
    (os.path.join(TIER, 'R14_COMMON.md'), 1081),
    (os.path.join(ROOT, 'lead', 'GOAL_THREE_TARGETS_20261018.md'), 337),
    (os.path.join(ROOT, 'lead', 'LEAD_LOCK'), 137),
    (os.path.join(TIER, 'STATUS_BOARD.md'), 0),
    (os.path.join(TIER, 'BOARD_ARCHIVE.md'), 2952),
]
for p, cr in FILES:
    raw = open(p, 'rb').read()
    ck('五 CR 之一 %s = %d' % (os.path.basename(p), cr), raw.count(b'\r') == cr, raw.count(b'\r'))
ck('看板行数 257 <= 260（本轮不需归档）', open(FILES[3][0], 'rb').read().count(b'\n') <= 260,
   open(FILES[3][0], 'rb').read().count(b'\n'))

# 节号与段落追加到位
rc = io.open(FILES[0][0], encoding='utf-8').read()
ck('R14 有 §2.184', '## 2.184 · R179' in rc)
ck('R14 §2.184 有收口补', '收口补（同轮第二段）：C16 随 §2.184 重钉' in rc)
led = io.open(FILES[1][0], encoding='utf-8').read()
ck('台账有 §1234', '## §1234 · R179' in led)
lock = io.open(FILES[2][0], encoding='utf-8').read()
ck('锁定有 PJ 段', '\nPJ · R17 第 179 轮' in lock)
ck('锁定有 PJ 收口补', 'S-661' in lock and 'S-662' in lock)
brd = io.open(FILES[3][0], encoding='utf-8').read()
ck('看板有第 179 轮', '## 🟢 R17 第 179 轮' in brd)

# 版本谱最终态
import glob
vers = []
for d in sorted(glob.glob(os.path.join(TIER, 'R17_R1*_FACTINDEX_V5*'))):
    p = os.path.join(d, 'FACT_INDEX.tsv')
    b = open(p, 'rb').read()
    vers.append((os.path.basename(d).split('_')[-1], len(b), b.count(b'%%'), b.count(b'\\\\')))
ck('版本数 34（V530..V563）', len(vers) == 34, len(vers))
ck('V562 双百分号归零', dict((v, p) for v, n, p, b in vers)['V562'] == 0)
ck('V563 双反斜杠归零', dict((v, b) for v, n, p, b in vers)['V563'] == 0)
ck('V561 仍 5 / 2（历史版本保留不删不改）',
   (dict((v, (p, b)) for v, n, p, b in vers)['V561']) == (5, 2),
   dict((v, (p, b)) for v, n, p, b in vers)['V561'])
ck('V534..V562 双反斜杠恒 2（V563 才归零）',
   all(b == 2 for v, n, p, b in vers if 534 <= int(v[1:]) <= 562),
   [(v, b) for v, n, p, b in vers if b])

# 指针
ptr = io.open(os.path.join(TIER, 'FACT_INDEX_CURRENT.md'), encoding='utf-8').read()
V563 = os.path.join(TIER, 'R17_R131_FACTINDEX_V563', 'FACT_INDEX.tsv')
ck('指针 sha == 现盘 V563 sha', sha(V563) in ptr)
ck('指针字节 == 133310', '| 字节数 | 133310 |' in ptr)
ck('指针轮次 R179', '| 声明轮次 | R179 |' in ptr)
ck('指针无 530..561 旧依据', '530..561 连续' not in ptr)

# 三个门禁实跑
def run(args):
    r = subprocess.run(args, capture_output=True, text=True, cwd=ROOT, timeout=400)
    return r.returncode, r.stdout + r.stderr

rc1, o1 = run([sys.executable, os.path.join(TIER, 'check_disc.py')])
ck('check_disc exit 0', rc1 == 0, rc1)
ck('check_disc C16 178/178 unpinned 0',
   '178 sections measured (pinned 178)' in o1 and 'unpinned 0' in o1)
rc2, o2 = run([sys.executable, os.path.join(ROOT, '_r160', 'facts_floors.py')])
ck('facts_floors exit 0', rc2 == 0, rc2)
ck('facts D0/D8/D9 三值在场',
   '28423e7928d84142' in o2 and '133310' in o2 and 'eab670346cd14b6e' in o2)
rc3, o3 = run([sys.executable, os.path.join(ROOT, '_r161', 'gate_runner.py')])
ck('gate_runner exit 0', rc3 == 0, rc3)
ck('gate_runner G1=G2=G3=ok', 'G1=ok' in o3 and 'G2=ok' in o3 and 'G3=ok' in o3)
ck('GATE_VER 仍 R166', 'GATE_VER=R166' in o3)

# 反控：显式传 V561 必须 D0 单红
rc4, o4 = run([sys.executable, os.path.join(ROOT, '_r160', 'facts_floors.py'), V563.replace('V563', 'V562').replace('R131', 'R130')])
ck('反控 V562 被 D0 抓（sha 已过期）', rc4 == 1 and 'D0 sha256 drifted' in o4, rc4)

print('---- %d PASS / %d FAIL ----' % (PASS, FAIL))
sys.exit(0 if FAIL == 0 else 1)
