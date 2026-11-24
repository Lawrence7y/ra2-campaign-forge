# -*- coding: utf-8 -*-
"""
R16-PROBE-4FINAL —— 静态 ④ 线路终局度量（度量卡：不判 grade、不写 ④ 正文）。

把「当前完全无 ④ 的那批 [已证] 行」（卡面约 1,279 行，本脚本实测为准）切成互斥四类：

  D1  可派生-槽位      entry 被某张活表在某个槽持有（u32(vt+slot*4)==entry），
                        且该表有装表点、且至少一个装表点落在 entry **体外**。
  D2  可派生-direct    无 D1，但存在 E8 direct call 站点（site+5+rel32==entry），
                        站点经 atlas 函数体包含性校验、且不是自环/体内。
  D3  不可派生-有表但同源 无 D1/D2，但 entry 被某张可解出的表持有 ⇒ 该表的槽
                        既定不了「别人装的活表」（D-47(A) 让位形态），
                        也就只能与 ② 同源。
  D4  结构性无          无表持有、无 direct 站点（无任何使用见证线索）。

优先级 D1 > D2 > D3 > D4（保证互斥），重叠数另列。

口径全部写死、自足实现（不 import 别的卡的扫描器，便于复跑与审计）：
  · 镜像：pefile 只读；ImageBase 0x400000；.text=[0x401000,0x7E038D)。
  · 表：.rdata/.data 里 4 字节对齐、`vt-4` 是合法 RTTI COL（sig==0、TD+8 是 `.?A`）。
  · 表长：从 vt 起连续 `0 或 .text 指针` 的槽数，遇到下一张表的起点即止（stop set）。
  · 活表：有 >=1 个 `mov [mem], imm32==vt` 装表点（宽口径，与 R16_DESIGN_D48 一致）。
  · 装表点在 entry 体外：site 不在 [entry, entry+atlas_size)。
  · direct：capstone 一次线性反汇编 .text（skipdata），`call imm32` 且 target==entry；
    站点必须落在 atlas 已知函数体内（指令边界代理）且不在 entry 自己体内。

只读纪律：sys.dont_write_bytecode=True；只写本目录；gamemd.exe 只 open('rb')。
复跑：
    python final.py              # 全流程：分类 + 交叉核对 + 抽样证据
    python final.py --repin      # 重新快照 coverage.tsv（默认沿用已有快照，保证复跑同数）
"""
import sys

sys.dont_write_bytecode = True                   # 只读纪律：连 __pycache__ 都不落

import os
import io
import re
import json
import time
import hashlib
import bisect
import collections

HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
COV_LIVE = os.path.join(R14, 'COVERAGE', 'coverage.tsv')
PIN = os.path.join(HERE, '_pin_coverage.tsv')
EXE = os.path.join(os.path.dirname(os.path.dirname(R14)), 'ra2youli', 'gamemd.exe')
ATLAS = os.path.join(os.path.dirname(os.path.dirname(R14)), 'lead',
                     'next_re_20261112_r10', 'W130_atlas', 'function_atlas.tsv')
YRPP = os.path.join(os.path.dirname(os.path.dirname(R14)), 'YRpp')
GAP = os.path.join(R14, 'R16_PROBE_4GAP')       # 交叉核对用（只读）

EXPECT_SHA = '73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476'
IMAGE_BASE = 0x400000
TEXT_LO, TEXT_HI = 0x401000, 0x7E038D
PROVED = '[已证]'
RING4 = '④'
RING4_SLOT = '④ 活表槽位见证'


# ------------------------------------------------------------------ 基础
def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest().upper()


class Image(object):
    def __init__(self, path):
        import pefile
        self.pe = pefile.PE(path, fast_load=True)
        self.base = self.pe.OPTIONAL_HEADER.ImageBase
        self.secs = []
        for s in self.pe.sections:
            nm = s.Name.rstrip(b'\x00').decode('latin-1')
            self.secs.append(dict(name=nm, va=self.base + s.VirtualAddress,
                                  vsize=s.Misc_VirtualSize, rsize=s.SizeOfRawData,
                                  data=s.get_data()))
        end = max(s['va'] + max(s['vsize'], s['rsize']) for s in self.secs)
        self.buf = bytearray(end - self.base + 16)
        for s in self.secs:
            off = s['va'] - self.base
            d = s['data']
            self.buf[off:off + len(d)] = d

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
        return bytes(self.buf[off:e]).decode('latin-1', 'replace')

    def section(self, name):
        for s in self.secs:
            if s['name'] == name:
                return s
        return None

    def in_image(self, va):
        return va is not None and IMAGE_BASE <= va < IMAGE_BASE + len(self.buf)


def col_of(img, vt):
    """vt-4 是合法 RTTI COL 才认作表起点。口径照 R16_COMMON §13.1（绝对 VA、TD+8 内联名）。"""
    col = img.u32(vt - 4)
    if not img.in_image(col):
        return None
    if img.u32(col) != 0:                        # signature 必须为 0
        return None
    td = img.u32(col + 12)
    if not img.in_image(td):
        return None
    nm = img.cstr(td + 8, 256)
    if not nm or not nm.startswith('.?A'):
        return None
    return dict(col=col, name=nm)


class Text(object):
    """一次反汇编 .text：direct call 落点、装表点、call[mem] 站点。"""

    def __init__(self, img):
        import capstone
        from capstone import x86 as X
        t = img.section('.text')
        n = min(len(t['data']), t['vsize'] or len(t['data']), TEXT_HI - t['va'])
        self.code = bytes(t['data'][:n])
        self.lo = t['va']
        self.hi = self.lo + len(self.code)
        self.direct = collections.Counter()
        self.direct_sites = collections.defaultdict(list)
        self.stores = collections.defaultdict(list)
        self.installs_insn = {}                 # site -> disasm text
        self.direct_insn = {}                   # site -> disasm text
        self.callmem = 0
        self.n_insn = 0
        self.n_skip = 0
        md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
        md.detail = True
        md.skipdata = True
        for insn in md.disasm(self.code, self.lo):
            if insn.id == 0:
                self.n_skip += 1
                continue
            self.n_insn += 1
            ops = insn.operands
            mg = insn.mnemonic
            if mg == 'call' and ops:
                o = ops[0]
                if o.type == X.X86_OP_IMM:
                    tgt = o.imm & 0xFFFFFFFF
                    self.direct[tgt] += 1
                    if len(self.direct_sites[tgt]) < 64:
                        self.direct_sites[tgt].append(insn.address)
                        self.direct_insn[insn.address] = '%s %s' % (mg, insn.op_str)
                elif o.type == X.X86_OP_MEM:
                    self.callmem += 1
            elif mg == 'mov' and len(ops) == 2:
                a, b = ops
                if a.type == X.X86_OP_MEM and b.type == X.X86_OP_IMM:
                    imm = b.imm & 0xFFFFFFFF
                    if IMAGE_BASE <= imm < IMAGE_BASE + 0x800000:
                        if len(self.stores[imm]) < 64:
                            self.stores[imm].append((insn.address, a.mem.disp))
                            self.installs_insn[insn.address] = '%s %s' % (mg, insn.op_str)

    def insn_at(self, va):
        import capstone
        o = va - self.lo
        if o < 0 or o >= len(self.code):
            return '?'
        md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
        md.detail = True
        for insn in md.disasm(self.code[o:o + 16], va):
            return '%s %s  [%s]' % (insn.mnemonic, insn.op_str,
                                    insn.bytes.hex(' '))
        return '?'


# ------------------------------------------------------------------ 输入
def load_coverage(path):
    rows = []
    with io.open(path, encoding='utf-8-sig') as f:
        for i, ln in enumerate(f):
            if i == 0:                            # 表头是逗号分隔（已知坑）
                continue
            c = ln.rstrip('\r\n').split('\t')
            if len(c) < 8:
                continue
            rows.append(dict(entry=c[0].strip().upper(), subsystem=c[1].strip(),
                             name=c[2], sem=c[3], grade=c[4], ev=c[5],
                             ns=c[6], conflict=c[7]))
    return rows


def load_atlas():
    out = {}
    with io.open(ATLAS, encoding='utf-8-sig') as f:
        for i, ln in enumerate(f):
            if i == 0:
                continue
            c = ln.rstrip('\r\n').split('\t')
            if len(c) < 2:
                continue
            try:
                out[int(c[0].strip(), 16)] = int(c[1])
            except ValueError:
                continue
    return out


def load_yrpp_idents():
    """YRpp 源码标识符集合：判 ② 是否另有独立名字源（§8.6 条 2 通道 2）。"""
    idx = set()
    if not os.path.isdir(YRPP):
        return idx
    for dp, _dn, fn in os.walk(YRPP):
        for f in fn:
            if not f.lower().endswith(('.h', '.hpp', '.cpp', '.c')):
                continue
            try:
                s = io.open(os.path.join(dp, f), encoding='utf-8',
                            errors='ignore').read()
            except OSError:
                continue
            idx.update(re.findall(r'[A-Za-z_][A-Za-z0-9_]*', s))
    return idx


def yrpp_anchor(name, idx):
    if not idx or '::' not in name:
        return False, False
    cls, meth = name.rsplit('::', 1)
    cls_ok = (cls in idx) or ((cls + 'Class') in idx)
    return cls_ok, bool(meth) and (meth in idx)


def class_from_name(name):
    return name.rsplit('::', 1)[0] if '::' in name else None


def col_match_of(name_cls, mangled):
    """行名类 vs RTTI 装饰名。模板名按「所有标识符都出现在装饰名里」判，
    否则按子串判（照 PROBE_802 的 col_name_match，避免模板名一律误判 nomatch）。"""
    if not name_cls or not mangled:
        return None
    if '<' in name_cls:
        base = name_cls.split('<', 1)[0]
        toks = re.findall(r'[A-Za-z_][A-Za-z0-9_]*', name_cls)
        toks = [t for t in toks if t and t != base] + [base]
        return all(t in mangled for t in toks)
    if name_cls.startswith('T_'):
        parts = [p for p in name_cls[2:].rstrip('_').split('_') if p]
        return all(p in mangled for p in parts)
    return name_cls in mangled


def load_surface():
    """只读复用 D47_SURFACE 的 classify()（不重写分类器，不 import 其 probe 扫描器）。"""
    d47 = os.path.join(R14, 'D47_SURFACE')
    if not os.path.isfile(os.path.join(d47, 'surface.py')):
        return None, None, None
    sys.path.insert(0, d47)
    try:
        import surface as S
        return S, S.load_audit_records(), S.load_census_trace()
    except Exception as exc:                        # 分类器不可用不阻塞主测量
        print('!! surface classifier unavailable: %r' % (exc,))
        return None, None, None


# ------------------------------------------------------------------ 表枚举
def enumerate_tables(img):
    tabs = {}
    for s in img.secs:
        if s['name'] not in ('.rdata', '.data'):
            continue
        d = s['data']
        for k in range(len(d) // 4):
            va = s['va'] + k * 4
            c = col_of(img, va)
            if c:
                tabs[va] = dict(vt=va, col=c['col'], cls=c['name'],
                                section=s['name'], n_slots=0, slots={})
    return tabs


def table_len(img, vt, stop, max_slots=4000):
    n = 0
    while n < max_slots:
        va = vt + n * 4
        if va != vt and va in stop:
            break
        v = img.u32(va)
        if v is None:
            break
        if v == 0 or TEXT_LO <= v < TEXT_HI:
            n += 1
            continue
        break
    return n


def body_of(sizes, starts, va):
    i = bisect.bisect_right(starts, va) - 1
    if i < 0:
        return None
    s = starts[i]
    if s <= va < s + sizes[i]:
        return s
    return None


# ------------------------------------------------------------------ 主流程
def main():
    t0 = time.time()
    repin = '--repin' in sys.argv
    if os.path.isfile(PIN) and not repin:
        cov = PIN
        pinned = True
    else:
        # 快照 live → 本目录（避免并表期间数字漂移，且保证复跑同数）
        with open(COV_LIVE, 'rb') as fi, open(PIN, 'wb') as fo:
            fo.write(fi.read())
        cov = PIN
        pinned = False

    exe_sha = sha256(EXE)
    print('gamemd.exe sha256 : %s  %s' % (exe_sha, 'OK' if exe_sha == EXPECT_SHA else 'MISMATCH'))
    cov_sha = sha256(cov)
    live_sha = sha256(COV_LIVE)
    print('coverage used     : %s' % os.path.basename(cov))
    print('  sha256          : %s' % cov_sha)
    print('  live now        : %s  %s' % (live_sha,
                                          'same' if live_sha == cov_sha else 'DIFFERS(盘在动)'))

    rows = load_coverage(cov)
    proved = [r for r in rows if r['grade'] == PROVED]
    no4 = [r for r in proved if RING4 not in r['sem']]
    ring4_any = [r for r in proved if RING4 in r['sem']]
    ring4_slot = [r for r in proved if RING4_SLOT in r['sem']]
    print('rows %d / proved %d / ring4_any %d / ring4_slot %d / proved_no4 %d'
          % (len(rows), len(proved), len(ring4_any), len(ring4_slot), len(no4)))

    # ---------------- 镜像
    img = Image(EXE)
    text = Text(img)
    print('.text insns %d (skip %d) [%08X,%08X) ; call[mem] %d'
          % (text.n_insn, text.n_skip, text.lo, text.hi, text.callmem))
    atlas = load_atlas()
    starts = sorted(atlas)
    sizes = [atlas[s] for s in starts]

    tabs = enumerate_tables(img)
    stop = set(tabs)
    for vt in tabs:
        tabs[vt]['n_slots'] = table_len(img, vt, stop)
    n_slots = sum(t['n_slots'] for t in tabs.values())
    print('tables %d / slots %d ; install-imm targets %d (of which table) %d'
          % (len(tabs), n_slots, len(text.stores),
             sum(1 for imm in text.stores if imm in tabs)))

    # 装表点：表 → [(site, disp)]
    installs = {}
    for vt in tabs:
        if text.stores.get(vt):
            installs[vt] = list(text.stores[vt])
    print('live tables (>=1 install site) %d ; install sites %d'
          % (len(installs), sum(len(v) for v in installs.values())))

    # entry → [(vt, slot)]
    holdings = collections.defaultdict(list)
    for vt, t in tabs.items():
        for k in range(t['n_slots']):
            v = img.u32(vt + k * 4)
            if v is None or not (TEXT_LO <= v < TEXT_HI):
                continue
            holdings[v].append((vt, k))
    print('entries held by some table: %d' % len(holdings))

    # ---------------- 逐行分类
    yrpp = load_yrpp_idents()
    print('YRpp idents %d' % len(yrpp))

    def own_body(e):
        sz = atlas.get(e)
        return (e, e + sz) if sz else None

    def in_own(site, body):
        return bool(body) and body[0] <= site < body[1]

    recs = []
    for r in no4:
        e = int(r['entry'], 16)
        body = own_body(e)
        hold = holdings.get(e, [])
        hold_live = [(vt, k) for vt, k in hold if vt in installs]
        ext = []
        selfs = []
        for vt, k in hold_live:
            for site, _disp in installs[vt]:
                if in_own(site, body):
                    selfs.append((vt, k, site))
                else:
                    ext.append((vt, k, site))
        # 表级：被任何活表持有（不论体内外）
        held_live_any = bool(hold_live)
        # direct（校验后）
        dsites = text.direct_sites.get(e, [])
        dver = []
        for s in dsites:
            if body_of(sizes, starts, s) is None:
                continue                      # 不在任何已知函数体内 ⇒ 指令边界存疑
            if in_own(s, body):
                continue                      # 自环/体内调用
            dver.append(s)
        # dd 命中（未解出表起点也算线索）
        dd_hits = 0
        pat = e.to_bytes(4, 'little')
        for sec in (img.section('.rdata'), img.section('.data')):
            if not sec:
                continue
            d = sec['data']
            i = d.find(pat)
            while i >= 0:
                if i % 4 == 0:
                    dd_hits += 1
                i = d.find(pat, i + 1)

        if ext:
            cls = 'D1'
            vt, k, site = ext[0]
        elif dver:
            cls = 'D2'
            vt, k, site = -1, -1, -1
        elif hold:
            cls = 'D3'
            vt, k = hold[0]
            site = installs.get(vt, [(None, None)])[0][0] if vt in installs else None
        else:
            cls = 'D4'
            vt, k, site = -1, -1, -1

        cls_ok, meth_ok = yrpp_anchor(r['name'], yrpp)
        col_names = [tabs[v]['cls'] for v, _ in hold] if hold else []
        name_cls = class_from_name(r['name'])
        col_match = None
        if col_names and name_cls:
            res = [col_match_of(name_cls, c) for c in col_names]
            col_match = True if True in res else (None if all(x is None for x in res) else False)

        notes = []
        if cls == 'D1':
            notes.append('ext_inst@%08X' % ext[0][2])
            if selfs:
                notes.append('also_self_inst')
            if len(set(v for v, _k, _s in ext)) > 1:
                notes.append('multi_table')
        elif cls == 'D2':
            notes.append('direct_v=%d' % len(dver))
        elif cls == 'D3':
            if vt in installs:
                notes.append('self_inst_only@%08X' % installs[vt][0][0])
            else:
                notes.append('dead_table')
        elif cls == 'D4':
            notes.append('dd_hits=%d' % dd_hits if dd_hits else 'no_dd_no_direct')
        if cls != 'D1' and selfs and cls != 'D3':
            notes.append('self_inst@%08X' % selfs[0][2])
        if '[未证]' in r['sem']:
            notes.append('sem[未证]')
        if col_match is False:
            notes.append('col_nomatch')
        if cls in ('D1', 'D2') and not (cls_ok and meth_ok):
            notes.append('no_yrpp_anchor')

        recs.append(dict(entry=r['entry'], subsystem=r['subsystem'], name=r['name'],
                         grade=r['grade'], cls=cls, vt=vt, slot=k, site=site,
                         direct=dver, dd_hits=dd_hits, sem=r['sem'],
                         hold=hold, hold_live=hold_live, ext=ext, selfs=selfs,
                         notes=notes, anchored=(cls_ok and meth_ok),
                         sem_unproved=('[未证]' in r['sem']),
                         col_names=col_names, col_match=col_match,
                         dec_col_match=(col_match_of(class_from_name(r['name']),
                                                     tabs[vt]['cls'])
                                        if vt > 0 else None),
                         held_live_any=held_live_any, body=body))

    cnt = collections.Counter(r['cls'] for r in recs)
    evpath = {r['entry']: r['ev'] for r in rows}

    # ---- 来源类别（M78 口径，只读复用 D47_SURFACE.classify）
    S, audit, trace = load_surface()
    for rec, r in zip(recs, no4):
        if S is None:
            rec['src'] = '-'
            continue
        d = S.classify(r, audit, trace)
        rec['src'] = d['form'] if d['form'] != 'F4' else 'F4:' + d['reason']
        rec['band'] = d.get('band', '-')
        rec['same_source'] = d.get('same_source', '') or '-'
    print('\n=== 四类（互斥，分母 %d）===' % len(recs))
    for k in ('D1', 'D2', 'D3', 'D4'):
        print('  %s %5d  (%.1f%%)' % (k, cnt[k], 100.0 * cnt[k] / len(recs) if recs else 0))

    # 重叠（供诚实说明分类优先级影响）
    both_d1d2 = sum(1 for r in recs if r['ext'] and r['direct'])
    d2_with_slot = sum(1 for r in recs if r['cls'] == 'D2' and r['hold_live'])
    d2_with_hold = sum(1 for r in recs if r['cls'] == 'D2' and r['hold'])
    print('  重叠：D1∩有direct %d ; 归 D2 但被活表持有 %d ; 归 D2 但被任何表持有 %d'
          % (both_d1d2, d2_with_slot, d2_with_hold))

    # D1 细分
    d1 = [r for r in recs if r['cls'] == 'D1']
    site_share = collections.Counter(r['site'] for r in d1)
    d1_excl = [r for r in d1 if site_share[r['site']] == 1]
    d1_anchor = [r for r in d1 if r['anchored']]
    d1_clean = [r for r in d1 if not r['sem_unproved']]
    d1_nomatch = [r for r in d1 if r['col_match'] is False]
    print('  D1 %d：装表站点 distinct %d / 独占行 %d / 共用行 %d ; YRpp 锚定 %d ; '
          '语义[未证] %d ; COL 与行名不符 %d'
          % (len(d1), len(site_share), len(d1_excl), len(d1) - len(d1_excl),
             len(d1_anchor), len(d1) - len(d1_clean), len(d1_nomatch)))

    d2 = [r for r in recs if r['cls'] == 'D2']
    d3 = [r for r in recs if r['cls'] == 'D3']
    d4 = [r for r in recs if r['cls'] == 'D4']
    d3_self = [r for r in d3 if r['vt'] in installs]
    d3_dead = [r for r in d3 if r['vt'] not in installs]
    print('  D2 %d：YRpp 锚定 %d ; 语义[未证] %d'
          % (len(d2), sum(1 for r in d2 if r['anchored']),
             sum(1 for r in d2 if r['sem_unproved'])))
    hist = collections.Counter(len(r['direct']) for r in d2)
    print('  D2 direct 站点数分布: %s' % ', '.join('%s处×%d' % kv
                                                  for kv in sorted(hist.items())))
    # 装表指令形态：寄存器基址（实例 this）vs 绝对地址（全局静态对象 vptr 初始化）
    def inst_kind(site):
        t = text.installs_insn.get(site, '')
        m = re.search(r'dword ptr \[([^\]]+)\]', t)
        if not m:
            return '?'
        op = m.group(1)
        return 'abs' if op.strip().startswith('0x') else 'reg'
    d1_kind = collections.Counter(inst_kind(r['site']) for r in d1)
    d1_host = collections.Counter()
    for r in d1:
        s = r['site']
        i = bisect.bisect_right(starts, s) - 1
        d1_host['in_body' if (i >= 0 and starts[i] <= s < starts[i] + sizes[i])
                else 'outside_atlas'] += 1
    print('  D1 装表指令形态: %s ; 装表点宿主函数: %s'
          % (dict(d1_kind), dict(d1_host)))
    d1_mismatch_rows = [r for r in d1 if r['col_match'] is False]
    print('  D1 COL 真不符（全部持有表都比对过、模板名已按标识符匹配）%d：%s'
          % (len(d1_mismatch_rows),
             ', '.join('%s(%s)' % (r['entry'], r['name'][:28])
                       for r in d1_mismatch_rows[:8]) or '-'))
    print('  D1 决定性表 COL vs 行名：相符 %d / 不符 %d'
          % (sum(1 for r in d1 if r['dec_col_match'] is True),
             sum(1 for r in d1 if r['dec_col_match'] is False)))
    top_shared = collections.Counter(r['site'] for r in d1).most_common(5)
    print('  共用最多的装表点: %s'
          % ', '.join('%08X×%d行' % (s, n) for s, n in top_shared))
    # 决定性表 COL 与行名不符的 36 行：落到诊断文件，供逐行判 ②
    d1_decbad = [r for r in d1 if r['dec_col_match'] is False]
    with io.open(os.path.join(HERE, '_d1_col_mismatch.txt'), 'w',
                 encoding='utf-8', newline='\n') as f:
        f.write('entry\tname\tdec_vt\tslot\tdec_COL\tall_holding_COLs\n')
        for r in sorted(d1_decbad, key=lambda x: x['entry']):
            f.write('%s\t%s\t%08X\t%d\t%s\t%s\n' % (
                r['entry'], r['name'], r['vt'], r['slot'],
                tabs[r['vt']]['cls'],
                ','.join(sorted(set(tabs[v]['cls'] for v, _k in r['hold'])))))
    print('  wrote _d1_col_mismatch.txt (%d rows)' % len(d1_decbad))
    print('  D3 %d：仅体内自装(表活) %d / 表全无装表点(死表) %d'
          % (len(d3), len(d3_self), len(d3_dead)))
    print('  D4 %d：其中 dd 有命中但定不出表 %d / 完全无线索 %d'
          % (len(d4), sum(1 for r in d4 if r['dd_hits']),
             sum(1 for r in d4 if not r['dd_hits'])))

    # ---------------- 交叉核对 1：与 D48/4GAP 的 317 / 962
    held_live_rows = [r for r in recs if r['held_live_any']]
    notheld = [r for r in recs if not r['held_live_any']]
    print('\n=== 交叉核对 1（活表槽位持有 vs D48 317/962）===')
    print('  被活表(宽口径)槽位持有 %d ; 不被持有 %d  (D48 报 317 / 962)'
          % (len(held_live_rows), len(notheld)))
    # 体内外拆分
    only_self = [r for r in held_live_rows if r['selfs'] and not r['ext']]
    print('  其中：有体外装表点(D1) %d ; 仅体内自装 %d ; 活表持有但无装表点差? %d'
          % (cnt['D1'], len(only_self),
             len(held_live_rows) - cnt['D1'] - len(only_self)))

    # ---------------- 交叉核对 2：与 4GAP 三个扫描表 & PROBE_746
    def load_tsv(path):
        out = {}
        if not os.path.isfile(path):
            return out
        with io.open(path, encoding='utf-8-sig') as f:
            hdr = None
            for ln in f:
                c = ln.rstrip('\r\n').split('\t')
                if hdr is None:
                    hdr = c
                    continue
                if len(c) == len(hdr):
                    out[c[0].strip().upper()] = dict(zip(hdr, c))
        return out

    gap_name = load_tsv(os.path.join(GAP, 'scan_F4_name_only_no_ring4.tsv'))
    gap_census = load_tsv(os.path.join(GAP, 'scan_F4_census_no_ring4.tsv'))
    gap_desc = load_tsv(os.path.join(GAP, 'scan_F4_no_ring4_described.tsv')) \
        if os.path.isfile(os.path.join(GAP, 'scan_F4_no_ring4_described.tsv')) else {}
    name_746 = {k for k, v in gap_name.items() if int(v.get('direct', '0') or 0) > 0}
    census_215 = {k for k, v in gap_census.items() if v.get('V1') == 'y'}
    census_all = set(gap_census)
    name_all = set(gap_name)
    mine = {r['entry']: r for r in recs}

    print('\n=== 交叉核对 2（与 PROBE_746 / PROBE_4GAP 扫描表）===')
    print('  PROBE_746 批(4GAP 重建: name_only 且 direct>0) n=%d' % len(name_746))
    d2set = {r['entry'] for r in d2}
    print('  我的 D2 n=%d ; 与 746 批交集 %d ; 746 批里被我归 D1 的 %d ; 归 D3 %d ; D4 %d'
          % (len(d2set), len(d2set & name_746),
             sum(1 for e in name_746 if e in mine and mine[e]['cls'] == 'D1'),
             sum(1 for e in name_746 if e in mine and mine[e]['cls'] == 'D3'),
             sum(1 for e in name_746 if e in mine and mine[e]['cls'] == 'D4')))
    print('  4GAP census 全量 n=%d ; 其 V1=215 n=%d' % (len(census_all), len(census_215)))
    print('  census215 里被我归 D1 %d / D2 %d / D3 %d / D4 %d'
          % tuple(sum(1 for e in census_215 if e in mine and mine[e]['cls'] == c)
                  for c in ('D1', 'D2', 'D3', 'D4')))
    print('  D1 里来自 census 的 %d / 来自 name_only 的 %d / 其它 %d'
          % (sum(1 for r in d1 if r['entry'] in census_all),
             sum(1 for r in d1 if r['entry'] in name_all),
             sum(1 for r in d1 if r['entry'] not in census_all
                 and r['entry'] not in name_all)))
    # 4GAP 扫描过、但现在已不在我分母里的行（= 这段时间被补了 ④）
    proved_set = {r['entry'] for r in proved}
    no4_set = {r['entry'] for r in no4}
    drift = {}
    for nm, s in (('census', census_all), ('name_only', name_all)):
        drift[nm] = dict(scanned=len(s),
                         now_no4=len(s & no4_set),
                         now_has4=len([e for e in s if e in proved_set and e not in no4_set]),
                         not_proved_now=len([e for e in s if e not in proved_set]))
    print('  4GAP 扫描批与现盘漂移: %s' % json.dumps(drift, ensure_ascii=False))
    print('  D4 里与 962 对照：D4 且不被活表持有 %d（D4 定义即无表，应等于 D4 全体 %d）'
          % (sum(1 for r in d4 if not r['held_live_any']), len(d4)))

    # ---------------- 防自欺 1：D1 的「体外」判据是否因缺函数边界而空转
    def raw_refs(va, secname):
        n = 0
        pat = va.to_bytes(4, 'little')
        for sec in img.secs:
            if sec['name'] != secname:
                continue
            d = sec['data']
            i = d.find(pat)
            while i >= 0:
                n += 1
                i = d.find(pat, i + 1)
        return n

    d1_noatlas = [r for r in d1 if not r['body']]
    print('\n=== 防自欺 1：D1 判据的函数边界质量 ===')
    print('  D1 里不在 atlas（body 未知，体外判据空转）%d / %d'
          % (len(d1_noatlas), len(d1)))
    if d1_noatlas:
        for r in d1_noatlas[:5]:
            print('    %s %s ext@%s' % (r['entry'], r['name'][:46],
                                        '%08X' % r['ext'][0][2]))
    # D4 的「无引用」强度：entry 地址在整个镜像里出现几次
    d4_refs = [(r, raw_refs(int(r['entry'], 16), '.text'),
                raw_refs(int(r['entry'], 16), '.data'),
                raw_refs(int(r['entry'], 16), '.rdata')) for r in d4]
    print('  D4 %d 行：.text 裸 imm32 引用 %s ; .data %s ; .rdata %s'
          % (len(d4),
             collections.Counter(t for _r, t, _d, _rd in d4_refs).most_common(),
             collections.Counter(d for _r, _t, d, _rd in d4_refs).most_common(),
             collections.Counter(rd for _r, _t, _d, rd in d4_refs).most_common()))
    d4_zero_all = sum(1 for _r, t, d, rd in d4_refs if t == 0 and d == 0 and rd == 0)
    d4_in_atlas = sum(1 for r in d4 if r['body'])
    print('  D4 中「全镜像零引用」%d/%d ; 在 atlas 里（有函数体）%d/%d'
          % (d4_zero_all, len(d4), d4_in_atlas, len(d4)))

    # ---------------- 先例核对：盘上「已带 ④」的行是不是同一个 D1 形态
    def d1_shape(e):
        sz = atlas.get(e)
        body = (e, e + sz) if sz else None
        for vt, _k in holdings.get(e, []):
            for s, _d in installs.get(vt, []):
                if not in_own(s, body):
                    return True
        return False

    r4_rows = [r for r in proved if RING4 in r['sem']]
    r4_d1shaped = [r for r in r4_rows if d1_shape(int(r['entry'], 16))]
    r4_no126 = [r for r in r4_rows if '§12.6' not in r['sem']]
    r4_126 = [r for r in r4_rows if '§12.6' in r['sem']]
    r4_no126_d1 = [r for r in r4_no126 if d1_shape(int(r['entry'], 16))]
    # 已并表的 §12.6 行的装表点共用度
    cite_site = {}
    for r in r4_126:
        e = int(r['entry'], 16)
        sz = atlas.get(e)
        body = (e, e + sz) if sz else None
        for vt, _k in holdings.get(e, []):
            hit = [s for s, _d in installs.get(vt, []) if not in_own(s, body)]
            if hit:
                cite_site[e] = hit[0]
                break
    cite_share = collections.Counter(cite_site.values())
    print('\n=== 先例核对：已带 ④ 的 %d 行里，有多少本来就是 D1 形态 ===' % len(r4_rows))
    print('  带 ④ 且机械上是 D1 形态: %d / %d' % (len(r4_d1shaped), len(r4_rows)))
    print('  其中带 §12.6 引用 %d 行（取到装表点 %d，distinct %d，独占 %d / 共用 %d）'
          % (len(r4_126), len(cite_site), len(cite_share),
             sum(1 for _e, s in cite_site.items() if cite_share[s] == 1),
             sum(1 for _e, s in cite_site.items() if cite_share[s] > 1)))
    print('  无 §12.6 引用 %d 行，其中机械上仍是 D1 形态 %d 行（引用纪律缺口）'
          % (len(r4_no126), len(r4_no126_d1)))
    r4_126_census = [r for r in r4_126 if r['entry'] in census_215]
    print('  §12.6 行里 census 形态（② 来自同一张表）: %d' % len(r4_126_census))

    # 争议区（② 来自那张表）里还有没有独立链：另有 direct 站点的行数
    disputed = [r for r in d1 if r['entry'] in census_215
                or r['src'] == 'F4:slot_pivot_not_stated_as_ring4']
    disputed_direct = [r for r in disputed if r['direct']]
    print('  D1 争议区（census %d + slot_pivot %d = %d）里另有 direct 站点: %d'
          % (sum(1 for r in d1 if r['entry'] in census_215),
             sum(1 for r in d1 if r['src'] == 'F4:slot_pivot_not_stated_as_ring4'),
             len(disputed), len(disputed_direct)))

    # ---------------- 写 final.tsv
    fp = os.path.join(HERE, 'final.tsv')
    with io.open(fp, 'w', encoding='utf-8', newline='\n') as f:
        f.write('entry\tsubsystem\tname\tgrade\thas_ring4\tvt\tslot\tinstall_site\t'
                'direct_sites\tnote\n')
        for r in recs:
            f.write('%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' % (
                r['entry'], r['subsystem'], r['name'], r['grade'], r['cls'],
                '%08X' % r['vt'] if r['vt'] > 0 else '-',
                r['slot'] if r['slot'] >= 0 else '-',
                '%08X' % r['site'] if r['site'] else '-',
                ','.join('%08X' % s for s in r['direct'][:4]) or '-',
                ';'.join(r['notes']) or '-'))
    print('\nwrote final.tsv (%d rows)' % len(recs))

    # ---------------- ④ 成色的分层（保守/乐观的来源）
    tiers = {}
    d1_colok = [r for r in d1 if r['col_match'] is not False]
    tiers['D1_all'] = len(d1)
    tiers['D1_yrpp_anchored'] = len(d1_anchor)                       # ② 另有独立名字源
    tiers['D1_col_match_ok'] = len(d1_colok)                         # ② 与表不打架
    tiers['D1_anchored_and_colok'] = sum(1 for r in d1_colok if r['anchored'])
    tiers['D1_exclusive_install_site'] = len(d1_excl)                # 字面「site 不共用」
    tiers['D1_clean_sem'] = len(d1_clean)
    tiers['D1_anchored_colok_clean'] = sum(1 for r in d1_colok
                                           if r['anchored'] and not r['sem_unproved'])
    tiers['D1_excl_colok_clean'] = sum(1 for r in d1_excl
                                       if r['col_match'] is not False
                                       and not r['sem_unproved'])
    # 逐级去重（不靠相减）：clean → 再扣 abs 装表 → 再要求 site 独占
    tiers['D1_clean_no_colconflict'] = sum(1 for r in d1
                                           if r['col_match'] is not False
                                           and not r['sem_unproved'])
    tiers['D1_clean_no_colconflict_regonly'] = sum(
        1 for r in d1 if r['col_match'] is not False and not r['sem_unproved']
        and inst_kind(r['site']) == 'reg')
    tiers['D1_clean_no_colconflict_regonly_excl'] = sum(
        1 for r in d1 if r['col_match'] is not False and not r['sem_unproved']
        and inst_kind(r['site']) == 'reg' and site_share[r['site']] == 1)
    print('\n=== D1 分层（保守/乐观区间来源）===')
    for k in ('D1_all', 'D1_yrpp_anchored', 'D1_col_match_ok', 'D1_anchored_and_colok',
              'D1_clean_sem', 'D1_exclusive_install_site', 'D1_anchored_colok_clean',
              'D1_excl_colok_clean', 'D1_clean_no_colconflict',
              'D1_clean_no_colconflict_regonly',
              'D1_clean_no_colconflict_regonly_excl'):
        print('  %-40s %d' % (k, tiers[k]))
    subs = collections.Counter(r['subsystem'] for r in d1)
    print('  D1 子系统分布: %s' % ', '.join('%s %d' % kv for kv in subs.most_common()))
    summary_subs = dict(subs)

    # D1 的 ② 独立度 2×2（census 成员 = ② 来自那张表）
    d1_census = [r for r in d1 if r['entry'] in census_215]
    d1_not_census = [r for r in d1 if r['entry'] not in census_215]
    quad = dict(
        census_v1_and_anchored=sum(1 for r in d1_census if r['anchored']),
        census_v1_not_anchored=sum(1 for r in d1_census if not r['anchored']),
        other_and_anchored=sum(1 for r in d1_not_census if r['anchored']),
        other_not_anchored=sum(1 for r in d1_not_census if not r['anchored']))
    print('  D1 × ② 来源：census-V1 且 YRpp 锚定 %d / census-V1 未锚定 %d / '
          '非 census 且锚定 %d / 非 census 未锚定 %d'
          % (quad['census_v1_and_anchored'], quad['census_v1_not_anchored'],
             quad['other_and_anchored'], quad['other_not_anchored']))

    # 四类 × 来源类别 矩阵
    srcs = collections.Counter(r['src'] for r in recs)
    matrix = collections.defaultdict(collections.Counter)
    for r in recs:
        matrix[r['src']][r['cls']] += 1
    print('\n=== 四类 × 来源类别（M78/D47 口径，只读复用 classify）===')
    print('  %-36s %5s %5s %5s %5s %5s' % ('source_class', 'n', 'D1', 'D2', 'D3', 'D4'))
    for src, _n in srcs.most_common():
        m = matrix[src]
        print('  %-36s %5d %5d %5d %5d %5d' % (src, _n, m['D1'], m['D2'], m['D3'], m['D4']))
    matrix_out = dict((k, dict(v)) for k, v in matrix.items())

    # ---------------- 抽样 18 行证据（人工判读用）
    def pick(pool, k):
        pool = sorted(pool, key=lambda r: int(r['entry'], 16))
        if len(pool) <= k:
            return pool
        idx = [int(round(i * (len(pool) - 1) / float(k - 1))) for i in range(k)]
        return [pool[i] for i in sorted(set(idx))]

    d1_anchor_rows = [r for r in d1 if r['anchored']]
    d1_plain = [r for r in d1 if not r['anchored']]
    sample = (pick(d1_anchor_rows, 4) + pick(d1_plain, 4) + pick(d1_excl, 3)
              + pick(d2, 4) + pick(d3_self, 1) + pick(d3_dead, 1) + pick(d4, 4))
    # 去重后截到 18
    seen = set()
    uniq = []
    for r in sample:
        if r['entry'] in seen:
            continue
        seen.add(r['entry'])
        uniq.append(r)
    sample = uniq[:18]

    ev = []
    for r in sample:
        e = int(r['entry'], 16)
        body = r['body']
        lines = []
        lines.append('entry %s  %s  %s' % (r['entry'], r['subsystem'], r['name']))
        lines.append('  auto=%s  body=%s  sem=%s' % (
            r['cls'],
            ('[%08X,%08X) %d B' % (body[0], body[1], body[1] - body[0])) if body else 'NOT-IN-ATLAS',
            r['sem'][:110]))
        if r['hold']:
            for vt, k in r['hold'][:3]:
                t = tabs[vt]
                ins = installs.get(vt)
                lines.append('  hold: vt=%08X slot=%d nslots=%d cls=%s %s  installs=%s'
                             % (vt, k, t['n_slots'], t['cls'],
                                ('LIVE' if ins else 'DEAD'),
                                ', '.join('%08X(%s)' % (s, 'in' if in_own(s, body) else 'OUT')
                                          for s, _d in (ins or [])[:3]) or '-'))
        if r['ext']:
            vt, k, s = r['ext'][0]
            hostfn = None
            i = bisect.bisect_right(starts, s) - 1
            if i >= 0 and starts[i] <= s < starts[i] + sizes[i]:
                hostfn = starts[i]
            lines.append('  ext install: %08X  insn=%s  host_fn=%s  rows_sharing_this_site=%d'
                         % (s, text.insn_at(s),
                            ('%08X' % hostfn) if hostfn else 'outside-atlas',
                            site_share.get(s, 1)))
        if r['direct']:
            lines.append('  direct sites(%d): %s' % (
                len(r['direct']),
                ', '.join('%08X %s' % (s, text.insn_at(s)) for s in r['direct'][:2])))
        lines.append('  dd_hits=%d  col=%s  col_match=%s  yrpp_anchor=%s  sem[未证]=%s'
                     % (r['dd_hits'], ','.join(r['col_names']) or '-',
                        r['col_match'], r['anchored'], r['sem_unproved']))
        lines.append('  evidence_path=%s' % evpath.get(r['entry'], '-'))
        # 关键字节：entry 头 8 字节
        lines.append('  entry+0 bytes: %s' % img.buf[e - IMAGE_BASE:e - IMAGE_BASE + 8].hex(' '))
        ev.append('\n'.join(lines))
    with io.open(os.path.join(HERE, '_sample18_evidence.txt'), 'w',
                 encoding='utf-8', newline='\n') as f:
        f.write('\n\n'.join(ev) + '\n')
    print('wrote _sample18_evidence.txt (%d rows)' % len(sample))
    print('\n===== 抽样证据 =====')
    for x in ev:
        print(x)
        print('-' * 70)

    # ---------------- summary.json
    summary = dict(
        generated=time.strftime('%Y-%m-%dT%H:%M:%S%z'),
        exe_sha256=exe_sha, exe_sha_ok=(exe_sha == EXPECT_SHA),
        coverage_used=os.path.basename(COV_LIVE if not pinned else PIN),
        coverage_sha256=cov_sha, coverage_live_sha256=live_sha,
        coverage_rows=len(rows), proved=len(proved),
        ring4_any=len(ring4_any), ring4_slot=len(ring4_slot),
        proved_no4=len(no4),
        text=dict(insn=text.n_insn, skip=text.n_skip, call_mem=text.callmem),
        tables=dict(n=len(tabs), slots=n_slots, live=len(installs),
                    install_sites=sum(len(v) for v in installs.values()),
                    entries_held=len(holdings)),
        classes=dict((k, cnt[k]) for k in ('D1', 'D2', 'D3', 'D4')),
        overlap=dict(d1_with_direct=both_d1d2, d2_held_live=d2_with_slot,
                     d2_held_any=d2_with_hold),
        D1=dict(n=len(d1), sites_distinct=len(site_share), rows_exclusive=len(d1_excl),
                rows_shared=len(d1) - len(d1_excl), yrpp_anchored=len(d1_anchor),
                yrpp_unanchored=len(d1) - len(d1_anchor),
                sem_unproved=len(d1) - len(d1_clean),
                col_nomatch=len(d1_nomatch)),
        D2=dict(n=len(d2), yrpp_anchored=sum(1 for r in d2 if r['anchored']),
                sem_unproved=sum(1 for r in d2 if r['sem_unproved'])),
        D3=dict(n=len(d3), self_install_only=len(d3_self), dead_table=len(d3_dead)),
        D4=dict(n=len(d4), dd_but_no_table=sum(1 for r in d4 if r['dd_hits']),
                no_clue=sum(1 for r in d4 if not r['dd_hits'])),
        tiers=tiers, D1_subsystems=summary_subs, D1_quad=quad,
        matrix_cls_x_src=matrix_out,
        guard1=dict(d1_no_atlas_body=len(d1_noatlas),
                    d4_zero_refs_all_sections=d4_zero_all,
                    d4_in_atlas=d4_in_atlas),
        D1_install_kind=dict(d1_kind), D1_install_host=dict(d1_host),
        D1_col_mismatch=len(d1_mismatch_rows),
        D1_dec_col_match=dict(ok=sum(1 for r in d1 if r['dec_col_match'] is True),
                              bad=sum(1 for r in d1 if r['dec_col_match'] is False)),
        D1_top_shared_sites=[['%08X' % s, n] for s, n in top_shared],
        precedent=dict(ring4_rows=len(r4_rows), ring4_d1_shaped=len(r4_d1shaped),
                      ring4_with_126=len(r4_126), ring4_without_126=len(r4_no126),
                      without_126_but_d1_shaped=len(r4_no126_d1),
                      with_126_census_form=len(r4_126_census),
                      with_126_sites=len(cite_share),
                      with_126_site_exclusive=sum(1 for _e, s in cite_site.items()
                                                  if cite_share[s] == 1),
                      with_126_site_shared=sum(1 for _e, s in cite_site.items()
                                               if cite_share[s] > 1)),
        disputed=dict(n=len(disputed), with_direct=len(disputed_direct)),
        D2_direct_hist=dict((str(k), v) for k, v in hist.items()),
        xcheck1=dict(held_by_live_table=len(held_live_rows),
                     not_held=len(notheld)),
        xcheck2=dict(probe746_batch=len(name_746),
                     d2_n=len(d2set), d2_inter_746=len(d2set & name_746),
                     census_all=len(census_all), census_v1_215=len(census_215),
                     census215_in_D1=sum(1 for e in census_215
                                         if e in mine and mine[e]['cls'] == 'D1')),
        secs=round(time.time() - t0, 1),
    )
    with io.open(os.path.join(HERE, 'summary.json'), 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=1)
    print('\nwrote summary.json ; %.1f s' % summary['secs'])
    return 0


if __name__ == '__main__':
    sys.exit(main())
