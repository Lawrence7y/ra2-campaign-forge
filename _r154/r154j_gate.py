# -*- coding: utf-8 -*-
"""R154 · 门禁回归：C16_FLOORS 纳 159、GATE_VER R153->R154、同步 C10 锚点、重钉 FREEZE / C7d。

必须重钉的原因（逐条由脚本自己算，不写死）：
  1) R14_COMMON 新增 §2.159 ⇒ 节数 152->153、末节 158->159、C16 unpinned +1。
  2) GATE_VER 变化 ⇒ DISC_RECHECK / DISC_UNVERIFIABLE 的 C10 锚点行同步 ⇒ DISC_UNVERIFIABLE sha 变
     ⇒ FREEZE_SHA256 重钉。
  3) DISC_RECHECK 第 20 行 col5 变化 ⇒ C7_TEXT_SHA256 / C7_ROW_SHA[20] 重钉。
口径正控：把 id20 的锚点还原成 R153 后，必须复现旧钉 6855dfae…
"""
import hashlib, io, os, re, subprocess, sys, time

ROOT = '/home/t628/projects/ra2-campaign-forge'
D = ROOT + '/lead/next_re_20261117_r14'
G, DR, DU, RC = D + '/check_disc.py', D + '/DISC_RECHECK.tsv', D + '/DISC_UNVERIFIABLE.tsv', D + '/R14_COMMON.md'
BAKDIR = D + '/R17_LEAD_BASELINE'
fail = []
def ck(n, c, d=''):
    ok = bool(c); print(('  PASS ' if ok else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not ok: fail.append(n)
    return ok

def backup(p, tag):
    b = os.path.join(BAKDIR, os.path.basename(p) + '.before_r154%s_%s.bak' % (tag, time.strftime('%Y%m%d_%H%M%S')))
    fd = os.open(b, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, 'wb') as f: f.write(open(p, 'rb').read())
    ck('备份 wx %s' % os.path.basename(b), os.path.exists(b))

s = io.open(G, encoding='utf-8').read()
ck("pre GATE_VER = 'R153'", s.count("GATE_VER = 'R153'") >= 1)
ck('pre C16_FLOORS 末项 158: 2329', re.search(r'158:\s*2329', s) is not None)
ck('pre C16_FLOORS_SHA256 = e694471e…',
   "C16_FLOORS_SHA256 = 'e694471e3731f37e013c71e1c5f9c2cf2e7dd2464cf367b7c8c6939102a387af'" in s)
ck('pre C7_TEXT_SHA256 = 6855dfae…', 'C7_TEXT_SHA256 = \'6855dfae' in s)

# ---------- 实测 §2.159 含标题体 ----------
rc = io.open(RC, encoding='utf-8', newline='').read()
cur, buf, out = None, [], {}
for l in rc.split('\n'):
    m = re.match(r'^##\s+2\.(\d+)\b', l)
    if m:
        if cur is not None: out[cur] = len('\n'.join(buf).encode('utf-8'))
        cur, buf = int(m.group(1)), [l]
    elif cur is not None:
        buf.append(l)
if cur is not None: out[cur] = len('\n'.join(buf).encode('utf-8'))
ck('实测节数 153 / 末节 159', len(out) == 153 and max(out) == 159, (len(out), max(out)))
b159 = out[159]
ck('§2.159 含标题体 > 4000', b159 > 4000, b159)
newfloor = b159 // 2
print('§2.159 含标题体=%d ⇒ 新 floor=%d（= 一半，与既有建表口径一致）' % (b159, newfloor))

old_row = '    157: 4596,\n    158: 2329,\n}'
new_row = '    157: 4596,\n    158: 2329,\n    159: %d,\n}' % newfloor
ck('表尾锚点唯一', s.count(old_row) == 1, s.count(old_row))
s = s.replace(old_row, new_row)

blk = re.search(r'C16_FLOORS = \{(.*?)\n\}', s, re.S).group(1)
T = {int(a): int(b) for a, b in re.findall(r'(\d+):\s*(\d+)', blk)}
ck('新表 153 条、末项 159', len(T) == 153 and max(T) == 159, (len(T), max(T)))
norm = '\n'.join('%d:%d' % (k, T[k]) for k in sorted(T))
newsha = hashlib.sha256(norm.encode('utf-8')).hexdigest()
print('新 C16_FLOORS_SHA256 = %s' % newsha)
olds = "C16_FLOORS_SHA256 = 'e694471e3731f37e013c71e1c5f9c2cf2e7dd2464cf367b7c8c6939102a387af'"
ck('旧 C16 sha 常量唯一', s.count(olds) == 1, s.count(olds))
s = s.replace(olds, "C16_FLOORS_SHA256 = '%s'" % newsha)

# ---------- GATE_VER ----------
ck("GATE_VER 常量唯一", s.count("GATE_VER = 'R153'") == 1, s.count("GATE_VER = 'R153'"))
s = s.replace("GATE_VER = 'R153'", "GATE_VER = 'R154'")
s = s.replace("live 写 `grep=(?m)^GATE_VER = 'R153'`", "live 写 `grep=(?m)^GATE_VER = 'R154'`")
backup(G, 'e')
open(G, 'wb').write(s.encode('utf-8'))
ck('check_disc 回读一致', open(G, 'rb').read() == s.encode('utf-8'))
ck('GATE_VER 行首锚定恰 1 处', len(re.findall(r"(?m)^GATE_VER = 'R154'", s)) == 1,
   len(re.findall(r"(?m)^GATE_VER = 'R154'", s)))

# ---------- DISC_RECHECK / DISC_UNVERIFIABLE 锚点 ----------
OLD, NEW = "grep=(?m)^GATE_VER = 'R153'", "grep=(?m)^GATE_VER = 'R154'"
for p, name in ((DR, 'DISC_RECHECK'), (DU, 'DISC_UNVERIFIABLE')):
    t = io.open(p, encoding='utf-8', newline='').read()
    ck('%s 旧锚点恰 1 处' % name, t.count(OLD) == 1, t.count(OLD))
    t2 = t.replace(OLD, NEW)
    ck('%s 新锚点 1 / 旧 0' % name, t2.count(NEW) == 1 and t2.count(OLD) == 0)
    backup(p, 'e')
    open(p, 'wb').write(t2.encode('utf-8'))
    back = open(p, 'rb').read()
    ck('%s 回读一致且 CR 0' % name, back == t2.encode('utf-8') and back.count(b'\r') == 0)

# ---------- FREEZE_SHA256 ----------
du_new = open(DU, 'rb').read()
new_freeze = hashlib.sha256(du_new).hexdigest()
print('DISC_UNVERIFIABLE 新 sha256 = %s' % new_freeze)
gs = io.open(G, encoding='utf-8').read()
m = re.search(r"FREEZE_SHA256 = '([0-9a-f]+)'", gs)
ck('找到 FREEZE_SHA256', m is not None)
ck('FREEZE 旧值 = c1b449b1…', m.group(1).startswith('c1b449b1'), m.group(1)[:12])
gs = gs.replace("FREEZE_SHA256 = '%s'" % m.group(1), "FREEZE_SHA256 = '%s'" % new_freeze)
open(G, 'wb').write(gs.encode('utf-8'))
ck('check_disc 回读一致（FREEZE）', open(G, 'rb').read() == gs.encode('utf-8'))

# ---------- C7d 重钉 ----------
txt = io.open(DR, encoding='utf-8', newline='').read()
rows = [l.split('\t') for l in txt.split('\n') if l][1:]
ck('门禁口径 rows = 31', len(rows) == 31, len(rows))
def digest(rs):
    blob = '\n'.join('%s\t%s\t%s' % (r[0], r[4].strip(), r[5].strip()) for r in rs if len(r) == 7)
    return hashlib.sha256(blob.encode('utf-8')).hexdigest()
new_text = digest(rows)
rowsha = {r[0]: hashlib.sha256(('%s\t%s\t%s' % (r[0], r[4].strip(), r[5].strip())).encode('utf-8')).hexdigest()
          for r in rows if len(r) == 7}
print('现算 C7_TEXT_SHA256 = %s' % new_text)
old_rows = []
for r in rows:
    r2 = list(r)
    if len(r2) == 7 and r2[0] == '20' and "GATE_VER = 'R154'" in r2[5]:
        r2[5] = r2[5].replace("GATE_VER = 'R154'", "GATE_VER = 'R153'")
    old_rows.append(r2)
ck('口径正控：还原 id20 后复现旧钉 6855dfae…', digest(old_rows).startswith('6855dfae'), digest(old_rows)[:12])

gs = io.open(G, encoding='utf-8').read()
m = re.search(r"C7_TEXT_SHA256 = '([0-9a-f]{64})'", gs)
ck('当前 C7_TEXT_SHA256 = 6855dfae…', m.group(1).startswith('6855dfae'), m.group(1)[:12])
gs = gs.replace("C7_TEXT_SHA256 = '%s'" % m.group(1), "C7_TEXT_SHA256 = '%s'" % new_text)
m2 = re.search(r"C7_ROW_SHA = \{.*?'20': '([0-9a-f]{64})'", gs, re.S)
ck('找到 C7_ROW_SHA[20]', m2 is not None)
gs = gs.replace("'20': '%s'" % m2.group(1), "'20': '%s'" % rowsha['20'])
open(G, 'wb').write(gs.encode('utf-8'))
ck('check_disc 回读一致（C7d）', open(G, 'rb').read() == gs.encode('utf-8'))
m3 = re.search(r"C7_ROW_SHA = \{(.*?)\}", io.open(G, encoding='utf-8').read(), re.S)
pairs = dict(re.findall(r"'(\d+)': '([0-9a-f]{64})'", m3.group(1)))
ck('C7_ROW_SHA 条目 31', len(pairs) == 31, len(pairs))
ck('C7_ROW_SHA 与现算逐键全等', [k for k in rowsha if pairs.get(k) != rowsha[k]] == [])

# ---------- 跑门禁 ----------
print('\n[跑门禁]')
r = subprocess.run([sys.executable, 'check_disc.py'], cwd=D, capture_output=True, text=True, timeout=600)
ck('门禁 exit 0', r.returncode == 0, r.returncode)
for ln in r.stdout.split('\n'):
    if re.search(r'C7 |C7b|C7d|C10 |C11 frozen|C12|C15 |C16 |C16d|PASS|FAIL|BOUNDARY', ln):
        print('  ' + ln.strip())
if r.returncode != 0:
    print('--- STDERR ---'); print(r.stderr[-2000:]); print('--- STDOUT tail ---'); print(r.stdout[-2000:])

# ---------- 孤儿进程 / 看板行数 ----------
me = os.getpid()
ps = subprocess.run(['ps', '-eo', 'pid,cmd'], capture_output=True, text=True).stdout.split('\n')
orph = [l for l in ps if ('_r154/' in l or 'r154' in l) and str(me) not in l.split()[:1]
        and 'ps -eo' not in l and 'grep' not in l and 'claude' not in l]
ck('无孤儿 _r154 进程（已排除自身与 claude 命令行）', not orph, orph[:3])
board = io.open(D + '/STATUS_BOARD.md', encoding='utf-8').read()
ck('看板行数 <= 300', board.count('\n') <= 300, board.count('\n'))
print('\nFAIL %d：%s' % (len(fail), fail))
sys.exit(1 if fail else 0)
