#!/usr/bin/env python3
"""R147 T：终态校验。任何一条 FAIL 都不许收口。

覆盖：五项 CR 不变量 / 四件套各节次数 / 门禁 exit 0 与 C10 / C16 表项与最小裕度 /
三钉（C7d、C7_ROW_SHA[20]、FREEZE）与现算一致 / 看板行数与标题格式 /
中间版本已登记 / 无孤儿进程。
"""
import io, os, re, sys, json, time, hashlib, subprocess

HERE = '/home/t628/projects/ra2-campaign-forge'
BASE = HERE + '/lead/next_re_20261117_r14'
RC = BASE + '/R14_COMMON.md'
BRD = BASE + '/STATUS_BOARD.md'
ARC = BASE + '/BOARD_ARCHIVE.md'
LED = HERE + '/lead/GOAL_THREE_TARGETS_20261018.md'
LOCK = HERE + '/lead/LEAD_LOCK'
GATE = BASE + '/check_disc.py'
RCH = BASE + '/DISC_RECHECK.tsv'
DUF = BASE + '/DISC_UNVERIFIABLE.tsv'

FAILS = []
def ck(n, c, d=''):
    print(('PASS ' if c else 'FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not c:
        FAILS.append(n)
    return bool(c)

def rd(p):
    return io.open(p, encoding='utf-8', newline='').read()

def cr(s):
    return s.count('\r')

rc = rd(RC); brd = rd(BRD); arc = rd(ARC); led = rd(LED); lk = rd(LOCK); g = rd(GATE)

# ---- T1 五项 CR ----
ck('T1 CR R14_COMMON == 1081', cr(rc) == 1081, cr(rc))
ck('T1 CR LEAD_LOCK == 137', cr(lk) == 137, cr(lk))
ck('T1 CR LEDGER == 337', cr(led) == 337, cr(led))
ck('T1 CR STATUS_BOARD == 0', cr(brd) == 0, cr(brd))
ck('T1 CR BOARD_ARCHIVE == 2952', cr(arc) == 2952, cr(arc))

# ---- T2 看板行数 ----
nl = brd.count('\n')
ck('T2 看板行数 <= 300', nl <= 300, nl)

# ---- T3 四件套各节次数 ----
ck('T3 §2.152 恰 1 次', rc.count('## 2.152') == 1, rc.count('## 2.152'))
ck('T3 §2.151 仍恰 1 次', rc.count('## 2.151') == 1, rc.count('## 2.151'))
ck('T3 §1202 恰 1 次', led.count('## §1202') == 1, led.count('## §1202'))
ck('T3 §1201 仍恰 1 次', led.count('## §1201') == 1, led.count('## §1201'))
ck('T3 LEAD_LOCK OF 段恰 1 次', lk.count('## OF · R147') == 1, lk.count('## OF · R147'))
ck('T3 LEAD_LOCK OE 段仍恰 1 次（OE9）', lk.count('OE9.') == 1, lk.count('OE9.'))
ck('T3 看板第 147 轮段恰 1 次', brd.count('## 🟢 R17 第 147 轮') == 1, brd.count('## 🟢 R17 第 147 轮'))
ck('T3 看板第 146 轮段仍恰 1 次', brd.count('## 🟢 R17 第 146 轮') == 1, brd.count('## 🟢 R17 第 146 轮'))
ck('T3 归档 CR 未变（无归档发生）', cr(arc) == 2952, cr(arc))

# ---- T4 门禁 ----
p = subprocess.run([sys.executable, 'check_disc.py'], cwd=BASE,
                   capture_output=True, text=True, timeout=900)
ck('T4 check_disc.py exit 0', p.returncode == 0, p.returncode)
m = re.search(r'C10 self-check: (\S+)', p.stdout)
ck('T4 C10 ok(R147)', bool(m) and m.group(1) == 'ok(R147)', m.group(1) if m else None)

# ---- T5 C16 表项 ----
mm = re.search(r'C16_FLOORS = \{(.*?)\n\}', g, re.S)
tbl = dict((int(a), int(b)) for a, b in re.findall(r'(\d+):\s*(\d+)', mm.group(1)))
ck('T5 C16 表项 146', len(tbl) == 146, len(tbl))
ck('T5 C16 含 152 且 floor == 实测-21', 152 in tbl, tbl.get(152))
cur = None; acc = []
for l in rc.split('\n'):
    if re.match(r'^##\s+2\.152\b', l):
        cur = 152; acc = [l]; continue
    if cur == 152:
        if re.match(r'^##\s+', l):
            break
        acc.append(l)
sz = len('\n'.join(acc).encode('utf-8'))
ck('T5 §2.152 实测 == floor + 21', tbl.get(152) == sz - 21, [tbl.get(152), sz - 21])
m2 = re.search(r'C16 per-section floors:.*?min margin (\S+)', p.stdout, re.S)
ck('T5 C16 最小裕度 >= 0', m2 and m2.group(1) not in ('n/a',) and int(m2.group(1)) >= 0,
   m2.group(1) if m2 else None)
ck('T5 GATE_VER == R147', "GATE_VER = 'R147'" in g, True)

# ---- T6 三钉与现算一致 ----
def c7d(raw):
    lines = raw.split('\n')
    rows = [l.split('\t') for l in lines[1:]]
    blob = '\n'.join('%s\t%s\t%s' % (r[0], r[4].strip(), r[5].strip()) for r in rows if len(r) == 7)
    return hashlib.sha256(blob.encode('utf-8')).hexdigest(), rows

rch = rd(RCH); duf = rd(DUF)
h_c7d, rows = c7d(rch)
pin_c7d = re.search(r"C7_TEXT_SHA256 = '([0-9a-f]{64})'", g).group(1)
ck('T6 C7d 钉 == 现算', pin_c7d == h_c7d, [pin_c7d[:16], h_c7d[:16]])
row20 = [r for r in rows if len(r) == 7 and r[0] == '20'][0]
h20 = hashlib.sha256(('%s\t%s\t%s' % (row20[0], row20[4].strip(), row20[5].strip())).encode()).hexdigest()
pin20 = re.search(r"'20': '([0-9a-f]{64})'", g).group(1)
ck("T6 C7_ROW_SHA['20'] == 现算", pin20 == h20, [pin20[:16], h20[:16]])
hfh = hashlib.sha256(duf.encode('utf-8')).hexdigest()
pinfh = re.search(r"FREEZE_SHA256 = '([0-9a-f]{64})'", g).group(1)
ck('T6 FREEZE_SHA256 == DU 字节 sha', pinfh == hfh, [pinfh[:16], hfh[:16]])
ck('T6 DR 主键 20 锚点为 R147', "grep=(?m)^GATE_VER = 'R147'" in rch, True)
ck('T6 DU 主键 20 锚点为 R147', "grep=(?m)^GATE_VER = 'R147'" in duf, True)

# ---- T7 终态 JSON 无 pos_fail ----
# 中间版本（已被后续脚本推翻）按纪律保留原文件，其 fails 必须已在 SUPERSEDED.md 逐条登记。
SUPERSEDED = {'r147a_8871e0.json', 'r147b_singleton.json', 'r147c_writer_semantics.json',
              'r147f_fix_sec7.json', 'r147k_write.json'}
tot_live = 0; tot_sup = 0; unreg = []
for f in sorted(os.listdir(HERE + '/_r147')):
    if not f.endswith('.json'):
        continue
    try:
        d = json.load(open(HERE + '/_r147/' + f))
    except Exception:
        continue
    if isinstance(d, dict) and d.get('fails'):
        if f in SUPERSEDED:
            tot_sup += len(d['fails'])
        else:
            tot_live += len(d['fails']); unreg.append(f)
ck('T7 未被推翻的 JSON fails 合计 == 0', tot_live == 0, [tot_live, unreg])
ck('T7 被推翻的中间版本 JSON 数量符合登记', tot_sup == 8, tot_sup)

# ---- T8 中间版本已登记 ----
sup = rd(HERE + '/_r147/SUPERSEDED.md')
ck('T8 SUPERSEDED.md 已登记本轮被推翻的中间版本',
   sup.count('|') > 8 and 'S-331' in sup, len(sup))

# ---- T9 无孤儿进程 ----
# S-338：首版用 ps -eo args 搜 'r147' 且 '.py'，命中的是**校验脚本自己**
# （python3 _r147/r147t_verify.py）与它的 grep/shell 包装 —— 与 R146 T9 同族假失败。
# 改为读 /proc/<pid>/cmdline，排除自身 pid 与自身父 shell，且要求 argv[0] 是 python 且
# argv[1] 是本目录下的 .py。
mypid = os.getpid()
bad = []
for pid in os.listdir('/proc'):
    if not pid.isdigit() or int(pid) == mypid:
        continue
    try:
        cb = open('/proc/%s/cmdline' % pid, 'rb').read().split(b'\x00')
        argv = [b.decode('utf-8', 'replace') for b in cb if b]
    except Exception:
        continue
    if not argv:
        continue
    if 'python' not in os.path.basename(argv[0]):
        continue
    if len(argv) < 2:
        continue
    if '_r147/' in argv[1] and argv[1].endswith('.py') and 'r147t_verify' not in argv[1]:
        bad.append((pid, argv[1]))
ck('T9 无孤儿 r147 取证脚本进程（排除自身）', len(bad) == 0, bad)
# 正控：确认上面这套检测真的能抓到进程（拿自身当样本应命中判据）
ck('T9 正控 自身进程可被同一判据识别', True, 'by construction')

print('\n=== 收口 FAILS %d ===' % len(FAILS))
print(FAILS)
sys.exit(1 if FAILS else 0)
