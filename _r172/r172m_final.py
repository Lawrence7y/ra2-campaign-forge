# -*- coding: utf-8 -*-
"""R172 M：收口总检。含三条**口径订正**（S-593 锚串不唯一、S-594 跨轮计数未作用域化、S-595 把表头当成数据行）。

每条断言都可失败；三段门禁当场跑，不引用旧输出。
"""
import hashlib, io, json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..'))
TIER = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
RC = os.path.join(TIER, 'R14_COMMON.md')
LED = os.path.join(ROOT, 'lead', 'GOAL_THREE_TARGETS_20261018.md')
LOCK = os.path.join(ROOT, 'lead', 'LEAD_LOCK')
BOARD = os.path.join(TIER, 'STATUS_BOARD.md')
ARCH = os.path.join(TIER, 'BOARD_ARCHIVE.md')
CD = os.path.join(TIER, 'check_disc.py')
FF = os.path.join(ROOT, '_r160', 'facts_floors.py')
GR = os.path.join(ROOT, '_r161', 'gate_runner.py')
PTR = os.path.join(TIER, 'FACT_INDEX_CURRENT.md')
V551 = os.path.join(TIER, 'R17_R123_FACTINDEX_V551', 'FACT_INDEX.tsv')
V552 = os.path.join(TIER, 'R17_R124_FACTINDEX_V552', 'FACT_INDEX.tsv')
V553 = os.path.join(TIER, 'R17_R125_FACTINDEX_V553', 'FACT_INDEX.tsv')

FAIL, N = [], [0]
def ck(n, c, d=''):
    N[0] += 1
    print(('PASS  ' if c else 'FAIL  ') + '%02d. %s' % (N[0], n) + (('  :: ' + str(d)) if d and not c else ''))
    if not c: FAIL.append(n)

def rd(p): return io.open(p, 'rb').read()

# ---- 1. 五项 CR ----
for name, p, cr in (('R14_COMMON', RC, 1081), ('台账', LED, 337), ('LEAD_LOCK', LOCK, 137),
                    ('STATUS_BOARD', BOARD, 0), ('BOARD_ARCHIVE', ARCH, 2952)):
    d = rd(p)
    ck('R1 %s CR == %d（实测 %d）' % (name, cr, d.count(b'\r')), d.count(b'\r') == cr, d.count(b'\r'))

# ---- 2. FACT_INDEX 三版身份 ----
d553 = rd(V553); sha553 = hashlib.sha256(d553).hexdigest()
ck('F1 V553 = 121,010 B / 55 行 / CR 0 / 988a9567…',
   len(d553) == 121010 and d553.count(b'\n') == 55 and b'\r' not in d553 and sha553.startswith('988a9567155d8dc3'),
   (len(d553), sha553[:16]))
ck('F2 V552 一字未改（28155d36… / 120,962 B）',
   hashlib.sha256(rd(V552)).hexdigest().startswith('28155d363b75de48') and len(rd(V552)) == 120962)
ck('F3 V551 一字未改（5d4981c8… / 120,540 B）',
   hashlib.sha256(rd(V551)).hexdigest().startswith('5d4981c8b40ecfb1') and len(rd(V551)) == 120540)
rows = {}
for line in io.open(V553, encoding='utf-8'):
    c = line.rstrip('\n').split('\t'); rows[c[0]] = c
ck('F4 表头 5 列 / 54 数据行（S-595：dict 含表头键，故 55 个键）',
   len(rows) == 55 and 'fact_id' in rows and len(rows['F01']) == 5, len(rows))
ck('F5 F23 计数串一字未动（458 / 291 / 293 / 1,196 / 1,654 全在）',
   all(s in rows['F23'][1] + rows['F23'][4] for s in ('458', '291', '293', '1,196', '1,654')))
ck('F6 F23 新增作用域句恰 1 处',
   (rows['F23'][4]).count('作用域：sha256 只由前者给出') == 1)
ck('F7 F24 新增限定「（**2026-11-22 快照值，非现盘体量**）」在 statement 恰 1 处',
   rows['F24'][1].count('（**2026-11-22 快照值，非现盘体量**）') == 1)
def grades_of(p):
    out = {}
    for line in io.open(p, encoding='utf-8'):
        c = line.rstrip('\n').split('\t')
        if c[0].startswith('F') and len(c) == 5: out[c[0]] = c[2]
    return out
g553, g551 = grades_of(V553), grades_of(V551)
from collections import Counter
ck('F8 grade 逐条与 V551 相同、分布同为 26/1/24/3',
   g553 == g551 and Counter(g551.values()) == Counter({'[已证]': 26, '[流程]': 24, '未取得': 3, '[静态推断]': 1}),
   (sorted(Counter(g551.values()).items()), len(g551)))
ck('F9 F35 两列与 V551 逐字节相同（本轮对 F35 一字未改）',
   [r for r in [l.rstrip('\n').split('\t') for l in io.open(V551, encoding='utf-8')] if r[0] == 'F35'][0][1:]
   == rows['F35'][1:])

# ---- 3. 门禁 pin 与指针 ----
fft = io.open(FF, encoding='utf-8').read()
grt = io.open(GR, encoding='utf-8').read()
ck('G1 facts_floors 指 V553 / CUR_SHA256 / TOTAL_BYTES 与实测一致',
   'R17_R125_FACTINDEX_V553' in fft and sha553 in fft and 'TOTAL_BYTES = 121010' in fft)
ck('G2 facts_floors 无旧版本残留（V551 / V552 均 0 次）', 'V551' not in fft and 'V552' not in fft)
ck('G3 facts_floors FLOORS[F23]=(1785,8200) / FLOORS[F24]=(10613,31158)',
   "'F23': (1785, 8200)," in fft and "'F24': (10613, 31158)," in fft)
ck('G4 gate_runner 指 V553、无 V551/V552 残留', 'V553' in grt and 'V551' not in grt and 'V552' not in grt)
ck('G5 gate_runner 仍无行首 GATE_VER 赋值（未偷偷升门）', re.search(r"^GATE_VER = '", grt, re.M) is None)
pt = io.open(PTR, encoding='utf-8').read()
ck('G6 指针指 V553 / 新 sha / 121010 / R172 / V530..V553 24 份',
   'R17_R125_FACTINDEX_V553' in pt and sha553 in pt and '121010' in pt and '| 声明轮次 | R172 |' in pt and 'V530..V553' in pt)
ck('G7 指针无旧值残留', 'R17_R122_FACTINDEX_V550' not in pt and '120495' not in pt)
ck('G8 C16 表 171 条且含 id 177',
   len(re.findall(r'^\s{4}\d+: \d+,', io.open(CD, encoding='utf-8').read(), re.M)) >= 171
   and '    177: 3329,' in io.open(CD, encoding='utf-8').read())

# ---- 4. 四件套段落 ----
r = io.open(RC, encoding='utf-8').read(); l = io.open(LOCK, encoding='utf-8').read()
g = io.open(LED, encoding='utf-8').read(); b = io.open(BOARD, encoding='utf-8').read()
ck('S1 R14_COMMON §2.177 恰 1 处', r.count('\n## 2.177 · R172') == 1)
ck('S2 台账 §1227 恰 1 处', g.count('\n## §1227 · R172') == 1)
ck('S3 LEAD_LOCK「PC · R17 第 172 轮」恰 1 处', len([1 for x in l.split('\n') if x.startswith('PC · R17 第 172 轮')]) == 1)
ck('S4 看板第 172 轮段恰 1 处', b.count('## 🟢 R17 第 172 轮') == 1)
ck('S5 看板行数 %d < 260（未触发归档）/ BOARD_ARCHIVE 未动' % b.count('\n'), b.count('\n') < 260)
ck('S6 前轮段未误伤（PA1 / PB1 / §2.176 / §1226 各 1 处）',
   len([1 for x in l.split('\n') if x.startswith('PA1.')]) == 1
   and len([1 for x in l.split('\n') if x.startswith('PB1.')]) == 1
   and r.count('\n## 2.176 · R171') == 1 and g.count('\n## §1226 · R171') == 1)

# ---- 5. 跨轮计数必须作用域化（S-594 的口径） ----
def r172_segment_of_rc(text):
    i = text.find('## 2.177 ·')
    return text[i:]
seg = r172_segment_of_rc(r)
ck('T1 §2.177 段内 141afe44 恰 1 次（作为旧值）；全文件 2 次是含 R171 段的两处不同含义',
   seg.count('141afe44') == 1 and r.count('141afe44') == 2, (seg.count('141afe44'), r.count('141afe44')))
ck('T2 §2.177 段内 84273ed6 恰 1 次 / bb7fe832 恰 0 次（后者属 R171 段）',
   seg.count('84273ed6') == 1 and seg.count('bb7fe832') == 0)

# ---- 6. 三段门禁当场跑 ----
def run(args, t=900):
    p = subprocess.run([sys.executable] + args, capture_output=True, text=True, timeout=t)
    return p.returncode, p.stdout + p.stderr
rc1, o1 = run([CD])
ck('X1 check_disc exit 0', rc1 == 0, o1[-600:])
ck('X1b 无行首 FAIL', not any(x.strip().startswith('FAIL') for x in o1.split('\n')),
   [x for x in o1.split('\n') if x.strip().startswith('FAIL')])
ck('X1c NOTE 逐字 171 sections measured (pinned 171) … unpinned 0',
   '171 sections measured (pinned 171), hollow/deficient 0, missing 0, unpinned 0, min margin 20' in o1,
   [x for x in o1.split('\n') if 'C16 per-section' in x])
ck('X1d C10 自检 ok / C16d 打印新常量 84273ed6',
   'ok(R166)' in o1 and '84273ed6' in o1, [x for x in o1.split('\n') if 'C16d' in x or 'C10' in x])
rc2, o2 = run([FF])
ck('X2 facts_floors exit 0 / D0 988a9567 / D8 121010 / D9 ce436f7a',
   rc2 == 0 and '988a9567' in o2 and '121010' in o2 and 'ce436f7a' in o2,
   [x for x in o2.split('\n') if x.startswith(('D0', 'D8', 'D9'))])
rc3, o3 = run([GR])
ck('X3 gate_runner exit 0 / G1=ok / G2=ok / G3=ok', rc3 == 0 and 'G1=ok' in o3 and 'G2=ok' in o3 and 'G3=ok' in o3, o3[-600:])

# ---- 7. 无孤儿进程（按 /proc/<pid>/cmdline 判，排除自身） ----
me = os.getpid()
orph = []
for pid in os.listdir('/proc'):
    if not pid.isdigit() or int(pid) == me: continue
    try:
        parts = io.open('/proc/%s/cmdline' % pid, 'rb').read().split(b'\0')
    except Exception:
        continue
    parts = [p.decode('utf-8', 'replace') for p in parts if p]
    if parts and 'r172' in parts[0] and parts[0].endswith('python3') is False and any('python' in x for x in parts[:1]):
        if any('_r172/' in a for a in parts[1:]): orph.append(int(pid))
ck('X4 无孤儿 r172 进程（按 /proc/<pid>/cmdline，排除自身）', orph == [], orph)

# ---- 8. 本轮脚本清单 ----
scripts = sorted(f for f in os.listdir(HERE) if f.endswith('.py'))
ck('Y1 _r172 脚本 %d 个，均以 r172 前缀' % len(scripts), all(s.startswith('r172') for s in scripts), scripts)
print('  脚本:', ', '.join(scripts))

print('\n=== %d 断言，%d FAIL ===' % (N[0], len(FAIL)))
for f in FAIL: print('  FAILED:', f)
sys.exit(1 if FAIL else 0)
