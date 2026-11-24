# -*- coding: utf-8 -*-
"""R72 · 审计 R71 §CY2「mtime 是 71 轮来从未用过的独立时钟」这个定性。

R71 的结论是：before_rNN_HHMMSS.md 的 mtime 逐秒等于文件名 HHMMSS，35/35 全中，
不等 0 —— 据此把 mtime 当成「独立于快照内容与自述行的第三个时钟」，用它裁窗口取边方向。

本轮实测发现该定性**不成立或须大幅降级**：
  (1) 复现：mtime 秒 == 文件名秒，35/35。R71 的数值本身可复现。
  (2) 但 **ctime 全部 = 2026-11-22 21:23:41**（35/35 同一批），与 mtime 相差可达 10 小时。
      ⇒ 这 35 个快照是本机在 21:23 一次性拷入的，mtime 是**随复制继承**的，
        不是本机观测到的发生时刻。本库内**无法重新观测**该时刻。
  (3) 因此「独立时钟」的独立性只在**原树**上成立；在本精简库上，它与
      R70 查明的「部署裁剪」属同一族（材料是搬进来的，不是长出来的）。
  (4) 不过：亚秒部分 0/35 是毫秒对齐、分布均匀（stdev 0.25 s）⇒ 文件名是从
      一个**真实亚秒级 mtime 截断到秒**得来，不是反过来「把文件名写进 mtime」。
      ⇒ 时刻值本身是真的，被推翻的只是「本库内可独立复核」这一层。

反控（防恒真 / 防测错方向）：
  N1 人为把副本 mtime 设为整秒（touch -d 到 HH:MM:SS.000000000）
     ⇒ 亚秒对齐检测器必须判「毫秒对齐」（证明检测器不是恒报非对齐）
  N2 同一副本在拷入后 ctime != mtime ⇒ 本库的 ctime≠mtime 判据能识别「搬入」文件
  N3 正控：本脚本自己新写的文件 ctime ≈ mtime（差值 < 1 s），证明 N2 不是恒判不同
"""
import io, os, re, sys, json, shutil, subprocess, statistics, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
BASE = os.path.join(R14, 'R17_LEAD_BASELINE')

P = print
FAILS = []
def ck(name, cond, detail=''):
    P('  %s %s  %s' % ('PASS' if cond else 'FAIL', name, detail))
    if not cond: FAILS.append(name)
    return cond

SNAP = re.compile(r'^STATUS_BOARD\.before_r(\d+)_(\d{6})\.md$')
rows = []
for f in sorted(os.listdir(BASE)):
    m = SNAP.match(f)
    if m:
        st = os.stat(os.path.join(BASE, f))
        rows.append({'round': int(m.group(1)), 'hh': m.group(2), 'file': f,
                     'mtime': st.st_mtime, 'mtime_ns': st.st_mtime_ns,
                     'ctime': st.st_ctime})

P('=== S1 · 复现 R71 的 35/35 ===')
ok = 0
for r in rows:
    if datetime.datetime.fromtimestamp(r['mtime']).strftime('%H%M%S') == r['hh']:
        ok += 1
ck('S1-a mtime 秒 == 文件名秒（复现 R71）', ok == len(rows), '%d/%d' % (ok, len(rows)))

P('')
P('=== S2 · ctime：这 35 个文件是怎么进到本库的 ===')
cs = sorted(set(round(r['ctime']) for r in rows))
P('  ctime 取值集合（秒级）：%s' % cs)
spread = max(r['ctime'] for r in rows) - min(r['ctime'] for r in rows)
ck('S2-a 35 个快照的 ctime 全部落在同一秒内（同一批写入）', spread < 1.0,
   'spread=%.3f s' % spread)
gaps = [r['ctime'] - r['mtime'] for r in rows]
P('  ctime-mtime 间隔：min=%.0fs max=%.0fs median=%.0fs'
  % (min(gaps), max(gaps), statistics.median(gaps)))
ck('S2-b 全部 35 个文件的 ctime 都晚于 mtime（继承而非本机观测）',
   all(g > 1 for g in gaps), 'min_gap=%.3f s' % min(gaps))

P('')
P('=== S3 · 亚秒部分：文件名是从 mtime 截断，还是 mtime 从文件名写死 ===')
tails = [r['mtime_ns'] % 1_000_000_000 for r in rows]
ms_aligned = sum(1 for t in tails if t % 1_000_000 == 0)
stdev = statistics.pstdev(tails)
P('  亚秒 stdev = %.0f ns ; 毫秒对齐数 = %d/%d ; 秒对齐数 = %d/%d'
  % (stdev, ms_aligned, len(tails),
     sum(1 for t in tails if t % 1_000_000_000 == 0), len(tails)))
ck('S3-a 0 个毫秒对齐（若是把文件名写进 mtime，会全为整秒 ⇒ 恒对齐）',
   ms_aligned == 0, '%d aligned' % ms_aligned)
ck('S3-b 亚秒分布非退化（stdev > 1e6 ns）', stdev > 1e6, 'stdev=%.0f' % stdev)
P('  ⇒ 文件名 = 真实亚秒 mtime 截断到秒（方向是 mtime -> 文件名，不是反向）')

P('')
P('=== S4 · 反控 ===')
tmpd = os.path.join(HERE, '_ck_tmp')
if os.path.isdir(tmpd): shutil.rmtree(tmpd)
os.makedirs(tmpd)
src = os.path.join(BASE, rows[0]['file'])

# N1：人为把 mtime 设为整秒
n1 = os.path.join(tmpd, 'n1.md')
shutil.copy2(src, n1)
subprocess.check_call(['touch', '-d', '2026-11-22 11:22:34.000000000', n1])
t = os.stat(n1).st_mtime_ns % 1_000_000_000
ck('S4-N1 反控 · 把 mtime 设成整秒 ⇒ 毫秒对齐检测器必须判「已对齐」（非恒报非对齐）',
   t % 1_000_000 == 0, 'ns_tail=%d' % t)

# N2：拷入文件的 ctime != mtime
st = os.stat(n1)
ck('S4-N2 反控 · 本机拷入的文件 ctime != mtime（距 > 1 s）⇒ 「搬入」可被识别',
   abs(st.st_ctime - st.st_mtime) > 1, 'gap=%.1f s' % abs(st.st_ctime - st.st_mtime))

# N3：正控：本脚本此刻新写的文件 ctime ≈ mtime
n3 = os.path.join(tmpd, 'n3.md')
io.open(n3, 'w', encoding='utf-8').write('x\n')
st3 = os.stat(n3)
ck('S4-N3 正控 · 本机新写文件 ctime ≈ mtime（<1 s）⇒ N2 判据非恒判不同',
   abs(st3.st_ctime - st3.st_mtime) < 1.0, 'gap=%.4f s' % abs(st3.st_ctime - st3.st_mtime))

shutil.rmtree(tmpd)

P('')
P('=== S5 · 对 R71 §CY2 结论的处置（降级，不是推翻）===')
P('  * R71 的**数值**可复现（35/35），本轮不推翻。')
P('  * R71 的**定性**「独立时钟」须降级为：「原树上真实、本库内继承、不可本地重观测」。')
P('  * 与 R70 的 43 条缺失判定为「部署裁剪」同族：材料是搬进来的。')
P('  * 影响面：R71 §CY3 那三条证据里，mtime 那一支的独立性从「跨机器可复核」')
P('    降为「仅在原树可复核」；另两支（卡面 mtime、_rNN 产物目录）本轮另测。')
P('  * 不推翻 R71 的裁决（窗口取边方向错），因为该裁决还依赖 at 与产物 mtime 两条。')

P('')
P('RESULT %s' % ('ALL-PASS' if not FAILS else 'FAILS=' + str(FAILS)))
sys.exit(0 if not FAILS else 1)
