# -*- coding: utf-8 -*-
"""
R16_AUDIT_F1_B4 · 独立审计复算器（审计员自带实现，不复用被审目录任何脚本）

只读：gamemd.exe / coverage.tsv / scan_F1_audit.tsv / atlas / 被审 R16_F1_B4 产物
只写：本目录（R16_AUDIT_F1_B4）

判据来源：
  * 卡面 R16-AUDIT-F1.md §4 B 项 8 条（6 项字节 + 2 项附加）
  * R14_COMMON §8.1 错源 ㉓ + §13.5 可执行判据：判 ④ 前必须枚举该虚表**全部**写点，
    并排除 (a) push <fn>; call 0x7C978A（atexit 注册的全局析构器）体内的写；
    (b) 删除析构器体内的写（特征 test byte[esp+X],1 + call 0x7C8B3D + ret 4）。
  * 卡面 §4 C 三种已知坑：同槽多表 / 本 entry 体内也装同表 / 同格并存两条 ④
"""
import io
import json
import os
import re
import sys
import hashlib
import collections
import bisect

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(R14))

EXE = os.path.join(ROOT, 'ra2youli', 'gamemd.exe')
COV = os.path.join(R14, 'COVERAGE', 'coverage.tsv')
PIN = os.path.join(HERE, '_pin_coverage.tsv')
F1AUDIT = os.path.join(R14, 'R16_PROBE_4GAP', 'scan_F1_audit.tsv')
ATLAS = os.path.join(ROOT, 'lead', 'next_re_20261112_r10', 'W130_atlas', 'function_atlas.tsv')
B4 = os.path.join(R14, 'R16_F1_B4')

EXPECT_SHA = '73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476'
IMAGE_BASE = 0x400000
TEXT_LO, TEXT_HI = 0x401000, 0x7E038D
ATEXIT_CALL = 0x7C978A          # push <dtor>; call -> 崩溃注册（atexit）
FREE_CALL = 0x7C8B3D            # 删除析构器释放调用
PRECED = ['00464AC0', '004DE630', '004F42F0']

D4 = '④'
WITNESS = '④ 活表槽位见证'


# ============================================================ PE 底图（自带）
class Image(object):
    def __init__(self, path):
        import pefile
        self.pe = pefile.PE(path, fast_load=True)
        self.base = self.pe.OPTIONAL_HEADER.ImageBase
        self.secs = []
        for s in self.pe.sections:
            nm = s.Name.rstrip(b'\x00').decode('latin-1')
            self.secs.append(dict(name=nm, va=self.base + s.VirtualAddress,
                                  vsize=s.Misc_VirtualSize,
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
        return self.buf[off:e].decode('latin-1')

    def sec_named(self, *names):
        want = set(names)
        return [s for s in self.secs if s['name'] in want]

    def in_image(self, va):
        return va is not None and self.base <= va < self.base + len(self.buf)


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest().upper()


# ============================================================ RTTI（自带实现）
def col_of(img, vt):
    """[vt-4] -> COL(绝对VA)；COL.signature==0；[COL+0xC] -> TD；TD+8 内联 .?A 串。"""
    if not img.in_image(vt - 4):
        return None
    col = img.u32(vt - 4)
    if not img.in_image(col):
        return None
    if img.u32(col) != 0:                     # signature
        return None
    td = img.u32(col + 12)
    if not img.in_image(td):
        return None
    nm = img.cstr(td + 8, 256)                # 内联串（不是指针）
    if not nm or not nm.startswith('.?A'):
        return None
    return dict(col=col, td=td, mangled=nm, off=img.u32(col + 4),
                pchd=img.u32(col + 16))


def vtable_start(img, hit, max_walk=0x1000):
    """从命中位置回走到表起点（取走得最远的合法 COL）。"""
    best = None
    k = 0
    while k * 4 <= max_walk:
        v = hit - k * 4
        if v <= IMAGE_BASE + 4:
            break
        if img.sec_of(v) is None or img.sec_of(v - 4) is None:
            k += 1
            continue
        c = col_of(img, v)
        if c is not None:
            best = (v, c)
        elif best is not None:
            break
        k += 1
    return best


def scan_dd(img, value, secnames=('.rdata', '.data')):
    """段内 4 字节对齐的 dd value 命中点。"""
    hits = []
    pat = value.to_bytes(4, 'little')
    for s in img.sec_named(*secnames):
        d = s['data']
        i = 0
        while True:
            i = d.find(pat, i)
            if i < 0:
                break
            if i % 4 == 0:
                hits.append(s['va'] + i)
            i += 1
    return hits


def demangled_head(mangled):
    """从 .?AV...@@ 里取出**主类名**（模板取外层名，同时给出模板实参串）。"""
    if not mangled or not mangled.startswith('.?A'):
        return None, ''
    s = mangled[4:]
    if s.startswith('?$'):                     # 模板
        s = s[2:]
        head = s.split('@')[0]
        args = s[len(head):]
        return head, args
    return s.split('@')[0], ''


def class_match(row_cls, mangled):
    """行名类 vs RTTI 装饰名：'match' / 'nomatch'。含模板 T_ 伪名兼容。"""
    if not row_cls or not mangled:
        return 'nomatch'
    head, args = demangled_head(mangled)
    if row_cls.startswith('T_'):
        inner = row_cls[2:].rstrip('_')
        parts = [p for p in inner.split('_') if p]
        return 'match' if all(p in mangled for p in parts) else 'nomatch'
    if head == row_cls:
        return 'match'
    return 'match' if row_cls in mangled else 'nomatch'


# ============================================================ capstone 扫描
class Code(object):
    """一次线性反汇编 .text：收 mov [mem],imm32 写点 + call imm32 落点。"""

    def __init__(self, img):
        import capstone
        self.cs = capstone
        t = img.sec_named('.text')[0]
        self.lo = t['va']
        n = min(len(t['data']), t['vsize'] or len(t['data']), TEXT_HI - t['va'])
        self.code = bytes(t['data'][:n])
        self.img = img
        self.writes = collections.defaultdict(list)    # imm -> [(site, disp, asm)]
        self.calls = collections.defaultdict(list)     # target -> [site]
        self.insns = {}                                # site -> (mnemonic, op_str, bytes)
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
            ops = insn.operands
            if insn.mnemonic == 'mov' and len(ops) == 2:
                a, b = ops
                if a.type == X.X86_OP_MEM and b.type == X.X86_OP_IMM:
                    imm = b.imm & 0xFFFFFFFF
                    if IMAGE_BASE <= imm < IMAGE_BASE + 0x800000:
                        if len(self.writes[imm]) < 96:
                            self.writes[imm].append((insn.address, a.mem.disp,
                                                     insn.mnemonic + ' ' + insn.op_str))
                        self.insns[insn.address] = (insn.mnemonic, insn.op_str,
                                                    insn.bytes)
            elif insn.mnemonic == 'call' and len(ops) == 1 and ops[0].type == X.X86_OP_IMM:
                self.calls[ops[0].imm & 0xFFFFFFFF].append(insn.address)

    def writes_of(self, vt):
        return self.writes.get(vt, [])

    def decode_one(self, va):
        md = self.cs.Cs(self.cs.CS_ARCH_X86, self.cs.CS_MODE_32)
        md.detail = True
        buf = bytes(self.img.buf[va - IMAGE_BASE: va - IMAGE_BASE + 16])
        for i in md.disasm(buf, va):
            return i
        return None


# ============================================================ atlas 函数体
def load_atlas():
    sizes = {}
    with io.open(ATLAS, encoding='utf-8-sig') as f:
        for i, ln in enumerate(f):
            if i == 0:
                continue
            c = ln.split('\t')
            if len(c) < 2:
                continue
            try:
                sizes[c[0].strip().upper()] = int(c[1])
            except ValueError:
                pass
    return sizes


def body_ranges(sizes):
    return sorted((int(k, 16), int(k, 16) + v) for k, v in sizes.items() if v)


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


# ============================================================ 写点分类（§13.5）
_ATEXIT_CACHE = {}


def atexit_targets(img, code):
    """一次性算出全部 `push <fn>; call 0x7C978A` 的注册目标集合（缓存）。"""
    key = id(code)
    if key in _ATEXIT_CACHE:
        return _ATEXIT_CACHE[key]
    reg = set()
    for csite in code.calls.get(ATEXIT_CALL, []):
        for back in range(0, 13):
            i = code.decode_one(csite - back)
            if i is None or i.mnemonic != 'push' or not i.op_str:
                continue
            try:
                v = int(i.op_str, 16)
            except ValueError:
                continue
            if TEXT_LO <= v < TEXT_HI:
                reg.add(v)
    _ATEXIT_CACHE[key] = reg
    return reg


def is_atexit_registered(img, code, func):
    """func 是否被 `push <func>; call 0x7C978A` 注册（atexit 析构链）。"""
    if func is None:
        return False
    return func in atexit_targets(img, code)


def dtor_bytes_signature(img, ranges, sizes, func):
    """删除析构器特征：test byte ptr [esp+X],1 + call 0x7C8B3D + ret 4（同一函数体内）。"""
    if func is None:
        return dict(test=False, free=False, ret4=False, verdict=False)
    sz = sizes.get('%08X' % func)
    lo = func
    hi = func + (sz if sz else 0x120)
    raw = bytes(img.buf[lo - IMAGE_BASE: max(0, hi - IMAGE_BASE)])
    has_test = False
    # F6 44 24 xx 01  -> test byte ptr [esp+xx], 1
    for i in range(0, max(0, len(raw) - 5)):
        if raw[i] == 0xF6 and raw[i + 1] == 0x44 and raw[i + 2] == 0x24 and raw[i + 4] == 0x01:
            has_test = True
            break
    has_free = any(lo <= c < hi for c in [])
    # 用 capstone 判 call 0x7C8B3D 是否落在该函数体内
    return dict(test=has_test, ret4=(b'\xC2\x04\x00' in raw),
                free=False, verdict=False, _range=(lo, hi))


def classify_write(img, code, ranges, sizes, site, entry, entry_size, vt):
    """给一个写点定位宿主函数并打标：in_entry_body / atexit / deleting_dtor / ctor_ok。"""
    func = which_body(ranges, site)
    in_entry = (entry <= site < entry + entry_size) if entry_size else (0 <= site - entry < 0x400)
    d = dict(site='%08X' % site, func=('%08X' % func) if func else None,
             in_entry_body=bool(in_entry))
    if func is None:
        d.update(verdict='unknown_func')
        return d
    sz = sizes.get('%08X' % func)
    lo, hi = func, func + (sz if sz else 0x120)
    raw = bytes(img.buf[lo - IMAGE_BASE: max(0, hi - IMAGE_BASE)])
    d['test_bit'] = (b'\xF6\x44\x24' in raw)
    d['ret4'] = (b'\xC2\x04\x00' in raw)
    free_sites = [c for c in code.calls.get(FREE_CALL, []) if lo <= c < hi]
    d['free_call'] = bool(free_sites)
    d['delfree_sig'] = bool(d['test_bit'] and d['free_call'] and d['ret4'])
    d['atexit_reg'] = is_atexit_registered(img, code, func)
    if d['in_entry_body']:
        d['verdict'] = 'entry_body(排除)'
    elif d['delfree_sig']:
        d['verdict'] = 'deleting_dtor(排除)'
    elif d['atexit_reg']:
        d['verdict'] = 'atexit_dtor(排除)'
    else:
        d['verdict'] = 'ctor_type(可用)'
    return d


# ============================================================ 输入装载
def load_cov(path):
    rows = []
    for i, ln in enumerate(io.open(path, encoding='utf-8-sig')):
        if i == 0:
            continue
        c = ln.rstrip('\r\n').split('\t')
        if len(c) < 6:
            continue
        rows.append(c)
    return rows


def derive_76():
    """卡面 §2 四判据独立派生，返回 (76 列表, 阶段计数)。"""
    raw = []
    with io.open(F1AUDIT, encoding='utf-8-sig') as f:
        head = f.readline().rstrip('\r\n').split('\t')
        for ln in f:
            c = ln.rstrip('\r\n').split('\t')
            if len(c) < len(head):
                c += [''] * (len(head) - len(c))
            raw.append(dict(zip(head, c)))
    s0 = len(raw)
    s1 = [r for r in raw if r['same_source'] == 'no']
    s2 = [r for r in s1 if int(r['n_install_decoded'] or 0) >= 1]
    s3 = [r for r in s2 if int(r['n_install_outside_body'] or 0) >= 1]
    s3 = sorted(s3, key=lambda r: int(r['entry'], 16))
    stages = dict(S0=s0, S1=len(s1), S2=len(s2), S3=len(s3))
    return s3, stages, raw


def patch_token(s):
    """ring4_at 里取第一个 8 位十六进制（主站点）。"""
    m = re.search(r'\b([0-9A-Fa-f]{8})\b', s or '')
    return m.group(1).upper() if m else None


# ============================================================ 单行审计
def audit_row(img, code, sizes, ranges, cov_row, pin_row, delta_row, field_row, audit_row):
    entry = delta_row[0].strip().upper()
    e = int(entry, 16)
    name = delta_row[2].strip()
    row_cls = name.rsplit('::', 1)[0] if '::' in name else name
    out = dict(entry=entry, name=name, row_class=row_cls)

    # ---- fields.tsv 声明值
    f = dict(zip(['entry', 'cls', 'slot', 'vt', 'src', 'col', 'off', 'td', 'mangled',
                  'site', 'func', 'status', 'same_source', 'note'], field_row))
    vt, slot, col, off, td, mang, site = (int(f['vt'], 16), int(f['slot']),
                                          int(f['col'], 16), int(f['off']),
                                          int(f['td'], 16), f['mangled'],
                                          int(f['site'], 16))
    out['decl'] = dict(vt='%08X' % vt, slot=slot, col='%08X' % col, off=off,
                       td='%08X' % td, mangled=mang, site='%08X' % site,
                       func=f['func'], status=f['status'], same_source=f['same_source'])

    # ---- 8 项
    i1 = (img.u32(vt + slot * 4) == e)
    i2 = (img.u32(vt - 4) == col)
    i3 = (img.u32(col + 4) == off)
    i4 = (img.u32(col + 12) == td)
    name_at_td = img.cstr(td + 8, 256)
    i5 = (name_at_td == mang)
    # 6：site 处 capstone 解码
    ins = code.decode_one(site)
    asm = (ins.mnemonic + ' ' + ins.op_str) if ins else None
    imm6 = None
    if ins is not None and ins.mnemonic == 'mov':
        X = code.cs.x86
        ops = ins.operands
        if len(ops) == 2 and ops[0].type == X.X86_OP_MEM and ops[1].type == X.X86_OP_IMM:
            imm6 = ops[1].imm & 0xFFFFFFFF
    i6 = (imm6 == vt)
    # 7：装表点所在函数 != entry
    site_func = which_body(ranges, site)
    i7 = (site_func is not None and site_func != e) or (site < e or site >= e + (sizes.get(entry) or 0))
    # 8：TD+8 类名与行名类同类（严格 + 宽松）
    head, targs = demangled_head(name_at_td or '')
    b8_strict = (head == row_cls)
    b8 = (class_match(row_cls, name_at_td or '') == 'match')
    vals = dict(declared=dict(vt='%08X' % vt, slot=slot, col='%08X' % col,
                              off=off, td='%08X' % td, mangled=mang,
                              site='%08X' % site, func=f['func']),
                measured=dict(vt_m4_col=img.u32(vt - 4), col_p4_off=img.u32(col + 4),
                              col_p12_td=img.u32(col + 12), td_p8_name=name_at_td,
                              vt_slot_val=img.u32(vt + slot * 4),
                              site_imm=imm6, site_asm=asm,
                              td_head=head, td_targs=targs))
    out['B'] = dict(B1=i1, B2=i2, B3=i3, B4=i4, B5=i5, B6=i6, B7=i7,
                    B8=b8, B8_strict=b8_strict)
    out['Bvals'] = vals
    out['site_func'] = ('%08X' % site_func) if site_func else None

    # ---- C1 · 同槽多表：枚举含 entry 的全部合法活表
    hits = scan_dd(img, e)
    tables = {}
    unmapped = []
    for h in hits:
        ws = vtable_start(img, h)
        if ws is None:
            unmapped.append(h)
            continue
        v, c = ws
        tables.setdefault(v, dict(vt=v, col=c['col'], td=c['td'],
                                  mangled=c['mangled'], hits=[],
                                  cls_match=class_match(row_cls, c['mangled']),
                                  head=demangled_head(c['mangled'])[0]))
        tables[v]['hits'].append(h)
    # 每张表在哪些槽位持有 entry
    for v, t in tables.items():
        slots = []
        i = 0
        while i * 4 <= 0x400:
            x = img.u32(t['vt'] + i * 4)
            if x is None:
                break
            if x == e:
                slots.append(i)
            if x is not None and x != 0 and not (TEXT_LO <= x < TEXT_HI) and i > 0:
                # 连续非代码指针 -> 表结束（容忍 2 个）
                nxt = img.u32(t['vt'] + (i + 1) * 4)
                if nxt is None or not (TEXT_LO <= nxt < TEXT_HI):
                    break
            i += 1
        t['slots_holding'] = slots
    same_slot = {v: t for v, t in tables.items() if slot in t['slots_holding']}
    same_slot_cls = {v: t for v, t in same_slot.items() if t['cls_match'] == 'match'}
    out['C1'] = dict(n_candidate_tables=len(tables),
                     n_raw_hits=len(hits),
                     raw_hit_is_slot=(len(hits) == 1 and hits[0] == vt + slot * 4),
                     n_unmapped_hits=len(unmapped),
                     unmapped_hits=['%08X' % x for x in unmapped],
                     n_same_slot=len(same_slot),
                     n_same_slot_classmatch=len(same_slot_cls),
                     same_slot=[dict(vt='%08X' % v, col='%08X' % t['col'],
                                     mangled=t['mangled'], head=t['head'],
                                     cls_match=t['cls_match'],
                                     slots=t['slots_holding']) for v, t in
                                sorted(same_slot.items())],
                     chosen_in_same_slot=('%08X' % vt) in {'%08X' % v for v in same_slot},
                     chosen_is_unique_classmatch=(len(same_slot_cls) == 1 and vt in same_slot_cls))
    # 表中所有含 entry 的槽（不限本槽）
    out['C1']['tables'] = [dict(vt='%08X' % t['vt'], col='%08X' % t['col'],
                                mangled=t['mangled'], cls_match=t['cls_match'],
                                slots=t['slots_holding']) for t in
                           sorted(tables.values(), key=lambda x: x['vt'])]

    # ---- C2 · 该虚表全部写点（§13.5 强制枚举）+ 逐点分类
    entry_size = sizes.get(entry) or 0x400
    w = []
    for (wsite, disp, asmtxt) in code.writes_of(vt):
        d = classify_write(img, code, ranges, sizes, wsite, e, entry_size, vt)
        d['asm'] = asmtxt
        d['is_declared'] = (wsite == site)
        w.append(d)
    w.sort(key=lambda d: int(d['site'], 16))
    usable = [d for d in w if d['verdict'] == 'ctor_type(可用)']
    excluded = [d for d in w if d['verdict'] != 'ctor_type(可用)']
    out['C2'] = dict(n_writes=len(w), writes=w,
                     n_usable=len(usable), n_excluded=len(excluded),
                     declared_usable=bool([d for d in w if d['is_declared']
                                           and d['verdict'] == 'ctor_type(可用)']),
                     declared_present=bool([d for d in w if d['is_declared']]))
    # 本 entry 体内是否也装同表（坑 2）
    body_writes = [d for d in w if d['in_entry_body']]
    out['C2b'] = dict(n_in_entry_body=len(body_writes),
                      in_entry_body=body_writes)

    # ---- ring4_at 主站点比对（按 token 集合判定，ring4_at 句常以「ctor <func>」开头）
    ring_txt = audit_row.get('ring4_at') or ''
    ring_addrs = set(re.findall(r'\b[0-9A-Fa-f]{8}\b', ring_txt))
    ring_addrs = {x.upper() for x in ring_addrs}
    tok = patch_token(ring_txt)
    out['ring4'] = dict(token=tok,
                        first_token_is_site=(tok == '%08X' % site) if tok else None,
                        contains_site=('%08X' % site) in ring_addrs,
                        addrs=sorted(ring_addrs),
                        raw=ring_txt)
    # ⑥b：该表全部写点里，声明站点是否为 ring4_at 所述主站点
    out['ring4']['site_is_listed'] = out['ring4']['contains_site']

    # ---- 坑 3 · 同格并存两条 ④（改前 col4 里的 ④ 与新增 ④ 是否同锚点）
    old4 = pin_row[3]
    new4 = delta_row[3]
    out['C3'] = dict(old_n4=old4.count(D4), new_n4=new4.count(D4),
                     old_has_witness=(WITNESS in old4),
                     new_has_witness=(WITNESS in new4))
    # 老 ④ 里出现的 8 位地址（老 ④ 子句锚点）
    segs = re.split(r'(?=' + D4 + r')', old4)
    old4_clauses = [s for s in segs if s.strip().startswith(D4)]
    old4_addrs = set()
    for s in old4_clauses:
        old4_addrs.update(re.findall(r'\b[0-9A-F]{8}\b', s))
    new_site_hex = '%08X' % site
    out['C3'].update(old4_clause_count=len(old4_clauses),
                     old4_addrs=sorted(old4_addrs),
                     new_site_in_old4=(new_site_hex in old4_addrs),
                     same_anchor_two_4=bool(old4_clauses) and any(
                         new_site_hex in set(re.findall(r'\b[0-9A-F]{8}\b', s))
                         for s in old4_clauses))

    # ---- A · 原文保全（对「开卡时盘上实值」= pin，并同时对照现盘 live）
    def a_check(cov_row_x):
        a_other7 = all(delta_row[i] == cov_row_x[i] for i in [0, 1, 2, 4, 5, 6, 7])
        a_prefix = delta_row[3].startswith(cov_row_x[3])
        return dict(other7_same=a_other7, col4_strict_prefix=a_prefix,
                    grade_same=(delta_row[4] == cov_row_x[4]),
                    col4_changed=(delta_row[3] != cov_row_x[3]))
    old4 = pin_row[3]
    new4 = delta_row[3]
    out['A'] = a_check(pin_row)
    out['A']['live'] = a_check(cov_row)
    out['A']['pin_equals_live_for_row'] = (pin_row == cov_row)
    out['A']['ncols'] = len(delta_row)
    a_appended = new4[len(old4):] if out['A']['col4_strict_prefix'] else None
    out['A']['appended_len'] = (len(a_appended) if a_appended is not None else -1)
    out['appended'] = a_appended

    # ---- D · 文本与事实一致
    txt = a_appended or ''
    d_ok = True
    findings = []
    if WITNESS not in txt:
        d_ok = False
        findings.append('缺 ④ 活表槽位见证 骨架')
    exp_site = re.search(r'装表点 ([0-9A-F]{8}) 位于 ([0-9A-F]{8}) 体内', txt)
    d_site = d_func = None
    if exp_site:
        d_site, d_func = exp_site.group(1), exp_site.group(2)
    else:
        d_ok = False
        findings.append('装表点句不可解析')
    exp_vt = re.search(r'vt=([0-9A-F]{8})', txt)
    exp_slot = re.search(r'槽 (\d+) 值=([0-9A-F]{8})', txt)
    exp_col = re.search(r'COL=([0-9A-F]{8}) offset=(\d+)', txt)
    exp_rtti = re.search(r'RTTI=([0-9A-F]{8})→(\.[?]?A[^；;）\s]+)', txt)
    checks = dict(
        site=(d_site == '%08X' % site),
        func=(d_func is not None and d_func == out['site_func']),
        vt=(exp_vt is not None and exp_vt.group(1) == '%08X' % vt),
        slot=(exp_slot is not None and int(exp_slot.group(1)) == slot),
        slot_val=(exp_slot is not None and exp_slot.group(2) == entry),
        col=(exp_col is not None and exp_col.group(1) == '%08X' % col),
        off=(exp_col is not None and int(exp_col.group(2)) == off),
        td=(exp_rtti is not None and exp_rtti.group(1) == '%08X' % td),
        mangled=(exp_rtti is not None and exp_rtti.group(2) == mang),
    )
    for k, v in checks.items():
        if not v:
            d_ok = False
            findings.append('文本 %s 与实测不符' % k)
    d_126 = ('§12.6' in txt)
    d_no124 = ('§12.4' not in txt)
    d_d47 = ('D-47(A)' in txt)
    # 正文里出现的 8 位十六进制 token 必须全部是这 6 个实测值之一
    txt_hex = set(re.findall(r'\b[0-9A-F]{8}\b', txt))
    allowed_hex = {'%08X' % x for x in (vt, slot and e, col, td, site,
                                        site_func if site_func else 0, e)}
    extra_hex = sorted(txt_hex - allowed_hex)
    upg = re.search(r'④升级句：([^（]+)（', txt)
    upg_cls = None
    if upg:
        m = re.match(r'([A-Za-z_0-9]+)::', upg.group(1))
        upg_cls = m.group(1) if m else None
    d_upg_cls = (upg_cls == row_cls)
    if not (d_126 and d_no124 and d_d47 and d_upg_cls):
        d_ok = False
        if not d_126:
            findings.append('缺 §12.6')
        if not d_no124:
            findings.append('出现 §12.4')
        if not d_d47:
            findings.append('缺 D-47(A)')
        if not d_upg_cls:
            findings.append('④升级句类名不一致')
    if extra_hex:
        d_ok = False
        findings.append('正文含未实测的地址 token: %s' % ','.join(extra_hex))
    out['D'] = dict(ok=d_ok, checks=checks, s126=d_126, no124=d_no124, d47=d_d47,
                    upg_class=upg_cls, upg_class_match=d_upg_cls,
                    txt_hex=sorted(txt_hex), extra_hex=extra_hex, findings=findings)

    # ---- 段名骨架（E 用）
    out['skeleton'] = re.sub(r'[0-9A-F]{8}', 'HHHHHHHH', txt)

    # ---- TD+8 内联串自证：u32(TD+8) 不是合法镜像 VA（证明读的是内联字符，不是指针）
    td8_word = img.u32(td + 8)
    out['td8_inline'] = dict(word='%08X' % td8_word if td8_word is not None else None,
                             is_image_va=img.in_image(td8_word) if td8_word else False)

    # ---- 装表点所在函数体内的「装表前 call」（构造器佐证）
    fstart = which_body(ranges, site)
    calls_before = []
    if fstart is not None:
        for tgt, sites in code.calls.items():
            for s in sites:
                if fstart <= s < site:
                    calls_before.append(('%08X' % s, '%08X' % tgt))
    out['ctor_support'] = dict(func=('%08X' % fstart) if fstart else None,
                               calls_before_site=sorted(calls_before)[-4:],
                               n_calls_before=len(calls_before))

    # ---- fields.tsv note 是否逐行标了「改前第4列已含④」
    note = f['note']
    out['note'] = dict(has_marker=('【改前第4列已含④=' in note),
                       says_yes=('改前第4列已含④=是' in note),
                       marker_consistent=(
                           ('改前第4列已含④=是' in note) == (old4.count(D4) > 0)),
                       len=len(note))
    return out


# ============================================================ 主流程
def main():
    log = []

    def P(s=''):
        log.append(str(s))
        print(str(s))

    ok_sha = sha256(EXE)
    P('gamemd.exe sha256 = %s  %s' % (ok_sha, 'OK' if ok_sha == EXPECT_SHA else 'MISMATCH'))
    P('gamemd.exe size   = %d' % os.path.getsize(EXE))
    cov_sha = sha256(COV)
    pin_sha = sha256(PIN)
    P('coverage.tsv sha  = %s (size %d)' % (cov_sha, os.path.getsize(COV)))
    P('pinned   cov sha  = %s (size %d)  same=%s'
      % (pin_sha, os.path.getsize(PIN), cov_sha == pin_sha))

    img = Image(EXE)
    code = Code(img)
    P('capstone: insn=%d skip=%d  stores=%d imm keys  calls keys=%d'
      % (code.n_insn, code.n_skip, len(code.writes), len(code.calls)))
    # 方法保真度锚点自检（独立复算，与 PROBE_802 ANCHORS 对齐）
    for a, n in (('004011C0', 1), ('0054F5C0', 44), ('007DC720', 437)):
        got = len(code.calls.get(int(a, 16), []))
        P('  anchor direct %s: got=%d expect=%d %s' % (a, got, n, 'OK' if got == n else 'DIFF'))

    sizes = load_atlas()
    ranges = body_ranges(sizes)
    P('atlas funcs=%d' % len(sizes))

    # ---- 派生集合
    base76, stages, raw = derive_76()
    P('derive stages: %s ; S3=%d (expect 76)' % (stages, len(base76)))
    b4 = base76[54:72]
    P('slice[54:72] -> %d rows' % len(b4))
    b4_entries = [r['entry'].upper() for r in b4]
    P('B4 entries: ' + ' '.join(b4_entries))

    # ---- 读被审产物
    def tsv(path):
        out = []
        with io.open(path, encoding='utf-8-sig') as f:
            for i, ln in enumerate(f):
                out.append(ln.rstrip('\r\n').split('\t'))
        return out
    delta_all = tsv(os.path.join(B4, 'delta.tsv'))
    dhead, delta = delta_all[0], delta_all[1:]
    P('delta.tsv: header=%d cols, rows=%d' % (len(dhead), len(delta)))
    fields_all = tsv(os.path.join(B4, 'fields.tsv'))
    fhead, fields = fields_all[0], fields_all[1:]
    P('fields.tsv: header=%d cols, rows=%d' % (len(fhead), len(fields)))

    cov = {r[0].strip().upper(): r for r in load_cov(COV)}
    audit = {}
    with io.open(F1AUDIT, encoding='utf-8-sig') as f:
        h = f.readline().rstrip('\r\n').split('\t')
        for ln in f:
            c = ln.rstrip('\r\n').split('\t')
            if len(c) < len(h):
                c += [''] * (len(h) - len(c))
            d = dict(zip(h, c))
            audit[d['entry'].upper()] = d

    # ---- 结构检查
    struct = dict(
        delta_ncols_all=all(len(r) == 8 for r in delta),
        fields_ncols_all=all(len(r) == len(fhead) for r in fields),
        delta_entries_match_slice=([r[0].strip().upper() for r in delta] == b4_entries),
        fields_entries_match_slice=([r[0].strip().upper() for r in fields] == b4_entries),
        delta_sorted=([r[0].strip().upper() for r in delta]
                      == sorted([r[0].strip().upper() for r in delta])),
        entries_in_76=all(r[0].strip().upper() in {x['entry'].upper() for x in base76}
                          for r in delta),
        no_dup=len({r[0].strip().upper() for r in delta}) == len(delta),
        fhdr14=len(fhead) == 14,
    )
    P('struct: %s' % json.dumps(struct, ensure_ascii=False))

    # B1/B2/B3 交集（硬要求）
    used = set()
    for b in ('B1', 'B2', 'B3'):
        p = os.path.join(R14, 'R16_F1_%s' % b, 'fields.tsv')
        if os.path.isfile(p):
            ent = {r[0].strip().upper() for r in tsv(p)[1:]}
            used |= ent
            P('  intersect %s: %d rows, overlap_with_B4=%d'
              % (b, len(ent), len(ent & set(b4_entries))))

    fmap = {r[0].strip().upper(): r for r in fields}
    pinmap = {r[0].strip().upper(): r for r in load_cov(PIN)}
    # 并发并表：pin 与 live 的差异（只报，不判）
    live_changed = [e for e in cov if e in pinmap and cov[e] != pinmap[e]]
    P('concurrent merge: pin sha %s (%d B) -> live sha %s (%d B); changed rows=%d'
      % (pin_sha, os.path.getsize(PIN), cov_sha, os.path.getsize(COV), len(live_changed)))
    P('  changed entries: ' + ' '.join(sorted(live_changed)))
    P('  any of the 18 B4 rows changed: %s'
      % bool(set(live_changed) & set(b4_entries)))
    results = []
    for dr in delta:
        ent = dr[0].strip().upper()
        if ent not in cov:
            P('MISSING in coverage: %s' % ent)
            continue
        results.append(audit_row(img, code, sizes, ranges, cov[ent], pinmap[ent],
                                 dr, fmap[ent], audit.get(ent, {})))
    P('audited rows: %d' % len(results))

    # ---- F · 反抄袭
    texts = [r['appended'] or '' for r in results]
    norm = [re.sub(r'[0-9A-F]{8}', 'ENTRY', t) for t in texts]
    f_check = dict(n=len(texts), uniq_full=len(set(texts)),
                   uniq_norm=len(set(norm)),
                   dup_full=[i for i, t in enumerate(texts) if texts.count(t) > 1],
                   dup_norm=[i for i, t in enumerate(norm) if norm.count(t) > 1])
    P('F anti-plagiarism: full=%d/%d norm=%d/%d' % (f_check['uniq_full'], len(texts),
                                                    f_check['uniq_norm'], len(norm)))

    # ---- E · 骨架与先例比对（必须先把类名/装饰名归一，否则每行天然不同）
    def skel(s, cls=None):
        s = re.sub(r'\.\?A[^；;）\s]+', 'MGL', s)
        if cls:
            s = s.replace(cls, 'CLS')
        s = re.sub(r'[0-9A-F]{8}', 'H8', s)
        s = re.sub(r'\d+', 'N', s)
        s = re.sub(r'CLS::slotN', 'CLS::SLOT', s)
        s = re.sub(r'CLS::ctor', 'CLS::CTORNAME', s)
        return s
    prec_skel = {}
    for e in PRECED:
        c4 = cov[e][3]
        i = c4.find(WITNESS)
        pc = cov[e][2].rsplit('::', 1)[0]
        prec_skel[e] = skel(c4[i:], pc) if i >= 0 else None
    mine = [skel(t[t.find(WITNESS):] if WITNESS in t else t, r['row_class'])
            for t, r in zip(texts, results)]
    e_match = {e: mine.count(v) if v else 0 for e, v in prec_skel.items()}
    # 真正的格式先例是「已并表的 R16_SLOTN 各行」（它们带 D-47 披露后缀）
    merged_skel = collections.Counter()
    merged_rows = 0
    for e, c in cov.items():
        c4 = c[3]
        if WITNESS in c4 and 'D-47(A) 裁决' in c4:
            i = c4.find(WITNESS)
            merged_skel[skel(c4[i:], c[2].rsplit('::', 1)[0])] += 1
            merged_rows += 1
    mine_hit = sum(1 for s in mine if s in merged_skel)
    P('E skeleton vs merged-SLOTN (%d rows, %d distinct): %d/%d B4 rows match a merged skeleton'
      % (merged_rows, len(merged_skel), mine_hit, len(mine)))
    for s, k in merged_skel.most_common(3):
        P('   merged skel x%-3d %s' % (k, s[:150]))
    P('E skeleton vs old 3 precedents (无 D-47 后缀): %s' % json.dumps(e_match))
    P('E B4 distinct skeletons: %d / %d' % (len(set(mine)), len(mine)))
    for s in sorted(set(mine)):
        if mine.count(s) < len(mine):
            P('   B4 skel x%-3d %s' % (mine.count(s), s[:150]))
    # 逐字段齐全性
    need_tokens = ['④ 活表槽位见证：', '（vt=', '，槽 ', ' 值=', '，COL=', ' offset=',
                   '，RTTI=', '；装表点 ', ' 位于 ', ' 体内，entry 体外）',
                   ' ④升级句：', '④ 表属类与行名类一致', '无归属歧义）',
                   'D-47(A) 裁决', '§12.6']
    field_ok = 0
    for t in texts:
        if all(k in t for k in need_tokens):
            field_ok += 1
    P('E field completeness: %d/%d' % (field_ok, len(texts)))
    # 见证头是否按先例写成 Class::slotN（而非行名里的 ::ctor）
    head_form = [re.search(r'④ 活表槽位见证：([A-Za-z_0-9]+::[A-Za-z_0-9]+)', t) for t in texts]
    heads = [m.group(1) for m in head_form if m]
    slot_named = sum(1 for h in heads if re.search(r'::slot\d+$', h))
    ctor_named = sum(1 for h in heads if re.search(r'::ctor$', h))
    P('E witness head form: Class::slotN=%d  Class::ctor=%d  (heads parsed %d/%d)'
      % (slot_named, ctor_named, len(heads), len(texts)))

    # ---- 汇总
    n = len(results)
    def cnt(pred):
        return sum(1 for r in results if pred(r))
    summary = dict(
        n=n,
        B=dict(
            B1=cnt(lambda r: r['B']['B1']), B2=cnt(lambda r: r['B']['B2']),
            B3=cnt(lambda r: r['B']['B3']), B4=cnt(lambda r: r['B']['B4']),
            B5=cnt(lambda r: r['B']['B5']), B6=cnt(lambda r: r['B']['B6']),
            B7=cnt(lambda r: r['B']['B7']), B8=cnt(lambda r: r['B']['B8']),
            B8_strict=cnt(lambda r: r['B']['B8_strict']),
            all8=cnt(lambda r: all(r['B'][k] for k in
                                   ('B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8'))),
        ),
        A=dict(other7=cnt(lambda r: r['A']['other7_same']),
               prefix=cnt(lambda r: r['A']['col4_strict_prefix']),
               grade=cnt(lambda r: r['A']['grade_same'])),
        D=dict(ok=cnt(lambda r: r['D']['ok']), s126=cnt(lambda r: r['D']['s126']),
               no124=cnt(lambda r: r['D']['no124']), d47=cnt(lambda r: r['D']['d47'])),
        C1=dict(unique_classmatch=cnt(lambda r: r['C1']['chosen_is_unique_classmatch']),
                multi_same_slot=cnt(lambda r: r['C1']['n_same_slot'] > 1),
                multi_classmatch=cnt(lambda r: r['C1']['n_same_slot_classmatch'] > 1),
                one_table=cnt(lambda r: r['C1']['n_candidate_tables'] == 1),
                raw_hit_is_slot=cnt(lambda r: r['C1']['raw_hit_is_slot']),
                unmapped_hits=cnt(lambda r: r['C1']['n_unmapped_hits'] > 0)),
        C2=dict(declared_usable=cnt(lambda r: r['C2']['declared_usable']),
                declared_listed=cnt(lambda r: r['C2']['declared_present']),
                entry_body_self_install=cnt(lambda r: r['C2b']['n_in_entry_body'] > 0)),
        C3=dict(old_had_4=cnt(lambda r: r['C3']['old_n4'] > 0),
                same_anchor=cnt(lambda r: r['C3']['same_anchor_two_4'])),
        ring4_contains=cnt(lambda r: r['ring4']['contains_site']),
        ring4_first=cnt(lambda r: r['ring4']['first_token_is_site'] is True),
        note_marker=cnt(lambda r: r['note']['marker_consistent']),
        struct=struct,
    )
    P('SUMMARY: ' + json.dumps(summary, ensure_ascii=False, indent=1))

    # ---- 4 行「析构/就地构造写点已排除」专项
    inbody_rows = [r for r in results if r['C2b']['n_in_entry_body'] > 0]
    P('')
    P('== trap 2 · 本 entry 体内也装同表: %d/%d rows' % (len(inbody_rows), len(results)))
    for r in inbody_rows:
        d = r['C2b']['in_entry_body'][0]
        P('   %s %-28s in-body write %s func=%s delfree=%s  ->  declared %s usable=%s'
          % (r['entry'], r['name'], d['site'], d['func'], d.get('delfree_sig'),
             r['decl']['site'], r['C2']['declared_usable']))
    flagged4 = [r for r in results
                if r['ring4']['raw'] and ('已排除' in r['ring4']['raw'] or '排除' in r['ring4']['raw'])]
    P('== ring4_at 显式标注「写点已排除」的行: %d' % len(flagged4))
    for r in flagged4:
        P('   %s %-28s declared=%s in_entry_body=%s'
          % (r['entry'], r['name'], r['decl']['site'], r['C2b']['n_in_entry_body']))

    # ---- 收尾：coverage.tsv 仍未被本审计改动
    cov_after = sha256(COV)
    P('coverage.tsv after run: %s  unchanged=%s' % (cov_after, cov_after == cov_sha))
    summary['cov_unchanged'] = (cov_after == cov_sha)

    # ---- 落盘
    json.dump(dict(summary=summary, f=f_check, e=e_match,
                   stages=stages, b4_entries=b4_entries,
                   cov_sha=cov_sha, exe_sha=ok_sha,
                   rows=results),
              io.open(os.path.join(HERE, 'verify_out.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1, default=str)

    # bytecheck.tsv
    cols = ['row', 'entry', 'name', 'name_cls', 'slot', 'vt',
            'B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B8_strict', 'ALL8',
            'site', 'site_asm', 'site_func', 'TD', 'COL', 'mangled',
            'A_other7', 'A_col4_prefix', 'A_grade',
            'D_ok', 'D_126', 'D_no124', 'D_d47', 'D_upg_cls',
            'C1_n_tables', 'C1_n_raw_hits', 'C1_n_unmapped', 'C1_n_same_slot',
            'C1_n_same_slot_cls', 'C1_unique_cls',
            'C2_n_writes', 'C2_n_usable', 'C2_declared_usable',
            'C2b_in_entry_body', 'ring4_contains_site', 'ring4_first_is_site',
            'C3_old_n4', 'C3_new_n4', 'C3_same_anchor', 'note_marker_ok']
    with io.open(os.path.join(HERE, 'bytecheck.tsv'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('\t'.join(cols) + '\n')
        for i, r in enumerate(results, 1):
            d = r['decl']
            b = r['B']
            row = [str(i), r['entry'], r['name'], r['row_class'], str(d['slot']), d['vt'],
                   *[('T' if b[k] else 'F') for k in
                     ('B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B8_strict')],
                   ('T' if all(b[k] for k in ('B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8')) else 'F'),
                   d['site'], r['Bvals']['measured']['site_asm'] or '',
                   r['site_func'] or '', d['td'], d['col'], d['mangled'],
                   'T' if r['A']['other7_same'] else 'F',
                   'T' if r['A']['col4_strict_prefix'] else 'F',
                   'T' if r['A']['grade_same'] else 'F',
                   'T' if r['D']['ok'] else 'F',
                   'T' if r['D']['s126'] else 'F',
                   'T' if r['D']['no124'] else 'F',
                   'T' if r['D']['d47'] else 'F',
                   'T' if r['D']['upg_class_match'] else 'F',
                   str(r['C1']['n_candidate_tables']),
                   str(r['C1']['n_raw_hits']),
                   str(r['C1']['n_unmapped_hits']),
                   str(r['C1']['n_same_slot']),
                   str(r['C1']['n_same_slot_classmatch']),
                   'T' if r['C1']['chosen_is_unique_classmatch'] else 'F',
                   str(r['C2']['n_writes']), str(r['C2']['n_usable']),
                   'T' if r['C2']['declared_usable'] else 'F',
                   str(r['C2b']['n_in_entry_body']),
                   'T' if r['ring4']['contains_site'] else 'F',
                   'T' if r['ring4']['first_token_is_site'] else 'F',
                   str(r['C3']['old_n4']), str(r['C3']['new_n4']),
                   'T' if r['C3']['same_anchor_two_4'] else 'F',
                   'T' if r['note']['marker_consistent'] else 'F']
            f.write('\t'.join(row) + '\n')
    P('wrote verify_out.json / bytecheck.tsv')

    io.open(os.path.join(HERE, 'run_log.txt'), 'w', encoding='utf-8').write('\n'.join(log))


if __name__ == '__main__':
    main()
