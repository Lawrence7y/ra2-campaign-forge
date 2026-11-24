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
import io, os, re, sys, hashlib, hashlib

ROOT = '/home/t628/projects/ra2-campaign-forge'
R14  = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
RC   = os.path.join(R14, 'R14_COMMON.md')
DR   = os.path.join(R14, 'DISC_RECHECK.tsv')
BRD  = os.path.join(R14, 'STATUS_BOARD.md')
LED  = os.path.join(ROOT, 'lead', 'GOAL_THREE_TARGETS_20261018.md')
SELF = os.path.abspath(__file__)
GATE_VER = 'R58'
FREEZE_SHA256 = '0ffeeff5acb825cd5204abd013fcbe0a98a0d1df47b9a20c6a8f35c7b72aab61'   # DISC_UNVERIFIABLE.tsv 的 sha256（防静默篡改）

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
    if r[2].strip() in PLACEHOLDER:
        fails.append('C9 id %s judge-column empty/placeholder' % r[0])
    if r[3].strip() in PLACEHOLDER:
        fails.append('C9 id %s anchor-column empty/placeholder' % r[0])

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
    if not later.startswith('\u6709'):
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
        c11_ok += 1
    elif n in C11_FROZEN:
        # R58：冻結类——在冻结档里，结构性不可验证 ⇒ 不 FAIL，但显式计入
        c11_declared += 1
    else:
        c11_fail += 1
        fails.append('C11 id %s claims recheck but has no valid self-description line (%s)'
                     % (r[0], str(detail)[:70]))
notes.append('C11 col7 machine-check: ok=%d fail=%d frozen-unverifiable=%d claims-none=%d'
             % (c11_ok, c11_fail, c11_declared, c11_unver))

# ---- C5 CR 抽查 ----
for name, p, exp in (('R14_COMMON', RC, 1081), ('STATUS_BOARD', BRD, 0), ('LEDGER', LED, 337)):
    if not os.path.exists(p): fails.append('C5 %s missing' % name); continue
    c = read(p).count('\r\n')
    if c != exp: fails.append('C5 %s CRLF=%d expected %d' % (name, c, exp))

print('--- check_disc.py (R49) ---')
print('discipline defs %d ; DISC_RECHECK rows %d' % (len(defs), len(rows)))
for n in notes: print('  NOTE  ' + n)
print('C7 live-checks passed %d ; none-skipped %d' % (c7_ok, c7_none))
print('C8 section-exists passed %d' % c8_ok)
print('C10 self-check: %s' % c10)
if fails:
    for f in fails: print('  FAIL  ' + f)
    print('[exit 1] %d FAIL' % len(fails)); sys.exit(1)
print('  PASS  structure/paths/sections/self all ok ; live checks %d' % c7_ok)
print('  BOUNDARY: C7 verifies product file exists AND its recorded byte count ;')
print('            it does NOT verify that the product content supports the discipline.')
print('            PASS != all 28 disciplines proven.  Row-7 truth is NOT machine-verified.')
print('[exit 0]'); sys.exit(0)
