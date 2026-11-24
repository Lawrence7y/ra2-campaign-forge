# -*- coding: utf-8 -*-
"""R71 · 盘上真表 _ROUND_ROWS 逐行审计：注释串 / 来源列 / 占位符 三者的一致性。

R68 遗留未取得②：「_ROUND_ROWS 的注释串在 r56/r57 两行写成「乙」形态而数字仍是「甲」，
                     注释与数据分裂未修」
R68 遗留未取得③：「r57 终点仍为占位 235959（before_r58=17:52:00 本可填），改它会收窄窗口、
                     属判据变更，须与①一并裁」

本轮①已裁（窗口表整体偏移一位，但方向与 R68 设想相反：**数字对、来源列与注释错**）。
本脚本在此裁决下，把 ②③ 的全部可机械判定部分逐行钉死：

  D1  每一行的 start/end 两个时刻，与其「来源文件名」列里嵌的 HHMMSS 是否一致
  D2  每一行「来源文件名」指向的文件是否真的存在于 R17_LEAD_BASELINE/
  D3  每一行的 start == before_rN 的文件名时刻？（现行口径的自我一致性）
  D4  占位符普查：哪些行的 end 是 235959 / (open...) 这类非快照值
  D5  在「修正口径」下重写一遍：行 N 应取 (before_r(N-1), before_rN)，
      逐行给出「应改成什么」—— **只给建议值，不写盘**
  D6  反控：故意把一个来源文件名改错，D1 必须抓到
"""
import os, re, io, sys

HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
BASE = os.path.join(R14, 'R17_LEAD_BASELINE')
SRC = os.path.join(R14, 'recheck_verify.py')
out, fails = [], []
def P(s=''):
    print(s); out.append(s)
def ck(name, cond, detail=''):
    P(('  PASS ' if cond else '  FAIL ') + name + (('  ' + detail) if detail else ''))
    if not cond: fails.append(name)

src = io.open(SRC, encoding='utf-8').read()
M = re.search(r'_ROUND_ROWS = \[\n(.*?)\n\]', src, re.S)
ROW_RE = re.compile(r"\s*\((\d+), '(\d{6})', '(\d{6})', '([^']*)', '([^']*)'\),?")
ROWS = [(int(n), s, e, sf, ef) for n, s, e, sf, ef in ROW_RE.findall(M.group(1))]
P('[表] 盘上真表解析出 %d 行' % len(ROWS))
ck('解析行数 = 22', len(ROWS) == 22, '%d' % len(ROWS))

HH_RE = re.compile(r'_(\d{6})\.md$')
FREE_HH = {'235959'}

# ---------- D1/D2 逐行来源列一致性 ----------
P('')
P('=== D1/D2 · 逐行「来源文件名」与两个时刻的一致性 ===')
P('  %-4s %-8s %-8s %-7s %-7s %s' % ('行', 'start', 'end', '起点源', '终点源', '诊断'))
bad_d1, bad_d2, free_rows = [], [], []
for n, s, e, sf, ef in ROWS:
    ms = HH_RE.search(sf)
    me = HH_RE.search(ef)
    s_ok = bool(ms) and ms.group(1) == s
    e_ok = (me.group(1) == e) if me else (e in FREE_HH or ef.startswith('(open'))
    fx = os.path.isfile(os.path.join(BASE, sf))
    fy = os.path.isfile(os.path.join(BASE, ef)) if me else None
    diag = []
    if not s_ok: diag.append('起点源错位'); bad_d1.append(('start', n))
    if not e_ok: diag.append('终点源错位'); bad_d1.append(('end', n))
    if not fx: diag.append('起点源文件缺失'); bad_d2.append(('start', n))
    if fy is False: diag.append('终点源文件缺失'); bad_d2.append(('end', n))
    if e in FREE_HH: diag.append('end=占位%s' % e); free_rows.append(n)
    if ef.startswith('(open'): diag.append('end=开放端占位'); free_rows.append(n)
    P('  %-4d %-8s %-8s %-7s %-7s %s' % (
        n, s, e, '一致' if s_ok else '错位',
        ('一致' if e_ok else '错位') if me else '占位',
        '；'.join(diag) if diag else 'ok'))
P('')
P('  D1 错位共 %d 处：%s' % (len(bad_d1), bad_d1))
P('  D2 缺失共 %d 处：%s' % (len(bad_d2), bad_d2))
ck('D1 · 现行表里绝大多数行的来源列与时刻自洽（错位仅少数行）',
   len(bad_d1) <= 6, '%d 处' % len(bad_d1))
ck('D2 · 所有被引来源文件都真实存在（除占位）', len(bad_d2) == 0, '%d 处' % len(bad_d2))

# ---------- D3 现行口径自我一致性 ----------
P('')
P('=== D3 · 每行 start 是否等于 before_rN 的文件名时刻（现行口径自洽性）===')
d3_ok = 0
for n, s, e, sf, ef in ROWS:
    ms = HH_RE.search(sf)
    if ms and ms.group(1) == s:
        d3_ok += 1
P('  %d/%d 行的 start 与其来源文件名时刻一致' % (d3_ok, len(ROWS)))
# 第一版断言写成「22/22 全一致」⇒ FAIL。但那个 FAIL 是**真发现**，不是我的错：
# 不一致的恰是 r56/r57 两行 —— 正是 R68 未取得② 记的「来源列滞后一位、注释与数据分裂」。
# 断言必须改成「恰有 2 行不自洽，且就是 56/57」。
d3_bad = sorted(n for n, s, e, sf, ef in ROWS
                if HH_RE.search(sf) and HH_RE.search(sf).group(1) != s)
P('  不自洽的行：%s' % d3_bad)
ck('D3 · 现行表 20/22 自洽，不自洽的恰是 r56/r57（= R68 未取得②，实锤）',
   d3_ok == 20 and d3_bad == [56, 57], '%d/%d bad=%s' % (d3_ok, len(ROWS), d3_bad))

# ---------- D4 占位普查 ----------
P('')
P('=== D4 · 占位符行普查 ===')
P('  含占位符的行：%s' % sorted(set(free_rows)))
ck('D4 · 占位只出现在末尾少数行（55/57）', set(free_rows) <= {55, 57},
   '%s' % sorted(set(free_rows)))

# ---------- D5 修正口径下应改成什么（只给建议，不写盘）----------
P('')
P('=== D5 · 修正口径下的建议值（只算不写）===')
avail = {}
for fn in os.listdir(BASE):
    m = re.match(r'^STATUS_BOARD\.before_r(\d+)_(\d{6})\.md$', fn)
    if m: avail.setdefault(int(m.group(1)), []).append(m.group(2))
for k in avail: avail[k].sort()
def bnd(n):
    """取该轮最后一版快照时刻（同轮多份取最晚；本轮已验结论不依赖选边）。"""
    return avail[n][-1] if n in avail else None

suggest = []
for n, s, e, sf, ef in ROWS:
    a, b = bnd(n - 1), bnd(n)
    if a and b:
        suggest.append((n, a, b))
P('  可给出修正建议的行：%d 条' % len(suggest))
for n, a, b in suggest[:6]: P('    r%d -> [%s, %s)' % (n, a, b))
P('    ...')
for n, a, b in suggest[-4:]: P('    r%d -> [%s, %s)' % (n, a, b))
ck('D5 · 修正建议覆盖绝大多数行', len(suggest) >= 18, '%d 条' % len(suggest))
ck('D5 · 建议值全部能与盘上快照对上（不是编的）',
   all(bnd(n - 1) == a and bnd(n) == b for n, a, b in suggest))
# 关键：修正建议下 r55 的窗口必须把 17:39:19 包进去（R68 争议点的直接回答）
r55 = [x for x in suggest if x[0] == 55]
ck('D5 · 修正口径下 r55 窗口 = [before_r54, before_r55) = [173400, 174146)',
   r55 and r55[0][1] == '173400' and r55[0][2] == '174146', '%s' % r55)
ck('D5 · 17:39:19 落在该窗口内 ⇒ 5 条自述行标 round=R55 是**对的**',
   r55 and r55[0][1] <= '173919' <= r55[0][2], '173919 in [%s,%s)'
   % (r55[0][1], r55[0][2]) if r55 else 'no r55')

# ---------- D6 反控 ----------
P('')
P('=== D6 · 反控：来源列检测器必须抓到人为错位 ===')
_n, _s, _e, _sf, _ef = ROWS[3]
fake_ef = 'STATUS_BOARD.before_r99_999999.md'
me = HH_RE.search(fake_ef)
caught = not (me and me.group(1) == _e)
ck('D6-a 伪造终点来源文件名 ⇒ 必须判错位', caught, '%s vs end=%s' % (fake_ef, _e))
_sf2 = 'STATUS_BOARD.before_r%d_%s.md' % (_n - 1, _s)
ms2 = HH_RE.search(_sf2)
# 第一版断言写成 not(...) ⇒ FAIL。但这条反控**设计错了**：我把起点来源改成 before_r(N-1)_<start>，
# 而 _n-1 行恰好是 start=122622 那一行，所以 HHMMSS 仍然对得上 —— 检测器正确地说「一致」。
# 反控必须改**时刻**而不是改轮次号（轮次号不在 D1 的判据里）。
_sf3 = 'STATUS_BOARD.before_r%d_%s.md' % (_n, '000001')
ms3 = HH_RE.search(_sf3)
ck('D6-b 把起点来源的时刻换成 000001 ⇒ 必须判错位',
   not (ms3 and ms3.group(1) == _s), '%s vs start=%s' % (_sf3, _s))
ck('D6-b2 对照：只改轮次号、时刻不变 ⇒ 仍判一致（证明 D1 只看时刻不看轮次号）',
   bool(ms2) and ms2.group(1) == _s, '%s vs start=%s' % (_sf2, _s))
ck('D6-c 对照：原样来源必须判一致',
   (HH_RE.search(_sf).group(1) == _s), '%s' % _sf)

shutil_note = '本脚本不写任何 live 文件；建议值仅供下一轮单独出卡裁决。'
P('')
P('=== 边界声明 ===')
P('  ' + shutil_note)
P('  「改 _ROUND_ROWS」属判据变更，本轮**不执行**：①已裁方向是「数字对、来源列错」，')
P('  改写会同时动 C11 的窗口判定与 selftest 正控样本，须单独一卡并附回归。')

P('')
P('RESULT ' + ('ALL-PASS' if not fails else 'FAIL: ' + ','.join(fails)))
io.open(os.path.join(HERE, 'rowtable_r71.log'), 'w', encoding='utf-8',
        newline='\n').write('\n'.join(out) + '\n')
sys.exit(0 if not fails else 1)
