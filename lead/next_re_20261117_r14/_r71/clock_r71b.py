# -*- coding: utf-8 -*-
"""R71 · 主裁决脚本：现行轮次窗口表是否整体偏移一位。

R68 遗留未取得①原文：
  「5 条自述行 at=17:39:19 / 17:40:02 落在 [before_r54=17:34:00, before_r55=17:41:46) 内，
    按现行表属第 54 轮窗口，而行里标 round=R55。两解释（窗口错 / round 字段错）都缺
    决定性材料，缺的是『第 54 轮封口时刻』的独立材料。」

本脚本用**两条互相独立的证据源**裁决，两者都不参与「窗口表」的构造：

  证据源 A · 卡面写入时刻   _cards/R<NN>-T*-*.md 的 mtime（派发轮次的那一轮写卡）
  证据源 B · 轮次产物目录   _r<NN>/ 内所有文件的 mtime 跨度下界

  时钟独立性 = M0：每条 before_rNN_HHMMSS.md 的 **文件系统 mtime 逐秒等于文件名里的 HHMMSS**。
  若这条成立，则文件名里的时刻不是手写估值，是真实写入时刻 ⇒ 可以当外部时钟用。
  （R68 及以前把「文件名里的 HHMMSS」既当窗口边界又当验证依据，是自证循环。）

口径两条：
  现行口径 CUR:  row N 窗口 = [before_rN,    before_r(N+1))
  修正口径 FIX:  row N 窗口 = [before_r(N-1), before_rN   )

判定：若 CUR 下命中率接近 0 而 FIX 下接近满分，且差异在两个独立证据源上**同向**，
      则「窗口表整体偏移一位」，**不是**「round 字段错」—— 因为 round 字段与 FIX 自洽。
"""
import os, re, io, sys, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
BASE = os.path.join(R14, 'R17_LEAD_BASELINE')
CARDS = os.path.join(R14, '_cards')
DATE = (2026, 11, 22)
out, fails = [], []
def P(s=''):
    print(s); out.append(s)
def ck(name, cond, detail=''):
    P(('  PASS ' if cond else '  FAIL ') + name + (('  ' + detail) if detail else ''))
    if not cond: fails.append(name)

def t_of(hhmmss):
    return datetime.datetime(*DATE, int(hhmmss[0:2]), int(hhmmss[2:4]), int(hhmmss[4:6]))
def hms(ts):
    return datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')
def hhmmss_of(ts):
    return datetime.datetime.fromtimestamp(ts).strftime('%H%M%S')

# ---------- 收集快照，同轮多份时同时保留最早/最晚 ----------
SNAP_RE = re.compile(r'^STATUS_BOARD\.before_r(\d+)_(\d{6})\.md$')
variants = {}      # round -> sorted list of HHMMSS
for fn in sorted(os.listdir(BASE)):
    m = SNAP_RE.match(fn)
    if not m: continue
    variants.setdefault(int(m.group(1)), []).append(m.group(2))
for k in variants: variants[k].sort()

P('[收集] 带时刻的 before 快照：%d 个轮次' % len(variants))
dups = {k: v for k, v in variants.items() if len(v) > 1}
P('[收集] 同轮多份快照（须显式选边并做稳健性检验）：%s' % dups)

# ---------- M0 独立时钟 ----------
P('')
P('=== M0 · 独立性前提：快照 mtime 是否逐秒等于文件名 HHMMSS ===')
rows0, ne = [], []
for r in sorted(variants):
    for hh in variants[r]:
        p = os.path.join(BASE, 'STATUS_BOARD.before_r%d_%s.md' % (r, hh))
        mt = hhmmss_of(os.stat(p).st_mtime)
        rows0.append((r, hh, mt))
        if hh != mt: ne.append((r, hh, mt))
P('  总 %d 条；相等 %d；不等 %d' % (len(rows0), len(rows0) - len(ne), len(ne)))
for r, hh, mt in ne: P('    不等 r%d name=%s mtime=%s' % (r, hh, mt))
ck('POS-M0 mtime 逐秒等于文件名 HHMMSS（%d 条全中）' % len(rows0),
   len(ne) == 0 and len(rows0) >= 25, '%d/%d' % (len(rows0) - len(ne), len(rows0)))

# NEG-M0：检测器必须能报不等
_r, _hh = rows0[0][0], rows0[0][1]
_p = os.path.join(BASE, 'STATUS_BOARD.before_r%d_%s.md' % (_r, _hh))
_bump = (t_of(_hh) + datetime.timedelta(seconds=1)).strftime('%H%M%S')
ck('NEG-M0 名称时刻 +1 秒 ⇒ 必须判不等（非恒真）',
   _bump != hhmmss_of(os.stat(_p).st_mtime), 'r%d name+1s=%s vs mtime=%s'
   % (_r, _bump, hhmmss_of(os.stat(_p).st_mtime)))

# ---------- 语义控制 ----------
P('')
P('=== 语义控制 · before_rN 内容最后一段轮次必须 = N-1 ===')
okc, tot = 0, 0
for r in sorted(variants):
    hh = variants[r][-1]
    p = os.path.join(BASE, 'STATUS_BOARD.before_r%d_%s.md' % (r, hh))
    txt = io.open(p, encoding='utf-8', errors='replace').read()
    heads = [int(x) for x in re.findall(r'(?m)^##.*?R17 第 (\d+) 轮', txt)]
    notes = [int(x) for x in re.findall(r'(?m)^> .{0,4}\*\*第 (\d+) 轮', txt)]
    last = max(heads + notes) if (heads or notes) else None
    tot += 1
    if last == r - 1: okc += 1
    else: P('    r%d 内容最后一轮=%s（期望 %d）' % (r, last, r - 1))
ck('内容最后一段恒为 N-1 ⇒ before_rN 拍在第 N 轮写板之前', okc == tot, '%d/%d' % (okc, tot))

# ---------- 两张表（同轮多份默认取最晚；稳检再取最早） ----------
def build_tables(pick):
    """pick ∈ {'last','first'}：同轮多份快照取哪个。"""
    bnd = {r: variants[r][-1] if pick == 'last' else variants[r][0] for r in variants}
    cur, fix = {}, {}
    for n in bnd:
        if (n + 1) in bnd: cur[n] = (bnd[n], bnd[n + 1])
        if (n - 1) in bnd: fix[n] = (bnd[n - 1], bnd[n])
    return cur, fix

CUR, FIX = build_tables('last')
P('')
P('=== 两张窗口表 ===')
P('  现行口径 CUR %d 行；修正口径 FIX %d 行' % (len(CUR), len(FIX)))
P('  CUR 顶层（最早 5）：%s' % sorted(CUR)[:5])
P('  CUR 末层（最晚 5）：%s' % sorted(CUR)[-5:])
P('  FIX 顶层（最早 5）：%s' % sorted(FIX)[:5])
P('  FIX 末层（最晚 5）：%s' % sorted(FIX)[-5:])
ck('两表至少各覆盖 20 个轮次', len(CUR) >= 20 and len(FIX) >= 20,
   'CUR=%d FIX=%d' % (len(CUR), len(FIX)))
ck('两表行数相差 ≤ 2（只差端点，不是缺一大截）', abs(len(CUR) - len(FIX)) <= 2,
   '差值=%d' % (len(CUR) - len(FIX)))

def which(tbl, t):
    return [n for n, (a, b) in tbl.items() if t_of(a) <= t <= t_of(b)]

# ---------- 证据源 A：卡面 ----------
CARD_RE = re.compile(r'^R(\d+)-T\d-.*\.md$')
cards = {}
for fn in sorted(os.listdir(CARDS)):
    m = CARD_RE.match(fn)
    if not m: continue
    p = os.path.join(CARDS, fn)
    cards.setdefault(int(m.group(1)), []).append(os.stat(p).st_mtime)

P('')
P('=== 证据源 A · 卡面 mtime 归属 ===')
P('  %-5s %-9s %-9s %-8s %-8s' % ('round', '最早', '最晚', 'CUR归入', 'FIX归入'))
a_tot = a_cur = a_fix = 0
for r in sorted(cards):
    if r not in CUR and r not in FIX: continue
    t0, t1 = min(cards[r]), max(cards[r])
    h1 = which(CUR, datetime.datetime.fromtimestamp(t0))
    h2 = which(FIX, datetime.datetime.fromtimestamp(t0))
    if r in CUR: a_tot += 1
    if r in h1: a_cur += 1
    if r in h2: a_fix += 1
    P('  %-5d %-9s %-9s %-8s %-8s' % (r, hms(t0), hms(t1), str(h1), str(h2)))
P('')
ck('A · CUR 下卡面落在自己轮次 = 0/%d' % a_tot, a_cur == 0, '%d/%d' % (a_cur, a_tot))
ck('A · FIX 下卡面落在自己轮次 = %d/%d 满分' % (a_fix, a_tot), a_fix == a_tot,
   '%d/%d' % (a_fix, a_tot))
ck('A · 两表结果不同向（否则测不出偏移）', a_cur != a_fix, 'CUR=%d FIX=%d' % (a_cur, a_fix))

# ---------- 证据源 B：轮次产物目录 ----------
DIR_RE = re.compile(r'^_r(\d+)$')
P('')
P('=== 证据源 B · _rNN 产物目录最早文件 mtime 归属 ===')
P('  %-5s %-9s %-8s %-8s' % ('round', '最早文件', 'CUR归入', 'FIX归入'))
b_tot = b_cur = b_fix = 0
dirs = []
for d in sorted(os.listdir(R14)):
    m = DIR_RE.match(d)
    if m: dirs.append((int(m.group(1)), os.path.join(R14, d)))
for r, p in dirs:
    ts = []
    for rt, _ds, fs in os.walk(p):
        for f in fs:
            try: ts.append(os.stat(os.path.join(rt, f)).st_mtime)
            except OSError: pass
    if not ts: continue
    t0 = min(ts)
    h1 = which(CUR, datetime.datetime.fromtimestamp(t0))
    h2 = which(FIX, datetime.datetime.fromtimestamp(t0))
    usable = (r in CUR) or (r in FIX)
    # 第一版把 r38 记进 b_tot 却没记进 b_fix（它只被 FIX 覆盖、不被 CUR 覆盖）
    # ⇒ 得 5/4 这种越界比值。**计数器口径写错，不是表错**（R68 教训）。
    # 正确口径：分母 = 被**至少一张表**覆盖的轮次数；两侧分别计数。
    if usable: b_tot += 1
    if r in h1: b_cur += 1
    if r in h2: b_fix += 1
    P('  %-5d %-9s %-8s %-8s%s' % (r, hms(t0), str(h1), str(h2),
                                   '' if usable else '   (表未覆盖)'))
P('')
ck('B · CUR 下产物目录归入自己轮次 = 0/%d' % b_tot, b_cur == 0, '%d/%d' % (b_cur, b_tot))
ck('B · FIX 下产物目录归入自己轮次 = %d/%d 满分' % (b_fix, b_tot), b_fix == b_tot,
   '%d/%d' % (b_fix, b_tot))

# ---------- 稳健性：同轮多份改取最早，结论必须不变 ----------
CUR2, FIX2 = build_tables('first')
P('')
P('=== 稳健性 · 同轮多份快照改取「最早」 ===')
a_cur2 = a_fix2 = 0
for r in sorted(cards):
    t0 = min(cards[r])
    if r in which(CUR2, datetime.datetime.fromtimestamp(t0)): a_cur2 += 1
    if r in which(FIX2, datetime.datetime.fromtimestamp(t0)): a_fix2 += 1
P('  CUR(最早口径) 命中 %d；FIX(最早口径) 命中 %d（基准：%d / %d）'
  % (a_cur2, a_fix2, a_cur, a_fix))
ck('稳健性 · 换成取最早，FIX 仍满分且 CUR 仍 0（结论不依赖选边）',
   a_fix2 == a_fix and a_cur2 == a_cur, 'FIX %d→%d, CUR %d→%d'
   % (a_fix, a_fix2, a_cur, a_cur2))

# ---------- M3：5 条自述行 ----------
LINES = [
    (3, 'R55', '2026-11-22T17:39:19+08:00'),
    (4, 'R55', '2026-11-22T17:40:02+08:00'),
    (22, 'R55', '2026-11-22T17:39:19+08:00'),
    (27, 'R55', '2026-11-22T17:39:19+08:00'),
    (28, 'R55', '2026-11-22T17:39:19+08:00'),
]
P('')
P('=== M3 · 5 条 DISC_RECHECK 自述行（R68 争议点本体） ===')
P('  %-4s %-6s %-10s %-10s %-10s' % ('纪律', '行标', 'at', 'CUR归入', 'FIX归入'))
m_cur = m_fix = 0
for disc, rlab, at in LINES:
    t = datetime.datetime.strptime(at, '%Y-%m-%dT%H:%M:%S%z').replace(tzinfo=None)
    h1, h2 = which(CUR, t), which(FIX, t)
    if 55 in h1: m_cur += 1
    if 55 in h2: m_fix += 1
    P('  %-4d %-6s %-10s %-10s %-10s' % (disc, rlab, at[11:19], str(h1), str(h2)))
P('')
ck('M3 · CUR 下 5 条落在第 55 轮 = 0/5', m_cur == 0, '%d/5' % m_cur)
ck('M3 · FIX 下 5 条落在第 55 轮 = 5/5 ⇒ 行里的 round=R55 是**对的**', m_fix == 5,
   '%d/5' % m_fix)

# NEG-M3：虚构行必须被抓（不许全放行）
t_fake = datetime.datetime(*DATE, 17, 44, 30)
h_fake = which(FIX, t_fake)
ck('NEG-M3 虚构 at=17:44:30 标 R55 ⇒ FIX 判第 56 轮、不在第 55 轮',
   (55 not in h_fake) and (56 in h_fake), 'FIX=%s' % h_fake)

# ---------- 附带裁决：盘上真表 r57 的 235959 占位后果 ----------
# 注意：本脚本上面自建的 CUR 是由快照边界**连续**拼出的，不含占位符。
# 「235959 占位」只存在于盘上的 recheck_verify.py::_ROUND_ROWS。
# 第一版拿自建 CUR 去测占位 ⇒ 只测到 175200 一个点，那是**测错了对象**（不是表错）。
# 正确做法：直接把盘上真表 import 进来，用它判定。
P('')
P('=== 附带 · 盘上真表 _ROUND_ROWS 的 r57=235959 占位吞掉了哪些快照时点 ===')
sys.path.insert(0, R14)
import recheck_verify as RV
REAL = RV.ROUND_WINDOWS
P('  盘上真表覆盖 %d 个轮次：%s' % (len(REAL), sorted(REAL)))
def which_real(hh):
    """按 HHMMSS 字符串比较，避开真表 +08:00 aware 与本地 naive 的混比。"""
    return [n for n, v in REAL.items()
            if v[0].strftime('%H%M%S') <= hh <= v[1].strftime('%H%M%S')]
swallowed = []
for hh in ('175200', '180234', '182334', '182640', '183210', '183611', '183842', '184136'):
    h1 = which_real(hh)
    if h1 == [57]:
        swallowed.append((hh, which(FIX, t_of(hh))))
P('  被真表吞进 r57 的快照时点（HHMMSS → FIX 真值）：')
for hh, h2 in swallowed: P('    %s → FIX %s' % (hh, h2))
ck('真表 r57 的 235959 占位把 r58–r65 共 8 个快照时点全吞进 r57',
   len(swallowed) == 8, '%d 个' % len(swallowed))
ck('反控 · 这 8 个时点在 FIX 下都落回各自轮次（不是全都无处归属）',
   all(h2 and h2 != [57] for _, h2 in swallowed), '%s' % [h2 for _, h2 in swallowed])
ck('反控 · 真表对本脚本自建的 8 个时点归类与 FIX 不同（占位确有实际后果）',
   all([57] != h2 for _, h2 in swallowed), '占位归入全为 [57]')

P('')
P('RESULT ' + ('ALL-PASS' if not fails else 'FAIL: ' + ','.join(fails)))
io.open(os.path.join(HERE, 'clock_r71b.log'), 'w', encoding='utf-8', newline='\n').write(
    '\n'.join(out) + '\n')
sys.exit(0 if not fails else 1)
