#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tools/verify_anchors.py —— 全库一键回归校验套件（生产级）

用途：
  对 RA2/YR (gamemd.exe, ImageBase 0x00400000) 进行字节级断言回归与二进制基线完整性审计。
  1. 验证 .text 代码段基线哈希（★严守 raw(SizeOfRawData) 口径，杜绝虚拟尺寸误报）
  2. 审计 PE 头特征与 0xAE 差异（辨识 ra2opt apply perf 留痕，确认代码段零污染）
  3. 核验 .detour 段原生 "@\\0\\0\\0Dtr\\0" 签名及严禁写入原则
  4. 批量复算 docs/re/anchor_claims.txt 全库 300+ 条决定性锚点断言，输出生产级回归报告
  5. ★GATE-SEG01：--segments <baseline.json> 把门禁射程从「.text 整段 raw + 断言触及字节(实测约 84.2%，
     无检测区约 15.8%)」扩到 PE头+全部段 raw+尾部 overlay = 文件 100% 字节 SHA-256 强校验。

特性：
  - 零重型外部依赖：内置基于 struct 的完整 PE 解析器，无 pefile 亦可 100% 独立运行；
  - 智能优雅降级：自动探测 capstone 反汇编引擎，缺失时平滑退化为十六进制比对模式；
  - 工业级 CLI：支持 --claims, --exe, --json, --verbose, --limit, --min-claims, --segments 等命令行参数。

退出码契约：
  0 = 既有判据全过（且启用段级校验时段级区间也全过）
  1 = 断言 MISMATCH/NOREAD/BSS-FAIL / 格式错误 / 断言集为空 / 未达 --min-claims / 段级 raw 哈希与基线不符
  2 = 参数非法 / 找不到文件或非法二进制 / 段级基线缺失、损坏、schema 不符、不适用于本镜像
      （段级 exit 2 无条件优先；--segments 与 --min-claims/--limit 正交叠加，不加入互斥）

裁决措辞阶梯（GATE-SEG01-A/C，单调收紧，只降不升）：
  [100% ALL PASS] …生产环境可安全放行  —— 当且仅当 --min-claims 显式达标 且 --segments 全过
  [REDUCED-COVERAGE PASS]             —— 存在规范基线但未启用 --segments（明示实测无检测比例）
  [SCOPE-UNDECLARED PASS]             —— 断言数已达台账条数但未声明 --min-claims
  [SUBSET PASS]                       —— 断言数少于台账条数（明示仅覆盖 N 条）
  [SAMPLE PASS]                       —— --limit 抽样（既有语义不变）
  注：台账条数参照值取默认断言文件的真实条数（取不到才回落常量 323 并声明来源），323 不作为硬编码下限。

用法：
  python tools/verify_anchors.py
  python tools/verify_anchors.py --min-claims 323   # 显式全库门禁（323条下限）
  python tools/verify_anchors.py --min-claims 323 --segments out/re_work/work_chain/CONTINUE_20261003/lead/gate_seg/segment_baseline.json   # 完整放行调用式
  python tools/verify_anchors.py docs/re/anchor_claims.txt --verbose
  python tools/verify_anchors.py --limit 10          # 抽样测试（明确标注抽样，禁止称为全库）
  python tools/verify_anchors.py --json out/re_work/re_sprint/S22/verify_report.json
"""

import argparse
import hashlib
import json
import os
import struct
import sys

# 保证控制台 UTF-8 输出无乱码
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

# ==============================================================================
# 基线黄金常数 (Baseline Gold Constants)
# ==============================================================================
DEFAULT_EXE_REL = os.path.join("ra2youli", "gamemd.exe")
DEFAULT_CLAIMS_REL = os.path.join("docs", "re", "anchor_claims.txt")
IMAGE_BASE = 0x00400000

# .text 基线 SHA-256 (严格使用 raw(SizeOfRawData=0x3E0000) 口径，源自 out/reverse/symbols.json)
EXPECTED_TEXT_RAW_SHA256 = "c0368a179f6e1a0f85bf94ebeb3a3e62efc8b1a2000abe164e5e1c61714eb738"
# 虚拟尺寸口径 (Misc_VirtualSize=0x3DF38D) 哈希值（用于误判诊断与警示）
KNOWN_TEXT_VSIZE_SHA256 = "bf9d56aea20a9e52432bbc152e8ff08d334712955e2689455770b8333779908e"

# 原生 .detour 段签名 (@\0\0\0Dtr\0)
DETOUR_HEADER_MAGIC = b"\x40\x00\x00\x00\x44\x74\x72\x00"

# 锚点台账条数兜底值：仅用于"范围措辞"判定，**不作为任何门禁下限**（下限只能由 --min-claims 显式声明）
FULL_CLAIMS_BASELINE_FALLBACK = 323

# 规范段级基线在仓库里的固定位置（GATE-SEG01-C：基线存在却未启用时，必须降级措辞）
CANONICAL_SEGMENT_BASELINE_REL = os.path.join(
    "out", "re_work", "work_chain", "CONTINUE_20261003", "lead", "gate_seg", "segment_baseline.json")


def canonical_segment_baseline(repo_root):
    """返回可用的规范段级基线路径，找不到返回 None。环境变量可覆盖（便于 CI 指定另一构建的基线）。"""
    p = os.environ.get("RA2_SEGMENT_BASELINE")
    if p:
        return p if os.path.isfile(p) else None
    p = os.path.join(repo_root, CANONICAL_SEGMENT_BASELINE_REL)
    return p if os.path.isfile(p) else None


def merge_intervals(iv):
    out = []
    for a, b in sorted(iv):
        if b <= a:
            continue
        if out and a <= out[-1][1]:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return out


def untested_ratio(data_len, text_sec, claim_spans):
    """既有门禁真实射程 = .text 整段 raw + 各条字节断言触及的 raw 区间；返回未覆盖比例(%)。"""
    iv = []
    if text_sec:
        iv.append((text_sec['rptr'], text_sec['rptr'] + text_sec['rsize']))
    iv.extend(claim_spans)
    covered = sum(b - a for a, b in merge_intervals(iv))
    if data_len <= 0:
        return 0.0, covered
    return (data_len - covered) / data_len * 100.0, covered


# ==============================================================================
# 段级基线校验 (Segment-Level Raw SHA-256 Gate) —— GATE-SEG01
# ==============================================================================
SEG_GATE_SCHEMA = 1


class SegGateError(Exception):
    """基线不可用 / 基线不适用于该镜像 => exit 2（与"内容被篡改"的 exit 1 区分）"""


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


def load_segment_baseline(path):
    if not os.path.isfile(path):
        raise SegGateError("基线文件不存在: %s" % path)
    if os.path.getsize(path) == 0:
        raise SegGateError("基线文件为空(0 字节): %s" % path)
    try:
        with open(path, 'r', encoding='utf-8') as f:
            doc = json.load(f)
    except SegGateError:
        raise
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


def true_size_of_headers(d):
    """取真实 SizeOfHeaders，**不做** PEReader 伪节映射里的 `or 0x1000` 回退。
    段级门禁与 audit_bytes.py 用同一严格口径：SizeOfHeaders=0 一律判"基线不适用"(exit 2)，不猜。"""
    pe = struct.unpack_from('<I', d, 0x3C)[0]
    soh = struct.unpack_from('<I', d, pe + 24 + 60)[0]
    if not soh:
        raise SegGateError("SizeOfHeaders=0，无法确定 PE 头区间（段级门禁拒绝回退猜测）")
    return soh


def seg_gate_check(data, path, image_base, size_of_headers, real_sections):
    """real_sections: [(name, va, vsize, rptr, rsize), ...]，按节表顺序，不含 PE 头伪节。
    返回 report(dict)。抛 SegGateError 表示基线不可用/不适用(exit 2)。"""
    rep = {'requested': True, 'baseline_path': path.replace('\\', '/'), 'status': None,
           'rows': [], 'overlay_rows': [], 'policy_notes': [], 'image_identity': None}
    doc = load_segment_baseline(path)
    fsize = len(data)
    declared_size = _seg_int(doc['exe_size'], 'exe_size')
    if fsize != declared_size:
        raise SegGateError("镜像大小 %d 与基线声明 %d 不符 => 基线不适用于本镜像" % (fsize, declared_size))
    declared_base = _seg_int(doc.get('image_base', image_base), 'image_base')
    if declared_base != image_base:
        raise SegGateError("镜像 ImageBase 0x%X 与基线 0x%X 不符" % (image_base, declared_base))

    def add(name, kind, exp, act, va=None, rptr=None, rsize=None, policy=None, note=""):
        rep['rows'].append({'name': name, 'kind': kind, 'expected_sha256': exp, 'actual_sha256': act,
                            'verdict': 'OK' if (act and act == exp) else 'MISMATCH',
                            'va': None if va is None else '0x%08X' % va,
                            'rptr': None if rptr is None else '0x%08X' % rptr,
                            'rsize': rsize, 'policy': policy, 'note': note})

    # --- PE 头 ---
    ph = doc['pe_header']
    declared_soh = _seg_int(ph.get('size_of_headers', ph.get('size')), 'pe_header.size_of_headers')
    if declared_soh != size_of_headers:
        raise SegGateError("镜像 SizeOfHeaders 0x%X 与基线 0x%X 不符 => 基线不适用于本镜像"
                           % (size_of_headers, declared_soh))
    add('PE-header', 'pe_header', ph['sha256'], hashlib.sha256(data[0:declared_soh]).hexdigest(),
        va=image_base, rptr=0, rsize=declared_soh, policy=ph.get('policy', 'STRICT_HASH'),
        note='MZ/DOS 头 + PE 签名 + 可选头 + 节表；节表被改会在此处与结构性检查同时暴露')

    # --- 段：先核结构，再核内容 ---
    actual = {}
    for name, va, vsize, rptr, rsize in real_sections:
        actual.setdefault(name, []).append((va, vsize, rptr, rsize))
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
    missing = [n for (n, *_r) in real_sections if n not in bnames]
    if missing:
        raise SegGateError("基线遗漏镜像真实存在的段 %s —— 拒绝作为放行依据(不得默默缩小射程)" % missing)

    # --- 尾部 overlay ---
    ranges = sorted([(0, declared_soh)] + [(s['rptr'], s['rptr'] + s['rsize']) for s in
                                           [dict(rptr=_seg_int(x['rptr'], 'rptr'), rsize=_seg_int(x['rsize'], 'rsize'))
                                            for x in doc['segments']]])
    merged, cur = [], None
    for a, b in ranges:
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

    # --- 覆盖性红线：基线必须覆盖整份文件 ---
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
    print("%s覆盖 : %s/%s 字节 = %.6f%%" % (prefix, rep['coverage']['bytes_hashed'],
                                            rep['coverage']['file_size'], rep['coverage']['coverage_ratio']))
    for r in rep['rows']:
        mark = '[PASS]' if r['verdict'] == 'OK' else '[FAIL]'
        print("%s%s %-10s %-9s va=%s raw=%s len=%s sha256=%s policy=%s"
              % (prefix, mark, r['name'], r['kind'], r['va'], r['rptr'], r['rsize'],
                 r['actual_sha256'], r['policy']))
        if r['verdict'] != 'OK':
            print("%s       期望 %s" % (prefix, r['expected_sha256']))
    bad = [r for r in rep['rows'] if r['verdict'] != 'OK']
    print("%s段级汇总 : %d 个区间(PE头+各段 raw+尾部)，OK=%d MISMATCH=%d"
          % (prefix, len(rep['rows']), len(rep['rows']) - len(bad), len(bad)))
    return 0


# ==============================================================================
# 内置纯 Python PE 解析器 (Native Pure-Python PE Parser)
# ==============================================================================
class PEReader:
    def __init__(self, raw_bytes: bytes):
        self.data = raw_bytes
        self.size = len(raw_bytes)
        self._parse()

    def _parse(self):
        if self.size < 0x40 or self.data[:2] != b'MZ':
            raise ValueError("无效的 DOS 头部 (未找到 MZ 标志)")
        
        self.e_lfanew = struct.unpack_from('<I', self.data, 0x3C)[0]
        if self.e_lfanew + 0x18 > self.size or self.data[self.e_lfanew:self.e_lfanew+4] != b'PE\0\0':
            raise ValueError("无效的 PE 头部 (未找到 PE\\0\\0 标志)")

        pe_off = self.e_lfanew
        # COFF File Header
        self.machine, self.num_sections = struct.unpack_from('<HH', self.data, pe_off + 4)
        self.timedatestamp = struct.unpack_from('<I', self.data, pe_off + 8)[0]
        self.opt_hdr_size = struct.unpack_from('<H', self.data, pe_off + 20)[0]
        self.characteristics = struct.unpack_from('<H', self.data, pe_off + 22)[0]

        # Optional Header (PE32)
        opt_off = pe_off + 24
        self.magic = struct.unpack_from('<H', self.data, opt_off)[0]
        if self.magic != 0x010B:
            raise ValueError(f"非 PE32 格式镜像 (OptionalHeader.Magic=0x{self.magic:X})")

        self.image_base = struct.unpack_from('<I', self.data, opt_off + 28)[0]
        self.section_alignment = struct.unpack_from('<I', self.data, opt_off + 32)[0]
        self.file_alignment = struct.unpack_from('<I', self.data, opt_off + 36)[0]
        self.size_of_image = struct.unpack_from('<I', self.data, opt_off + 56)[0]
        self.size_of_headers = struct.unpack_from('<I', self.data, opt_off + 60)[0]
        self.subsystem = struct.unpack_from('<H', self.data, opt_off + 68)[0]
        self.dll_characteristics = struct.unpack_from('<H', self.data, opt_off + 70)[0]
        self.size_of_stack_reserve = struct.unpack_from('<I', self.data, opt_off + 72)[0]
        self.size_of_stack_commit = struct.unpack_from('<I', self.data, opt_off + 76)[0]

        # Sections Table
        # PE 头伪节：MZ/PE 签名/可选头/节表位于首节之前，映射 off = VA − ImageBase
        # 与 audit_bytes.py v3 的 PE-header 伪节口径完全对齐，杜绝 0x400000 NOREAD
        soh = self.size_of_headers or 0x1000
        sec_table_off = opt_off + self.opt_hdr_size
        self.sections = [
            {
                'index': -1,
                'name': 'PE-header',
                'va': self.image_base,
                'vsize': soh,
                'rptr': 0,
                'rsize': soh,
                'flags': 0
            }
        ]
        for i in range(self.num_sections):
            entry_off = sec_table_off + i * 40
            name_raw = self.data[entry_off:entry_off+8]
            name = name_raw.rstrip(b'\0').decode('latin1', errors='replace')
            vsize, va, rsize, rptr = struct.unpack_from('<IIII', self.data, entry_off + 8)
            flags = struct.unpack_from('<I', self.data, entry_off + 36)[0]
            self.sections.append({
                'index': i,
                'name': name,
                'va': self.image_base + va,
                'vsize': vsize,
                'rptr': rptr,
                'rsize': rsize,
                'flags': flags
            })

    def get_section(self, name: str):
        for s in self.sections:
            if s['name'].lower() == name.lower():
                return s
        return None

    def va_to_offset(self, va: int):
        """将虚拟地址 (VA) 映射为文件偏移。仅当地址落在文件数据区间内返回 (offset, sec_name)"""
        for s in self.sections:
            sec_start = s['va']
            # 判断地址是否落在段的虚拟空间内
            if sec_start <= va < sec_start + s['vsize']:
                delta = va - sec_start
                # 只有当偏移落在文件原始数据大小 rsize 范围内时，文件才有对应数据
                if delta < s['rsize']:
                    file_offset = s['rptr'] + delta
                    if file_offset < self.size:
                        return file_offset, s['name']
                return None, s['name'] + "(BSS/无文件数据)"
        return None, "未映射(UNMAPPED)"

    def va_in_bss(self, va: int):
        """返回 (is_bss, sec_name)：VA 是否落在节表定义的虚拟零填充 BSS 区域"""
        for s in self.sections:
            sec_start = s['va']
            if sec_start <= va < sec_start + s['vsize']:
                delta = va - sec_start
                if delta >= s['rsize']:
                    return True, s['name']
                return False, s['name']
        return False, "未映射(UNMAPPED)"

    def range_hash_window(self, va_lo: int, va_hi: int):
        """区间哈希 [va_lo,va_hi) → (file_off, span, sec_name) 或 None（qc173 #13）。
        起端须落在某段虚拟范围内且 delta 有 raw 支撑；整段跨度须全部落在该段 raw 之内
        （止端可越过 VirtualSize 至 raw 尾，对应 SizeOfRawData 口径）。"""
        span = va_hi - va_lo
        if span <= 0:
            return None
        for s in self.sections:
            sec_start = s['va']
            if sec_start <= va_lo < sec_start + s['vsize']:
                delta = va_lo - sec_start
                if delta < s['rsize'] and delta + span <= s['rsize']:
                    return s['rptr'] + delta, span, s['name']
                return None
        return None

# ==============================================================================
# 反汇编优雅降级封装 (Disassembly Engine Wrapper)
# ==============================================================================
def get_disassembler():
    try:
        from capstone import Cs, CS_ARCH_X86, CS_MODE_32
        md = Cs(CS_ARCH_X86, CS_MODE_32)
        return md
    except Exception:
        return None

def disassemble_bytes(md, byte_seq: bytes, va: int, max_insn: int = 2) -> str:
    if not md or not byte_seq:
        return ""
    res = []
    try:
        for ins in md.disasm(byte_seq, va):
            res.append(f"{ins.mnemonic} {ins.op_str}".strip())
            if len(res) >= max_insn:
                break
    except Exception:
        pass
    return " ; ".join(res)

# ==============================================================================
# 断言文件解析器 (Claims File Parser)
# ==============================================================================
def parse_claims_file(claims_path: str):
    """
    解析 claims 文本。返回 (claims, errors)。
    支持：
      0x0055DE73 = 8B 15 84 ED A8 00    # 注释说明
      0x6DD8D7 = 8B 56 2C               # 短写格式
      bss 0x0087E180 = virtual          # BSS 区域断言
      0x00401000..0x007E1000 = <64位sha256hex>  # 区间哈希断言（半开区间 [起,止) 映射 raw 字节的 SHA-256，qc173 #13 扩展）
    对空期望、格式错误、非法地址不予静默丢弃，统一记录到 errors 列表中。
    """
    claims = []
    errors = []
    category = "默认分类"
    if not os.path.isfile(claims_path):
        raise FileNotFoundError(f"未找到断言文件: {claims_path}")

    with open(claims_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line_no, raw_line in enumerate(f, 1):
            line = raw_line.strip()
            if not line:
                continue
            # 分类注释头提取
            if line.startswith("# PART") or line.startswith("# === PART"):
                category = line.lstrip("# =").strip()
                continue
            if line.startswith("#"):
                continue

            parts = line.split('#', 1)
            content = parts[0].strip()
            comment = parts[1].strip() if len(parts) > 1 else ""
            if not content:
                continue

            # BSS 区域断言: bss 0xVA = virtual
            if content.lower().startswith('bss '):
                body = content[4:].strip()
                if '=' not in body:
                    errors.append((line_no, raw_line.strip(), "BSS 声明缺少 '=' 分隔符"))
                    continue
                lhs, rhs = body.split('=', 1)
                lhs_str, rhs_str = lhs.strip(), rhs.strip()
                try:
                    va = int(lhs_str, 16)
                except ValueError:
                    errors.append((line_no, raw_line.strip(), f"BSS 声明 VA 非法十六进制: '{lhs_str}'"))
                    continue
                mode = rhs_str.lower()
                if mode not in ('virtual', 'bss', 'noraw'):
                    errors.append((line_no, raw_line.strip(), f"BSS 声明模式非法: '{rhs_str}' (仅允许 virtual/bss/noraw)"))
                    continue
                claims.append({
                    'line_no': line_no,
                    'category': category,
                    'va': va,
                    'expected_bytes': b'',
                    'expected_hex': 'virtual',
                    'comment': comment,
                    'kind': 'bss'
                })
                continue

            # 字节断言: 0xVA = HEX
            if '=' not in content:
                errors.append((line_no, raw_line.strip(), "断言行缺少 '=' 分隔符"))
                continue

            lhs, rhs = content.split('=', 1)
            va_str = lhs.strip()
            hex_str = rhs.strip().replace(' ', '').replace('\t', '')

            # 区间哈希断言: 0xVA1..0xVA2 = SHA256(64hex)（半开区间 [起,止)，qc173 #13 扩展）
            if '..' in va_str:
                segs = va_str.split('..')
                if len(segs) != 2 or not segs[0].strip() or not segs[1].strip():
                    errors.append((line_no, raw_line.strip(), f"区间哈希断言 LHS 非法: '{va_str}' (期望 0xA..0xB)"))
                    continue
                try:
                    va_lo = int(segs[0], 16)
                    va_hi = int(segs[1], 16)
                except ValueError:
                    errors.append((line_no, raw_line.strip(), f"区间哈希断言端点非法十六进制: '{va_str}'"))
                    continue
                if va_hi <= va_lo:
                    errors.append((line_no, raw_line.strip(), f"区间哈希断言止端不大于起端: '{va_str}'"))
                    continue
                if not hex_str:
                    errors.append((line_no, raw_line.strip(), "区间哈希期望值为空 (空期望值判 FATAL)"))
                    continue
                if len(hex_str) != 64:
                    errors.append((line_no, raw_line.strip(), f"区间哈希期望值长度 {len(hex_str)} ≠ 64 (SHA-256 hex)"))
                    continue
                try:
                    bytes.fromhex(hex_str)
                except ValueError as e:
                    errors.append((line_no, raw_line.strip(), f"区间哈希期望值非法十六进制: '{hex_str}' ({e})"))
                    continue
                claims.append({
                    'line_no': line_no,
                    'category': category,
                    'va': va_lo,
                    'va_end': va_hi,
                    'expected_bytes': b'',
                    'expected_hex': hex_str.lower(),
                    'comment': comment,
                    'kind': 'rangehash'
                })
                continue

            try:
                va = int(va_str, 16)
            except ValueError:
                errors.append((line_no, raw_line.strip(), f"断言 VA 非法十六进制: '{va_str}'"))
                continue

            if not hex_str:
                errors.append((line_no, raw_line.strip(), "期望字节为空 (空期望字节判 FATAL)"))
                continue

            try:
                expected_bytes = bytes.fromhex(hex_str)
            except ValueError as e:
                errors.append((line_no, raw_line.strip(), f"期望字节非法十六进制: '{rhs.strip()}' ({e})"))
                continue

            claims.append({
                'line_no': line_no,
                'category': category,
                'va': va,
                'expected_bytes': expected_bytes,
                'expected_hex': expected_bytes.hex(' ').upper(),
                'comment': comment,
                'kind': 'bytes'
            })
    return claims, errors

# ==============================================================================
# 基线完整性核验器 (Baseline Integrity Auditor)
# ==============================================================================
def audit_baseline_integrity(pe: PEReader):
    """
    严格执行三项黄金准则审计：
    1. .text 段 SHA-256（严格使用 raw(SizeOfRawData) 口径，比对 symbols.json 记录值）
    2. PE 头 0xAE/0xB2 处特征核验（识别 ra2opt apply perf 留痕，确认无代码区修改）
    3. .detour 段原生 "Dtr\0" 签名比对与禁写入红线确认
    """
    results = {}
    
    # 1. .text 段校验
    text_sec = pe.get_section(".text")
    if not text_sec:
        results['text_check'] = {'status': 'FAIL', 'reason': '未找到 .text 代码段'}
    else:
        raw_slice = pe.data[text_sec['rptr']:text_sec['rptr'] + text_sec['rsize']]
        vsize_slice = pe.data[text_sec['rptr']:text_sec['rptr'] + text_sec['vsize']]
        
        raw_sha = hashlib.sha256(raw_slice).hexdigest()
        vsize_sha = hashlib.sha256(vsize_slice).hexdigest()
        
        raw_match = (raw_sha.lower() == EXPECTED_TEXT_RAW_SHA256.lower())
        results['text_check'] = {
            'status': 'PASS' if raw_match else 'FAIL',
            'raw_sha256': raw_sha,
            'expected_raw_sha256': EXPECTED_TEXT_RAW_SHA256,
            'vsize_sha256': vsize_sha,
            'vsize_known_sha256': KNOWN_TEXT_VSIZE_SHA256,
            'raw_size': text_sec['rsize'],
            'virtual_size': text_sec['vsize'],
            'raw_match': raw_match,
            'is_vsize_misconception': (vsize_sha.lower() == KNOWN_TEXT_VSIZE_SHA256.lower())
        }

    # 2. PE 头 0xAE/0xB2 留痕分析
    dll_char = pe.dll_characteristics
    stack_res = pe.size_of_stack_reserve
    pe_state = "UNKNOWN"
    if dll_char == 0x0020 and stack_res == 0x00400000:
        pe_state = "RA2OPT_PERF_APPLIED (0xAE=0x20, Stack=4MB, .text未变)"
    elif dll_char == 0x0000 and stack_res == 0x00100000:
        pe_state = "VANILLA_ORIGINAL (0xAE=0x00, Stack=1MB)"
    else:
        pe_state = f"CUSTOM (DllChar=0x{dll_char:04X}, Stack=0x{stack_res:X})"

    results['pe_header'] = {
        'status': 'PASS',
        'state': pe_state,
        'dll_characteristics': hex(dll_char),
        'size_of_stack_reserve': hex(stack_res),
        'e_lfanew': hex(pe.e_lfanew)
    }

    # 3. .detour 段签名核验
    detour_sec = pe.get_section(".detour")
    if not detour_sec:
        results['detour_check'] = {'status': 'MISSING', 'reason': '未找到 .detour 段'}
    else:
        detour_head = pe.data[detour_sec['rptr']:detour_sec['rptr'] + 8]
        has_magic = (detour_head == DETOUR_HEADER_MAGIC)
        results['detour_check'] = {
            'status': 'PASS' if has_magic else 'SIGNATURE_MISMATCH',
            'va': hex(detour_sec['va']),
            'rptr': hex(detour_sec['rptr']),
            'vsize': hex(detour_sec['vsize']),
            'rsize': hex(detour_sec['rsize']),
            'head_bytes': detour_head.hex(' ').upper(),
            'has_dtr_magic': has_magic,
            'policy': 'STRICT_FORBID_INJECTION'
        }

    return results

# ==============================================================================
# 回归校验主流程 (Main Regression Engine)
# ==============================================================================
def resolve_claims_scope_baseline(repo_root):
    """读取锚点台账默认文件的真实条数，作为"范围措辞"的参照值。
    它**不是**门禁下限（下限只能由 --min-claims 显式声明），所以宁可动态取也不要钉死数字。"""
    path = os.path.join(repo_root, DEFAULT_CLAIMS_REL)
    try:
        claims, _errors = parse_claims_file(path)
        if not claims:
            raise ValueError("默认断言文件解析出 0 条")
        return len(claims), "default_claims_file(%s)" % DEFAULT_CLAIMS_REL.replace('\\', '/')
    except Exception as e:
        return FULL_CLAIMS_BASELINE_FALLBACK, "fallback_constant(取不到默认断言文件: %s)" % e


def claims_scope_kind(report):
    """断言维度的范围：'declared-gate' | 'sampling' | 'undeclared-full' | 'subset'
    —— 只影响措辞强度，不影响退出码。段级维度由 segment_gate.requested 单独决定，
    在裁决阶梯里优先级更高（GATE-SEG01-C）。"""
    if report['min_claims'] is not None:
        return 'declared-gate'
    if report['is_sampling']:
        return 'sampling'
    if report['total_parsed_claims'] >= report['claims_scope_baseline']:
        return 'undeclared-full'
    return 'subset'


def run_verification(claims_path: str, exe_path: str, verbose: bool = False, limit: int = None,
                     min_claims: int = None, segments_path: str = None,
                     scope_baseline: int = None, scope_basis: str = "",
                     canonical_baseline: str = None):
    if not os.path.isfile(exe_path):
        raise FileNotFoundError(f"未找到目标二进制文件: {exe_path}")
    
    with open(exe_path, 'rb') as f:
        raw_bytes = f.read()
    
    pe = PEReader(raw_bytes)
    md = get_disassembler()
    claims, errors = parse_claims_file(claims_path)
    for line_no, raw_line, reason in errors:
        print(f"[格式错误] 第 {line_no} 行: {reason} | 原始行: '{raw_line}'", file=sys.stderr)

    total_parsed_claims = len(claims)
    is_sampling = (limit is not None and limit > 0)
    if is_sampling:
        claims = claims[:limit]

    integrity = audit_baseline_integrity(pe)

    # 段级基线校验（GATE-SEG01）
    if segments_path:
        real = [(s['name'], s['va'], s['vsize'], s['rptr'], s['rsize'])
                for s in pe.sections if s['index'] >= 0]
        try:
            segment_gate = seg_gate_check(raw_bytes, segments_path, pe.image_base,
                                          true_size_of_headers(raw_bytes), real)
        except SegGateError as e:
            segment_gate = {'requested': True, 'baseline_path': segments_path.replace('\\', '/'),
                            'status': 'BASELINE UNUSABLE', 'error': str(e), 'rows': [],
                            'coverage': {'file_size': pe.size, 'bytes_hashed': 0, 'coverage_ratio': 0.0},
                            'exit_code': 2}
    else:
        segment_gate = {'requested': False, 'status': 'NOT REQUESTED', 'exit_code': 0, 'rows': []}
    
    # 逐条断言校验
    verified_rows = []
    ok_count = 0
    fail_count = 0
    noread_count = 0
    claim_spans = []          # 断言触及的 raw 区间，用于如实计算"未检测区域"比例

    for item in claims:
        va = item['va']
        kind = item.get('kind', 'bytes')

        if kind == 'bss':
            is_bss, sec_name = pe.va_in_bss(va)
            if is_bss:
                ok_count += 1
                verdict = "BSS-OK"
            else:
                fail_count += 1
                verdict = "BSS-FAIL"
            verified_rows.append({
                'line_no': item['line_no'],
                'category': item['category'],
                'va': f"0x{va:08X}",
                'offset': "N/A(VIRTUAL)",
                'section': sec_name,
                'expected_hex': "virtual",
                'actual_hex': "N/A",
                'verdict': verdict,
                'comment': item['comment'],
                'disasm': ""
            })
            continue

        if kind == 'rangehash':
            va_end = item['va_end']
            exp_sha = item['expected_hex']
            w = pe.range_hash_window(va, va_end)
            rng = f"0x{va:08X}..0x{va_end:08X}"
            if w is None:
                noread_count += 1
                verdict = "NOREAD"
                actual_hex = "N/A"
                sec0 = "未映射/无raw"
                off0 = None
            else:
                off0, span, sec0 = w
                claim_spans.append((off0, off0 + span))
                got_sha = hashlib.sha256(raw_bytes[off0:off0 + span]).hexdigest()
                actual_hex = got_sha
                if got_sha == exp_sha:
                    ok_count += 1
                    verdict = "OK"
                else:
                    fail_count += 1
                    verdict = "MISMATCH"
            verified_rows.append({
                'line_no': item['line_no'],
                'category': item['category'],
                'va': rng,
                'offset': f"0x{off0:06X}" if off0 is not None else "N/A",
                'section': sec0,
                'expected_hex': exp_sha,
                'actual_hex': actual_hex,
                'verdict': verdict,
                'comment': item['comment'],
                'disasm': ""
            })
            continue

        exp = item['expected_bytes']
        off, sec_name = pe.va_to_offset(va)

        if off is None:
            noread_count += 1
            verdict = "NOREAD"
            actual_bytes = b""
            actual_hex = "N/A"
            disasm = ""
        else:
            claim_spans.append((off, off + len(exp)))
            actual_bytes = raw_bytes[off:off + len(exp)]
            actual_hex = actual_bytes.hex(' ').upper()
            if actual_bytes == exp:
                ok_count += 1
                verdict = "OK"
            else:
                fail_count += 1
                verdict = "MISMATCH"

            # 抓取反汇编
            disasm = disassemble_bytes(md, actual_bytes if verdict == "OK" else raw_bytes[off:off+12], va)

        verified_rows.append({
            'line_no': item['line_no'],
            'category': item['category'],
            'va': f"0x{va:08X}",
            'offset': f"0x{off:06X}" if off is not None else "N/A",
            'section': sec_name,
            'expected_hex': item['expected_hex'],
            'actual_hex': actual_hex,
            'verdict': verdict,
            'comment': item['comment'],
            'disasm': disasm
        })

    untested_pct, covered_bytes = untested_ratio(
        pe.size, pe.get_section('.text'), claim_spans)
    return {
        'exe_path': exe_path,
        'claims_path': claims_path,
        'image_base': hex(pe.image_base),
        'file_size': pe.size,
        'integrity': integrity,
        'segment_gate': segment_gate,
        'segment_gate_path': segments_path,
        'segment_exit_code': segment_gate.get('exit_code', 0),
        'legacy_covered_bytes': covered_bytes,
        'legacy_untested_ratio_percent': round(untested_pct, 4),
        'canonical_segment_baseline': canonical_baseline,
        'claims_scope_baseline': scope_baseline,
        'claims_scope_basis': scope_basis,
        'capstone_available': md is not None,
        'total_claims': len(claims),
        'total_parsed_claims': total_parsed_claims,
        'ok_count': ok_count,
        'fail_count': fail_count,
        'noread_count': noread_count,
        'error_count': len(errors),
        'errors': errors,
        'pass_rate': (ok_count / len(claims) * 100.0) if claims else 0.0,
        'is_sampling': is_sampling,
        'limit_value': limit,
        'min_claims': min_claims,
        'rows': verified_rows
    }

# ==============================================================================
# 控制台报告渲染 (Console Report Renderer)
# ==============================================================================
def print_console_report(report: dict, verbose: bool = False):
    print("=" * 115)
    print("  RA2/YR 二进制决定性锚点自动化回归测试套件 (verify_anchors.py)")
    print("=" * 115)
    print(f"目标文件 : {report['exe_path']} (大小: {report['file_size']:,} 字节, ImageBase: {report['image_base']})")
    print(f"断言文件 : {report['claims_path']}")
    print(f"反汇编器 : {'Capstone x86-32 引擎已就绪' if report['capstone_available'] else '未检测到 Capstone (使用原生Hex比对)'}")
    print("-" * 115)

    # 1. 基线完整性核验汇报
    integ = report['integrity']
    print("[基线完整性审计]")
    text_chk = integ.get('text_check', {})
    if text_chk.get('status') == 'PASS':
        print(f"  [PASS] .text 原始段哈希: {text_chk['raw_sha256']} (口径: raw(SizeOfRawData=0x{text_chk['raw_size']:X}))")
    else:
        print(f"  [FAIL] .text 原始段哈希不匹配! 实际: {text_chk.get('raw_sha256')} 期望: {text_chk.get('expected_raw_sha256')}")
        if text_chk.get('is_vsize_misconception'):
            print(f"         ★警告：检测到当前计算命中了 Misc_VirtualSize 口径 ({text_chk.get('vsize_sha256')})！请确保以 rawsize 统一核算。")

    pe_hdr = integ.get('pe_header', {})
    print(f"  [INFO] PE头特征判定 : {pe_hdr.get('state')} (DllChar: {pe_hdr.get('dll_characteristics')}, StackReserve: {pe_hdr.get('size_of_stack_reserve')})")

    detour_chk = integ.get('detour_check', {})
    seg_req = bool(report.get('segment_gate', {}).get('requested'))
    if detour_chk.get('status') == 'PASS':
        print(f"  [PASS] .detour 原生签名: {detour_chk['head_bytes']} ('@\\0\\0\\0Dtr\\0' @ VA {detour_chk['va']}) -> 严禁写入/注入原则确立")
    else:
        print(f"  [WARN] .detour 段状态异常: {detour_chk}")
    if not seg_req:
        print("  [SCOPE] .detour 完整性说明: 签名 8 字节由锚点断言覆盖；整段(raw=%s)其余字节仅在 --segments 段级哈希下受检。"
              % detour_chk.get('rsize', '?'))
    print("-" * 115)

    # 1.5 段级基线校验 (GATE-SEG01)
    sg = report.get('segment_gate', {})
    print("[段级基线校验 GATE-SEG01]")
    if seg_req:
        if sg.get('status') == 'BASELINE UNUSABLE':
            print(f"  [FATAL] 基线不可用/不适用: {sg.get('error')}")
            print("  ⇒ 退出码 2（与'内容被篡改'的 1 区分）")
        else:
            print_segment_gate(sg)
    else:
        print("  [WARN] 段级基线校验未启用（未指定 --segments <baseline.json>）：")
        print("         本次射程仅 .text 整段 raw 哈希 + 断言覆盖字节，.rdata/.data/.rsrc/.detour/PE头/尾部 的篡改不会被发现。")
        print("         实测无检测区域: %.2f%%（%s 字节未被任何判据取过哈希）"
              % (report.get('legacy_untested_ratio_percent', 0.0),
                 "{:,}".format(max(0, report['file_size'] - report.get('legacy_covered_bytes', 0)))))
        cb = report.get('canonical_segment_baseline')
        if cb:
            print("         仓库中已有规范基线: %s" % cb.replace('\\', '/'))
    print("-" * 115)

    # 2. 逐条断言明细展示
    if verbose or report['fail_count'] > 0 or report['noread_count'] > 0:
        print(f"{'VA':<12} {'段':<8} {'期望字节':<22} {'实际字节':<22} {'判定':<8} {'说明 / 反汇编上下文'}")
        print("-" * 115)
        for r in report['rows']:
            # 在非 verbose 模式下只打印失败项
            if not verbose and r['verdict'] in ('OK', 'BSS-OK'):
                continue
            ctx = f"| {r['disasm']}" if r['disasm'] else ""
            desc = f"{r['comment']} {ctx}".strip()
            print(f"{r['va']:<12} {r['section']:<8} {r['expected_hex'][:20]:<22} {r['actual_hex'][:20]:<22} {r['verdict']:<8} {desc}")
        print("-" * 115)

    # 3. 汇总大卡片
    total = report['total_claims']
    ok = report['ok_count']
    fail = report['fail_count']
    noread = report['noread_count']
    errors = report['error_count']
    rate = report['pass_rate']
    text_ok = report['integrity'].get('text_check', {}).get('status') == 'PASS'
    has_claims = (total > 0)
    min_claims_met = True
    if report['min_claims'] is not None:
        min_claims_met = (report['total_parsed_claims'] >= report['min_claims'])
    sgate = report.get('segment_gate', {})
    seg_ok = (report.get('segment_exit_code', 0) == 0)
    scope = claims_scope_kind(report)

    all_clean = (fail == 0 and noread == 0 and errors == 0 and text_ok and has_claims
                 and min_claims_met and seg_ok)

    err_suffix = f" | 格式错误: {errors}" if errors > 0 else ""
    print(f"回归汇总 : 断言总数 {total} 条 | PASS: {ok} ({rate:.2f}%) | FAIL: {fail} | NOREAD: {noread}{err_suffix}")

    n_parsed = report['total_parsed_claims']
    scope_base = report.get('claims_scope_baseline')
    if not has_claims:
        print("★ 最终裁决 : [REGRESSION DETECTED] 断言集为空 (0 条有效断言)，门禁判定失败，严禁放行！")
    elif not min_claims_met:
        print(f"★ 最终裁决 : [REGRESSION DETECTED] 断言数不足 ({n_parsed} < {report['min_claims']})，未达门禁下限，严禁放行！")
    elif not seg_ok and sgate.get('status') == 'BASELINE UNUSABLE':
        print("★ 最终裁决 : [GATE-SEG01 FATAL] 段级基线不可用或不适用本镜像，门禁无法收敛，严禁放行！(退出码 2)")
    elif not all_clean:
        if not seg_ok:
            print("★ 最终裁决 : [REGRESSION DETECTED] 段级 raw 哈希与基线不符（二进制内容已被改动），严禁放行！")
        else:
            print("★ 最终裁决 : [REGRESSION DETECTED] 存在不匹配断言、格式错误或基线异常，请查阅明细排查！")
    else:
        seg_requested = bool(sgate.get('requested'))
        if report['is_sampling']:
            print(f"★ 最终裁决 : [SAMPLE PASS] 抽样锚点测试通过 (限制前 {report['limit_value']} 条，明示范围为抽样，非全库验证，严禁作为生产安全放行依据！)")
            if not seg_requested:
                print(f"            另：段级 raw 哈希未启用，本镜像约 {report['legacy_untested_ratio_percent']:.2f}% 字节处于无检测区域，抽样结果更不构成放行依据。")
        elif not seg_requested:
            cb = report.get('canonical_segment_baseline')
            if scope == 'subset':
                claims_part = "本次仅覆盖 %d 条断言（锚点台账共 %s 条），范围不足" % (n_parsed, scope_base)
            elif scope == 'undeclared-full':
                claims_part = "%d 条断言全部一致但未声明 --min-claims 下限" % n_parsed
            else:
                claims_part = "%d/%d 条断言一致且已声明 --min-claims %s" % (
                    n_parsed, n_parsed, report['min_claims'])
            print(f"★ 最终裁决 : [REDUCED-COVERAGE PASS] {claims_part}；但段级 raw 哈希未启用："
                  f"本镜像约 {report['legacy_untested_ratio_percent']:.2f}% 字节（.rdata/.data/.rsrc/.detour/PE头/尾部）处于无检测区域，非生产放行依据。")
            print(f"            完整放行调用式（两条件缺一不可）: python tools/verify_anchors.py --min-claims {report['claims_scope_baseline']}"
                  f" --segments {cb.replace(chr(92), '/') if cb else '<segment_baseline.json>'}")
        elif scope == 'declared-gate':
            print("★ 最终裁决 : [100% ALL PASS] 全库决定性锚点与二进制基线完全一致，生产环境可安全放行！")
        elif scope == 'undeclared-full':
            print(f"★ 最终裁决 : [SCOPE-UNDECLARED PASS] {n_parsed}/{n_parsed} 条锚点与二进制基线一致，"
                  f"但本次未声明 --min-claims 门禁下限，不构成放行依据（如需放行级结论请加 --min-claims {scope_base}）。")
        else:
            print(f"★ 最终裁决 : [SUBSET PASS] 本次仅覆盖 {n_parsed} 条断言（锚点台账共 {scope_base} 条），"
                  f"范围不足，严禁作为放行依据；如需放行级结论请加 --min-claims {scope_base}。")
    print("=" * 115)

# ==============================================================================
# CLI 主入口 (CLI Entry Point)
# ==============================================================================
def main():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    default_exe = os.path.join(repo_root, DEFAULT_EXE_REL)
    default_claims = os.path.join(repo_root, DEFAULT_CLAIMS_REL)

    parser = argparse.ArgumentParser(
        description="RA2/YR 二进制决定性锚点自动化回归测试套件 (verify_anchors.py)"
    )
    parser.add_argument("claims_pos", nargs="?", default=None, help="锚点断言文件路径 (可选位置参数)")
    parser.add_argument("--claims", "-c", dest="claims_opt", default=None, help="锚点断言文件路径 (默认: docs/re/anchor_claims.txt)")
    parser.add_argument("--exe", "-e", default=default_exe, help=f"目标 exe 路径 (默认: {DEFAULT_EXE_REL})")
    parser.add_argument("--json", "-j", dest="json_out", default=None, help="输出回归测试报告为 JSON 文件")
    parser.add_argument("--verbose", "-v", action="store_true", help="显示全部断言的逐条明细输出")
    parser.add_argument("--limit", "-n", type=int, default=None, help="限制仅测试前 N 条断言 (抽样模式，与 --min-claims 互斥)")
    parser.add_argument("--min-claims", "-m", type=int, default=None, help="要求最少断言条数 (正整数，显式全库门禁使用 323，与 --limit 互斥)")
    parser.add_argument("--segments", "-s", dest="segments", default=None,
                        help="段级 raw SHA-256 基线 JSON (GATE-SEG01)。内容不符 exit 1；基线缺失/损坏/不适用本镜像 exit 2")

    args = parser.parse_args()
    claims_path = args.claims_pos or args.claims_opt or default_claims

    # 参数互斥与有效性校验
    if args.min_claims is not None and args.limit is not None:
        print("[FATAL ERROR] 参数 --min-claims 与 --limit 互斥，严禁同时指定！", file=sys.stderr)
        sys.exit(2)
    if args.min_claims is not None and args.min_claims <= 0:
        print(f"[FATAL ERROR] --min-claims 必须为正整数 (当前值: {args.min_claims})", file=sys.stderr)
        sys.exit(2)
    if args.limit is not None and args.limit <= 0:
        print(f"[FATAL ERROR] --limit 必须为正整数 (当前值: {args.limit})", file=sys.stderr)
        sys.exit(2)
    if args.segments is not None and not args.segments.strip():
        print("[FATAL ERROR] --segments 需要非空的基线 JSON 路径", file=sys.stderr)
        sys.exit(2)

    scope_baseline, scope_basis = resolve_claims_scope_baseline(repo_root)

    try:
        report = run_verification(
            claims_path=claims_path,
            exe_path=args.exe,
            verbose=args.verbose,
            limit=args.limit,
            min_claims=args.min_claims,
            segments_path=args.segments,
            scope_baseline=scope_baseline,
            scope_basis=scope_basis,
            canonical_baseline=canonical_segment_baseline(repo_root)
        )
    except Exception as e:
        print(f"[FATAL ERROR] 回归套件执行失败: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(2)

    print_console_report(report, verbose=args.verbose)
    print(f"[SCOPE] 断言条数参照值 : {scope_baseline} (来源: {scope_basis}) "
          f"—— 该值只决定裁决措辞强度，不是门禁下限；下限须由 --min-claims 显式声明")

    if args.json_out:
        out_dir = os.path.dirname(os.path.abspath(args.json_out))
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        with open(args.json_out, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"[JSON] 详细测试报告已导出至: {args.json_out}")

    # 退出码：既有判据不变（全部断言通过、无格式错误、非空、满足 min_claims、.text 校验通过 -> 0）；
    # 叠加段级基线：基线不可用/不适用=2（最高优先级），段级内容不符=1（与回归同级）
    text_ok = report['integrity'].get('text_check', {}).get('status') == 'PASS'
    has_claims = (report['total_claims'] > 0)
    min_claims_met = True
    if report['min_claims'] is not None:
        min_claims_met = (report['total_parsed_claims'] >= report['min_claims'])
    all_ok = (report['fail_count'] == 0 and report['noread_count'] == 0 and report['error_count'] == 0 and text_ok and has_claims and min_claims_met)
    seg_code = report.get('segment_exit_code', 0)
    if seg_code == 2:
        sys.exit(2)
    sys.exit(0 if (all_ok and seg_code == 0) else 1)

if __name__ == "__main__":
    main()
