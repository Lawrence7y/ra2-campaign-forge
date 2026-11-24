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
import io, os, re, sys, hashlib, hashlib, json

ROOT = r'D:\Project\ra2-campaign-forge'
if not os.path.isdir(ROOT):                      # R73：POSIX 上按本文件位置反推三层
    ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
R14  = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
RC   = os.path.join(R14, 'R14_COMMON.md')
DR   = os.path.join(R14, 'DISC_RECHECK.tsv')
BRD  = os.path.join(R14, 'STATUS_BOARD.md')
LED  = os.path.join(ROOT, 'lead', 'GOAL_THREE_TARGETS_20261018.md')
SELF = os.path.abspath(__file__)
GATE_VER = 'R120'
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
C11B_PIN_GAP = [11, 12, 13, 14, 15, 17, 26]
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
        c11_declared += 1
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
    7: 595, 8: 937, 9: 1361, 10: 671, 11: 385, 12: 1144, 13: 923, 14: 1020, 15: 812, 16: 710,
    17: 860, 18: 1518, 19: 1006, 20: 1037, 21: 710, 22: 1520, 23: 991, 24: 1699, 25: 1320,
    26: 2660, 27: 1185, 28: 1398, 29: 1283, 30: 1200, 31: 1403, 32: 1103, 33: 1345, 34: 1259,
    35: 1294, 36: 979, 37: 970, 38: 1144, 39: 1066, 40: 982, 41: 1143, 42: 1286, 43: 1051,
    44: 1298, 45: 1064, 46: 870, 47: 1239, 48: 992, 49: 1010, 50: 1385, 51: 1104, 52: 1299,
    53: 903, 54: 925, 55: 1169, 56: 1067, 57: 992, 58: 826, 59: 1281, 60: 1179, 61: 1071, 62: 809,
    63: 933, 64: 842, 65: 1172, 66: 1039, 67: 922, 68: 1223, 69: 908, 70: 1115, 71: 1116, 72: 3440,
    73: 3596, 74: 1871, 75: 1616, 76: 2848, 77: 2709, 78: 1884, 79: 3264, 80: 1520, 81: 3460,
    82: 2096, 83: 1843, 84: 2318, 85: 3034, 86: 1607, 87: 2508, 88: 1910, 89: 2745, 90: 3120,
    91: 2000, 92: 1864, 93: 2044, 94: 866, 95: 1295, 96: 1584, 97: 2244, 98: 1437, 99: 1173,
    100: 1397, 101: 1595, 102: 4028, 103: 2914, 104: 2985, 105: 2986, 106: 2748, 107: 3312,
    108: 1628, 109: 1992, 110: 2381, 111: 2796, 112: 2931, 113: 2827, 114: 2981, 115: 2911,
    116: 2214, 117: 3359, 118: 2911, 119: 2857, 120: 2547, 121: 1854, 122: 2701, 123: 2355
}
# 🐞 自错 S-61（成对回归 E5 当场抓出）：初稿给**新节**也设了 400 B 下限，
# 于是「追加一个合法的短新节」被误判 FAIL —— 这是把「不许清空」误扩成「不许写短」。
# 新节不是被钉对象（C15 已保证 7..106 存在、末节号不回退），故新节不设下限。
C16_FLOORS_SHA256 = 'df02e3169aa109b2faff66660f3030f7737ec39f210f5dd1b42d62fd123ed299'   # 上表的 sha256（逐 id:floor 规范化）；审计 R119 ③ 成立：
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
C17_PIN = {
    (3, 55, '2026-11-22T17:39:19+08:00'),
    (4, 55, '2026-11-22T17:40:02+08:00'),
    (22, 55, '2026-11-22T17:39:19+08:00'),
    (27, 55, '2026-11-22T17:39:19+08:00'),
    (28, 55, '2026-11-22T17:39:19+08:00'),
}
C17_PIN_SHA256 = '642c9cd8b9176f4e8dffd0c744e651d26e5465186a79bcaace70cadbc7a59288'
C17_REUSED_ATS = {'2026-11-22T17:39:19+08:00': 4}   # at -> 复用的不同轮次目录数（下限）
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
notes.append('C17 self-produced-line anachrony: checked=%d impossible=%d (pinned %d), '
             'reused-at=%s, pin=%s'
             % (_c17_checked, len(_c17_imposs), len(C17_PIN),
                json.dumps(_c17_reuse, ensure_ascii=False) if False else repr(_c17_reuse),
                _c17_pin_sha[:16]))

# ---- C5 CR 抽查 ----
for name, p, exp in (('R14_COMMON', RC, 1081), ('STATUS_BOARD', BRD, 0), ('LEDGER', LED, 337)):
    if not os.path.exists(p): fails.append('C5 %s missing' % name); continue
    c = read(p).count('\r\n')
    if c != exp: fails.append('C5 %s CRLF=%d expected %d' % (name, c, exp))

print('--- check_disc.py (%s) ---' % GATE_VER)
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
