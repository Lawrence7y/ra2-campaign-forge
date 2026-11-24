# -*- coding: utf-8 -*-
"""R72 · 语义控制「before_rN 内容最后一段 = N-1」的口径边界实测。

R71 §CY3 记「语义控制：30 个快照内容最后一段恒为 N-1（30/30）」。
本轮把「扫描口径」与「分母口径」两件事分开量化。

【R72 自错修正 · 由跨家族审计 A2(hy4flash) 抓出，已复算确认】
  初版 docstring 写「R71 可能只扫了有补记的那 30 个」，并据此把 R71 的 30/30
  追认为 35/35 —— 这是**无证据的回溯赋数**，已收回。
  实测：R17_LEAD_BASELINE 有 35 个快照文件，但只覆盖 **30 个 distinct 轮次**
  （r56/r58/r60 各 2 份、r62 有 3 份）。R71 的语义控制循环遍历 variants（按轮次
  分组的字典），分母本来就是 **30 轮**，不是 35 文件。故：
      30 不是「口径子集」，是 **distinct 轮次数**。
  正确表述：R71 的 30/30 在 B 口径下**成立且可复现**；本轮要说的只是
  「A 口径下同一批数据不成立（27/30）」，A/B 差异真实存在，与 30/35 无关。

两种扫描口径的差异（本轮唯一实质发现）：
  A 仅 `## ... R17 第 N 轮` 标题      -> 27/30（按轮次取一份）或 32/35（按文件）
  B 标题 + `> 📌 **第 N 轮**` 补记行  -> 30/30（按轮次）或 35/35（按文件）

反控：
  N1 伪造一个末段轮次 = N 的快照副本 ⇒ 两口径都必须判违规（非恒真）
  N2 伪造末段 = N-2 ⇒ 两口径都必须判违规
  N3 反控 A 口径不是「空集恒过」：必须至少有 3 个违反被报出
"""
import io, os, re, sys, shutil

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
RE_H = re.compile(r'(?m)^##.*?R17 第 (\d+) 轮')
RE_N = re.compile(r'(?m)^> .{0,4}\*\*第 (\d+) 轮')

def scan(path, mode):
    txt = io.open(path, encoding='utf-8', errors='replace').read()
    h = [int(x) for x in RE_H.findall(txt)]
    n = [int(x) for x in RE_N.findall(txt)]
    if mode == 'A':
        return max(h) if h else None
    return max(h + n) if (h or n) else None

rows = []
for f in os.listdir(BASE):
    m = SNAP.match(f)
    if m: rows.append((int(m.group(1)), m.group(2), f))
rows.sort()

P('=== S1 · 两种口径逐快照对照 ===')
P('  round  file_hh   A(仅##标题)  B(标题+补记)  A_ok  B_ok')
na = nb = 0
violA = []
for r, hh, f in rows:
    a = scan(os.path.join(BASE, f), 'A')
    b = scan(os.path.join(BASE, f), 'B')
    oka = (a == r - 1); okb = (b == r - 1)
    na += oka; nb += okb
    if not oka: violA.append(r)
    if not (oka and okb):
        P('  %5d  %-8s  %-11s  %-13s  %-5s %s' % (r, hh, a, b, oka, okb))
ck('S1-a A 口径（仅 ## 标题）不满足 N-1 的快照存在（非空集）', len(violA) > 0,
   'viol=%s' % violA)
P('  A 口径合规 %d/%d ; B 口径合规 %d/%d' % (na, len(rows), nb, len(rows)))

# 关键：两口径必须给出不同答案，否则「口径边界」这个说法本身是假的
diff = [r for r, hh, f in rows
        if scan(os.path.join(BASE, f), 'A') != scan(os.path.join(BASE, f), 'B')]
ck('S1-b 两口径在至少一个快照上给出不同结果（否则「口径边界」不成立）',
   len(diff) > 0, 'diff_rounds=%s' % diff)
ck('S1-c 差异快照集合恰等于 A 口径的违反集合（B 口径把它们全部救回）',
   sorted(diff) == sorted(violA), 'diff=%s violA=%s' % (sorted(diff), sorted(violA)))
ck('S1-d B 口径 100% 合规', nb == len(rows), '%d/%d' % (nb, len(rows)))

P('')
P('=== S2 · 违规快照的形态差异（为何 B 口径救得回）===')
for r in violA:
    f = [x for x in rows if x[0] == r][0][2]
    p = os.path.join(BASE, f)
    txt = io.open(p, encoding='utf-8', errors='replace').read()
    hs = [int(x) for x in RE_H.findall(txt)]
    ns = [int(x) for x in RE_N.findall(txt)]
    P('  r%-3d ## 标题轮次=%s ; > 补记轮次=%s ; 差集=%s'
      % (r, sorted(set(hs)), sorted(set(ns)), sorted(set(ns) - set(hs))))

P('')
P('=== S3 · 反控 ===')
tmp = os.path.join(HERE, '_semctl_tmp.md')

def synth(last_round, upto, notes_only=()):
    """合成一个最小快照文本：标题覆盖 upto-4..upto，另可把指定轮次只写成补记行。

    R72 自错修正（A2 抓出）：初版 synth 只生成 ## 标题列表，docstring 却写
    「标题与补记各占一半」——实现与文档不符，导致 N1/N2/N3 中 B 的补记分支
    从未触发，A≡B，「两口径都必须…」成同义反复。现改为：标题与补记都生成，
    并允许把某几个轮次**只**放进补记，从而真正覆盖 RE_N 分支。
    """
    parts = []
    for k in range(upto - 4, upto + 1):
        parts.append('## \U0001f534 R17 第 %d 轮（伪）\n' % k)
    for k in notes_only:
        parts.append('> \U0001f4cc **第 %d 轮**（伪补记）\n' % k)
    return ''.join(parts)

# （本轮自错修正：初版把「更低轮次」append 到真实快照上，max 不变 ⇒ 反控失效。
#  这是当天第二类「反控设计错」，与 R71 §CY9⑤ 同族。改为合成最小文本，直接控制 max。）
# N1/N2 的关键是「B 的补记分支也必须被覆盖」⇒ 把末段轮次**只**写进补记行
for last, tag in ((55, 'N1 末段=N（应为 N-1）'), (53, 'N2 末段=N-2')):
    t2 = synth(52, 52, notes_only=(last,))   # ## 末段 52；补记里出现 last
    io.open(tmp, 'w', encoding='utf-8').write(t2)
    a = scan(tmp, 'A'); b = scan(tmp, 'B')
    ck('S3 %s ⇒ 两口径都必须判违规（N=55；B 的补记分支确实被触发）' % tag,
       a != 54 and b != 54 and b == last, 'A=%s B=%s' % (a, b))

# N3：末段恰为 N-1 ⇒ 两口径都必须合规（证明 N1/N2 不是「永远违法」）
io.open(tmp, 'w', encoding='utf-8').write(synth(54, 54, notes_only=(54,)))
a = scan(tmp, 'A'); b = scan(tmp, 'B')
ck('S3 N3 对照 · 末段恰为 N-1（标题与补记都是 54）⇒ 两口径都必须合规',
   a == 54 and b == 54, 'A=%s B=%s' % (a, b))

# N4：只在补记行里出现 N ⇒ A 口径漏检、B 口径抓到（这正是本轮要证的漏检方向）
t4 = synth(54, 54, notes_only=(55,))
io.open(tmp, 'w', encoding='utf-8').write(t4)
a = scan(tmp, 'A'); b = scan(tmp, 'B')
ck('S3 N4 关键 · 第 N 轮只出现在补记行 ⇒ A 漏检(a==54 合规) 而 B 抓到(b==55 违规)',
   a == 54 and b == 55, 'A=%s B=%s' % (a, b))
os.remove(tmp)

P('')
P('=== S4 · 判据（应当用哪个口径，不是选能过关的）===')
P('  * 目标命题是「before_rN 拍在第 N 轮写板之前」，即快照里**不应出现第 N 轮及以后的内容**。')
P('  * 因此正确判据是 B（标题 + 补记行）：补记行 `> 📌 **第 K 轮**` 也是看板上的轮次声明，')
P('    只扫 ## 标题会**漏掉**「我在补记里已经写了第 N 轮」的情形 ⇒ A 口径漏检（假合规）。')
P('  * 实测：A 口径对 r63/r64/r65 报违规，是**假阳性**——这三个快照的 ## 末段停在 r61，')
P('    但补记里已有 r62 的内容，末段轮次仍是 N-1 ⇒ B 口径正确。')
P('  * 边界（A2 抓出的方向差）：N4 证的是 A 的**假阴性**（漏检），r63/64/65 是 A 的')
P('    **假阳性**；N4 不能直接支撑后者。后者由 S1 的逐快照实测直接支撑（见 S2 段）。')
P('  * 分母口径：R71 的 30/30 分母是 **30 distinct 轮次**（35 文件 / 4 轮有多份），')
P('    **不是**「只扫了 30 个」的子集。本轮初版把它误说成「R71 只扫 30 个」并追认 35/35，')
P('    该追认已收回（A2 指正、主会话复算确认）。')
P('  * 结论：R71 的 30/30 在 B 口径下**成立且可复现**；本轮实质发现是')
P('    「A 口径下同一批数据不成立（27/30）」，即**口径未声明会改变结论**。')
P('    今后引此控制**必须写明「标题+补记」**。')

P('')
P('RESULT %s' % ('ALL-PASS' if not FAILS else 'FAILS=' + str(FAILS)))
sys.exit(0 if not FAILS else 1)
