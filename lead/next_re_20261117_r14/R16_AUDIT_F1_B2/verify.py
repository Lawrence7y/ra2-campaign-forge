# -*- coding: utf-8 -*-
"""
R16-AUDIT-F1-B2 —— 审计员独立复算脚本（B2：派生集合第 19-36 行）

独立性声明：
  * 不 import 任何执行器脚本（R16_F1_B2/*.py 一律不读、不调），也不 import PROBE_802/probe.py。
  * PE 读取、RTTI 解析、表起点枚举、.text 反汇编（capstone 5.0.7 全扫 + skipdata）、
    装表点解码，全部本文件自写，独立跑一遍。
  * gamemd.exe 只读打开；只写本目录（sys.dont_write_bytecode 防留 .pyc）。

审计项：
  §A 最小改动 / 原文保全（对开卡时盘上 coverage 快照 _pin_coverage.tsv 逐字节）
  §B 8 项字节事实独立复算（6 项卡面 + 2 项附加）
  §C 指定主题：18 行定表唯一性（同槽号持有它的类一致活表张数）
  §D 文本与事实一致 + 披露指针 §12.6
  §E 格式合先例
  §F 反抄袭（entry 归一后两两不同）

跑法：  python verify.py
产物：  bytecheck.tsv / verify_out.json（本目录）
"""
import os
import sys
import re
import json
import bisect
import hashlib
import collections
from collections import Counter

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(R14))

EXE = os.path.join(ROOT, 'ra2youli', 'gamemd.exe')
COV_PIN = os.path.join(HERE, '_pin_coverage.tsv')          # 开卡时盘上快照
AUDIT_TSV = os.path.join(R14, 'R16_PROBE_4GAP', 'scan_F1_audit.tsv')
DELTA = os.path.join(R14, 'R16_F1_B2', 'delta.tsv')
FIELDS = os.path.join(R14, 'R16_F1_B2', 'fields.tsv')
ATLAS = os.path.join(ROOT, 'lead', 'next_re_20261112_r10', 'W130_atlas',
                     'function_atlas.tsv')

EXPECT_EXE_SHA = '73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476'
IMAGE_BASE = 0x400000
TEXT_LO, TEXT_HI = 0x401000, 0x7E038D
WITNESS = '④ 活表槽位见证'


def sha256p(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest().upper()


# ---------------------------------------------------------------- PE 底图（自写）
class Image(object):
    def __init__(self, path):
        import pefile
        self.pe = pefile.PE(path, fast_load=True)
        self.base = self.pe.OPTIONAL_HEADER.ImageBase
        self.secs = []
        for s in self.pe.sections:
            nm = s.Name.rstrip(b'\x00').decode('latin-1')
            va = self.base + s.VirtualAddress
            self.secs.append(dict(name=nm, va=va, vsize=s.Misc_VirtualSize,
                                  rsize=s.SizeOfRawData, data=s.get_data()))
        end = max(s['va'] + max(s['vsize'], s['rsize']) for s in self.secs)
        self.buf = bytearray(end - self.base + 16)
        for s in self.secs:
            off = s['va'] - self.base
            d = s['data']
            self.buf[off:off + len(d)] = d

    def sec_of(self, va):
        for s in self.secs:
            if s['va'] <= va < s['va'] + max(s['vsize'], s['rsize']):
                return s['name']
        return None

    def in_image(self, va):
        return va is not None and self.base <= va < self.base + len(self.buf)

    def u32(self, va):
        off = va - self.base
        if off < 0 or off + 4 > len(self.buf):
            return None
        return int.from_bytes(self.buf[off:off + 4], 'little')

    def cstr(self, va, n=256):
        off = va - self.base
        if off < 0 or off >= len(self.buf):
            return None
        e = self.buf.find(b'\x00', off, min(off + n, len(self.buf)))
        if e < 0:
            return None
        return bytes(self.buf[off:e]).decode('latin-1')

    def secs_named(self, *names):
        want = set(names)
        return [s for s in self.secs if s['name'] in want]


def in_text(va):
    return TEXT_LO <= va < TEXT_HI


# ---------------------------------------------------------------- RTTI（自写）
def col_at(img, table_start):
    """table_start-4 必须是 COL 绝对 VA 且 RTTI 链自洽 ⇒ 认定 table_start 是表起点。

    返回 dict(col, td, mangled) 或 None。
    """
    col = img.u32(table_start - 4)
    if not img.in_image(col) or img.u32(col) is None or img.u32(col) != 0:
        return None                                   # ClassDescriptor.signature 必须 0
    td = img.u32(col + 12)
    if not img.in_image(td):
        return None
    nm = img.cstr(td + 8, 256)                        # TD+8 内联装饰名（不是指针）
    if not nm or not nm.startswith('.?A'):
        return None
    return dict(col=col, td=td, mangled=nm)


# ---------------------------------------------------------------- .text 全扫（自写）
class StoreScan(object):
    """capstone 5.0.7 线性反汇编全 .text（skipdata=True），收 `mov <mem>, imm32`。"""

    def __init__(self, img):
        import capstone
        t = [s for s in img.secs if s['name'] == '.text'][0]
        n = min(len(t['data']), TEXT_HI - t['va'])
        self.lo = t['va']
        self.code = bytes(t['data'][:n])
        self.hi = self.lo + len(self.code)
        self.stores = collections.defaultdict(list)    # imm -> [(site, disp, base_reg)]
        self.n_insn = 0
        self.n_skip = 0
        md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
        md.detail = True
        md.skipdata = True
        X = capstone.x86
        for insn in md.disasm(self.code, self.lo):
            if insn.id == 0:
                self.n_skip += 1
                continue
            self.n_insn += 1
            if insn.mnemonic != 'mov':
                continue
            ops = insn.operands
            if len(ops) != 2:
                continue
            a, b = ops
            if a.type == X.X86_OP_MEM and b.type == X.X86_OP_IMM:
                imm = b.imm & 0xFFFFFFFF
                if IMAGE_BASE <= imm < IMAGE_BASE + 0x800000:
                    self.stores[imm].append((insn.address, a.mem.disp, a.mem.base))

    def sites_of(self, vt):
        return self.stores.get(vt, [])


def decode_site(img, site):
    """独立解码单条指令（不做线性扫，直接对 site 处字节反汇编），返回 (mnemonic, ops_txt)。"""
    import capstone
    off = site - IMAGE_BASE
    raw = bytes(img.buf[off:off + 16])
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = True
    for insn in md.disasm(raw, site):
        return insn.mnemonic, insn.op_str, insn
    return None, None, None


def imm_and_memkind(insn):
    """从已解码指令取 (是否 mov, a 是 MEM, b 是 IMM, imm)。"""
    import capstone
    X = capstone.x86
    if insn is None or len(insn.operands) != 2 or insn.mnemonic != 'mov':
        return False, None
    a, b = insn.operands
    if a.type != X.X86_OP_MEM or b.type != X.X86_OP_IMM:
        return False, None
    return True, (b.imm & 0xFFFFFFFF)


# ---------------------------------------------------------------- atlas 函数体
def load_atlas():
    d = {}
    if not os.path.isfile(ATLAS):
        return d
    with open(ATLAS, encoding='utf-8-sig') as f:
        f.readline()
        for ln in f:
            c = ln.split('\t')
            if len(c) < 2:
                continue
            try:
                d[c[0].strip().upper()] = int(c[1])
            except ValueError:
                pass
    return d


def which_body(ranges, va):
    i = bisect.bisect_right(ranges, (va, 1 << 62)) - 1
    while i >= 0:
        s, e = ranges[i]
        if s <= va < e:
            return s
        if e <= va:
            return None
        i -= 1
    return None


# ---------------------------------------------------------------- 名称解析
def split_name(name):
    """Class::slotN → (class, slot)。"""
    m = re.match(r'^(?P<cls>.+?)::slot(?P<slot>\d+)$', name.strip())
    if not m:
        return None, None
    return m.group('cls'), int(m.group('slot'))


def class_match(name_cls, mangled):
    """行名类 vs RTTI 装饰名（沿用项目既有口径：T_ 伪名按分片全含）。"""
    if not name_cls or not mangled:
        return 'none'
    if name_cls.startswith('T_'):
        parts = [p for p in name_cls[2:].rstrip('_').split('_') if p]
        return 'match' if all(p in mangled for p in parts) else 'nomatch'
    return 'match' if name_cls in mangled else 'nomatch'


def class_match_strict(name_cls, mangled):
    """更严口径：非模板名要求 mangled 恰为 .?AV<Class>@@；模板名要求参数类完全一致。"""
    if not name_cls or not mangled:
        return 'none'
    if name_cls.startswith('T_'):
        inner = name_cls[2:].rstrip('_')
        m = re.match(r'^(?P<tpl>[A-Za-z_0-9]+)_(?P<arg>.+)$', inner)
        if not m:
            return 'nomatch'
        tpl, arg = m.group('tpl'), m.group('arg')
        want = '.?AV?$%s@%s@@@@' % (tpl, arg)
        return 'match' if mangled == want else 'nomatch'
    want = '.?AV%s@@' % name_cls
    return 'match' if mangled == want else 'nomatch'


def probe_repro(img, hit, max_walk=0x1000):
    """按 PROBE_802/probe.py vtable_start 的字面语义复现（首个失败处停），仅用于口径对照。

    本审计的主口径是 enum_tables 的 owner（最近合法表起点），因为「表起点」的定义是
    u32(t-4) 为合法 COL 且 t..hit 之间皆槽位；窗口内更远处的合法 COL 属于**别的表**。
    """
    best = None
    k = 0
    while k * 4 <= max_walk:
        v = hit - k * 4
        if v <= IMAGE_BASE + 4:
            break
        if img.sec_of(v) is None or img.sec_of(v - 4) is None:
            k += 1
            continue
        c = col_at(img, v)
        if c is not None:
            best = (v, c)
        else:
            if best is not None:
                break
        k += 1
    return best


def table_slots(img, vt, limit=600):
    """表内槽位值是否全为 .text 代码指针（含 NULL），并返回槽数。"""
    n = 0
    while n < limit:
        v = img.u32(vt + n * 4)
        if v is None:
            break
        if v == 0:
            n += 1
            continue
        if not in_text(v):
            break
        n += 1
    return n


def all_table_starts(img):
    """枚举 .rdata/.data 内**全部**合法表起点（t-4 为自洽 COL）。与命中扫描完全独立。"""
    out = []
    for s in img.secs_named('.rdata', '.data'):
        d = s['data']
        va = s['va']
        for i in range(0, max(0, len(d) - 4), 4):
            p = va + i
            c = col_at(img, p)
            if c is not None:
                out.append((p, c))
    return out


class RawFile(object):
    """第三口径：不经虚拟缓冲，直接按 PE 段表把 VA 映射到文件偏移读字节。

    专门用来防「Image.buf 构造有 bug」这一风险：若两口径结论一致，则字节事实可信。
    """

    def __init__(self, path):
        import pefile
        self.f = open(path, 'rb')
        pe = pefile.PE(path, fast_load=True)
        self.base = pe.OPTIONAL_HEADER.ImageBase
        self.map = []
        for s in pe.sections:
            va = self.base + s.VirtualAddress
            span = min(s.Misc_VirtualSize or s.SizeOfRawData, s.SizeOfRawData)
            self.map.append((va, span, s.PointerToRawData))
        pe.close()

    def off(self, va):
        for (v, span, praw) in self.map:
            if v <= va < v + span:
                return praw + (va - v)
        return None

    def read(self, va, n):
        o = self.off(va)
        if o is None:
            return None
        self.f.seek(o)
        return self.f.read(n)

    def u32(self, va):
        b = self.read(va, 4)
        return None if b is None or len(b) < 4 else int.from_bytes(b, 'little')

    def cstr(self, va, n=256):
        b = self.read(va, n)
        if b is None:
            return None
        e = b.find(b'\x00')
        return b[:e].decode('latin-1') if e >= 0 else None

    def close(self):
        self.f.close()


# ---------------------------------------------------------------- 表枚举（自写）
def enum_tables(img, entry, max_walk=0x1000):
    """扫 .rdata/.data 里 4 字节对齐的 dd entry，逐命中反推所在表。

    对每个命中 h，收集 [h-max_walk, h] 内所有「t-4 是合法 COL」的 t：
      owner = max(t)  —— 最近的合法表起点（本审计采用为主口径）
      back  = 连续链走得最远者（复现 probe.vtable_start 口径，用于对照）
    返回 (hits, tables)：hits=[h...]，tables=[{vt, slot_owner, slot_back, col, td, mangled, live, sites}]
    """
    pat = entry.to_bytes(4, 'little')
    hits = []
    for s in img.secs_named('.rdata', '.data'):
        d = s['data']
        i = d.find(pat)
        while i >= 0:
            if i % 4 == 0:
                hits.append(s['va'] + i)
            i = d.find(pat, i + 1)
    # 全域（含非 .rdata/.data 段）命中数，用来证明「表只在 .rdata/.data」这一前提
    hits_all = []
    for s in img.secs:
        if s['name'] in ('.rdata', '.data'):
            continue
        d = s['data']
        i = d.find(pat)
        while i >= 0:
            hits_all.append(s['name'] + '@%08X' % (s['va'] + i))
            i = d.find(pat, i + 1)
    tables = []
    for h in hits:
        cands = []
        k = 0
        while k * 4 <= max_walk:
            t = h - k * 4
            if t <= IMAGE_BASE + 4:
                break
            c = col_at(img, t)
            if c is not None:
                cands.append((t, c))
            k += 1
        if not cands:
            tables.append(dict(hit=h, vt=None, slot=None, slot_back=None, vt_back=None,
                               col=None, td=None, mangled=None, live=None, sites=[],
                               ncand=0))
            continue
        owner, oc = cands[0]                      # k 递增 ⇒ cands[0] 是最近的
        pr = probe_repro(img, h)
        back, bc = pr if pr else (owner, oc)
        tables.append(dict(hit=h, vt=owner, slot=(h - owner) // 4,
                           slot_back=(h - back) // 4, vt_back=back,
                           col=oc['col'], td=oc['td'], mangled=oc['mangled'],
                           col_back=bc['col'], mangled_back=bc['mangled'],
                           ncand=len(cands), sites=[], live=None))
    return hits, hits_all, tables


# ---------------------------------------------------------------- 输入装载
def load_cov(path):
    """entry -> {'cols': [bytes]*8, 'line_no': int}"""
    d = {}
    with open(path, 'rb') as f:
        raw = f.read()
    for i, ln in enumerate(raw.split(b'\n')):
        if not ln:
            continue
        c = ln.split(b'\t')
        if len(c) != 8:
            continue
        e = c[0].decode('ascii', 'ignore').strip().upper()
        if not e:
            continue
        d.setdefault(e, dict(cols=c, line_no=i + 1))
    return d


def load_audit():
    with open(AUDIT_TSV, encoding='utf-8') as f:
        lines = f.read().splitlines()
    hdr = lines[0].split('\t')
    idx = {k: i for i, k in enumerate(hdr)}
    return idx, [ln.split('\t') for ln in lines[1:] if ln.strip()]


def load_delta():
    with open(DELTA, 'rb') as f:
        raw = f.read()
    out = []
    for ln in raw.split(b'\n'):
        if not ln:
            continue
        c = ln.split(b'\t')
        out.append(c)
    return out[0], out[1:]


def load_fields():
    with open(FIELDS, encoding='utf-8') as f:
        lines = f.read().splitlines()
    hdr = lines[0].split('\t')
    rows = {}
    for ln in lines[1:]:
        c = ln.split('\t')
        if c and c[0].strip():
            rows[c[0].strip().upper()] = dict(zip(hdr, c))
    return hdr, rows


# ---------------------------------------------------------------- §D 文本解析
RE_WIT = re.compile(
    r'④ 活表槽位见证：'
    r'(?P<cls>[^：（）]+?)::slot(?P<slot>\d+)'
    r'（vt=(?P<vt>[0-9A-Fa-f]{8})，槽 (?P<slot2>\d+) 值=(?P<entry>[0-9A-Fa-f]{8})，'
    r'COL=(?P<col>[0-9A-Fa-f]{8}) offset=(?P<off>\d+)，'
    r'RTTI=(?P<td>[0-9A-Fa-f]{8})→(?P<mangled>\.\?A[^；）]*)；'
    r'装表点 (?P<site>[0-9A-Fa-f]{8}) 位于 (?P<func>[0-9A-Fa-f]{8}) 体内，entry 体外）\s*'
    r'④升级句：(?P<cls2>[^：（）]+?)::slot(?P<slot3>\d+)'
    r'（④ 表属类与行名类一致，均为 (?P<cls3>[^；）]+)；'
    r'该槽即其 vt=(?P<vt2>[0-9A-Fa-f]{8}) 表 slot(?P<slot4>\d+)，无归属歧义）'
)

RE_D47_OK = re.compile(r'D-47\(A\) 裁决：槽位占用即 ④，§12\.3 对该形态让位，'
                       r'见 R14_COMMON §12\.6 与 PANEL 对应披露')


# ---------------------------------------------------------------- 主流程
def main():
    res = dict(errors=[], notes=[])
    print('=' * 100)
    print('R16-AUDIT-F1-B2 · 审计员独立复算（B2 = 派生集合第 19-36 行）')
    print('=' * 100)

    # ---- 环境与指纹
    exe_sha = sha256p(EXE)
    cov_sha = sha256p(COV_PIN)
    print('gamemd.exe sha256 : %s' % exe_sha)
    print('  expect          : %s  %s' % (EXPECT_EXE_SHA,
                                          'OK' if exe_sha == EXPECT_EXE_SHA else '!! MISMATCH'))
    print('coverage 快照 sha : %s  (%d B)' % (cov_sha, os.path.getsize(COV_PIN)))
    res['exe_sha'] = exe_sha
    res['cov_pin_sha'] = cov_sha
    if exe_sha != EXPECT_EXE_SHA:
        res['errors'].append('gamemd.exe sha 不符卡面')

    img = Image(EXE)
    print('ImageBase         : %08X（卡面 0x400000）%s'
          % (img.base, 'OK' if img.base == IMAGE_BASE else '!! MISMATCH'))
    tsec = [s for s in img.secs if s['name'] == '.text'][0]
    print('.text             : [%08X,%08X)  卡面 [0x401000,0x7E038D)'
          % (tsec['va'], tsec['va'] + min(len(tsec['data']), TEXT_HI - tsec['va'])))
    print('PE 段清单         : %s' % ', '.join(
        '%s[%08X,+%X]' % (s['name'], s['va'], s['vsize']) for s in img.secs))

    # ---- 派生集合复现
    aidx, arows = load_audit()
    cov = load_cov(COV_PIN)
    print('\n--- 派生集合复现（卡面 §2 判据）---')
    s0 = arows
    s1 = [r for r in s0 if r[aidx['same_source']] == 'no']
    s2 = [r for r in s1 if int(r[aidx['n_install_decoded']]) >= 1]
    s3 = [r for r in s2 if int(r[aidx['n_install_outside_body']]) >= 1]

    def cov_ok(r):
        e = r[aidx['entry']].upper()
        g = cov.get(e)
        if not g:
            return False
        grade = g['cols'][4].decode('utf-8', 'ignore')
        sem = g['cols'][3].decode('utf-8', 'ignore')
        return grade == '[已证]' and WITNESS not in sem

    s4 = [r for r in s3 if cov_ok(r)]
    print('  S0 all F1 gap rows             : %d' % len(s0))
    print('  S1 same_source==no             : %d' % len(s1))
    print('  S2 +install decoded            : %d' % len(s2))
    print('  S3 +install outside body       : %d' % len(s3))
    print('  S4 +[已证] & no ④ witness       : %d  <== derived set' % len(s4))
    s4s = sorted(s4, key=lambda r: int(r[aidx['entry']], 16))
    ents = [r[aidx['entry']].upper() for r in s4s]
    B2 = ents[18:36]
    print('  derived=%d（卡面 76）  B1=1-18  B2=19-36  → B2 %d 行' % (len(ents), len(B2)))
    print('  B2 = %s' % ' '.join(B2))
    res['derived_n'] = len(ents)
    res['B2'] = B2
    if len(ents) != 76:
        res['errors'].append('派生集合 %d 行 ≠ 卡面 76' % len(ents))

    # ---- delta / fields 装载
    dhdr, drows = load_delta()
    print('\ndelta.tsv         : 表头 %s' % [c.decode("utf-8", "replace") for c in dhdr])
    print('                    数据行 %d（应 18）' % len(drows))
    dent = [c[0].decode('utf-8', 'ignore').strip().upper() for c in drows]
    if dent != B2:
        res['errors'].append('delta entry 序列 ≠ 派生集合第 19-36 行')
        print('  !! delta entry 序列与派生 B2 不一致')
        print('     delta:', ' '.join(dent))
    else:
        print('  OK  delta entry 序列 == 派生集合第 19-36 行（顺序也一致）')
    fhdr, frows = load_fields()
    print('fields.tsv        : %d 列 %s' % (len(fhdr), fhdr))

    # ---- 全 .text 反汇编（唯一的重活）
    print('\n--- 独立跑 capstone 全 .text 反汇编 ---')
    scan = StoreScan(img)
    print('  insn %d / skip %d  (区间 [%08X,%08X))'
          % (scan.n_insn, scan.n_skip, scan.lo, scan.hi))
    atlas = load_atlas()
    ranges = sorted((int(k, 16), int(k, 16) + v) for k, v in atlas.items() if v)
    print('  atlas 函数体 %d 个' % len(ranges))

    # 独立口径 2：枚举镜像内全部表起点（不依赖 dd entry 命中扫描）
    print('\n--- 独立口径 2：枚举 .rdata/.data 内全部表起点 ---')
    tabs = all_table_starts(img)
    print('  合法表起点 %d 个（t-4 均为自洽 COL）' % len(tabs))
    tab_index = []                                   # (vt, col, td, mangled, nslots)
    for (p, c) in tabs:
        tab_index.append((p, c, table_slots(img, p)))
    by_val = collections.defaultdict(list)           # 槽值 -> [(vt, slot)]
    for (p, c, nsl) in tab_index:
        for j in range(nsl):
            v = img.u32(p + j * 4)
            if v is not None and TEXT_LO <= v < TEXT_HI:
                by_val[v].append((p, j))
    print('  建索引：%d 个表、%d 个不同槽值'
          % (len(tab_index), len(by_val)))

    # ---- 逐行
    print('\n' + '=' * 100)
    print('逐行审计（18/18，不抽样）')
    print('=' * 100)
    bc_rows = []
    per = {}
    details = []
    for k, erow in enumerate(s4s[18:36], 19):
        entry_s = erow[aidx['entry']].upper()
        name = erow[aidx['name']]
        ring4_at = erow[aidx['ring4_at']]
        same_source = erow[aidx['same_source']]
        e = int(entry_s, 16)
        name_cls, name_slot = split_name(name)

        drow = next((c for c in drows
                     if c[0].decode('utf-8', 'ignore').strip().upper() == entry_s), None)
        frow = frows.get(entry_s, {})
        txt = drow[3].decode('utf-8', 'replace') if drow else ''

        # --- 自建表枚举
        hits, hits_all, tables = enum_tables(img, e)
        for t in tables:
            if t['vt'] is not None:
                t['sites'] = [s for (s, _d, _b) in scan.sites_of(t['vt'])]
                t['live'] = len(t['sites']) > 0
        live_tabs = [t for t in tables if t['vt'] is not None and t['live']]
        # §C：同槽号（= 行名 slot）持有它的表
        same_slot = [t for t in tables if t['vt'] is not None and t['slot'] == name_slot]
        same_slot_live = [t for t in same_slot if t['live']]
        same_slot_live_cls = [t for t in same_slot_live
                              if class_match(name_cls, t['mangled']) == 'match']
        # 补充：任意槽号上类一致的表
        any_slot_cls = set(t['vt'] for t in live_tabs
                           if class_match(name_cls, t['mangled']) == 'match')

        # 独立口径 2：全表起点枚举，看哪些表在「该槽号」持有 entry
        holdings = by_val.get(e, [])
        hold_same_slot = [h for h in holdings if h[1] == name_slot]
        info = {}
        hold_rows = []
        for (p, j) in hold_same_slot:
            rec = next((r for r in tab_index if r[0] == p), None)
            c = rec[1] if rec else col_at(img, p)
            sites = [s for (s, _d, _b) in scan.sites_of(p)]
            hold_rows.append(dict(vt=p, slot=j, mangled=c['mangled'],
                                  live=bool(sites), nsites=len(sites),
                                  cls_match=class_match(name_cls, c['mangled']),
                                  cls_match_strict=class_match_strict(name_cls,
                                                                      c['mangled'])))
        hold_live = [h for h in hold_rows if h['live']]
        hold_live_cls = [h for h in hold_live if h['cls_match'] == 'match']
        info['all_slots'] = [('%08X' % p, j) for (p, j) in holdings]
        info['same_slot'] = [('%08X' % h['vt'], h['slot']) for h in hold_rows]
        info['same_slot_live'] = [('%08X' % h['vt'], h['slot']) for h in hold_live]
        info['same_slot_live_cls'] = [('%08X' % h['vt'], h['slot']) for h in hold_live_cls]

        # --- §A 逐字节
        pin = cov.get(entry_s)
        A = {}
        if pin is None:
            A = dict(missing=True)
        else:
            pcols = pin['cols']
            A['cols8'] = (len(drow) == 8)
            same = [drow[i] == pcols[i] for i in range(8)]
            A['byte_same'] = same
            A['other7'] = all(same[i] for i in (0, 1, 2, 4, 5, 6, 7))
            A['col4_prefix'] = drow[3].startswith(pcols[3])
            A['grade_ok'] = drow[4].decode('utf-8', 'ignore') == '[已证]'
            A['appended_len'] = len(drow[3]) - len(pcols[3])
            A['pin_line'] = pin['line_no']

        # --- §D 文本
        D = {}
        m = RE_WIT.search(txt)
        D['parse'] = bool(m)
        if m:
            g = m.groupdict()
            D['slot_ok'] = (int(g['slot']) == int(g['slot2']) == int(g['slot3']) == int(g['slot4']))
            D['entry_ok'] = (g['entry'].upper() == entry_s)
            D['site'] = g['site'].upper()
            D['func'] = g['func'].upper()
            D['vt'] = g['vt'].upper()
            D['col'] = g['col'].upper()
            D['td'] = g['td'].upper()
            D['mangled'] = g['mangled']
            D['cls'] = g['cls']
            D['cls2'] = g['cls2']
            D['cls3'] = g['cls3']
            D['slot'] = g['slot']
            D['off'] = int(g['off'])
        D['d47_ok'] = bool(RE_D47_OK.search(txt))
        D['no_124'] = '§12.4' not in txt

        # --- 独立实测：表起点 / RTTI / 装表点
        chosen = None
        if m:
            vt_claim = int(D['vt'], 16)
            chosen = next((t for t in tables if t['vt'] == vt_claim), None)
        if chosen is None and same_slot_live_cls:
            chosen = same_slot_live_cls[0]

        # --- §D 交叉核对（文本 vs 独立实测）—— 放在 §B 之后执行，见下

        # --- §B 8 项 + 附加
        B = {}
        vt = int(D['vt'], 16) if D.get('vt') else (chosen['vt'] if chosen else None)
        B['vt_measured'] = vt
        B['vt_claim_eq_measured'] = (vt == chosen['vt']) if (chosen and D.get('vt')) else None
        if vt is not None:
            B['1_slot_val'] = (img.u32(vt + name_slot * 4) == e) if name_slot is not None else False
            B['2_col'] = (D.get('col') is not None and
                          img.u32(vt - 4) == int(D['col'], 16))
            col_va = img.u32(vt - 4)
            B['col_measured'] = col_va
            B['3_off'] = (col_va is not None and img.u32(col_va + 4) == D.get('off'))
            B['4_td'] = (col_va is not None and D.get('td') is not None and
                         img.u32(col_va + 12) == int(D['td'], 16))
            td_va = img.u32(col_va + 12) if col_va is not None else None
            B['td_measured'] = td_va
            nm = img.cstr(td_va + 8, 256) if td_va else None
            B['5_mangled'] = (nm is not None and D.get('mangled') is not None and
                              nm == D['mangled'])
            B['mangled_measured'] = nm
            B['8_class'] = class_match(name_cls, nm)
            B['8_class_strict'] = class_match_strict(name_cls, nm)
        else:
            for kk in ('1_slot_val', '2_col', '3_off', '4_td', '5_mangled'):
                B[kk] = False
            B['8_class'] = 'none'
            B['8_class_strict'] = 'none'

        # 6) 装表点独立解码
        site = int(D['site'], 16) if D.get('site') else None
        if site is not None:
            mn, ops, insn = decode_site(img, site)
            ok_mov, imm = imm_and_memkind(insn)
            B['6_install'] = bool(ok_mov and imm == vt)
            B['6_asm'] = '%s %s' % (mn, ops) if mn else None
            B['6_imm'] = None if imm is None else '%08X' % imm
            B['6_site'] = '%08X' % site
            in_scan = any(s == site for (s, _d, _b) in (scan.sites_of(vt) if vt else []))
            B['6_in_linear_scan'] = in_scan
            # 7) 装表点所在函数 ≠ entry
            func = which_body(ranges, site)
            B['7_func'] = '%08X' % func if func else None
            B['7_func_ok'] = (func is not None and func != e)
            size = atlas.get(entry_s)
            B['7_entry_size'] = size
            B['7_site_in_entry_body'] = bool(size and e <= site < e + size)
            B['7_self_install_same_vt'] = None
        else:
            B['6_install'] = False
            B['7_func_ok'] = False

        # 附加：本 entry 体内是否也装了同一张表（self-install，证据强度相关，非卡面必判项）
        size = atlas.get(entry_s)
        body = (e, e + size) if size else (e, e)
        allsites = [s for (s, _d, _b) in (scan.sites_of(vt) if vt else [])]
        selfsites = [s for s in allsites if body[0] <= s < body[1]]
        outsites = [s for s in allsites if not (body[0] <= s < body[1])]
        B['self_install_sites'] = ['%08X' % s for s in selfsites]
        B['all_install_sites'] = ['%08X' % s for s in allsites]
        B['n_outside_sites'] = len(outsites)
        B['has_outside_site'] = len(outsites) >= 1

        # ring4_at 一致性
        ring_tok = [t for t in re.findall(r'[0-9A-Fa-f]{8}', ring4_at)]
        B['ring4_has_site'] = ('%08X' % site in [t.upper() for t in ring_tok]) if site else False
        B['ring4_has_func'] = ('%08X' % func in [t.upper() for t in ring_tok]) if site and func else None

        # 全部 8 项
        eight = [B.get('1_slot_val'), B.get('2_col'), B.get('3_off'), B.get('4_td'),
                 B.get('5_mangled'), B.get('6_install'), B.get('7_func_ok'),
                 B.get('8_class') == 'match']
        B['all8'] = all(bool(x) for x in eight)

        per[entry_s] = dict(
            entry=entry_s, name=name, name_cls=name_cls, name_slot=name_slot,
            same_source=same_source, ring4_at=ring4_at,
            A=A, B=B, D=D,
            hits=['%08X' % h for h in hits], hits_outside_rd=' '.join(hits_all),
            tables=[dict(vt=('%08X' % t['vt']) if t['vt'] else None,
                         hit='%08X' % t['hit'], slot=t['slot'],
                         slot_back=t['slot_back'],
                         vt_back=('%08X' % t['vt_back']) if t.get('vt_back') else None,
                         mangled=t['mangled'], live=t['live'],
                         nsites=len(t['sites']),
                         cls_match=class_match(name_cls, t['mangled']),
                         cls_match_strict=class_match_strict(name_cls, t['mangled']))
                    for t in tables],
            c_n_same_slot=len(same_slot),
            c_n_same_slot_live=len(same_slot_live),
            c_n_same_slot_live_cls=len(same_slot_live_cls),
            c2=info,
            c2_agree=(len(hold_live_cls) == len(same_slot_live_cls) == 1 and
                      len(hold_same_slot) == len(same_slot) == 1),
            c_any_slot_cls_tables=sorted('%08X' % v for v in any_slot_cls),
            c_dup_class_tables=sorted('%08X' % v for v in any_slot_cls),
        )

        # --- §D 交叉核对（文本 vs 独立实测）
        if D.get('parse'):
            D['slot_eq_name'] = (int(D['slot']) == name_slot)
            D['cls_eq_name'] = (D['cls'] == name_cls)
            D['cls2_eq_name'] = (D['cls2'] == name_cls)
            D['cls3_eq_name'] = (D['cls3'] == name_cls)
            D['func_eq_measured'] = (D['func'] == B.get('7_func'))
            D['td_eq_measured'] = (B.get('td_measured') is not None and
                                   int(D['td'], 16) == int(B['td_measured']))
            D['col_eq_measured'] = (B.get('col_measured') is not None and
                                    int(D['col'], 16) == int(B['col_measured']))
            D['vt_eq_enum'] = any(('%08X' % p) == D['vt'] for (p, _j) in holdings)
            D['off_eq_measured'] = (B.get('col_measured') is not None and
                                    img.u32(int(B['col_measured']) + 4) == D['off'])
            D['all_ok'] = all(D.get(kk) for kk in
                              ('slot_ok', 'entry_ok', 'd47_ok', 'no_124',
                               'slot_eq_name', 'cls_eq_name', 'cls2_eq_name',
                               'cls3_eq_name', 'func_eq_measured',
                               'td_eq_measured', 'col_eq_measured',
                               'vt_eq_enum', 'off_eq_measured'))
        else:
            D['all_ok'] = False

        # 控制台逐行
        print('\n#%d %s  %s  (same_source=%s)' % (k, entry_s, name, same_source))
        print('   §C hits=%d  同槽(%s)表=%d  其中活=%d  其中类一致=%d  → 定表唯一性 %s'
              % (len(hits), name_slot, len(same_slot), len(same_slot_live),
                 len(same_slot_live_cls),
                 '成立' if len(same_slot_live_cls) == 1 else
                 ('歧义(%d)' % len(same_slot_live_cls))))
        print('      §C 口径2（全表起点枚举）: 该 entry 在镜像内共出现在 %d 个表位 %s；'
              '同槽(%s) %s；其中活 %s；类一致 %s  → 与口径1 %s'
              % (len(holdings), info['all_slots'], name_slot, info['same_slot'],
                 info['same_slot_live'], info['same_slot_live_cls'],
                 '一致' if info and (len(hold_live_cls) == len(same_slot_live_cls))
                 else '不一致'))
        if hits_all:
            print('      !! 非 .rdata/.data 段也有该地址命中: %s' % hits_all)
        for t in tables:
            nsl = table_slots(img, t['vt']) if t['vt'] else 0
            print('      table vt=%s slot=%s%s live=%s sites=%d slots=%d cls=%s%s'
                  % (('%08X' % t['vt']) if t['vt'] else '----',
                     t['slot'], '' if t['slot'] == t['slot_back'] else
                     '[probe-repro vt=%s slot=%s]' % (
                         ('%08X' % t['vt_back']) if t['vt_back'] else '-', t['slot_back']),
                     t['live'], len(t['sites']), nsl,
                     class_match(name_cls, t['mangled']),
                     '' if class_match_strict(name_cls, t['mangled']) == 'match'
                     else ' [strict=%s]' % class_match_strict(name_cls, t['mangled'])))
        print('   §A cols8=%s other7_byte_same=%s col4_prefix=%s grade=%s 追加%dB'
              % (A.get('cols8'), A.get('other7'), A.get('col4_prefix'),
                 A.get('grade_ok'), A.get('appended_len', -1)))
        print('   §B ' + ' '.join('%s=%s' % (kk, B.get(kk)) for kk in
                                  ('1_slot_val', '2_col', '3_off', '4_td', '5_mangled',
                                   '6_install', '7_func_ok', '8_class'))
              + '  all8=%s' % B['all8'])
        print('      asm@site: %s   imm=%s  func=%s  体内self-install=%s'
              % (B.get('6_asm'), B.get('6_imm'), B.get('7_func'), B.get('self_install_sites')))
        print('   §D parse=%s slot_ok=%s entry_ok=%s d47=%s no_124=%s'
              % (D.get('parse'), D.get('slot_ok'), D.get('entry_ok'),
                 D.get('d47_ok'), D.get('no_124')))
        print('      §D 交叉：slot==name:%s cls==name:%s/%s/%s func==实测:%s '
              'td==实测:%s col==实测:%s vt∈表枚举:%s → D_ALL=%s'
              % (D.get('slot_eq_name'), D.get('cls_eq_name'), D.get('cls2_eq_name'),
                 D.get('cls3_eq_name'), D.get('func_eq_measured'),
                 D.get('td_eq_measured'), D.get('col_eq_measured'),
                 D.get('vt_eq_enum'), D.get('all_ok')))

        bc_rows.append(dict(
            row=k, entry=entry_s, name=name, name_cls=name_cls, slot=name_slot,
            vt=(('%08X' % vt) if vt else '-'),
            b1=('T' if B.get('1_slot_val') else 'F'),
            b2=('T' if B.get('2_col') else 'F'),
            b3=('T' if B.get('3_off') else 'F'),
            b4=('T' if B.get('4_td') else 'F'),
            b5=('T' if B.get('5_mangled') else 'F'),
            b6=('T' if B.get('6_install') else 'F'),
            b7=('T' if B.get('7_func_ok') else 'F'),
            b8=('T' if B.get('8_class') == 'match' else 'F'),
            b8s=('T' if B.get('8_class_strict') == 'match' else 'F'),
            all8=('T' if B['all8'] else 'F'),
            site=B.get('6_site') or '-', asm=B.get('6_asm') or '-',
            func=B.get('7_func') or '-',
            td=B.get('td_measured') and ('%08X' % int(B['td_measured'])) or '-',
            col=B.get('col_measured') and ('%08X' % int(B['col_measured'])) or '-',
            off=(B.get('3_off') and '0' or '?'),
            mangled=B.get('mangled_measured') or '-',
            a_other7=('T' if A.get('other7') else 'F'),
            a_prefix=('T' if A.get('col4_prefix') else 'F'),
            a_grade=('T' if A.get('grade_ok') else 'F'),
            d_parse=('T' if D.get('parse') else 'F'),
            d_d47=('T' if D.get('d47_ok') else 'F'),
            d_no124=('T' if D.get('no_124') else 'F'),
            d_all=('T' if D.get('all_ok') else 'F'),
            d_cls=('T' if (D.get('cls_eq_name') and D.get('cls2_eq_name') and
                           D.get('cls3_eq_name')) else 'F'),
            d_func=('T' if D.get('func_eq_measured') else 'F'),
            a_only_col4=('T' if (A.get('byte_same') and
                                 [i for i in range(8) if not A['byte_same'][i]] == [3])
                         else 'F'),
            same_slot=len(same_slot),
            same_slot_live=len(same_slot_live),
            same_slot_live_cls=len(same_slot_live_cls),
            self_install=';'.join(B.get('self_install_sites') or []),
        ))

    # ---- §E 格式合先例
    print('\n' + '=' * 100)
    print('§E 格式合先例（对照前三次并表 43 行「④ 活表槽位见证 + D-47」与三条先例 00464AC0/004DE630/004F42F0）')
    print('=' * 100)
    with open(COV_PIN, 'rb') as f:
        craw = f.read()
    crows = [l.split(b'\t') for l in craw.split(b'\n') if l]
    crows = [c for c in crows if len(c) == 8]
    wit_rows = [c for c in crows if WITNESS in c[3].decode('utf-8', 'ignore')]
    dis43 = [c for c in wit_rows if '§12.6' in c[3].decode('utf-8', 'ignore')]
    prec_ents = ('00464AC0', '004DE630', '004F42F0')
    precs = [c for c in crows if c[0].decode().strip() in prec_ents]
    print('  盘上含「④ 活表槽位见证」行 %d；其中带 §12.6 披露 %d；三条先例取到 %d'
          % (len(wit_rows), len(dis43), len(precs)))

    def wit_seg(s):
        i = s.find(WITNESS)
        return s[i:] if i >= 0 else None

    def skel(seg):
        """把 ④ 段按固定模板还原成骨架串（值全部占位）；不匹配返回 None。"""
        m = RE_WIT.search(seg)
        if not m:
            return None
        g = m.groupdict()
        core = ('④ 活表槽位见证：<CLS>::slot<N>（vt=<H>，槽 <N> 值=<H>，COL=<H> '
                'offset=<N>，RTTI=<H>→<M>；装表点 <H> 位于 <H> 体内，entry 体外） '
                '④升级句：<CLS>::slot<N>（④ 表属类与行名类一致，均为 <CLS>；'
                '该槽即其 vt=<H> 表 slot<N>，无归属歧义）')
        rest = seg[m.end():]
        d47 = bool(RE_D47_OK.search(rest))
        rest_clean = RE_D47_OK.sub('', rest).replace('（）', '').strip()
        return core, d47, rest_clean

    E = {}
    b2_sk = collections.Counter()
    b2_rest_bad = 0
    for k, c in enumerate(drows, 19):
        seg = wit_seg(c[3].decode('utf-8', 'replace'))
        sk = skel(seg) if seg else None
        if sk is None:
            b2_rest_bad += 1
            per[c[0].decode().strip().upper()]['E_skel'] = None
            continue
        b2_sk[(sk[0], sk[1], sk[2])] += 1
        per[c[0].decode().strip().upper()]['E_skel'] = sk
    print('  B2 18 行 ④ 段骨架种类 : %d（应 1）' % len(b2_sk))
    if b2_sk:
        print('    骨架: %s' % b2_sk.most_common(1)[0][0][0][:300])
        print('    骨架外残留种类: %s' % set((sk[1], sk[2]) for sk in b2_sk))
    prec_sk = []
    for c in precs:
        seg = wit_seg(c[3].decode('utf-8', 'replace'))
        prec_sk.append(skel(seg) if seg else None)
    print('  三条先例 ④ 段骨架全部可解析 : %s' % all(p is not None for p in prec_sk))
    b2_cores = set(x[0] for x in b2_sk)
    prec_cores = set(p[0] for p in prec_sk if p)
    print('    先例骨架 == B2 骨架        : %s（先例无 D-47 后缀）'
          % (prec_cores and prec_cores <= b2_cores))
    print('    先例 D-47 后缀              : %s（应全 False，先例属前批）'
          % [p[1] for p in prec_sk if p])
    print('    先例骨架外残留              : %s（应为空串）'
          % set(p[2] for p in prec_sk if p))
    d43_sk = Counter()
    for c in dis43:
        seg = wit_seg(c[3].decode('utf-8', 'replace'))
        s2 = skel(seg) if seg else None
        if s2:
            d43_sk[(s2[0], s2[1], s2[2])] += 1
    print('  43 行 D-47 行 ④ 骨架种类    : %d' % len(d43_sk))
    print('    B2 骨架 ∩ 43 行骨架        : %d（应 1，即同骨架）'
          % len(set(b2_sk) & set(d43_sk)))
    if set(b2_sk) - set(d43_sk):
        print('    B2 独有骨架差 : %s' % (set(b2_sk) - set(d43_sk)))
    E['b2_skeleton_kinds'] = len(b2_sk)
    E['b2_skeleton'] = list(b2_sk)[0][0] if b2_sk else None
    E['b2_rest'] = [list(x[1:]) for x in b2_sk]
    E['prec_parsed'] = all(p is not None for p in prec_sk)
    E['prec_skeleton_in_b2'] = bool(prec_cores) and prec_cores <= b2_cores
    E['d43_skeleton_kinds'] = len(d43_sk)
    E['b2_and_d43_share'] = len(set(b2_sk) & set(d43_sk))
    # 追加段是否以 '；' 起
    E['sep_ok'] = sum(1 for c in drows
                      if '；' + WITNESS in c[3].decode('utf-8', 'replace'))
    print('  追加段以「；④ 活表槽位见证」起 : %d/18' % E['sep_ok'])
    # ④ 段是否在行尾（无后续内容）
    E['at_tail'] = sum(1 for c in drows
                       if c[3].decode('utf-8', 'replace').rstrip().endswith('披露）'))
    print('  ④ 段位于第 4 列末尾           : %d/18' % E['at_tail'])

    # ---- §D 汇总 / 披露指针
    print('\n' + '=' * 100)
    print('§D 汇总：披露指针 / 文本-事实一致')
    print('=' * 100)
    n126 = sum(1 for c in drows if '§12.6' in c[3].decode('utf-8', 'replace'))
    n124 = sum(1 for c in drows if '§12.4' in c[3].decode('utf-8', 'replace'))
    nd47 = sum(1 for c in drows if RE_D47_OK.search(c[3].decode('utf-8', 'replace')))
    print('  含 §12.6 = %d/18 ; 含 §12.4 = %d/18 ; D-47 披露指针完整 = %d/18' % (n126, n124, nd47))

    # ---- §F 反抄袭
    print('\n' + '=' * 100)
    print('§F 反抄袭（entry 归一为占位符后两两不同）')
    print('=' * 100)
    norm = []
    for c in drows:
        s = c[3].decode('utf-8', 'replace')
        s = re.sub(r'[0-9A-Fa-f]{8}', '<ADDR>', s)
        norm.append(s)
    print('  原文 18 行 set 大小 : %d' % len(set(c[3] for c in drows)))
    print('  entry 归一后 set 大小: %d' % len(set(
        re.sub(c[0].decode().strip().upper(), '<ENTRY>', c[3].decode('utf-8', 'replace'))
        for c in drows)))
    print('  全地址归一后 set 大小: %d' % len(set(norm)))
    dup = [k for k, v in collections.Counter(norm).items() if v > 1]
    print('  全地址归一重复文本 : %d 组' % len(dup))
    res['F'] = dict(n_orig=len(set(c[3] for c in drows)), n_norm=len(set(norm)),
                    dup=len(dup))

    # ---- 汇总
    def cnt(pred):
        return sum(1 for v in per.values() if pred(v))

    summ = dict(
        A_other7_bad=cnt(lambda v: not v['A'].get('other7')),
        A_prefix_bad=cnt(lambda v: not v['A'].get('col4_prefix')),
        A_grade_bad=cnt(lambda v: not v['A'].get('grade_ok')),
        A_cols8_bad=cnt(lambda v: not v['A'].get('cols8')),
        B_all8_bad=cnt(lambda v: not v['B']['all8']),
        B1_bad=cnt(lambda v: not v['B'].get('1_slot_val')),
        B2_bad=cnt(lambda v: not v['B'].get('2_col')),
        B3_bad=cnt(lambda v: not v['B'].get('3_off')),
        B4_bad=cnt(lambda v: not v['B'].get('4_td')),
        B5_bad=cnt(lambda v: not v['B'].get('5_mangled')),
        B6_bad=cnt(lambda v: not v['B'].get('6_install')),
        B7_bad=cnt(lambda v: not v['B'].get('7_func_ok')),
        B8_bad=cnt(lambda v: v['B'].get('8_class') != 'match'),
        B8s_bad=cnt(lambda v: v['B'].get('8_class_strict') != 'match'),
        D_parse_bad=cnt(lambda v: not v['D'].get('parse')),
        D_all_bad=cnt(lambda v: not v['D'].get('all_ok')),
        A_only_col4_bad=cnt(lambda v: not (v['A'].get('byte_same') and
                                          [i for i in range(8)
                                           if not v['A']['byte_same'][i]] == [3])),
        D_d47_bad=cnt(lambda v: not v['D'].get('d47_ok')),
        D_124_bad=cnt(lambda v: not v['D'].get('no_124')),
        C_not_unique=cnt(lambda v: v['c_n_same_slot_live_cls'] != 1),
        C_multi=cnt(lambda v: v['c_n_same_slot_live_cls'] > 1),
        C2_disagree=cnt(lambda v: not v['c2_agree']),
        C2_multi=cnt(lambda v: len(v['c2']['same_slot_live_cls']) > 1),
        self_install=cnt(lambda v: bool(v['B'].get('self_install_sites'))),
        not_live_solely_by_entry=cnt(lambda v: not v['B'].get('has_outside_site')),
    )
    print('\n' + '=' * 100)
    print('汇总')
    print('=' * 100)
    for k2, v2 in summ.items():
        print('  %-16s %d' % (k2, v2))
    print('\n  §C 同槽多表行：')
    for e2, v2 in per.items():
        if v2['c_n_same_slot_live_cls'] > 1:
            print('    %s %s → %d 张类一致的活表' % (e2, v2['name'],
                                                 v2['c_n_same_slot_live_cls']))
            for t in v2['tables']:
                print('       vt=%s slot=%s live=%s cls=%s' % (t['vt'], t['slot'],
                                                              t['live'], t['cls_match']))
    print('\n  同槽有表但「活着」的只有 0 张的行：')
    for e2, v2 in per.items():
        if v2['c_n_same_slot_live'] == 0:
            print('    %s %s' % (e2, v2['name']))
    print('\n  体内 self-install 同表行（证据强度附注项）：')
    for e2, v2 in per.items():
        if v2['B'].get('self_install_sites'):
            print('    %s %s  体内装表点=%s  采用的体外装表点=%s'
                  % (e2, v2['name'], v2['B']['self_install_sites'], v2['B'].get('6_site')))
    print('\n  槽号/类名一致性：')
    for e2, v2 in per.items():
        if v2['B'].get('8_class_strict') != 'match':
            print('    %s %s  strict=%s  mangled=%s'
                  % (e2, v2['name'], v2['B'].get('8_class_strict'),
                     v2['B'].get('mangled_measured')))

    res['summary'] = summ
    res['E'] = E
    res['per'] = per
    res['atlas_missing'] = [e2 for e2 in per if e2 not in atlas]

    # ---- 第三口径：raw 文件偏移复核 6 项核心事实
    print('\n' + '=' * 100)
    print('第三口径（raw 文件偏移直读，不经虚拟缓冲）复核 6 项核心事实')
    print('=' * 100)
    rf = RawFile(EXE)
    raw_bad = []
    for e2, v2 in per.items():
        D2 = v2['D']
        if not D2.get('parse'):
            raw_bad.append((e2, 'no-parse'))
            continue
        vt = int(D2['vt'], 16)
        slot = int(D2['slot'])
        chk = {
            'r1_slot': rf.u32(vt + slot * 4) == int(e2, 16),
            'r2_col': rf.u32(vt - 4) == int(D2['col'], 16),
            'r3_off': rf.u32(int(D2['col'], 16) + 4) == D2['off'],
            'r4_td': rf.u32(int(D2['col'], 16) + 12) == int(D2['td'], 16),
            'r5_mangled': rf.cstr(int(D2['td'], 16) + 8, 256) == D2['mangled'],
        }
        site = int(D2['site'], 16)
        _mn, _ops, insn = decode_site(img, site)
        ok_mov, imm = imm_and_memkind(insn)
        chk['r6_install'] = bool(ok_mov and imm == vt)
        bad = [kk for kk, vv in chk.items() if not vv]
        if bad:
            raw_bad.append((e2, ','.join(bad)))
        v2['raw_checks'] = chk
    rf.close()
    print('  raw 口径不一致行数 : %d %s' % (len(raw_bad), raw_bad if raw_bad else '（全部一致）'))
    res['raw_bad'] = raw_bad
    summ['raw_bad'] = len(raw_bad)

    # ---- 写产物
    cols = [('row', 'row'), ('entry', 'entry'), ('name', 'name'),
            ('name_cls', 'name_cls'), ('slot', 'slot'), ('vt', 'vt'),
            ('B1_u32_vt_slot_eq_entry', 'b1'), ('B2_u32_vt_m4_eq_COL', 'b2'),
            ('B3_u32_COL_p4_eq_offset', 'b3'), ('B4_u32_COL_p12_eq_TD', 'b4'),
            ('B5_cstr_TD_p8_eq_mangled', 'b5'), ('B6_install_mov_mem_imm', 'b6'),
            ('B7_site_func_ne_entry', 'b7'), ('B8_TD_name_class_match', 'b8'),
            ('B8_strict', 'b8s'), ('ALL8', 'all8'),
            ('install_site', 'site'), ('asm_at_site', 'asm'), ('site_func', 'func'),
            ('TD_measured', 'td'), ('COL_measured', 'col'), ('mangled_measured', 'mangled'),
            ('A_other7_byte_same', 'a_other7'), ('A_col4_strict_prefix', 'a_prefix'),
            ('A_grade_kept', 'a_grade'),
            ('D_parse', 'd_parse'), ('D_d47_ptr', 'd_d47'), ('D_no_12_4', 'd_no124'),
            ('D_all_consistent', 'd_all'), ('D_class_3places', 'd_cls'),
            ('D_func_eq_measured', 'd_func'),
            ('A_only_col4_changed', 'a_only_col4'),
            ('C1_same_slot_tables', 'same_slot'),
            ('C1_same_slot_live', 'same_slot_live'),
            ('C1_same_slot_live_classmatch', 'same_slot_live_cls'),
            ('entry_self_install_sites', 'self_install')]
    with open(os.path.join(HERE, 'bytecheck.tsv'), 'w', encoding='utf-8', newline='') as f:
        f.write('\t'.join(h for h, _k in cols) + '\n')
        for r in bc_rows:
            f.write('\t'.join(str(r[k]) for _h, k in cols) + '\n')
    with open(os.path.join(HERE, 'verify_out.json'), 'w', encoding='utf-8') as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    print('\nwrote bytecheck.tsv / verify_out.json  (%s)' % HERE)
    return 0


if __name__ == '__main__':
    sys.exit(main())
