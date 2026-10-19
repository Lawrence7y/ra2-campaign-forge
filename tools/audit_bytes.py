#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""audit_bytes.py (v4) —— 字节级断言审计工具（Lead 公用）

用法：
  python tools/audit_bytes.py claims.txt [--exe gamemd.exe] [--json out/re_work/audit.json] [--verbose]
  python tools/audit_bytes.py claims.txt --min-claims 323  # 要求最少断言数
  python tools/audit_bytes.py claims.txt --limit 5         # 抽样运行（与 --min-claims 互斥）
  python tools/audit_bytes.py --selftest                   # 口径自检（映射基准 + 已知锚点）

claims.txt 每行一条（# 后为标签，可省）：
  0x6F936B = 3B C1        # cmp eax,ecx（严格大于比较点）
  bss 0x0087E180 = virtual # .data BSS 区域断言（虚拟存在但无 raw）
  0x00401000..0x007E1000 = <64位sha256hex>  # 区间哈希断言（半开区间 [起,止) 映射 raw 字节的 SHA-256）

映射基准（重要）：
  off = rawptr + (VA − (ImageBase + VirtualAddress))   # 段映射
  与 `VA − 0x400000` 在 .text/.rdata/.data 三段上**完全等价**（这三段 VA−rawptr = 0）；
  仅 .rsrc/.detour 两段不同（本镜像差值 = 0x2FC000，且 .rsrc/.detour 靠 VA−0x400000 会越界）。
  ⇒ 本工具一律用**段映射**，对全部区域都正确。
  PE 头（MZ/PE 签名/节表）位于首节之前，映射为 off = VA − ImageBase，
  区间 [ImageBase, ImageBase+SizeOfHeaders)；v2 只遍历节表导致 0x00400000 NOREAD，v3 已补。

断言类型：
  1. 字节断言  0xVA = HEX…          —— 校验文件字节（含 PE 头）
  2. BSS 区域  bss 0xVA = virtual   —— 校验 VA 落在「虚拟存在、无 raw」区域（从节表推导）
  3. 区间哈希  0xVA1..0xVA2 = SHA256(64hex) —— 对半开区间 [VA1,VA2) 的整段 raw 字节求 SHA-256 比对；
       起端须落在某 raw 段虚拟范围内，且整段跨度 [起,止) 必须有 raw 支撑（止端可越过该段 VirtualSize，
       如 .text raw 尾 0x007E1000 > 虚拟尾 0x007E038D，正是 SizeOfRawData 口径）；否则判 NOREAD。

★GATE-SEG01 段级基线（与 tools/verify_anchors.py 共用同一基线 JSON 格式与退出码契约）：
  python tools/audit_bytes.py claims.txt --min-claims 323 --segments <segment_baseline.json>
  PE头 + 全部段 raw + 尾部 overlay 逐区间 SHA-256；不传 --segments 时输出会量化本次真实射程。
  退出码：0=全过；1=断言不符/段级内容与基线不符/空断言/未达 --min-claims；
          2=参数非法、文件缺失、基线缺失或损坏、基线不适用于本镜像（含 SizeOfHeaders=0、节表结构不符）。
  --segments 与 --selftest / claims / --min-claims / --limit 全部正交叠加，不改变既有互斥语义。
"""
import argparse, hashlib, json, os, struct, sys
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEFAULT_EXE = os.path.join(REPO_ROOT, "ra2youli", "gamemd.exe")
IMAGE_BASE = 0x400000
# 规范段级基线在仓库里的固定位置（与 verify_anchors.py 同一约定）
CANONICAL_SEGMENT_BASELINE_REL = os.path.join(
    "out", "re_work", "work_chain", "CONTINUE_20261003", "lead", "gate_seg", "segment_baseline.json")


def canonical_segment_baseline():
    p = os.environ.get("RA2_SEGMENT_BASELINE")
    if p:
        return p if os.path.isfile(p) else None
    p = os.path.join(REPO_ROOT, CANONICAL_SEGMENT_BASELINE_REL)
    return p if os.path.isfile(p) else None

SELFTEST = [
    (0x6CE210, 'b880000000c3', 'SuperClass::Size()=0x80'),
    (0x6F936B, '3bc1',         'Greatest_Threat 严格大于比较点'),
    (0x750931, 'c20800',       'PlayGlobal ret 8'),
    (0x7509EF, 'c20400',       'PlayAt ret 4'),
    (0x6F8DF0, '83ec5c8b1534eca800', 'Greatest_Threat 入口'),
    (0x7F7C80, '09010000000000 00c000000000000046'.replace(' ', ''), 'IID_IPersistStream'),
]

def load(path):
    with open(path, 'rb') as f:
        return f.read()

def sections(d):
    pe = struct.unpack_from('<I', d, 0x3C)[0]
    nsec = struct.unpack_from('<H', d, pe + 6)[0]
    optsz = struct.unpack_from('<H', d, pe + 20)[0]
    size_headers = struct.unpack_from('<I', d, pe + 24 + 60)[0] or 0x200
    off = pe + 24 + optsz
    # PE 头伪节：MZ/PE 签名/可选头/节表，映射 off = VA − ImageBase（v3 新增）
    out = [('PE-header', IMAGE_BASE, size_headers, size_headers, 0)]
    for i in range(nsec):
        o = off + i * 40
        name = d[o:o + 8].rstrip(b'\0').decode('ascii', 'replace')
        vs, va, rs, rp = struct.unpack_from('<IIII', d, o + 8)
        out.append((name, IMAGE_BASE + va, vs, rs, rp))
    return out

def va2off(secs, va):
    for name, base, vs, rs, rp in secs:
        if base <= va < base + vs:
            delta = va - base
            if delta < rs:
                return rp + delta, name
            return None, name + '(虚拟段/无文件数据)'
    return None, '未映射'

def va_in_bss(secs, va):
    """返回 (is_bss, secname)：VA 是否落在「虚拟存在、无 raw」区域。"""
    for name, base, vs, rs, rp in secs:
        if base <= va < base + vs:
            delta = va - base
            if delta >= rs:
                return True, name
            return False, name
    return False, '未映射'

def range_hash_window(secs, va_lo, va_hi):
    """区间哈希 [va_lo,va_hi) → (file_off, span, secname) 或 None。
    起端须落在某段虚拟范围内且该起端 delta 有 raw 支撑；整段跨度须全部落在该段 raw 之内
    （止端允许越过 VirtualSize 至多到 raw 尾，对应 SizeOfRawData 口径）。"""
    span = va_hi - va_lo
    if span <= 0:
        return None
    for name, base, vs, rs, rp in secs:
        if base <= va_lo < base + vs:
            delta = va_lo - base
            if delta < rs and delta + span <= rs:
                return rp + delta, span, name
            return None
    return None

# ==============================================================================
# 段级基线校验 (GATE-SEG01) —— 与 tools/verify_anchors.py 共用同一基线格式与退出码契约
#   0=全部区间一致  1=区间内容与基线不符(篡改)  2=基线缺失/损坏/不适用于本镜像
# ==============================================================================
SEG_GATE_SCHEMA = 1


class SegGateError(Exception):
    """基线不可用 / 基线不适用于该镜像 => exit 2（与'内容被篡改'的 exit 1 区分）"""


def _seg_int(v, what):
    if isinstance(v, bool):
        raise SegGateError("%s 非法(bool)" % what)
    if isinstance(v, int):
        return v
    if isinstance(v, str):
        s = v.strip()
        try:
            return int(s, 16) if s.lower().startswith('0x') else int(s, 10)
        except ValueError:
            raise SegGateError("%s 非法数值: %r" % (what, v))
    raise SegGateError("%s 类型非法: %r" % (what, type(v)))


def true_size_of_headers(d):
    """取真实 SizeOfHeaders，**不做** sections() 里的 `or 0x200` 回退（回退会掩盖镜像异常）。"""
    pe = struct.unpack_from('<I', d, 0x3C)[0]
    optsz = struct.unpack_from('<H', d, pe + 20)[0]
    soh = struct.unpack_from('<I', d, pe + 24 + 60)[0]
    if not soh:
        raise SegGateError("SizeOfHeaders=0，无法确定 PE 头区间（段级门禁拒绝回退猜测）")
    return soh, optsz


def load_segment_baseline(path):
    if not os.path.isfile(path):
        raise SegGateError("基线文件不存在: %s" % path)
    if os.path.getsize(path) == 0:
        raise SegGateError("基线文件为空(0 字节): %s" % path)
    try:
        with open(path, 'r', encoding='utf-8') as f:
            doc = json.load(f)
    except Exception as e:
        raise SegGateError("基线 JSON 无法解析: %s (%s)" % (path, e))
    if not isinstance(doc, dict):
        raise SegGateError("基线顶层不是 JSON 对象")
    if doc.get('schema_version') != SEG_GATE_SCHEMA:
        raise SegGateError("基线 schema_version=%r 不受支持(期望 %d)" % (doc.get('schema_version'), SEG_GATE_SCHEMA))
    for k in ('target_exe', 'exe_sha256', 'exe_size', 'build_identity', 'pe_header', 'segments'):
        if k not in doc:
            raise SegGateError("基线缺少必备字段 %r" % k)
    segs = doc['segments']
    if not isinstance(segs, list) or not segs:
        raise SegGateError("基线 segments 缺失/为空 —— 空基线不作为放行依据")
    for i, s in enumerate(segs):
        if not isinstance(s, dict):
            raise SegGateError("segments[%d] 不是对象" % i)
        for k in ('name', 'va', 'vsize', 'rptr', 'rsize', 'sha256'):
            if k not in s:
                raise SegGateError("segments[%d] 缺少字段 %r" % (i, k))
            if k == 'sha256' and (not isinstance(s[k], str) or len(s[k]) != 64):
                raise SegGateError("segments[%d].sha256 非法: %r" % (i, s[k]))
    return doc


def seg_gate_check(data, path, secs):
    """secs: sections() 的返回（含下标 0 的 PE-header 伪节，元素为 (name, base, vs, rs, rp)）。"""
    rep = {'requested': True, 'baseline_path': path.replace('\\', '/'), 'status': None,
           'rows': [], 'image_identity': None}
    doc = load_segment_baseline(path)
    fsize = len(data)
    if fsize != _seg_int(doc['exe_size'], 'exe_size'):
        raise SegGateError("镜像大小 %d 与基线声明 %d 不符 => 基线不适用于本镜像" % (fsize, _seg_int(doc['exe_size'], 'exe_size')))
    soh, _optsz = true_size_of_headers(data)
    image_base = struct.unpack_from('<I', data, struct.unpack_from('<I', data, 0x3C)[0] + 24 + 28)[0]
    if _seg_int(doc.get('image_base', image_base), 'image_base') != image_base:
        raise SegGateError("镜像 ImageBase 0x%X 与基线 0x%X 不符" % (image_base, _seg_int(doc['image_base'], 'image_base')))

    def add(name, kind, exp, act, va=None, rptr=None, rsize=None, policy='STRICT_HASH', note=''):
        rep['rows'].append({'name': name, 'kind': kind, 'expected_sha256': exp, 'actual_sha256': act,
                            'verdict': 'OK' if (act and act == exp) else 'MISMATCH',
                            'va': None if va is None else '0x%08X' % va,
                            'rptr': None if rptr is None else '0x%08X' % rptr,
                            'rsize': rsize, 'policy': policy, 'note': note})

    ph = doc['pe_header']
    declared_soh = _seg_int(ph.get('size_of_headers', ph.get('size')), 'pe_header.size_of_headers')
    if declared_soh != soh:
        raise SegGateError("镜像 SizeOfHeaders 0x%X 与基线 0x%X 不符 => 基线不适用于本镜像" % (soh, declared_soh))
    add('PE-header', 'pe_header', ph['sha256'], hashlib.sha256(data[0:declared_soh]).hexdigest(),
        va=image_base, rptr=0, rsize=declared_soh, policy=ph.get('policy', 'STRICT_HASH'),
        note='MZ/DOS 头 + PE 签名 + 可选头 + 节表；节表被改会在此处与结构性检查同时暴露')

    actual = {}
    for name, base, vs, rs, rp in secs[1:]:
        actual.setdefault(name, []).append((base, vs, rp, rs))
    bnames = []
    for s in doc['segments']:
        nm = s['name']
        bnames.append(nm)
        if nm not in actual:
            raise SegGateError("基线声明的段 %r 在镜像中不存在 => 基线不适用于本镜像" % nm)
        if len(actual[nm]) > 1:
            raise SegGateError("段 %s 在镜像中出现 %d 次(重名)，无法唯一映射 => 基线不适用" % (nm, len(actual[nm])))
        va, vsize, rptr, rsize = actual[nm][0]
        for fld, mine, theirs in (('va', va, s['va']), ('vsize', vsize, s['vsize']),
                                  ('rptr', rptr, s['rptr']), ('rsize', rsize, s['rsize'])):
            if _seg_int(theirs, '%s.%s' % (nm, fld)) != mine:
                raise SegGateError("段 %s 的 %s 与基线不符(镜像 0x%X / 基线 0x%X) => 基线不适用于本镜像"
                                   % (nm, fld, mine, _seg_int(theirs, fld)))
        a, b = rptr, rptr + rsize
        if not (0 <= a <= b <= fsize):
            raise SegGateError("段 %s raw 区间越界" % nm)
        add(nm, 'segment', s['sha256'], hashlib.sha256(data[a:b]).hexdigest(),
            va=va, rptr=rptr, rsize=rsize, policy=s.get('policy', 'STRICT_HASH'),
            note=(s.get('note', '') + (' ' + str(s.get('runtime_write')) if s.get('runtime_write') else '')).strip())
    missing = [n for n, *_r in secs[1:] if n not in bnames]
    if missing:
        raise SegGateError("基线遗漏镜像真实存在的段 %s —— 拒绝作为放行依据(不得默默缩小射程)" % missing)

    # 尾部 overlay：由镜像实际残余区间反查基线声明是否一致
    rng = sorted([(0, declared_soh)] + [(_seg_int(s['rptr'], 'rptr'), _seg_int(s['rptr'], 'rptr') + _seg_int(s['rsize'], 'rsize'))
                                        for s in doc['segments']])
    merged, cur = [], None
    for a, b in rng:
        if cur is None:
            cur = [a, b]
        elif a <= cur[1]:
            cur[1] = max(cur[1], b)
        else:
            merged.append(tuple(cur)); cur = [a, b]
    if cur:
        merged.append(tuple(cur))
    gaps, pos = [], 0
    for a, b in merged:
        if a > pos:
            gaps.append((pos, a))
        pos = max(pos, b)
    if pos < fsize:
        gaps.append((pos, fsize))
    declared_over = [(_seg_int(o['raw_offset'], 'overlay.raw_offset'),
                      _seg_int(o['raw_offset'], 'overlay.raw_offset') + _seg_int(o['size'], 'overlay.size'), o)
                     for o in doc.get('overlay_tail') or []]
    if [(a, b) for a, b, _o in declared_over] != gaps:
        raise SegGateError("基线 overlay 区间声明 %s 与镜像实际残余 %s 不符 => 基线不完整"
                           % ([(hex(a), hex(b)) for a, b, _o in declared_over], [(hex(a), hex(b)) for a, b in gaps]))
    for a, b, o in declared_over:
        add('overlay@0x%X' % a, 'overlay', o['sha256'], hashlib.sha256(data[a:b]).hexdigest(),
            rptr=a, rsize=b - a, policy=o.get('policy', 'STRICT_HASH'),
            note='未被任何段/PE头覆盖的尾部字节，纳入强校验以消除盲区')

    hashed = declared_soh + sum(_seg_int(s['rsize'], 'rsize') for s in doc['segments']) \
        + sum(b - a for a, b, _o in declared_over)
    if hashed != fsize:
        raise SegGateError("基线仅覆盖 %d/%d 字节，存在门禁盲区 —— 拒绝作为放行依据" % (hashed, fsize))
    rep['coverage'] = {'file_size': fsize, 'bytes_hashed': hashed,
                       'coverage_ratio': round(hashed / fsize * 100.0, 6)}

    whole = hashlib.sha256(data).hexdigest()
    rep['image_identity'] = 'MATCH' if whole == doc['exe_sha256'] else 'CONTENT_DIFFERS'
    rep['exe_sha256_actual'] = whole
    rep['exe_sha256_baseline'] = doc['exe_sha256']
    rep['build_identity'] = doc['build_identity'].get('state')
    rep['segment_count'] = len(doc['segments'])
    bad = [r for r in rep['rows'] if r['verdict'] != 'OK']
    if rep['image_identity'] == 'MATCH' and bad:
        raise SegGateError("基线内部不一致：整镜像 sha 相符但 %d 个区间哈希不符（基线被手改？）" % len(bad))
    rep['status'] = 'SEGMENTS OK' if not bad else 'SEGMENTS MISMATCH'
    rep['mismatch_count'] = len(bad)
    rep['exit_code'] = 0 if not bad else 1
    return rep


def print_segment_gate(rep, prefix="  "):
    print("%s基线 : %s (schema=%s, 段数=%s, 镜像身份=%s, 基线声明构建态=%s)"
          % (prefix, rep['baseline_path'], SEG_GATE_SCHEMA, rep.get('segment_count'),
             rep.get('image_identity'), rep.get('build_identity')))
    cov = rep.get('coverage') or {}
    if cov:
        print("%s覆盖 : %s/%s 字节 = %.6f%%" % (prefix, cov.get('bytes_hashed'), cov.get('file_size'),
                                                cov.get('coverage_ratio', 0.0)))
    for r in rep['rows']:
        print("%s%s %-10s %-9s va=%s raw=%s len=%s sha256=%s policy=%s"
              % (prefix, '[PASS]' if r['verdict'] == 'OK' else '[FAIL]', r['name'], r['kind'], r['va'],
                 r['rptr'], r['rsize'], r['actual_sha256'], r['policy']))
        if r['verdict'] != 'OK':
            print("%s       期望 %s" % (prefix, r['expected_sha256']))
    bad = [r for r in rep['rows'] if r['verdict'] != 'OK']
    print("%s段级汇总 : %d 个区间(PE头+各段 raw+尾部)，OK=%d MISMATCH=%d"
          % (prefix, len(rep['rows']), len(rep['rows']) - len(bad), len(bad)))


def legacy_untested(d, secs, claims):
    """本工具既有射程 = 各条字节断言触及的区间（audit_bytes 从不哈希整段）。返回 (未覆盖%, 未覆盖字节数)。"""
    iv = []
    for _ln, va, exp, _label, kind in claims:
        if kind == 'rangehash':
            _hi, _sha = exp
            w = range_hash_window(secs, va, _hi)
            if w is not None:
                _off, _span, _nm = w
                iv.append((_off, _off + _span))
            continue
        if kind != 'bytes':
            continue
        off, _n = va2off(secs, va)
        if off is not None:
            iv.append((off, off + len(exp)))
    iv.sort()
    merged = []
    for a, b in iv:
        if merged and a <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])
    covered = sum(b - a for a, b in merged)
    return (len(d) - covered) / len(d) * 100.0 if d else 0.0, max(0, len(d) - covered)


def report_segment_gate(rep, requested=True, untested=None, canonical=None):
    """统一渲染：未请求时也必须显式量化射程，不得静默。"""
    print('[段级基线校验 GATE-SEG01]')
    if not requested:
        print('  [WARN] 段级基线校验未启用（未指定 --segments <baseline.json>）：')
        print('         本次射程仅断言触及的字节 + 段表映射自检，.text/.rdata/.data/.rsrc/.detour/PE头/尾部 的整段篡改不会被发现。')
        if untested:
            print('         实测无检测区域: %.2f%%（%s 字节未被任何判据取过哈希）'
                  % (untested[0], "{:,}".format(untested[1])))
        if canonical:
            print('         仓库中已有规范基线: %s' % canonical.replace('\\', '/'))
        return 0
    if rep is None:
        return 0
    if rep.get('status') == 'BASELINE UNUSABLE':
        print('  [FATAL] 基线不可用/不适用: %s' % rep.get('error'))
        print("  ⇒ 退出码 2（与'内容被篡改'的 1 区分）")
        return 2
    print_segment_gate(rep)
    return rep.get('exit_code', 0)


def parse_claims(path):
    """解析断言行。返回 (claims, errors)。
    严格检查语法、VA、期望字节与 BSS 模式，不静默丢弃任何错误行。
    """
    claims = []
    errors = []
    if not os.path.isfile(path):
        raise FileNotFoundError(f"未找到断言文件: {path}")

    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        for ln, raw in enumerate(f, 1):
            line_str = raw.strip()
            if not line_str:
                continue
            # 允许纯注释行
            if line_str.startswith('#'):
                continue

            parts = raw.split('#', 1)
            content = parts[0].strip()
            label = parts[1].strip() if len(parts) > 1 else ''
            if not content:
                continue

            # BSS 区域断言: bss 0xVA = virtual
            if content.lower().startswith('bss '):
                body = content[4:].strip()
                if '=' not in body:
                    errors.append((ln, raw.strip(), "BSS 声明缺少 '=' 分隔符"))
                    continue
                lhs, rhs = body.split('=', 1)
                lhs_str, rhs_str = lhs.strip(), rhs.strip()
                try:
                    va = int(lhs_str, 16)
                except ValueError:
                    errors.append((ln, raw.strip(), f"BSS 声明 VA 非法十六进制: '{lhs_str}'"))
                    continue
                mode = rhs_str.lower()
                if mode not in ('virtual', 'bss', 'noraw'):
                    errors.append((ln, raw.strip(), f"BSS 声明模式非法: '{rhs_str}' (仅允许 virtual/bss/noraw)"))
                    continue
                claims.append((ln, va, b'', label, 'bss'))
                continue

            # 字节断言: 0xVA = HEX
            if '=' not in content:
                errors.append((ln, raw.strip(), "断言行缺少 '=' 分隔符"))
                continue
            lhs, rhs = content.split('=', 1)
            lhs_str = lhs.strip()
            rhs_str = rhs.strip().replace(' ', '').replace('\t', '')
            # 区间哈希断言: 0xVA1..0xVA2 = SHA256(64hex)（半开区间 [起,止)，qc173 #13 扩展）
            if '..' in lhs_str:
                segs = lhs_str.split('..')
                if len(segs) != 2 or not segs[0].strip() or not segs[1].strip():
                    errors.append((ln, raw.strip(), f"区间哈希断言 LHS 非法: '{lhs_str}' (期望 0xA..0xB)"))
                    continue
                try:
                    va_lo = int(segs[0], 16)
                    va_hi = int(segs[1], 16)
                except ValueError:
                    errors.append((ln, raw.strip(), f"区间哈希断言端点非法十六进制: '{lhs_str}'"))
                    continue
                if va_hi <= va_lo:
                    errors.append((ln, raw.strip(), f"区间哈希断言止端不大于起端: '{lhs_str}'"))
                    continue
                if not rhs_str:
                    errors.append((ln, raw.strip(), "区间哈希期望值为空 (空期望值判 FATAL)"))
                    continue
                if len(rhs_str) != 64:
                    errors.append((ln, raw.strip(), f"区间哈希期望值长度 {len(rhs_str)} ≠ 64 (SHA-256 hex)"))
                    continue
                try:
                    bytes.fromhex(rhs_str)
                except ValueError as e:
                    errors.append((ln, raw.strip(), f"区间哈希期望值非法十六进制: '{rhs_str}' ({e})"))
                    continue
                claims.append((ln, va_lo, (va_hi, rhs_str.lower()), label, 'rangehash'))
                continue
            try:
                va = int(lhs_str, 16)
            except ValueError:
                errors.append((ln, raw.strip(), f"断言 VA 非法十六进制: '{lhs_str}'"))
                continue
            if not rhs_str:
                errors.append((ln, raw.strip(), "期望字节为空 (空期望字节判 FATAL)"))
                continue
            try:
                rawb = bytes.fromhex(rhs_str)
            except ValueError as e:
                errors.append((ln, raw.strip(), f"期望字节非法十六进制: '{rhs.strip()}' ({e})"))
                continue
            claims.append((ln, va, rawb, label, 'bytes'))

    return claims, errors

def selftest(d, secs):
    print('=== 口径自检 ===')
    print('%-8s %-10s %-10s %-12s %s' % ('段', 'VA', 'rawptr', 'VA-rawptr', '映射基准说明'))
    for name, base, vs, rs, rp in secs:
        print('%-8s %08X  %08X  %08X    %s' % (name, base, rp, base - rp,
              'VA−0x400000 等价' if (base - rp) == IMAGE_BASE else '** 与 VA−0x400000 不等价，必须用段映射 **'))
    bad = 0
    print('\n%-10s %-24s %-24s %s' % ('VA', '期望', '实际', '判定/标签'))
    for va, exp, label in SELFTEST:
        off, sec = va2off(secs, va)
        got = d[off:off + len(exp) // 2] if off is not None else b''
        ok = got.hex() == exp
        bad += (not ok)
        print('%-10s %-24s %-24s %s %s' % (hex(va), exp, got.hex(), 'OK' if ok else 'MISMATCH', label))
    # PE 头映射自检：MZ 签名（v3 新增）
    off, sec = va2off(secs, IMAGE_BASE)
    mz_ok = (off == 0 and d[0:2] == b'MZ')
    bad += (not mz_ok)
    print('%-10s %-24s %-24s %s %s' % (hex(IMAGE_BASE), '4d5a', d[0:2].hex() if off == 0 else '-',
          'OK' if mz_ok else 'MISMATCH', 'PE-header MZ（v3 映射）'))
    print('\n自检结果：%s（%d 条锚点，%d 条不一致）' % ('全部通过' if bad == 0 else '存在不一致', len(SELFTEST) + 1, bad))
    return bad

def main():
    ap = argparse.ArgumentParser(description="audit_bytes.py (v4) —— 字节级断言审计工具")
    ap.add_argument('claims', nargs='?', help='断言文件路径')
    ap.add_argument('--exe', default=DEFAULT_EXE, help=f'目标 exe 路径 (默认: {DEFAULT_EXE})')
    ap.add_argument('--json', dest='json_out', help='输出审计报告为 JSON 文件')
    ap.add_argument('--selftest', action='store_true', help='口径自检（映射基准 + 已知锚点）')
    ap.add_argument('--verbose', action='store_true', help='输出详细段映射信息')
    ap.add_argument('--limit', '-n', type=int, default=None, help='限制仅测试前 N 条断言')
    ap.add_argument('--min-claims', type=int, default=None, help='要求最少断言条数 (正整数)')
    ap.add_argument('--segments', '-s', dest='segments', default=None,
                    help='段级 raw SHA-256 基线 JSON (GATE-SEG01，与 verify_anchors.py 同一格式)。'
                         '内容不符 exit 1；基线缺失/损坏/不适用本镜像 exit 2')
    a = ap.parse_args()

    # 参数互斥与有效性校验
    if a.min_claims is not None and a.limit is not None:
        print("[FATAL ERROR] 参数 --min-claims 与 --limit 互斥，严禁同时指定！", file=sys.stderr)
        sys.exit(2)
    if a.min_claims is not None and a.min_claims <= 0:
        print(f"[FATAL ERROR] --min-claims 必须为正整数 (当前值: {a.min_claims})", file=sys.stderr)
        sys.exit(2)
    if a.limit is not None and a.limit <= 0:
        print(f"[FATAL ERROR] --limit 必须为正整数 (当前值: {a.limit})", file=sys.stderr)
        sys.exit(2)
    if a.segments is not None and not a.segments.strip():
        print("[FATAL ERROR] --segments 需要非空的基线 JSON 路径", file=sys.stderr)
        sys.exit(2)

    if not os.path.isfile(a.exe):
        print(f"[FATAL ERROR] 未找到目标二进制文件: {a.exe}", file=sys.stderr)
        sys.exit(2)

    d = load(a.exe)
    secs = sections(d)

    # 段级基线校验（先跑，selftest 与 claims 两条路都要吃它的退出码）
    seg_rep = None
    if a.segments:
        try:
            seg_rep = seg_gate_check(d, a.segments, secs)
        except SegGateError as e:
            seg_rep = {'requested': True, 'baseline_path': a.segments.replace('\\', '/'),
                       'status': 'BASELINE UNUSABLE', 'error': str(e), 'rows': []}
    untested = None
    if not a.segments and a.claims and os.path.isfile(a.claims):
        _pre, _errs = parse_claims(a.claims)
        untested = legacy_untested(d, secs, _pre)
    seg_code = report_segment_gate(seg_rep, requested=bool(a.segments), untested=untested,
                                   canonical=canonical_segment_baseline())

    if a.selftest:
        st_bad = 1 if selftest(d, secs) else 0
        if seg_code == 2:
            sys.exit(2)
        sys.exit(1 if (st_bad or seg_code == 1) else 0)

    if not a.claims:
        ap.error("缺少 claims 断言文件参数 (或指定 --selftest 进行口径自检)")

    if not os.path.isfile(a.claims):
        print(f"[FATAL ERROR] 未找到断言文件: {a.claims}", file=sys.stderr)
        sys.exit(2)

    claims, errors = parse_claims(a.claims)

    for line_no, raw, reason in errors:
        print(f"[格式错误] 第 {line_no} 行: {reason} | 原始行: '{raw}'", file=sys.stderr)

    if len(claims) == 0:
        print("[FATAL ERROR] 断言集为空 (0 条有效断言)，门禁判定失败！", file=sys.stderr)
        sys.exit(2 if seg_code == 2 else 1)

    if a.min_claims is not None and len(claims) < a.min_claims:
        print(f"[FATAL ERROR] 有效断言数不足: {len(claims)} < {a.min_claims} (未达门禁下限)", file=sys.stderr)
        sys.exit(2 if seg_code == 2 else 1)

    if a.limit is not None:
        claims = claims[:a.limit]
        print(f"[提示] 抽样模式: 仅测试前 {a.limit} 条断言 (非全量审计)")

    try:
        from capstone import Cs, CS_ARCH_X86, CS_MODE_32
        md = Cs(CS_ARCH_X86, CS_MODE_32)
    except Exception:
        md = None

    if a.verbose:
        for name, base, vs, rs, rp in secs:
            print('[段] %-8s VA=%08X rawptr=%08X VA-rawptr=%08X' % (name, base, rp, base - rp))

    ok = bad = 0
    rows = []
    print('%-10s %-26s %-22s %-6s %s' % ('VA', '期望字节', '实际字节', '判定', '标签/上下文'))
    print('-' * 110)
    for line_no, va, exp, label, kind in claims:
        if kind == 'rangehash':
            va_hi, exp_sha = exp
            w = range_hash_window(secs, va, va_hi)
            rng = '0x%08X..0x%08X' % (va, va_hi)
            if w is None:
                bad += 1
                rows.append(dict(line=line_no, va=rng, expect=exp_sha, actual=None,
                                 verdict='NOREAD', section='未映射/无raw', label=label, kind='rangehash'))
                print('%-26s %-64s %-64s %-6s %s' % (rng, exp_sha, '-', 'NOREAD', label))
                continue
            off, span, secname = w
            got_sha = hashlib.sha256(d[off:off + span]).hexdigest()
            if got_sha == exp_sha:
                ok += 1
                verdict = 'OK'
            else:
                bad += 1
                verdict = 'MISMATCH'
            rows.append(dict(line=line_no, va=rng, expect=exp_sha, actual=got_sha,
                             verdict=verdict, section=secname, label=label, kind='rangehash'))
            print('%-26s %-64s %-64s %-6s %s [%s, raw %s B]' % (rng, exp_sha, got_sha, verdict, label, secname, span))
            continue
        if kind == 'bss':
            is_bss, secname = va_in_bss(secs, va)
            verdict = 'BSS-OK' if is_bss else 'BSS-FAIL'
            if is_bss:
                ok += 1
            else:
                bad += 1
            rows.append(dict(line=line_no, va=hex(va), expect='virtual', actual=None,
                             verdict=verdict, section=secname, label=label, kind='bss'))
            print('%-10s %-26s %-22s %-6s %s' % (hex(va), 'virtual', '-', verdict, secname + ' ' + label))
            continue
        off, secname = va2off(secs, va)
        if off is None:
            bad += 1
            rows.append(dict(line=line_no, va=hex(va), expect=exp.hex(), actual=None, verdict='NOREAD', section=secname, label=label, kind='bytes'))
            print('%-10s %-26s %-22s %-6s %s' % (hex(va), exp.hex(' '), '-', 'NOREAD', secname + ' ' + label))
            continue
        got = d[off:off + len(exp)]
        verdict = 'OK' if got == exp else 'MISMATCH'
        ctx = ''
        if md:
            for i in md.disasm(d[off:off + 12], va):
                ctx = '%s %s' % (i.mnemonic, i.op_str)
                break
        if verdict == 'OK':
            ok += 1
        else:
            bad += 1
        rows.append(dict(line=line_no, va=hex(va), expect=exp.hex(), actual=got.hex(),
                         verdict=verdict, section=secname, label=label, disasm=ctx, kind='bytes'))
        print('%-10s %-26s %-22s %-6s %s %s' % (hex(va), exp.hex(' '), got.hex(' '), verdict, label, ('| ' + ctx) if ctx else ''))

    print('-' * 110)
    print('合计 %d 条：OK=%d  MISMATCH/NOREAD/BSS-FAIL=%d  格式错误=%d' % (len(claims), ok, bad, len(errors)))
    if a.json_out:
        out_dir = os.path.dirname(a.json_out)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        with open(a.json_out, 'w', encoding='utf-8') as f:
            json.dump(dict(ok=ok, bad=bad, errors=len(errors), rows=rows,
                           segment_gate=seg_rep if a.segments else None,
                           segment_exit_code=seg_code), f, ensure_ascii=False, indent=2)
        print('JSON →', a.json_out)

    all_ok = (bad == 0 and len(errors) == 0 and ok > 0 and seg_code == 0)
    sys.exit(2 if seg_code == 2 else (0 if all_ok else 1))

if __name__ == '__main__':
    main()