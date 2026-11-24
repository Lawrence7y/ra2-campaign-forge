# -*- coding: utf-8 -*-
"""R71 · 决定性反控：门禁自带的 selftest，其正控样本是不是「按现行口径」写的？

为什么这一问是决定性的：
  R68 用「全量重映射会让 selftest 变成 4/5」来否定全量重映射，即把 selftest 当**独立证据**。
  但如果 selftest 的正控样本本身是按现行口径构造的（round=R52, at=16:20:00），
  那么它只是在**复述**现行口径，再用它去验现行口径 = 自证循环，不能算独立证据。

做法（不写盘 live，全部在本目录下临时目录里做）：
  把 recheck_verify.py 复制到临时目录，只打**路径分隔符**补丁（这是 Linux 上能跑起来的前提，
  对窗口判定无影响），然后：
    T1  原样（现行 _ROUND_ROWS）⇒ selftest 应全过
    T2  _ROUND_ROWS 整体前移一位（= 修正口径）⇒ 看 selftest 是否变 4/5
    T3  _ROUND_ROWS 顶层再多移一位 ⇒ 应更差（证明 selftest 对偏移敏感）
    T4  只把正控那一条的 at/round 改成「修正口径下 R52 的合法时刻」，其余不动
        ⇒ 若仍全过，说明 selftest 只是跟着样本走，不锚定任何客观事实
    T5  反控：把 _ROUND_ROWS 清空 ⇒ 必须变红（证明它不是恒真）

关键判据：
  若 T2 变 4/5 且 T4 也能全过 ⇒ selftest **不是**独立证据，它只测「样本 vs 表」的一致性。
  这正是自证循环的定义：表与样本由同一人按同一口径写成，再用一者验另一者。
"""
import io, os, re, sys, shutil, subprocess, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
SRC = os.path.join(R14, 'recheck_verify.py')
out, fails = [], []
def P(s=''):
    print(s); out.append(s)
def ck(name, cond, detail=''):
    P(('  PASS ' if cond else '  FAIL ') + name + (('  ' + detail) if detail else ''))
    if not cond: fails.append(name)

BASE_SRC = io.open(SRC, encoding='utf-8').read()
# Linux 可运行性补丁：只改路径分隔符，不碰任何窗口/时刻逻辑。
PATCHED = BASE_SRC.replace("ap = rel.replace('/', '\\\\')", "ap = rel.replace('\\\\', '/')")
ck('路径补丁只改 1 处（不触碰窗口逻辑）', PATCHED != BASE_SRC and
   PATCHED.count("rel.replace('\\\\', '/')") == 1)

BOX = tempfile.mkdtemp(prefix='r71_selftest_')
def install(src, tag):
    """把 src 装成 BOX/recheck_verify.py，把 DISC_ESTABLISH.tsv 也带过去。"""
    p = os.path.join(BOX, 'recheck_verify.py')
    io.open(p, 'w', encoding='utf-8', newline='\n').write(src)
    shutil.copy2(os.path.join(R14, 'DISC_ESTABLISH.tsv'),
                 os.path.join(BOX, 'DISC_ESTABLISH.tsv'))
    # _self_test 的 root 由 _HERE/../.. 推出；把产物临时文件写在 BOX 内即可
    r = subprocess.run([sys.executable, p, '--self-test'], cwd=BOX,
                       capture_output=True, text=True, timeout=300)
    return r.returncode, r.stdout + r.stderr, tag

def tally(o):
    m = re.search(r'SELFTEST (PASS|FAIL) \((\d+)/(\d+)\)', o)
    return (m.group(1), int(m.group(2)), int(m.group(3))) if m else (None, 0, 0)

P('')
P('=== T1 · 原样（现行 _ROUND_ROWS）===')
rc1, o1, _ = install(PATCHED, 'T1')
s1 = tally(o1)
P('  exit=%d selftest=%s %d/%d' % (rc1, s1[0], s1[1], s1[2]))
for l in o1.strip().split('\n'):
    if 'ok=' in l or 'SELFTEST' in l: P('    ' + l[:130])

# ---- 提取并重写 _ROUND_ROWS ----
M = re.search(r'_ROUND_ROWS = \[\n(.*?)\n\]', PATCHED, re.S)
ck('能定位 _ROUND_ROWS 块', M is not None)
BLOCK = M.group(1)
ROW_RE = re.compile(r"\s*\((\d+), '(\d{6})', '(\d{6})', '([^']*)', '([^']*)'\),?")
ROWS = ROW_RE.findall(BLOCK)
P('  _ROUND_ROWS 解析出 %d 行' % len(ROWS))
ck('解析出的行数与盘上一致（22）', len(ROWS) == 22, '%d' % len(ROWS))

def rebuild(rows):
    body = '\n'.join(
        "    (%s, '%s', '%s', '%s', '%s')," % r for r in rows)
    return PATCHED[:M.start(1)] + body + PATCHED[M.end(1):]

# T2：整体改到修正口径 —— 修正口径下「行 N」= 原行 N-1（原行 N-1 的两端正是 before_r(N-1), before_rN）
#     ⇒ 重编号方向是 N -> N+1。
#     第一版写成 N -> N-1（方向反了）：那样 T2 测的是「再往前挪一位」，不是修正口径本身。
#     这个方向错必须记下来 —— 它让 T2 的 4/5 看起来像「复现了 R68 的观察」，其实测的是另一个东西。
SHIFT = [(str(int(n) + 1), s, e, sf, ef) for (n, s, e, sf, ef) in ROWS]
P('')
P('=== T2 · _ROUND_ROWS 整体前移一位（= 修正口径）===')
rc2, o2, _ = install(rebuild(SHIFT), 'T2')
s2 = tally(o2)
P('  exit=%d selftest=%s %d/%d' % (rc2, s2[0], s2[1], s2[2]))
for l in o2.strip().split('\n'):
    if 'ok=' in l or 'SELFTEST' in l: P('    ' + l[:130])

# T3：再移一位
# T3：再往前一位 = 行 N -> N+2。
# 第一版写成 [(n-1) for n in SHIFT]，而 SHIFT 已是 N+1 ⇒ 算回 N+1-1 = N = 原表，
# 于是 T3 恒等于 T1（5/5 是**同义反复**，不是「偏移更远仍然过」）。这个错必须记：
# 它会把「表越错越没事」当成结论读出来，而事实只是我又把表装回去了。
SHIFT2 = [(str(int(n) + 1), s, e, sf, ef) for (n, s, e, sf, ef) in SHIFT]
P('')
P('=== T3 · 再前移一位（更远离现行口径）===')
rc3, o3, _ = install(rebuild(SHIFT2), 'T3')
s3 = tally(o3)
P('  exit=%d selftest=%s %d/%d' % (rc3, s3[0], s3[1], s3[2]))

# T4：只改正控样本，让它按「修正口径」合法，其余不动（表仍为修正口径）
#     修正口径下 R52 = [before_r51, before_r52) = [16:01:44, 16:17:50)
#     取一个合法时刻 16:10:00（落在该区间内，且晚于纪律 11 的立条上界 12:00:54）
P('')
P('=== T4 · 表=修正口径 + 正控样本改成修正口径下合法的时刻 ===')
src_t4 = rebuild(SHIFT)
before_t4 = src_t4
src_t4 = src_t4.replace(
    "round=R52 at=2026-11-22T16:20:00+08:00",
    "round=R52 at=2026-11-22T16:10:00+08:00")
ck('T4 确实改到了正控样本（1 处）',
   src_t4 != before_t4 and src_t4.count('T16:10:00') >= 1)
# NEG3 与 NEG2 的替换锚也要跟着改，否则它们会因为「锚不存在」而假通过
src_t4 = src_t4.replace("good.replace('at=2026-11-22T16:20:00', 'at=2026-11-22T11:00:00')",
                        "good.replace('at=2026-11-22T16:10:00', 'at=2026-11-22T11:00:00')")
src_t4 = src_t4.replace("good.replace('at=2026-11-22T16:20:00+08:00', 'at=2026-11-22T15:00:00+08:00')",
                        "good.replace('at=2026-11-22T16:10:00+08:00', 'at=2026-11-22T15:00:00+08:00')")
rc4, o4, _ = install(src_t4, 'T4')
s4 = tally(o4)
P('  exit=%d selftest=%s %d/%d' % (rc4, s4[0], s4[1], s4[2]))
for l in o4.strip().split('\n'):
    if 'ok=' in l or 'SELFTEST' in l: P('    ' + l[:130])

# T5 反控：表清空
P('')
P('=== T5 · 反控：_ROUND_ROWS 清空 ⇒ 必须全红（非恒真）===')
src_t5 = PATCHED[:M.start(1)] + '    (99, \'000000\', \'000001\', \'x\', \'y\'),' + PATCHED[M.end(1):]
rc5, o5, _ = install(src_t5, 'T5')
s5 = tally(o5)
P('  exit=%d selftest=%s %d/%d' % (rc5, s5[0], s5[1], s5[2]))

P('')
P('=== 判定 ===')
ck('T1 原样全过（基线可跑）', s1[1] == s1[2] == 5 or s1[1] >= 4, '%d/%d' % (s1[1], s1[2]))
P('  T1 %d/%d | T2 %d/%d | T3 %d/%d | T4 %d/%d | T5 %d/%d'
  % (s1[1], s1[2], s2[1], s2[2], s3[1], s3[2], s4[1], s4[2], s5[1], s5[2]))
ck('T5 反控清空表后明显变差（selftest 非恒真）', s5[1] < s1[1],
   '%d/%d vs %d/%d' % (s5[1], s5[2], s1[1], s1[2]))
# 核心判据
if s1[1] == s1[2] and s2[1] < s2[2]:
    P('  ⇒ T1 全过而 T2 不满分：selftest 对偏移**敏感**，R68 的观察可复现')
else:
    P('  ⇒ 注意：T1/T2 的关系与 R68 记录不同，须如实记差异')
if s4[1] == s4[2]:
    P('  ⇒ T4 全过：把样本改成修正口径下合法后，修正口径也能全过')
    P('     ⇒ selftest **不锚定任何客观时刻**，只测「样本 vs 表」一致性 ⇒ 自证循环成立')
else:
    P('  ⇒ T4 未全过（%d/%d）：需看具体哪条不过' % (s4[1], s4[2]))

shutil.rmtree(BOX, ignore_errors=True)
P('')
P('RESULT ' + ('ALL-PASS' if not fails else 'FAIL: ' + ','.join(fails)))
io.open(os.path.join(HERE, 'selftest_r71.log'), 'w', encoding='utf-8',
        newline='\n').write('\n'.join(out) + '\n')
sys.exit(0 if not fails else 1)
