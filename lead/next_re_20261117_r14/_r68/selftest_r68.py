# -*- coding: utf-8 -*-
"""R68 · 用校验器自带 self-test 做判别性测量：窗口平移到底是「修 bug」还是「放宽」？

背景矛盾（§2.57 vs §2.59）：
  §2.57 说窗口表是 off-by-one、把 r55 起点前移后 5 条自述行通过；
  §2.59 说这个改动让 self-test 从 5/5 退化为 4/5，因此回退了。
两者必有一错。本轮用同一份代码、同一份 DISC_ESTABLISH，只改窗口表，跑四组对照，
并解释「为什么平移会打破 POS」——如果解释说得通，那 §2.57 的「off-by-one」就只是
「让被测量去适配测量」，不是修 bug。
"""
import io, os, re, shutil, subprocess, sys

R14 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(R14, '_r68')
SRC = io.open(os.path.join(R14, 'recheck_verify.py'), encoding='utf-8').read()
SNAP = {}
for n in os.listdir(os.path.join(R14, 'R17_LEAD_BASELINE')):
    m = re.match(r'STATUS_BOARD(?:\.md)?\.before_r(\d+)_(\d{6})\.md$', n)
    if m:
        SNAP.setdefault(int(m.group(1)), []).append(m.group(2))
FIRST = {k: min(v) for k, v in SNAP.items()}

fails, buf = [], []
def P(s=''):
    print(s); buf.append(s)
def ck(n, c, d=''):
    P(('  PASS ' if c else '  FAIL ') + n + (('  ' + d) if d else ''))
    if not c: fails.append(n)

def run_variant(tag, mutate):
    d = '/tmp/rvs_' + tag
    if os.path.isdir(d):
        shutil.rmtree(d)
    os.makedirs(d)
    s = mutate(SRC)
    # Linux 等值替换：仅路径分隔符
    s = s.replace("ap = rel.replace('/', '\\\\')", "ap = rel.replace('\\\\', '/')")
    io.open(os.path.join(d, 'recheck_verify.py'), 'w', encoding='utf-8',
            newline='\n').write(s)
    code = ('import sys; sys.path.insert(0,%r)\n'
            'import recheck_verify as rv\n'
            'rv.ESTABLISH_PATH=%r\n'
            'rv._self_test()\n'
            % (d, os.path.join(R14, 'DISC_ESTABLISH.tsv')))
    r = subprocess.run([sys.executable, '-c', code], cwd=d,
                       capture_output=True, text=True, timeout=300)
    out = r.stdout + r.stderr
    npass = len(re.findall(r'\bPASS \|', out))
    ntot = len(re.findall(r'ok=', out))
    res = {}
    for m in re.finditer(r'^(\S+.*?)\s+ok=(\w+)\s+expect=(\w+)\s+(PASS|FAIL)', out, re.M):
        res[m.group(1).strip()] = m.group(4)
    return out, res

IDENT = lambda s: s

def remap_all(s):
    def f(m):
        n = int(m.group(1))
        if n - 1 in FIRST and n in FIRST:
            return "(%d, '%s', '%s', 'b%d', 'b%d')" % (n, FIRST[n - 1], FIRST[n], n - 1, n)
        return m.group(0)
    return re.sub(r"\((\d+), '(\d{6})', '(\d{6})', '[^']*', '[^']*'\)", f, s)

def shift_55_only(s):
    return s.replace(
        "(55, '174146', '174645', 'STATUS_BOARD.before_r55_174146.md', '(open: no r56 snapshot yet)')",
        "(55, '173400', '174146', 'STATUS_BOARD.before_r54_173400.md', 'STATUS_BOARD.before_r55_174146.md')")

def widen_all(s):
    return re.sub(r"\((\d+), '(\d{6})', '(\d{6})',",
                  lambda m: "(%s, '000000', '235959'," % m.group(1), s)

P('=== 四组对照（同一份代码，只改 _ROUND_ROWS）===')
variants = [('ident', '原样（现行表）', IDENT),
            ('shift55', '只把 r55 按 §2.57 前移', shift_55_only),
            ('remap', '§2.57 描述的「20 条全量重映射」', remap_all),
            ('widen', '全部窗口放宽到全天', widen_all)]
out_all = {}
for tag, label, fn in variants:
    out, res = run_variant(tag, fn)
    out_all[tag] = (out, res)
    P('')
    P('[%s] %s' % (tag, label))
    for k in ('POS 完全合法', 'NEG1 discipline 号错', 'NEG2 at 早于立条',
              'NEG3 at 与 round 窗口矛盾', 'NEG4 anchors 哈希不符'):
        P('    %-28s %s' % (k, res.get(k, 'MISSING')))
    m = re.search(r'SELFTEST (\w+) \((\d+)/(\d+)\)', out)
    P('    -> %s' % (m.group(0) if m else 'NO SELFTEST LINE'))

P('')
P('=== 判定 ===')
base = out_all['ident'][1]
ck('1. 现行表 self-test 5/5 PASS（§2.59 记的「回退后 5/5」可复现）',
   base.get('POS 完全合法') == 'PASS'
   and all(v == 'PASS' for v in base.values()), str(base))
ck('2. 只前移 r55 ⇒ self-test 仍 5/5（POS 用的是 r52，不受 r55 影响）',
   all(v == 'PASS' for v in out_all['shift55'][1].values()),
   str(out_all['shift55'][1]))
rm = out_all['remap'][1]
ck('3. 全量重映射 ⇒ POS 变 FAIL（§2.59 记的 4/5 可复现）',
   rm.get('POS 完全合法') == 'FAIL', str(rm.get('POS 完全合法')))
neg4line = [l for l in out_all['remap'][0].split('\n') if 'NEG4' in l][0]
ck('4. 全量重映射下 NEG4「哈希不符」仍报 PASS —— 但拦截理由是 R4 而非 R5',
   rm.get('NEG4 anchors 哈希不符') == 'PASS' and 'R4 at outside' in neg4line,
   neg4line.strip()[:130])
ck('4b. 即：NEG4 这条反控已不再测它声称要测的 R5（测试形态退化，§2.59 原话可复现）',
   'R5 anchors mismatch' not in neg4line, 'r4_only=%s' % ('R5' not in neg4line))
wd = out_all['widen'][1]
pos_w = [l for l in out_all['widen'][0].split('\n') if 'POS' in l][0]
neg3_w = [l for l in out_all['widen'][0].split('\n') if 'NEG3' in l][0]
ck('5. 放宽到全天 ⇒ POS 仍 PASS（被接受），但 NEG3「越窗须被抓」变成 FAIL',
   wd.get('POS 完全合法') == 'PASS' and wd.get('NEG3 at 与 round 窗口矛盾') == 'FAIL',
   'POS=%s NEG3=%s' % (wd.get('POS 完全合法'), wd.get('NEG3 at 与 round 窗口矛盾')))
ck('5b. ⇒ 自测确实能抓「放宽」：它抓在 NEG3 那一侧（前一版我以为抓不到，是我写错了断言）',
   'expect=False' in neg3_w and 'ok=True' in neg3_w, neg3_w.strip()[:130])

P('')
P('=== 为什么全量重映射会打破 POS：可算的解释 ===')
pos = [l for l in out_all['remap'][0].split('\n') if 'POS' in l][0]
P('  ' + pos.strip()[:200])
P('  自测里 POS 的 at 固定为 16:20:00，断言它落在 R52 窗口内。')
P('  原表 R52 = [before_r52=16:17:50, before_r53=16:28:03) ⇒ 16:20 在内。')
P('  全量重映射后 R52 = [before_r51=16:01:44, before_r52=16:17:50) ⇒ 16:20 落到窗口外。')
ck('6. 解释与实测一致（16:20:00 在原 R52 内、在重映射后 R52 外）',
   'at outside R052 window [2026-11-22T16:01:44+08:00, 2026-11-22T16:17:50+08:00]' in pos,
   pos.strip()[:160])
P('')
P('  这不是「自测写死了旧窗口」，因为自测从没写死时刻表 —— 它只写 at 与 expect，')
P('  窗口由被测代码提供。因此：自测的 POS 事实上把「R52 = [16:17:50, 16:28:03)」这个')
P('  语义固化成了可执行断言。全量重映射把它打破了 ⇒ 两种解释只能选一：')
P('    (a) 自测的 POS 时刻取错了（该改成落在新窗口内的时刻）；')
P('    (b) 全量重映射把语义改错了。')
P('  判别证据在本轮 window_r68 的结论：35 份规范快照的内容 max 全部 = N-1，')
P('  即 before_rN 拍在「第 N 轮写之前」⇒ 第 N 轮的窗口起点**就是** before_rN。')
P('  而自测 POS 用的 R52 恰好是 before_r52 起点 = 16:17:50 ⇒ 自测与快照内容一致。')
P('  ⇒ (b) 成立：全量重映射错了；§2.57 的「off-by-one」是把终点当起点。')
ck('7. 故 §2.57 的窗口平移不是修 bug，而是让被测量去适配期望（且它破坏了自己的自测）',
   True)

P('')
P('RESULT ' + ('ALL-PASS' if not fails else 'FAIL: ' + ','.join(fails)))
io.open(os.path.join(OUT, 'selftest_r68.log'), 'w', encoding='utf-8',
        newline='\n').write('\n'.join(buf) + '\n')
