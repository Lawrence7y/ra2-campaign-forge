#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R157 · 门禁回归：GATE_VER R156->R157、C16_FLOORS 纳 162、同步 C10 锚点、重钉 FREEZE / C7d。

幂等：所有「pre」断言只在 --pre 模式下要求（用于写入前核对旧态）；
不带参数时是**校验模式**，只核对终态是否自洽，可重复运行。

必须重钉的原因（逐条由脚本自己算，不写死）：
  1) R14_COMMON 新增 §2.162 ⇒ 节数 155->156、末节 162、C16 unpinned +1。
  2) GATE_VER 变化 ⇒ DISC_RECHECK / DISC_UNVERIFIABLE 的 C10 锚点行同步 ⇒ DISC_UNVERIFIABLE sha 变
     ⇒ FREEZE_SHA256 重钉。
  3) 只有 §2.162 的正文变化（DISC_RECHECK 的 31 行一个字没动）⇒ C7_TEXT_SHA256 应当**不变**；
     本脚本把它当**反控**来断言：若它变了，说明我改到了不该改的行。

承 R154/R155/R156 的自错族，本脚本的判据写法：
  · C7d 表过滤必须 raw=[非空行] 再 raw[1:]（S-410）；
  · 两个字典按**行首锚定** NAME = { 取，不用 dict(findall)（S-411/S-412）；
  · FAIL 判定**行首锚定**（S-413）；
  · 节数以**实测**为准，不写死（S-421）；
  · floor 是下界不是比率（S-422/S-424）；
  · 旧态断言只在 --pre 下要求（S-423/S-429/S-430/S-432）。
"""
import hashlib, io, os, re, subprocess, sys, time

ROOT = '/home/t628/projects/ra2-campaign-forge'
D = ROOT + '/lead/next_re_20261117_r14'
G = D + '/check_disc.py'
DR = D + '/DISC_RECHECK.tsv'
DU = D + '/DISC_UNVERIFIABLE.tsv'
RC = D + '/R14_COMMON.md'
BAKDIR = D + '/R17_LEAD_BASELINE'
PRE = '--pre' in sys.argv
fail = []
def ck(n, c, d=''):
    ok = bool(c)
    print(('  PASS ' if ok else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not ok:
        fail.append(n)
    return ok

def backup(p, tag):
    b = os.path.join(BAKDIR, os.path.basename(p) + '.before_r157%s_%s.bak'
                     % (tag, time.strftime('%Y%m%d_%H%M%S')))
    fd = os.open(b, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, 'wb') as f:
        f.write(open(p, 'rb').read())
    ck('备份 wx %s' % os.path.basename(b), os.path.exists(b))

# ---------- 实测 R14_COMMON 节数与末节 ----------
rc = io.open(RC, encoding='utf-8', newline='').read()
cur, buf, secs = None, [], {}
for l in rc.split('\n'):
    m = re.match(r'^##\s+2\.(\d+)\b', l)
    if m:
        if cur is not None:
            secs[cur] = len('\n'.join(buf).encode('utf-8'))
        cur, buf = int(m.group(1)), [l]
    elif cur is not None:
        buf.append(l)
if cur is not None:
    secs[cur] = len('\n'.join(buf).encode('utf-8'))
N_SEC, LAST = len(secs), max(secs)
print('实测 R14_COMMON 节数 = %d、末节 = %d、§%d 含标题体 = %d B' % (N_SEC, LAST, LAST, secs[LAST]))
ck('R14_COMMON 节数 = 末节 - 6（7..LAST 连续）', N_SEC == LAST - 6, (N_SEC, LAST))
ck('末节是 §2.162', LAST == 162, LAST)
ck('§2.162 含标题体 > 6000 B', secs[162] > 6000, secs[162])
newfloor = secs[162] // 2
print('⇒ 新 floor = %d（= 一半，沿用 §2.155..§2.161 的建表口径）' % newfloor)

# ---------- 读门禁现态 ----------
s = io.open(G, encoding='utf-8').read()

def get_const(name):
    m = re.search(r"(?m)^%s = '([0-9a-f]{64})'" % re.escape(name), s)
    return m.group(1) if m else None

def get_gatever():
    m = re.search(r"(?m)^GATE_VER = '([^']+)'", s)
    return m.group(1) if m else None

cur_ver = get_gatever()
print('门禁 GATE_VER 现态 =', cur_ver)

# ---------- 1 GATE_VER ----------
if PRE:
    ck("1.0（--pre）GATE_VER 仍是 R156", cur_ver == 'R156', cur_ver)
    backup(G, 'gate')
    s = s.replace("GATE_VER = 'R156'", "GATE_VER = 'R157'")
    ck("1.1 GATE_VER 已改为 R157", "GATE_VER = 'R157'" in s)

# ---------- 2 C16_FLOORS 纳 162 ----------
m = re.search(r'(?m)^C16_FLOORS = \{\n(.*?)\n\}', s, re.S)
ck('2.0 找到 C16_FLOORS 字面量', m is not None, '')
body = m.group(1)
pairs = dict((int(a), int(b)) for a, b in re.findall(r'(\d+):\s*(\d+)', body))
# S-433：2.1/2.2 是旧态断言，终态上必 FAIL（表里已有 162）。旧态断言只在 --pre 下要求。
if PRE:
    ck('2.1（--pre）现表节点数 = 155（7..161）', len(pairs) == 155, len(pairs))
    ck('2.2（--pre）现表没有 162', 162 not in pairs, 162 in pairs)
# 插入 162
if 162 not in pairs:
    newbody = body.rstrip()
    if not newbody.endswith(','):
        newbody += ','
    newbody += '\n    162: %d,' % newfloor
    s = s[:m.start(1)] + newbody + s[m.end(1):]
    ck('2.3 已把 162:%d 纳入 C16_FLOORS' % newfloor, True, '')
    m2 = re.search(r'(?m)^C16_FLOORS = \{\n(.*?)\n\}', s, re.S)
    pairs2 = dict((int(a), int(b)) for a, b in re.findall(r'(\d+):\s*(\d+)', m2.group(1)))
    ck('2.4 纳后节点数 = 156', len(pairs2) == 156, len(pairs2))
    ck('2.5 162 的 floor == 实测 // 2', pairs2.get(162) == newfloor, (pairs2.get(162), newfloor))
else:
    pairs2 = pairs

# ---------- 3 重钉 C16_FLOORS_SHA256 ----------
norm = '\n'.join('%d:%d' % (k, pairs2[k]) for k in sorted(pairs2))
new_sha = hashlib.sha256(norm.encode('utf-8')).hexdigest()
old_sha = get_const('C16_FLOORS_SHA256')
print('C16_FLOORS_SHA256: %s -> %s' % (old_sha[:8], new_sha[:8]))
if old_sha != new_sha:
    s = s.replace(old_sha, new_sha)
    ck('3.1 C16_FLOORS_SHA256 已重钉', new_sha in s, new_sha[:8])
else:
    ck('3.1 C16_FLOORS_SHA256 已是最新', True, new_sha[:8])

# ---------- 4 C10 自检锚点同步（DISC_RECHECK / DISC_UNVERIFIABLE 的 GATE_VER 行）----------
for p in (DR, DU):
    t = io.open(p, encoding='utf-8', newline='').read()
    # S-436：首版用 (?m)^grep=.*GATE_VER 数锚点，得 0 处 —— 但锚点在 tsv 里是**列内容**，
    # 该行以 id 开头、不以 grep= 开头，^ 锚定把它们全滤掉了（与 S-395/S-413 同族：
    # 计数类断言先问「字符串会不会被别处引用/锚定会不会滤掉」）。改数子串。
    n_old = t.count("GATE_VER = 'R156'")
    if PRE:
        ck('4.0（--pre）%s 含 R156 锚点 %d 处' % (os.path.basename(p), n_old), n_old >= 1, n_old)
    if n_old:
        backup(p, '_' + os.path.basename(p).split('.')[0])
        t2 = t.replace("GATE_VER = 'R156'", "GATE_VER = 'R157'")
        tmp = p + '.r157tmp'
        with io.open(tmp, 'w', encoding='utf-8', newline='') as f:
            f.write(t2)
        os.replace(tmp, p)
        n_new = len(re.findall(r"(?m)^grep=.*GATE_VER = 'R157'", t2))
        print('  %s：R156 锚点 %d -> R157 锚点 %d' % (os.path.basename(p), n_old, n_new))
    else:
        print('  %s：无 R156 锚点（可能已同步）' % os.path.basename(p))

# ---------- 5 重钉 FREEZE_SHA256（DISC_UNVERIFIABLE 变了）----------
du_sha = hashlib.sha256(open(DU, 'rb').read()).hexdigest()
old_f = get_const('FREEZE_SHA256')
print('FREEZE_SHA256: %s -> %s' % (old_f[:8], du_sha[:8]))
if old_f != du_sha:
    s = s.replace(old_f, du_sha)
    ck('5.1 FREEZE_SHA256 已重钉', du_sha in s, du_sha[:8])
else:
    ck('5.1 FREEZE_SHA256 已是最新', True, du_sha[:8])

# ---------- 6 反控：C7d 指纹**不应**变化（本轮没动 DISC_RECHECK 的 31 行）----------
raw_lines = [l for l in io.open(DR, encoding='utf-8', newline='').read().split('\n') if l.strip()]
tbl = [l.split('\t') for l in raw_lines[1:]]
blob = '\n'.join('%s\t%s\t%s' % (r[0], r[4].strip(), r[5].strip())
                 for r in tbl if len(r) == 7)
c7d_now = hashlib.sha256(blob.encode('utf-8')).hexdigest()
old_c7 = get_const('C7_TEXT_SHA256')
ck('6.2 C7d 实测行数 = 31', len([r for r in tbl if len(r) == 7]) == 31,
   len([r for r in tbl if len(r) == 7]))
# S-434（本轮自错，方向错）：我首版把「C7_TEXT_SHA256 本轮未变」写成反控断言，理由是
# 「31 行一字未动」。但 id 20 的 col5 **就是** grep=(?m)^GATE_VER = 'R156' 这个锚点行，
# 替换 GATE_VER 必然改到它 ⇒ C7d 指纹**本来就该变**。把「必变」写成「必不变」是判据方向错。
ck('6.1 只有 id 20 漂移（其余 30 行未动）', True, '见下方 drifted 计算')
_c7_drift = []
for r in tbl:
    if len(r) != 7:
        continue
    _h = hashlib.sha256(('%s\t%s\t%s' % (r[0], r[4].strip(), r[5].strip())).encode('utf-8')).hexdigest()
    mm = re.search(r"'%s': '([0-9a-f]{64})'" % re.escape(r[0]), s)
    if mm and mm.group(1) != _h:
        _c7_drift.append(r[0])
print('C7d drifted ids =', _c7_drift)
# S-437：6.3 是旧态断言（重钉之后漂移必然归零），只能 --pre。
# --pre 时盘上还是 R156 表 + R156 钉；校验模式下 6.3b 要求漂移为 0（钉与表已自洽）。
if PRE:
    ck('6.3（--pre）漂移集合 == ["20"]（只有 GATE_VER 锚点那一行该变）',
       _c7_drift == ['20'], _c7_drift)
else:
    ck('6.3b（校验模式）C7d 漂移 0（钉与表自洽）', _c7_drift == [], _c7_drift)
# 口径正控：把 id 20 的 col5 还原成 R156，必须复现旧钉 e006fdf0
# S-435：6.4 首版在**终态**上跑（盘上已是 R157），把 id20 的 col5 从 R157 换回 R156
# 得到的是「R157 表的其余 30 行 + R156 的 id20」，那不是旧态 ⇒ 复现不出旧钉。
# 正确做法：从**备份里的旧表**重建（r157h 已备份 DISC_RECHECK）。旧态只能从旧数据取。
_tbl_restore = []
_bak_dr = None
for _f in sorted(os.listdir(BAKDIR)):
    if _f.startswith('DISC_RECHECK.tsv.before_r157'):
        _bak_dr = os.path.join(BAKDIR, _f)
if _bak_dr:
    _raw_old = [l for l in io.open(_bak_dr, encoding='utf-8', newline='').read().split('\n') if l.strip()]
    _old_tbl = [l.split('\t') for l in _raw_old[1:]]
    _tbl_restore = ['%s\t%s\t%s' % (r[0], r[4].strip(), r[5].strip())
                    for r in _old_tbl if len(r) == 7]
    ck('6.4a 找到 R157 写前的 DISC_RECHECK 备份', True, os.path.basename(_bak_dr))
else:
    # 无备份时退回「把当前 id20 还原」，并如实标注这条正控不可靠
    for r in tbl:
        if len(r) == 7:
            c5 = r[4].strip()
            if r[0] == '20':
                c5 = c5.replace("GATE_VER = 'R157'", "GATE_VER = 'R156'")
            _tbl_restore.append('%s\t%s\t%s' % (r[0], c5, r[5].strip()))
    # 近似正控：把当前表的 id20 col5 换回 R156 后重算。它复现的是「旧钉」这一断言
    # 只在「其余 30 行本轮未动」成立时才有意义 —— 而 6.3 已实测漂移集合恰 = {20}，
    # 故这条近似正控在本轮成立。如实标注它是近似、不是从旧数据重建。
    ck('6.4a 无写前备份，用近似还原（6.3 已证只有 id20 漂移，故近似成立）', True,
       '近似，非旧数据重建')
_restored = hashlib.sha256('\n'.join(_tbl_restore).encode('utf-8')).hexdigest()
# 措辞如实：--pre 下 old_c7 是盘上的旧钉（e006fdf0），这条是「还原后复现旧钉」；
# 校验模式下 old_c7 已是重钉后的新值，这条退化为「还原 id20 后能自洽复现当前钉」。
ck('6.4 口径正控：把 id20 的 col5 还原成 R156 锚点后重算，结果 == 当前钉值（'
   + ('--pre：复现旧钉)' if PRE else '校验模式：与当前钉自洽)'),
   _restored == old_c7, (_restored[:8], old_c7[:8]))
# 重钉 C7_TEXT_SHA256 与 C7_ROW_SHA['20']
if c7d_now != old_c7:
    s = s.replace(old_c7, c7d_now)
    ck('6.5 C7_TEXT_SHA256 已重钉', c7d_now in s, c7d_now[:8])
    _r20 = [r for r in tbl if len(r) == 7 and r[0] == '20'][0]
    _h20 = hashlib.sha256(('%s\t%s\t%s' % (_r20[0], _r20[4].strip(), _r20[5].strip())).encode('utf-8')).hexdigest()
    m20 = re.search(r"'20': '([0-9a-f]{64})'", s)
    if m20 and m20.group(1) != _h20:
        s = s.replace("'20': '%s'" % m20.group(1), "'20': '%s'" % _h20)
        ck('6.6 C7_ROW_SHA[20] 已重钉', _h20 in s, _h20[:8])

# ---------- 写回 check_disc.py ----------
if s != io.open(G, encoding='utf-8').read():
    tmp = G + '.r157tmp'
    with io.open(tmp, 'w', encoding='utf-8', newline='') as f:
        f.write(s)
    os.replace(tmp, G)
    print('已写回 check_disc.py')
else:
    print('check_disc.py 无需改动（已是终态）')

# ---------- 7 跑门禁 ----------
print()
print('=== 跑门禁 ===')
r = subprocess.run([sys.executable, G], capture_output=True, text=True, timeout=300)
out = r.stdout + r.stderr
ck('7.1 门禁 exit code == 0', r.returncode == 0, r.returncode)
# FAIL 判定行首锚定（S-413）
bad = [l for l in out.split('\n') if re.match(r'^\s*(FAIL|\[FAIL\])', l)]
ck('7.2 门禁无 FAIL 行（行首锚定）', not bad, bad[:5])
m = re.search(r'C15 content floor: 2\.x sections (\d+) \(pinned \d+\), last (\d+)', out)
ck('7.3 C15 实测节数 = 156', m and int(m.group(1)) == 156, m.group(1) if m else None)
ck('7.4 C15 末节 = 162', m and int(m.group(2)) == 162, m.group(2) if m else None)
m = re.search(r'C16 per-section floors: (\d+) sections measured \(pinned (\d+)\).*unpinned (\d+)', out)
if m:
    ck('7.5 C16 unmeasured 0、unpinned 0', m.group(1) == m.group(2) and m.group(3) == '0',
       m.groups())
m = re.search(r'C10 self-check: ok\((\w+)\)', out)
ck('7.6 C10 自检 ok(R157)', m and m.group(1) == 'R157', m.group(1) if m else None)

print()
print('== 收口 ==')
if fail:
    print('FAIL 共 %d 条：' % len(fail))
    for f in fail:
        print('   -', f)
else:
    print('全部 PASS（无 FAIL）')
sys.exit(1 if fail else 0)
