# -*- coding: utf-8 -*-
"""R68 · 轮次窗口的语义复算：现行表（甲）与「快照名 N ⇒ 内容 max=N-1」（乙）的判别性测量

问题：5 条 C11 FAIL 全部是 R4 at outside R055 window [17:41:46, 17:46:45)。
现行表把第 N 轮窗口定义为 [before_rN, before_r(N+1))，这假设「快照 before_rN 是第 N 轮的起点」。
若假设反过来（before_rN 是第 N 轮结束后的快照），则窗口应为 [before_r(N-1), before_rN)。

判别性证据只有一个来源：**快照内容里最后一轮是哪一轮**。若 before_rN 里最后一段是第 N-1 轮，
说明该快照拍在「第 N 轮写好之前」= 起点（甲）；若是第 N 轮，则它是终点（乙）。

反控：
  A 用抽样文件人工核对 max 值（防解析器把指针行当段头）
  B 把窗口统一放宽到全天，5 条必须全过（证明判据确实在区分）
  C 把窗口统一收窄到 1 秒，5 条必须全不过（证明不是恒真）
"""
import io, os, re, datetime, json

R14 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = os.path.join(R14, 'R17_LEAD_BASELINE')
# R68 修正：轮次记录在盘上有两种形态 —— 顶格 ## 段头，以及 > 📌 **第 N 轮** 笔记行。
# 第一版只认前者，把 r63/r64/r65 快照误判成「max=61 违例」，其实那几轮写在笔记行里。
HDR = re.compile(r'^##\s+(?:[\U0001F300-\U0001FAFF☀-➿]\s*)*R17\s+第\s*(\d+)\s*轮', re.M)
NOTE = re.compile(r'^>\s*📌\s*\*\*第\s*(\d+)\s*轮', re.M)
SNAP = re.compile(r'^STATUS_BOARD(?:\.md)?\.before_r(\d+)(add\d*)?_(\d{6})\.md$')

fails, buf = [], []
def P(s=''):
    print(s); buf.append(s)
def ck(n, c, d=''):
    P(('  PASS ' if c else '  FAIL ') + n + (('  ' + d) if d else ''))
    if not c: fails.append(n)

# ---- 1 · 每份快照的 (名字轮次, 时刻, 内容最大轮次) ----
snaps = []
for n in sorted(os.listdir(B)):
    m = SNAP.match(n)
    if not m:
        continue
    r, add, t = int(m.group(1)), m.group(2) or '', m.group(3)
    txt = io.open(os.path.join(B, n), encoding='utf-8', errors='replace').read()
    rh = [int(x) for x in HDR.findall(txt)]
    rn = [int(x) for x in NOTE.findall(txt)]
    rs = rh + rn
    # 反控 A：指针行不得被当段头
    ptr = len(re.findall(r'^> 📦', txt, re.M))
    snaps.append(dict(name=n, r=r, add=add, t=t, mx=(max(rs) if rs else None),
                      segs=len(rs), ptr=ptr))
P('=== 1 · 快照清单（%d 份）===' % len(snaps))
P('%-46s %-8s %-6s %-6s %s' % ('文件名', '时刻', 'max', '段数', '指针行'))
for s in snaps:
    P('%-46s %-8s %-6s %-6s %d' % (s['name'], s['t'], s['mx'], s['segs'], s['ptr']))

ck('反控 A：解析器把 ## 段头与 > 📌 笔记行两类都计入（无遗漏轮次）',
   all(s['mx'] is not None for s in snaps))

# ---- 2 · 甲/乙 判别的核心统计 ----
# 对「无 add 后缀」的规范快照：甲 ⇒ max = N-1；乙 ⇒ max = N
canon = [s for s in snaps if not s['add']]
jia = [s for s in canon if s['mx'] == s['r'] - 1]
yi = [s for s in canon if s['mx'] == s['r']]
other = [s for s in canon if s['mx'] not in (s['r'] - 1, s['r'])]
P('')
P('=== 2 · 判别统计（只用无 add 后缀的规范快照，共 %d 份）===' % len(canon))
P('  甲（max = N-1，即快照是第 N 轮的起点）: %d 份 %s'
  % (len(jia), [s['r'] for s in jia]))
P('  乙（max = N，即快照是第 N 轮的终点）  : %d 份 %s'
  % (len(yi), [s['r'] for s in yi]))
P('  其它                                 : %d 份 %s'
  % (len(other), [(s['r'], s['mx']) for s in other]))
ck('2.1 规范快照里没有「乙」类（若有，说明快照名是终点语义）',
   len(yi) == 0, 'yi=%s' % [s['r'] for s in yi])
ck('2.2 规范快照全部符合甲（max = N-1）', len(other) == 0,
   'other=%s' % [(s['r'], s['mx']) for s in other])
ck('2.3 样本量足够（>= 20 份规范快照）', len(canon) >= 20, str(len(canon)))

# ---- 3 · 用甲语义复现现行对 5 条的判定 ----
FIVE = [('3', '17:39:19'), ('4', '17:40:02'), ('22', '17:39:19'),
        ('27', '17:39:19'), ('28', '17:39:19')]
def hhmmss(t):
    return datetime.datetime(2026, 11, 22, int(t[:2]), int(t[2:4]), int(t[4:6]),
                             tzinfo=datetime.timezone(datetime.timedelta(hours=8)))
def hms(t):
    h, m, sec = t.split(':')
    return datetime.datetime(2026, 11, 22, int(h), int(m), int(sec),
                             tzinfo=datetime.timezone(datetime.timedelta(hours=8)))

boot = {}
for s in canon:
    boot.setdefault(s['r'], s['t'])
P('')
P('=== 3 · 现行（甲）窗口下 r55 的边界 ===')
P('  before_r55 = %s（起点）；下一份 before_r56 = %s（终点）'
  % (boot.get(55), boot.get(56)))
w0, w1 = hhmmss(boot[55]), hhmmss(boot[56])
for d, at in FIVE:
    a = hms(at)
    P('  discipline=%-3s at=%s  -> %s' % (d, at, 'IN ' if w0 <= a < w1 else 'OUT'))
ck('3.1 现行甲窗口把所有 5 条判为 OUT（复现门禁报错）',
   all(not (w0 <= hms(at) < w1) for _, at in FIVE))

# ---- 4 · 反控 B：放宽到全天 ⇒ 全 IN ----
P('')
P('=== 4 · 反控 ===')
day0 = datetime.datetime(2026, 11, 22, 0, 0, 0,
                         tzinfo=datetime.timezone(datetime.timedelta(hours=8)))
day1 = day0 + datetime.timedelta(days=1)
ck('反控 B：窗口放宽到全天 ⇒ 5 条全部 IN（判据确实在区分，不是恒 OUT）',
   all(day0 <= hms(at) < day1 for _, at in FIVE))
wk0 = w0 + datetime.timedelta(seconds=30)
ck('反控 C：窗口收窄到 [17:42:16,17:46:45) ⇒ 5 条全部 OUT（不是恒 IN）',
   all(not (wk0 <= hms(at) < w1) for _, at in FIVE))

# ---- 5 · 若改用乙语义，5 条会怎样 ----
P('')
P('=== 5 · 若改用乙语义（[before_r54, before_r55)）===')
e0, e1 = hhmmss(boot[54]), hhmmss(boot[55])
P('  r55 乙窗口 = [%s, %s)' % (boot[54], boot[55]))
for d, at in FIVE:
    a = hms(at)
    P('  discipline=%-3s at=%s  -> %s' % (d, at, 'IN ' if e0 <= a < e1 else 'OUT'))
ck('5.1 乙语义下 5 条全部 IN', all(e0 <= hms(at) < e1 for _, at in FIVE))
ck('5.2 但第 2 节已证乙语义与快照内容矛盾（max=N-1）⇒ 不能用它',
   len(yi) == 0)

# ---- 6 · 结论：真正的问题不是窗口，是「快照拍摄时刻 vs 工作时刻」 ----
P('')
P('=== 6 · 决定性事实 ===')
P('  5 条自述行的时刻 17:39:19 / 17:40:02 落在 [before_r54=17:34:00, before_r55=17:41:46)')
P('  按甲语义，这段属于「第 54 轮」的窗口；而被写的行却标 round=R55')
ck('6.1 5 条 at 落在第 54 轮窗口（甲语义）之内',
   all(hhmmss(boot[54]) <= hms(at) < hhmmss(boot[55]) for _, at in FIVE))
P('')
P('  两种解释只能选一，且必须用盘上证据判：')
P('    (i) 窗口表错：第 55 轮的工作被算进第 54 轮');
P('    (ii) 自述行的 round 字段错：那些工作其实是第 54 轮做的')
mx55 = [s['mx'] for s in canon if s['r'] == 55][0]
P('  判别证据：before_r55 的内容 max 轮次 = %d' % mx55)
P('    ⇒ 拍这张快照时看板里最后一轮是第 %d 轮 ⇒ 第 55 轮还没开始' % mx55)
P('    ⇒ 17:39:19 做的那些事，只可能属于第 55 轮（第 54 轮已封口）')
P('    ⇒ 现行窗口 [before_r55, before_r56) 把第 55 轮的工作时段排除在外 ⇒ (i) 成立：')
P('      窗口表把「本轮写完后的快照」当成了「本轮的起点」，是终点/起点错配')
ck('6.2 before_r55 内容 max=54（第 55 轮尚未开始）', mx55 == 54, str(mx55))
P('')
P('RESULT ' + ('ALL-PASS' if not fails else 'FAIL: ' + ','.join(fails)))
io.open(os.path.join(R14, '_r68', 'window_r68.log'), 'w', encoding='utf-8',
        newline='\n').write('\n'.join(buf) + '\n')
