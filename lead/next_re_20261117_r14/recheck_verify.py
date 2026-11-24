# -*- coding: utf-8 -*-
"""recheck_verify.py -- 第 7 列「是否真回跑」自描述行的机检器（R53-T2 / C11）

交付接口（§2.51 / R51-T2 约定，Lead 在 check_disc.py 增 C11 调用）：
    verify_recheck_line(root, row) -> (ok: bool, detail: str)
        row = DISC_RECHECK.tsv 的一行 split('\\t') 结果（7 列）
        ok  = True / False；**无 None**——任何字段缺失/格式不符/时刻不可解析一律 False（fail-closed）

自描述行格式（§2.51 逐字）：
    DISC_RECHECK discipline=<N> round=<Rxx> at=<ISO8601> anchors=<sha256:HEX64> conclusion=<PASS|FAIL|UNKNOWN>

六条校验（4 必须 + ⑤⑥ 建议）：
    R1 行存在且恰好一条（且 token 结构合法、字段集完整、无重复键）
    R2 discipline 十进制无前导零，等于 row[0]
    R3 at 严格 ISO8601(+HH:MM) 可解析，且 > 立条落盘时刻（取自 DISC_ESTABLISH.tsv）
    R4 round 形如 R\\d{2,3}，序号 > 立条轮次序号，且 at 落在该 round 的 [start,end] 窗口
    R5 anchors == 'sha256:' + sha256(UTF-8(row[3] 『必查的现有数据锚』逐字串))
    R6 conclusion ∈ {PASS, FAIL, UNKNOWN}

关键设计（如实声明，见 REPORT FALSIFY）：
  * DISC_ROUNDS.tsv 在本盘上 **不存在**，且本卡只允许新建两个文件（DISC_ESTABLISH.tsv、
    本文件），故 round 窗口表 **内嵌于本模块** ROUND_WINDOWS。它不是自造数：它来自
    R17_LEAD_BASELINE\\STATUS_BOARD.before_rNN_HHMMSS.md 的文件名时分秒（r35-r53），
    每条注释给出来源文件名。窗口 = [本轮 before 快照时刻, 下一轮 before 快照时刻)。
    **窗口外的 round 一律 False（fail-closed）。R94 起表由磁盘快照推导，覆盖 r36..r65
    去掉缺端点的 r41/r42 共 28 轮；表外轮次仍一律不可验证。**
  * 立条落盘时刻来自 DISC_ESTABLISH.tsv（第 4 列），该文件缺失/行缺失/时刻不可解析 ⇒ False。
  * 立条落盘时刻本身是「上界推断」（中/高置信度见该表第 6 列），不是精确落盘秒；
    R3 用的是「>= 上界」的宽松语义的反向：at 必须 **严格晚于**该上界，故 at 落在
    上界与真实落盘之间会被误判为「非回跑」（保守方向，不与造假同向）。FALSIFY 另有详述。
  * 本校验只证明「自述行的跨字段一致性」，不证明「真的按该纪律判据回跑过」；
    at/anchors 皆同一行为者可自写，无外部可信时钟（lead 全树 git 未跟踪）。见 FALSIFY。
"""
import io
import os
import re
import hashlib
from datetime import datetime, timedelta, timezone

# ---- 路径 -------------------------------------------------------------------
# DISC_ESTABLISH.tsv 与本模块同目录（lead\next_re_20261117_r14\）
_HERE = os.path.dirname(os.path.abspath(__file__))
ESTABLISH_PATH = os.path.join(_HERE, 'DISC_ESTABLISH.tsv')

# ---- 轮次窗口：R94 起改为**从磁盘快照推导**，不再内嵌手抄表 ----------------
# 语义（这是本轮唯一的判据变更，见 R94 R14_COMMON §2.98）：
#     窗口(N) = [T(N-1), T(N))
#   T(N) = R17_LEAD_BASELINE/STATUS_BOARD.before_rN_HHMMSS.md 的时分秒，日期 2026-11-22，+08:00。
#
# 为什么是 N-1..N 而不是 N..N+1：R86 §DM5–DM9 用派发卡 mtime 当与看板无关的时钟，
# 实测 30 份主快照、270 张卡、50 张两端可判定，H_OLD=[T(N),T(N+1)) 命中 0，
# H_NEW=[T(N-1),T(N)) 命中 50/50，位移剖面峰值唯一落在 delta=-1 且 delta=0 为 0。
# 语义含义：before_rN 快照是**第 N 轮开工前**拍的，故第 N 轮的全部工作落在它之前。
#
# 三项结构性保证（缺一即不可信，故写成代码而不是注释）：
#   1. 端点溯源：每个窗口端点必须**恰好**是某份主快照的时刻。放宽（±1 秒、撑开一小时、
#      全天）都会造出不在该集合里的端点 ⇒ 立刻被 detect_widening 抓到。
#   2. 分区性：相邻两轮的窗口首尾相接，无重叠。
#   3. 缺端点 fail-closed：r41 无主快照 ⇒ R41 与 R42 都没有窗口，一律 False，不补、不合并。
#   4. 同轮重复主快照（r56/r58/r60/r62）取**最早**那份作为该轮起点，其余记入 _DUP_SNAPSHOTS
#      单列，不静默丢弃。
_SNAP_RE = re.compile(r'^STATUS_BOARD\.before_r(\d+)(add\d*)?_(\d{6})\.md$')
_SNAP_DIR = os.path.join(_HERE, 'R17_LEAD_BASELINE')
_DATE = '2026-11-22'
_TZ = timezone(timedelta(hours=8))


def _hhmmss(s, date=None):
    """'HHMMSS' -> aware datetime(+08:00)；非法即 ValueError。"""
    if not re.fullmatch(r'\d{6}', s):
        raise ValueError('bad HHMMSS %r' % s)
    h, m, sec = int(s[0:2]), int(s[2:4]), int(s[4:6])
    y, mo, d = [int(x) for x in (date or _DATE).split('-')]
    return datetime(y, mo, d, h, m, sec, tzinfo=_TZ)


def load_main_snapshots(snap_dir=None):
    """扫 R17_LEAD_BASELINE，返回 ({round: 'HHMMSS'}, [(round,file,hhmmss,kept)])。
    只收主快照（文件名带 6 位时分秒且无 add 段）。同轮重复取最早，其余入 dup。
    目录不存在 -> ({}, [])，调用方据此 fail-closed。"""
    d = snap_dir or _SNAP_DIR
    main, dup = {}, []
    if not os.path.isdir(d):
        return main, dup
    for f in sorted(os.listdir(d)):
        if not f.startswith('STATUS_BOARD.before_'):
            continue
        m = _SNAP_RE.match(f)
        if not m or m.group(2):
            continue
        n, hh = int(m.group(1)), m.group(3)
        if n in main:
            dup.append((n, f, hh, main[n]))
            if hh < main[n]:
                main[n] = hh
        else:
            main[n] = hh
    return main, dup


_SNAP_HH, _DUP_SNAPSHOTS = load_main_snapshots()
_SNAP_T = {n: _hhmmss(hh) for n, hh in _SNAP_HH.items()}

# 兼容旧接口：ROUND_WINDOWS[n] = (lo, hi, 起点来源文件名, 终点来源文件名)
ROUND_WINDOWS = {}
for _n in sorted(_SNAP_T):
    if (_n - 1) in _SNAP_T:
        ROUND_WINDOWS[_n] = (
            _SNAP_T[_n - 1], _SNAP_T[_n],
            'STATUS_BOARD.before_r%d_%s.md' % (_n - 1, _SNAP_HH[_n - 1]),
            'STATUS_BOARD.before_r%d_%s.md' % (_n, _SNAP_HH[_n]))


# 快照清单摘要：R94 把窗口表改成「从磁盘推导」之后，**改文件名即可改判据**
# （主会话实测：把 r65 改名成 r94，表跟着变、W1..W4 仍然全过）。
# W5 把清单钉死：清单与登记摘要不符 ⇒ 判 FAIL，必须由 Lead 显式改这个常量。
SNAPSHOT_MANIFEST_SHA256 = '418bf81e19c3faaf902c9b043eeac3db264a1676cbb67b991bb8ce9cfc3d95ce'


def snapshot_manifest_sha256():
    """{round: 'HHMMSS'} -> sha256。只含主快照（不含 add 变体、不含无时刻文件名）。"""
    blob = '\n'.join('%d %s' % kv for kv in sorted(_SNAP_HH.items()))
    return hashlib.sha256(blob.encode('utf-8')).hexdigest()


def detect_widening(table):
    """R94 新增的门禁自检：窗口表是否被「放宽」而不是「按快照逐轮切分」。
    table: {round: (lo, hi)}。返回 (ok: bool, detail: str)。
    四项，任一不过即 ok=False：
      W1 端点溯源：所有 lo/hi 都必须恰好等于某份主快照时刻
      W2 分区性：窗口两两不重叠
      W3 非空：lo < hi
      W4 与磁盘一致：窗口必须等于 [T(N-1), T(N)) 按磁盘重建的结果
      W5 快照清单未被改动：清单 sha256 必须等于登记值（防止改名/加文件改判据）
    """
    if not table:
        return False, 'W0 empty table'
    ts = set(_SNAP_T.values())
    for n in sorted(table):
        lo, hi = table[n]
        if not lo < hi:
            return False, 'W3 empty window R%d' % n
        if lo not in ts or hi not in ts:
            return False, 'W1 endpoint of R%d not a snapshot instant' % n
    rs = sorted(table)
    for a in range(len(rs)):
        for b in range(a + 1, len(rs)):
            a0, a1 = table[rs[a]]
            b0, b1 = table[rs[b]]
            if a0 < b1 and b0 < a1:
                return False, 'W2 R%d overlaps R%d (widened)' % (rs[a], rs[b])
    man = snapshot_manifest_sha256()
    if man != SNAPSHOT_MANIFEST_SHA256:
        return False, 'W5 snapshot manifest changed: %s != %s' % (
            man[:16], SNAPSHOT_MANIFEST_SHA256[:16])
    rebuilt = {n: (v[0], v[1]) for n, v in ROUND_WINDOWS.items()}
    if {n: tuple(table[n]) for n in rs} != rebuilt:
        only_t = [n for n in rs if n not in rebuilt]
        only_d = [n for n in rebuilt if n not in table]
        return False, 'W4 table != disk-derived (extra=%s missing=%s)' % (
            only_t[:5], only_d[:5])
    return True, 'W1..W5 ok, %d windows, %d snapshots, %d dup' % (
        len(rs), len(_SNAP_T), len(_DUP_SNAPSHOTS))



# 自描述行字段集（顺序固定，单空格分隔，行首顶格）
_FIELDS = ['discipline', 'round', 'at', 'anchors', 'conclusion']
_PREFIX = 'DISC_RECHECK '
_LINE_RE = re.compile(
    r'^DISC_RECHECK '
    r'discipline=(\d+) '
    r'round=(R\d{2,3}) '
    r'at=(\S+) '
    r'anchors=(sha256:[0-9a-f]{64}) '
    r'conclusion=(\S+)$'
)
_CONCLUSIONS = frozenset(('PASS', 'FAIL', 'UNKNOWN'))


def _fail(reason):
    return (False, reason)


def _read_utf8(path):
    with io.open(path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()


def _parse_iso8601_strict(s):
    """严格 YYYY-MM-DDTHH:MM:SS+HH:MM；失败返回 None。"""
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}', s):
        return None
    try:
        dt = datetime.strptime(s, '%Y-%m-%dT%H:%M:%S%z')
    except ValueError:
        return None
    return dt


def _load_establish():
    """读 DISC_ESTABLISH.tsv -> {int(纪律号): (round_no, landing_dt)}。
    文件/TSV 结构/字段/时刻任何不合法 ⇒ 抛 ValueError（由调用方转 False）。"""
    if not os.path.isfile(ESTABLISH_PATH):
        raise ValueError('R3 DISC_ESTABLISH.tsv missing: %s' % ESTABLISH_PATH)
    txt = _read_establish_text()
    lines = [l for l in txt.split('\n') if l != '']
    if len(lines) < 2:
        raise ValueError('R3 DISC_ESTABLISH.tsv no data row')
    head = lines[0].split('\t')
    if len(head) != 6:
        raise ValueError('R3 DISC_ESTABLISH.tsv header cols=%d' % len(head))
    est = {}
    for ln in lines[1:]:
        c = ln.split('\t')
        if len(c) != 6:
            raise ValueError('R3 establish row cols=%d' % len(c))
        n_s, _sec, round_s, at_s, _basis, _conf = c
        if not re.fullmatch(r'\d+', n_s.strip()):
            raise ValueError('R3 establish bad discipline %r' % n_s)
        m = re.fullmatch(r'R(\d{2,3})', round_s.strip())
        if not m:
            raise ValueError('R3 establish bad round %r' % round_s)
        dt = _parse_iso8601_strict(at_s.strip())
        if dt is None:
            raise ValueError('R3 establish bad landing time %r' % at_s)
        est[int(n_s.strip())] = (int(m.group(1)), dt)
    return est


def _read_establish_text():
    return _read_utf8(ESTABLISH_PATH)


_WIDENING_CACHE = {}   # key = 当前表的内容指纹，不是「空/非空」（R94 审计 #115 抓到的缺陷）


def _table_fingerprint():
    """窗口表的内容指纹。用来判定缓存是否还对应当前这张表。
    缺陷背景（R94 审计员 #115 D10 实测）：旧实现用列表当「算过没」的开关，
    预热一次后即使把表换成全天，verify_recheck_line 仍拿旧缓存判「表没问题」。
    症状：POS 用例句拿坏表判 PASS。修法是让缓存键绑定表内容。"""
    blob = '\n'.join('%d %s %s' % (n, v[0].isoformat(), v[1].isoformat())
                      for n, v in sorted(ROUND_WINDOWS.items()))
    return hashlib.sha256(blob.encode('utf-8')).hexdigest()


def _widening_selfcheck():
    """整表自检（W1..W5），结果按表指纹缓存。表一旦被改（放宽/删轮/改名）⇒ False。"""
    k = _table_fingerprint()
    hit = _WIDENING_CACHE.get(k)
    if hit is None:
        hit = detect_widening({n: (v[0], v[1]) for n, v in ROUND_WINDOWS.items()})
        if hit[0]:
            _WIDENING_CACHE.clear()      # 只缓存「通过」的结果，坏表每次都重算
        _WIDENING_CACHE[k] = hit
    return hit


def verify_recheck_line(root, row):
    """校验 row 对应产物里的 DISC_RECHECK 自描述行。

    root : 项目根（check_disc.py 的 ROOT）；产物路径 row[4] 相对它解析。
    row  : DISC_RECHECK.tsv 一行 split('\\t')，须 7 列。
    return (ok: bool, detail: str) —— 全 fail-closed，无 None。
    """
    # ---- 入参结构（fail-closed）----
    if not isinstance(row, (list, tuple)) or len(row) != 7:
        return _fail('R0 row cols != 7')
    n_s = row[0].strip()
    if not re.fullmatch(r'\d+', n_s):
        return _fail('R0 bad discipline in row: %r' % n_s)
    N = int(n_s)
    anchor4 = row[3]           # 逐字，不 strip：哈希绑定原文
    rel = row[4].strip()
    if not rel:
        return _fail('R0 empty product path')
    ap = rel.replace('\\', os.sep).replace('/', os.sep)   # R73：分隔符无关（Windows 下与旧行为等价）
    if not os.path.isabs(ap):
        ap = os.path.join(root, ap)
    if not os.path.isfile(ap):
        return _fail('R1 product file missing: %s' % rel)

    # ---- R1 行存在且唯一 + token 结构 ----
    txt = _read_utf8(ap)
    # R56 修（缺陷 3）：原为「该产物里 DISC_RECHECK 行必须恰好 1 条」——
    # 但纪律 3 与 4 共用同一产物 anchor_check.txt，各写一条 ⇒ 永远满足不了。
    # 正确语义：**本纪律**的行必须恰好 1 条（同产物可含其它纪律的行）。
    allh = [l for l in txt.splitlines() if l.startswith(_PREFIX)]
    hits = []
    for _l in allh:
        _m = re.search(r'\bdiscipline=(\d+)\b', _l)
        if _m and int(_m.group(1)) == N:
            hits.append(_l)
    if len(hits) != 1:
        return _fail('R1 line_count_for_discipline_%d=%d (must be 1; product has %d DISC_RECHECK lines total)'
                     % (N, len(hits), len(allh)))
    line = hits[0]
    m = _LINE_RE.match(line)
    if not m:
        # 进一步定位：是字段数/顺序/重复键问题
        toks = line.split(' ')
        if any('=' not in t for t in toks[1:]):
            return _fail('R1 bad_token(no =)')
        keys = [t.split('=', 1)[0] for t in toks[1:]]
        if len(keys) != len(set(keys)):
            return _fail('R1 duplicate_key')
        if set(keys) != set(_FIELDS) or len(keys) != len(_FIELDS):
            return _fail('R1 field_set=%s' % keys)
        return _fail('R1 regex_mismatch (format/order/width)')
    d_s, r_s, at_s, anchors_s, concl_s = m.groups()

    # ---- R2 discipline 对齐 ----
    if not re.fullmatch(r'[1-9]\d*', d_s):       # 无前导零
        return _fail('R2 discipline leading-zero/noncanonical: %s' % d_s)
    if int(d_s) != N:
        return _fail('R2 discipline %s != row %d' % (d_s, N))

    # ---- 立条表（R3/R4 共同外部输入；缺失即 fail-closed）----
    try:
        est = _load_establish()
    except ValueError as e:
        return _fail(str(e))
    if N not in est:
        return _fail('R3 no establish row for discipline %d' % N)
    est_round, est_at = est[N]

    # ---- R3 at 严格可解析 + 晚于立条落盘上界 ----
    at = _parse_iso8601_strict(at_s)
    if at is None:
        return _fail('R3 bad ISO8601 at=%s' % at_s)
    if at <= est_at:
        return _fail('R3 at<=establish (%s <= %s)' % (at_s, est_at.isoformat()))

    # ---- R4 round 格式 / 序号 / 窗口 ----
    if not re.fullmatch(r'R\d{2,3}', r_s):
        return _fail('R4 bad round %s' % r_s)
    rno = int(r_s[1:])
    if rno <= est_round:
        return _fail('R4 round_no %d <= establish round %d' % (rno, est_round))
    # R94：先自检整张窗口表没被放宽（只做一次，模块级缓存）
    okw, dw = _widening_selfcheck()
    if not okw:
        return _fail('W table widened: %s' % dw)
    win = ROUND_WINDOWS.get(rno)
    if win is None:
        return _fail('R4 no round window for R%03d (unverifiable -> False)' % rno)
    w0, w1, _sf, _ef = win
    if not (w0 <= at <= w1):
        return _fail('R4 at outside R%03d window [%s, %s]' % (
            rno, w0.isoformat(), w1.isoformat()))

    # ---- R5 anchors 绑定第 4 列逐字串 ----
    want = 'sha256:' + hashlib.sha256(anchor4.encode('utf-8')).hexdigest()
    if anchors_s != want:
        return _fail('R5 anchors mismatch: got %s want %s' % (anchors_s, want))

    # ---- R6 conclusion 闭集合 ----
    if concl_s not in _CONCLUSIONS:
        return _fail('R6 conclusion not in {PASS,FAIL,UNKNOWN}: %s' % concl_s)

    return (True, 'ok R1-R6; disc=%d round=%s at=%s est<=%s window=[%s,%s]' % (
        N, r_s, at_s, est_at.isoformat(), w0.isoformat(), w1.isoformat()))


# ===========================================================================
# 自测：1 正控 + 4 反控（Q4 硬要求）。临时产物写在本模块目录，跑完即删。
#   python recheck_verify.py --self-test
# ===========================================================================
def _self_test():
    root = os.path.abspath(os.path.join(_HERE, '..', '..'))  # D:\Project\ra2-campaign-forge
    here = _HERE
    tmp = os.path.join(here, '_posctl_product.tmp')
    disc = 11
    # discipline 11 的立条上界 12:00:54；R52 窗口在新语义下 = [T(51),T(52))
    #   = [16:01:44, 16:17:50)，故取 at=16:10:00（旧夹具的 16:20:00 属旧语义，已废）。
    # 正控用**真实** DISC_RECHECK.tsv 第 11 行（含真实第 4 列锚），只把产物路径改向临时文件，
    # 让「一条完全合法的自描述行」落在该临时产物里——不是凭空造 row。
    dr_path = os.path.join(here, 'DISC_RECHECK.tsv')
    real = None
    if os.path.isfile(dr_path):
        for ln in _read_utf8(dr_path).split('\n')[1:]:
            if ln and ln.split('\t')[0].strip() == str(disc):
                real = ln.split('\t')
                break
    if real is None or len(real) != 7:
        # 退路（不应发生）：仍构造 7 列，但如实标注锚为占位
        real = ['11', '\u00a72.24', 'judge', '\u7b49\u7ea7\u5224\u636e\u8868',
                'x', 'grep=x', '\u6709']
    anchor4 = real[3]                      # 真实第 4 列『必查的现有数据锚』逐字串
    row = list(real)
    row[4] = os.path.relpath(tmp, root)    # 仅把产物路径改向临时文件
    good = ('DISC_RECHECK discipline=11 round=R52 at=2026-11-22T16:10:00+08:00 '
            'anchors=sha256:%s conclusion=PASS' % hashlib.sha256(anchor4.encode('utf-8')).hexdigest())
    # 注：R5 用 row[3]（第 4 列锚逐字串）重算 sha256，good 中 anchors 即由同一 anchor4 算出。

    cases = []
    cases.append(('POS \u5b8c\u5168\u5408\u6cd5', good, row, True))
    cases.append(('NEG1 discipline \u53f7\u9519', good.replace('discipline=11', 'discipline=12'), row, False))
    cases.append(('NEG2 at \u65e9\u4e8e\u7acb\u6761', good.replace('at=2026-11-22T16:10:00', 'at=2026-11-22T11:00:00'), row, False))
    cases.append(('NEG3 at \u4e0e round \u7a97\u53e3\u77db\u76fe', good.replace('at=2026-11-22T16:10:00+08:00', 'at=2026-11-22T15:00:00+08:00'), row, False))
    bad_hash = 'sha256:' + ('0' * 64)
    cases.append(('NEG4 anchors \u54c8\u5e0c\u4e0d\u7b26', good.replace('anchors=sha256:' + hashlib.sha256(anchor4.encode('utf-8')).hexdigest(), 'anchors=' + bad_hash), row, False))

    results = []
    try:
        for name, line, r, expect in cases:
            with io.open(tmp, 'w', encoding='utf-8', newline='') as f:
                f.write('# fixture\n' + line + '\n')
            ok, detail = verify_recheck_line(root, r)
            passed = (ok == expect)
            results.append((name, ok, expect, passed, detail))
            print('%-28s ok=%-5s expect=%-5s %s | %s' % (
                name, ok, expect, 'PASS' if passed else 'FAIL', detail))
    finally:
        if os.path.isfile(tmp):
            os.remove(tmp)
    # ---- 6/7 窗口表反控：坏表必须被 detect_widening 抓住 ----
    # R94 新增。理由：把窗口表改成全天，POS 用例会失败，但那可能只是「碰巧失败」。
    # 这两项直接断言「坏表必被抓 / 好表必通过」，使自测真正覆盖窗口表。
    saved_tab = {n: (v[0], v[1]) for n, v in ROUND_WINDOWS.items()}
    bad_allday = {n: (datetime(2026, 11, 22, 0, 0, tzinfo=_TZ),
                      datetime(2026, 11, 22, 23, 59, 59, tzinfo=_TZ))
                  for n in saved_tab}
    bad_shift = {n: (a - timedelta(seconds=1), b) for n, (a, b) in saved_tab.items()}
    bad_drop = {n: v for n, v in saved_tab.items() if n != 55}
    cases2 = [('NEG5 窗口表放宽到全天', bad_allday, False),
              ('NEG6 首轮下界前移 1 秒', bad_shift, False),
              ('NEG7 删掉 R55', bad_drop, False),
              ('POS2 磁盘推导表原样', saved_tab, True)]
    for name, tab, expect in cases2:
        ok2, d2 = detect_widening(tab)
        passed = (ok2 == expect)
        results.append((name, ok2, expect, passed, d2))
        print('%-28s ok=%-5s expect=%-5s %s | %s' % (
            name, ok2, expect, 'PASS' if passed else 'FAIL', d2))

    allok = all(p for _, _, _, p, _ in results)
    print('SELFTEST %s (%d/%d)' % ('PASS' if allok else 'FAIL',
                                   sum(1 for _, _, _, p, _ in results if p), len(results)))
    return allok


if __name__ == '__main__':
    import sys
    if '--self-test' in sys.argv:
        sys.exit(0 if _self_test() else 1)
    print(__doc__)
