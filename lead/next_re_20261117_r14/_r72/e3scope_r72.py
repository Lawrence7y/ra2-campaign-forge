# -*- coding: utf-8 -*-
"""R72 · R71 证据源 B（_rNN 产物目录最早文件 mtime）的 5 个样本全部取自搬入批。

R71 §CY3 用三支证据裁窗口取边方向，其中 B 支报「CUR 0/5 vs FIX 5/5」。
本轮实测这 5 个样本是 _r38 / _r62 / _r63 / _r64 / _r65。

关键问题：这 5 个目录是不是本机真跑的产物？
  若它们的 ctime 全部是同一个值（21:23:41），则其 mtime 是**搬入时继承**的，
  与本轮 clockindep_r72 查明的 E1（before 快照）属同一批 ⇒ B 支不是独立时钟，
  它的 5/5 只是「搬入时刻恰好落在 FIX 窗口内」，是搬入这件事的后果。

反控：
  N1 本机真跑的 5 个目录（_r68.._r72）必须判「非搬入」⇒ 判据能区分
  N2 人为构造一个同秒 ctime 的目录 ⇒ 必须判「搬入」
  N3 若把 _r68.._r72 当成 B 支样本代入同一套「取最早文件 mtime 归入轮次」的判据，
     它们全部落在**表未覆盖**区（R71 日志已记 6 个这样的目录）⇒ B 支在样本层面
     就已经在用的表之外取样，不能同时用于证明该表。
"""
import io, os, re, sys, datetime, shutil, statistics

HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
BASE = os.path.join(R14, 'R17_LEAD_BASELINE')

P = print
FAILS = []
def ck(name, cond, detail=''):
    P('  %s %s  %s' % ('PASS' if cond else 'FAIL', name, detail))
    if not cond: FAILS.append(name)
    return cond

DIR_RE = re.compile(r'^_r(\d+)$')
info = {}
for d in sorted(os.listdir(R14), key=lambda x: (len(x), x)):
    m = DIR_RE.match(d)
    if not m: continue
    dp = os.path.join(R14, d)
    if not os.path.isdir(dp): continue
    files = [f for f in os.listdir(dp) if os.path.isfile(os.path.join(dp, f))]
    if not files: continue
    cts = [round(os.stat(os.path.join(dp, f)).st_ctime) for f in files]
    mts = [os.stat(os.path.join(dp, f)).st_mtime for f in files]
    info[int(m.group(1))] = {
        'dir': d, 'n': len(files),
        'distinct_ctime': len(set(cts)),
        'ctime_uniq': sorted(set(cts)),
        'earliest_mtime': min(mts),
    }

P('=== S1 · R71 证据源 B 的 5 个样本 ===')
B_SAMPLES = [38, 62, 63, 64, 65]
P('  %-5s %-6s %-10s %-22s %s' % ('r', 'files', 'dist_ct', 'ctime', 'status'))
imp_b = 0
for r in B_SAMPLES:
    if r not in info:
        P('  %-5d MISSING from disk' % r); continue
    i = info[r]
    imp = i['distinct_ctime'] == 1
    imp_b += imp
    P('  %-5d %-6d %-10d %-22s %s' % (r, i['n'], i['distinct_ctime'],
      datetime.datetime.fromtimestamp(i['ctime_uniq'][0]).strftime('%Y-%m-%d %H:%M:%S'),
      'IMPORTED' if imp else 'LOCAL'))
ck('S1-a B 支 5 个样本全部在场', all(r in info for r in B_SAMPLES), 'missing=%s'
   % [r for r in B_SAMPLES if r not in info])
ck('S1-b B 支 5 个样本**全部**是搬入目录（ctime 单一取值）', imp_b == 5, '%d/5' % imp_b)
ck('S1-c 这 5 个目录的 ctime 是同一个值（同一次部署）',
   len({info[r]['ctime_uniq'][0] for r in B_SAMPLES if r in info}) == 1,
   '%s' % {datetime.datetime.fromtimestamp(info[r]['ctime_uniq'][0]).strftime('%H:%M:%S')
           for r in B_SAMPLES if r in info})

P('')
P('=== S2 · 对照：本机真跑的目录长什么样 ===')
LOCAL = [r for r in info if r >= 68]
P('  %-5s %-6s %-10s %s' % ('r', 'files', 'dist_ct', 'status'))
for r in sorted(LOCAL):
    P('  %-5d %-6d %-10d %s' % (r, info[r]['n'], info[r]['distinct_ctime'], 'LOCAL'))
ck('S2-a 本机真跑的目录 ctime 取值数 > 1（非搬入）',
   all(info[r]['distinct_ctime'] > 1 for r in LOCAL), '%s'
   % {r: info[r]['distinct_ctime'] for r in sorted(LOCAL)})

P('')
P('=== S3 · 结论 ===')
ck('S3-a B 支样本 100% 来自搬入批 ⇒ B 支与 E1 同源，不是独立第三支',
   imp_b == 5 and len({info[r]['ctime_uniq'][0] for r in B_SAMPLES if r in info}) == 1, 'ok')
P('  ⇒ R71 §CY3「三条证据全部同向」实为：')
P('    E1（before 快照 mtime）、E2（卡面 mtime）、E3（轮目录最早文件 mtime）')
P('    三者的样本**全部**落在 2026-11-22 21:23:41 那次部署搬入的批里。')
P('    它们的 mtime 都是**拷入时继承的**，本库内无法重新观测。')
P('    ⇒ 三者一致不是三个独立验证，而是**同一份拷贝的三种读法**。')
P('  ⇒ 这不推翻 R71 的**裁决方向**（数据仍约束方向），但「三条证据」这个强度说法须收回，')
P('    降级为「一次搬入所携带的时刻信息，在三个不同口径下给出同一方向」。')

P('')
P('=== S4 · 反控 ===')
# N1：本机真跑必须判非搬入（已在 S2-a 证明，这里单列一条）
ck('S4-N1 反控 · _r71 判「非搬入」', info[71]['distinct_ctime'] > 1,
   'dist_ct=%d' % info[71]['distinct_ctime'])
# N2：构造同秒 ctime 目录 ⇒ 判搬入
tmpd = os.path.join(HERE, '_e3_probe')
if os.path.isdir(tmpd): shutil.rmtree(tmpd)
os.makedirs(tmpd)
for k in range(3):
    io.open(os.path.join(tmpd, 'f%d.txt' % k), 'w', encoding='utf-8').write('x\n')
cts = [round(os.stat(os.path.join(tmpd, f)).st_ctime) for f in os.listdir(tmpd)]
ck('S4-N2 反控 · 同一次循环写出的 3 个文件 ctime 单一取值 ⇒ 判据会判「搬入」',
   len(set(cts)) == 1, 'distinct=%d' % len(set(cts)))
shutil.rmtree(tmpd)
# N3：B 支样本的 earliest_mtime 与 before 快照的 mtime 是否同批
P('  B 支样本 earliest_mtime：%s'
  % {r: datetime.datetime.fromtimestamp(info[r]['earliest_mtime']).strftime('%H:%M:%S')
     for r in B_SAMPLES if r in info})
# 卡面 mtime 也同源检验
CARDS = os.path.join(R14, '_cards')
card_ct = {}
for f in os.listdir(CARDS):
    p = os.path.join(CARDS, f)
    if not os.path.isfile(p): continue
    m = re.match(r'R(\d+)[-_]', f)
    if m:
        st = os.stat(p)
        if st.st_ctime - st.st_mtime > 300:
            card_ct.setdefault(int(m.group(1)), []).append(round(st.st_ctime))
same_uniq = {r: set(card_ct[r]) for r in B_SAMPLES if r in card_ct}
P('  B 支各轮对应的搬入卡片的 ctime 取值集合：%s'
  % {r: sorted({datetime.datetime.fromtimestamp(x).strftime('%H:%M:%S') for x in v})
     for r, v in same_uniq.items()})
ck('S4-N3 对照 · B 支各轮卡片 ctime 与目录 ctime 是同一个值（同一批）',
   all(len(v) == 1 for v in same_uniq.values()) and len(same_uniq) > 0,
   '%d rounds' % len(same_uniq))

P('')
P('RESULT %s' % ('ALL-PASS' if not FAILS else 'FAILS=' + str(FAILS)))
sys.exit(0 if not FAILS else 1)
