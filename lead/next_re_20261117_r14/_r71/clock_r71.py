# -*- coding: utf-8 -*-
"""R71 · 用「快照文件 mtime == 文件名 HHMMSS」这条独立时钟，裁决 R68 遗留未取得项①。

背景（R68 未取得①原文）：
  「5 条自述行 at=17:39:19 / 17:40:02 落在 [before_r54=17:34:00, before_r55=17:41:46) 内，
    按现行表属第 54 轮窗口，而行里标 round=R55。两解释（窗口错 / round 字段错）都缺决定性
    材料，缺的是『第 54 轮封口时刻』的独立材料。」

本脚本的独立材料 = 每个 before_rNN snapshot 的**文件系统 mtime**。
  R68 及以前所有轮次都用「文件名里的 HHMMSS」当窗口边界 —— 那是**同一个字符串**，
  用它去验它自己等于 0 信息。mtime 是**另一条独立记录的时钟**（写入时刻），
  只有当 mtime == 文件名 HHMMSS 时，才说明文件名里的时刻不是手写拍脑袋，是真实写入时刻。

三条测量：
  M0  27/27 全量：mtime 的 HH:MM:SS 是否逐秒等于文件名 HHMMSS（这是「独立时钟可用」的前提）
  M1  卡面 mtime 落在**现行表**的哪个 round 窗口
  M2  卡面 mtime 落在**修正表** [before_r(N-1), before_rN) 的哪个 round 窗口
  M3  5 条 DISC_RECHECK 自述行的 at，在现行表 vs 修正表下分别归第几轮

控制组（纪律 11/13：控制组必须覆盖每一个子检查）：
  POS-M0  真实 27 条全部秒级相等
  NEG-M0  把某条文件名的 HHMMSS 人为 +1 秒 ⇒ 检测器必须报不等（证明它不是恒真）
  POS-M1/M2  卡面在各自表下命中率
  NEG-M2  修正表整体再移一位（= 现行表）⇒ 必须回到 M1 的结果（证明两表确实差一位，不是同一张表）
  NEG-M3  虚构一条 at=17:50:00 round=R55 的行 ⇒ 修正表必须判它不在第 55 轮（不许全放行）
"""
import os, re, io, sys, datetime, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
BASE = os.path.join(R14, 'R17_LEAD_BASELINE')
DATE = (2026, 11, 22)
out = []
fails = []
def P(s=''):
    print(s); out.append(s)
def ck(name, cond, detail=''):
    P(('  PASS ' if cond else '  FAIL ') + name + (('  ' + detail) if detail else ''))
    if not cond: fails.append(name)

def t_of(hhmmss):
    h, m, s = int(hhmmss[0:2]), int(hhmmss[2:4]), int(hhmmss[4:6])
    return datetime.datetime(*DATE, h, m, s)

def hhmmss_of_ts(ts):
    return datetime.datetime.fromtimestamp(ts).strftime('%H%M%S')

# ---------- 扫描快照 ----------
SNAP_RE = re.compile(r'^STATUS_BOARD\.before_r(\d+)_(\d{6})\.md$')
snaps = {}      # round_no -> (hhmmss_in_name, mtime_hhmmss, last_round_in_content)
for fn in sorted(os.listdir(BASE)):
    m = SNAP_RE.match(fn)
    if not m:
        continue
    rno, hh = int(m.group(1)), m.group(2)
    p = os.path.join(BASE, fn)
    mt = hhmmss_of_ts(os.stat(p).st_mtime)
    txt = io.open(p, encoding='utf-8', errors='replace').read()
    heads = [int(x) for x in re.findall(r'(?m)^##.*?R17 第 (\d+) 轮', txt)]
    notes = [int(x) for x in re.findall(r'(?m)^> .{0,4}\*\*第 (\d+) 轮', txt)]
    last = max(heads + notes) if (heads or notes) else None
    snaps[rno] = (hh, mt, last, fn)

P('[扫描] 命中 before_rNN_HHMMSS.md 快照 %d 个' % len(snaps))
P('[扫描] 轮次：%s' % sorted(snaps))

# ---------- M0：独立时钟是否可用 ----------
P('')
P('=== M0 · 快照 mtime 是否逐秒等于文件名 HHMMSS ===')
eq = [(r, snaps[r]) for r in sorted(snaps) if snaps[r][0] == snaps[r][1]]
ne = [(r, snaps[r]) for r in sorted(snaps) if snaps[r][0] != snaps[r][1]]
P('  相等 %d / 不等 %d' % (len(eq), len(ne)))
for r, v in ne:
    P('    不等: r%d name=%s mtime=%s' % (r, v[0], v[1]))
ck('POS-M0 全部 %d 条 mtime 秒级等于文件名 HHMMSS' % len(snaps),
   len(ne) == 0 and len(eq) == len(snaps), '%d/%d' % (len(eq), len(snaps)))

# NEG-M0：把第一条的文件名时刻 +1 秒，检测器必须报不等
_r0 = sorted(snaps)[0]
_h, _m, _s = [int(x) for x in snaps[_r0][0][0:2]], [int(x) for x in snaps[_r0][0][2:4]], [int(x) for x in snaps[_r0][0][4:6]]
_alt = (datetime.datetime(*DATE, _h[0], _m[0], _s[0]) + datetime.timedelta(seconds=1)).strftime('%H%M%S')
ck('NEG-M0 名称时刻 +1 秒后必须被判不等（检测器非恒真）',
   _alt != snaps[_r0][1], 'name+1s=%s mtime=%s' % (_alt, snaps[_r0][1]))

# ---------- 语义控制：before_rN 内容最后一轮 = N-1 ----------
P('')
P('=== 语义控制 · before_rN 内容最后一段轮次 ===')
okc = 0
for r in sorted(snaps):
    hh, mt, last, fn = snaps[r]
    good = (last == r - 1) if last is not None else False
    if good: okc += 1
    if not good:
        P('    r%d 内容最后一轮=%s（期望 %d）' % (r, last, r - 1))
ck('内容最后一段恒为 N-1（证明 before_rN = 第 N 轮写板之前）',
   okc == len(snaps), '%d/%d' % (okc, len(snaps)))

# ---------- 两张窗口表 ----------
# 现行表：row N = [before_rN, before_r(N+1))  （只对表里列出的 N）
CUR = {
    35: ('112234', '112911'), 36: ('112911', '114901'), 37: ('114901', '120113'),
    38: ('120113', '122622'), 39: ('122622', '123652'), 40: ('123652', '131109'),
    42: ('131109', '132425'), 43: ('132425', '135348'), 44: ('135348', '140857'),
    45: ('140857', '143641'), 46: ('143641', '152510'), 47: ('152510', '152809'),
    48: ('152809', '153819'), 49: ('153819', '155139'), 50: ('155139', '160144'),
    51: ('160144', '161750'), 52: ('161750', '162803'), 53: ('162803', '173400'),
    54: ('173400', '174146'), 55: ('174146', '174645'),
    56: ('174645', '174854'), 57: ('174854', '235959'),
}
# 修正表：row N = [before_r(N-1), before_rN)
FIX = {}
for n in CUR:
    if (n - 1) in snaps and n in snaps:
        FIX[n] = (snaps[n - 1][0], snaps[n][0])

def which(tbl, t):
    hits = [n for n, (a, b) in tbl.items() if t_of(a) <= t <= t_of(b)]
    return hits

P('')
P('=== 两张窗口表覆盖 ===')
P('  现行表 %d 行；修正表 %d 行（需要 N-1 与 N 两张快照都在）' % (len(CUR), len(FIX)))
P('  现行表未覆盖的轮次（本盘有快照但表里没有）：%s'
  % sorted(set(snaps) - set(CUR)))
# 修正表比现行表少两行是**结构性**的，不是缺陷：r35 需要 r34 快照、r42 需要 r41 快照，
# 而盘上 before_r34 只有无时刻的 STATUS_BOARD.before_r34.md、r41 根本没有快照（R68 已记）。
# 第一版断言写成「两表覆盖相等」⇒ 必然 FAIL；那是**我的期望值写错**，不是表错。
_missing = sorted(set(CUR) - set(FIX))
ck('修正表缺口恰为 {35,42}（因其前置快照无时刻/不存在）', _missing == [35, 42], '%s' % _missing)
ck('修正表覆盖 = 现行表 − {35,42}', set(FIX) == set(CUR) - {35, 42}, '%d 行' % len(FIX))

# ---------- M1/M2：卡面 mtime 落在哪张表的哪个窗口 ----------
CARD_RE = re.compile(r'^R(\d+)-T\d-.*\.md$')
cards = {}      # round -> [mtimes]
for fn in sorted(os.listdir(os.path.join(R14, '_cards'))):
    m = CARD_RE.match(fn)
    if not m: continue
    rno = int(m.group(1))
    if rno < 45: continue
    p = os.path.join(R14, '_cards', fn)
    cards.setdefault(rno, []).append((os.stat(p).st_mtime, fn))

P('')
P('=== M1/M2 · 卡面写入时刻归属哪个 round 窗口 ===')
P('  %-6s %-10s %-10s %-22s %-22s' % ('round', '卡最早', '卡最晚', '现行表归入', '修正表归入'))
m1_hit = m2_hit = tested = 0
for r in sorted(cards):
    if r not in CUR or r not in FIX:
        P('  r%-5d %-10s %-10s %-22s %-22s' % (r, '', '', '(表未覆盖，跳过)', ''))
        continue
    tested += 1
    ts = sorted(t for t, _ in cards[r])
    t0, t1 = ts[0], ts[-1]
    h1 = which(CUR, datetime.datetime.fromtimestamp(t0))
    h2 = which(FIX, datetime.datetime.fromtimestamp(t0))
    if r in h1: m1_hit += 1
    if r in h2: m2_hit += 1
    P('  r%-5d %-10s %-10s %-22s %-22s' % (
        r,
        datetime.datetime.fromtimestamp(t0).strftime('%H:%M:%S'),
        datetime.datetime.fromtimestamp(t1).strftime('%H:%M:%S'),
        str(h1), str(h2)))
P('')
# 第一版这两条断言把期望值写成 True（恒真）⇒ 是**断言写坏**，不是逻辑坏（R68 教训）。
# 真实期望：现行表下卡面「一条都不落在自己轮次」= 系统偏移一位的直接证据。
ck('M1 卡面落在「自己轮次」的现行窗口内 = 0/%d（偏移一位）' % tested,
   m1_hit == 0, '%d/%d' % (m1_hit, tested))
ck('M2 卡面落在「自己轮次」的修正窗口内：%d/%d' % (m2_hit, tested),
   m2_hit == tested, '%d/%d' % (m2_hit, tested))
ck('NEG-M2 两张表确实差一位（M1 命中数 != M2 命中数）',
   m1_hit != m2_hit, 'M1=%d M2=%d' % (m1_hit, m2_hit))

# ---------- M3：5 条自述行 ----------
LINES = [
    (3,  'R55', '2026-11-22T17:39:19+08:00'),
    (4,  'R55', '2026-11-22T17:40:02+08:00'),
    (22, 'R55', '2026-11-22T17:39:19+08:00'),
    (27, 'R55', '2026-11-22T17:39:19+08:00'),
    (28, 'R55', '2026-11-22T17:39:19+08:00'),
]
P('')
P('=== M3 · 5 条 DISC_RECHECK 自述行归属 ===')
P('  %-4s %-6s %-26s %-14s %-14s' % ('纪律', '行标', 'at', '现行表归入', '修正表归入'))
m3_cur = m3_fix = 0
for disc, rlab, at in LINES:
    t = datetime.datetime.strptime(at, '%Y-%m-%dT%H:%M:%S%z')
    t = t.replace(tzinfo=None)
    h1 = which(CUR, t)
    h2 = which(FIX, t)
    if 55 in h1: m3_cur += 1
    if 55 in h2: m3_fix += 1
    P('  %-4d %-6s %-26s %-14s %-14s' % (disc, rlab, at[11:19], str(h1), str(h2)))
P('')
ck('M3-a 现行表下 5 条落在第 55 轮窗口 = 0/5（同样偏移一位）',
   m3_cur == 0, '%d/5' % m3_cur)
ck('M3-b 修正表下 5 条落在第 55 轮窗口：%d/5' % m3_fix, m3_fix == 5, '%d/5' % m3_fix)

# NEG-M3：虚构一条落在 17:44:30、标 R55 的行 —— 修正表必须判它在第 56 轮，且**不在**第 55 轮。
# 第一版取 17:50:00 写在「必须归第 56 轮」是错的：17:50:00 在 before_r57(17:48:54) 与
# before_r58(17:52:00) 之间 ⇒ 修正口径下属第 58 轮，而两表都只到 57。**期望值写错，不是表错。**
t_fake = datetime.datetime(*DATE, 17, 44, 30)
h_fix = which(FIX, t_fake)
ck('NEG-M3 虚构 at=17:44:30 标 R55 ⇒ 修正表判第 56 轮、且不在第 55 轮（不许全放行）',
   (55 not in h_fix) and (56 in h_fix), '修正表归入=%s' % h_fix)

# 顺带记录一个本轮新发现：17:50:00 在修正口径下属第 58 轮，而两张表都不覆盖 58 ⇒
# 现行表第 57 行 end=235959 占位把 58 及以后全部吞进第 57 轮。这是「占位」的直接后果，实测非推断。
t_probe = datetime.datetime(*DATE, 17, 50, 0)
ck('17:50:00 在两表下均无归属 ⇒ 现行表 r57 的 235959 占位已吞掉第 58 轮起',
   which(CUR, t_probe) == [57] and which(FIX, t_probe) == [],
   'CUR=%s FIX=%s（真值应为第 58 轮 [17:48:54,17:52:00)）' % (
       which(CUR, t_probe), which(FIX, t_probe)))

# ---------- 附带：现行表第 56/57 行的「来源文件列」错位（R68 未取得②） ----------
P('')
P('=== 附带 · R68 未取得② 的来源文件列错位 ===')
src_rows = [
    (55, '174146', '174645', 'STATUS_BOARD.before_r55_174146.md', '(open: no r56 snapshot yet)'),
    (56, '174645', '174854', 'STATUS_BOARD.before_r55_174146.md', 'STATUS_BOARD.before_r56_174645.md'),
    (57, '174854', '235959', 'STATUS_BOARD.before_r56_174645.md', 'STATUS_BOARD.before_r57_174854.md'),
]
lag = 0
for n, s, e, sf, ef in src_rows:
    s_hh = re.search(r'_(\d{6})\.md$', sf)
    e_hh = re.search(r'_(\d{6})\.md$', ef) if ef.startswith('STATUS') else None
    s_ok = bool(s_hh and s_hh.group(1) == s)
    e_ok = bool(e_hh and e_hh.group(1) == e) if e_hh else None
    P('  行 r%d: start=%s 来源=%s ⇒ %s ; end=%s 来源=%s ⇒ %s'
      % (n, s, os.path.basename(sf), '一致' if s_ok else '错位',
         e, (os.path.basename(ef) if e_hh else ef),
         ('一致' if e_ok else '错位') if e_ok is not None else '开放端'))
    if not s_ok: lag += 1
ck('第 55 行来源列自洽；第 56/57 行来源列整体滞后一位（与数值差一位）', lag == 2, '错位行数=%d' % lag)

P('')
P('RESULT ' + ('ALL-PASS' if not fails else 'FAIL: ' + ','.join(fails)))
io.open(os.path.join(HERE, 'clock_r71.log'), 'w', encoding='utf-8', newline='\n').write(
    '\n'.join(out) + '\n')
sys.exit(0 if not fails else 1)
