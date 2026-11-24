# -*- coding: utf-8 -*-
"""W130_atlas/glm/vtable_audit.py — gamemd.exe (RA2/YR) 虚表独立抽查。

gamemd.exe 只读。全部输出写在本脚本所在目录 (W130_atlas\\glm\\)。

任务口径:
  1) 扫 .rdata/.data, 4 字节步进, 把 pos 处 dword 当候选 COL 指针;
     COL 自洽 = pTypeDescriptor 落在 .rdata/.data 且 [pTD+8..] 以 '.?AV'/'.?AU' 开头
     => pos+4 记为候选虚表起点, 解出类名; 按 vt 去重。
  2) 统计候选总数 / 类名总数 / 按段分布。
  3) random.seed(20261115) 抽 40 个详查 (槽 0..11 是否 .text / 判定)。
  4) 单列 "槽0为代码但槽1/2既非代码也非0" 的候选 (前 10 全槽值)。
  5) 深查疑点 0x007E1F24 / 0x007E1F2C (.?AVAbstractClass@@)。
判定规则: 从槽 0 起连续为代码指针(或 0 / _purecall), 直到第一个既非代码也非 0 的槽。
"""
import bisect
import hashlib
import json
import os
import random
import struct
import sys
import traceback
from collections import Counter, defaultdict

import pefile
import capstone

EXE_PATH   = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
HERE       = os.path.dirname(os.path.abspath(__file__))
IMAGE_BASE = 0x400000
EXPECT_SHA = "73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476"
SEED, SAMPLE_N, NSLOTS = 20261115, 40, 12
ANOM = (0x007E1F24, 0x007E1F2C)
IMG_LO, IMG_HI = 0x00401000, 0x00B7A000

STATED = {'.text':  (0x00401000, 0x007E038D),
          '.rdata': (0x007E1000, 0x00811074),
          '.data':  (0x00812000, 0x00B79BE4)}

sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')
NOTES = []

with open(EXE_PATH, 'rb') as _f:
    RAW = _f.read()
SHA = hashlib.sha256(RAW).hexdigest().upper()
pe = pefile.PE(data=RAW, fast_load=True)
pe.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_IMPORT']])

SECTS = []
for s in pe.sections:
    SECTS.append({'name': s.Name.rstrip(b'\x00').decode('ascii', 'replace'),
                  'va': IMAGE_BASE + s.VirtualAddress,
                  'vsize': s.Misc_VirtualSize or s.SizeOfRawData,
                  'rawsize': s.SizeOfRawData,
                  'rawptr': s.PointerToRawData})
SEC = {s['name']: s for s in SECTS}
for _n in ('.text', '.rdata', '.data'):
    if _n not in SEC:
        raise SystemExit('missing section ' + _n)


def sect_of_va(va):
    for s in SECTS:
        if s['va'] <= va < s['va'] + max(s['vsize'], s['rawsize']):
            return s
    return None


def read_va(va, n):
    """按段表 + 原始文件字节读取; 超出 SizeOfRawData (BSS) 一律返回 None。"""
    s = sect_of_va(va)
    if s is None:
        return None
    off = va - s['va']
    if off + n > s['rawsize']:
        return None
    fo = s['rawptr'] + off
    if fo + n > len(RAW):
        return None
    return RAW[fo:fo + n]


def rd32(va):
    b = read_va(va, 4)
    return struct.unpack('<I', b)[0] if (b is not None and len(b) == 4) else None


def cstr(va, maxlen=224):
    b = read_va(va, maxlen)
    if b is None:
        return None
    i = b.find(b'\x00')
    return b[:i] if i >= 0 else None


MD = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
MD.skipdata = True  # 纪律2: 遇不可解码字节继续, 不静默停止


def disasm(va, n=3):
    b = read_va(va, 20)
    if b is None:
        return '(no raw bytes)'
    out = []
    try:
        for ins in MD.disasm(b, va):
            out.append('%s %s' % (ins.mnemonic, ins.op_str))
            if len(out) >= n:
                break
    except Exception as e:
        return '(disasm error %s)' % e
    return ' | '.join(out) if out else '(undecodable)'


# ---------------- IAT 与 _purecall 识别 ----------------
IAT = {}
for entry in getattr(pe, 'DIRECTORY_ENTRY_IMPORT', []):
    dll = entry.dll.decode('ascii', 'replace').lower()
    for imp in entry.imports:
        if imp.address:
            IAT[int(imp.address)] = (dll,
                                     imp.name.decode('ascii', 'replace') if imp.name
                                     else 'ord%d' % imp.ordinal)

PURECALL = set()
PURECALL_IAT = [slot for slot, (d, f) in IAT.items() if f == '_purecall']
_t = SEC['.text']
_TEXT_BLOB = RAW[_t['rawptr']:_t['rawptr'] + _t['rawsize']]
for _slot in PURECALL_IAT:
    _needle = b'\xff\x25' + struct.pack('<I', _slot)
    _i = _TEXT_BLOB.find(_needle)
    while _i != -1:
        PURECALL.add(_t['va'] + _i)
        _i = _TEXT_BLOB.find(_needle, _i + 1)


def disp_name(nmb):
    try:
        t = nmb[4:]
        if t.endswith(b'@@'):
            t = t[:-2]
        parts = [p for p in t.split(b'@') if p]
        if not parts:
            return nmb.decode('ascii', 'replace')
        return '::'.join(p.decode('ascii', 'replace') for p in reversed(parts))
    except Exception:
        return nmb.decode('ascii', 'replace')


def resolve_field(v):
    """COL 内部指针字段: 先按绝对 VA 解释, 再按 RVA+ImageBase 解释。"""
    if v is None:
        return (None, None)
    if sect_of_va(v) is not None and read_va(v, 4) is not None:
        return (v, 'VA')
    v2 = (v + IMAGE_BASE) & 0xFFFFFFFF
    if sect_of_va(v2) is not None and read_va(v2, 4) is not None:
        return (v2, 'RVA')
    return (None, None)


def td_struct_ok(td_va):
    """TD 结构校验: [+0]=type_info vftable 指针(指向 .rdata/.data), [+4]=spare==0。"""
    d0, d1 = rd32(td_va), rd32(td_va + 4)
    if d0 is None or d1 is None:
        return False
    s0 = sect_of_va(d0)
    return bool(s0 and s0['name'] in ('.rdata', '.data')) and d1 == 0


def validate_col(col_va):
    """任务规格的 COL 自洽校验 (+记录 TD 结构佐证, 不作为入选条件)。"""
    b = read_va(col_va, 0x14)
    if b is None or len(b) < 0x14:
        return None
    sig, off, cdoff, tdf, chdf = struct.unpack('<5I', b)
    td_va, td_mode = resolve_field(tdf)
    if td_va is None:
        return None
    s = sect_of_va(td_va)
    if s is None or s['name'] not in ('.rdata', '.data'):
        return None
    nm = cstr(td_va + 8)
    if nm is None:
        return None
    if not (nm.startswith(b'.?AV') or nm.startswith(b'.?AU')):
        return None
    chd_va, chd_mode = resolve_field(chdf)
    return {'addr': col_va, 'sig': sig, 'offset': off, 'cd_offset': cdoff,
            'td': td_va, 'td_mode': td_mode, 'chd': chd_va, 'chd_mode': chd_mode,
            'name_raw': nm.decode('ascii', 'replace'), 'name_disp': disp_name(nm),
            'td_struct_ok': td_struct_ok(td_va)}


COL_CACHE = {}


def col_at(va):
    if va is None or va < IMG_LO or va >= IMG_HI:
        return None
    if va in COL_CACHE:
        return COL_CACHE[va]
    c = validate_col(va)
    COL_CACHE[va] = c
    return c


def td_name_at(va):
    d0 = rd32(va)
    nm = cstr(va + 8)
    if d0 is None or nm is None or not nm.startswith(b'.?A'):
        return None
    s0 = sect_of_va(d0)
    if s0 is None or s0['name'] not in ('.rdata', '.data'):
        return None
    return nm


def classify(v):
    """槽值分类: C=.text代码, P=_purecall跳转, 0=零, D=数据指针, X=未映射, B=无文件字节。"""
    if v is None:
        return ('?', '')
    if v == 0:
        return ('0', '')
    s = sect_of_va(v)
    if s is None:
        return ('X', 'unmapped')
    if read_va(v, 1) is None:
        return ('B', 'no-raw')
    n = s['name']
    if n == '.text':
        return ('P', '') if v in PURECALL else ('C', '')
    if n in ('.rdata', '.data'):
        c = col_at(v)
        if c:
            return ('D', 'COL:%s(off=%d)' % (c['name_disp'], c['offset']))
        nm = td_name_at(v)
        if nm:
            return ('D', 'TD:%s' % disp_name(nm))
        return ('D', '')
    return ('D', n)


# ================= 1. 扫描 =================
print('[1] scanning .rdata/.data for COL-anchored vtable candidates ...')
cand = {}
col_refs = defaultdict(list)
td_mode_hist = Counter()
for _nm in ('.rdata', '.data'):
    _s = SEC[_nm]
    for _o in range(0, _s['rawsize'] - 3, 4):
        _v = struct.unpack_from('<I', RAW, _s['rawptr'] + _o)[0]
        if _v < IMG_LO or _v >= IMG_HI:
            continue
        _c = col_at(_v)
        if _c is None:
            continue
        td_mode_hist[_c['td_mode']] += 1
        _pos = _s['va'] + _o
        _vt = _pos + 4
        col_refs[_c['addr']].append(_pos)
        if _vt in cand:
            continue
        _pt, _pa = classify(rd32(_pos - 4))
        _nv = rd32(_pos + 4)
        _nt, _na = classify(_nv)
        cand[_vt] = {'vt': _vt, 'pos': _pos, 'col': _c['addr'], 'sig': _c['sig'],
                     'offset': _c['offset'], 'cd_offset': _c['cd_offset'],
                     'td': _c['td'], 'td_mode': _c['td_mode'],
                     'chd': _c['chd'], 'chd_mode': _c['chd_mode'],
                     'name_raw': _c['name_raw'], 'name_disp': _c['name_disp'],
                     'td_struct_ok': _c['td_struct_ok'], 'sec': _nm,
                     'prev': _pt + ((':' + _pa) if _pa else ''),
                     'next_val': _nv,
                     'next': _nt + ((':' + _na) if _na else '')}

VT_SET = set(cand)
print('[1] candidates = %d' % len(cand))


def count_refs(val, names, cap=500):
    if val is None or val == 0:
        return 0
    needle = struct.pack('<I', val)
    total = 0
    for nm in names:
        s = SEC[nm]
        blob = RAW[s['rawptr']:s['rawptr'] + s['rawsize']]
        i = blob.find(needle)
        while i != -1:
            total += 1
            if total >= cap:
                return cap
            i = blob.find(needle, i + 1)
    return total


def slots_of(vt):
    out = []
    for i in range(NSLOTS):
        v = rd32(vt + 4 * i)
        t, a = classify(v)
        out.append({'i': i, 'val': v, 'tag': t, 'ann': a})
    return out


def verdict_of(rec, slots):
    ok = ('C', 'P', '0')
    run, k, bad = 0, NSLOTS, None
    for sl in slots:
        if sl['tag'] in ok:
            run += 1
        else:
            k, bad = sl['i'], sl
            break
    rec['run'] = run
    if k == NSLOTS:
        codes = [sl for sl in slots if sl['tag'] != '0']
        pure = bool(codes) and all(sl['tag'] == 'P' for sl in codes)
        return 'REAL_VTABLE', ('槽0..11 全为代码或0; ' +
                               ('全部代码槽=_purecall => 抽象类虚表特征' if pure else '连续代码指针'))
    if k == 0:
        return 'NOT_VTABLE', 'slot0=0x%08X 为 %s(%s), 不是代码也不是0' % (
            bad['val'] or 0, bad['tag'], bad['ann'])
    c_bad = col_at(bad['val']) if (bad['tag'] == 'D' and bad['val']) else None
    if c_bad and k >= 3:
        return 'REAL_VTABLE', ('前 %d 槽连续代码, slot%d=&COL(%s): 紧跟下一个虚表的 COL 头'
                               ' => 本虚表共 %d 槽' % (run, k, c_bad['name_disp'], run))
    if c_bad:
        return 'UNCERTAIN', ('仅 %d 个代码槽, slot%d=&COL(%s): 短代码段后内嵌 COL 指针,'
                             ' 疑似 pos 扫描假阳性(或 %d 槽小虚表)' % (run, k, c_bad['name_disp'], run))
    return 'UNCERTAIN', '前 %d 槽连续代码, slot%d=0x%08X 为 %s(%s); xr_text=%d' % (
        run, k, bad['val'] or 0, bad['tag'], bad['ann'], rec.get('xr_text', 0))


print('[2] slots/xrefs/verdicts for %d candidates ...' % len(cand))
for rec in cand.values():
    vt = rec['vt']
    rec['xr_text'] = count_refs(vt, ('.text',))
    rec['xr_rdata'] = count_refs(vt, ('.rdata',))
    rec['xr_data'] = count_refs(vt, ('.data',))
    rec['slots'] = slots_of(vt)
    rec['verdict'], rec['reason'] = verdict_of(rec, rec['slots'])

# ================= 2. 统计 =================
names = set(r['name_raw'] for r in cand.values())
sec_dist = Counter(r['sec'] for r in cand.values())
off_hist = Counter(r['offset'] for r in cand.values())
sig_hist = Counter(r['sig'] for r in cand.values())
tstruct = Counter(r['td_struct_ok'] for r in cand.values())
next_hist = Counter(r['next'].split(':')[0] for r in cand.values())
prev_hist = Counter(r['prev'].split(':')[0] for r in cand.values())
verdict_hist = Counter(r['verdict'] for r in cand.values())
adj4 = sum(1 for r in cand.values() if (r['vt'] + 4) in VT_SET)
adj8 = sum(1 for r in cand.values() if (r['vt'] + 8) in VT_SET)
zero_slot_cands = sum(1 for r in cand.values() if any(sl['tag'] == '0' for sl in r['slots']))
multiref = {a: ps for a, ps in col_refs.items() if len(ps) > 1}

slot_freq = Counter()
for r in cand.values():
    for sl in r['slots']:
        if sl['tag'] in ('C', 'P') and sl['val']:
            slot_freq[sl['val']] += 1
top_slots = slot_freq.most_common(8)

# 独立 TD 清单 (交叉核对)
td_names = set()
td_prefix = Counter()
td_cnt = 0
for _nm in ('.rdata', '.data'):
    _s = SEC[_nm]
    _lo, _hi = _s['rawptr'], _s['rawptr'] + _s['rawsize']
    _i = RAW.find(b'.?A', _lo, _hi)
    while _i != -1:
        if _i - 8 >= _lo:
            _va = _s['va'] + (_i - 8 - _s['rawptr'])
            nmb = cstr(_va + 8)
            if nmb and nmb.startswith(b'.?A'):
                d0, d1 = rd32(_va), rd32(_va + 4)
                s0 = sect_of_va(d0) if d0 else None
                if s0 and s0['name'] in ('.rdata', '.data') and d1 == 0:
                    td_cnt += 1
                    td_prefix[nmb[:4].decode('ascii', 'replace')] += 1
                    td_names.add(nmb.decode('ascii', 'replace'))
        _i = RAW.find(b'.?A', _i + 1, _hi)

td_only = sorted(td_names - names)
cand_only = sorted(names - td_names)

# 采样 40
random.seed(SEED)
vts_sorted = sorted(VT_SET)
sample = random.sample(vts_sorted, min(SAMPLE_N, len(vts_sorted)))
sample_hist = Counter(cand[v]['verdict'] for v in sample)

# 列表 A: 槽0代码但槽1/2非代码非0
listA = sorted([r for r in cand.values()
                if r['slots'][0]['tag'] in ('C', 'P') and
                (r['slots'][1]['tag'] not in ('C', 'P', '0') or
                 r['slots'][2]['tag'] not in ('C', 'P', '0'))],
               key=lambda r: r['vt'])

# COL 对象区间 (用于判断 pos 是否落在某 COL 对象内部)
_colobjs = sorted(a for a, c in COL_CACHE.items() if c)


def pos_inside_col(p):
    i = bisect.bisect_right(_colobjs, p) - 1
    if i >= 0 and p < _colobjs[i] + 0x14:
        return _colobjs[i]
    return None


odd_pos = [(r['vt'], pos_inside_col(r['pos'])) for r in cand.values()
           if pos_inside_col(r['pos']) is not None]


def find_refs_to(targets):
    hits = defaultdict(list)
    tset = set(targets)
    for nm in ('.rdata', '.data'):
        s = SEC[nm]
        for o in range(0, s['rawsize'] - 3, 4):
            v = struct.unpack_from('<I', RAW, s['rawptr'] + o)[0]
            if v in tset:
                hits[v].append(s['va'] + o)
    return hits


def pattern_run(p0, limit=96):
    """围绕 p0 探测 stride-8 的 {COL指针, 代码} 成对结构, 返回 (lo, hi, [(pos, col), ...])。"""
    def is_pair(p):
        c = col_at(rd32(p))
        t, _ = classify(rd32(p + 4))
        return (c is not None and t in ('C', 'P')), c
    lo = p0
    n = 0
    while n < limit:
        ok, _ = is_pair(lo - 8)
        if not ok:
            break
        lo -= 8
        n += 1
    hi = p0
    cols = []
    n = 0
    while n < limit:
        ok, c = is_pair(hi)
        if not ok:
            break
        cols.append((hi, c))
        hi += 8
        n += 1
    return lo, hi, cols


def dump_region(R, lo, hi):
    R.append('| 地址 | 值 | 类别 | 注 | 标记 |')
    R.append('|---|---|---|---|---|')
    for va in range(lo, hi, 4):
        v = rd32(va)
        t, a = classify(v)
        marks = []
        if va in VT_SET:
            marks.append('==候选vt')
        if (va + 4) in VT_SET:
            marks.append('==候选vt的[vt-4]')
        c = COL_CACHE.get(va)
        if c:
            marks.append('==COL对象(sig=%d,off=%d)' % (c['sig'], c['offset']))
        R.append('| %08X | %s | %s | %s | %s |' % (
            va, ('%08X' % v) if v is not None else '(无文件字节)',
            t, a, ' '.join(marks)))


def identify_struct_full(va):
    L = ['--- 结构识别 @ %08X ---' % va]
    for i in range(10):
        d = rd32(va + 4 * i)
        L.append('  +%02X: %s' % (4 * i, ('%08X' % d) if d is not None else '(无文件字节)'))
    c = col_at(va)
    if c:
        L.append('  => 完整对象定位器 COL: sig=%d offset=%d cdOffset=%d pTD=%08X(%s) '
                 'pCHD=%08X(%s) 类名=%s td_struct_ok=%s' % (
                     c['sig'], c['offset'], c['cd_offset'], c['td'], c['td_mode'],
                     c['chd'], c['chd_mode'], c['name_raw'], c['td_struct_ok']))
        chd = c['chd']
        if chd:
            d0 = rd32(chd)
            attr = rd32(chd + 4)
            num = rd32(chd + 8)
            bca = rd32(chd + 0xC)
            L.append('     CHD@%08X: sig=%s attr=%s num=%s pBCA=%s' % (
                chd, d0, attr, num, ('%08X' % bca) if bca is not None else '?'))
            if bca and num:
                for j in range(min(num, 8)):
                    e = rd32(bca + 4 * j)
                    ev, _m = resolve_field(e)
                    nmc = cstr(ev + 8) if ev else None
                    L.append('       BCA[%d] = %s -> %s' % (
                        j, ('%08X' % e) if e is not None else '?',
                        disp_name(nmc) if nmc else '(不可解析为TD)'))
        return '\n'.join(L)
    nm = td_name_at(va)
    if nm:
        L.append('  => TypeDescriptor: name=%s spare(+=4)=%s' % (
            nm.decode('ascii', 'replace'), rd32(va + 4)))
        return '\n'.join(L)
    d0 = rd32(va)
    ev, _m = resolve_field(d0)
    if ev:
        nmc = cstr(ev + 8)
        if nmc and nmc.startswith(b'.?A'):
            pm = [rd32(va + 0xC + 4 * k) for k in range(3)]
            if all(x is not None and x < 0x400000 for x in pm):
                L.append('  => BaseClassDescriptor: td->%s attrs=%08X numContained=%s '
                         'pmd(mdisp,pdisp,vdisp)=%s' % (disp_name(nmc), rd32(va + 4),
                                                        rd32(va + 8), pm))
                return '\n'.join(L)
    if d0 == 0:
        num = rd32(va + 8)
        bca = rd32(va + 0xC)
        sb = sect_of_va(bca) if bca else None
        if sb and sb['name'] in ('.rdata', '.data') and num is not None and num < 0x400:
            L.append('  => ClassHierarchyDescriptor?: num=%d pBCA=%08X' % (num, bca))
            return '\n'.join(L)
    L.append('  => 无标准 RTTI 结构解释')
    return '\n'.join(L)


# ================= 报告 =================
R = []
R.append('# W130 独立虚表抽查报告 (gamemd.exe)')
R.append('')
R.append('## 0. 环境与段核对')
R.append('- SHA-256: %s (期望 %s) => %s' % (
    SHA, EXPECT_SHA, 'MATCH' if SHA == EXPECT_SHA else 'MISMATCH'))
if SHA != EXPECT_SHA:
    NOTES.append('SHA-256 与任务给定值不一致!')
R.append('- IAT 导入函数数=%d; msvcrt _purecall IAT 槽=%s; .text 中 FF25 thunk 数=%d' % (
    len(IAT), ['%08X' % x for x in PURECALL_IAT] or '无', len(PURECALL)))
if not PURECALL_IAT:
    NOTES.append('导入表无 _purecall: 纯虚槽识别退化为 "同址高频" 启发式 (P 标签可能缺失)。')
for nm, (lo, hi) in STATED.items():
    s = SEC[nm]
    R.append('- %-6s 任务给定 %08X..%08X | 实际 VA %08X..%08X (VirtualSize=%06X) '
             'SizeOfRawData=%06X => 文件字节覆盖 %08X..%08X' % (
                 nm, lo, hi, s['va'], s['va'] + s['vsize'], s['vsize'], s['rawsize'],
                 s['va'], s['va'] + s['rawsize'] - 1))
    if s['va'] != lo or s['va'] + s['vsize'] != hi:
        NOTES.append('%s 段范围与任务给定不一致: 给定 %08X..%08X, 实际 %08X..%08X' % (
            nm, lo, hi, s['va'], s['va'] + s['vsize']))
R.append('- .data SizeOfRawData = %08X (任务称 0x6C000) => %s' % (
    SEC['.data']['rawsize'],
    '一致' if SEC['.data']['rawsize'] == 0x6C000 else '不一致!'))
if SEC['.data']['rawsize'] != 0x6C000:
    NOTES.append('.data SizeOfRawData 与任务给定 0x6C000 不一致: 实际 %X' % SEC['.data']['rawsize'])
R.append('- 读取层: 段表 + 原始文件字节, VA>=ImageBase; 任何超出 SizeOfRawData 的地址一律视为无字节 (BSS 保护)。')
R.append('- 校验: 0x400000 处前2字节 = %s (应为 MZ)' % repr(RAW[0:2]))
R.append('')

R.append('## 1. 独立 TD 清单 (交叉核对)')
R.append('- 独立发现的结构完整 TypeDescriptor: %d 个; 类名(去重) %d 个' % (td_cnt, len(td_names)))
R.append('- 前缀分布: %s' % dict(td_prefix))
other_prefix = {k: v for k, v in td_prefix.items() if k not in ('.?AV', '.?AU')}
if other_prefix:
    NOTES.append('TD 清单中存在非 .?AV/.?AU 前缀: %s (任务口径只收 AV/AU, 这些未进候选)' % other_prefix)
R.append('- 仅出现在 TD 清单、无候选虚表的类: %d 个%s' % (
    len(td_only), ('; 例: ' + ', '.join(td_only[:10])) if td_only else ''))
if td_only:
    NOTES.append('%d 个类有 TD 但按本口径无候选虚表 (可能: 无虚表/虚表不在扫描段/COL 未被 .rdata/.data 引用)' % len(td_only))
R.append('- 候选中有而 TD 清单没有的类名: %d 个%s' % (
    len(cand_only), ('; 例: ' + ', '.join(cand_only[:10])) if cand_only else ''))
R.append('')

R.append('## 2. 候选虚表扫描 (任务口径)')
R.append('- 候选虚表总数: **%d**' % len(cand))
R.append('- 涉及类名总数(原始修饰名去重): **%d**' % len(names))
R.append('- 按段分布: %s' % {k: v for k, v in sec_dist.items()})
R.append('- COL 内 pTypeDescriptor 解释方式: %s (VA=绝对指针, RVA=镜像相对)' % dict(td_mode_hist))
R.append('- COL signature 分布: %s' % dict(sig_hist))
R.append('- COL offset 字段分布(前8): %s; offset!=0 的候选数=%d' % (
    off_hist.most_common(8), sum(v for k, v in off_hist.items() if k != 0)))
R.append('- TD 结构佐证 (td_struct_ok, [+4]==0): True=%d False=%d' % (
    tstruct.get(True, 0), tstruct.get(False, 0)))
if tstruct.get(False, 0):
    NOTES.append('%d 个候选的 TD spare 字段非 0 — 若占比高需重审 TD 布局假设' % tstruct.get(False, 0))
R.append('- 候选 [pos-4] 前值类别: %s' % dict(prev_hist))
R.append('- 候选 [pos+4] 后值类别: %s' % dict(next_hist))
R.append('- 相邻候选: pos+4 也是候选的 %d 个; pos+8 也是候选的 %d 个 (stride-8 成对特征计数)' % (adj4, adj8))
R.append('- 前12槽含 0 的候选数: %d' % zero_slot_cands)
R.append('- 被 >1 个位置引用的 COL 数: %d' % len(multiref))
R.append('- 候选 pos 落在某已验证 COL 对象内部的: %d 个%s' % (
    len(odd_pos), ('; 例: ' + ', '.join('%08X(in COL@%08X)' % t for t in odd_pos[:8])) if odd_pos else ''))
if odd_pos:
    NOTES.append('%d 个候选的 pos 位于某个 COL 对象内部 — 该类候选几乎必为假阳性' % len(odd_pos))
R.append('- 全体候选判定分布: %s' % dict(verdict_hist))
R.append('- 最高频代码槽值(潜在 _purecall/公共桩): ')
for v, n in top_slots:
    R.append('  - %08X x%d  [%s]  %s' % (v, n, classify(v)[0], disasm(v, 3)))
R.append('')
R.append('槽值图例: C=.text代码 | P=_purecall跳转(仍在.text) | 0=零 | D=数据指针(.rdata/.data) | '
         'X=未映射 | B=无文件字节(BSS) | ?=不可读')
R.append('')

R.append('## 3. 抽样 40 详查 (random.seed(%d))' % SEED)
R.append('- 抽样判定分布: REAL=%d NOT=%d UNCERTAIN=%d' % (
    sample_hist.get('REAL_VTABLE', 0), sample_hist.get('NOT_VTABLE', 0),
    sample_hist.get('UNCERTAIN', 0)))
R.append('')


def fmt_slot(sl):
    v = sl['val']
    vs = ('%08X' % v) if v is not None else '(无字节)'
    return '[%2d] %s  %-2s %s' % (sl['i'], vs, sl['tag'], sl['ann'])


def cand_block(rec, idx=None):
    L = []
    head = ('### [%s] ' % idx) if idx is not None else '### '
    L.append(head + 'vt=%08X  类=%s (%s)  段=%s' % (
        rec['vt'], rec['name_disp'], rec['name_raw'], rec['sec']))
    L.append('- [vt-4]=%08X -> COL=%08X: sig=%d offset=%d cdOffset=%d td=%s(%s) '
             'chd=%s(%s) td_struct_ok=%s' % (
                 rec['pos'], rec['col'], rec['sig'], rec['offset'], rec['cd_offset'],
                 ('%08X' % rec['td']) if rec['td'] is not None else 'None', rec['td_mode'],
                 ('%08X' % rec['chd']) if rec['chd'] is not None else 'None',
                 rec['chd_mode'], rec['td_struct_ok']))
    L.append('- xr: text=%d rdata=%d data=%d | [pos-4]=%s | [pos+4]=0x%08X %s' % (
        rec['xr_text'], rec['xr_rdata'], rec['xr_data'], rec['prev'],
        rec['next_val'] or 0, rec['next']))
    L.append('- 槽 0..11:')
    for sl in rec['slots']:
        line = '  ' + fmt_slot(sl)
        if sl['tag'] in ('C', 'P') and sl['val']:
            line += '   ; ' + disasm(sl['val'], 2)
        L.append(line)
    L.append('- 连续代码游程 run=%d' % rec['run'])
    L.append('- **判定: %s** — %s' % (rec['verdict'], rec['reason']))
    return L


for k, v in enumerate(sample, 1):
    R.extend(cand_block(cand[v], k))
    R.append('')

R.append('## 4. 列表A: 槽0为代码但槽1/2既非代码也非0 (疑似假阳性)')
R.append('- 总数: **%d**' % len(listA))
if listA:
    R.append('- 全部地址: %s' % ', '.join('%08X(%s)' % (r['vt'], r['name_disp'])
                                          for r in listA[:40]))
for k, rec in enumerate(listA[:10], 1):
    R.extend(cand_block(rec, 'A%d' % k))
    R.append('')

v20, v28 = rd32(0x7E1F20), rd32(0x7E1F28)
v24, v2C, v30 = rd32(0x7E1F24), rd32(0x7E1F2C), rd32(0x7E1F30)
c20, c28 = col_at(v20), col_at(v28)


def _hx(x):
    return ('%08X' % x) if x is not None else '(无文件字节)'


R.append('## 5. 疑点深查: 0x007E1F24 / 0x007E1F2C (任务称均为 .?AVAbstractClass@@)')
R.append('- 线索核对: dword[0x7E1F28] = %s (任务线索称 0x007FAFF0) ; dword[0x7E1F30] = %s (任务线索称 0x007FB008)'
         % (_hx(v28), _hx(v30)))
R.append('- dword[0x7E1F20] = %s -> %s' % (
    _hx(v20), ('COL: %s off=%d sig=%d td=%08X' % (c20['name_raw'], c20['offset'], c20['sig'], c20['td']))
    if c20 else '按任务口径不构成 COL'))
R.append('- dword[0x7E1F28] = %s -> %s' % (
    _hx(v28), ('COL: %s off=%d sig=%d td=%08X' % (c28['name_raw'], c28['offset'], c28['sig'], c28['td']))
    if c28 else '按任务口径不构成 COL'))
R.append('- 本独立扫描候选集: 0x007E1F24 %s ; 0x007E1F2C %s' % (
    '在' if 0x7E1F24 in VT_SET else '不在', '在' if 0x7E1F2C in VT_SET else '不在'))
try:
    for avt in ANOM:
        R.append('')
        R.append('### %08X 槽序列' % avt)
        if avt in cand:
            rec = cand[avt]
            R.append('- 候选记录: 类=%s (%s) pos=%08X col=%08X offset=%d sig=%d | xr: text=%d rdata=%d data=%d' % (
                rec['name_disp'], rec['name_raw'], rec['pos'], rec['col'], rec['offset'], rec['sig'],
                rec['xr_text'], rec['xr_rdata'], rec['xr_data']))
            R.append('- 判定: %s — %s' % (rec['verdict'], rec['reason']))
            slots = rec['slots']
        else:
            slots = slots_of(avt)
        for sl in slots:
            line = '  ' + fmt_slot(sl)
            if sl['tag'] in ('C', 'P') and sl['val']:
                line += '   ; ' + disasm(sl['val'], 3)
            R.append(line)
        s0 = slots[0]
        if s0['tag'] in ('C', 'P') and s0['val']:
            R.append('- slot0=%08X 反汇编: %s' % (s0['val'], disasm(s0['val'], 5)))
    R.append('')

    R.append('### 区域转储 .rdata 0x7E1EC0 .. 0x7E1FC0')
    dump_region(R, 0x7E1EC0, 0x7E1FC0)
    R.append('')
    R.append('### 区域转储 .rdata 0x7FAFC0 .. 0x7FB040 (线索中的两个数据指针)')
    dump_region(R, 0x7FAFC0, 0x7FB040)
    R.append('')

    R.append('### 结构识别')
    for sa in (0x7FAFF0, 0x7FB008, 0x7FB004):
        R.append(identify_struct_full(sa))
        R.append('')
    if c20 and v20 != 0x7FAFF0:
        R.append('### dword[0x7E1F20] 指向对象识别')
        R.append(identify_struct_full(v20))
        R.append('')

    R.append('### stride-8 成对结构探测 (锚 0x7E1F20)')
    plo, phi, pcols = pattern_run(0x7E1F20)
    R.append('- 成对区间 %08X .. %08X, 共 %d 对 {COL指针, 代码}' % (plo, phi, len(pcols)))
    for p, c in pcols:
        _nv = rd32(p + 4)
        _nt, _na = classify(_nv)
        R.append('  - [%08X]=&COL(%s, off=%d, td=%08X) ; [%08X]=%s (%s %s) %s' % (
            p, c['name_raw'], c['offset'], c['td'], p + 4, _hx(_nv), _nt, _na,
            disasm(_nv, 2) if _nt in ('C', 'P') else ''))
    R.append('')

    R.append('### 引用扫描 (谁引用了这些对象)')
    _cb = c28 or c20
    td_abs = _cb['td'] if _cb else None
    targets = [x for x in (v20, v28, td_abs) if x]
    hits = find_refs_to(targets)
    for tgt in targets:
        ps = hits.get(tgt, [])
        R.append('- %08X 被 .rdata/.data 引用 %d 处:' % (tgt, len(ps)))
        for p in ps[:24]:
            owner = pos_inside_col(p)
            own = ('位于 COL@%08X+0x%02X' % (owner, p - owner)) if owner else ''
            nxt = rd32(p + 4)
            nt, na = classify(nxt)
            R.append('  - pos=%08X %s | 后值=%s (%s %s)' % (p, own, _hx(nxt), nt, na))
except Exception:
    R.append('深查异常:\n' + traceback.format_exc())
R.append('')

if adj8 > 50:
    NOTES.append('stride-8 相邻候选 %d 个 — 存在系统性的 {COL指针, 代码} 成对布局 (证据见第 5 节)' % adj8)
NOTES.append('疑点 0x7E1F24/0x7E1F2C: dword[7E1F20]=%s->%s ; dword[7E1F28]=%s->%s ; 详见第 5 节' % (
    _hx(v20), 'COL(' + c20['name_raw'] + ')' if c20 else '非COL',
    _hx(v28), 'COL(' + c28['name_raw'] + ')' if c28 else '非COL'))

R.append('## 6. 与任务"背景"描述的一致性核对')
va_n, rva_n = td_mode_hist.get('VA', 0), td_mode_hist.get('RVA', 0)
R.append('- [背景] "[vt-4] 存指向 COL 的指针": 成立 — 全部候选均由该关系产生, 扫描按绝对 VA 读 [vt-4]。')
R.append('- [背景] COL 布局 +0x00 sig/+0x04 offset/+0x08 cdOffset/+0x0C pTD/+0x10 pCHD: '
         'pTD 字段按绝对 VA 解释命中 %d 个候选, 按 RVA+ImageBase 解释命中 %d 个 => 本镜像实际采用: %s' % (
             va_n, rva_n, '绝对 VA' if va_n >= rva_n else 'RVA'))
R.append('- [背景] COL offset=0 表示主虚表: offset 分布(前5) %s, offset!=0 候选 %d 个' % (
    off_hist.most_common(5), sum(v for k, v in off_hist.items() if k != 0)))
R.append('- [背景] TD +0x08 起为内联字符数组: 成立 — 全部候选都是直接在 td+8 读出 ".?A?" 名字 '
         '(若 +8 是指针, 该读法不可能命中)。TD 结构佐证 [+0]=vftable指针/[+4]==0 通过率: %d/%d' % (
             tstruct.get(True, 0), len(cand)))
R.append('- [背景] 纯虚槽允许 0 或 _purecall: 前 12 槽出现 0 的候选 %d 个; IAT _purecall 槽=%s; '
         '识别出 FF25 thunk %d 个; 最高频槽值见第 2 节' % (
             zero_slot_cands, ['%08X' % x for x in PURECALL_IAT] or '无', len(PURECALL)))
R.append('- [背景] 真虚表槽 0..k 连续指向 .text: slot0 即非代码非 0 的候选 %d 个 (NOT_VTABLE 口径)' % sum(
    1 for r in cand.values() if r['slots'][0]['tag'] not in ('C', 'P', '0')))
R.append('- [背景] 段范围/.data raw size: 实测见第 0 节。')
R.append('')

R.append('## 7. NOTES (与任务口径/背景不一致或需注意)')
if NOTES:
    for i, n in enumerate(NOTES, 1):
        R.append('%d. %s' % (i, n))
else:
    R.append('(无)')

# ================= 落盘 =================
json_cands = []
for vt in vts_sorted:
    r = cand[vt]
    json_cands.append({
        'vt': '0x%08X' % vt, 'pos': '0x%08X' % r['pos'], 'col': '0x%08X' % r['col'],
        'sig': r['sig'], 'offset': r['offset'], 'cd_offset': r['cd_offset'],
        'td': ('0x%08X' % r['td']) if r['td'] is not None else None,
        'td_mode': r['td_mode'],
        'chd': ('0x%08X' % r['chd']) if r['chd'] is not None else None,
        'name_raw': r['name_raw'], 'name_disp': r['name_disp'],
        'td_struct_ok': r['td_struct_ok'], 'sec': r['sec'],
        'prev': r['prev'],
        'next_val': ('0x%08X' % r['next_val']) if r['next_val'] is not None else None,
        'next': r['next'],
        'run': r['run'], 'verdict': r['verdict'], 'reason': r['reason'],
        'xr_text': r['xr_text'], 'xr_rdata': r['xr_rdata'], 'xr_data': r['xr_data'],
        'slots': [{'i': sl['i'],
                   'val': ('0x%08X' % sl['val']) if sl['val'] is not None else None,
                   'tag': sl['tag'], 'ann': sl['ann']} for sl in r['slots']],
    })
stats = {
    'sha256': SHA, 'candidates': len(cand), 'classes': len(names),
    'sec_dist': dict(sec_dist), 'td_inventory': td_cnt, 'td_names': len(td_names),
    'verdict_hist': dict(verdict_hist), 'sample_hist': dict(sample_hist),
    'sample': ['0x%08X' % v for v in sample],
    'listA_count': len(listA),
    'listA_addrs': ['0x%08X' % r['vt'] for r in listA],
    'adj4': adj4, 'adj8': adj8, 'multiref_cols': len(multiref),
    'td_mode_hist': dict(td_mode_hist),
    'offset_hist': {str(k): v for k, v in off_hist.items()},
    'sig_hist': {str(k): v for k, v in sig_hist.items()},
    'td_struct_ok': dict(tstruct), 'zero_slot_cands': zero_slot_cands,
    'purecall_iat': ['0x%08X' % x for x in PURECALL_IAT], 'purecall_thunks': len(PURECALL),
    'notes': NOTES,
}
with open(os.path.join(HERE, 'vtable_candidates.json'), 'w', encoding='utf-8') as f:
    json.dump({'stats': stats, 'candidates': json_cands}, f, ensure_ascii=False, indent=1)
with open(os.path.join(HERE, 'vtable_audit_report.md'), 'w', encoding='utf-8') as f:
    f.write('\n'.join(R) + '\n')

print('[SUM] sha256=%s...' % SHA[:16])
print('[SUM] candidates=%d classes=%d sec=%s' % (len(cand), len(names), dict(sec_dist)))
print('[SUM] verdict_all=%s' % dict(verdict_hist))
print('[SUM] sample40 REAL=%d NOT=%d UNC=%d' % (
    sample_hist.get('REAL_VTABLE', 0),
    sample_hist.get('NOT_VTABLE', 0),
    sample_hist.get('UNCERTAIN', 0)))
print('[SUM] listA=%d adj4=%d adj8=%d multiref_cols=%d' % (len(listA), adj4, adj8, len(multiref)))
print('[SUM] td_inventory=%d td_names=%d cand_classes=%d td_mode=%s td_struct_ok=%s' % (
    td_cnt, len(td_names), len(names), dict(td_mode_hist), dict(tstruct)))
print('[ANOM] dword[7E1F20]=%s -> %s' % (_hx(v20), 'COL:' + c20['name_raw'] if c20 else 'non-COL'))
print('[ANOM] dword[7E1F28]=%s -> %s' % (_hx(v28), 'COL:' + c28['name_raw'] if c28 else 'non-COL'))
print('[ANOM] 7E1F24 in cand=%s ; 7E1F2C in cand=%s' % (0x7E1F24 in VT_SET, 0x7E1F2C in VT_SET))
for _vt in ANOM:
    if _vt in cand:
        _r = cand[_vt]
        print('[ANOM] %08X verdict=%s run=%d xr_text=%d slots=%s' % (
            _vt, _r['verdict'], _r['run'], _r['xr_text'],
            ','.join(sl['tag'] for sl in _r['slots'])))
    else:
        _sl = slots_of(_vt)
        print('[ANOM] %08X not-in-cand slots=%s' % (_vt, ','.join(sl['tag'] for sl in _sl)))
print('[DONE] report -> %s' % os.path.join(HERE, 'vtable_audit_report.md'))
