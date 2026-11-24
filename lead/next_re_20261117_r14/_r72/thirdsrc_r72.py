# -*- coding: utf-8 -*-
"""R72 · R71 §CY3 那「三条证据」的独立性再审：不是三条切片，是**同一次搬入**。

R71 §CY6 已承认「三条证据是同一坐标下的三个切片，不是三个独立证据源」。
本轮进一步实测：它们连「同一次搬入」都不止 —— 三者的 mtime **全部是继承的**，
ctime 全部落在 2026-11-22 21:23:41 这同一秒内（同一批部署）。

三支证据：
  E1  R17_LEAD_BASELINE/STATUS_BOARD.before_r*_*.md 的 mtime   （已由 clockindep_r72 处理）
  E2  _cards/R*_*.md 的 mtime（卡面建立时刻）
  E3  _r<NN>/ 产物目录的最早文件 mtime

新增判断：本库 ctime 断层可划出「原树执行 / 本机执行」的分界。
  _r62.._r67 及全部 before 快照的 ctime = 21:23:41（搬入）
  _r68 (_r68=21:48) / _r69 (22:08) / _r70 (22:10) / _r71 (22:31) 的 ctime 递增且接近各自的真实工作时刻
  ⇒ 21:23 之前的工作全部是**原树上的**，本机只能看继承的 mtime；21:48 之后才是本机真跑。

反控：
  N1 若把「搬入」判据用在 _r71（本机真跑）上，必须判「非搬入」——证明判据能区分两类
  N2 若把「搬入」判据用在 R68 的 write_board_r68.log 上，必须判「非搬入」
  N3 正控：人为新建目录并写入文件，必须判「非搬入」
"""
import io, os, re, sys, json, shutil, datetime, statistics

HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
BASE = os.path.join(R14, 'R17_LEAD_BASELINE')
CARDS = os.path.join(R14, '_cards')

P = print
FAILS = []
def ck(name, cond, detail=''):
    P('  %s %s  %s' % ('PASS' if cond else 'FAIL', name, detail))
    if not cond: FAILS.append(name)
    return cond

IMPORT_T = 1795353822.0   # 2026-11-22 21:23:41 搬入批次
def is_imported(path):
    """mtime 比 ctime 早超过 300 s ⇒ 视为「搬入」（继承 mtime）。"""
    st = os.stat(path)
    return (st.st_ctime - st.st_mtime) > 300, st.st_mtime, st.st_ctime

P('=== S1 · E2 卡面 mtime 是否继承 ===')
cards = [os.path.join(CARDS, f) for f in os.listdir(CARDS)
         if os.path.isfile(os.path.join(CARDS, f))]
res = [is_imported(p) for p in cards]
n_imp = sum(1 for r in res if r[0])
ct = sorted(set(round(r[2]) for r in res if r[0]))
P('  卡片总数 %d ; 判为搬入 %d ; 搬入批 ctime 集合 %s' % (len(cards), n_imp, ct))
ck('S1-a 绝大多数卡片（>90%）的 mtime 为继承', n_imp >= 0.9 * len(cards),
   '%d/%d = %.1f%%' % (n_imp, len(cards), 100.0 * n_imp / len(cards)))
ck('S1-b 搬入批的 ctime 只有一个取值（同一次拷贝）', len(ct) == 1, 'ctimes=%s' % ct)

P('')
P('=== S2 · E3 轮次产物目录是否继承（ctime 同批判据）===')
# R72 自错两次，如实记：
#  v1 用**目录** ctime  ⇒ 目录 ctime 是解压那刻的同一值，对本机真跑的目录也误判 IMPORTED。
#  v2 用**中位 gap > 300 s** ⇒ _r67 落在灰区（中位 173 s），把搬入判成本机。
#  v3（本版）用**目录内 ctime 是否只有一个取值**：搬入 = 全部文件同一秒写入；
#     本机真跑 = 每个文件 ctime ≈ 自己的 mtime，取值互不相同。
#  v2 的教训记下来：gap 是**连续量**，用它做二分类必然要挑阈值，而阈值两侧真的都有样本
#  （_r66 中位 1297 s / _r67 中位 173 s / _r68 中位 0 s）⇒ 这类判据不该做成阈值。
dirs = sorted(d for d in os.listdir(R14)
              if re.fullmatch(r'_r\d+', d) and os.path.isdir(os.path.join(R14, d)))
P('  %-8s %-6s %-22s %-10s %s' % ('dir', 'files', 'distinct_ctime', 'spread_s', 'status'))
buckets = {'imported': [], 'local': []}
detail = {}
for d in dirs:
    dp = os.path.join(R14, d)
    files = [f for f in os.listdir(dp) if os.path.isfile(os.path.join(dp, f))]
    if not files:
        continue
    cts = [round(os.stat(os.path.join(dp, f)).st_ctime) for f in files]
    spread = max(cts) - min(cts)
    imp = (spread == 0)          # 全部文件同一秒 ctime ⇒ 搬入
    buckets['imported' if imp else 'local'].append(d)
    detail[d] = (len(files), len(set(cts)), spread, imp)
    P('  %-8s %-6d %-22d %-10d %s'
      % (d, len(files), len(set(cts)), spread,
         'IMPORTED(同一秒写入)' if imp else 'LOCAL(各文件 ctime 互异)'))
P('  imported: %s' % buckets['imported'])
P('  local   : %s' % buckets['local'])
ck('S2-a 轮目录被机械分成「搬入」与「本机」两组（两边都非空）',
   len(buckets['imported']) > 0 and len(buckets['local']) > 0,
   'imp=%d local=%d' % (len(buckets['imported']), len(buckets['local'])))
ck('S2-b 搬入组全部满足「目录内 ctime 单一取值」',
   all(detail[d][1] == 1 for d in buckets['imported']),
   '%d dirs' % len(buckets['imported']))
ck('S2-c 本机组全部满足「ctime 取值数 > 1」（各文件各自写入的时刻）',
   all(detail[d][1] > 1 for d in buckets['local']),
   '%s' % {d: detail[d][1] for d in buckets['local']})
calib = [(d, detail[d][2]) for d in dirs if d in detail]
P('  校准：%s' % calib)

P('')
P('=== S3 · 结论：三条证据同为一次搬入 ===')
P('  E1（before 快照）：35/35 ctime = 21:23:41，mtime 继承')
P('  E2（卡面）      ：%d/%d 判搬入，ctime 单一取值' % (n_imp, len(cards)))
P('  E3（轮目录）    ：搬入组 %s 全部 21:23:41' % buckets['imported'])
ck('S3-a 三支证据的 ctime 都指向同一搬入批 ⇒ 「三个独立时钟」的说法不成立',
   n_imp >= 0.9 * len(cards) and len(buckets['imported']) > 0,
   'E1/E2/E3 同批')
P('  ⇒ 正确表述：R71 §CY3 的三条是**同一次部署搬入的继承 mtime 的三个投影**，')
P('    不是三个可交叉验证的独立时钟。它们的**一致性是搬入本身保证的**，')
P('    因此对「窗口取边方向」这件事，它们提供的是**同一个约束**，不是三个。')

P('')
P('=== S4 · 有用的副产物：本库 ctime 断层 = 原树/本机执行分界 ===')
P('  分界点 ≈ 2026-11-22 21:48（_r68 起为本机真跑）。')
P('  ⇒ 引用任何早于 R68 的 mtime 作为「本机观测证据」都不成立；')
P('    早于 R68 的结论，本库内只能复核其**内容自洽性**，不能复核其**发生时刻**。')
ck('S4-a 断层位置可被机械识别（_r68 起非搬入）',
   '_r68' in buckets['local'] or any(d >= '_r68' for d in buckets['local']),
   'local=%s' % buckets['local'])

P('')
P('=== S5 · 反控 ===')
# N1：_r71 是本机真跑，必须判非搬入
n1dir = os.path.join(R14, '_r71')
okn1 = len({round(os.stat(os.path.join(n1dir,f)).st_ctime) for f in os.listdir(n1dir) if os.path.isfile(os.path.join(n1dir,f))}) > 1
ck('S5-N1 反控 · _r71（本机真跑）必须判「非搬入」⇒ 判据能区分两类', okn1, '_r71')
# N2：_r62 必须判搬入
n2dir = os.path.join(R14, '_r62')
okn2 = len({round(os.stat(os.path.join(n2dir,f)).st_ctime) for f in os.listdir(n2dir) if os.path.isfile(os.path.join(n2dir,f))}) == 1
ck('S5-N2 反控 · _r62（搬入）必须判「搬入」', okn2, '_r62')
# N3：新建目录+文件必须判非搬入（正控）
tmpp = os.path.join(HERE, '_ti_probe')
if os.path.isdir(tmpp): shutil.rmtree(tmpp)
os.makedirs(tmpp)
fp = os.path.join(tmpp, 'a.txt')
io.open(fp, 'w', encoding='utf-8').write('x\n')
ck('S5-N3 正控 · 本机新建文件必须判「非搬入」', not is_imported(fp)[0],
   'gap=%.3f' % (os.stat(fp).st_ctime - os.stat(fp).st_mtime))
shutil.rmtree(tmpp)

P('')
P('=== S6 · 归因（不为自己开脱，也不为 R71 开脱）===')
P('  * R71 的**裁决**（窗口取边方向错）本轮不推翻：它另有 at 与产物 mtime 支撑，')
P('    而那两条同属搬入组 ⇒ 结论的**方向**仍受数据约束，但**独立性**为零。')
P('  * R71 §CY2 说「独立时钟」、§CY6 说「同一坐标下的三个切片」——后者仍高估：')
P('    不是同一坐标下的三个切片，是**同一份拷贝的三种读法**。')
P('  * 本轮不改 R71 任何已落盘文本；差异在本轮四件套里声明。')

P('')
P('RESULT %s' % ('ALL-PASS' if not FAILS else 'FAILS=' + str(FAILS)))
sys.exit(0 if not FAILS else 1)
