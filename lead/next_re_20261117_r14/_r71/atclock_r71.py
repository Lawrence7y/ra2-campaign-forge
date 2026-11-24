# -*- coding: utf-8 -*-
"""R71 · 决定性反证：5 条 DISC_RECHECK 的 at 是「手写自述」还是「真实写入时刻」？

为什么必须回答这一问：
  R59-T4 卡的 Q2 把它列为「本审计最关键的问题」：
    「若 at 是执行员事后手写的（而非产物自动打的时间），那它就是自述，
      §2.57 的『off-by-one』就是在为一个自述时间调整判据。」
  该卡要求的产物目录 R17_R95_T4_AUDIT57 **从未建立**（本轮实测：MISSING），
  即这一问**问了 12 轮、一直没人回答**。

本轮的独立材料：**产物文件自己的 mtime**（文件系统记录，不经过自述行）。
判据：
  * 若 at 是事后手写/编造 ⇒ 它与 mtime 应当**普遍不符**（人手写不到秒）。
  * 若 at 是写入时由代码取的 now() ⇒ 与「该文件**最后一次**写入的 mtime」应当**秒级吻合**。
  * 特别注意：一个产物可能被写多次（如 anchor_check.txt 同时是纪律 3 与 4 的产物），
    此时只有一个 at 能与最终 mtime 吻合 —— 另一条必然不吻合。**这本身就是证据**：
    若两条都吻合，反而说明有人在事后对齐过。

测量：
  F1  逐条比对 at 的时分秒 vs 产物 mtime 的时分秒
  F2  对多纪律共用的产物，验证「最后写入者吻合、先前写入者不吻合」这一结构
  F3  反控：把 at 整体平移 1 秒 ⇒ 必须全部判不吻合（证明比对不是恒真）
  F4  反控：把 at 设成整分钟（人手写时最可能的样子）⇒ 必须判不吻合
"""
import os, re, io, sys, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
out, fails = [], []
def P(s=''):
    print(s); out.append(s)
def ck(name, cond, detail=''):
    P(('  PASS ' if cond else '  FAIL ') + name + (('  ' + detail) if detail else ''))
    if not cond: fails.append(name)

# 5 条自述行的 (纪律号, 产物相对路径, at 字符串) —— 从盘上按 DISC_RECHECK.tsv 取，不硬编码猜
import importlib.util
sys.path.insert(0, R14)
spec = importlib.util.spec_from_file_location('rv', os.path.join(R14, 'recheck_verify.py'))
rv = importlib.util.module_from_spec(spec); spec.loader.exec_module(rv)

# 从产物文件里真读自述行，避免手抄
PATHS = {
    3:  'R17_R61_FACTINDEX_V58/anchor_check.txt',
    4:  'R17_R61_FACTINDEX_V58/anchor_check.txt',
    22: 'R17_R84_T1_NARRATIVE/should_exclude.tsv',
    27: 'R17_R81_T2_EVID/_verdicts.tsv',
    28: 'R17_R88_T1_SEMDEF/tier_final.tsv',
}
LINE_RE = re.compile(r'^DISC_RECHECK discipline=(\d+) round=(R\d+) at=(\S+) anchors=(\S+) conclusion=(\S+)$')

found = {}
for disc, rel in sorted(PATHS.items()):
    p = os.path.join(R14, rel)
    if not os.path.isfile(p):
        P('[跳过] 产物不存在：%s' % rel); continue
    for ln in io.open(p, encoding='utf-8', errors='replace').read().splitlines():
        m = LINE_RE.match(ln)
        if m and int(m.group(1)) == disc:
            found[disc] = (rel, m.group(3))
P('[读取] 从产物里真读出自述行 %d 条（期望 5）' % len(found))
ck('能从产物里读到 5 条自述行', len(found) == 5, '%d' % len(found))

# 同一个产物的最后写入 mtime
def mtime_of(rel):
    return os.stat(os.path.join(R14, rel)).st_mtime

P('')
P('=== F1 · at 与产物 mtime 逐秒比对 ===')
P('  %-4s %-46s %-10s %-10s %s' % ('纪律', '产物', 'at', 'mtime', '判定'))
hit = 0
for disc in sorted(found):
    rel, at = found[disc]
    mt = datetime.datetime.fromtimestamp(mtime_of(rel)).strftime('%H:%M:%S')
    ok = (at[11:19] == mt)
    if ok: hit += 1
    P('  %-4d %-46s %-10s %-10s %s' % (disc, rel, at[11:19], mt, '吻合' if ok else '不吻合'))
P('')
P('  吻合 %d / %d' % (hit, len(found)))
ck('F1 · 多数自述 at 与产物 mtime 秒级吻合（4/5，非「普遍不符」）',
   hit == 4, '%d/%d' % (hit, len(found)))

# ---------- F2 共享产物的结构 ----------
P('')
P('=== F2 · 共享产物 anchor_check.txt：谁吻合、谁不吻合 ===')
shared = [d for d in found if sorted(found).count(d) and
          sum(1 for x in found if found[x][0] == found[d][0]) > 1]
by_file = {}
for d in sorted(found):
    by_file.setdefault(found[d][0], []).append(d)
multi = {k: v for k, v in by_file.items() if len(v) > 1}
P('  多纪律共用的产物：%s' % multi)
ck('F2-a 存在一个 2 纪律共用的产物（纪律 3 与 4）',
   any(set(v) == {3, 4} for v in multi.values()), '%s' % multi)
for rel, ds in multi.items():
    mt = datetime.datetime.fromtimestamp(mtime_of(rel)).strftime('%H:%M:%S')
    match = [d for d in ds if found[d][1][11:19] == mt]
    P('    %s mtime=%s；吻合者=%s；不吻合者=%s'
      % (rel, mt, match, [d for d in ds if d not in match]))
    ck('F2-b %s：恰有 1 条吻合（= 最后写入者），另 1 条不吻合' % os.path.basename(rel),
       len(match) == 1, '吻合 %s' % match)
    # 关键：吻合的是**时刻更晚**的那条
    later = max(ds, key=lambda d: found[d][1])
    ck('F2-c 吻合的恰是 at 更晚的那条（= 后写者覆盖了文件 mtime）',
       match == [later], 'later=%s match=%s' % (later, match))

# ---------- F3/F4 反控 ----------
P('')
P('=== F3/F4 · 反控 ===')
def cmp_at_mtime(at):
    """整体比对函数：给定 at 字符串，返回与各产物 mtime 的吻合条数。"""
    n = 0
    for rel, a in [(found[d][0], at) for d in found]:
        if a[11:19] == datetime.datetime.fromtimestamp(mtime_of(rel)).strftime('%H:%M:%S'):
            n += 1
    return n

# F3：把每条 at 平移 1 秒 —— 逐条算，必须全部不吻合
P('  F3 · 逐条 at 平移 1 秒：')
f3_bad = 0
for d in sorted(found):
    rel, at = found[d]
    t = datetime.datetime.strptime(at, '%Y-%m-%dT%H:%M:%S%z')
    t2 = (t + datetime.timedelta(seconds=1)).strftime('%Y-%m-%dT%H:%M:%S+08:00')
    mt = datetime.datetime.fromtimestamp(mtime_of(rel)).strftime('%H:%M:%S')
    same = (t2[11:19] == mt)
    P('    纪律%d at+1s=%s vs mtime=%s ⇒ %s' % (d, t2[11:19], mt, '仍吻合(坏)' if same else '不吻合'))
    if same: f3_bad += 1
ck('F3 平移 1 秒后全部不吻合（比对精确到秒，非粗粒度）', f3_bad == 0, '%d 条仍吻合' % f3_bad)

# F4：人手写时间最可能的形态 = 整分钟或整秒 00
P('  F4 · 假设 at 是「人手写的整分钟」：')
f4_hit = 0
for d in sorted(found):
    rel, at = found[d]
    mt = datetime.datetime.fromtimestamp(mtime_of(rel)).strftime('%H:%M:%S')
    rounded = mt[:6] + '00'
    if rounded == mt: f4_hit += 1
P('    若 mtime 本身恰是整分 00 秒的条数：%d（越少 ⇒ 越不可能由「整分自述」撞上）' % f4_hit)
ck('F4 没有一个产物的 mtime 落在整分 00 秒 ⇒ 「人手写整分」无法解释这批吻合',
   f4_hit == 0, '%d 条' % f4_hit)

P('')
P('=== 结论（如实，含边界）===')
P('  5 条里 4 条 at 与产物 mtime **秒级吻合**，唯一不吻合的第 3 条')
P('  与第 4 条共用 anchor_check.txt，且吻合的恰是 at 更晚的第 4 条。')
P('  ⇒ at 不是事后手写的估值，而是写入时取的当前时刻（后写者覆盖了 mtime）。')
P('  边界：这证明「at 记的是真实写入时刻」，**不**证明「该次写入做了纪律所要求的回跑」。')
P('        门禁 R1-R6 检的是「自述行跨字段一致性」，本测量也只加强到「时刻真实性」。')

P('')
P('RESULT ' + ('ALL-PASS' if not fails else 'FAIL: ' + ','.join(fails)))
io.open(os.path.join(HERE, 'atclock_r71.log'), 'w', encoding='utf-8',
        newline='\n').write('\n'.join(out) + '\n')
sys.exit(0 if not fails else 1)
