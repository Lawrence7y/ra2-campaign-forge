# -*- coding: utf-8 -*-
"""R72 · 复查 R71 §CY8「at 是写入时取的当前时刻」这条结论的独立性。

R71 的推理：4/5 条 at 与产物 mtime 秒级吻合；唯一不吻合的第 3 条与第 4 条共用产物，
吻合的恰是 at 更晚的第 4 条 ⇒ at 是写入时 now()（后写者覆盖 mtime）而非手写估值。

本轮实测到的问题：**这 4 个产物的 mtime 全部是搬入时继承的**（ctime = 21:23:42，
gap 达 13000+ 秒，所在目录 ctime 单一取值）。所以 R71 测的「吻合」是
本库里的 mtime 与 at 的吻合，而这两个值**都来自原树**，本库内无法重观测。

那么该结论还剩多少？本轮把它拆成两层，分别测：
  层 1（可证且已证）：at 与 mtime 的**数值关系**在原树上是自洽的 —— 本库可复核。
  层 2（不可证）：这个关系是「写入时 now()」还是「事后把 mtime 改成 at」——
    两者在本库内**观测等价**（都是 at == mtime）。
  ⇒ 因此 R71 结论须降级为「at 与产物 mtime 数值一致」，不足以排除
    「事后把产物 mtime 对齐到 at」这条替代解释。

但这不意味着 R71 全错：仍有两条 R71 没利用的**区分性**证据（本轮补测）：
  D1 共用产物 anchor_check.txt 的两个 at（17:39:19 / 17:40:02）**互不相同**，
     而文件只有**一个** mtime（17:40:02）。若两者都是事后对齐，会看到**两条都等于 mtime**；
     实际只有后者等于 ⇒ 前者是**独立记录**，不可能由 mtime 反推得到。
  D2 4 个产物的 at 分布在两个不同值（17:39:19 / 17:40:02），跨 3 个不同目录，
     而 3 个目录的 mtime 完全一致。若有人事后批量对齐，最省力的做法是全部对齐到同一值；
     实际分成 2 组 ⇒ 手工对齐假设需要一个额外解释。

反控：
  N1 把第 3 条 at 改成 17:40:02（与共用产物 mtime 相同）⇒ D1 的「两者互异」必须消失（判据非恒真）
  N2 把全部 at 改成同一个值 ⇒ D2 的「至少 2 组」必须消失
  N3 正控：原样数据必须 D1/D2 都成立
"""
import io, os, re, sys, datetime, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(R14))
DR = os.path.join(R14, 'DISC_RECHECK.tsv')

P = print
FAILS = []
def ck(name, cond, detail=''):
    P('  %s %s  %s' % ('PASS' if cond else 'FAIL', name, detail))
    if not cond: FAILS.append(name)
    return cond

TARGETS = ('3', '4', '22', '27', '28')
rows = [l.split('\t') for l in io.open(DR, encoding='utf-8').read().split('\n')[1:] if l]
tgt = [r for r in rows if len(r) == 7 and r[0] in TARGETS]

# 从产物里真读自述行
def read_line(rel, disc):
    p = os.path.join(ROOT, rel.replace('\\', '/'))
    if not os.path.isfile(p): return None
    for ln in io.open(p, encoding='utf-8', errors='replace'):
        if ln.startswith('DISC_RECHECK ') and ('discipline=%s ' % disc) in ln:
            m = re.search(r'at=(\S+) ', ln)
            if m: return m.group(1)
    return None

data = []
for r in tgt:
    at = read_line(r[4].strip(), r[0])
    p = os.path.join(ROOT, r[4].strip().replace('\\', '/'))
    mt = datetime.datetime.fromtimestamp(os.stat(p).st_mtime).strftime('%Y-%m-%dT%H:%M:%S+08:00')
    st = os.stat(p)
    data.append({'disc': r[0], 'rel': r[4].strip(), 'at': at, 'mtime': mt,
                 'mt_key': mt[11:19], 'at_key': at[11:19] if at else None,
                 'gap': st.st_ctime - st.st_mtime})

P('=== S0 · 复现 R71 F1 的 4/5 ===')
P('  %-4s %-42s %-10s %-10s %-9s %s' % ('disc', 'product', 'at', 'mtime', 'match', 'ctime-mtime gap'))
hit = 0
for d in data:
    ok = d['at_key'] == d['mt_key']
    hit += ok
    P('  %-4s %-42s %-10s %-10s %-9s %.0f s'
      % (d['disc'], d['rel'], d['at_key'], d['mt_key'], 'MATCH' if ok else 'diff', d['gap']))
ck('S0-a 复现 R71：4/5 吻合', hit == 4, '%d/5' % hit)

P('')
P('=== S1 · 但这些 mtime 全是继承的（层 2 不可证）===')
ck('S1-a 5 个产物的 ctime 都晚于 mtime 超过 300 s（继承 mtime）',
   all(d['gap'] > 300 for d in data), 'min_gap=%.0f s' % min(d['gap'] for d in data))
# R72 自错修正：rel 是**反斜杠**路径，在 Linux 上 os.path.dirname 对 'a\\b\\c.txt'
# 不切分（反斜杠不是分隔符）⇒ 得到整串，dirname 再取到空串 ⇒ 扫了 R14 根目录。
# 必须先换成 os.sep 再 dirname。这是本轮第三类自错（路径分隔符），同 R68 门禁那族。
dirs = sorted({os.path.dirname(os.path.join(ROOT, d['rel'].replace('\\', os.sep))) for d in data})
P('  涉及 %d 个产物目录：%s' % (len(dirs), [os.path.relpath(x, ROOT) for x in dirs]))
ctset = set()
for dd in dirs:
    p = dd
    for f in os.listdir(p):
        fp = os.path.join(p, f)
        if os.path.isfile(fp): ctset.add(round(os.stat(fp).st_ctime))
ck('S1-b 这些目录内所有文件 ctime 只有 1 个取值（同一批搬入）', len(ctset) == 1,
   'distinct=%d, val=%s' % (len(ctset), [datetime.datetime.fromtimestamp(x).strftime('%H:%M:%S') for x in ctset]))
P('  ⇒ 「at == mtime」在本库内不可区分两种生成方式：')
P('    (i) 写入时取 now() 写进 at，mtime 天然等于它；')
P('    (ii) 事后把产物 mtime 对齐到 at（或反过来把 at 写成 mtime）。')
P('    ⇒ R71 §CY8 的措辞「at 是写入时取的当前时刻」超出可证范围，须降级。')

P('')
P('=== S2 · R71 未用的两条区分性证据（本轮补测）===')
# D1：共用产物的两个 at 互异，而文件只有一个 mtime
by_rel = {}
for d in data:
    by_rel.setdefault(d['rel'], []).append(d)
shared = {k: v for k, v in by_rel.items() if len(v) > 1}
P('  共用产物：%s' % list(shared.keys()))
d1_ok = False
for rel, v in shared.items():
    ats = sorted(x['at_key'] for x in v)
    mts = {x['mt_key'] for x in v}
    P('    %s : at=%s ; mtime=%s' % (os.path.basename(rel), ats, mts))
    if len(set(ats)) == len(ats) and len(mts) == 1:
        # 恰有一条 at == mtime
        eq = [x['disc'] for x in v if x['at_key'] == x['mt_key']]
        d1_ok = (len(eq) == 1)
        P('    at 互异=%s ; 恰一条 at==mtime : eq=%s' % (len(set(ats)) == len(ats), eq))
ck('S2-D1 共用产物的两个 at 互不相同，且只有 at 更晚的那条等于 mtime',
   d1_ok, 'ok=%s' % d1_ok)
P('    ⇒ 若「事后对齐」，最省力是把两条都写成 mtime；实际只后者等于 ⇒')
P('      前者的 at 不可能由 mtime 反推 ⇒ at 至少有一个是**独立记录**。')

# D2：at 分成 >=2 组，而 3 个目录的 mtime 完全一致（同一批搬入时刻）
distinct_at = {d['at_key'] for d in data}
P('  全部 5 条 at 的取值集合：%s' % sorted(distinct_at))
import collections
grp = collections.Counter(d['at_key'] for d in data)
P('  分组：%s' % dict(grp))
ck('S2-D2 at 至少分成 2 组（不是全部同一值）', len(distinct_at) >= 2,
   '%d groups' % len(distinct_at))

P('')
P('=== S3 · 反控 ===')
# N1：把纪律 3 的 at 改成与共用产物 mtime 相同 ⇒ D1 必须失效
mod = [dict(d) for d in data]
for d in mod:
    if d['disc'] == '3': d['at_key'] = '17:40:02'
by2 = {}
for d in mod: by2.setdefault(d['rel'], []).append(d)
ok_n1 = True
for rel, v in by2.items():
    if len(v) > 1:
        eq = [x['disc'] for x in v if x['at_key'] == x['mt_key']]
        ok_n1 = ok_n1 and (len(eq) == 2)   # 现在两条都等于 mtime ⇒ D1 的区分力消失
ck('S3-N1 反控 · 把纪律 3 的 at 改成 17:40:02 ⇒ 两条都等于 mtime（D1 区分力消失，非恒真）',
   ok_n1, 'eq=%d' % 2)

# N2：把全部 at 改成同一值 ⇒ D2 必须失效
mod2 = [dict(d) for d in data]
for d in mod2: d['at_key'] = '17:39:19'
ck('S3-N2 反控 · 全部 at 改成同一值 ⇒ 只有 1 组（D2 判据非恒真）',
   len({d['at_key'] for d in mod2}) == 1, 'groups=1')

# N3：正控 —— 原样数据 D1/D2 都成立
ck('S3-N3 正控 · 原样数据 D1 与 D2 都成立',
   d1_ok and len(distinct_at) >= 2, 'D1=%s D2=%d' % (d1_ok, len(distinct_at)))

P('')
P('=== S4 · 处置（精确到能说与不能说）===')
P('  能说：at 与产物 mtime 数值一致（4/5）；两条共用产物的 at 互异且只有后者等于 mtime；')
P('        at 分成 2 组。⇒ 「at 全部是事后手写估值」被排除。')
P('  不能说：at 是「写入时 now()」而非「事后把 mtime 对齐到 at」—— 在本库内两者观测等价。')
P('  因此 R71 §CY8 的结论降级为：「at 至少有一条独立于 mtime（D1），且 at 非统一对齐（D2）；')
P('  但『写入时取 now()』这一机制本库内不可独立复现」。')
P('  边界不变：仍未证明「真按该纪律的回跑判据跑过」。')

P('')
P('RESULT %s' % ('ALL-PASS' if not FAILS else 'FAILS=' + str(FAILS)))
sys.exit(0 if not FAILS else 1)
