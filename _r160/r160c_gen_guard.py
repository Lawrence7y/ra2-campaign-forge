#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r160c_gen_guard.py (v2) —— 生成 facts_floors.py。

v1 被跨家族审计员 #372 打出 5 个真洞，v2 逐条堵：
  洞1 D0 恒真：v1 用 argv 指向副本时 abspath != EXPECT_CUR ⇒ D0 断言体根本不执行，
      沙箱 10/10 调用全带 argv，等于 D0 一次没测。v2：D0 **总是**比 sha256，
      只有显式 --ignore-pin（且会大声打印）才跳过。
  洞2 D5 只钉普查不钉归属：F01↔F13 互换 grade，普查仍是 27/24/1/2 ⇒ 过。v2：逐 fid 钉。
  洞3 D6 下界=实测一半：把每列截到下界，96765→54372 B 仍 exit 0。v2：下界=实测字节（不许缩）。
  洞4 D7 只钉计数不钉归属：失联项从 F04 搬到 F06、剥掉全部括号注解（-2733 B）⇒ 过。
      v2：逐 fid 钉证据项清单 + 第 4 列字节下界。
  洞5 D9 只覆盖 FLOORS/LOST 两张表：改 GRADES/TOTAL_BYTES_FLOOR 常量零成本。v2：一个
      主指纹覆盖**全部**常量（含逐 fid 的 grade 与证据清单）。

不手抄任何数字：全部从 V543 实测产出。
"""
import hashlib
import io
import csv
import os
import re
import sys
from collections import Counter

R = '/home/t628/projects/ra2-campaign-forge'
D = R + '/lead/next_re_20261117_r14'
CUR = D + '/R17_R115_FACTINDEX_V543/FACT_INDEX.tsv'
OUT = R + '/_r160/facts_floors.py'

fails = []
def ck(n, c, d=''):
    ok = bool(c)
    print(('  PASS ' if ok else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not ok: fails.append(n)
    return ok

def strip_note(s):
    s = s.strip()
    if s.endswith(')'):
        d = 0
        for i in range(len(s) - 1, -1, -1):
            if s[i] == ')': d += 1
            elif s[i] == '(':
                d -= 1
                if d == 0: return s[:i].strip()
    return s

def norm(p): return p.replace('\\', '/').strip()

def resolvable(p):
    for c in (p, 'lead/' + p, D + '/' + p):
        if os.path.exists(os.path.join(R, c)): return True
    return False

print('== 0 · 读 V543 实测 ==')
raw = open(CUR, 'rb').read()
sha543 = hashlib.sha256(raw).hexdigest()
ck('0.1 V543 LF-only', raw.count(b'\r') == 0, raw.count(b'\r'))
txt = io.open(CUR, encoding='utf-8', newline='').read()
rows = list(csv.reader(io.StringIO(txt), delimiter='\t'))
hdr, data = rows[0], rows[1:]
ck('0.2 表头 5 列', hdr == ['fact_id', 'statement', 'grade', 'evidence_paths', 'limitations'], hdr)
ck('0.3 54 行 / 每行 5 列', len(data) == 54 and all(len(r) == 5 for r in data), len(data))
ids = [r[0] for r in data]
ck('0.4 id = F01..F54', ids == ['F%02d' % i for i in range(1, 55)])
tot = sum(len(f.encode()) for r in rows for f in r)
ntab = sum(len(r) - 1 for r in rows)
nl = txt.count('\n')
ck('0.5 字节恒等式闭合', tot + ntab + nl == len(raw), '%d+%d+%d vs %d' % (tot, ntab, nl, len(raw)))

GRADES = {r[0]: r[2] for r in data}
FLOORS = {r[0]: (len(r[1].encode()), len(r[4].encode())) for r in data}   # v2: 下界 = 实测（不许缩）
EVID = {r[0]: [norm(strip_note(x)) for x in r[3].split(';') if x.strip()] for r in data}
EVIDB = {r[0]: len(r[3].encode()) for r in data}
items = [(r[0], p) for r in data for p in EVID[r[0]]]
lost = [p for _, p in items if not resolvable(p)]
lostc = Counter(lost)
ck('0.6 证据 178/74/43/16',
   (len(items), len(set(p for _, p in items)), len(lost), len(lostc)) == (178, 74, 43, 16),
   (len(items), len(set(p for _, p in items)), len(lost), len(lostc)))

def canon_g(d):   return '\n'.join("    '%s': '%s'," % (k, d[k]) for k in sorted(d))
def canon_f(d):   return '\n'.join("    '%s': (%d, %d)," % (k, d[k][0], d[k][1]) for k in sorted(d))
def canon_e(d):   return '\n'.join("    '%s': [%s]," % (k, ', '.join("'%s'" % x for x in d[k])) for k in sorted(d))
def canon_eb(d):  return '\n'.join("    '%s': %d," % (k, d[k]) for k in sorted(d))
def canon_l(d):   return '\n'.join("    '%s': %d," % (k, d[k]) for k in sorted(d))

GS, FS, ES, EBS, LS = canon_g(GRADES), canon_f(FLOORS), canon_e(EVID), canon_eb(EVIDB), canon_l(lostc)
# v2 洞5：一个主指纹覆盖全部常量
MASTER = hashlib.sha256(('\n'.join([sha543, str(len(raw)), GS, FS, ES, EBS, LS,
                                     str(len(items)), str(len(set(p for _, p in items))),
                                     str(len(lost)), str(len(lostc))])).encode()).hexdigest()
ck('0.7 主指纹可复算（正控）',
   hashlib.sha256(('\n'.join([sha543, str(len(raw)), GS, FS, ES, EBS, LS,
                              str(len(items)), str(len(set(p for _, p in items))),
                              str(len(lost)), str(len(lostc))])).encode()).hexdigest() == MASTER)

guard = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""facts_floors.py —— FACT_INDEX 守门脚本（R160 v2 生成，勿手改；改请改 _r160/r160c_gen_guard.py）。

存在理由（实测）：主门禁 check_disc.py 从不读 FACT_INDEX.tsv —— 它是这两条纪律的
C7 证据产物之外的**零接触**。所以台账的任何改动对既有门禁完全不可见。本脚本补此缺口。

检查项（v2 全部收紧；每条都经破坏性沙箱证明能 FAIL）：
  D0  sha256 指针。**无论 argv 指向哪里都比**（v1 在 argv 模式下恒不触发，是假门）。
  D1  LF-only。
  D2  表头 5 列逐字。
  D3  54 数据行 / 每行恰 5 列。
  D4  fact_id 恰为 F01..F54 有序无重。
  D5  **逐 fid 的 grade**（v1 只钉普查，F01<->F13 互换可过）。
  D6  **逐 fid 的 statement/limitations 字节不许缩**（v1 用一半为下界，截断一半可过）。
  D7  **逐 fid 的证据项清单** + 第 4 列字节不许缩 + 失联多重集（v1 只钉全局计数）。
  D8  总字节不许缩（v1 用一半为下界）。
  D9  **单一主指纹覆盖全部常量**（含 grade/EVID/EVIDB/字节/GATE 计数）。

如实声明的边界：
  1) 所有 pin 都是本文件里的常量。**同时改数据与常量**仍能过 —— 这是所有指纹/下界类
     门禁的共同上限（与主门禁 C10/C16 同族）。本脚本的价值不是「不可能绕过」，而是把
     「完全不被读」变成「任何缩水/换归/改 grade 都会撞到一条会 FAIL 的断言」。
  2) D6/D7/D8 采用「不许缩」而非「不许改」：允许追加、允许等长改写，禁止变短。
     若某轮确需缩短，必须**显式重钉**（与 GATE_VER 重钉同纪律），不得静默。
  3) 本脚本**不判断事实真假**，只判断台账结构与规模没有被静默削减。
  4) --ignore-pin 仅供破坏性自测使用，且会大声打印警告；生产调用不得带它。

退出码：0 全通过；1 有 FAIL。
"""
import csv
import hashlib
import io
import os
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.isdir(os.path.join(ROOT, 'lead')):
    ROOT = '/home/t628/projects/ra2-campaign-forge'
TIER = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
EXPECT_CUR = os.path.join(TIER, 'R17_R115_FACTINDEX_V543', 'FACT_INDEX.tsv')
CUR = EXPECT_CUR
IGNORE_PIN = False
for a in sys.argv[1:]:
    if a == '--ignore-pin': IGNORE_PIN = True
    elif not a.startswith('-'): CUR = a
if IGNORE_PIN:
    print('  !! WARNING --ignore-pin: sha256/master-pin assertions DISABLED (self-test only)')

CUR_SHA256 = '__SHA543__'
TOTAL_BYTES = __TOTALBYTES__
GRADES = {
__GS__
}
FLOORS = {
__FS__
}
EVID = {
__ES__
}
EVIDB = {
__EBS__
}
LOST = {
__LS__
}
LOST_ITEMS = __LOSTITEMS__
LOST_UNIQ = __LOSTUNIQ__
ITEMS = __ITEMS__
UNIQ = __UNIQ__
MASTER_SHA256 = '__MASTER__'

fails = []
def F(m): fails.append(m)

def strip_note(s):
    s = s.strip()
    if s.endswith(')'):
        d = 0
        for i in range(len(s) - 1, -1, -1):
            if s[i] == ')': d += 1
            elif s[i] == '(':
                d -= 1
                if d == 0: return s[:i].strip()
    return s

def norm(p): return p.replace('\\\\', '/').strip()

def resolvable(p):
    for c in (p, 'lead/' + p, TIER + '/' + p):
        if os.path.exists(os.path.join(ROOT, c)): return True
    return False

def canon_g(d):   return '\\n'.join("    '%s': '%s'," % (k, d[k]) for k in sorted(d))
def canon_f(d):   return '\\n'.join("    '%s': (%d, %d)," % (k, d[k][0], d[k][1]) for k in sorted(d))
def canon_e(d):   return '\\n'.join("    '%s': [%s]," % (k, ', '.join("'%s'" % x for x in d[k])) for k in sorted(d))
def canon_eb(d):  return '\\n'.join("    '%s': %d," % (k, d[k]) for k in sorted(d))
def canon_l(d):   return '\\n'.join("    '%s': %d," % (k, d[k]) for k in sorted(d))

print('--- facts_floors.py (R160 v2) ---')
if not os.path.exists(CUR):
    print('  FAIL  D0 ledger not found: %s' % CUR); print('[exit 1]'); sys.exit(1)

raw = open(CUR, 'rb').read()
sha = hashlib.sha256(raw).hexdigest()

# ---- D0：v2 无论路径是否等于 EXPECT_CUR 都比 sha ----
if not IGNORE_PIN and sha != CUR_SHA256:
    F('D0 sha256 drifted: %s != pinned %s (file=%s; deliberate re-pin required)'
      % (sha[:16], CUR_SHA256[:16], os.path.basename(os.path.dirname(CUR))))
print('  D0 sha=%s pinned=%s %s' % (sha[:16], CUR_SHA256[:16],
                                   'skip(--ignore-pin)' if IGNORE_PIN else ''))

cr = raw.count(b'\\r')
if cr: F('D1 CR bytes present: %d (must be LF-only)' % cr)
print('  D1 LF-only: CR=%d' % cr)
if cr:
    print('[exit 1] cannot parse safely'); sys.exit(1)

txt = io.open(CUR, encoding='utf-8', newline='').read()
rows = list(csv.reader(io.StringIO(txt), delimiter='\\t'))
hdr, data = rows[0], rows[1:]

EXP = ['fact_id', 'statement', 'grade', 'evidence_paths', 'limitations']
if hdr != EXP: F('D2 header differs: %r' % (hdr,))
print('  D2 header: %s' % ('ok' if hdr == EXP else 'MISMATCH'))

if len(data) != 54: F('D3 data rows = %d != 54' % len(data))
bad = [i for i, r in enumerate(data) if len(r) != 5]
if bad: F('D3 rows with !=5 cols at %r' % bad[:8])
print('  D3 rows=%d all-5-col=%s' % (len(data), 'yes' if not bad else 'NO'))

ids = [r[0] for r in data]
exp_ids = ['F%02d' % i for i in range(1, 55)]
if ids != exp_ids:
    F('D4 fact_id sequence broke at %r'
      % next((('idx%d %s!=%s' % (i, a, b)) for i, (a, b) in enumerate(zip(ids, exp_ids)) if a != b), 'length'))
print('  D4 fact_id F01..F54: %s' % ('ok' if ids == exp_ids else 'BROKEN'))

# ---- D5 v2：逐 fid 钉 grade ----
g_now = {r[0]: r[2] for r in data}
g_diff = [(k, GRADES[k], g_now.get(k)) for k in sorted(GRADES) if g_now.get(k) != GRADES[k]]
if g_diff: F('D5 per-fact grade changed: %r' % g_diff[:6])
print('  D5 per-fact grade: %d facts, %d changed' % (len(GRADES), len(g_diff)))

# ---- D6 v2：不许缩 ----
sh_ = []
for r in data:
    fid = r[0]
    if fid not in FLOORS: continue
    fs, fl = FLOORS[fid]
    s, l = len(r[1].encode()), len(r[4].encode())
    if s < fs: sh_.append('%s.stmt %d<%d' % (fid, s, fs))
    if l < fl: sh_.append('%s.lim %d<%d' % (fid, l, fl))
if sh_: F('D6 per-fact bytes SHRANK (growth is allowed, shrinkage is not): %s' % sh_[:10])
print('  D6 per-fact no-shrink: %d facts, %d breaches' % (len(FLOORS), len(sh_)))

# ---- D7 v2：逐 fid 证据清单 + 第4列字节不许缩 ----
items = []
ed = []
for r in data:
    fid = r[0]
    if fid not in EVID: continue
    cur = [norm(strip_note(x)) for x in r[3].split(';') if x.strip()]
    if cur != EVID[fid]:
        only_new = [x for x in cur if x not in EVID[fid]]
        only_gone = [x for x in EVID[fid] if x not in cur]
        ed.append('%s (+%r -%r)' % (fid, only_new[:3], only_gone[:3]))
    if len(r[3].encode()) < EVIDB[fid]:
        ed.append('%s col4 %dB<%dB' % (fid, len(r[3].encode()), EVIDB[fid]))
    items.extend((fid, p) for p in cur)
if ed: F('D7 per-fact evidence list/bytes changed: %s' % ed[:8])
uniq = set(p for _, p in items)
lost = [p for _, p in items if not resolvable(p)]
lostc = Counter(lost)
if len(items) != ITEMS: F('D7 evidence items = %d != %d' % (len(items), ITEMS))
if len(uniq) != UNIQ: F('D7 distinct paths = %d != %d' % (len(uniq), UNIQ))
if len(lost) != LOST_ITEMS: F('D7 lost items = %d != %d' % (len(lost), LOST_ITEMS))
if dict(lostc) != LOST:
    F('D7 lost multiset changed: new=%r gone=%r'
      % (sorted(set(lostc) - set(LOST))[:5], sorted(set(LOST) - set(lostc))[:5]))
print('  D7 evidence: items=%d uniq=%d lost_items=%d lost_uniq=%d per-fact-changes=%d'
      % (len(items), len(uniq), len(lost), len(lostc), len(ed)))

# ---- D8 v2：总字节不许缩 ----
if len(raw) < TOTAL_BYTES:
    F('D8 total bytes SHRANK: %d < %d (lost >= %d B)'
      % (len(raw), TOTAL_BYTES, TOTAL_BYTES - len(raw)))
print('  D8 total bytes: %d (no-shrink floor %d)' % (len(raw), TOTAL_BYTES))

# ---- D9 v2：单一主指纹覆盖全部常量 ----
_master = hashlib.sha256(('\\n'.join([CUR_SHA256, str(TOTAL_BYTES), canon_g(GRADES), canon_f(FLOORS),
                                      canon_e(EVID), canon_eb(EVIDB), canon_l(LOST),
                                      str(ITEMS), str(UNIQ), str(LOST_ITEMS), str(LOST_UNIQ)])).encode()).hexdigest()
if not IGNORE_PIN and _master != MASTER_SHA256:
    F('D9 MASTER pin drifted: constants were edited together with data')
print('  D9 master pin: %s' % _master[:16])

if fails:
    for m in fails: print('  FAIL  ' + m)
    print('[exit 1] %d FAIL' % len(fails)); sys.exit(1)
print('  PASS  structure/scale/ownership/evidence-chain all ok')
print('  BOUNDARY: pins STRUCTURE and SCALE, not truth; and a same-edit of data+constants')
print('            would still pass (common ceiling of all digest-based gates).')
print('[exit 0]'); sys.exit(0)
'''

guard = (guard
         .replace('__SHA543__', sha543)
         .replace('__TOTALBYTES__', str(len(raw)))
         .replace('__GS__', GS).replace('__FS__', FS).replace('__ES__', ES)
         .replace('__EBS__', EBS).replace('__LS__', LS)
         .replace('__LOSTITEMS__', str(len(lost))).replace('__LOSTUNIQ__', str(len(lostc)))
         .replace('__ITEMS__', str(len(items))).replace('__UNIQ__', str(len(set(p for _, p in items))))
         .replace('__MASTER__', MASTER))

with open(OUT, 'w', encoding='utf-8', newline='\n') as f:
    f.write(guard)
back = io.open(OUT, encoding='utf-8', newline='').read()
ck('1.1 回读逐字一致', back == guard)
ck('1.2 LF-only', back.count('\r') == 0)
ck('1.3 可编译', (lambda: (compile(back, OUT, 'exec'), True)[1])())
ck('1.4 无残留占位符', not re.search(r'__[A-Z0-9]{3,}__', back), re.findall(r'__[A-Z0-9]{3,}__', back)[:3])
print('\ngenerated %s bytes=%d sha=%s master=%s'
      % (OUT, len(guard.encode()), hashlib.sha256(guard.encode()).hexdigest()[:16], MASTER[:16]))
print('FAILS:', fails if fails else 'NONE')
sys.exit(1 if fails else 0)
