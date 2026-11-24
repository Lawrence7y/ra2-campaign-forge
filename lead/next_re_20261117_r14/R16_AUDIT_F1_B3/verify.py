# -*- coding: utf-8 -*-
"""
R16-AUDIT-F1-B3 —— 审计员独立复算脚本（B3 = 派生集合第 37-54 行）

独立性声明：
  * 不 import 任何执行器脚本（R16_F1_B3/*.py 一律不读、不调），也不 import PROBE_802/probe.py。
  * PE 读取、RTTI 解析、表起点枚举、.text 全量 capstone 反汇编（skipdata）、装表点解码，
    全部本文件自写，独立跑一遍。
  * gamemd.exe 只读打开；只写本目录（sys.dont_write_bytecode 防留 .pyc）。

审计项：
  §A 最小改动 / 原文保全（对开卡时盘上 coverage 快照 _pin_coverage.tsv 逐字节）
  §B 8 项字节事实独立复算（6 项卡面 + 2 项附加）
  §C 指定主题：18 行定表唯一性
       c1 同槽号持有它的活表张数 / 其中类一致张数（两条互相独立的口径）
       c2 本 entry 体内是否也装同一张表（self-install）
       c3 改前第 4 列是否已含其它 ④ 表述（同格并存两条 ④）＋ 旧 ④ 与新事实是否矛盾
  §D 文本与事实一致 + 披露指针 §12.6
  §E 格式合先例
  §F 反抄袭（entry 归一 / 全地址归一后两两不同）

跑法：  python verify.py
产物：  bytecheck.tsv / verify_out.json / tables.md / run_log.txt
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
COV_LIVE = os.path.join(R14, 'COVERAGE', 'coverage.tsv')
AUDIT_TSV = os.path.join(R14, 'R16_PROBE_4GAP', 'scan_F1_audit.tsv')
DELTA = os.path.join(R14, 'R16_F1_B3', 'delta.tsv')
FIELDS = os.path.join(R14, 'R16_F1_B3', 'fields.tsv')
ATLAS = os.path.join(ROOT, 'lead', 'next_re_20261112_r10', 'W130_atlas',
                     'function_atlas.tsv')

EXPECT_EXE_SHA = '73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476'
IMAGE_BASE = 0x400000
TEXT_LO, TEXT_HI = 0x401000, 0x7E038D
WITNESS = '④ 活表槽位见证'
BATCH_LO, BATCH_HI = 37, 55          # 派生集合第 37-54 行（1-based, 左闭右开）


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
    """table_start-4 必须是 COL 绝对 VA 且 RTTI 链自洽 ⇒ 认定 table_start 是表起点。"""
    col = img.u32(table_start - 4)
    if not img.in_image(col) or img.u32(col) is None or img.u32(col) != 0:
        return None
    td = img.u32(col + 12)
    if not img.in_image(td):
        return None
    nm = img.cstr(td + 8, 256)
    if not nm or not nm.startswith('.?A'):
        return None
    return dict(col=col, td=td, mangled=nm)


# ---------------------------------------------------------------- .text 全扫（自写）
class StoreScan(object):
    """capstone 线性反汇编全 .text（skipdata=True），收 `mov <mem>, imm32`。"""

    def __init__(self, img):
        import capstone
        t = [s for s in img.secs if s['name'] == '.text'][0]
        n = min(len(t['data']), TEXT_HI - t['va'])
        self.lo = t['va']
        self.code = bytes(t['data'][:n])
        self.hi = self.lo + len(self.code)
        self.stores = collections.defaultdict(list)    # imm -> [(site, disp, base_reg)]
        self.calls = collections.defaultdict(list)     # target -> [site]
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
            if insn.mnemonic == 'call':
                ops = insn.operands
                if len(ops) == 1 and ops[0].type == X.X86_OP_IMM:
                    tgt = ops[0].imm & 0xFFFFFFFF
                    if TEXT_LO <= tgt < TEXT_HI:
                        self.calls[tgt].append(insn.address)
                continue
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

    def callers_of(self, func):
        return self.calls.get(func, [])


def decode_site(img, site):
    import capstone
    off = site - IMAGE_BASE
    raw = bytes(img.buf[off:off + 16])
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = True
    for insn in md.disasm(raw, site):
        return insn.mnemonic, insn.op_str, insn
    return None, None, None


def imm_and_memkind(insn):
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
    m = re.match(r'^(?P<cls>.+?)::slot(?P<slot>\d+)$', name.strip())
    if not m:
        return None, None
    return m.group('cls'), int(m.group('slot'))


def class_match(name_cls, mangled):
    """沿用项目既有口径（T_ 伪名按分片全含）。"""
    if not name_cls or not mangled:
        return 'none'
    if name_cls.startswith('T_'):
        parts = [p for p in name_cls[2:].rstrip('_').split('_') if p]
        return 'match' if all(p in mangled for p in parts) else 'nomatch'
    return 'match' if name_cls in mangled else 'nomatch'


def class_match_strict(name_cls, mangled):
    """严口径：非模板名要求 mangled 恰为 .?AV<Class>@@；模板名要求参数类完全一致。"""
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
    """复现 probe.py vtable_start 的字面语义（首个失败处停），仅作口径对照。"""
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
    """枚举 .rdata/.data 内全部合法表起点（t-4 为自洽 COL）。与命中扫描完全独立。"""
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
    """第三口径：不经虚拟缓冲，按 PE 段表把 VA 映射到文件偏移读字节。"""

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
    """扫 .rdata/.data 里 4 字节对齐的 dd entry，逐命中反推所在表（口径 1）。"""
    pat = entry.to_bytes(4, 'little')
    hits = []
    for s in img.secs_named('.rdata', '.data'):
        d = s['data']
        i = d.find(pat)
        while i >= 0:
            if i % 4 == 0:
                hits.append(s['va'] + i)
            i = d.find(pat, i + 1)
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
        owner, oc = cands[0]
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
        out.append(ln.split(b'\t'))
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

SKEL_CORE = ('④ 活表槽位见证：<CLS>::slot<N>（vt=<H>，槽 <N> 值=<H>，COL=<H> '
             'offset=<N>，RTTI=<H>→<M>；装表点 <H> 位于 <H> 体内，entry 体外） '
             '④升级句：<CLS>::slot<N>（④ 表属类与行名类一致，均为 <CLS>；'
             '该槽即其 vt=<H> 表 slot<N>，无归属歧义）')


def wit_seg(s):
    i = s.find(WITNESS)
    return s[i:] if i >= 0 else None


def skel(seg):
    if seg is None:
        return None
    m = RE_WIT.search(seg)
    if not m:
        return None
    rest = seg[m.end():]
    d47 = bool(RE_D47_OK.search(rest))
    rest_clean = RE_D47_OK.sub('', rest).replace('（）', '').strip()
    return SKEL_CORE, d47, rest_clean, m


def old_marks(txt):
    """从旧第 4 列里抽出已有的 ④ 表述（按 '④' 出现位置切出邻域片段）。"""
    out = []
    for m in re.finditer('④', txt):
        a = max(0, m.start() - 8)
        b = min(len(txt), m.start() + 60)
        out.append(txt[a:b].replace('\t', ' '))
    return out


STMT_PREV = set(['', '。', '；', '）', ')', '\t', ' '])


def diamond_statements(txt):
    """切出「④ …」语句（不是 '②④ 不同源' / '④ 锚点…' / '即 ④，' 这类内嵌提及）。

    判定顺序：
      1) '④升级句' → 计作 升级句（追加段模板成分）
      2) '④' 后紧跟的不是空格（如 '④，'）→ 内嵌提及，跳过
      3) '④ 表属类…' → ④升级句括号内的内嵌成分，跳过
      4) 前一个字符 ∈ {串首, 。, ；, ）, ), 空白} → 一条独立 ④ 语句（范围到下一个 '。'）
    """
    out = []
    for m in re.finditer('④', txt):
        j = m.start()
        if txt[j + 1:j + 4].startswith('升级'):
            out.append(('升级句', txt[j:j + 40]))
            continue
        if j + 1 >= len(txt) or txt[j + 1] != ' ':
            continue
        if txt[j + 2:j + 5] == '表属类':
            out.append(('内嵌', txt[j:j + 40]))
            continue
        prev = txt[j - 1] if j > 0 else ''
        if prev not in STMT_PREV:
            continue
        e = txt.find('。', j)
        seg = txt[j:(e + 1) if e >= 0 else len(txt)]
        out.append(('stmt', seg))
    return out


def old_claims(oldseg, vt, col, td, site, func, slot, name_cls, caller_hosts):
    """旧 ④ 语句里明写的 vt/ctor/@站点/slot/COL/TD/宿主 与新实测是否矛盾。"""
    res = {}
    vts = [v.upper() for v in re.findall(r'vt ([0-9A-Fa-f]{8})', oldseg)]
    res['old_vt'] = vts
    res['old_vt_ok'] = all(v == ('%08X' % vt) for v in vts) if (vts and vt) else None
    ctors = [c.upper() for c in re.findall(r'ctor ([0-9A-Fa-f]{8})', oldseg)]
    res['old_ctor'] = ctors
    res['old_ctor_ok'] = (all(c == ('%08X' % func) for c in ctors)
                          if (ctors and func) else None)
    ats = [a.upper() for a in re.findall(r'@([0-9A-Fa-f]{8})', oldseg)]
    res['old_at'] = ats
    res['old_site_ok'] = ((('%08X' % site) in ats) if (ats and site) else None)
    slots = re.findall(r'slot#?(\d+)', oldseg)
    res['old_slot'] = slots
    res['old_slot_ok'] = (all(int(s) == slot for s in slots) if (slots and slot is not None)
                          else None)
    res['old_col'] = [x.upper() for x in re.findall(r'COL=([0-9A-Fa-f]{8})', oldseg)]
    res['old_col_ok'] = (all(int(x, 16) == col for x in res['old_col'])
                         if (res['old_col'] and col) else None)
    res['old_td'] = [x.upper() for x in re.findall(r'TD=([0-9A-Fa-f]{8})', oldseg)]
    res['old_td_ok'] = (all(int(x, 16) == td for x in res['old_td'])
                        if (res['old_td'] and td) else None)
    hosts = [h.upper() for h in re.findall(r'宿主 ([0-9A-Fa-f]{8})', oldseg)]
    res['old_host'] = hosts
    # 旧文「宿主」既可指装表点所在函数，也可指调用该 ctor 的注册函数；两者都接受，但必须可核
    hstat = []
    for h in hosts:
        hv = int(h, 16)
        if func is not None and hv == func:
            hstat.append('is_install_func')
        elif hv in caller_hosts:
            hstat.append('is_caller_host')
        else:
            hstat.append('UNVERIFIED')
    res['old_host_status'] = hstat
    res['old_host_ok'] = (all(s != 'UNVERIFIED' for s in hstat) if hstat else None)
    res['old_class_seen'] = (name_cls in oldseg) if name_cls else None
    return res


# ---------------------------------------------------------------- 主流程
def main():
    out_lines = []

    def P(*a):
        s = ' '.join(str(x) for x in a)
        print(s)
        out_lines.append(s)

    res = dict(errors=[], notes=[])
    P('=' * 100)
    P('R16-AUDIT-F1-B3 · 审计员独立复算（B3 = 派生集合第 37-54 行）')
    P('=' * 100)

    # ---- 环境与指纹
    exe_sha = sha256p(EXE)
    cov_sha = sha256p(COV_PIN)
    live_sha = sha256p(COV_LIVE)
    P('gamemd.exe sha256 : %s' % exe_sha)
    P('  expect          : %s  %s' % (EXPECT_EXE_SHA,
                                      'OK' if exe_sha == EXPECT_EXE_SHA else '!! MISMATCH'))
    P('coverage 快照 sha : %s  (%d B)' % (cov_sha, os.path.getsize(COV_PIN)))
    P('coverage 现盘 sha : %s  (%d B)  %s'
      % (live_sha, os.path.getsize(COV_LIVE),
         '与快照相同（无并发改动）' if live_sha == cov_sha else '!! 与快照不同'))
    res['exe_sha'] = exe_sha
    res['cov_pin_sha'] = cov_sha
    res['cov_live_sha'] = live_sha
    if exe_sha != EXPECT_EXE_SHA:
        res['errors'].append('gamemd.exe sha 不符卡面')

    img = Image(EXE)
    P('ImageBase         : %08X（卡面 0x400000）%s'
      % (img.base, 'OK' if img.base == IMAGE_BASE else '!! MISMATCH'))
    tsec = [s for s in img.secs if s['name'] == '.text'][0]
    P('.text             : [%08X,%08X)  卡面 [0x401000,0x7E038D)'
      % (tsec['va'], tsec['va'] + min(len(tsec['data']), TEXT_HI - tsec['va'])))

    # ---- 派生集合复现
    aidx, arows = load_audit()
    cov = load_cov(COV_PIN)
    P('\n--- 派生集合复现（卡面 §2 判据）---')
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
    P('  S0 all F1 gap rows             : %d' % len(s0))
    P('  S1 same_source==no             : %d' % len(s1))
    P('  S2 +install decoded            : %d' % len(s2))
    P('  S3 +install outside body       : %d' % len(s3))
    P('  S4 +[已证] & no ④ witness       : %d  <== derived set' % len(s4))
    s4s = sorted(s4, key=lambda r: int(r[aidx['entry']], 16))
    ents = [r[aidx['entry']].upper() for r in s4s]
    B3 = ents[BATCH_LO - 1:BATCH_HI - 1]
    P('  derived=%d（卡面 76）  → B3 切片 = 第 %d-%d 行，共 %d 行'
      % (len(ents), BATCH_LO, BATCH_HI - 1, len(B3)))
    P('  B3 = %s' % ' '.join(B3))
    res['derived_n'] = len(ents)
    res['B3'] = B3
    if len(ents) != 76:
        res['errors'].append('派生集合 %d 行 ≠ 卡面 76' % len(ents))

    # ---- delta / fields 装载
    dhdr, drows = load_delta()
    P('\ndelta.tsv         : 表头 %s'
      % [c.decode("utf-8", "replace") for c in dhdr])
    P('                    数据行 %d（应 18）' % len(drows))
    dent = [c[0].decode('utf-8', 'ignore').strip().upper() for c in drows]
    if dent != B3:
        res['errors'].append('delta entry 序列 ≠ 派生集合第 37-54 行')
        P('  !! delta entry 序列与派生 B3 不一致')
        P('     delta:', ' '.join(dent))
    else:
        P('  OK  delta entry 序列 == 派生集合第 37-54 行（顺序也一致）')
    fhdr, frows = load_fields()
    P('fields.tsv        : %d 列 %s' % (len(fhdr), fhdr))
    # 与 B1/B2 切片无交集（硬要求）
    def load_fields_at(fp):
        with open(fp, encoding='utf-8') as f:
            ls = f.read().splitlines()
        return [ln.split('\t')[0].strip().upper() for ln in ls[1:] if ln.strip()]
    for prev in ('R16_F1_B1', 'R16_F1_B2'):
        fp = os.path.join(R14, prev, 'fields.tsv')
        if os.path.isfile(fp):
            es = set(load_fields_at(fp))
            P('  与 %s fields entry 交集: %d（应 0）' % (prev, len(es & set(B3))))
            if es & set(B3):
                res['errors'].append('%s 与 B3 有交集' % prev)

    # ---- 全 .text 反汇编（唯一的重活）
    P('\n--- 独立跑 capstone 全 .text 反汇编 ---')
    scan = StoreScan(img)
    P('  insn %d / skip %d  (区间 [%08X,%08X))'
      % (scan.n_insn, scan.n_skip, scan.lo, scan.hi))
    atlas = load_atlas()
    ranges = sorted((int(k, 16), int(k, 16) + v) for k, v in atlas.items() if v)
    P('  atlas 函数体 %d 个' % len(ranges))
    if not ranges:
        res['errors'].append('atlas 未装载')

    # 独立口径 2：枚举镜像内全部表起点
    P('\n--- 独立口径 2：枚举 .rdata/.data 内全部表起点 ---')
    tabs = all_table_starts(img)
    P('  合法表起点 %d 个（t-4 均为自洽 COL）' % len(tabs))
    tab_index = []
    for (p, c) in tabs:
        tab_index.append((p, c, table_slots(img, p)))
    by_val = collections.defaultdict(list)
    for (p, c, nsl) in tab_index:
        for j in range(nsl):
            v = img.u32(p + j * 4)
            if v is not None and TEXT_LO <= v < TEXT_HI:
                by_val[v].append((p, j))
    P('  建索引：%d 个表、%d 个不同槽值' % (len(tab_index), len(by_val)))

    starts_sorted = sorted(p for (p, _c, _n) in tab_index)
    start_set = set(starts_sorted)

    def table_extent(p):
        """该表的真实槽位范围：从 p 到「下一个合法表起点」为止（不因中间有洞而早停）。"""
        i = bisect.bisect_right(starts_sorted, p)
        nxt = starts_sorted[i] if i < len(starts_sorted) else p + 600 * 4
        return max(0, min(600, (nxt - p) // 4))

    def enum_holdings_greedy(e):
        """口径 2b：在每张表「到下一个表起点」的全槽位范围内找 entry（不提前截断）。"""
        out = []
        for (p, c, _nsl) in tab_index:
            for j in range(table_extent(p)):
                if img.u32(p + j * 4) == e:
                    out.append((p, j))
        return out

    # ---- 逐行
    P('\n' + '=' * 100)
    P('逐行审计（18/18，不抽样）')
    P('=' * 100)
    bc_rows = []
    per = {}
    details = []
    for k, erow in enumerate(s4s[BATCH_LO - 1:BATCH_HI - 1], BATCH_LO):
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

        # --- 口径 1：命中扫描
        hits, hits_all, tables = enum_tables(img, e)
        for t in tables:
            if t['vt'] is not None:
                t['sites'] = [s for (s, _d, _b) in scan.sites_of(t['vt'])]
                t['live'] = len(t['sites']) > 0
        live_tabs = [t for t in tables if t['vt'] is not None and t['live']]
        same_slot = [t for t in tables if t['vt'] is not None and t['slot'] == name_slot]
        same_slot_live = [t for t in same_slot if t['live']]
        same_slot_live_cls = [t for t in same_slot_live
                              if class_match(name_cls, t['mangled']) == 'match']
        same_slot_live_cls_strict = [t for t in same_slot_live
                                     if class_match_strict(name_cls, t['mangled']) == 'match']
        any_slot_cls = sorted(set(t['vt'] for t in live_tabs
                                  if class_match(name_cls, t['mangled']) == 'match'))

        # --- 口径 2：全表起点枚举
        holdings = by_val.get(e, [])
        hold_same_slot = [h for h in holdings if h[1] == name_slot]
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

        # --- 口径 2b：全表起点 × 全槽位（不提前截断）
        greedy = enum_holdings_greedy(e)
        greedy_same_slot = [h for h in greedy if h[1] == name_slot]
        greedy_extra = [('%08X' % p, j) for (p, j) in greedy
                        if (p, j) not in holdings]

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
            oldtxt = pcols[3].decode('utf-8', 'replace')
            A['n_diamond_old'] = oldtxt.count('④')
            A['has_old_diamond'] = oldtxt.count('④') > 0
            A['old_marks'] = old_marks(oldtxt)
            # 旧 ④ 里「活表槽位见证」不应已存在（否则不是 append-only 目标）
            A['old_has_witness'] = WITNESS in oldtxt
            A['n_diamond_new'] = txt.count('④')

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
            D['vt2_ok'] = (g['vt2'].upper() == g['vt'].upper())
        D['d47_ok'] = bool(RE_D47_OK.search(txt))
        D['no_124'] = '§12.4' not in txt

        # --- §B 8 项
        chosen = None
        if m:
            vt_claim = int(D['vt'], 16)
            chosen = next((t for t in tables if t['vt'] == vt_claim), None)
        if chosen is None and same_slot_live_cls:
            chosen = same_slot_live_cls[0]

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

        site = int(D['site'], 16) if D.get('site') else None
        func = None
        if site is not None:
            mn, ops, insn = decode_site(img, site)
            ok_mov, imm = imm_and_memkind(insn)
            B['6_install'] = bool(ok_mov and imm == vt)
            B['6_asm'] = '%s %s' % (mn, ops) if mn else None
            B['6_imm'] = None if imm is None else '%08X' % imm
            B['6_site'] = '%08X' % site
            B['6_in_linear_scan'] = any(s == site for (s, _d, _b)
                                        in (scan.sites_of(vt) if vt else []))
            func = which_body(ranges, site)
            B['7_func'] = '%08X' % func if func else None
            B['7_func_ok'] = (func is not None and func != e)
            B['7_func_size'] = atlas.get('%08X' % func) if func else None
            B['7_func_body_ok'] = bool(func is not None and B['7_func_size'] and
                                       func <= site < func + B['7_func_size'])
            size = atlas.get(entry_s)
            B['7_entry_size'] = size
            B['7_site_in_entry_body'] = bool(size and e <= site < e + size)
        else:
            B['6_install'] = False
            B['7_func_ok'] = False

        # 附加：本 entry 体内是否也装同一张表
        size = atlas.get(entry_s)
        body = (e, e + size) if size else (e, e)
        allsites = [s for (s, _d, _b) in (scan.sites_of(vt) if vt else [])]
        selfsites = [s for s in allsites if body[0] <= s < body[1]]
        outsites = [s for s in allsites if not (body[0] <= s < body[1])]
        B['self_install_sites'] = ['%08X' % s for s in selfsites]
        B['all_install_sites'] = ['%08X' % s for s in allsites]
        B['n_outside_sites'] = len(outsites)
        B['has_outside_site'] = len(outsites) >= 1
        B['entry_in_atlas'] = entry_s in atlas

        # ring4_at 一致性
        ring_tok = [t.upper() for t in re.findall(r'[0-9A-Fa-f]{8}', ring4_at)]
        B['ring4_has_site'] = (('%08X' % site) in ring_tok) if site else False
        B['ring4_has_func'] = (('%08X' % func) in ring_tok) if (site and func) else None

        eight = [B.get('1_slot_val'), B.get('2_col'), B.get('3_off'), B.get('4_td'),
                 B.get('5_mangled'), B.get('6_install'), B.get('7_func_ok'),
                 B.get('8_class') == 'match']
        B['all8'] = all(bool(x) for x in eight)

        # --- §C 附加 c3：旧 ④ 语句与新事实
        C = {}
        if pin is not None:
            oldtxt = pin['cols'][3].decode('utf-8', 'replace')
            stmts = [s for (kind, s) in diamond_statements(oldtxt) if kind == 'stmt']
            C['old_stmt_count'] = len(stmts)
            C['old_present'] = len(stmts) > 0
            C['old_statements'] = stmts
            oldseg = ' '.join(stmts)
            C['old_seg'] = oldseg[:600]
            callers = scan.callers_of(func) if func else []
            caller_hosts = set(which_body(ranges, cs) for cs in callers) - {None}
            C['callers_of_install_func'] = ['%08X' % c for c in callers]
            C['caller_hosts'] = sorted('%08X' % h for h in caller_hosts)
            oc = old_claims(oldseg, vt, B.get('col_measured'), B.get('td_measured'),
                            site, func, name_slot, name_cls, caller_hosts)
            C.update(oc)
            conflict = [kk for kk in ('old_vt_ok', 'old_ctor_ok', 'old_site_ok',
                                      'old_slot_ok', 'old_col_ok', 'old_td_ok',
                                      'old_host_ok')
                        if oc.get(kk) is False]
            C['old_conflicts'] = conflict
            C['old_consistent'] = (len(conflict) == 0)
            new_stmts = [s for (kind, s) in diamond_statements(txt) if kind == 'stmt']
            C['new_stmt_count'] = len(new_stmts)
            C['double_diamond'] = (len(stmts) >= 1 and len(new_stmts) >= 2)

        per[entry_s] = dict(
            entry=entry_s, name=name, name_cls=name_cls, name_slot=name_slot,
            same_source=same_source, ring4_at=ring4_at,
            A=A, B=B, C=C, D=D,
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
            c_n_same_slot_live_cls_strict=len(same_slot_live_cls_strict),
            c_any_slot_cls_tables=sorted('%08X' % v for v in any_slot_cls),
            c2=dict(all_slots=[('%08X' % p, j) for (p, j) in holdings],
                    same_slot=[('%08X' % h['vt'], h['slot']) for h in hold_rows],
                    same_slot_live=[('%08X' % h['vt'], h['slot']) for h in hold_live],
                    same_slot_live_cls=[('%08X' % h['vt'], h['slot']) for h in hold_live_cls]),
            c2_agree=(len(hold_live_cls) == len(same_slot_live_cls) and
                      len(hold_same_slot) == len(same_slot)),
            c2_n_live_cls=len(hold_live_cls),
            c2b_all=[('%08X' % p, j) for (p, j) in greedy],
            c2b_same_slot=len(greedy_same_slot),
            c2b_extra=greedy_extra,
        )

        # --- §D 交叉核对
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
                               'vt_eq_enum', 'off_eq_measured', 'vt2_ok'))
        else:
            D['all_ok'] = False

        # 控制台逐行
        P('\n#%d %s  %s  (same_source=%s)' % (k, entry_s, name, same_source))
        P('   §C 口径1 命中=%d  同槽(%s)表=%d 其中活=%d 其中类一致=%d(严=%d)  → %s'
          % (len(hits), name_slot, len(same_slot), len(same_slot_live),
             len(same_slot_live_cls), len(same_slot_live_cls_strict),
             '唯一' if len(same_slot_live_cls) == 1 else '多重(%d)' % len(same_slot_live_cls)))
        P('      §C 口径2 该 entry 全镜像表位=%d %s；同槽=%s；活=%s；类一致=%s → 与口径1 %s'
          % (len(holdings), per[entry_s]['c2']['all_slots'],
             per[entry_s]['c2']['same_slot'], per[entry_s]['c2']['same_slot_live'],
             per[entry_s]['c2']['same_slot_live_cls'],
             '一致' if per[entry_s]['c2_agree'] else '不一致'))
        P('      §C 口径2b（每张表到下一个表起点全槽位，不因洞早停）：表位=%d %s；同槽 %d；超出口径2 的新增 %s'
          % (len(greedy), per[entry_s]['c2b_all'][:8], len(greedy_same_slot),
             greedy_extra[:8] or '无'))
        if hits_all:
            P('      !! 非 .rdata/.data 段也有该地址命中: %s' % hits_all)
        for t in tables:
            nsl = table_slots(img, t['vt']) if t['vt'] else 0
            P('      table vt=%s slot=%s%s live=%s sites=%d slots=%d cls=%s%s'
              % (('%08X' % t['vt']) if t['vt'] else '----',
                 t['slot'], '' if t['slot'] == t['slot_back'] else
                 '[probe-repro vt=%s slot=%s]' % (
                     ('%08X' % t['vt_back']) if t['vt_back'] else '-', t['slot_back']),
                 t['live'], len(t['sites']), nsl,
                 class_match(name_cls, t['mangled']),
                 '' if class_match_strict(name_cls, t['mangled']) == 'match'
                 else ' [strict=%s]' % class_match_strict(name_cls, t['mangled'])))
        P('   §A cols8=%s other7_byte_same=%s col4_prefix=%s grade=%s 追加%dB 旧④=%d'
          % (A.get('cols8'), A.get('other7'), A.get('col4_prefix'),
             A.get('grade_ok'), A.get('appended_len', -1), A.get('n_diamond_old', -1)))
        P('   §B ' + ' '.join('%s=%s' % (kk, B.get(kk)) for kk in
                             ('1_slot_val', '2_col', '3_off', '4_td', '5_mangled',
                              '6_install', '7_func_ok', '8_class'))
          + '  all8=%s' % B['all8'])
        P('      asm@site: %s   imm=%s  func=%s  体内self-install=%s 体外站点数=%d'
          % (B.get('6_asm'), B.get('6_imm'), B.get('7_func'),
             B.get('self_install_sites'), B.get('n_outside_sites', -1)))
        P('   §D parse=%s d47=%s no_124=%s D_ALL=%s'
          % (D.get('parse'), D.get('d47_ok'), D.get('no_124'), D.get('all_ok')))
        P('   §C-c3 旧④语句=%s 旧④与新事实矛盾项=%s 旧④宿主=%s'
          % (C.get('old_stmt_count'), C.get('old_conflicts') or '无',
             C.get('old_host_status')))

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
            td=('%08X' % int(B['td_measured'])) if B.get('td_measured') else '-',
            col=('%08X' % int(B['col_measured'])) if B.get('col_measured') else '-',
            mangled=B.get('mangled_measured') or '-',
            a_other7=('T' if A.get('other7') else 'F'),
            a_prefix=('T' if A.get('col4_prefix') else 'F'),
            a_grade=('T' if A.get('grade_ok') else 'F'),
            d_parse=('T' if D.get('parse') else 'F'),
            d_d47=('T' if D.get('d47_ok') else 'F'),
            d_no124=('T' if D.get('no_124') else 'F'),
            d_all=('T' if D.get('all_ok') else 'F'),
            a_only_col4=('T' if (A.get('byte_same') and
                                 [i for i in range(8) if not A['byte_same'][i]] == [3])
                         else 'F'),
            c1_same_slot=len(same_slot),
            c1_live=len(same_slot_live),
            c1_live_cls=len(same_slot_live_cls),
            c1_live_cls_strict=len(same_slot_live_cls_strict),
            c2_same_slot=len(hold_same_slot),
            c2_live_cls=len(hold_live_cls),
            c2b_positions=len(greedy),
            c2b_same_slot=len(greedy_same_slot),
            self_install=';'.join(B.get('self_install_sites') or []) or '-',
            old_diamonds=C.get('old_stmt_count', -1) if pin is not None else -1,
            new_diamonds=C.get('new_stmt_count', -1) if pin is not None else -1,
            old_conflicts=','.join(C.get('old_conflicts') or []) or '-',
            n_outside=B.get('n_outside_sites', -1),
        ))

    # ---- §A 附加：与「现盘」coverage 对照（卡面 §4A：以开卡时盘上实值为准，但需判断并发写者）
    P('\n' + '=' * 100)
    P('§A 附加：并发写者判定（pin 快照 vs 现盘 coverage）')
    P('=' * 100)
    livc = load_cov(COV_LIVE)
    P('  pin entries %d / live entries %d ; 新增 %d / 消失 %d'
      % (len(cov), len(livc), len(set(livc) - set(cov)), len(set(cov) - set(livc))))
    changed_entries = []
    for e2, v2 in livc.items():
        p2 = cov.get(e2)
        if not p2:
            continue
        diff = [i for i in range(8) if v2['cols'][i] != p2['cols'][i]]
        if diff:
            changed_entries.append((e2, diff, p2['line_no'], v2['line_no']))
    P('  全盘内容变化 entry %d 个：%s' % (len(changed_entries),
        '; '.join('%s%s' % (e2, d) for e2, d, _a, _b in changed_entries)))
    mine = set(per)
    touched_mine = [x for x in changed_entries if x[0] in mine]
    P('  其中属于本批 18 行的：%d 个 %s' % (len(touched_mine),
        [x[0] for x in touched_mine]))
    line_shift = [x for x in changed_entries if x[2] != x[3]]
    mine_shift = [x[0] for x in line_shift if x[0] in mine]
    P('  发生行号位移的：%d 个（本批行号是否位移：%s）'
      % (len(line_shift), '是 %s' % mine_shift if mine_shift else '否'))
    live_ok = dict(n=0, bad=[])
    for e2, v2 in per.items():
        d2 = next((c for c in drows
                   if c[0].decode('utf-8', 'ignore').strip().upper() == e2), None)
        lv = livc.get(e2)
        if d2 is None or lv is None:
            live_ok['bad'].append((e2, 'missing'))
            continue
        diff = [i for i in range(8) if d2[i] != lv['cols'][i]]
        prefix = d2[3].startswith(lv['cols'][3])
        if diff == [3] and prefix:
            live_ok['n'] += 1
        else:
            live_ok['bad'].append((e2, diff, prefix))
    P('  与现盘逐字节对照：仅第 4 列不同且以现盘原值为前缀 %d/18；异常 %s'
      % (live_ok['n'], live_ok['bad'] or '无'))
    res['concurrency'] = dict(pin_n=len(cov), live_n=len(livc),
                              changed=[(e2, d) for e2, d, _a, _b in changed_entries],
                              touched_mine=[x[0] for x in touched_mine],
                              live_only_col4_ok=live_ok['n'],
                              live_bad=live_ok['bad'])

    # ---- §E 格式合先例
    P('\n' + '=' * 100)
    P('§E 格式合先例（三条先例 00464AC0/004DE630/004F42F0 + 盘上已并表带 §12.6 行）')
    P('=' * 100)
    with open(COV_PIN, 'rb') as f:
        craw = f.read()
    crows = [l.split(b'\t') for l in craw.split(b'\n') if l]
    crows = [c for c in crows if len(c) == 8]
    wit_rows = [c for c in crows if WITNESS in c[3].decode('utf-8', 'ignore')]
    dis_merged = [c for c in wit_rows if '§12.6' in c[3].decode('utf-8', 'ignore')]
    prec_ents = ('00464AC0', '004DE630', '004F42F0')
    precs = [c for c in crows if c[0].decode().strip() in prec_ents]
    P('  盘上含「④ 活表槽位见证」行 %d；其中带 §12.6 披露 %d；三条先例取到 %d'
      % (len(wit_rows), len(dis_merged), len(precs)))

    E = {}
    b3_sk = Counter()
    b3_bad = 0
    for c in drows:
        seg = wit_seg(c[3].decode('utf-8', 'replace'))
        sk = skel(seg)
        if sk is None:
            b3_bad += 1
            per[c[0].decode().strip().upper()]['E_skel'] = None
            continue
        b3_sk[(sk[0], sk[1], sk[2])] += 1
        per[c[0].decode().strip().upper()]['E_skel'] = sk[:3]
    P('  B3 18 行 ④ 段骨架种类 : %d（应 1）；解析失败 %d' % (len(b3_sk), b3_bad))
    for skk, cntt in b3_sk.items():
        P('    骨架×%d  D-47=%s  残留=%r' % (cntt, skk[1], skk[2]))
    prec_sk = [skel(wit_seg(c[3].decode('utf-8', 'replace'))) for c in precs]
    P('  三条先例骨架可解析 : %s' % all(p is not None for p in prec_sk))
    b3_cores = set(x[0] for x in b3_sk)
    prec_cores = set(p[0] for p in prec_sk if p)
    P('    先例骨架 == B3 骨架 : %s（先例无 D-47 后缀）'
      % (bool(prec_cores) and (prec_cores <= b3_cores)))
    P('    先例 D-47 后缀       : %s（应全 False）' % [p[1] for p in prec_sk if p])
    P('    先例骨架外残留       : %r（应为空串）' % set(p[2] for p in prec_sk if p))
    msk = Counter()
    for c in dis_merged:
        s2 = skel(wit_seg(c[3].decode('utf-8', 'replace')))
        if s2:
            msk[(s2[0], s2[1], s2[2])] += 1
    P('  盘上已并表 %d 行 ④ 骨架种类 : %d' % (len(dis_merged), len(msk)))
    P('    B3 骨架 ∩ 已并表骨架 : %d（应 1）' % len(set(b3_sk) & set(msk)))
    if set(b3_sk) - set(msk):
        P('    B3 独有骨架差 : %r' % (set(b3_sk) - set(msk),))
    E['b3_skeleton_kinds'] = len(b3_sk)
    E['b3_parse_bad'] = b3_bad
    E['prec_parsed'] = all(p is not None for p in prec_sk)
    E['prec_skeleton_in_b3'] = bool(prec_cores) and (prec_cores <= b3_cores)
    E['merged_skeleton_kinds'] = len(msk)
    E['b3_and_merged_share'] = len(set(b3_sk) & set(msk))
    E['sep_ok'] = sum(1 for c in drows
                      if '；' + WITNESS in c[3].decode('utf-8', 'replace'))
    P('  追加段以「；④ 活表槽位见证」起 : %d/18' % E['sep_ok'])
    E['at_tail'] = sum(1 for c in drows
                       if c[3].decode('utf-8', 'replace').rstrip().endswith('披露）'))
    P('  ④ 段位于第 4 列末尾           : %d/18' % E['at_tail'])
    # 字段齐全性
    need = ['vt=', '槽 ', '值=', 'COL=', 'offset=', 'RTTI=', '装表点 ', '体内，entry 体外',
            '④升级句：', '无归属歧义']
    E['fields_complete'] = sum(1 for c in drows
                               if all(x in c[3].decode('utf-8', 'replace') for x in need))
    P('  字段齐全（%d 个必需片段）      : %d/18' % (len(need), E['fields_complete']))

    # ---- §D 汇总
    P('\n' + '=' * 100)
    P('§D 汇总：披露指针')
    P('=' * 100)
    n126 = sum(1 for c in drows if '§12.6' in c[3].decode('utf-8', 'replace'))
    n124 = sum(1 for c in drows if '§12.4' in c[3].decode('utf-8', 'replace'))
    nd47 = sum(1 for c in drows if RE_D47_OK.search(c[3].decode('utf-8', 'replace')))
    P('  含 §12.6 = %d/18 ; 含 §12.4 = %d/18 ; D-47 披露句逐字完整 = %d/18'
      % (n126, n124, nd47))

    # ---- §F 反抄袭
    P('\n' + '=' * 100)
    P('§F 反抄袭（entry 归一为占位符后仍须两两不同）')
    P('=' * 100)
    norm = [re.sub(r'[0-9A-Fa-f]{8}', '<ADDR>', c[3].decode('utf-8', 'replace'))
            for c in drows]
    norm_entry = [re.sub(c[0].decode().strip().upper(), '<ENTRY>',
                         c[3].decode('utf-8', 'replace')) for c in drows]
    P('  原文 18 行 set 大小       : %d' % len(set(c[3] for c in drows)))
    P('  entry 归一后 set 大小     : %d' % len(set(norm_entry)))
    P('  全地址归一后 set 大小     : %d' % len(set(norm)))
    dup = [k2 for k2, v2 in Counter(norm).items() if v2 > 1]
    P('  全地址归一重复文本        : %d 组' % len(dup))
    for d in dup[:3]:
        P('    dup: %s' % d[:160])
    # 追加段两两（只看本批新增部分）
    app = []
    for c in drows:
        s = c[3].decode('utf-8', 'replace')
        i = s.find(WITNESS)
        app.append(s[i:] if i >= 0 else '')
    P('  仅追加段 set 大小         : %d' % len(set(app)))
    P('  仅追加段 entry 归一 set   : %d'
      % len(set(re.sub(c[0].decode().strip().upper(), '<ENTRY>', a)
                for c, a in zip(drows, app))))
    res['F'] = dict(n_orig=len(set(c[3] for c in drows)),
                    n_entrynorm=len(set(norm_entry)),
                    n_norm=len(set(norm)), dup=len(dup),
                    n_app=len(set(app)))

    # ---- 汇总
    def cnt(pred):
        return sum(1 for v in per.values() if pred(v))

    summ = dict(
        A_other7_bad=cnt(lambda v: not v['A'].get('other7')),
        A_prefix_bad=cnt(lambda v: not v['A'].get('col4_prefix')),
        A_grade_bad=cnt(lambda v: not v['A'].get('grade_ok')),
        A_cols8_bad=cnt(lambda v: not v['A'].get('cols8')),
        A_only_col4_bad=cnt(lambda v: not (v['A'].get('byte_same') and
                                          [i for i in range(8)
                                           if not v['A']['byte_same'][i]] == [3])),
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
        D_d47_bad=cnt(lambda v: not v['D'].get('d47_ok')),
        D_124_bad=cnt(lambda v: not v['D'].get('no_124')),
        C_not_unique=cnt(lambda v: v['c_n_same_slot_live_cls'] != 1),
        C_multi=cnt(lambda v: v['c_n_same_slot_live_cls'] > 1),
        C2_disagree=cnt(lambda v: not v['c2_agree']),
        C2_multi=cnt(lambda v: v['c2_n_live_cls'] > 1),
        C_self_install=cnt(lambda v: bool(v['B'].get('self_install_sites'))),
        C_old_diamond=cnt(lambda v: v.get('C', {}).get('old_present')),
        C_old_conflict=cnt(lambda v: v.get('C', {}).get('old_conflicts')),
        C_not_live_outside=cnt(lambda v: not v['B'].get('has_outside_site')),
        B7_func_body_bad=cnt(lambda v: not v['B'].get('7_func_body_ok')),
        C2b_extra=cnt(lambda v: v.get('c2b_extra')),
        A_live_only_col4_bad=0,
    )
    P('\n' + '=' * 100)
    P('汇总')
    P('=' * 100)
    for k2, v2 in summ.items():
        P('  %-20s %d' % (k2, v2))
    P('\n  §C 同槽多表（>1 张类一致活表）的行：')
    any_multi = False
    for e2, v2 in per.items():
        if v2['c_n_same_slot_live_cls'] > 1:
            any_multi = True
            P('    %s %s → %d 张类一致的活表' % (e2, v2['name'], v2['c_n_same_slot_live_cls']))
            for t in v2['tables']:
                P('       vt=%s slot=%s live=%s cls=%s' % (t['vt'], t['slot'],
                                                          t['live'], t['cls_match']))
    if not any_multi:
        P('    （无）')
    P('\n  体内 self-install 同表行：')
    if summ['C_self_install'] == 0:
        P('    （无）')
    for e2, v2 in per.items():
        if v2['B'].get('self_install_sites'):
            P('    %s %s 体内=%s 采用体外=%s' % (e2, v2['name'],
                                              v2['B']['self_install_sites'],
                                              v2['B'].get('6_site')))
    P('\n  旧第 4 列已含 ④ 语句的行（同格并存两条 ④）：')
    for e2, v2 in per.items():
        c3 = v2.get('C', {})
        P('    %s %-42s 旧④语句=%d 新④语句=%d 旧④与新事实矛盾项=%s'
          % (e2, v2['name'], c3.get('old_stmt_count', -1),
             c3.get('new_stmt_count', -1), c3.get('old_conflicts') or '无'))

    # ---- §C 四问四答（机读汇总，供 VERDICT §C 引用）
    P('\n' + '=' * 100)
    P('§C 四问四答汇总')
    P('=' * 100)
    q1 = [e2 for e2, v2 in per.items() if v2['c_n_same_slot_live_cls'] == 1]
    q1_all_pos = [e2 for e2, v2 in per.items() if len(v2['c2']['all_slots']) == 1]
    q2 = [e2 for e2, v2 in per.items()
          if v2['B'].get('8_class') == 'match' and v2['B'].get('8_class_strict') == 'match']
    q3 = [e2 for e2, v2 in per.items() if v2['B'].get('ring4_has_site')]
    P('  问1 同槽号类一致活表 == 1 的行 : %d/18' % len(q1))
    P('  问1 附加：该 entry 在全镜像只落 1 个表位的行 : %d/18' % len(q1_all_pos))
    P('  问2 TD+8 类名与行名类一致（松+严）: %d/18' % len(q2))
    P('  问3 采纳装表点 == ring4_at 首 token : %d/18' % len(q3))
    P('  问4 另有一张类一致活表的行（同槽）: %d'
      % sum(1 for v2 in per.values() if v2['c_n_same_slot_live_cls'] > 1))
    res['C4'] = dict(q1=len(q1), q1_all_pos=len(q1_all_pos), q2=len(q2),
                     q3=len(q3), multi=sum(1 for v2 in per.values()
                                           if v2['c_n_same_slot_live_cls'] > 1))

    res['summary'] = summ
    res['E'] = E
    res['per'] = per
    res['atlas_missing'] = [e2 for e2 in per if e2 not in atlas]

    # ---- 第三口径：raw 文件偏移复核
    P('\n' + '=' * 100)
    P('第三口径（raw 文件偏移直读，不经虚拟缓冲）复核 6 项核心事实')
    P('=' * 100)
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
    P('  raw 口径不一致行数 : %d %s' % (len(raw_bad), raw_bad if raw_bad else '（全部一致）'))
    res['raw_bad'] = raw_bad
    summ['raw_bad'] = len(raw_bad)

    # ---- 写 bytecheck.tsv
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
            ('A_grade_kept', 'a_grade'), ('A_only_col4_changed', 'a_only_col4'),
            ('D_parse', 'd_parse'), ('D_d47_ptr', 'd_d47'), ('D_no_12_4', 'd_no124'),
            ('D_all_consistent', 'd_all'),
            ('C1_same_slot_tables', 'c1_same_slot'),
            ('C1_same_slot_live', 'c1_live'),
            ('C1_same_slot_live_classmatch', 'c1_live_cls'),
            ('C1_same_slot_live_classmatch_strict', 'c1_live_cls_strict'),
            ('C2_enum_same_slot', 'c2_same_slot'),
            ('C2_enum_same_slot_live_classmatch', 'c2_live_cls'),
            ('C2b_greedy_positions', 'c2b_positions'),
            ('C2b_greedy_same_slot', 'c2b_same_slot'),
            ('C3_entry_body_self_install_sites', 'self_install'),
            ('C3_old_col4_diamond_count', 'old_diamonds'),
            ('C3_new_col4_diamond_count', 'new_diamonds'),
            ('C3_old_vs_new_conflicts', 'old_conflicts'),
            ('B_outside_install_sites', 'n_outside')]
    with open(os.path.join(HERE, 'bytecheck.tsv'), 'w', encoding='utf-8', newline='') as f:
        f.write('\t'.join(h for h, _k in cols) + '\n')
        for r in bc_rows:
            f.write('\t'.join(str(r[k]) for _h, k in cols) + '\n')

    # ---- 写 tables.md（§C 独立枚举明细）
    tl = []
    tl.append('# R16-AUDIT-F1-B3 · §C 定表唯一性独立枚举')
    tl.append('')
    tl.append('> 由 `verify.py` 只读复算生成。口径 1：`.rdata`/`.data` 内 4 字节对齐 `dd <entry>` 命中'
              ' → 回走最近合法表起点（`t-4` 为自洽 COL）→ `slot=(hit-vt)/4`。')
    tl.append('> 口径 2：**不依赖命中扫描**，先枚举镜像内全部合法表起点，再逐个表逐槽位比对。')
    tl.append('> 「活」= 该表在 `.text` 内至少有一处 `mov <mem>, imm32(==vt)` 装表点。')
    tl.append('')
    for e2, v2 in per.items():
        tl.append('## %s · %s（slot %d）' % (e2, v2['name'], v2['name_slot']))
        tl.append('')
        tl.append('- 口径1：命中 %d 处；同槽(%d)持有该 entry 的表 **%d** 张，其中活 **%d** 张，'
                  '其中类一致 **%d** 张（严口径 %d）'
                  % (len(v2['hits']), v2['name_slot'], v2['c_n_same_slot'],
                     v2['c_n_same_slot_live'], v2['c_n_same_slot_live_cls'],
                     v2['c_n_same_slot_live_cls_strict']))
        tl.append('- 口径2：全镜像表位 %d 处 `%s`；同槽 `%s`；其中活 `%s`；类一致 `%s`'
                  % (len(v2['c2']['all_slots']), ' '.join(
                      '%s@slot%d' % (a, b) for a, b in v2['c2']['all_slots']),
                     v2['c2']['same_slot'], v2['c2']['same_slot_live'],
                     v2['c2']['same_slot_live_cls']))
        tl.append('- 本 entry 体内装同一张表的站点：`%s`；体外装表点 %d 处'
                  % (v2['B'].get('self_install_sites') or '无（0 处）',
                     v2['B'].get('n_outside_sites', -1)))
        tl.append('- 旧第 4 列已有 ④ 语句：%s（%d 条；追加后同格 %d 条）；旧 ④ 与新事实矛盾项：%s'
                  % (v2.get('C', {}).get('old_present'),
                     v2.get('C', {}).get('old_stmt_count', -1),
                     v2.get('C', {}).get('new_stmt_count', -1),
                     v2.get('C', {}).get('old_conflicts') or '无'))
        if v2.get('C', {}).get('old_statements'):
            tl.append('- 旧 ④ 原文：%s' % ' ⏎ '.join(v2['C']['old_statements'])[:800])
        if v2.get('C', {}).get('old_host'):
            tl.append('- 旧 ④「宿主」实测归类：%s（装表点函数=%s；调用该 ctor 的站点宿主=%s）'
                      % (v2['C'].get('old_host_status'), v2['B'].get('7_func'),
                         v2['C'].get('caller_hosts')))
        tl.append('')
        if v2['tables']:
            tl.append('| vt | 槽数 | COL | TD | TD+8 装饰名 | 类一致 | 活 | 装表点（前 6） | 本文所选 |')
            tl.append('|---|---|---|---|---|---|---|---|---|')
            for t in v2['tables']:
                vt_i = int(t['vt'], 16) if t['vt'] else None
                nsl = table_slots(img, vt_i) if vt_i else 0
                cc = col_at(img, vt_i) if vt_i else None
                sites = [s for (s, _d, _b) in (scan.sites_of(vt_i) if vt_i else [])]
                tl.append('| `%s` | %d | `%s` | `%s` | `%s` | %s | %s | %s | %s |'
                          % (t['vt'], nsl,
                             ('%08X' % cc['col']) if cc else '-',
                             ('%08X' % cc['td']) if cc else '-',
                             t['mangled'] or '-', t['cls_match'], t['live'],
                             ', '.join('%08X' % s for s in sorted(sites)[:6]),
                             '←' if ('%08X' % vt_i) == v2['D'].get('vt') else ''))
        else:
            tl.append('（口径1 无命中表）')
        tl.append('')
    with open(os.path.join(HERE, 'tables.md'), 'w', encoding='utf-8', newline='') as f:
        f.write('\n'.join(tl) + '\n')

    with open(os.path.join(HERE, 'verify_out.json'), 'w', encoding='utf-8') as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    P('\nwrote bytecheck.tsv / tables.md / verify_out.json  (%s)' % HERE)

    # 日志落盘：先写 verify_log.txt（避免与 shell 重定向到 run_log.txt 时自锁），再复制一份
    log_path = os.path.join(HERE, 'verify_log.txt')
    with open(log_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(out_lines) + '\n')
    try:
        import shutil
        shutil.copyfile(log_path, os.path.join(HERE, 'run_log.txt'))
        print('wrote verify_log.txt + run_log.txt')
    except Exception as ex:
        print('wrote verify_log.txt（run_log.txt 未更新：%s）' % ex)
    return 0


if __name__ == '__main__':
    sys.exit(main())
