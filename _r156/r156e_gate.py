# -*- coding: utf-8 -*-
"""R156 · 门禁回归：C16_FLOORS 纳 161、GATE_VER R155->R156、同步 C10 锚点、重钉 FREEZE / C7d。

幂等：所有「pre」断言只在 `--pre` 模式下要求（用于写入前核对旧态）；
不带参数时是**校验**模式，只核对终态是否自洽，可重复运行。

必须重钉的原因（逐条由脚本自己算，不写死）：
  1) R14_COMMON 新增 §2.161 ⇒ 节数 154->155、末节 161、C16 unpinned +1。
  2) GATE_VER 变化 ⇒ DISC_RECHECK / DISC_UNVERIFIABLE 的 C10 锚点行同步 ⇒ DISC_UNVERIFIABLE sha 变
     ⇒ FREEZE_SHA256 重钉。
  3) DISC_RECHECK 第 20 行 col5 变化 ⇒ C7_TEXT_SHA256 / C7_ROW_SHA[20] 重钉。
口径正控：把 id20 的锚点还原成 R155 后，必须复现旧钉 4ae99d52…

承 R154/R155 的自错族，本脚本的判据写法：
  · C7d 表过滤**必须** raw=[非空行] 再 raw[1:]（不能按 len(r)==7 过滤，表头会被算进去 —— S-410）；
  · 两个字典按**行首锚定** NAME = { 取，不用 dict(findall) 扫全文件（S-411/S-412）；
  · FAIL 判定**行首锚定**，不用 'FAIL' in stdout（S-413）；
  · 节数以**实测**为准，不写死（S-421：本轮我把它写成 154，实测 155）。
"""
import hashlib, io, os, re, subprocess, sys, time

ROOT = '/home/t628/projects/ra2-campaign-forge'
D = ROOT + '/lead/next_re_20261117_r14'
G, DR, DU, RC = D + '/check_disc.py', D + '/DISC_RECHECK.tsv', D + '/DISC_UNVERIFIABLE.tsv', D + '/R14_COMMON.md'
BAKDIR = D + '/R17_LEAD_BASELINE'
PRE = '--pre' in sys.argv
fail = []
def ck(n, c, d=''):
    ok = bool(c); print(('  PASS ' if ok else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not ok: fail.append(n)
    return ok

def backup(p, tag):
    b = os.path.join(BAKDIR, os.path.basename(p) + '.before_r156%s_%s.bak' % (tag, time.strftime('%Y%m%d_%H%M%S')))
    fd = os.open(b, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, 'wb') as f: f.write(open(p, 'rb').read())
    ck('备份 wx %s' % os.path.basename(b), os.path.exists(b))

# ---------- 实测 R14_COMMON 节数与末节 ----------
rc = io.open(RC, encoding='utf-8', newline='').read()
cur, buf, secs = None, [], {}
for l in rc.split('\n'):
    m = re.match(r'^##\s+2\.(\d+)\b', l)
    if m:
        if cur is not None: secs[cur] = len('\n'.join(buf).encode('utf-8'))
        cur, buf = int(m.group(1)), [l]
    elif cur is not None:
        buf.append(l)
if cur is not None: secs[cur] = len('\n'.join(buf).encode('utf-8'))
N_SEC, LAST = len(secs), max(secs)
print('实测 R14_COMMON 节数 = %d、末节 = %d、§%d 含标题体 = %d B' % (N_SEC, LAST, LAST, secs[LAST]))
ck('R14_COMMON 节数 = 末节 - 6（7..LAST 连续，历史口径）', N_SEC == LAST - 6, (N_SEC, LAST))
ck('末节是 §2.161', LAST == 161, LAST)
b161 = secs[161]
ck('§2.161 含标题体 > 4000 B', b161 > 4000, b161)
newfloor = b161 // 2
print('⇒ 新 floor = %d（= 一半，与既有建表口径一致）' % newfloor)

# ---------- 读门禁现态 ----------
s = io.open(G, encoding='utf-8').read()
ver = re.findall(r"(?m)^GATE_VER = '(\w+)'", s)
ck("GATE_VER 行首锚定恰 1 处", len(ver) == 1, ver)
def sha_of(name):
    m = re.search(name + r" = '([0-9a-f]{64})'", s)
    return m.group(1) if m else None
def table():
    blk = re.search(r'C16_FLOORS = \{(.*?)\n\}', s, re.S).group(1)
    return {int(a): int(b) for a, b in re.findall(r'(\d+):\s*(\d+)', blk)}

if PRE:
    ck("pre GATE_VER = 'R155'", ver == ['R155'], ver)
    ck('pre C16_FLOORS 末项 160: 3349', table().get(160) == 3349 and max(table()) == 160, (max(table()), table().get(160)))
    ck('pre C16_FLOORS_SHA256 = edf32ead…', (sha_of('C16_FLOORS_SHA256') or '').startswith('edf32ead'), sha_of('C16_FLOORS_SHA256'))
    ck('pre C7_TEXT_SHA256 = 4ae99d52…', (sha_of('C7_TEXT_SHA256') or '').startswith('4ae99d52'), sha_of('C7_TEXT_SHA256'))
    ck('pre FREEZE_SHA256 = 582137f6…', (sha_of('FREEZE_SHA256') or '').startswith('582137f6'), sha_of('FREEZE_SHA256'))

    old_row = '    159: 3198,\n    160: 3349,\n}'
    ck('pre 表尾锚点唯一', s.count(old_row) == 1, s.count(old_row))
    s = s.replace(old_row, '    159: 3198,\n    160: 3349,\n    161: %d,\n}' % newfloor)
    norm = '\n'.join('%d:%d' % (k, v) for k, v in sorted(table().items()))
    ck('pre 新表 %d 条、末项 161' % N_SEC, len(table()) == N_SEC and max(table()) == 161, (len(table()), max(table())))
    s = s.replace("C16_FLOORS_SHA256 = 'edf32eadcfe46d5211ecec18a85b850b0240d474323dc6fa053cfd57be2ad144'",
                  "C16_FLOORS_SHA256 = '%s'" % hashlib.sha256(norm.encode('utf-8')).hexdigest())
    s = s.replace("GATE_VER = 'R155'", "GATE_VER = 'R156'")
    s = s.replace("live 写 `grep=(?m)^GATE_VER = 'R155'`", "live 写 `grep=(?m)^GATE_VER = 'R156'`")
    backup(G, 'e')
    open(G, 'wb').write(s.encode('utf-8'))
    ck('check_disc 回读一致', open(G, 'rb').read() == s.encode('utf-8'))

    OLDV, NEWV = "grep=(?m)^GATE_VER = 'R155'", "grep=(?m)^GATE_VER = 'R156'"
    for p, name in ((DR, 'DISC_RECHECK'), (DU, 'DISC_UNVERIFIABLE')):
        t = io.open(p, encoding='utf-8', newline='').read()
        ck('%s pre 旧锚点恰 1 处' % name, t.count(OLDV) == 1, t.count(OLDV))
        t2 = t.replace(OLDV, NEWV)
        backup(p, 'e')
        open(p, 'wb').write(t2.encode('utf-8'))
        ck('%s 回读一致且 CR 0' % name, open(p, 'rb').read() == t2.encode('utf-8') and open(p, 'rb').read().count(b'\r') == 0)

    new_freeze = hashlib.sha256(open(DU, 'rb').read()).hexdigest()
    print('DISC_UNVERIFIABLE 新 sha256 = %s' % new_freeze)
    gs = io.open(G, encoding='utf-8').read()
    gs = gs.replace("FREEZE_SHA256 = '%s'" % re.search(r"FREEZE_SHA256 = '([0-9a-f]+)'", gs).group(1),
                    "FREEZE_SHA256 = '%s'" % new_freeze)
    open(G, 'wb').write(gs.encode('utf-8'))

    # C7d 重钉（门禁真实口径）
    txt = io.open(DR, encoding='utf-8', newline='').read()
    raw = [l for l in txt.split('\n') if l.strip()]
    rows = [l.split('\t') for l in raw[1:]]
    def digest(rs):
        return hashlib.sha256('\n'.join('%s\t%s\t%s' % (r[0], r[4].strip(), r[5].strip()) for r in rs if len(r) == 7).encode('utf-8')).hexdigest()
    rowsha = {r[0]: hashlib.sha256(('%s\t%s\t%s' % (r[0], r[4].strip(), r[5].strip())).encode('utf-8')).hexdigest() for r in rows if len(r) == 7}
    old_rows = []
    for r in rows:
        r2 = list(r)
        if len(r2) == 7 and r2[0] == '20' and "GATE_VER = 'R156'" in r2[5]:
            r2[5] = r2[5].replace("GATE_VER = 'R156'", "GATE_VER = 'R155'")
        old_rows.append(r2)
    ck('口径正控：还原 id20 后复现旧钉 4ae99d52…', digest(old_rows).startswith('4ae99d52'), digest(old_rows)[:12])
    gs = io.open(G, encoding='utf-8').read()
    cur7 = re.search(r"C7_TEXT_SHA256 = '([0-9a-f]{64})'", gs).group(1)
    ck('pre C7_TEXT_SHA256 = 4ae99d52…', cur7.startswith('4ae99d52'), cur7[:12])
    gs = gs.replace("C7_TEXT_SHA256 = '%s'" % cur7, "C7_TEXT_SHA256 = '%s'" % digest(rows))
    m2 = re.search(r"C7_ROW_SHA = \{.*?'20': '([0-9a-f]{64})'", gs, re.S)
    gs = gs.replace("'20': '%s'" % m2.group(1), "'20': '%s'" % rowsha['20'])
    open(G, 'wb').write(gs.encode('utf-8'))
    ck('check_disc 回读一致（C7d）', open(G, 'rb').read() == gs.encode('utf-8'))

# ---------- 终态自洽校验（两种模式都跑） ----------
print('\n[终态校验]')
s = io.open(G, encoding='utf-8').read()
ver = re.findall(r"(?m)^GATE_VER = '(\w+)'", s)
ck("终态 GATE_VER 行首锚定恰 1 处 = 'R156'", ver == ['R156'], ver)
ck("终态旧 GATE_VER 'R155' 行首 0 处", len(re.findall(r"(?m)^GATE_VER = 'R155'", s)) == 0)
T = table()
ck('终态 C16 表 %d 条、末项 161' % N_SEC, len(T) == N_SEC and max(T) == 161, (len(T), max(T)))
# S-422：上一版这里断言「每个 floor == 该节实测字节 // 2」，那是把 §2.161 的建表口径
# 当成全表口径。实测：7..12 的 ratio 恒为 0.25、156 是 0.50、157 是 0.45、158-160 是 0.41/0.38
# —— floor 是**逐节手写的历史值**，没有统一比例。正确判据只有两条：
#   ① floor <= 实测字节（不许超过实测，否则节被删改就会假通过）
#   ② 新增的 §2.161 的 floor 用本轮既定口径（实测 // 2）
ck('终态 C16 表所有 floor <= 该节实测字节（floor 不得高于实测）',
   all(T[k] <= secs[k] for k in T if k in secs), [k for k in T if k in secs and T[k] > secs[k]])
# S-424：上一版断言「§2.161 的 floor == 实测 // 2」。写完第九/十一节补记后 §2.161 变长
# （10,300 -> 11,712 B），而 floor 是**写入时刻**钉下的，不随正文增长 —— 于是等式自然不成立，
# 这是**正确行为**（floor 是下界，不是比率）。与 S-422 同族：又一次把「某一个时刻的口径」当成不变式。
# 真正该断言的只有：floor 存在、floor <= 实测、且门禁自己报 hollow/deficient 0。
ck('终态 §2.161 的 floor <= 该节当前实测（floor 是下界，不随正文增长）',
   T.get(161) is not None and T[161] <= secs[161], (T.get(161), secs[161]))
ck('终态 §2.161 的 margin > 0（节未被掏空）', secs[161] - T.get(161, 0) > 0, secs[161] - T.get(161, 0))
ck('终态 C16 表覆盖全部 %d 个节（无缺项）' % N_SEC, sorted(T) == sorted(secs), (len(T), len(secs)))
norm = '\n'.join('%d:%d' % (k, T[k]) for k in sorted(T))
ck('终态 C16_FLOORS_SHA256 与表内容一致', sha_of('C16_FLOORS_SHA256') == hashlib.sha256(norm.encode('utf-8')).hexdigest(),
   sha_of('C16_FLOORS_SHA256')[:16])
ck('终态 FREEZE_SHA256 与 DISC_UNVERIFIABLE 现 sha 一致',
   sha_of('FREEZE_SHA256') == hashlib.sha256(open(DU, 'rb').read()).hexdigest(), sha_of('FREEZE_SHA256')[:16])

# 终态 C7d：按门禁真实口径重算并与常量比
txt = io.open(DR, encoding='utf-8', newline='').read()
raw = [l for l in txt.split('\n') if l.strip()]
rows = [l.split('\t') for l in raw[1:]]
ck('终态 DISC_RECHECK raw 非空行 32 / 数据行 31', len(raw) == 32 and len(rows) == 31, (len(raw), len(rows)))
d_now = hashlib.sha256('\n'.join('%s\t%s\t%s' % (r[0], r[4].strip(), r[5].strip()) for r in rows if len(r) == 7).encode('utf-8')).hexdigest()
ck('终态 C7_TEXT_SHA256 与现算一致', sha_of('C7_TEXT_SHA256') == d_now, (sha_of('C7_TEXT_SHA256')[:16], d_now[:16]))
rowsha = {r[0]: hashlib.sha256(('%s\t%s\t%s' % (r[0], r[4].strip(), r[5].strip())).encode('utf-8')).hexdigest() for r in rows if len(r) == 7}
m3 = re.search(r"C7_ROW_SHA = \{(.*?)\}", s, re.S)
pairs = dict(re.findall(r"'(\d+)': '([0-9a-f]{64})'", m3.group(1)))
ck('终态 C7_ROW_SHA 条目 31', len(pairs) == 31, len(pairs))
ck('终态 C7_ROW_SHA 与现算逐键全等', [k for k in rowsha if pairs.get(k) != rowsha[k]] == [],
   [k for k in rowsha if pairs.get(k) != rowsha[k]])

# 跑门禁
print('\n[跑门禁]')
r = subprocess.run([sys.executable, 'check_disc.py'], cwd=D, capture_output=True, text=True, timeout=600)
ck('门禁 exit 0', r.returncode == 0, r.returncode)
for ln in r.stdout.split('\n'):
    if re.search(r'C7 |C7b|C7d|C10 |C11 frozen|C12|C15 |C16 |C16d|BOUNDARY', ln):
        print('   | ' + ln[:190])
bad = [l for l in r.stdout.split('\n') if re.match(r'^\s*(FAIL|\[FAIL\])', l)]
ck('门禁无 FAIL 行（行首锚定，不用 in 判断 —— S-413）', bad == [], bad[:3])
ck('门禁打印 C10 self-check: ok(R156)', 'C10 self-check: ok(R156)' in r.stdout,
   [l for l in r.stdout.split('\n') if 'C10 self-check' in l][:2])
ck('门禁 C16 报 unpinned 0', re.search(r'unpinned 0', r.stdout) is not None,
   [l for l in r.stdout.split('\n') if 'C16 per-section' in l][:1])

print('\n=== FAIL %d ===' % len(fail))
for f in fail: print('  ! ' + f)
sys.exit(0 if not fail else 1)
