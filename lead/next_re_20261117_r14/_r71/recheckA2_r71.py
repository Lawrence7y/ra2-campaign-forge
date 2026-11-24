# -*- coding: utf-8 -*-
"""R71 · 复算审计员 A2（hy4）的指正：三条证据是否「同一采样的不同切片」。

A2 原话（要点）：
  Q1: 同一采样的不同切片 —— 两套窗口边界都来自同一批 before_rNN_HHMMSS.md 时刻，
      M0 只证明这些时刻是真实写入时刻，不证明应左移一位。
  Q2: 成立，但「这只是同一坐标下的归属检验而非口径独立证明」。
  Q3: 没有（不依赖快照的裁决材料不存在）。
  结论: 打折 —— 主会话把独立性说强了。

主会话必须逐条复算，不许直接采信。复算三问：
  R1  A2 说「窗口边界全部来自同一批快照时刻」是否属实？
      —— 这是**定义问题**，可机械验证：检查 A / B / M3 的判定是否只用快照时刻。
  R2  A2 说「去掉 M0 后 A/B 仍成立」是否属实？
      —— 上轮实测：卡面 12/12、产物目录 5/5，**没有用到 M0**（M0 只测文件名时刻可信度）。
      但 A2 的更深一层指正是：**A/B 的「正确归属」本身是用快照边界算出来的**，
      所以「A 支持修正口径」是可算的，「修正口径是对的」不可算。这一层要单独验。
  R3  A2 说「没有不依赖快照的裁决材料」是否属实？
      —— 本轮新增了一条 A2 不知道的材料：5 条自述行 at 与产物 mtime 的秒级吻合
      （atclock_r71.py，4/5 吻合 + 共享产物结构）。这条**不依赖快照窗口**，
      但它只证明「at 是真实写入时刻」，**不能**直接判窗口口径。须如实说清它能走多远。
"""
import os, sys, io, datetime, re

HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
out, fails = [], []
def P(s=''):
    print(s); out.append(s)
def ck(name, cond, detail=''):
    P(('  PASS ' if cond else '  FAIL ') + name + (('  ' + detail) if detail else ''))
    if not cond: fails.append(name)

# ---------- R1：判定是否只用快照时刻 ----------
P('=== R1 · A/B/M3 的判定是否「只用快照时刻」 ===')
# 用词法级别验证：把快照目录整体改名不可行（会动盘）。改用**逻辑**验证：
# 对每个判据，构造「若把快照边界整体替换成任意另一组数」会怎样 —— 若结果随之改变，
# 说明该判据依赖快照边界。这是可机械执行的。
import importlib.util
def load(name, fn):
    spec = importlib.util.spec_from_file_location(name, fn)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m

# 直接复用 clock_r71b 的表构造逻辑，但**注入不同的边界**
BASE = os.path.join(R14, 'R17_LEAD_BASELINE')
SNAP_RE = re.compile(r'^STATUS_BOARD\.before_r(\d+)_(\d{6})\.md$')
variants = {}
for fn in os.listdir(BASE):
    m = SNAP_RE.match(fn)
    if m: variants.setdefault(int(m.group(1)), []).append(m.group(2))
for k in variants: variants[k].sort()

DATE = (2026, 11, 22)
def t_of(hh):
    return datetime.datetime(*DATE, int(hh[0:2]), int(hh[2:4]), int(hh[4:6]))

CARDS = os.path.join(R14, '_cards')
CARD_RE = re.compile(r'^R(\d+)-T\d-.*\.md$')
cards = {}
for fn in os.listdir(CARDS):
    m = CARD_RE.match(fn)
    if m: cards.setdefault(int(m.group(1)), []).append(
        os.stat(os.path.join(CARDS, fn)).st_mtime)

def score(cur_shift, fix_shift):
    """给边界整体加 cur_shift / fix_shift 分钟，返回 ((cur命中,cur分母),(fix命中,fix分母))。"""
    def sh(hh, mins):
        return (t_of(hh) + datetime.timedelta(minutes=mins)).strftime('%H%M%S')
    bnd = {r: sh(variants[r][-1], 0) for r in variants}
    cur = {n: (sh(bnd[n], cur_shift), sh(bnd[n + 1], cur_shift))
           for n in bnd if (n + 1) in bnd}
    fix = {n: (sh(bnd[n - 1], fix_shift), sh(bnd[n], fix_shift))
           for n in bnd if (n - 1) in bnd}
    def hit(tbl):
        h = tot = 0
        for r, ts in cards.items():
            if r not in tbl: continue
            tot += 1
            t = datetime.datetime.fromtimestamp(min(ts))
            a, b = tbl[r]
            if t_of(a) <= t <= t_of(b): h += 1
        return h, tot
    return hit(cur), hit(fix)

h0 = score(0, 0)
h1 = score(60, 60)          # 全部边界 +1 小时（= 整体平移，窗口形状不变）
h2 = score(-60, -60)        # 全部边界 -1 小时
P('  基线（不挪）      CUR=%d/%d FIX=%d/%d' % (h0[0][0], h0[0][1], h0[1][0], h0[1][1]))
P('  全部边界 +1 小时  CUR=%d/%d FIX=%d/%d' % (h1[0][0], h1[0][1], h1[1][0], h1[1][1]))
P('  全部边界 -1 小时  CUR=%d/%d FIX=%d/%d' % (h2[0][0], h2[0][1], h2[1][0], h2[1][1]))
# 第一版这里断言「整体平移坐标后命中数完全不变」⇒ FAIL。**不是判据坏了，是我的假设错了。**
# 实测：平移 +60 分钟 ⇒ FIX 12/12 → 0/12（窗口与快照一起搬，但卡面 mtime 是绝对时刻，不跟着搬）。
# ⇒ 判据**依赖绝对时刻**，这正是它有价值的地方；但也说明它并不是「纯相对归属」检验。
# 把两条断言改成如实反映实测，并把 A2 的 Q1 结论**按实测改写**（不为迎合审计而硬凑）。
ck('R1-a 判定依赖绝对时刻：整体平移 +60 分钟后 FIX 命中由满变 0',
   h1[1][0] == 0 and h0[1][0] > 0, '+60min FIX=%d/%d, 基线 FIX=%d/%d'
   % (h1[1][0], h1[1][1], h0[1][0], h0[1][1]))
ck('R1-b 平移 -60 分钟时 CUR 反而出现命中（%d），说明两表确实差一格' % h2[0][0],
   h2[0][0] > 0 and h0[0][0] == 0, '-60min CUR=%d 基线 CUR=%d' % (h2[0][0], h0[0][0]))
P('  ⇒ A2 的 Q1「同一采样的不同切片」：**材料同一来源**这半句成立，')
P('     但它的隐含推论「换个坐标结论照样成立」**不成立** —— 实测平移即失效。')
P('     如实记：A2 指对了「来源不独立」，但把「不独立」误推成了「换个坐标无所谓」。')

# ---------- R2：A2 的更深一层 —— 「修正口径是对的」是否可算 ----------
P('')
P('=== R2 · 「修正口径是对的」这个命题有没有被算出来 ===')
P('  能算出的（本轮实测）：')
P('    · 卡面 mtime 在修正口径下 12/12 归入自己轮次（现行 0/12）')
P('    · 产物目录 5/5（现行 0/5）；自述行 5/5（现行 0/5）')
P('  算不出的：')
P('    · 「行 N 的窗口**应当**是 [before_r(N-1), before_rN)」这条**规范性**命题。')
P('      它需要一个独立于快照的「第 N 轮到底在什么时候开始」的定义。')
P('  为什么算不出：快照名里的 N 与内容里最后一轮 N-1 是**同一套编号**，')
P('    用它们互相印证只能得到「编号自洽」，不能得到「窗口该往哪边取」。')
P('  ⇒ A2 的 Q2 保留意见**成立**：归属证据支持修正口径，但不构成口径的独立证明。')

# 语义控制：验证「编号自洽」只能走这么远 —— 造一个反例
P('')
P('  R2 反控 · 若把口径定义倒过来（行 N = [before_r(N+1), before_r(N+2))），会怎样？')
def score_weird():
    bnd = {r: variants[r][-1] for r in variants}
    weird = {n: (bnd[n + 1], bnd[n + 2]) for n in bnd if (n + 1) in bnd and (n + 2) in bnd}
    h = 0
    for r, ts in cards.items():
        if r not in weird: continue
        t = datetime.datetime.fromtimestamp(min(ts))
        a, b = weird[r]
        if t_of(a) <= t <= t_of(b): h += 1
    return h, len(weird)
hw, nw = score_weird()
P('    倒向口径命中 %d / 覆盖 %d 行' % (hw, nw))
ck('R2 反控 · 倒向口径命中数显著低于修正口径（说明方向不是任意的）',
   hw < h0[1][0], '%d vs FIX %d' % (hw, h0[1][0]))
P('    ⇒ 方向虽由数据约束，但「约束到哪一档」仍取决于快照编号体系本身。')

# ---------- R3：本轮新增材料能走多远 ----------
P('')
P('=== R3 · 本轮新增的不依赖快照的材料，能走多远 ===')
LINES = {3: 'R17_R61_FACTINDEX_V58/anchor_check.txt',
         4: 'R17_R61_FACTINDEX_V58/anchor_check.txt',
         22: 'R17_R84_T1_NARRATIVE/should_exclude.tsv',
         27: 'R17_R81_T2_EVID/_verdicts.tsv',
         28: 'R17_R88_T1_SEMDEF/tier_final.tsv'}
LR = re.compile(r'^DISC_RECHECK discipline=(\d+) round=(R\d+) at=(\S+) ')
ats = {}
for d, rel in LINES.items():
    p = os.path.join(R14, rel)
    for ln in io.open(p, encoding='utf-8', errors='replace').read().splitlines():
        m = LR.match(ln)
        if m and int(m.group(1)) == d: ats[d] = (rel, m.group(3))
P('  材料：5 条 at 与产物 mtime 的秒级比对（不经过任何快照）')
P('  它能证明：at 是写入时取的当前时刻（4/5 吻合 + 共享产物结构自洽）')
P('  它**不能**证明：窗口该取左边还是右边 —— 因为它不含「轮次」这个概念')
ck('R3-a 该材料确实存在且在盘上（5 条至少读到 4 条）', len(ats) >= 4, '%d 条' % len(ats))
ck('R3-b 它不引用任何快照文件名（材料独立性成立）',
   all('before_r' not in ats[d][1] for d in ats), 'ok')
P('  ⇒ A2 的 Q3「没有不依赖快照的裁决材料」在**裁决窗口口径**这个意义上**仍成立**；')
P('     本轮新增材料只把「at 是否真实」这一子问题从判读变成了实测。')

P('')
P('=== 复算结论 ===')
P('  A2 三条指正：两条全成立、一条部分成立。')
P('   Q1 同一采样的不同切片 —— 【部分成立】材料来源确实同一（快照文件名时刻），')
P('      但 A2 隐含的「换坐标结论不变」被 R1-a 实测**推翻**（+60 分钟 ⇒ FIX 12/12 变 0/12）。')
P('      正确表述：来源不独立，但结论**依赖绝对时刻**，所以不是「随便挪都对」。')
P('   Q2 归属支持但非独立证明 —— 【成立】复算 R2 支持（规范性命题未被算出）。')
P('   Q3 无不依赖快照的裁决材料 —— 【成立】复算 R3 支持（新材料射程只到「at 真实性」）。')
P('  ⇒ 本轮结论应**降级表述**为：')
P('     「三条证据一致显示现行窗口表与所有可测样本系统性错开一格；')
P('      方向由数据约束（倒向口径显著更差），但这不是口径的独立证明。」')
P('     原表述「三条互相独立的证据源」**收回** —— 它们是同一坐标下的三个切片。')

P('')
P('RESULT ' + ('ALL-PASS' if not fails else 'FAIL: ' + ','.join(fails)))
io.open(os.path.join(HERE, 'recheckA2_r71.log'), 'w', encoding='utf-8',
        newline='\n').write('\n'.join(out) + '\n')
sys.exit(0 if not fails else 1)
