# -*- coding: utf-8 -*-
"""check_disc.py —— 纪律回跑门禁
R47 落地；R48 装下半截（C7）；R49 关闭 T4 审计查出的 6 处「看似在查、实则永过」。

检查项：
  C1  行数 == R14_COMMON 中「纪律 N ·」正式定义条数
  C1b TSV 必须 LF-only
  C2  纪律号 1..N 连续无缺
  C3  「回跑」列不得空；**且必须是两个闭集合取值之一**（R49 收紧）
  C4  标「有（后续轮回跑）」者，产物路径非空且校验式非 none
  C5  三项 CR 抽查（R14_COMMON=1081 / 看板=0 / 台账=337）
  C6  命名空间：「纪律 N」非规范出现次数超阈值即 FAIL（R49：原为纯 NOTE，永不过）
  C7  逐行真跑校验式（exists / bytes=N / rows=N；R49：exists 改为**比对注解里的字节数**）
  C8  「节」列指向的 ## x.y 必须存在于 R14_COMMON
  C9  【R49 新增】第 3 列判据、第 4 列锚不得为空/占位符（GARBAGE/TBD/xxx/无）
  C10 【R49 新增】门自检：本脚本自身的字节数必须与 DISC_RECHECK.tsv 中登记的「门自身」行一致
       （无该行则 FAIL —— 要求显式登记，关掉「门无门禁」的循环依赖）

退出码：0 全通过；1 有 FAIL。
说明：本脚本**不使用**任何非 ASCII 打印字符（规避 GBK 控制台 UnicodeEncodeError）。
"""
import io, os, re, sys, hashlib, hashlib, json, ast

ROOT = r'D:\Project\ra2-campaign-forge'
if not os.path.isdir(ROOT):                      # R73：POSIX 上按本文件位置反推三层
    ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
R14  = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
RC   = os.path.join(R14, 'R14_COMMON.md')
DR   = os.path.join(R14, 'DISC_RECHECK.tsv')
BRD  = os.path.join(R14, 'STATUS_BOARD.md')
LED  = os.path.join(ROOT, 'lead', 'GOAL_THREE_TARGETS_20261018.md')
SELF = os.path.abspath(__file__)
GATE_VER = 'R166'
FREEZE_SHA256 = '5fc21cfece52f1e44525d9510c4cd2a6a08172c2b134be4686008355c4bf7f61'   # DISC_UNVERIFIABLE.tsv 的 sha256（防静默篡改）

# 阈值（可用命令行覆盖：--c6max=120）
C6MAX = 120
for a in sys.argv[1:]:
    if a.startswith('--c6max='):
        C6MAX = int(a.split('=')[1])

fails, notes = [], []
def read(p): return io.open(p, encoding='utf-8', newline='').read()

rc = read(RC); lines = rc.split('\n')
CANON = re.compile(r'(?:\u21d2\s*)?\*{0,2}\u7eaa\u5f8b\s*(\d+)\s*\u00b7')   # 纪律 N ·
LOOSE = re.compile(r'\u7eaa\u5f8b\s*(\d+)')                                 # 纪律 N
defs, cur = set(), None
for l in lines:
    m = re.match(r'^##\s*(\d+(?:\.\d+)*)', l)
    if m: cur = m.group(1)
    mm = CANON.search(l)
    if mm:
        n = int(mm.group(1))
        if cur and cur.startswith('2.') and float(cur.split('.')[1]) >= 14:
            defs.add(n)

rows = []
if not os.path.exists(DR):
    fails.append('C1 DISC_RECHECK.tsv missing')
else:
    txt = read(DR)
    if '\r' in txt: fails.append('C1b DISC_RECHECK.tsv contains CR (must be LF-only)')
    raw = [l for l in txt.split('\n') if l]
    rows = [l.split('\t') for l in raw[1:]]
    if len(rows) != len(defs):
        fails.append('C1 rows %d != disciplines %d' % (len(rows), len(defs)))
    nums = sorted(int(r[0]) for r in rows if r and r[0].isdigit())
    if nums != sorted(defs):
        fails.append('C2 discipline numbers mismatch: %s vs %s' % (nums, sorted(defs)))

# ---- C3 / C4 / C9 ----
ALLOWED_LATER = ('\u6709', '\u65e0')   # 以「有」或「无」开头
import place_r87 as _P87
_PLACE_IS = _P87.is_placeholder
PLACEHOLDER = ('', '\u65e0', 'GARBAGE', 'TBD', 'xxx', 'XXX', '?', '-')
c3 = c4 = 0
for r in rows:
    if len(r) != 7:
        fails.append('C3 colcount %d (id %s)' % (len(r), r[0] if r else '?')); continue
    later = r[6].strip()
    if not later:
        fails.append('C3 id %s later-column empty' % r[0])
    elif not later.startswith(ALLOWED_LATER):
        fails.append('C3 id %s later-column not in {有,无}: %r' % (r[0], later[:20]))
    else:
        c3 += 1
    if later.startswith('\u6709'):
        if r[4].strip() in ('', '\uff08\u6587\u6863\u5185\u951a\uff09'):
            fails.append('C4 id %s claims recheck but product path empty' % r[0])
        elif r[5].strip() in ('', 'none'):
            fails.append('C4 id %s claims recheck but checkexpr none' % r[0])
        else:
            c4 += 1
    # C9 判据/锚不得为空或占位
    _jp, _jr = _PLACE_IS(r[2].strip())
    _ap_, _ar = _PLACE_IS(r[3].strip())
    if _jp:
        fails.append('C9 id %s judge-column empty/placeholder (%s)' % (r[0], _jr))
    if _ap_:
        fails.append('C9 id %s anchor-column empty/placeholder (%s)' % (r[0], _ar))

# ---- C6 命名空间：只统计「真正在 §2.14+ 之外」的提及，并要求映射表逐条覆盖 ----
# R50 修正：原版用 LOOSE-CANON 之差，把「§2.x 里对我自己纪律的非规范引用」也当成旧命名空间冲突。
# R52 修正：改为**复合引用感知**（「纪律 1/4」含两个号），并与映射表的「计入」行数对齐。
NSMAP = os.path.join(R14, 'DISC_NS_MAP.tsv')
_cur = None
_sec = []
for l in lines:
    m = re.match(r'^##\s*(\d+(?:\.\d+)*)', l)
    if m: _cur = m.group(1)
    _sec.append(_cur)
def _in_mine(s):
    try:
        return bool(s) and s.startswith('2.') and float(s.split('.')[1]) >= 14
    except Exception:
        return False
REF = re.compile(r'\u7eaa\u5f8b\s*(\d+(?:\s*/\s*\d+)*)')
cross = 0
for i, l in enumerate(lines):
    if _in_mine(_sec[i]):
        continue
    for m in REF.finditer(l):
        nums = [x for x in re.split(r'\s*/\s*', m.group(1)) if x]
        if re.search(r'\u7eaa\u5f8b\s*19\s*\u6761', l):
            continue          # 数量修饰，非条号
        cross += len(nums)
notes.append('C6 cross-namespace refs (compound-aware, outside 2.14+) = %d' % cross)
# ---- C6 阈值（R102 接线）：docstring 一直声称「超阈值即 FAIL」，而 C6MAX 此前从未被读（AST 实测 Load=0）。 ----
if cross > C6MAX:
    fails.append('C6 cross-namespace refs %d > threshold %d (--c6max= to raise deliberately)'
                 % (cross, C6MAX))
else:
    notes.append('C6 threshold ok: %d <= %d' % (cross, C6MAX))
if not os.path.exists(NSMAP):
    fails.append('C6 DISC_NS_MAP.tsv missing (old numbering must be mapped, not guessed)')
else:
    mrows = [x for x in read(NSMAP).split('\n') if x]
    body = [r.split('\t') for r in mrows[1:]]
    included = sum(1 for r in body if len(r) > 5 and r[5].strip() == 'INCLUDE')
    if included != cross:
        fails.append('C6 map INCLUDE rows %d != cross-namespace refs %d (must cover every ref)'
                     % (included, cross))
    else:
        notes.append('C6 map INCLUDE rows cover all %d refs (%d total rows, %d excluded)'
                     % (included, len(body), len(body) - included))

# ---- C7 真跑：exists 现在比对注解里的字节数 ----
c7_ok = c7_none = 0
def run_expr(path, expr):
    ap = os.path.join(ROOT, path.replace('\\', '/'))
    if not os.path.isfile(ap): return False, 'FILE_MISSING'
    head = expr.split(' ')[0]
    txt_cache = None
    def get_txt():
        nonlocal txt_cache
        if txt_cache is None:
            txt_cache = io.open(ap, encoding='utf-8', errors='replace').read()
        return txt_cache
    # grep=<regex>  : 至少命中 1 次（内容级、且不受文档增长影响）
    if head.startswith('grep='):
        pat = expr[len('grep='):].strip()
        try:
            n = len(re.findall(pat, get_txt(), re.M))
        except re.error as e:
            return False, 'BAD_REGEX:%s' % e
        return (n >= 1), 'grep hits=%d' % n
    # grepcount=<regex>=<N>
    if head.startswith('grepcount='):
        rest = expr[len('grepcount='):].strip()
        m0 = re.match(r'^(.*)=(\d+)$', rest, re.S)
        if not m0: return False, 'BAD_GREPCOUNT'
        pat, want = m0.group(1), int(m0.group(2))
        try:
            n = len(re.findall(pat, get_txt(), re.M))
        except re.error as e:
            return False, 'BAD_REGEX:%s' % e
        return (n == want), 'grepcount %d vs %d' % (n, want)
    m = re.search(r'[\(\uff08](\d+)\s*B[\)\uff09]', expr)   # ✓(123 B)
    if head == 'exists':
        if m:
            want = int(m.group(1)); got = os.path.getsize(ap)
            return (got == want), 'bytes %d vs %d' % (got, want)
        return False, 'exists-without-size-annotation'
    m2 = re.fullmatch(r'bytes=(\d+)', head)
    if m2:
        return (os.path.getsize(ap) == int(m2.group(1))), 'bytes=%d' % os.path.getsize(ap)
    m3 = re.fullmatch(r'rows=(\d+)', head)
    if m3:
        # R55 修：跳过表头与 DISC_RECHECK 自述行，否则「补凭证」会把 rows 计数 +1 而误 FAIL
        n = 0
        hdr_seen = 0
        with io.open(ap, encoding='utf-8', errors='replace') as f:
            for ln in f:
                s = ln.strip()
                if s.startswith('DISC_RECHECK '):
                    continue
                if hdr_seen == 0:
                    hdr_seen = 1
                    continue
                n += 1
        return (n == int(m3.group(1))), 'rows=%d' % n
    if head == 'none': return None, 'none'
    return False, 'BAD_EXPR:' + head

for r in rows:
    if len(r) != 7: continue
    path, expr = r[4].strip(), r[5].strip()
    if path in ('', '\uff08\u6587\u6863\u5185\u951a\uff09') or expr.startswith('none'):
        c7_none += 1; continue
    ok, detail = run_expr(path, expr)
    if ok is None: c7_none += 1
    elif ok: c7_ok += 1
    else: fails.append('C7 id %s expr %s mismatch (%s)' % (r[0], expr.split(' ')[0], detail))

# ---- C7c 【R134 新增】校验式的结构判据：空文件即真 / 命中数不唯一 的式子不是「检查」----
# R134 承重实测（_r134/r134a_exploit.py，8/8 PASS）：C7b 只把 col6 的**首 token 形态**钉住了，
# 而 col6 的**正则全文**与 col5 的**产物路径**都没有任何检查在读。两条实测漏洞：
#   HOLE A（A2）：把某行 col5 指向另一个同样能满足该式的产物 -> 门禁 exit 0。
#   HOLE B（A3）：给某行 col6 追加一条永真分支（如 grep=...|(?m:^)）-> 门禁 exit 0，
#                 即该行此后**无论产物内容如何都通过**。A3b 用空文件证明那条分支确实永真。
# 这不是「再加一个计数」能修的（R133 已记：普查加计数还是同一维度）。根因是**判据本身**：
# 一个能匹配空串的正则，在任何文件上都命中，它作为「这份产物支持这条纪律」的证据是零信息。
# 故 C7c 改为拒收这类式子：对每个 grep= / grepcount= 行，在**空文件**上跑一次，
# 命中即 FAIL —— 它证明不了任何东西，不该被当作检查存在。
# 边界（如实声明）：C7c 只挡「对内容完全不敏感」，挡不住「对内容敏感但敏感错了地方」；
# 后者由 C7d 的路径指纹承担，两者维度不同、缺一不可。
C7C_EMPTY_NULLABLE = []      # 实测该集合为空，见下
_c7c_bad = []
for r in rows:
    if len(r) != 7: continue
    expr = r[5].strip()
    head = expr.split(' ')[0]
    if head.startswith('grep='):
        pat = expr[len('grep='):].strip()
    else:
        _m7c = re.fullmatch(r'grepcount=(.*)=(\d+)$', expr, re.S)
        pat = _m7c.group(1) if _m7c else None
    if pat is None:
        continue
    try:
        _null_hit = re.search(pat, '', re.M) is not None
    except re.error:
        continue                       # 语法错由 C7 自己报，C7c 不重复计
    if _null_hit:
        _c7c_bad.append(r[0])
if _c7c_bad:
    fails.append('C7c vacuous check expression(s) on ids ' + repr(_c7c_bad[:8])
                 + ': the pattern matches the EMPTY STRING, so it would pass on any file '
                   'and proves nothing about the product. Replace it with a pattern that '
                   'cannot match empty (R134)')
notes.append('C7c vacuity pre-filter: %d regex rows tested against empty string, '
             '%d nullable (pinned 0)' % (sum(1 for r in rows if len(r) == 7 and
                                             r[5].strip().startswith(('grep=', 'grepcount='))),
                                         len(_c7c_bad)))

# ---- C7d 【R134 新增】第 5 列与第 6 列的整表指纹（对象钉，不是计数钉）----
# 为什么必须另加一格：C14 只钉 (col2, col3, col4)，col5/col6 在任何指纹之外，
# 故 HOLE A 那种「换一个同样满足的产物」是全静默的。把 (id, col5, col6) 逐行聚合成
# 一个 sha256 钉住，任何对这两列的改动都必须显式重钉本常量 —— 与 C14 同族、同一手法。
# 边界（如实声明，与纪律 31 / C14 / C16d 同族）：sha 钉只能抬高成本，不能防伪造；
# 同时改表与改常量者仍可过。它的价值是把 col5/col6 从「完全不被钉」变成「改动必被看见」。
C7_TEXT_SHA256 = 'b07f46981eb34a22cd31ceb1b9019b7f3c7718fe69b9e3a348a1fa9fb3bc1d59'
C7_ROW_SHA = {'1': '3bd8f1296faa2b5b7fd2e20363e76264f825a988abec3dc8e7b0c7d898ecbf79', '2': '6b3d25928b9ea324365306391f21168d7d3e284957d4f0ee376a431b46c0b233', '3': '791141f5134b0fadc741ca92d25d54c2633fa14c5a8f3e270a53948fb6bd8dd9', '4': '04522bd92abbd261759037dcd3abb20cdb344eb7452f70000c61de1c1b4af6fc', '5': 'e2650359b2cb6db4ad22207caabf88dabb3c260b899805729cb63aa6049afa93', '6': '1c3eda16b711b4b5d9bc2d8a2c865418add8ee02d3592ce789838395d837197e', '7': 'd4b731366633b4fe2b91a4b8990ac36b1d730e208130f7a3ea54295dc5f04781', '8': '085e4dc29160640a80c1595279b4f50507a683fb01b20422785299740f84b91e', '9': '765ff166b62273cba5a08d1a69057fef00e632768773ff001ebd3ac87e4b562f', '10': '6a803a9389a5f8160c55ca529cbad811a76d94d784eb1731054a4d400ee0557e', '11': 'b80c3d58cb8df7ed267fde46aaaf35caaf079082d8a06339352719cf622d0579', '12': 'b1ca293c585977af8fd48d7c63785fcdeb2a88575ab1c008827e08309bc0c3c1', '13': '4c89128afb2d16dc00e0c2a378c74bf4916d911530bca2b8f28a65e6ed99aa22', '14': '6a348503052a806a2b3459989be2a58066f567292eb2f63f59b698a755f764d2', '15': 'adc80803543ec09040fbb425c8c117f40d1a87d5e85f5fbc3b475c642bbdffc6', '16': '92bacd450df54b06c63133f8a46f54360d27f8aaee2d0372aa114e4cee84d976', '17': '61f073607d461d7415f8d76de536922e7cf5c10ec897ea1cfb8ebdcfda72e716', '18': '945463c31bc8f7b88fb6b92cfc0a104a01b3393113bfc0a0cad519d2c97b19bd', '19': '8f32f05826be040cc24ac9fe09137b1b93dc425c919ad20146fb040a0d49ebf1', '20': 'b4ccd655724f636a899fb457483496d68afbaf1e7f867b41e2a508f9cad55394', '21': 'ad68a5c24394fb293c08dd336283e9c1ffe7c56ca052349b69c4bdf6be0f80ff', '22': 'cf8eb1bd09c06bf06e25208384b58bf14fa9e3cdf366b8ca2a95e9c3c06b03ee', '23': '6500c688c068215f7cfa007ed8f35c3d5cf4bab26b821b7681ceab7d30f92a1c', '24': 'b034a698090af1c6d9de32cb4ad493b14e4386d17fe718ef3c2808e5dfcc6fe5', '25': '4c60e5e491b111c62d925e3bcd4fc258ef9f4a4bf767608d25ae48ebbc0de76e', '26': '207b19e4c796d6b92ec3acd9c0b7c59e41e8625f2361beeee3121ae60205f5a1', '27': 'e11c12663acb17113d3f17da716e1968990f02e2b5b950ce14da9a74bbd1fd5c', '28': 'd11694c1ad038217d1d7043d6f21857ba2978b356ecccbc860912dc215b4df03', '31': '074782d1b6ba50287e448caa8b56676d0a1168335e7e29df7cafa0220cf11c54', '32': '94d99bce1cca88243b1e519f6bff375f96de658eaa9ae8c7bbdb9eb5c156aeda', '33': 'f45c47e13897d0b747f0f7401f0688e56d5f1d166d565826e7359412422654d6'}
_c7d_blob = '\n'.join('%s\t%s\t%s' % (r[0], r[4].strip(), r[5].strip())
                      for r in rows if len(r) == 7)
_c7d_now = hashlib.sha256(_c7d_blob.encode('utf-8')).hexdigest()
if _c7d_now != C7_TEXT_SHA256:
    _c7d_drift = []
    for r in rows:
        if len(r) != 7:
            continue
        _h7 = hashlib.sha256(('%s\t%s\t%s' % (r[0], r[4].strip(), r[5].strip()))
                             .encode('utf-8')).hexdigest()
        if C7_ROW_SHA.get(r[0]) != _h7:
            _c7d_drift.append(r[0])
    fails.append('C7d product/expression table changed: sha256 %s != pinned %s ; drifted ids=%s '
                 '(col5 and col6 are now pinned; re-pin C7_TEXT_SHA256/C7_ROW_SHA deliberately)'
                 % (_c7d_now[:16], C7_TEXT_SHA256[:16], _c7d_drift[:12]))
else:
    notes.append('C7d product/expression fingerprint ok: 31 rows, sha256=%s' % _c7d_now[:16])

# ---- C7b 【R133 新增】形态覆盖普查：31/31 passed 不等于「所有分支形态都被走过了」----
# R132 测得 C7 的 exists / bytes= / none 三个分支在 31 行里各覆盖 0 行；R133 r133g 复测
# 仍是 0/0/0（8/8 PASS），r133h 证明注入一行对应形态会把计数从 0 推到 1（钉有分辨力）。
# 修法不用「为不可达形态硬造产物」——那会制造一条只为过门禁而存在的行。改为把普查本身
# 显式钉住：形态计数一旦漂移就 FAIL，逼下一个人先做裁定再改数据。
C7_SHAPE_PIN = {'grep=': 24, 'grepcount=': 3, 'rows=': 4,
                'exists': 0, 'bytes=': 0, 'none': 0}
c7_shape = dict((_k, 0) for _k in C7_SHAPE_PIN)   # S-226, corrected wording S-225:
# a zero count is ABSENT from a frequency dict, not present-with-value-zero. Seeding every
# pinned shape at 0 is NOT what makes "exists=0" checkable -- the first loop below already
# catches an appearing row via C7_SHAPE_PIN.get(k) != measured, seeding or no seeding.
# What seeding actually fixes is the OPPOSITE bug: without it, loop 2 would report every
# zero-count shape as "vanished from the table entirely", i.e. manufacture three fake
# failures on a healthy table. So the seeding prevents a false alarm, not a false pass.
# (hy4 cross-family audit G2 raised this; lead recomputed and agreed, see _r133/LEAD_v_hy4.json)
for _r in rows:
    if len(_r) != 7:
        continue
    _h = _r[5].strip().split(' ')[0]
    _k = ('none' if _h in ('none', '') else
          'bytes=' if _h.startswith('bytes=') else
          'rows=' if _h.startswith('rows=') else
          'grepcount=' if _h.startswith('grepcount=') else
          'grep=' if _h.startswith('grep=') else
          'exists' if _h == 'exists' else 'BAD:' + _h)
    c7_shape[_k] = c7_shape.get(_k, 0) + 1
c7_shape_pin_ok = True
for _k, _v in sorted(c7_shape.items()):
    if C7_SHAPE_PIN.get(_k) != _v:
        c7_shape_pin_ok = False
        fails.append('C7b shape census drifted: %s=%d but pinned %s '
                     '(a new shape needs a deliberate decision, not a silent addition)'
                     % (_k, _v, C7_SHAPE_PIN.get(_k)))
for _k, _v in sorted(C7_SHAPE_PIN.items()):
    if _k not in c7_shape:
        c7_shape_pin_ok = False
        fails.append('C7b pinned shape %s=%d vanished from the table entirely' % (_k, _v))
# (seeded above, so this loop only fires if a future edit removes the seeding)
notes.append('C7b shape census: %s ; three of six shapes have ZERO rows '
             '(exists/bytes=/none are live code with no data behind them -- 31/31 passed '
             'MUST NOT be read as all shapes exercised)%s'
             % (', '.join('%s=%d' % (k, v) for k, v in sorted(c7_shape.items())),
                '' if c7_shape_pin_ok else ' [DRIFTED]'))

# ---- C8 节号存在性 ----
secs = set(re.findall(r'(?m)^##\s*(\d+(?:\.\d+)*)', rc))
c8_ok = 0
for r in rows:
    if len(r) != 7: continue
    s = r[1].lstrip('\u00a7').strip()
    if s in secs: c8_ok += 1
    else: fails.append('C8 id %s section %r not found in R14_COMMON' % (r[0], r[1]))

# ---- C10 门自检：登记行的版本标记必须与本脚本的 GATE_VER 一致 ----
# 不用字节数（每改一次脚本就要刷新，是忙碌功陷阱）；用版本标记 = 真自检。
c10 = 'not-registered'
for r in rows:
    if len(r) == 7 and r[4].strip().replace('/', '\\').endswith('check_disc.py'):
        m = re.search(r"GATE_VER\s*=\s*'([^']+)'", r[5])
        if not m:
            fails.append('C10 self row must register GATE_VER (e.g. grep=(?m)^GATE_VER = \'R49\')')
        elif m.group(1) != GATE_VER:
            fails.append('C10 self GATE_VER registered %s != actual %s' % (m.group(1), GATE_VER))
        else:
            c10 = 'ok(%s)' % GATE_VER
        break
else:
    fails.append('C10 no row registers check_disc.py (gate has no gate)')


# ---- C11 【R53 新增】第 7 列「是否真回跑」机检（部分落地 + 显式 unverifiable）----
# 现状：0/28 有合规自描述行；12/28 可补；16/28 无自产出机制 ⇒ 显式 unverifiable。
# 规则：col7 以「有」开头者，其产物必须含一条通过 recheck_verify 的自描述行，否则 FAIL。
#       col7 以「无」开头者计入 unverifiable 计数（不 FAIL，但必须在输出里显式可见）。
C11_LANDABLE = {3, 4, 11, 12, 13, 14, 15, 17, 22, 26, 27, 28}
# ---- C11b 【R102 新增】C11_LANDABLE 载重：死常量变成可核的缺口量与钉住 ----
# R102 实测：该常量此前 Load 次数 = 0（纯死代码），且它列的 12 个 id 里有 7 个写着「无」——声明不需要回跑，故永远不可能 FAIL。那 7 行不是「还未补」是「声明不补」。
# 本段不修那 7 行（那是写入变更，须单独一卡），只把缺口显式化并钉住。
C11B_PIN_GAP = [3, 4, 11, 12, 13, 14, 15, 17, 22, 26, 27, 28]
c11b_gap = []
for _r in rows:
    if len(_r) == 7 and _r[0].strip().isdigit() and int(_r[0]) in C11_LANDABLE:
        if not _r[6].strip().startswith('\u6709'):
            c11b_gap.append(int(_r[0]))
c11b_gap = sorted(c11b_gap)
notes.append('C11b loadable-registry: declared=%d rows, gap(claims-none, can never FAIL)=%d ids=%s'
             % (len(C11_LANDABLE), len(c11b_gap), c11b_gap))
if c11b_gap != sorted(C11B_PIN_GAP):
    fails.append('C11b loadable gap drifted: %s != pinned %s (fix the rows, then re-pin deliberately)'
                 % (c11b_gap, sorted(C11B_PIN_GAP)))
C11_FROZEN = set()
_FREEZE = os.path.join(R14, 'DISC_UNVERIFIABLE.tsv')
if os.path.exists(_FREEZE):
    _frows = [x for x in read(_FREEZE).split('\n') if x]
    for _r in _frows[1:]:
        _c = _r.split('\t')
        if _c and _c[0].strip().isdigit():
            C11_FROZEN.add(int(_c[0]))
    _fh = hashlib.sha256(io.open(_FREEZE, 'rb').read()).hexdigest()
    if _fh != FREEZE_SHA256:
        fails.append('C11 frozen-class registry TAMPERED: sha256 %s != registered %s '
                     '(新增/删除不可验证类必须经 Lead 显式改 FREEZE_SHA256)' % (_fh[:16], FREEZE_SHA256[:16]))
    notes.append('C11 frozen-class registry loaded: %d ids %s ; sha256=%s %s'
                 % (len(C11_FROZEN), sorted(C11_FROZEN), _fh[:16],
                    'OK' if _fh == FREEZE_SHA256 else 'TAMPERED'))
else:
    fails.append('C11 frozen-class registry DISC_UNVERIFIABLE.tsv MISSING '
                 '(structurally-unverifiable rows must be registered, not assumed)')

c11_ok = c11_fail = c11_unver = c11_declared = 0
_vmod = None
try:
    sys.path.insert(0, R14)
    import recheck_verify as _vmod
except Exception as _e:
    notes.append('C11 verifier import FAILED: %s' % _e)

for r in rows:
    if len(r) != 7:
        continue
    n = int(r[0]) if r[0].isdigit() else -1
    later = r[6].strip()
    if not later.startswith('有'):
        # R128 真修：claims-none 此前是「声明不补」的免检通道，永不 FAIL。
        # 实测 14 行现状诚实（_r128/r128f_gate_probe.py F2），但无机制阻止有人把
        # 「有」悄悄改成「无」而产物里仍留着自述行。故此处补一条可失败的判据：
        # claims-none 行的产物里不得出现本纪律的自述行。
        _p_none = os.path.join(ROOT, r[4].strip().replace('\\', '/'))
        if os.path.isfile(_p_none):
            try:
                _t_none = io.open(_p_none, encoding='utf-8', errors='replace').read()
            except OSError:
                _t_none = ''
            _hits_none = 0
            for _l_none in _t_none.splitlines():
                if not _l_none.startswith('DISC_RECHECK '):
                    continue
                _m_none = re.search(r'\bdiscipline=(\d+)\b', _l_none)
                if _m_none and int(_m_none.group(1)) == int(r[0]):
                    _hits_none += 1
            if _hits_none > 0:
                c11_fail += 1
                fails.append('C11 id %s claims-none but its product carries %d '
                             'self-description line(s) for this discipline (R128)'
                             % (r[0], _hits_none))
                continue
        # R129 真修：claims-none 的第二道口子。R128 只挡住了「产物里还留着自述行」，
        # 没挡「校验式本身已经不成立」。实测（_r129/r129d_tautology_probe.py，8/8 PASS）
        # 14 条 claims-none 的校验式在真产物上 14/14 成立、在空产物上 0/14 成立 ⇒
        # 接上它零误伤、且有分辨力。判据：claims-none 行的校验式必须真跑通过。
        _e_none = r[5].strip()
        if _e_none not in ('', 'none') and not _e_none.startswith('none'):
            _ok_none, _det_none = run_expr(r[4].strip(), _e_none)
            if _ok_none is not True:
                c11_fail += 1
                fails.append('C11 id %s claims-none but its check expression no longer holds '
                             '(%s) :: %s (R129)' % (r[0], _det_none, _e_none[:40]))
                continue
        c11_unver += 1
        continue
    if _vmod is None:
        fails.append('C11 id %s claims recheck but verifier unavailable' % r[0])
        c11_fail += 1
        continue
    try:
        ok, detail = _vmod.verify_recheck_line(ROOT, r)
    except Exception as e:
        ok, detail = False, 'verifier-error:%s' % e
    if ok:
        # R87-T2: frozen-class self-produced evidence must FAIL
        # 冻结档语义是「结构上不可能自产出凭证」；一旦该档产物出现通过校验
        # 的自述行即违规。旧实现把它计入 ok，等于把违规记成好事。
        if n in C11_FROZEN:
            c11_fail += 1
            fails.append('C11 id %s registered structurally-unverifiable but now '
                         'carries a PASSING self-description line (R87-T2)' % r[0])
            continue
        c11_ok += 1
    elif n in C11_FROZEN:
        # R58：冻結类——在冻结档里，结构性不可验证 ⇒ 不 FAIL，但显式计入
        # ---- R135 真修：此前这里是「入档即 declared」，任何失败理由都走这条路 ----
        # 实测（_r135/r135a_measure.py，M3b 12/12）：12 条冻结行的 verify 失败理由**全部**是
        # R1 line_count_for_discipline_<N>=0，即「产物里一条本纪律自述行都没有」——这正是冻结
        # 档语义（结构上不可能自产出凭证）。但代码并不检查这一点：给产物写一条**半截**自述行
        # （实测 DISC_RECHECK discipline=1 garbage ⇒ 理由 R1 bad_token(no =)）同样落进 declared。
        # 两条路在语义上相反：前者是「结构上没有凭证」，后者是「有凭证但写坏了」——后者是可修的，
        # 修好它就能摘帽（R59 Q2-③ 记过的那条「补一行即摘帽」漏洞的同一个入口）。
        # 故冻结豁免只对「凭证行不存在」成立；其它任何失败理由一律 FAIL。
        _reason = str(detail)
        _absent = re.match(r'^R1 line_count_for_discipline_%d=0\b' % n, _reason) is not None
        if _absent:
            c11_declared += 1
        else:
            c11_fail += 1
            fails.append('C11 id %s frozen-class row failed verification for a reason that is '
                         'NOT "no self-description line exists" (%s): the freeze only exempts '
                         'the structural absence of a credential, not a malformed one (R135)'
                         % (r[0], _reason[:70]))
    else:
        c11_fail += 1
        fails.append('C11 id %s claims recheck but has no valid self-description line (%s)'
                     % (r[0], str(detail)[:70]))
notes.append('C11 col7 machine-check: ok=%d fail=%d frozen-unverifiable=%d claims-none=%d'
             % (c11_ok, c11_fail, c11_declared, c11_unver))

# ---- C12 【R102 新增】冻结档自身可核性：12 行「结构性不可验证」不是免检牌 ----
# R102 实测（_r102/r102a_holes.json）：C11 的 31 行里 26 行不可 FAIL，其中 12 行走冻结档。
# 冻结档一旦被读成「免检名单」，本门禁对它们就只剩 sha256 一个约束 —— 而 sha 是同一代码库
# 里的常量，改锚 + 同步改常量即可无声通过（r102b NC1 实测：坏锚 + 同步 sha，未打补丁的
# 门禁 exit 0）。故 C12 把冻结档第 4 列校验式**真跑一遍**：冻结只豁免「自产出 DISC_RECHECK
# 行」，不豁免「它引用的锚真的存在且可命中」。
c12 = 0
if os.path.exists(_FREEZE):
    _fbody = [x.split('\t') for x in _frows[1:]]
    _claim_ids = set()
    for _r in rows:
        if len(_r) == 7 and _r[6].strip().startswith('\u6709') and _r[0].strip().isdigit():
            _claim_ids.add(int(_r[0]))
    for _c in _fbody:
        if not (_c and _c[0].strip().isdigit()):
            continue
        _id = int(_c[0])
        _fid = 'C12 id %d' % _id
        if len(_c) < 8:
            fails.append('%s frozen row cols=%d (must be 8)' % (_fid, len(_c)))
            continue
        _p, _e, _why, _at = _c[2].strip(), _c[3].strip(), _c[5].strip(), _c[6].strip()
        if _id not in _claim_ids:
            fails.append('%s frozen but not claims-\u6709 in DISC_RECHECK (freeze != escape hatch)'
                         % _fid)
        if not _p or _e in ('', 'none'):
            fails.append('%s frozen row has empty product/expr' % _fid)
        else:
            _ok, _det = run_expr(_p, _e)
            if _ok is not True:
                fails.append('%s frozen anchor does not hold (%s) :: %s' % (_fid, _det, _e[:40]))
            else:
                c12 += 1
        if not _why:
            fails.append('%s frozen reason empty' % _fid)
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}', _at):
            fails.append('%s frozen timestamp not strict ISO8601(+HH:MM): %r' % (_fid, _at))
notes.append('C12 frozen-anchor live-check: %d frozen rows, %d anchors hit' % (len(_fbody), c12))

# ---- C12b 【R135 新增】冻结档是 live 表的**副本**还是**另一个对象**？----
# R135 实测（_r135/r135a_measure.py，M1a..M1d 与 M2a..M2d）：C12 检的是冻结档自己的
# 第 3/4 列，而纪律的「产物路径 / 校验式」在 live 表里是第 5/6 列。两表逐行比对，12 行里
# **4 行不一致**（id 1 / 2 / 9 / 20），且四处全部是「冻结档那份是 live 式的真前缀」——
# 即冻结档持有的是**更松**的式子（例如 live 写 `grep=(?m)^\*\*纪律 1 ·`，冻结档只写
# `grep=(?m)^\*\*纪律`；live 写 `grep=(?m)^GATE_VER = 'R154'`，冻结档只写 `grep=(?m)^GATE_VER`）。
# 后果不是「今天算错」（M2b 实测：按 live 式求值同样 12/12 命中，故当前零误判），而是
# **改 live 式在 C12 上完全静默**（M2d：把 live 式换成永假式，C12 仍报命中）——冻结档成了
# 一份只被自己检查的副本，这与 C7d 修的是同一个病（HOLE A：检查对象可被无声替换）。
# 故 C12b 只做一件事：钉住两表同一性，不一致即 FAIL。冻结档不是独立数据源，它是 live 表的
# 镜像；任何一侧被改都必须同时改另一侧，且两侧都由本判据兜住。
_c12b_bad = []
for _c in (_fbody if os.path.exists(_FREEZE) else []):
    if not (_c and _c[0].strip().isdigit()):
        continue
    _id = int(_c[0])
    _live = None
    for _r in rows:
        if len(_r) == 7 and _r[0].strip() == _c[0].strip():
            _live = _r
            break
    if _live is None:
        _c12b_bad.append((_id, 'missing-in-live-table'))
        continue
    if len(_c) < 8:
        continue                      # 列数不足由 C12 自己报
    _d1 = _c[1].strip() != _live[1].strip()
    _d2 = _c[2].strip() != _live[4].strip()
    _d3 = _c[3].strip() != _live[5].strip()
    if _d1 or _d2 or _d3:
        _c12b_bad.append((_id, 'sec' if _d1 else '', 'path' if _d2 else '', 'expr' if _d3 else ''))
if _c12b_bad:
    fails.append('C12b frozen registry is not a faithful copy of the live table: %s '
                 '(frozen col2/col3/col4 must equal live col2/col5/col6; the registry is a '
                 'mirror, not a second source of truth -- edit both or neither) (R135)'
                 % repr(_c12b_bad[:8]))
else:
    notes.append('C12b frozen registry mirrors the live table: %d/%d rows identical on '
                 '(sec, product, expr)' % (len(_fbody), len(_fbody)))

# ---- C13 【R103 新增】第 2 列「节」必须与纪律号对应，不能只求「存在」 ----
# R103 实测（_r103/r103a_freetext.json）：31 行第 2 列全改成真实存在的 §2.14 ⇒ exit 0。
# C8 只查「该 ## x.y 在 R14_COMMON 里存在」，故把任意行指向任意存在的节都不被看见。
# 严格化可行（零误伤）：从正文反推每个「纪律 N ·」所属的 ## 2.x 节，31/31 行原值都在该集合内。
# 唯一歧义：纪律 1 在正文出现于 2.14（定义）与 2.26（引用），故按**集合成员**判，不按单值。
SEC_DEF = {}
_c13_cur = None
for _l in lines:
    _m13 = re.match(r'^##\s*(\d+(?:\.\d+)*)', _l)
    if _m13:
        _c13_cur = _m13.group(1)
    _mm13 = re.search(r'(?:⇒\s*)?\*{0,2}纪律\s*(\d+)\s*·', _l)
    if _mm13 and _c13_cur and _c13_cur.startswith('2.') and float(_c13_cur.split('.')[1]) >= 14:
        SEC_DEF.setdefault(int(_mm13.group(1)), set()).add(_c13_cur)
c13 = 0
for r in rows:
    if len(r) != 7 or not r[0].strip().isdigit():
        continue
    _n13, _s13 = int(r[0]), r[1].lstrip('§').strip()
    _want13 = SEC_DEF.get(_n13, set())
    if not _want13:
        fails.append('C13 id %d has no 纪律 %d · definition in R14_COMMON (cannot cross-check section)'
                     % (_n13, _n13))
    elif _s13 not in _want13:
        fails.append('C13 id %d section %r != definition section(s) %s (col2 must point at the defining section)'
                     % (_n13, r[1], sorted(_want13)))
    else:
        c13 += 1
notes.append('C13 section-correspondence: %d/%d rows match their definition section' % (c13, len(rows)))

# ---- C14 【R103 新增】第 2/3/4 列自由文本的整表指纹 ----
# R103 实测：第 3 列 31 行全改单字符 x ⇒ exit 0；第 4 列只有 5 行被 R5 的 sha256 看到
# （改全表 col4 的 FAIL 集合恰为 [3,4,22,27,28]），其余 26 行改一字不可见。
# 且 R5 是自洽性检查：同时改 col4 并重写那 5 条自述行的 anchors ⇒ exit 0（M5）。
# 故把 (id, col2, col3, col4) 逐行指纹聚合钉住；任一字符改动即 FAIL 并列出变更 id。
# 边界（如实声明，与纪律 31 同族）：sha 钉只能抬高成本，不能防伪造 —— 同时改表与本常量者仍可过。
# 它的价值是把今天 26 行「完全不被读」变成 31 行「改动必被看见」。
C14_TEXT_SHA256 = 'a740bcc9add4e6073071e5d6b693d213b4711ee2f3df8ab3c1db32e1a153975f'
C14_ROW_SHA = {'1': '975155a4cc793796937a4dd07235a319aeb91f82d034ed89994c8ce13126f2d2', '2': 'ddf02236837ea35cc1ccba7a6847d61ee37c75c4812357ff9dcb71e1efe36769', '3': '97879cafb1a2de25e8c36d044e1e47ff43156e9ff0481f9a46ca7794a61fb8f2', '4': '7abce6808c29cf9ef7eee62caeb85ebecf2537805e26b1ae55a12e21c1c9dc2c', '5': 'af83c382cf85d3069f6ed174506b2dbf55b330224a01971113905c682083d6c1', '6': 'e6389fc807c40a3d37b0cc8fa11120635855be964c5fb5c30061e7c1f0c4a485', '7': 'c64d3d3fc8a3ee93402b48dbde081bd12bc6ff4506c74a4c654a7539b9926cf0', '8': '5aa1cf70b8bcab954e0a085bba64fb28d755faa57cc0edffd9f921652a6b2b76', '9': '36b99c8be128cc28198951687c4067c5c8d06e8cc2975ca241b1747e281f9091', '10': '492785892e386a9f49218aeb991dbc14ef3b4418ee5a0cf882b012e5bb37ccca', '11': '65e1dfb73bb6c937fcf5489a5a7b8eaf95834b47e409f631db52334fcaddedf0', '12': 'ee732dcd91cfe3657eab27aee543bc6a20ef2b02ae1af4c3f21d94054b6744f2', '13': '603f8a65dda4c15bb14df902c4213e9e7fd1e81f21fc3f4d3f288c96ef3a675f', '14': 'bc2f2dd76390e3f919913f8864d126805a4ac5f96caa7050aa5afbde584791d2', '15': 'fa7fda157f675554572a0deb7fd567992159fd7b250d22eb1b900e3f269b6fbc', '16': '94c63079dc9e57d9f972c2a863da0682146e6830723fa265b6b6b3fb6f778ac8', '17': '2d20a5b2133953074351e618531290ef7622e693f27ffed1f6cdf53cb3bc6260', '18': '0780e1f9093f2defb109a00032ba4f076e5630e9481623600a2b40097ec3989b', '19': '1e1f3c949ecc1d0d15cc5bc59732b9a969750700930e3e1ff34156f0879faee6', '20': '279a1035b2c2a8ef59134b1fecaceec15e3bdd34782f41c520b26eae30abc42e', '21': '45f224d29d6b0d52f6a8752aa2a0dbba088221777cd89957390cdf19bbff7c51', '22': '3afbeca10b1839c1b9a551bf19259ae95c057ecce0e93be8f0aadc2f82e75d7f', '23': 'aed93a812e7b20538b61584dcded40b41fdc828541a8cdaba05ac9b6535fe0cf', '24': 'be042cfe886aa1cef48f9a5ab6e874f332842116b5a000984603fff3ba2de422', '25': 'e7d22026fd1fb5240f765c000e2138f171d9c0a6ae6f3d9f4b2a2f3b930910e8', '26': '02603207fc8d87fba0494e7c08b504c8c94e87c268e911b179238a58cfc7368c', '27': '1cdad3536710292933efb098277768f42bd21e1bb4163a23fb1009e5aaf7470b', '28': 'e7783a0e5e7f2fcd7580fb441c917550525e785de78a6d06f4e8555a7889396e', '31': '4acda5272edc789ac2627953f47edde65fdaa5f81dd754c37852f999497d819e', '32': '12ea00b28dc1d4609b492407aca66149392affa33e60b9800324d5357f1198c5', '33': '97fc2b5483135bca516cfd4852982778fa1dc9994193ccc6fa45cc12fa06375a'}
_c14_blob = '\n'.join('%s\t%s\t%s\t%s' % (r[0], r[1], r[2], r[3])
                      for r in rows if len(r) == 7)
_c14_now = hashlib.sha256(_c14_blob.encode('utf-8')).hexdigest()
if _c14_now != C14_TEXT_SHA256:
    _c14_drift = []
    for r in rows:
        if len(r) != 7:
            continue
        _k = r[0]
        _h = hashlib.sha256(('%s\t%s\t%s\t%s' % (r[0], r[1], r[2], r[3])).encode('utf-8')).hexdigest()
        if C14_ROW_SHA.get(_k) != _h:
            _c14_drift.append(_k)
    fails.append('C14 col2/col3/col4 free-text table changed: sha256 %s != pinned %s ; drifted ids=%s '
                 '(re-pin C14_TEXT_SHA256/C14_ROW_SHA deliberately after editing those rows)'
                 % (_c14_now[:16], C14_TEXT_SHA256[:16], _c14_drift[:12]))
else:
    notes.append('C14 free-text table fingerprint ok: 31 rows, sha256=%s' % _c14_now[:16])

# ---- C15 【R103 新增】R14_COMMON 内容的单调下界：整节丢失必须 FAIL ----
# R103 实测（_r103/r103b_loss.json A 组）：删 §2.100..§2.106（7 节 / 74,626 B）⇒ 现门禁 exit 0，
# 且 CRLF 计数 1081→1081 变化量 0 —— C5 的 CR 不变量对丢内容失明，这正是 R102 那次
# 828,603→738,215 B 事故能全绿的结构性原因。C15 只加下界，不动任何行：
# 允许小节内改写、允许正常增节，不允许整节消失、末节号回退、字节数跌破下界。
C15_SECS = [7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106]
C15_LAST = 106
C15_FLOOR_BYTES = 831406
C15_FLOOR_HEAD = 99
_rc15 = rc
_secs15 = [int(x) for x in re.findall(r'(?m)^##\s+2\.(\d+)\b', _rc15.replace('\r\n', '\n'))]
_miss15 = sorted(set(C15_SECS) - set(_secs15))
if _miss15:
    fails.append('C15 R14_COMMON section(s) disappeared: %d missing %s (content loss is NOT allowed; '
                 'if a section was legitimately merged, re-pin C15_SECS deliberately)'
                 % (len(_miss15), _miss15[:12]))
if not _secs15 or max(_secs15) < C15_LAST:
    fails.append('C15 R14_COMMON last 2.x section %s < pinned %d (tail truncation)'
                 % (max(_secs15) if _secs15 else 'none', C15_LAST))
_bytes15 = len(_rc15.encode('utf-8'))
if _bytes15 < C15_FLOOR_BYTES:
    fails.append('C15 R14_COMMON bytes %d < floor %d (lost >= %d B)'
                 % (_bytes15, C15_FLOOR_BYTES, C15_FLOOR_BYTES - _bytes15))
if len(_secs15) < C15_FLOOR_HEAD:
    fails.append('C15 R14_COMMON 2.x headings %d < floor %d' % (len(_secs15), C15_FLOOR_HEAD))
notes.append('C15 content floor: 2.x sections %d (pinned %d), last %s (pinned %d), bytes %d (floor %d)'
             % (len(_secs15), len(C15_SECS), max(_secs15) if _secs15 else 'none', C15_LAST, _bytes15, C15_FLOOR_BYTES))

# ---- C16 (R119 新增) 逐节字节下界：补 C15 的两处结构性缺口 ----
# R119 实测（_r119/r119a_hole.py，8/8 PASS）：
#   缺口一 C15_SECS 硬编码 7..106 共 100 节，而盘上已有 116 节（7..122）⇒ 2.107..2.122 共 16 节、
#     168,835 B（占 2.x 正文 21.7 个百分点）完全不在覆盖集内。沙箱实证：把这 16 节逐节清空成
#     「只剩标题行」，未装 C16 的门禁 16/16 全部 exit 0（整节内容丢失不可见）。
#   缺口二 C15 四条子项都只看总量：覆盖集内连续清空 8 节才跌破 byte floor ⇒ 单节空壳照样过
#     （R115 已证「清空 1 节 ⇒ exit 0」，本轮给出精确节数 8 与逐节字节表）。
# C16 只加下界、不改任何行：每节正文必须 >= 登记下界（= 建表时实测字节的一半），
# 新节（id 不在表里）必须 >= 400 B。允许小节内改写、允许正常增节；不允许「留标题、清正文」。
# 边界（如实声明，与纪律 31 同族）：下界是表里的常量，同改表与常量者仍可过；它的价值是把
# 116 节「完全不被读」变成 116 节「缩到一半必被看见」。
C16_FLOORS = {
    7: 595,
    8: 937,
    9: 1361,
    10: 671,
    11: 385,
    12: 1144,
    13: 923,
    14: 1020,
    15: 812,
    16: 710,
    17: 860,
    18: 1518,
    19: 1006,
    20: 1037,
    21: 710,
    22: 1520,
    23: 991,
    24: 1699,
    25: 1320,
    26: 2660,
    27: 1185,
    28: 1398,
    29: 1283,
    30: 1200,
    31: 1403,
    32: 1103,
    33: 1345,
    34: 1259,
    35: 1294,
    36: 979,
    37: 970,
    38: 1144,
    39: 1066,
    40: 982,
    41: 1143,
    42: 1286,
    43: 1051,
    44: 1298,
    45: 1064,
    46: 870,
    47: 1239,
    48: 992,
    49: 1010,
    50: 1385,
    51: 1104,
    52: 1299,
    53: 903,
    54: 925,
    55: 1169,
    56: 1067,
    57: 992,
    58: 826,
    59: 1281,
    60: 1179,
    61: 1071,
    62: 809,
    63: 933,
    64: 842,
    65: 1172,
    66: 1039,
    67: 922,
    68: 1223,
    69: 908,
    70: 1115,
    71: 1116,
    72: 3440,
    73: 3596,
    74: 1871,
    75: 1616,
    76: 2848,
    77: 2709,
    78: 1884,
    79: 3264,
    80: 1520,
    81: 3460,
    82: 2096,
    83: 1843,
    84: 2318,
    85: 3034,
    86: 1607,
    87: 2508,
    88: 1910,
    89: 2745,
    90: 3120,
    91: 2000,
    92: 1864,
    93: 2044,
    94: 866,
    95: 1295,
    96: 1584,
    97: 2244,
    98: 1437,
    99: 1173,
    100: 1397,
    101: 1595,
    102: 4028,
    103: 2914,
    104: 2985,
    105: 2986,
    106: 2748,
    107: 3312,
    108: 1628,
    109: 1992,
    110: 2381,
    111: 2796,
    112: 2931,
    113: 2827,
    114: 2981,
    115: 2911,
    116: 2214,
    117: 3359,
    118: 2911,
    119: 2857,
    120: 2547,
    121: 1854,
    122: 2701,
    123: 2355,
    124: 2331,
    125: 2018,
    126: 4075,
    127: 3932,
    128: 4001,
    129: 3629,
    130: 3722,
    131: 5958,
    132: 5998,
    133: 4747,
    134: 941,
    135: 3059,
    136: 4444,
    137: 3159,
    138: 4803,
    139: 4118,
    140: 4782,
    141: 2548,
    142: 3404,
    143: 3039,
    144: 4010,
    145: 2372,
    146: 8400,
    147: 2200,
    148: 8403,
    149: 9026,
    150: 8600,
    151: 10384,
    152: 6702,
    153: 9662,
    154: 6373,
    155: 10813,
    156: 5873,
    157: 4596,
    158: 2329,
    159: 3198,
    160: 3349,
    161: 5150,
    162: 4867,
    163: 5671,
    164: 9748,
    165: 3477,
    166: 3076,
    167: 7223,
    168: 4462,
    169: 5331,
    170: 6818,
    171: 5966,
    172: 3362,
    173: 6282,
    174: 4012,
    175: 3353,
    176: 2777,
    177: 3329,
    178: 3653,
    179: 4939,
    180: 4540,
   181: 4213,
   182: 3488,
   183: 4344,
   184: 3637,
   185: 3910,
   186: 3512,
}
# 🐞 自错 S-61（成对回归 E5 当场抓出）：初稿给**新节**也设了 400 B 下限，
# 于是「追加一个合法的短新节」被误判 FAIL —— 这是把「不许清空」误扩成「不许写短」。
# 新节不是被钉对象（C15 已保证 7..106 存在、末节号不回退），故新节不设下限。
C16_FLOORS_SHA256 = '70f66602ba9a2905c4f174429d3fa8e07a523893aa9510a6565df59ed29ab0d3'   # 上表的 sha256（逐 id:floor 规范化）；审计 R119 ③ 成立：
# 无摘要时「同改表与常量」只需把一个十进制数改小，diff 与正常重钉无法区分；加钉后至少要改这个 64 hex。
C16_NEW_MIN = 0
# C16b：表外新节不设字节下限 ⇒ 若不加约束，「每轮新增一节」就等于「每轮白得一张永久免检票」，
# 与本门禁历史上被咬过的「claims-无 即免检」同构（R68 CW8 ③）。故给未钉节数设上限：
# 超过 C16_UNPINNED_MAX 必须由 Lead 显式重钉 C16_FLOORS（把新节也纳进来）。
C16_UNPINNED_MAX = 2
_c16_b = []
b16_lines = {}
_cur16 = None
_buf16 = []
for _l in rc.split('\n'):
    _m16 = re.match(r'^##\s+2\.(\d+)\b', _l)
    if _m16:
        if _cur16 is not None:
            _c16_b.append((_cur16, len('\n'.join(_buf16).encode('utf-8'))))
            b16_lines[_cur16] = _buf16
        _cur16 = int(_m16.group(1))
        _buf16 = [_l]
    elif _cur16 is not None:
        _buf16.append(_l)
if _cur16 is not None:
    _c16_b.append((_cur16, len('\n'.join(_buf16).encode('utf-8'))))
    b16_lines[_cur16] = _buf16
_c16_seen = set()
# 审计 R119 ③ 成立：无钉时「把某节 floor 改小 1 个数」与正常重钉在 diff 上不可区分。
# 加 sha 钉：表内容（逐 id:floor 规范化串）必须与 C16_FLOORS_SHA256 一致，否则 FAIL。
_c16_norm = '\n'.join('%d:%d' % (k, C16_FLOORS[k]) for k in sorted(C16_FLOORS))
_c16_sha = hashlib.sha256(_c16_norm.encode('utf-8')).hexdigest()
if _c16_sha != C16_FLOORS_SHA256:
    fails.append('C16d floor table TAMPERED: sha256 ' + _c16_sha[:16] + ' != registered '
                 + C16_FLOORS_SHA256[:16] + ' (editing a single floor requires re-pinning this '
                   'constant deliberately; that is the point)')
notes.append('C16d floor-table pin: ' + _c16_sha[:16] + ' ('
             + ('OK' if _c16_sha == C16_FLOORS_SHA256 else 'TAMPERED') + ')')
_c16_bad = []
for _n16, _sz16 in _c16_b:
    _c16_seen.add(_n16)
    _want16 = C16_FLOORS.get(_n16, C16_NEW_MIN)
    if _sz16 < _want16:
        _c16_bad.append((_n16, _sz16, _want16))
if _c16_bad:
    fails.append('C16 section(s) hollowed out (body below per-section floor): ' + repr(_c16_bad[:8])
                 + ' (a section must not lose more than half its pinned body; if a section '
                   'legitimately shrank, re-pin C16_FLOORS deliberately)')
_miss16 = sorted(set(C16_FLOORS) - _c16_seen)
if _miss16:
    fails.append('C16 R14_COMMON section(s) gone: ' + str(len(_miss16)) + ' missing '
                 + repr(_miss16[:12]) + ' (deleting a whole section is never a valid edit)')
_unp16 = sorted(_c16_seen - set(C16_FLOORS))
# 审计 R119 ② 成立：表外新节只受「张数上限 2」约束、票上没有内容约束 ⇒ 一个「只有标题行」的空壳
# 新节永远不被看见。修法：表外新节必须至少有 1 行正文（非空、非标题）。实测现有 116 节的正文
# 行数最少为 6（2.11）⇒ 该约束不会误伤任何正常短节（_r119/r119g_audit.py A2b）。
_c16_shell = []
for _n16 in _unp16:
    _ls = [x for x in b16_lines.get(_n16, []) if x.strip() and not x.lstrip().startswith('#')]
    if not _ls:
        _c16_shell.append(_n16)
if _c16_shell:
    fails.append('C16c unpinned section(s) with no body text: ' + repr(_c16_shell[:8])
                 + ' (a new section must carry at least one non-empty, non-heading line; '
                   'a title-only shell is not a section)')
if len(_unp16) > C16_UNPINNED_MAX:
    fails.append('C16b unpinned sections ' + str(len(_unp16)) + ' > ' + str(C16_UNPINNED_MAX)
                 + ' (ids ' + repr(_unp16[:8]) + '): new sections must be pinned into '
                   'C16_FLOORS deliberately, otherwise each new section silently acquires '
                   'a permanent no-check ticket (same shape as claims-none)')
_marg16 = [_sz16 - C16_FLOORS.get(_n16, C16_NEW_MIN) for _n16, _sz16 in _c16_b]
notes.append('C16 per-section floors: ' + str(len(_c16_b)) + ' sections measured (pinned '
             + str(len(C16_FLOORS)) + '), hollow/deficient ' + str(len(_c16_bad))
             + ', missing ' + str(len(_miss16)) + ', unpinned ' + str(len(_unp16))
             + ', min margin '
             + (str(min(_marg16)) if _marg16 else 'n/a'))

# ---- C17 (R120 新增) C11 的五条「ok」到底是真回跑还是跨轮复制？----
# R120 实测（_r120/r120a_anachrony.py，9/9 PASS）：C11 只校验自述行的**跨字段自洽**
# （discipline/round/at/anchors 与 DISC_ESTABLISH 上界、ROUND_WINDOWS 窗口一致），
# 但**从不校验这条行所在的产物在它声称的那一刻是否可能存在**。两个互不共用字节的量：
#   量一 路径轮次：产物路径里的 R<n> token 是「它所在轮次」的下界。声称轮次 < 路径轮次
#        ⇒ 该行不可能由它声称的轮次产出。5/5 命中（3/4 在 R61、22 在 R84、27 在 R81、28 在 R88
#        的产物里，全都声称 R55）。
#   量二 时刻复用：同一 at 秒值出现在 4 个不同轮次目录的产物里。真回跑是本轮为**本轮**产物
#        各写一条，不可能让 3 个不同轮次的产物共享同一秒；只有复制粘贴会产生该复用。
# 且这与 R90 的结论独立得出（R90 用派发卡 mtime 当外部时钟，本段不用任何 mtime）。
# C17 只在**表这一层**加两道：C17a 时间不可能性、C17b 跨轮复用；
# 它们不改任何自述行（那是裁定，须单独裁），只把「已存在的 5 条不可能行」钉住，
# 使「悄悄把它们改成诚实行」或「再添一条同类行」都必须显式改本段的常量。
# R129 裁定（_r129/r129i_ruling_design.py 12/12 PASS）：这五条已从「声称有」降级成「无」，
# 自述行本身仍留在原产物里（不删别人的产物），但第 7 列不再声称它们回跑过 ⇒ C17 扫不到它们。
# 故集合由 5 条塌成 0 条。空集不是「关掉检查」：判据仍是「实测集合必须等于这个集合」，
# 只要有人再写一条时间上不可能的自述行并声称有，集合就 ≠ 空集 ⇒ FAIL。
C17_PIN = set()
C17_PIN_SHA256 = 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'
C17_REUSED_ATS = {}   # R129：五条假声称已撤回，复用随之消失（重钉见 _r129/r129k）   # at -> 复用的不同轮次目录数（下限）
_PATHR = re.compile(r'(?:^|[/\\])R(?:17_)?R?(\d+)_')
_LINERE = re.compile(r'^DISC_RECHECK discipline=(\d+) round=(R\d+) at=(\S+) '
                     r'anchors=(sha256:[0-9a-f]{64}) conclusion=(\S+?)\r?$')
_c17_imposs, _c17_atmap, _c17_checked = [], {}, 0
for _r in rows:
    if len(_r) != 7 or not _r[0].strip().isdigit():
        continue
    if not _r[6].strip().startswith('\u6709'):
        continue
    _p17 = _r[4].strip()
    _prs = sorted(set(int(m.group(1)) for m in _PATHR.finditer(_p17.replace('\\', '/'))))
    if not _prs:
        continue
    _ap17 = os.path.join(ROOT, _p17.replace('\\', '/'))
    if not os.path.isfile(_ap17):
        continue
    try:
        _txt17 = io.open(_ap17, encoding='utf-8', errors='replace').read()
    except OSError:
        continue
    for _l17 in _txt17.splitlines():
        _m17 = _LINERE.match(_l17)
        if not _m17 or int(_m17.group(1)) != int(_r[0]):
            continue
        _c17_checked += 1
        _rn17 = int(_m17.group(2)[1:])
        _at17 = _m17.group(3)
        if _rn17 < min(_prs):
            _c17_imposs.append((int(_r[0]), _rn17, _at17))
        _c17_atmap.setdefault(_at17, set()).add(tuple(_prs))
_c17_imposs = sorted(_c17_imposs)
_c17_reuse = {k: len(v) for k, v in _c17_atmap.items() if len(v) > 1}
_c17_pin_now = '\n'.join('%d|%d|%s' % t for t in _c17_imposs)
_c17_pin_sha = hashlib.sha256(_c17_pin_now.encode('utf-8')).hexdigest()
if set(_c17_imposs) != C17_PIN:
    fails.append('C17a 时间上不可能的自述行集合变了：实测 %s != 钉住 %s '
                 '(adding or silently fixing such a row must be a deliberate re-pin)'
                 % (repr(_c17_imposs[:8]), repr(sorted(C17_PIN)[:8])))
if _c17_pin_sha != C17_PIN_SHA256:
    fails.append('C17a pin TAMPERED: sha256 %s != registered %s'
                 % (_c17_pin_sha[:16], C17_PIN_SHA256[:16]))
for _at17, _n17 in C17_REUSED_ATS.items():
    if _c17_reuse.get(_at17, 0) < _n17:
        fails.append('C17b at=%s 的跨轮复用数降到 %d (< pinned %d)：要么真回跑补了行，'
                     '要么行被删 —— 两者都必须显式改 C17_REUSED_ATS'
                     % (_at17, _c17_reuse.get(_at17, 0), _n17))
_bad17 = {k: v for k, v in _c17_reuse.items() if k not in C17_REUSED_ATS}
if _bad17:
    fails.append('C17b 出现新的跨轮复用 at 值 %s（同一秒值落在多个轮次目录 = 复制粘贴特征）'
                 % repr(sorted(_bad17)[:4]))

# ---- C18 【R131 新增】C17 空转的机检：checked=0 不许是「静默的 0」----
# R131 实测（_r131/r131p_c17vac.py 8 项 + _r131/r131s_closings.py 9 项）：
#   C17 只扫 col7 以「有」开头的行；那 12 行恰好 == DISC_UNVERIFIABLE.tsv 的 12 行；
#   而冻结档的语义就是「结构上不可能自产出凭证行」。于是 C17 的输入集按定义不可能含
#   任何自述行 ⇒ checked 恒 0。C11 同理：19 claims-none + 12 frozen = 31，无一能到 ok。
# 这不是「恰好没有」，是「构造上不可能有」。若不把它变成可失败的判据，它就是一张永久
# 免检票 —— 与本仓被咬过多次的「claims-无 即免检」同构（R68 CW8 ③、R102 C11b）。
# 判据不是「要求 checked>0」（那要求真回跑，是业务动作，做不到也不该伪造），
# 而是：空转必须**被显式登记**，且一旦空转消失（有人真补了行）就必须显式改本常量。
# 三个量都是实测值，不是手填。
C18_VACUOUS = {
    'c17_checked': 0,        # C17 实际扫过的自述行数
    'c11_ok': 0,             # C11 实际通过的 claims-有 行数
    'claims_you_rows': 12,   # 声称「有」的行数
    'frozen_rows': 12,       # 冻结档行数
    'claims_none_rows': 19,  # 声称「无」的行数
}
_c18_now = {'c17_checked': _c17_checked, 'c11_ok': c11_ok,
            'claims_you_rows': sum(1 for _r in rows
                                   if len(_r) == 7 and _r[6].strip().startswith('有')),
            'frozen_rows': len(C11_FROZEN),
            'claims_none_rows': c11_unver}
for _k18, _want18 in C18_VACUOUS.items():
    if _c18_now[_k18] != _want18:
        fails.append('C18 vacuity pin drifted: %s = %d != pinned %d (if a real DISC_RECHECK '
                     'line was produced, this is good news -- re-pin C18_VACUOUS deliberately; '
                     'do NOT let the count move silently)'
                     % (_k18, _c18_now[_k18], _want18))
# 结构判据：空转的根因是「claims-有 集合」与「冻结档集合」完全相同。
# 若两者不再相同，空转已被真修，本常量必须重钉（上面那条会先 FAIL）；这条把因果也钉住，
# 防止有人只改上面的数字而留下一个仍然恒真的空转。
_c18_you = set(int(_r[0]) for _r in rows
               if len(_r) == 7 and _r[0].strip().isdigit() and _r[6].strip().startswith('有'))
if _c18_you != C11_FROZEN:
    fails.append('C18 vacuity cause changed: claims-有 set %s != frozen set %s '
                 '(the two being equal is exactly why C11 ok and C17 checked are both 0; '
                 'if they diverged, re-derive C18_VACUOUS from measurement)'
                 % (repr(sorted(_c18_you)[:8]), repr(sorted(C11_FROZEN)[:8])))
notes.append('C18 vacuity: C17 checked=%d, C11 ok=%d pinned (claims-有==frozen==%d, '
             'claims-none=%d) -- zero is STRUCTURAL, not incidental'
             % (_c17_checked, c11_ok, len(C11_FROZEN), c11_unver))

notes.append('C17 self-produced-line anachrony: checked=%d impossible=%d (pinned %d), '
             'reused-at=%s, pin=%s'
             % (_c17_checked, len(_c17_imposs), len(C17_PIN),
                json.dumps(_c17_reuse, ensure_ascii=False) if False else repr(_c17_reuse),
                _c17_pin_sha[:16]))

# ---- C19 [R181 新增] 事实层联动：主门禁必须看见事实层与当前版指针 ----
# 存在理由（实测）：R181 两次独立计数（_r180/r180a、_r181/r181a，正控在 gate_runner.py 上
# 得 14/5/0）测得本脚本对 facts_floors / FACT_INDEX / FACT_INDEX_CURRENT 的子串出现各 0；
# 且把 FACT_INDEX.tsv 的 F24 grade 由 [已证] 改成 [流程] 后以副本路径跑本脚本仍 exit 0,
# 而 facts_floors.py 同一改动 exit 1 且 D5 点名 —— 主门禁完全看不见事实层。
#
# 判据的**靶子路径一律由指针解析**，本块不硬编码任何版本号：
#   若硬编码 R17_R131_FACTINDEX_V563，而纪律规定「历史版本一律保留不删不改」，
#   则升版到 V564 之后 V563 那份文件仍在盘上且字节与 sha 都不变 ⇒ 判据永远通过。
#   这种「钉住一个永不变化的僵尸快照」与 C7b/C11b/C18 抓的恒真子项同型，且更坏：
#   现状至少没人误以为台账被检查过。故 v2 改为 pointer-driven。
# 判据：
#   (a) 指针「相对路径」字段解析出的绝对路径必须存在
#   (b) 该路径实测 sha256 == 指针「sha256」字段
#   (c) 该路径实测字节数 == 指针「字节数」字段
#   (d) 指针「版本目录」字段 == 该路径所在目录名
#   (e) facts_floors.py 的 EXPECT_CUR 必须解析到同一个绝对路径（抓「两门各查各的版本」）
#   (f) facts_floors.py 的 CUR_SHA256 / TOTAL_BYTES 必须等于该路径的实测 sha / 字节数
# 读不到或解析不出 → FAIL（不得因读不到而跳过，与 facts_floors D10 同纪律）。
C19_FACTS = os.path.join(ROOT, '_r160', 'facts_floors.py')
C19_PTR = os.path.join(R14, 'FACT_INDEX_CURRENT.md')

def _c19_consts(p):
    tree = ast.parse(io.open(p, encoding='utf-8').read())
    out = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            t = node.targets[0]
            if isinstance(t, ast.Name) and isinstance(node.value, ast.Constant):
                out[t.id] = node.value.value
    return out

def _c19_eval_expect_cur(p):
    """取 facts_floors.py 里 EXPECT_CUR 的值，**不执行该文件**。

    它是 os.path.join(TIER, 'DIR', 'FACT_INDEX.tsv') 形式（Call，不是 Constant），
    故 ast 顶层常量表取不到。这里只按词法解析这一行，支持两种写法：
      1) os.path.join(<TIER 名>, 'DIR', 'FILE')  —— 把 TIER 名换成 tier 实际路径
      2) 字面量字符串
    解析不出返回 None（调用方 FAIL，不得跳过）。
    S-678：首版想 exec 该文件的常量区，但常量与主体之间没有可停的分界（首个 print 在 332 行，
    D0..D10 的副作用在此之前已发生）⇒ 执行他人门禁脚本不是一个可接受的做法，改为词法解析。
    """
    txt = io.open(p, encoding='utf-8', newline='').read()
    m = re.search(r'^([A-Z_][A-Z0-9_]*)\s*=\s*os\.path\.join\(\s*TIER\s*,\s*'
                  r"'([^']+)'\s*,\s*'([^']+)'\s*\)", txt, re.M)
    if m:
        # S-680：本文件里 tier 路径的变量名是 R14，不是 TIER（TIER 是 facts_floors.py 的叫法）
        return os.path.join(R14, m.group(2), m.group(3))
    # S-679：首版在这里写了同时含单双引号的字符类，在块里引号层数错
    # ⇒ 整个 BLOCK 语法错。改用 chr() 拼引号，块内不再出现裸引号字符类。
    _Q = chr(34) + chr(39)
    m = re.search(r'^(?:EXPECT_CUR|CUR)\s*=\s*TIER\s*/\s*(\S+)', txt, re.M)
    if m:
        return os.path.join(R14, m.group(1).strip().strip(_Q))
    m = re.search(r'^EXPECT_CUR\s*=\s*[rbu]?(\S+)', txt, re.M)
    if m:
        v = m.group(1).strip().strip(_Q)
        return v if os.path.isabs(v) else os.path.join(ROOT, v)
    return None

_c19 = 'not-run'
# R182（采纳审计 #435 的 B3）：C20 需要区分「指针坏了」与「C19 根本没跑到」。
# 此前用 locals().get('_c19_abs') 取，两者同为 None ⇒ FAIL 文本不可区分。
_c19_abs = None
_c19_ptr_state = 'not-run'
if not os.path.exists(C19_PTR):
    _c19_ptr_state = 'pointer-missing'
    fails.append('C19 pointer file missing: %s (the pointer is what declares the current '
                 'ledger; absent means the fact layer is unanchored, not "nothing to check")'
                 % C19_PTR)
elif not os.path.exists(C19_FACTS):
    fails.append('C19 facts_floors.py missing: %s' % C19_FACTS)
else:
    _c19_pt = io.open(C19_PTR, encoding='utf-8', newline='').read()
    _c19_ms = re.search(r'\| sha256 \| ([0-9a-f]{64}) \|', _c19_pt)
    _c19_mb = re.search(r'\| 字节数 \| (\d+) \|', _c19_pt)
    _c19_md = re.search(r'\| 版本目录 \| (\S+) \|', _c19_pt)
    _c19_mp = re.search(r'\| 相对路径 \| (\S+) \|', _c19_pt)
    if not (_c19_ms and _c19_mb and _c19_md and _c19_mp):
        _c19_ptr_state = 'fields-unparseable'
        fails.append('C19 pointer fields unparseable (sha=%r bytes=%r dir=%r relpath=%r)'
                     % (bool(_c19_ms), bool(_c19_mb), bool(_c19_md), bool(_c19_mp)))
    else:
        _c19_rel = _c19_mp.group(1).replace('\\', '/').strip()
        _c19_abs = os.path.join(ROOT, _c19_rel)
        if not os.path.exists(_c19_abs):
            _c19_ptr_state = 'path-missing'
            fails.append('C19 pointer relative path does not exist: %r -> %r '
                         '(pointer names a version that is not on disk)' % (_c19_rel, _c19_abs))
        else:
            _c19_raw = open(_c19_abs, 'rb').read()
            _c19_sha = hashlib.sha256(_c19_raw).hexdigest()
            _c19_len = len(_c19_raw)
            if _c19_ms.group(1) != _c19_sha:
                fails.append('C19 pointer sha %s != on-disk sha %s of %r'
                             % (_c19_ms.group(1), _c19_sha, _c19_rel))
            if int(_c19_mb.group(1)) != _c19_len:
                fails.append('C19 pointer bytes %s != on-disk bytes %d of %r'
                             % (_c19_mb.group(1), _c19_len, _c19_rel))
            _c19_dir = os.path.basename(os.path.dirname(_c19_abs))
            if _c19_md.group(1) != _c19_dir:
                fails.append('C19 pointer version dir %r != actual dir %r of the declared '
                             'relative path (the two pointer fields disagree)'
                             % (_c19_md.group(1), _c19_dir))
            try:
                _c19_k = _c19_consts(C19_FACTS)
            except Exception as e:
                _c19_k = None
                fails.append('C19 facts_floors.py unparseable (%s): cannot verify the link' % e)
            if _c19_k is not None:
                # S-677：首版用 ast 的「顶层 Assign + Constant」取 EXPECT_CUR，而它是
                # os.path.join(TIER, 'R17_R131_FACTINDEX_V563', 'FACT_INDEX.tsv') —— 是 Call
                # 不是 Constant ⇒ 取不到，于是 v2 在**正常盘面**上也 FAIL（假 FAIL）。
                # 改为直接 exec facts_floors.py 的**常量区**（import 会跑整条门禁，不行），
                # 用「把 os.path 换成可控桩 + 执行到第一个 print 之前」的方式求值真路径。
                _c19_exp = _c19_eval_expect_cur(C19_FACTS)
                if not _c19_exp:
                    fails.append('C19 cannot resolve EXPECT_CUR in facts_floors.py '
                                 '(the fact gate must declare which file it targets)')
                else:
                    if os.path.normpath(_c19_exp) != os.path.normpath(_c19_abs):
                        fails.append('C19 fact gate targets a different file than the pointer: '
                                     'EXPECT_CUR=%r vs pointer=%r (two gates checking two '
                                     'different versions both report green)'
                                     % (_c19_exp, _c19_abs))
                for _c19_nm, _c19_val, _c19_real in (
                        ('CUR_SHA256', _c19_k.get('CUR_SHA256'), _c19_sha),
                        ('TOTAL_BYTES', _c19_k.get('TOTAL_BYTES'), _c19_len)):
                    if _c19_nm not in _c19_k:
                        fails.append('C19 facts_floors.py lacks %s literal' % _c19_nm)
                    elif _c19_val != _c19_real:
                        fails.append('C19 facts %s %r != on-disk %r of %r'
                                     % (_c19_nm, _c19_val, _c19_real, _c19_rel))
                if not [x for x in fails if x.startswith('C19')]:
                    _c19 = 'ok(%s/%d/%s)' % (_c19_sha[:8], _c19_len, _c19_dir)
                    _c19_ptr_state = 'ok'
                    notes.append('C19 fact-layer link (pointer-driven): %r sha %s bytes %d ; '
                                 'facts_floors EXPECT_CUR/CUR_SHA256/TOTAL_BYTES all agree'
                                 % (_c19_rel, _c19_sha[:8], _c19_len))
                else:
                    _c19 = 'FAIL'
                    _c19_ptr_state = 'content-mismatch'


# ---- C20 [R182 新增] 三方路径一致性：gate_runner / facts_floors / 指针必须指同一份台账 ----
# 存在理由（实测）：R181 把它登记为未取得项 —— gate_runner.py 第 51 行写
#   LEDGER = os.path.join(TIER, '<版本目录>', 'FACT_INDEX.tsv')
# facts_floors.py 第 46 行写同形状的 EXPECT_CUR，指针文件第三行写同一相对路径。
# 三处**各自独立**（_r182/r182b T1：本脚本生效字面量 0、facts 1、gate_runner 1），
# 而 C19 的 (e) 只比对后两者 ⇒ gate_runner 那一份从未被告知。
# 实测分辨率（_r182/r182b T3）：沙箱把 gate_runner.LEDGER 改成上一版，本脚本基线仍 exit 0
# 且无任何 C20 条目 ⇒ 现状是「三份常量各写各的、无人守同一性」，不是「已有人守」。
#
# 判据（全部从盘上现算；本块内**不存任何版本号常量**，注释里也不留可粘贴的版本字面量）：
#   (a) gate_runner.py 存在，且其顶层 LEDGER 赋值可由 **AST** 解析出 os.path.join 的实参
#       —— 或用 import 形态（from facts_floors import EXPECT_CUR as LEDGER）声明同源。
#   (b) 解析出的绝对路径必须 == 指针「相对路径」解析出的绝对路径
#   (c) 解析出的绝对路径必须 == facts_floors.EXPECT_CUR 解析出的绝对路径
#   (d) gate_runner.py 里指向台账版本目录的**字面量集合大小必须 == 1**
#       （换名 LEDGER2 / 裸字面量 / 函数内夹具 都算第二份；import 形态视为同源、不计）
#   (e) 文件缺失 / 解析不出 / 常量缺失 → FAIL，不跳过
#
# 为什么用 AST 而不是正则（R182 审计 #435 的 B1/B6，主会话 _r182/r182g 19 断言复算成立）：
#   v1 的词法判据在六种**完全合法**的写法上假 FAIL：双引号、类型注解、pathlib、变量间接、
#   字符串拼接、以及 from facts_floors import EXPECT_CUR as LEDGER —— 最后一种恰恰是
#   「消灭第三份常量」的终局重构，却被判成「未能声明」。AST 只收 Constant 节点，
#   天然忽略注释与 docstring（本文件 docstring 与 ck 名称里残留旧版本字样，正则必假 FAIL）。
#
# **边界（R182 改诚实，替代 v1 那句「由 D0 与 C19 负责」）**：C20 只证三处指向同一绝对路径。
# 至于「那份是否**当前版**」，本系统**无人覆盖** —— C19 的 (a)(b)(c)、facts_floors 的
# D0/D10 都以「指针已声明的那份」为输入做自洽校验；要回答「是不是最新」必须反向枚举
# 版本目录族，而三份源码对 os.listdir 版本目录的调用次数实测均为 0。故
# 「建了新版本目录却忘记改指针」是本体系的**已知盲区**（_r182/r182g D1–D3 沙箱实测：
# 建一个更高版本号的目录（复制现版台账）但不改任何指针 ⇒ check_disc exit 0、C19 与 C20 均报 ok、零告警），
# 登记为未取得项，**不以 C20 的绿色代表已覆盖**。
C20_GR = os.path.join(ROOT, '_r161', 'gate_runner.py')
C20_VDIR_RE = r'R17_R\d+_FACTINDEX_V\d+'

def _c20_ast_ledger(txt):
    """取 gate_runner.py 顶层 LEDGER 的 os.path.join 实参（只认 Constant）。
    返回 (dir_str, file_str) / None。用 AST.Module.body 只看顶层，函数内夹具不计。"""
    tree = ast.parse(txt)
    for node in tree.body:
        if not (isinstance(node, ast.Assign) and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id == 'LEDGER'):
            continue
        v = node.value
        if (isinstance(v, ast.Call) and isinstance(v.func, ast.Attribute)
                and v.func.attr == 'join'):
            vals = [a.value for a in v.args if isinstance(a, ast.Constant)]
            # S-182h1：os.path.join(TIER, VDIR, FILE) 的 Constant 实参只有 2 个
            # （TIER 是 ast.Name 不是 Constant）。首版写 >= 3 ⇒ 恒返回 None ⇒ 生产假红。
            if len(vals) >= 2:
                return vals[-2], vals[-1]
        # LEDGER = EXPECT_CUR（同源别名）等形态 → 交给 import 分支或失败分支
        return None
    return None

def _c20_vdir_literals(txt):
    """全文件（含函数体）所有 os.path.join 实参里形如台账版本目录的 Constant 集合。"""
    out = set()
    for node in ast.walk(ast.parse(txt)):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr == 'join'):
            for a in node.args:
                if isinstance(a, ast.Constant) and isinstance(a.value, str) \
                        and re.fullmatch(C20_VDIR_RE, a.value):
                    out.add(a.value)
    return out

def _c20_imports_same(txt):
    """gate_runner 是否以 import 形态声明同源（单源、零副本）。"""
    return re.search(r'^from\s+facts_floors\s+import\s+[^\n]*\bEXPECT_CUR\b[^\n]*\bas\s+LEDGER\b',
                     txt, re.M) is not None

_c20 = 'not-run'
if not os.path.exists(C20_GR):
    fails.append('C20 gate_runner.py missing: %s (the third copy of the ledger path is the one '
                 'this check exists for; absent means the three-way link is unverifiable, not '
                 '"nothing to check")' % C20_GR)
else:
    _c20_txt = io.open(C20_GR, encoding='utf-8', newline='').read()
    _c20_ff = _c19_eval_expect_cur(C19_FACTS) if os.path.exists(C19_FACTS) else None
    _c20_ptr = _c19_abs
    _c20_same_src = _c20_imports_same(_c20_txt)
    try:
        _c20_pair = _c20_ast_ledger(_c20_txt)
        _c20_vdirs = _c20_vdir_literals(_c20_txt)
        _c20_ast_err = None
    except Exception as _e:
        _c20_pair, _c20_vdirs, _c20_ast_err = None, set(), _e
    if _c20_ast_err is not None:
        fails.append('C20 gate_runner.py unparseable (%s): cannot verify the three-way link'
                     % _c20_ast_err)
    elif _c20_same_src and _c20_ff is not None:
        _c20_gr = _c20_ff
        notes.append('C20 gate_runner LEDGER is imported from facts_floors (single source of '
                     'truth; the (d) copy-count criterion is deliberately not applied)')
    elif _c20_pair is None:
        fails.append('C20 cannot resolve LEDGER in gate_runner.py (the runner must declare which '
                     'ledger it feeds to both gates, via os.path.join or an import of '
                     'facts_floors.EXPECT_CUR)')
        _c20_gr = None
    else:
        _c20_gr = os.path.join(R14, _c20_pair[0], _c20_pair[1])
        if len(_c20_vdirs) != 1:
            fails.append('C20 gate_runner.py carries %d distinct ledger version literals %r '
                         '(expected exactly 1; a second copy is a constant that can drift '
                         'silently)' % (len(_c20_vdirs), sorted(_c20_vdirs)))
    if _c20_gr is None:
        pass
    else:
        if _c20_ff is None:
            fails.append('C20 cannot resolve EXPECT_CUR in facts_floors.py')
        elif os.path.normpath(_c20_gr) != os.path.normpath(_c20_ff):
            fails.append('C20 gate_runner.LEDGER=%r vs facts_floors.EXPECT_CUR=%r (the runner '
                         'feeds gate 2 a different file than gate 2 checks by default)'
                         % (_c20_gr, _c20_ff))
        if _c20_ptr is None:
            fails.append('C20 pointer not usable (C19 pointer state=%r); see the C19 entry above '
                         '(this distinguishes "pointer broken" from "C19 never ran")'
                         % _c19_ptr_state)
        elif os.path.normpath(_c20_gr) != os.path.normpath(_c20_ptr):
            fails.append('C20 gate_runner.LEDGER=%r vs pointer=%r (the runner drives both gates '
                         'against a version the pointer no longer declares)'
                         % (_c20_gr, _c20_ptr))
        if _c19 != 'not-run' and not _c19.startswith('ok('):
            fails.append('C20 cannot certify the three-way link while C19 is %r (the pointer '
                         'itself failed; a green C20 note here would be misleading)'
                         % (_c19,))
        if not [x for x in fails if x.startswith('C20')]:
            _c20 = 'ok(%s)' % os.path.basename(os.path.dirname(_c20_gr))
            notes.append('C20 three-way ledger path (runner/facts/pointer): all three resolve to '
                         '%r ; C19 pointer state=%r' % (_c20_gr, _c19_ptr_state))
        else:
            _c20 = 'FAIL'


# ---- C5 CR 抽查 ----
for name, p, exp in (('R14_COMMON', RC, 1081), ('STATUS_BOARD', BRD, 0), ('LEDGER', LED, 337)):
    if not os.path.exists(p): fails.append('C5 %s missing' % name); continue
    c = read(p).count('\r\n')
    if c != exp: fails.append('C5 %s CRLF=%d expected %d' % (name, c, exp))

print('--- check_disc.py (%s) ---' % GATE_VER)
print('discipline defs %d ; DISC_RECHECK rows %d' % (len(defs), len(rows)))
for n in notes: print('  NOTE  ' + n)
print('C7 live-checks passed %d ; none-skipped %d ; shape census %s'
      % (c7_ok, c7_none, ', '.join('%s=%d' % (k, v) for k, v in sorted(c7_shape.items()))))
print('C8 section-exists passed %d' % c8_ok)
print('C10 self-check: %s' % c10)
print('C19 fact-layer link: %s' % _c19)
print('C20 three-way ledger path: %s' % _c20)
if fails:
    for f in fails: print('  FAIL  ' + f)
    print('[exit 1] %d FAIL' % len(fails)); sys.exit(1)
print('  PASS  structure/paths/sections/self all ok ; live checks %d' % c7_ok)
print('  BOUNDARY: C7 verifies product file exists AND its recorded byte count ;')
print('            it does NOT verify that the product content supports the discipline.')
print('            PASS != all 28 disciplines proven.  Row-7 truth is NOT machine-verified.')
print('[exit 0]'); sys.exit(0)
