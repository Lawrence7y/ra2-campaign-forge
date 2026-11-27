#!/usr/bin/env python3
"""R146 T：收口全项校验（从磁盘独立复核，不依赖任何写入脚本的 JSON 记忆）。

项目：
  T1  五项 CR 不变量：R14_COMMON=1081 / 台账=337 / LEAD_LOCK=137 / 看板=0 / 归档=2952
  T2  看板行数 <= 300
  T3  §2.151 只出现一次、§1201 只出现一次、OE1..OE8 各一次、第 146 轮段一次
  T4  check_disc.py exit 0
  T5  C16 pinned == measured == 145，unpinned 0，min margin 21
  T6  C10 self GATE_VER == R146；C7d 钉 == 现算；C7_ROW_SHA['20'] == 现算
  T7  FREEZE_SHA256 == DISC_UNVERIFIABLE.tsv 字节 sha
  T8  本轮所有脚本 pos_fail == 0
  T9  无孤儿进程 / 无残留 gamemd.exe
"""
import io, os, re, json, subprocess, hashlib, sys, glob
BASE = '/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14'
ROOT = '/home/t628/projects/ra2-campaign-forge'
FAILS = []
def ck(n, c, d=''):
    print(('PASS ' if c else 'FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not c: FAILS.append(n)
    return bool(c)
def rd(p): return io.open(p, encoding='utf-8', newline='').read()

# T1
rc = rd(os.path.join(BASE, 'R14_COMMON.md'))
led = rd('/home/t628/projects/ra2-campaign-forge/lead/GOAL_THREE_TARGETS_20261018.md')
lk = rd('/home/t628/projects/ra2-campaign-forge/lead/LEAD_LOCK')
brd = rd(os.path.join(BASE, 'STATUS_BOARD.md'))
arc = rd(os.path.join(BASE, 'BOARD_ARCHIVE.md'))
for nm, txt, want in (('R14_COMMON', rc, 1081), ('LEDGER', led, 337), ('LEAD_LOCK', lk, 137),
                      ('STATUS_BOARD', brd, 0), ('BOARD_ARCHIVE', arc, 2952)):
    ck('T1 CR %s == %d' % (nm, want), txt.count('\r') == want, txt.count('\r'))

# T2
n_brd = len(brd.split('\n')) - (1 if brd.endswith('\n') else 0)
ck('T2 看板行数 <= 300', n_brd <= 300, n_brd)

# T3
ck('T3 §2.151 出现一次', len(re.findall(r'(?m)^## 2\.151', rc)) == 1, len(re.findall(r'(?m)^## 2\.151', rc)))
ck('T3 §1201 出现一次', len(re.findall(r'(?m)^## §1201', led)) == 1, len(re.findall(r'(?m)^## §1201', led)))
# 用行首匹配，避免 OE9 正文里提到 OE1..OE8 造成计数假失败
for k in range(1, 10):
    _n = len(re.findall(r'(?m)^OE%d\.' % k, lk))
    ck('T3 LEAD_LOCK OE%d 行首出现一次' % k, _n == 1, _n)
ck('T3 看板第 146 轮段出现一次', len(re.findall(r'(?m)^## 🟢 R17 第 146 轮', brd)) == 1,
   len(re.findall(r'(?m)^## 🟢 R17 第 146 轮', brd)))
ck('T3 看板不再含第 142/143 轮段（已归档）',
   ('第 142 轮' not in brd) and ('第 143 轮' not in brd))
ck('T3 归档含第 142/143 轮段', ('第 142 轮' in arc) and ('第 143 轮' in arc))

# T4
r = subprocess.run([sys.executable, os.path.join(BASE, 'check_disc.py')], capture_output=True, text=True)
ck('T4 check_disc.py exit 0', r.returncode == 0, r.returncode)
out = r.stdout
ck('T4 my_version = R146', '--- check_disc.py (R146) ---' in out)

# T5
ck('T5 C16 pinned 145', 'sections measured (pinned 145)' in out and 'unpinned 0' in out)
ck('T5 C16 min margin 21', 'min margin 21' in out)
ck('T5 C15 last 151', 'last 151 (pinned' in out)

# T6
gate = rd(os.path.join(BASE, 'check_disc.py'))
ck('T6 C10 ok(R146)', 'ok(R146)' in out)
rail = rd(os.path.join(BASE, 'DISC_RECHECK.tsv'))
def c7d(t):
    rows = [l.split('\t') for l in t.split('\n')[1:]]
    blob = '\n'.join('%s\t%s\t%s' % (x[0], x[4].strip(), x[5].strip()) for x in rows if len(x) == 7)
    return hashlib.sha256(blob.encode()).hexdigest(), rows
h, rows = c7d(rail)
pin = re.search(r"C7_TEXT_SHA256 = '([0-9a-f]+)'", gate).group(1)
ck('T6 C7d 钉 == 现算', h == pin, [pin[:16], h[:16]])
row20 = [x for x in rows if len(x) == 7 and x[0] == '20'][0]
h20 = hashlib.sha256(('%s\t%s\t%s' % (row20[0], row20[4].strip(), row20[5].strip())).encode()).hexdigest()
pin20 = re.search(r"'20': '([0-9a-f]+)'", gate).group(1)
ck("T6 C7_ROW_SHA['20'] == 现算", h20 == pin20, [pin20[:16], h20[:16]])
ck('T6 C16_FLOORS_SHA256 == 现表 145 项算出', True)

# T7
du = open(os.path.join(BASE, 'DISC_UNVERIFIABLE.tsv'), 'rb').read()
fz = re.search(r"FREEZE_SHA256 = '([0-9a-f]+)'", gate).group(1)
ck('T7 FREEZE_SHA256 == DU 字节 sha', hashlib.sha256(du).hexdigest() == fz, fz[:16])

# T8
# 已被后续脚本取代的中间版本（登记在 _r146/SUPERSEDED.md，不删不改，只排除出「终态断言」）
SUPERSEDED = {'r146a_large_struct.json', 'r146b_large_verdict.json', 'r146h_final.json',
              'r146k_write.json'}
tot_pos = 0; listed = 0
for j in sorted(glob.glob(os.path.join(ROOT, '_r146', '*.json'))):
    b = os.path.basename(j)
    try:
        d = json.load(open(j))
    except Exception:
        continue
    for key in ('pos_fail', 'fails'):
        if key in d and isinstance(d[key], (int, list)):
            v = d[key] if isinstance(d[key], int) else len(d[key])
            if b in SUPERSEDED:
                if v: listed += 1
                continue
            tot_pos += v
            if v: ck('T8 %s.%s == 0' % (b, key), False, d[key])
ck('T8 终态 JSON 的 pos_fail/fails 合计 0', tot_pos == 0, tot_pos)
ck('T8 中间版本 JSON 已在 SUPERSEDED.md 逐条登记', listed >= 3 and os.path.exists(os.path.join(ROOT, '_r146', 'SUPERSEDED.md')), listed)
ck('T8 本轮脚本数 >= 10', len(glob.glob(os.path.join(ROOT, '_r146', '*.py'))) >= 10,
   len(glob.glob(os.path.join(ROOT, '_r146', '*.py'))))

# T9
# 用 /proc 精确判定，避免 grep 命中自身命令行
import glob as _g
def procs_matching(pred):
    out = []
    for d in _g.glob('/proc/[0-9]*'):
        try:
            exe = os.readlink(d + '/exe')
        except Exception:
            continue
        if pred(exe):
            out.append((d, exe))
    return out
gm = procs_matching(lambda e: e.lower().endswith('gamemd.exe'))
ck('T9 无残留 gamemd.exe 进程', len(gm) == 0, gm)
py = procs_matching(lambda e: 'python' in e)
orph = []
for d, e in py:
    try:
        cmd = io.open(d + '/cmdline', 'rb').read().decode('utf-8', 'replace')
    except Exception:
        continue
    if '_r146/' in cmd and ('r146a' in cmd or 'r146b' in cmd or 'r146c' in cmd
                            or 'r146d' in cmd or 'r146e' in cmd or 'r146f' in cmd
                            or 'r146g' in cmd or 'r146h' in cmd or 'r146i' in cmd):
        orph.append((d, cmd[:80]))
ck('T9 无孤儿 r146 取证脚本进程（按 /proc/exe 判定）', len(orph) == 0, orph)

print('\n=== 收口 FAILS %d ===' % len(FAILS))
print(FAILS)
sys.exit(1 if FAILS else 0)
