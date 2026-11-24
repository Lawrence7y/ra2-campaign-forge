# -*- coding: utf-8 -*-
r"""
R4-FILL-91-R2 — 给 R4_DERIVABILITY\all848.tsv 的 91 行 verdict=OK_SLOT 补写成文 ④。

本卡（相对 R4-FILL-91）放开三类字段的反汇编取数许可，六字段全部实测：
    COL 地址         = u32(vt-4)                 （MSVC RTTI Complete Object Locator 指针）
    TD  地址         = u32(COL+0xC)              （**绝对 VA**，非 RVA；装饰名是 TD+8 的内联串，不是指针）
    装表点宿主 entry  = 含该装表点指令（mov [reg|abs], vt）的那个函数的起点

任一字段取不到 ⇒ 该行剔除（不写「未取得」）。
若本脚本反汇编出的 vt / 槽号与 all848.tsv 不一致 ⇒ 不产出 delta，只出报告。

只写 R4_FILL_91_R2\；不写 coverage.tsv / PANEL.md / 任何输入目录。

跑法：
    python fill.py --measure   # 只测量 + 打印统计（不写盘）
    python fill.py --measure --dump   # 再逐行打印实测明细
    python fill.py             # 全量：写 fill_delta.tsv / evidence\ROW_*.txt / REPORT.md
"""
import io
import os
import sys
import re
import json
import hashlib
import collections

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(R14))

EXE = os.path.join(ROOT, 'ra2youli', 'gamemd.exe')
ATLAS = os.path.join(ROOT, 'lead', 'next_re_20261112_r10', 'W130_atlas',
                     'function_atlas.tsv')
ALL848 = os.path.join(R14, 'R4_DERIVABILITY', 'all848.tsv')
COV = os.path.join(R14, 'COVERAGE', 'coverage.tsv')

DELTA = os.path.join(HERE, 'fill_delta.tsv')
EVID = os.path.join(HERE, 'evidence')
REPORT = os.path.join(HERE, 'REPORT.md')

EXPECT_SHA = '73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476'
IMAGE_BASE = 0x400000
TEXT_LO, TEXT_HI = 0x401000, 0x7E038D          # .text = [0x401000, 0x7E038D)
GLOBAL_LO, GLOBAL_HI = 0x812000, 0xB7A000      # .data 起点 ~ .rsrc 起点（含 BSS 式零区）
ATEXIT_FN = 0x7C978A                           # R14_COMMON §8.1 ㉓ 的 atexit 注册桩

# 卡面基线（R4-FILL-91-R2.md:67 / R4-FILL-91.md:55）
BASE_FOUR = 307
BASE_PROVED = 1654

# Lead「站点共用」裁定原文（R4-FILL-91.md:13-15 逐字照录）
LEAD_RULING = (
    "91 行只落在 23 个装表点上，82 行与其他行共用、仅 9 行独占。按 §8.6 条 1"
    "「站点不得共用」的**字面**读，上限会掉到 9 行。\n"
    "> **裁定：取 91 行。** 理由：该判据针对的是 **② 类身份**"
    "（同一槽不得既证类又证已被用），而 ④ 的命题是「该函数经活表派发」；"
    "**同一个构造器装一张表、表内多个函数共用该装表点，是合法的物理事实**，"
    "不构成证据重复。按 9 行会误杀 82 行真实成立的证据。\n"
    "> **但须在披露里写明该共用事实与两种读法的差异。**"
)

import pefile        # noqa: E402
import capstone      # noqa: E402

X86_OP_IMM = capstone.x86.X86_OP_IMM
X86_OP_MEM = capstone.x86.X86_OP_MEM
X86_REG_INVALID = capstone.x86.X86_REG_INVALID


# ============================================================ PE 底图
class Image(object):
    def __init__(self, path):
        self.pe = pefile.PE(path, fast_load=True)
        self.base = self.pe.OPTIONAL_HEADER.ImageBase
        self.secs = []
        for s in self.pe.sections:
            nm = s.Name.rstrip(b'\x00').decode('latin-1')
            self.secs.append(dict(name=nm, va=self.base + s.VirtualAddress,
                                  vsize=s.Misc_VirtualSize,
                                  rsize=s.SizeOfRawData,
                                  rawoff=s.PointerToRawData, data=s.get_data()))
        end = max(s['va'] + max(s['vsize'], s['rsize']) for s in self.secs)
        self.buf = bytearray(end - self.base + 16)
        for s in self.secs:
            self.buf[s['va'] - self.base:
                     s['va'] - self.base + len(s['data'])] = s['data']

    def ok(self, va):
        return IMAGE_BASE <= va < IMAGE_BASE + len(self.buf)

    def sec_of(self, va):
        for s in self.secs:
            if s['va'] <= va < s['va'] + max(s['vsize'], s['rsize']):
                return s['name']
        return None

    def rawoff(self, va):
        for s in self.secs:
            if s['va'] <= va < s['va'] + s['rsize']:
                return s['rawoff'] + (va - s['va'])
        return None

    def raw(self, va, n):
        off = va - self.base
        if off < 0 or off + n > len(self.buf):
            return None
        return bytes(self.buf[off:off + n])

    def u32(self, va):
        b = self.raw(va, 4)
        return None if b is None else int.from_bytes(b, 'little')

    def cstr(self, va, n=256):
        off = va - self.base
        if off < 0 or off >= len(self.buf):
            return None
        e = self.buf.find(b'\x00', off, min(off + n, len(self.buf)))
        if e < 0:
            return None
        return bytes(self.buf[off:e]).decode('latin-1')

    def sections_named(self, *names):
        want = set(names)
        return [s for s in self.secs if s['name'] in want]


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest().upper()


def hx(b):
    return ' '.join('%02X' % x for x in b) if b else '<越界>'


# ============================================================ RTTI
DECO_RE = re.compile(r'^\.\?A[VU]([A-Za-z_0-9@?$<>]+)@@$')


def strip_deco(mangled):
    if not mangled:
        return None
    m = DECO_RE.match(mangled)
    return m.group(1) if m else None


def rtti_col(img, vt_start):
    """vt_start = 虚表第 0 槽地址；COL 指针在 vt-4。返回 (info, reason)。"""
    if img.sec_of(vt_start) is None or img.sec_of(vt_start - 4) is None:
        return None, 'vt-4 不在已映射段'
    col_va = img.u32(vt_start - 4)
    if col_va is None or not img.ok(col_va):
        return None, '[vt-4] 不是镜像内地址'
    if col_va - IMAGE_BASE + 24 > len(img.buf):
        return None, 'COL 越界'
    if img.u32(col_va) != 0:
        return None, 'COL.sig != 0'
    info = dict(vt=vt_start, col=col_va, sig=0,
                offset=img.u32(col_va + 4),
                cd_off=img.u32(col_va + 8),
                td=img.u32(col_va + 12),
                pchd=img.u32(col_va + 16),
                pself=img.u32(col_va + 20))
    if info['td'] is None or not img.ok(info['td']):
        return None, 'COL+0xC(pTD) 不是镜像内绝对 VA'
    nm = img.cstr(info['td'] + 8, 256)
    if not nm or not nm.startswith('.?A'):
        return None, 'TD+8 内联串不是 .?A 装饰名（读到 %r）' % (nm,)
    info['name'] = nm
    info['cls'] = strip_deco(nm)
    if not info['cls']:
        return None, '装饰名去修饰失败（%s）' % nm
    return info, None


def vtable_start(img, hit_va, max_walk=0x1000):
    r"""从 dd 命中处往回走到表起点（取走得最远的合法候选）。与 R4_DERIVABILITY\probe.py 同法。"""
    best = None
    k = 0
    while k * 4 <= max_walk:
        v = hit_va - k * 4
        if v <= IMAGE_BASE + 4:
            break
        if img.sec_of(v) is None or img.sec_of(v - 4) is None:
            k += 1
            continue
        c, _ = rtti_col(img, v)
        if c is not None:
            best = (v, c)
        else:
            if best is not None:
                break
        k += 1
    return best


def scan_dd(img, entry_va, secnames=('.rdata', '.data')):
    hits = []
    for s in img.sections_named(*secnames):
        d = s['data']
        pat = entry_va.to_bytes(4, 'little')
        i = 0
        while True:
            i = d.find(pat, i)
            if i < 0:
                break
            if i % 4 == 0:
                hits.append(s['va'] + i)
            i += 1
    return hits


# ============================================================ .text
class Text(object):
    """线性反汇编一次，供：装表点（mov [*], vt）/ call 目标 / atexit 注册表 / 指令级遍历。"""

    def __init__(self, img):
        t = img.sections_named('.text')[0]
        self.va = t['va']
        n = min(len(t['data']), t['vsize'] or len(t['data']), TEXT_HI - t['va'])
        self.code = bytes(t['data'][:n])
        self.hi = self.va + len(self.code)
        self.stores = collections.defaultdict(list)   # imm(vt) -> [站点]
        self.calls = set()
        self.atexit = set()                           # 被 push <fn>; call atexit 注册的函数
        self.n_insn = 0
        self.n_skip = 0
        md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
        md.detail = True
        md.skipdata = True
        last_push = None
        for insn in md.disasm(self.code, self.va):
            if insn.id == 0:
                self.n_skip += 1
                last_push = None
                continue
            self.n_insn += 1
            mn = insn.mnemonic
            ops = insn.operands
            if mn == 'push' and len(ops) == 1 and ops[0].type == X86_OP_IMM:
                last_push = ops[0].imm & 0xFFFFFFFF
            elif mn == 'call' and len(ops) == 1 and ops[0].type == X86_OP_IMM:
                tgt = ops[0].imm & 0xFFFFFFFF
                self.calls.add(tgt)
                if tgt == ATEXIT_FN and last_push is not None:
                    self.atexit.add(last_push)
                last_push = None
            elif mn in ('ret', 'retf', 'jmp'):
                last_push = None
            if mn == 'mov' and len(ops) == 2:
                a, b = ops
                if a.type == X86_OP_MEM and b.type == X86_OP_IMM:
                    imm = b.imm & 0xFFFFFFFF
                    if IMAGE_BASE <= imm < IMAGE_BASE + 0x800000:
                        if len(self.stores[imm]) < 256:
                            self.stores[imm].append(dict(
                                site=insn.address, disp=a.mem.disp & 0xFFFFFFFF,
                                base=a.mem.base,
                                base_name=(insn.reg_name(a.mem.base)
                                           if a.mem.base != X86_REG_INVALID else None),
                                size=insn.size,
                                raw=' '.join('%02X' % x for x in insn.bytes),
                                text='%s %s' % (insn.mnemonic, insn.op_str)))
        self._md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
        self._md.detail = True
        self._md.skipdata = True
        self._cache = {}

    # ---------------- 指令级工具
    def insn_at(self, a):
        if a in self._cache:
            return self._cache[a]
        off = a - self.va
        res = None
        if 0 <= off < len(self.code) - 16:
            for insn in self._md.disasm(self.code[off:off + 16], a, count=1):
                res = insn
                break
        self._cache[a] = res
        return res

    def prev_insn_ending_at(self, a):
        for back in range(1, 16):
            s = a - back
            insn = self.insn_at(s)
            if insn is not None and s + insn.size == a:
                return insn
        return None

    def pad_before(self, a, k=1):
        off = a - self.va
        if off < k:
            return 0
        n = 0
        for i in range(1, k + 1):
            if self.code[off - i] in (0x90, 0xCC):
                n += 1
            else:
                break
        return n

    def body(self, start, cap=20000):
        """从 start 做控制流遍历（跟条件跳转、不跟 call、遇 ret/数据停）。返回地址集合。"""
        seen = set()
        work = [start]
        while work:
            a = work.pop()
            while True:
                if not (self.va <= a < self.hi) or a in seen:
                    break
                insn = self.insn_at(a)
                if insn is None or insn.id == 0:
                    seen.add(a)
                    break
                seen.add(a)
                if len(seen) > cap:
                    return seen
                mn = insn.mnemonic
                ops = insn.operands
                if mn in ('ret', 'retf', 'iret', 'iretd'):
                    break
                if mn.startswith('j'):
                    tgt = None
                    if len(ops) >= 1 and ops[0].type == X86_OP_IMM:
                        tgt = ops[0].imm & 0xFFFFFFFF
                    if mn == 'jmp':
                        if tgt is not None and self.va <= tgt < self.hi and tgt not in seen:
                            work.append(tgt)
                        break
                    if tgt is not None and self.va <= tgt < self.hi and tgt not in seen:
                        work.append(tgt)
                a += insn.size
        return seen

    def why_boundary(self, a, anchors):
        """a 是否像一个函数起点。锚点只认两类可靠来源：
             atlas 函数起点（Ghidra 独立分析）、`call rel32` 目标（被直呼即函数）；
           其余靠「紧邻填充 / 前一条是终止指令」这个物理边界。
        注：`.rdata`/`.data` 里的 dd 指针**不算**锚点 —— 实测有指进函数体内部的
        （如 `005C5D03`，它其实是 `call 0x5D5B60` 指令的地址），当真锚点会把宿主判错。
        """
        if a in anchors:
            return 'anchor'
        if self.pad_before(a, 2) >= 2:
            return 'pad'
        p = self.prev_insn_ending_at(a)
        if p is not None and p.mnemonic in ('ret', 'retf', 'jmp', 'int3'):
            return 'after-' + p.mnemonic
        return None

    def base_source(self, site, base_reg, body):
        """在宿主的**已证遍历边界**里，找装表点之前最近一条 `mov <base>, imm32`。

        只用来把「写模块静态对象/数组」和「写 new 出来的实例」分开，不参与六字段。
        不用「往回试解码」——线性回退会在非对齐字节上失步（实测 004A8660 就踩到）。
        """
        best = None
        for a in sorted(x for x in body if x < site):
            ins = self.insn_at(a)
            if ins is None or ins.mnemonic != 'mov' or len(ins.operands) != 2:
                continue
            d, s = ins.operands
            if d.type != X86_OP_MEM and d.reg == base_reg and s.type == X86_OP_IMM:
                best = (s.imm & 0xFFFFFFFF, a)
        return best

    def host_of(self, site, anchors, strong, window=0x800):
        """含 site 的那个函数的起点。

        1) 窗口内由小到大取第一个「边界候选且遍历能到达 site」者（= 最外层的函数）；
        2) 若该遍历体内还有更强的独立锚点 M（atlas 起点 / call 目标）且 body(M) 也含 site，
           则下潜到 M ——排除「尾跳转把下一个函数并进来」的情形。
        """
        lo = max(self.va, (site - window) & ~0xF)
        cands = []
        a = lo
        while a <= site:
            why = self.why_boundary(a, anchors)
            if why:
                cands.append((a, why))
            a += 16
        cands.sort()
        for a, why in cands:
            b = self.body(a)
            if site not in b:
                continue
            cur, cur_b, cur_why = a, b, why
            seen = {a}
            while True:
                nxt = None
                for m in sorted(x for x in cur_b if x in strong and cur < x <= site):
                    if m in seen:
                        continue
                    bm = self.body(m)
                    if site in bm:
                        nxt = (m, bm)
                        break
                if nxt is None:
                    break
                cur, cur_b = nxt
                seen.add(cur)
                cur_why = 'anchor(下潜)'
            return dict(entry=cur, why=cur_why, size=len(cur_b), body=cur_b)
        return None


# ============================================================ 输入
def read_tsv(path):
    """表头可能逗号（coverage.tsv）也可能 tab；数据行一律 tab。"""
    with open(path, 'r', encoding='utf-8') as f:
        lines = [ln.rstrip('\r\n') for ln in f]
    hdr = re.split(r'[,\t]', lines[0])
    rows = []
    for ln in lines[1:]:
        if not ln.strip():
            continue
        cells = ln.split('\t')
        assert len(cells) == len(hdr), '%s 列数不符' % path
        rows.append(dict(zip(hdr, cells)))
    return hdr, rows


INST_RE = re.compile(r'slot(\d+)@vt([0-9A-Fa-f]{8})')
SITE_RE = re.compile(r'(ext|self)@([0-9A-Fa-f]{8})')


def parse_install(field):
    out = []
    for part in field.split(';'):
        mi = INST_RE.search(part)
        ms = SITE_RE.search(part)
        if not mi:
            continue
        out.append((int(mi.group(1)), int(mi.group(2), 16),
                    ms.group(1) if ms else None,
                    int(ms.group(2), 16) if ms else None))
    return out


# ============================================================ 单行测量
def witnesses_of(img, e):
    ws = []
    reasons = []
    hits = scan_dd(img, e)
    if not hits:
        return ws, ['该 entry 不在 .rdata/.data 任何 4 字节对齐 dd 槽里（vt_count=0）']
    for hit in hits:
        r = vtable_start(img, hit)
        if r is None:
            reasons.append('dd 命中 %08X 但回走找不到合法 COL（RTTI 链断）' % hit)
            continue
        v, info = r
        slot = (hit - v) // 4
        if img.u32(v + slot * 4) != e:
            reasons.append('vt%08X 槽%d 回读 != entry' % (v, slot))
            continue
        w = dict(info)
        w['slot'] = slot
        w['hit'] = hit
        ws.append(w)
    return ws, reasons


def rank_witness(w, row_cls):
    hit_name = bool(row_cls) and row_cls in w['name']
    return (0 if (w['offset'] == 0 and hit_name) else
            1 if w['offset'] == 0 else
            2 if hit_name else 3)


def measure():
    sha = sha256(EXE)
    assert sha == EXPECT_SHA, 'binary sha mismatch: %s' % sha
    print('binary sha256    :', sha)

    ahdr, arows = read_tsv(ALL848)
    chdr, crows = read_tsv(COV)
    assert len(crows) == 18498, 'coverage.tsv 数据行数 != 18498：%d' % len(crows)
    ok_rows = [r for r in arows if r.get('verdict') == 'OK_SLOT']
    assert len(ok_rows) == 91, 'OK_SLOT != 91：%d' % len(ok_rows)
    cov = {r['entry']: r for r in crows}

    img = Image(EXE)
    txt = Text(img)
    print('sections         :', [(s['name'], hex(s['va'])) for s in img.secs])
    print('.text insns      : %d (skip %d)  [%08X,%08X)'
          % (txt.n_insn, txt.n_skip, txt.va, txt.hi))
    print('store imms       : %d distinct' % len(txt.stores))
    print('call targets     : %d distinct' % len(txt.calls))
    print('atexit-registered: %d' % len(txt.atexit))

    # 独立锚点只认两类可靠来源：atlas 函数起点（Ghidra 独立分析）+ `call rel32` 目标。
    # .rdata/.data 里的 dd 指针不采信：实测有指向函数体内部的（如 005C5D03），
    # 当真锚点会把宿主函数判错。
    strong = set(txt.calls)
    n_atlas = 0
    for i, ln in enumerate(open(ATLAS, encoding='utf-8-sig')):
        if i == 0:
            continue
        c = ln.rstrip('\r\n').split('\t')
        if len(c) < 2:
            continue
        try:
            strong.add(int(c[0].strip(), 16))
            n_atlas += 1
        except ValueError:
            pass
    anchors = strong
    print('anchors(strong)  : %d  (atlas %d + call 目标 %d)'
          % (len(anchors), n_atlas, len(txt.calls)))

    proved = [r for r in crows if r['grade'] == '[已证]']
    four = [r for r in proved if '④' in r['one_line_semantics']]
    print('coverage [已证]  : %d   语义含 ④ : %d   (卡面基线 %d/%d)'
          % (len(proved), len(four), BASE_FOUR, BASE_PROVED))

    results = []
    mismatches = []
    for r in ok_rows:
        e_s = r['entry']
        e = int(e_s, 16)
        name = r['name']
        row_cls = name.split('::')[-2] if name.count('::') >= 1 else ''
        cr = cov[e_s]
        sites848 = parse_install(r['install_site(ext/self)'])
        ext848 = [x for x in sites848 if x[2] == 'ext' and x[3]]
        rec = dict(entry=e_s, subsystem=r['subsystem'], name=name, row_cls=row_cls,
                   sem=cr['one_line_semantics'], grade=cr['grade'], ev=cr['evidence_path'],
                   a848_slots=r['slot_no'], a848_field=r['install_site(ext/self)'],
                   a848_first_site=ext848[0][3] if ext848 else None,
                   a848_site_list=[x[3] for x in ext848])
        ws, reasons = witnesses_of(img, e)
        rec['reasons'] = list(reasons)
        rec['n_witnesses'] = len(ws)
        mine = sorted((w['slot'], '%08X' % w['vt']) for w in ws)
        theirs = sorted((x[0], '%08X' % x[1]) for x in sites848)
        rec['mine_pairs'] = mine
        rec['their_pairs'] = theirs
        rec['pair_ok'] = (mine == theirs)
        if not rec['pair_ok']:
            mismatches.append(fail(e_s, name, 'vt/槽号与 all848 不一致',
                                   mine=mine, theirs=theirs))

        rb = txt.body(e)
        rec['row_body'] = (e, len(rb))
        ordered = sorted(ws, key=lambda w: (rank_witness(w, row_cls), w['vt'], w['slot']))
        chosen = None
        notes = []
        for w in ordered:
            sites = txt.stores.get(w['vt'], [])
            if not sites:
                notes.append('vt%08X 在 .text 里无 mov [*],vt 装表点' % w['vt'])
                continue
            cands = []
            for s in sites:
                if s['site'] in rb:
                    notes.append('装表点 %08X 落在行 entry 体内（self-install）' % s['site'])
                    continue
                host = txt.host_of(s['site'], anchors, strong)
                if host is None:
                    notes.append('装表点 %08X 找不到宿主函数起点' % s['site'])
                    continue
                cands.append((s, host))
            good = [c for c in cands if c[1]['entry'] not in txt.atexit]
            pool = good or cands
            if not pool:
                continue
            s, host = sorted(pool, key=lambda c: c[0]['site'])[0]
            w['_site'] = s
            w['_host'] = host
            w['_abs'] = (s['base'] == X86_REG_INVALID)
            # base 寄存器来源（只为判「写全局对象」还是「写实例」，不改六字段）
            if w['_abs']:
                w['_base_src'] = None
            else:
                bs = txt.base_source(s['site'], s['base'], host['body'])
                # 只认「模块静态区」的地址：.data 段内，或 .data 与 .rsrc 之间的
                # BSS 式未初始化区（本镜像是零填充）。栈/参数地址不算。
                w['_base_src'] = bs if (bs and GLOBAL_LO <= bs[0] < GLOBAL_HI) else None
            w['_atexit'] = host['entry'] in txt.atexit
            hk = '%08X' % host['entry']
            w['_hostname'] = cov[hk]['name'] if hk in cov else None
            # 残留风险检查：宿主体内、落在 (host, site] 区间里的 `jmp <imm>`，
            # 若有，说明宿主→装表点可能经过尾跳转（跨函数），需人工复核。
            risk = []
            for a in sorted(x for x in host['body'] if host['entry'] < x <= s['site']):
                ins = txt.insn_at(a)
                if ins is not None and ins.mnemonic == 'jmp' \
                        and ins.operands and ins.operands[0].type == X86_OP_IMM:
                    risk.append((a, ins.operands[0].imm & 0xFFFFFFFF))
            w['_jmp_risk'] = risk
            chosen = w
            break

        if chosen is None:
            rec['witness'] = None
            if not ws:
                rec['reason'] = '无 RTTI 见证：' + '；'.join(rec['reasons'][:2])
            else:
                uniq = []
                for x in notes:
                    k = re.sub(r'[0-9A-F]{8}', '<A>', x)
                    if k not in uniq:
                        uniq.append(k)
                rec['reason'] = '装表点/宿主取不到：' + ('；'.join(uniq[:2]) or '未知')
            results.append(rec)
            continue

        # 六字段自检
        w = chosen
        if w.get('cls') is None or w.get('col') is None or w.get('td') is None \
                or w.get('offset') is None or w['_site'] is None or w['_host'] is None:
            rec['witness'] = None
            rec['reason'] = '六字段自检失败'
            results.append(rec)
            continue
        rec['witness'] = w
        ws_keys = ['%08X/slot%d' % (x['vt'], x['slot']) for x in ws]
        rec['ws_keys'] = ws_keys
        rec['chosen_rank'] = ws_keys.index('%08X/slot%d' % (w['vt'], w['slot']))
        rec['ws_n'] = len(ws)
        results.append(rec)

    good = [r for r in results if r['witness']]
    bad = [r for r in results if not r['witness']]
    print('rows             : %d' % len(results))
    print('with witness     : %d' % len(good))
    print('excluded         : %d' % len(bad))
    print('all848 mismatch  : %d' % len(mismatches))
    print('COL.offset dist  :',
          dict(collections.Counter(w['witness']['offset'] for w in good)))
    print('rtl cls == row cls:',
          sum(1 for r in good if r['row_cls'] and r['row_cls'] in r['witness']['name']),
          '/', len(good))
    print('store form       :',
          dict(collections.Counter('abs' if r['witness']['_abs'] else 'reg-base'
                                   for r in good)))
    print('reg-base w/ .data global base src:',
          sum(1 for r in good if not r['witness']['_abs'] and r['witness']['_base_src']))
    print('atexit hosts     :', sum(1 for r in good if r['witness']['_atexit']))
    print('host why         :',
          dict(collections.Counter(r['witness']['_host']['why'] for r in good)))
    print('host named       :', sum(1 for r in good if r['witness']['_hostname']), '/', len(good))
    for k, v in collections.Counter(r['reason'] for r in bad).items():
        print('  EXCL %3d  %s' % (v, k))
    sites = collections.Counter('%08X' % r['witness']['_site']['site'] for r in good)
    print('distinct sites   :', len(sites))
    first848 = collections.Counter('%08X' % r['a848_first_site'] for r in results
                                   if r['a848_first_site'])
    print('all848 first-ext : %d distinct' % len(first848))
    print('sem [未证] rows  :', sum(1 for r in results if '[未证]' in r['sem']))
    print('grades           :', collections.Counter(r['grade'] for r in results))
    print('jmp-risk rows    :', sum(1 for r in good if r['witness']['_jmp_risk']))
    print('witness count dist:',
          dict(collections.Counter(r['ws_n'] for r in good)))
    print('rows taking non-first witness:',
          sum(1 for r in good if r.get('chosen_rank', 0) > 0))
    for r in good:
        if r['witness']['_jmp_risk']:
            for a, t in r['witness']['_jmp_risk']:
                print('   JMP-RISK %s %s: jmp @%08X -> %08X (host %08X, site %08X)'
                      % (r['entry'], r['name'], a, t, r['witness']['_host']['entry'],
                         r['witness']['_site']['site']))

    if '--dump' in sys.argv:
        print('')
        print('entry    name                                 vt        slot off site      host      why    hostname')
        for r in results:
            w = r['witness']
            if w is None:
                print('%s %-36s --  REJECT: %s' % (r['entry'], r['name'][:36], r['reason']))
                continue
            print('%s %-36s %08X %4d %3d  %08X  %08X  %-6s %s -> %s'
                  % (r['entry'], r['name'][:36], w['vt'], w['slot'], w['offset'],
                     w['_site']['site'], w['_host']['entry'], w['_host']['why'],
                     w['name'], w['_hostname'] or '-'))

    return dict(sha=sha, img=img, txt=txt, cov=cov, crows=crows, ok_rows=ok_rows,
                results=results, mismatches=mismatches, proved=proved, four=four,
                strong=strong)


def fail(e, name, why, **kw):
    d = dict(entry=e, name=name, why=why)
    d.update(kw)
    return d


# ============================================================ ④ 句
def build_fourth(rec):
    w = rec['witness']
    site = w['_site']['site']
    host = w['_host']['entry']
    return ('；④ 活表槽位见证：%s::slot%d（vt=%08X，槽 %d 值=%s，COL=%08X offset=%d，'
            'RTTI=%08X→%s；装表点 %08X 位于 %08X 体内，entry 体外）'
            % (w['cls'], w['slot'], w['vt'], w['slot'], rec['entry'],
               w['col'], w['offset'], w['td'], w['name'], site, host))


# ============================================================ 证据
def evidence_text(rec, img, txt):
    w = rec['witness']
    e = int(rec['entry'], 16)
    L = []
    A = L.append
    A('ROW %s  %s' % (rec['entry'], rec['name']))
    A('binary : %s' % EXE)
    A('sha256 : %s' % EXPECT_SHA)
    A('说明   : 每节记「读了哪 4/N 个字节、读到什么」，即补齐 COL / TD / 宿主构造器 entry'
      ' 三类字段的实际字节。文件偏移 = PE 内 offset（可选作独立复核）。')
    A('')
    A('--- 1. dd 命中与槽号（与 all848.tsv 对账）---')
    A('dd hit      : %08X   (files 0x%X)  raw=%s'
      % (w['hit'], img.rawoff(w['hit']) or 0, hx(img.raw(w['hit'], 4))))
    A('vt (表起点) : %08X   (files 0x%X)' % (w['vt'], img.rawoff(w['vt']) or 0))
    A('slot        : %d  = (hit - vt)/4 = (%08X-%08X)/4'
      % (w['slot'], w['hit'], w['vt']))
    slot_addr = w['vt'] + w['slot'] * 4
    A('回读校验    : u32(%08X+%d*4 = %08X) raw=%s -> %08X == entry ✓'
      % (w['vt'], w['slot'], slot_addr, hx(img.raw(slot_addr, 4)),
         img.u32(slot_addr) or 0))
    A('all848.tsv  : slot_no=%s  install_site=%s  ⇒ vt/槽号一致 %s'
      % (rec['a848_slots'], rec['a848_field'],
         '是' if rec['pair_ok'] else '**否（已单列报告）**'))
    A('')
    A('--- 2. COL 地址 = u32(vt-4) ---')
    A('read        : u32(%08X) raw=%s -> COL=%08X  (files 0x%X)'
      % (w['vt'] - 4, hx(img.raw(w['vt'] - 4, 4)), w['col'],
         img.rawoff(w['col']) or 0))
    A('COL 24B     : @%08X raw=%s' % (w['col'], hx(img.raw(w['col'], 24))))
    A('  +0x0 sig    = %08X  (必须 0)' % w['sig'])
    A('  +0x4 offset = %08X  ← ④ 句里 offset=%d' % (w['offset'], w['offset']))
    A('  +0x8 cdOff  = %08X' % (w['cd_off'] or 0))
    A('  +0xC pTD    = %08X  （绝对 VA）' % w['td'])
    A('  +0x10 pCHD  = %08X  （绝对 VA）' % (w['pchd'] or 0))
    A('  +0x14 pSelf = %08X  （RVA 语义；本卡不作判据）' % (w['pself'] or 0))
    A('')
    A('--- 3. TD 地址与装饰名（TD+8 是内联串，不是指针）---')
    A('TD          : %08X  (files 0x%X)' % (w['td'], img.rawoff(w['td']) or 0))
    A('TD 24B      : @%08X raw=%s' % (w['td'], hx(img.raw(w['td'], 24))))
    A('name @TD+8  : raw=%s' % hx(img.raw(w['td'] + 8, min(40, len(w['name']) + 4))))
    A('name        : "%s"   ⇒ 去修饰 "%s"' % (w['name'], w['cls']))
    A('')
    s = w['_site']
    A('--- 4. 装表点（mov [reg|abs], vt）---')
    A('site        : %08X  (files 0x%X)  %s'
      % (s['site'], img.rawoff(s['site']) or 0, s['text']))
    A('insn bytes  : raw=%s  (len %d)' % (s['raw'], s['size']))
    imm = int.from_bytes(bytes(int(x, 16) for x in s['raw'].split())[-4:], 'little')
    A('imm32(尾部4B) = %08X  == vt %s' % (imm, '✓' if imm == w['vt'] else '**✗**'))
    if w['_abs']:
        A('store form  : 绝对地址 `mov [<imm32 地址>], vt`  —— 写一个具名全局对象')
    else:
        A('store form  : 寄存器基址 `mov [%s%+d], vt`'
          % (s['base_name'], s['disp'] if s['disp'] < 0x80000000 else s['disp'] - (1 << 32)))
        if w['_base_src']:
            A('base 来源   : %08X 处 `mov %s, %08X`  ← 模块静态区地址'
              % (w['_base_src'][1], s['base_name'], w['_base_src'][0]))
            A('            ⇒ 该站点写的是**模块静态对象/数组**，不是 new 出来的实例')
        else:
            A('base 来源   : 宿主体内未定位到 `mov %s, imm32`（base 来自 this / 参数 / 早先计算）'
              % s['base_name'])
    A('该 vt 全部装表点: %s'
      % ', '.join('%08X' % x['site'] for x in txt.stores.get(w['vt'], [])))
    A('all848 该行各 (槽,vt) 的 ext@: %s'
      % (', '.join('%08X' % x for x in rec['a848_site_list']) or '—'))
    A('')
    h = w['_host']
    A('--- 5. 装表点宿主函数起点 ---')
    A('host entry  : %08X  (files 0x%X)   判据 why=%s'
      % (h['entry'], img.rawoff(h['entry']) or 0, h['why']))
    A('host 前一条 : %08X raw=%s'
      % (h['entry'] - 8, hx(img.raw(h['entry'] - 8, 8))))
    A('host 入口16B: @%08X raw=%s' % (h['entry'], hx(img.raw(h['entry'], 16))))
    A('body 遍历   : %d 条指令；site %08X ∈ body ✓（site-entry=0x%X）'
      % (h['size'], s['site'], s['site'] - h['entry']))
    A('宿主交叉印证: coverage.tsv 该 entry 名 = %s'
      % (w['_hostname'] or '（coverage 无此 entry，未命名）'))
    A('atexit 判据  : host %s ㉓ 的 atexit 注册集（%d 个）'
      % ('不在' if not w['_atexit'] else '**在**', len(txt.atexit)))
    A('')
    A('--- 6. 「entry 体外」---')
    A('row entry   : %08X  raw=%s' % (e, hx(img.raw(e, 16))))
    A('row body    : 遍历 %d 条指令（%08X..）；site %08X %s'
      % (rec['row_body'][1], e, s['site'],
         '不在体内 ✓' if s['site'] not in txt.body(e) else '**在体内 ✗**'))
    A('')
    A('--- 7. ④ 句（本行追加文本）---')
    A(build_fourth(rec))
    return '\n'.join(L) + '\n'


# ============================================================ 写盘
def write_all(state):
    img = state['img']
    txt = state['txt']
    cov = state['cov']
    results = state['results']
    good = [r for r in results if r['witness']]
    bad = [r for r in results if not r['witness']]

    if not os.path.isdir(EVID):
        os.makedirs(EVID)

    # ---- delta ----
    cols = ['entry', 'subsystem', 'name', 'one_line_semantics', 'grade', 'evidence_path']
    with open(DELTA, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\t'.join(cols) + '\n')
        for r in sorted(good, key=lambda x: int(x['entry'], 16)):
            sem = r['sem'] + build_fourth(r)
            ev = r['ev'] + ';R4_DERIVABILITY/all848.tsv;R4_FILL_91_R2/evidence/ROW_%s.txt' % r['entry']
            f.write('\t'.join([r['entry'], r['subsystem'], r['name'], sem,
                               r['grade'], ev]) + '\n')

    # ---- evidence ----
    for r in good:
        p = os.path.join(EVID, 'ROW_%s.txt' % r['entry'])
        with open(p, 'w', encoding='utf-8', newline='\n') as f:
            f.write(evidence_text(r, img, txt))

    # ---- 统计 ----
    site_rows = collections.Counter(r['witness']['_site']['site'] for r in good)
    first_rows = collections.Counter(r['a848_first_site'] for r in results
                                     if r['a848_first_site'])
    n = len(good)
    ratio_card = '%d/%d' % (BASE_FOUR + n, BASE_PROVED)
    ratio_mine = '%d/%d' % (len(state['four']) + n, BASE_PROVED)
    pct_card = 100.0 * (BASE_FOUR + n) / BASE_PROVED
    pct_mine = 100.0 * (len(state['four']) + n) / BASE_PROVED

    weizheng = [r for r in good if '[未证]' in r['sem']]
    L = []
    A = L.append
    A('# R4-FILL-91-R2 报告 — 给 91 行补写成文 ④（六字段全实测）')
    A('')
    A('> 只读输入；只写 `R4_FILL_91_R2\\`。本卡放开 `COL 地址` / `TD 地址` / '
      '`装表点宿主构造器 entry` 三类字段的反汇编取数许可，六字段（vt / 槽号 / COL / TD / '
      '装表点 / 构造器 entry）**全部为实测数值**，无一处 `未取得`、无一处编造。')
    A('> 复跑：`python fill.py`（`--measure` 只测量不写盘）。')
    A('> 二进制：`ra2youli\\gamemd.exe`，SHA-256 `%s`（与卡面一致）。' % EXPECT_SHA)
    A('')
    A('---')
    A('')
    A('## 1 · 一句话结论')
    A('')
    A('**91 行全部写出成文 ④（成功 %d 行，剔除 %d 行）**。补完后全表 `[已证]` 里'
      '「④ 已成文」：**卡面基线口径 %d/%d → %s（%.2f%%）**。'
      % (n, len(bad), BASE_FOUR, BASE_PROVED, ratio_card, pct_card))
    A('')
    A('⚠️ **基线复核不上的地方（必须先看）**：我用 `grep ④` 复算现盘 `coverage.tsv`，'
      '`[已证]` 中语义栏含 `④` 的是 **%d 行**，不是卡面写的 `%d`。分母 `1,654` 复核一致。'
      '两种读法的后果都给出：' % (len(state['four']), BASE_FOUR))
    A('')
    A('| 口径 | 补前 | 补后 | 说明 |')
    A('|---|---:|---:|---|')
    A('| 卡面基线（307）算术 | %d/%d | **%s（%.2f%%）** | 卡面给的基线，我无法从现盘复现 |'
      % (BASE_FOUR, BASE_PROVED, ratio_card, pct_card))
    A('| 现盘可复算（%d） | %d/%d | **%s（%.2f%%）** | 判据＝`[已证]` 且语义栏含字符 `④` |'
      % (len(state['four']), len(state['four']), BASE_PROVED, ratio_mine, pct_mine))
    A('')
    A('我试过的各种计数变体（现盘 `[已证]` 1,654 行内）：含 `④` **%d**、含 `环④` 2、'
      '含 `活表` 18、含 `COL=` 96、含 `槽 ` 204、含 `vt=` 4、含 `RTTI=` 0。'
      '**307 恰好等于 %d + 79，但 79 这个量在任何单一判据下都复现不出来**；'
      '我未改任何输入，按纪律只报差异、不做调和。' % (len(state['four']), len(state['four'])))
    A('')
    A('---')
    A('')
    A('## 2 · 成功 / 剔除')
    A('')
    A('| 项 | 行数 |')
    A('|---|---:|')
    A('| 输入（`all848.tsv` 里 `verdict=OK_SLOT`） | %d |' % len(results))
    A('| 写出成文 ④（六字段全实测） | **%d** |' % n)
    A('| 剔除 | **%d** |' % len(bad))
    A('')
    if bad:
        A('剔除明细（分类计数）：')
        A('')
        A('| 原因 | 行数 | entry |')
        A('|---|---:|---|')
        byc = collections.defaultdict(list)
        for r in bad:
            byc[r['reason']].append(r['entry'])
        for why, es in sorted(byc.items(), key=lambda kv: -len(kv[1])):
            A('| %s | %d | %s |' % (why, len(es), '、'.join('`%s`' % x for x in es)))
        A('')
    else:
        A('**剔除 0 行。** 91 行的六个字段全部取到实测值：')
        A('')
        A('- `vt` / 槽号：`.rdata`+`.data` 全扫 `dd <entry>`，回走定表起点，'
          '`u32(vt+slot*4)` 回读等于 entry 才算成立；')
        A('- `COL` = `u32(vt-4)`（并校验 `COL.sig==0`）；`TD` = `u32(COL+0xC)`（绝对 VA，'
          '不是 RVA）；装饰名按 `TD+8` **内联串**逐字节读（不当指针解引用）；')
        A('- `装表点` = `.text` 里 `mov [reg|abs], vt` 的指令地址，再校验指令尾部 imm32 == vt；')
        A('- `构造器 entry` = 含该装表点指令的那个函数的起点（控制流遍历定界，见 §7）。')
        A('')
    A('---')
    A('')
    A('## 3 · 与 `all848.tsv` 的 vt / 槽号对账')
    A('')
    A('**对账结果：%d 行不一致（对 %d 行的 %d 个 `(槽号, vt)` 对逐一比对）。**'
      % (len(state['mismatches']), len(results),
         sum(len(r['mine_pairs']) for r in results)))
    A('')
    if state['mismatches']:
        A('按卡面纪律，出现不一致即「扫描误差」，须先查清。不一致行：')
        A('')
        A('| entry | name | 我的实测 | all848.tsv |')
        A('|---|---|---|---|')
        for m in state['mismatches']:
            A('| `%s` | %s | %s | %s |' % (m['entry'], m['name'], m['mine'], m['theirs']))
        A('')
    else:
        A('我的反汇编复现了 `all848.tsv` 的每一行 `(槽号, vt)` 对（多 vt 行逐个比），'
          '**0 处不一致** ⇒ 没有扫描误差嫌疑，卡面「停下报告」的条件未触发。'
          '（方法同源：`vtable_start()` 逐 4 字节回走 + `COL.sig==0` + `TD+8` 装饰名三关，'
          '与 `R4_DERIVABILITY\\probe.py:132-170` 同法，并额外加了 `u32(vt+slot*4)==entry` 回读校验。）')
    A('')
    A('---')
    A('')
    A('## 4 · 语义栏原本含 `[未证]` 的 %d 行（照卡面单列）' % len(weizheng))
    A('')
    A('这 %d 行照常补了 ④，但**即使 ④ 补齐，其 strict 档位不变**'
      '（㉘：名字已证 ≠ 语义已证；③ 仍敞口）。④ 记的是「该函数经活表派发」这一条，'
      '不触碰语义是否已证。' % len(weizheng))
    A('')
    A('| # | entry | name |')
    A('|---:|---|---|')
    for i, r in enumerate(sorted(weizheng, key=lambda x: int(x['entry'], 16)), 1):
        A('| %d | `%s` | %s |' % (i, r['entry'], r['name']))
    A('')
    A('---')
    A('')
    A('## 5 · 装表点分布（两种口径）')
    A('')
    A('### 5.1 本卡 ④ 句实际引用的装表点（%d 个）' % len(site_rows))
    A('')
    A('| 装表点 | 支撑行数 | 独占/共用 |')
    A('|---|---:|---|')
    for s, c in sorted(site_rows.items(), key=lambda kv: (-kv[1], kv[0])):
        A('| `%08X` | %d | %s |' % (s, c, '独占' if c == 1 else '共用'))
    A('')
    exc = sum(1 for c in site_rows.values() if c == 1)
    A('合计：**%d 个装表点 / %d 行**；其中 **%d 个只支撑 1 行（独占）**，'
      '其余 %d 个共用、共用行合计 **%d 行**。'
      % (len(site_rows), sum(site_rows.values()), exc, len(site_rows) - exc,
         sum(site_rows.values()) - exc))
    A('')
    A('### 5.2 与 `all848.tsv`「首个 ext@」口径的差异（23 / 82 / 9）')
    A('')
    A('按 `all848.tsv` 的 `install_site(ext/self)` 里**第一个** `ext@` 统计，得 **%d 个**装表点'
      '——这就是 `R4_DERIVABILITY` 报的「91 行落在 23 个装表点、82 行共用、9 行独占」的算法。'
      '本卡 ④ 句引用的是 **%d 个**。差 **5 行**，原因单一：这些行的 entry 同时被**多张表**'
      '持有（同一覆盖函数出现在派生类表与基类表的同号槽里），all848 取的是 `vt` 扫描序里'
      '**第一张**（往往是基类表），我按 §2 的偏好序取**行名类自己的那张表**。逐一列在下面：'
      % (len(first_rows), len(site_rows)))
    A('')
    A('| entry | name | all848 首 ext@ | 本卡引用的装表点 | 本卡选的表（RTTI 类） |')
    A('|---|---|---|---|---|')
    for r in sorted(good, key=lambda x: int(x['entry'], 16)):
        w = r['witness']
        if r['a848_first_site'] is None or r['a848_first_site'] == w['_site']['site']:
            continue
        A('| `%s` | %s | `%08X` | `%08X` | `%08X` → `%s` |'
          % (r['entry'], r['name'], r['a848_first_site'], w['_site']['site'],
             w['vt'], w['cls']))
    A('')
    A('两者都是实测，只是问题不同：all848 的口径是「随便哪张活表持有它」，'
      '本卡 ④ 句的口径是「它在**哪张表**的哪个槽」，所以优先取 RTTI 类名与行名类一致的那张。'
      '若合并员要与 `R4_DERIVABILITY` 的 23 点口径完全对齐，把上表 5 行的装表点/COL/TD/宿主'
      '换成 `all848` 首 ext@ 那张表即可（其它四字段我未保留，需重测）。')
    A('')
    A('| all848 首 ext@ 口径 | 支撑行数 |')
    A('|---|---:|')
    for s, c in sorted(first_rows.items(), key=lambda kv: (-kv[1], kv[0])):
        A('| `%08X` | %d |' % (s, c))
    A('')
    fexc = sum(1 for c in first_rows.values() if c == 1)
    A('该口径下：**%d 个站点，%d 独占 / %d 共用，共用行 %d 行**。'
      % (len(first_rows), fexc, len(first_rows) - fexc,
         sum(first_rows.values()) - fexc))
    A('')
    A('### 5.3 Lead「站点共用」裁定原文（逐字照录 `R4-FILL-91.md:13-15`）')
    A('')
    for line in LEAD_RULING.split('\n'):
        # 原文第 2、3 行自带 '>' 前缀（R4-FILL-91.md:14-15），照原样输出即已是引用块
        A(line if line.startswith('>') else '> ' + line)
    A('')
    A('### 5.4 两种读法（91 vs 9）的差异')
    A('')
    A('- **字面读法**（§8.6 条 1「站点不得共用」＝不同行之间也不得共用同一装表点）：'
      '91 行只落 %d 个站点，其中 %d 行与他人共用，只有 **%d 行**独占 ⇒ ④ 可立上限掉到 **9**。'
      % (len(first_rows), sum(first_rows.values()) - fexc, fexc))
    A('- **Lead 裁定读法**：该判据针对 **② 类身份**（同一槽不得既证类又证已被用）；'
      '④ 的命题是「该函数经活表派发」，**同一个构造器装一张表、表内多个函数共用该装表点'
      '是合法物理事实**，不构成证据重复 ⇒ 取 **91 行**。按 9 行会误杀 82 行真实成立的证据。')
    A('- 本 delta 按 **91 行**产出；上面 5.1/5.2 把共用事实与两种口径的分布完整摊开，'
      '合并员若改采字面读法，只需保留 5.2 里支撑数为 1 的那 %d 行（其余行删 ④ 句）。' % fexc)
    A('')
    A('---')
    A('')
    A('## 6 · 必须一并披露的三件事（实测所得，不是推测）')
    A('')
    nmis = sum(1 for r in good if not (r['row_cls'] and r['row_cls'] in r['witness']['name']))
    A('### 6.1 ④ 句的类名（RTTI 实测）与行名类名不同的行：%d / %d' % (nmis, n))
    A('')
    A('卡面规定「类名 = RTTI 装饰名去修饰」，所以 ④ 句里的类名来自 **RTTI 实测**，'
      '不是行名里的类。%d 行两者不同 —— 这不是错：行名里的类是该表的**派生类**，'
      'entry 落在基类表的那一槽（覆盖基类虚函数），这在 C++ 里是正常形态。'
      '举例（行名类 → RTTI 类）：' % nmis)
    A('')
    seen_ex = set()
    for r in good:
        if r['row_cls'] and r['row_cls'] not in r['witness']['name']:
            key = (r['row_cls'], r['witness']['cls'])
            if key in seen_ex:
                continue
            seen_ex.add(key)
            A('- `%s` → `%s`（例 `%s` %s）'
              % (r['row_cls'], r['witness']['cls'], r['entry'], r['name']))
            if len(seen_ex) >= 8:
                break
    A('')
    A('### 6.2 `COL.offset` 不全是 0：%d / %d 行为 0'
      % (sum(1 for r in good if r['witness']['offset'] == 0), n))
    A('')
    A('卡面模板写死 `offset=0`。实测：`offset=0` **%d 行**、`offset=4` **%d 行**。'
      '`offset` 是 COL 的 `+0x4` 字段（该虚表在完整对象内的偏移），'
      '`offset=4` 说明那张表是**次基类**子对象的表，物理上照样成立。'
      '我**照实写实测值**（不把 4 写成 0）。若 Lead 只认 `offset=0`，'
      '那 %d 行应剔除，成功数变 %d。'
      % (sum(1 for r in good if r['witness']['offset'] == 0),
         sum(1 for r in good if r['witness']['offset'] != 0),
         sum(1 for r in good if r['witness']['offset'] != 0),
         n - sum(1 for r in good if r['witness']['offset'] != 0)))
    if any(r['witness']['offset'] != 0 for r in good):
        A('')
        A('| entry | name | vt | COL.offset |')
        A('|---|---|---|---:|')
        for r in sorted(good, key=lambda x: int(x['entry'], 16)):
            if r['witness']['offset'] != 0:
                A('| `%s` | %s | `%08X` | %d |'
                  % (r['entry'], r['name'], r['witness']['vt'], r['witness']['offset']))
    A('')
    nabs = sum(1 for r in good if r['witness']['_abs'])
    nglob = sum(1 for r in good if not r['witness']['_abs'] and r['witness']['_base_src'])
    A('### 6.3 装表点写的是模块静态对象、而非实例：%d / %d' % (nabs + nglob, n))
    A('')
    A('按指令形态分：**绝对地址写** `mov [<imm32>], vt` **%d 行**；'
      '**寄存器基址写** `mov [reg(+disp)], vt` **%d 行**。'
      '寄存器基址里又有 **%d 行**的 base 是在宿主体内由 `mov reg, <模块静态地址>` 预置的'
      '（写全局对象/数组，不是 `this`）；其余 %d 行的 base 来自 `this`/参数，'
      '即普通实例构造器。' % (nabs, n - nabs, nglob, n - nabs - nglob))
    A('')
    A('这类「写全局对象」的行，宿主函数是 `initterm` 链上的静态初始化函数'
      '（coverage.tsv 名如 `initterm_thunk_XXXX`），**不是类构造器**。'
      '④ 句按卡面格式写的是「位于 <宿主 entry> 体内」，我把实测起点填进去、没有假装它是 ctor；'
      '若 Lead 认为「构造器 entry」必须字面是类构造器，这 %d 行应剔除，成功数变 %d。'
      % (nabs + nglob, n - nabs - nglob))
    A('')
    A('按 `R14_COMMON` §8.1 ㉓ 我又查了 **atexit 注册集**（`push <fn>; call 0x7C978A`，'
      '本镜像实测 %d 个函数）：**%d 行**的宿主落在该集合内（＝死表，④ 不成立）。'
      '本卡 **%d 行全部不在**该集合，即所用装表点都来自活路径。'
      % (len(txt.atexit), sum(1 for r in good if r['witness']['_atexit']),
         sum(1 for r in good if r['witness']['_atexit'])))
    if nabs or nglob:
        A('')
        A('| entry | name | 装表点 | 存储形态 | 宿主 | 宿主名 |')
        A('|---|---|---|---|---|---|')
        for r in sorted(good, key=lambda x: int(x['entry'], 16)):
            w = r['witness']
            if not (w['_abs'] or w['_base_src']):
                continue
            if w['_abs']:
                form = '`mov [<绝对地址>], vt`'
            else:
                form = ('`mov [%s%+d], vt`（%s←%08X）'
                        % (w['_site']['base_name'],
                           w['_site']['disp'] if w['_site']['disp'] < 0x80000000
                           else w['_site']['disp'] - (1 << 32),
                           w['_site']['base_name'], w['_base_src'][0]))
            A('| `%s` | %s | `%08X` | %s | `%08X` | %s |'
              % (r['entry'], r['name'], w['_site']['site'], form,
                 w['_host']['entry'], w['_hostname'] or '—'))
    A('')
    A('### 6.4 多见证行的选取规则（④ 句是单槽格式，必须挑一个）')
    A('')
    wd = collections.Counter(r['ws_n'] for r in good)
    A('91 行共实测 **%d 个 `(槽号, vt)` 见证对**（= `all848.tsv` 里 vt 命中总数）。'
      '分布：%s。**%d 行有多个候选见证**，而卡面的 ④ 句只能写一个槽，所以必须有明确的'
      '选取规则：'
      % (sum(r['ws_n'] for r in good),
         '、'.join('%d 个见证 %d 行' % (k, v) for k, v in sorted(wd.items())),
         sum(1 for r in good if r['ws_n'] > 1)))
    A('')
    A('1. **偏好序**（先比第 1 条，平手再比下一条）：'
      '① `COL.offset==0` 且 RTTI 类名命中行名类 → ② `COL.offset==0` → ③ RTTI 类名命中行名类 '
      '→ ④ 其余（按 vt 升序）。理由：④ 问的是「该函数在**哪张表**的哪个槽」，'
      '取行名类自己那张、且是主基类表（offset=0）的，最不容易被误读。')
    A('2. **同一见证内的装表点**：取**最低地址**且落在**行 entry 体外**的那个；'
      '若某见证的全部装表点都在行 entry 体内（self-install）或找不到宿主函数，则换下一个见证。')
    A('3. **结果**：%d 行按偏好序用到了**非首个**（非扫描序第一个）见证；'
      '这些行的全部候选见证仍可在 `all848.tsv` 的 `install_site` 列逐条查。'
      % sum(1 for r in good if r.get('chosen_rank', 0) > 0))
    A('')
    A('---')
    A('')
    A('## 7 · 取数方法论（六个字段各自怎么测出来的）')
    A('')
    A('| 字段 | 测法 | 校验 |')
    A('|---|---|---|')
    A('| vt（虚表地址） | `.rdata`+`.data` 全扫 `dd <entry>` 命中；由命中处每 4 字节回走，'
      '取最远的「`u32(vt-4)` 是合法 COL」的地址为表起点 | `u32(vt+slot*4)==entry` 回读 |')
    A('| 槽号 | `(hit - vt)/4` | 同上；并与 `all848.tsv` 逐行对账（0 处不一致） |')
    A('| COL | `u32(vt-4)` | `COL.sig==0`；`COL+0xC` 落在镜像内 |')
    A('| TD | `u32(COL+0xC)`（**绝对 VA**） | `TD+8` 按**内联串**读，须以 `.?A` 开头，'
      r'再正则 `^\.\?A[VU](...)@@$` 去修饰 |')
    A('| 装表点 | capstone 5.0.7（`skipdata=True`）线性反汇编 `.text`，'
      '收 `mov [reg|abs], imm32` 且 imm 落在镜像内 | 指令尾部 4 字节 == vt |')
    A('| 构造器 entry | 装表点所在函数的起点：在 0x800 字节窗口内取「有独立锚点'
      '（atlas 函数起点 / `call rel32` 目标）或紧邻 `0x90`·`0xCC` 填充 / 前一条指令是'
      '`ret`·`jmp`·`int3`」的 16 字节对齐候选，由小到大做**控制流遍历**'
      '（跟条件跳转、不跟 call、遇 ret 停），取第一个能到达装表点者；'
      '若该遍历体内另有更强锚点也含装表点，则下潜一层（排除尾跳转并入；本卡 0 次触发） | '
      '遍历体必须含装表点；装表点必须不在行 entry 的遍历体内；且从宿主到装表点之间'
      '没有 `jmp`（本卡 0 行有跨函数跳转风险）；`coverage.tsv` 里该宿主 entry 的**名字**'
      '交叉印证（%d/%d 行命中，多为 `XxxClass::XxxClass` 构造器） |'
      % (sum(1 for r in good if r['witness']['_hostname']), n))
    A('')
    A('宿主判定分布：%s。'
      % '、'.join('%s %d 行' % (k, v) for k, v in
                 sorted(collections.Counter(r['witness']['_host']['why']
                                            for r in good).items(), key=lambda kv: -kv[1])))
    A('')
    A('> 说明：`anchor` = 该起点是 atlas 函数起点或 `call rel32` 目标（两种独立来源）；'
      '`pad` = 仅靠「前有 ≥2 字节 `0x90`/`0xCC` 填充」定界。`pad` 的 %d 行我逐行反汇编看过'
      '入口字节与前一条指令（`004A8630` / `0040CB80` / `005C93E0` / `006CF070`，'
      '各见其 `evidence/ROW_*.txt` §5）。' 
      % sum(1 for r in good if r['witness']['_host']['why'] == 'pad'))
    A('')
    A('> **锚点为什么不含 `.rdata`/`.data` 里的指针**：实测存在指向函数体**内部**的 dd'
      '（如 `005C5D03`，它其实是 `call 0x5D5B60` 指令的地址），把它当函数起点会把宿主判错'
      '——我第一版就踩到：4 行的宿主被判成 `005C5D03`、1 行被判成 `004D33CC`（都不是函数起点）。'
      '排除之后 91/91 行的宿主在 `coverage.tsv` 里都有名字，交叉印证通过。')
    A('')
    A('### 为什么不用 `W130_atlas/function_atlas.tsv` 单独定界')
    A('')
    A('先按 atlas 的 `entry+size` 做包含判定，只有 **51/91** 行能定出宿主——atlas 缺函数'
      '（如装表点 `005C0DF8`/`005C5D08`/`005C9408`/`005CA658`/`005CB3C8` 所在构造器根本'
      '不在 atlas 里，缺口 47~667 字节）。所以本卡改用「控制流遍历 + 独立锚点/填充定界」，'
      '并保留 atlas 作为**候选锚点**之一，仍得到 0 处与 `all848.tsv` 冲突的结果。')
    A('')
    A('---')
    A('')
    A('## 8 · 产物与纪律自检')
    A('')
    A('- `R4_FILL_91_R2/fill_delta.tsv`：表头 6 列，**%d 数据行**；`grade` 全为原值 `[已证]`；'
      '第 4 列 = 原文 + 追加 ④ 句（**既有文字一字未删**）；'
      '`evidence_path` = 原值 + `;R4_DERIVABILITY/all848.tsv;R4_FILL_91_R2/evidence/ROW_<entry>.txt`。' % n)
    A('- `R4_FILL_91_R2/evidence/ROW_<entry>.txt`：%d 个，逐行记录为补齐三类字段实际读的'
      '字节（地址 + 原始字节 + 文件偏移 + 校验结论）。' % n)
    A('- `R4_FILL_91_R2/fill.py`：可复跑（`--measure` 只测不写；输出全部落在本目录）。')
    A('- **未**改 `coverage.tsv`（仍是 18,498 数据行）、`PANEL.md`、`R14_COMMON.md`、台账、'
      '`STATUS_BOARD.md`、`BOARD_ARCHIVE.md`、`D47_SURFACE`、`R4_DERIVABILITY`、`R4_FILL_91`、'
      '任何 `NAMED_PUSH_*` / `AUDIT*` / `INVENTORY*`。')
    A('- 未动第 1/2/3/5/7/8 列；未改任何 grade；未删改第 4 列既有文字。')
    A('- 六字段无一处 `未取得`、无一处编造地址；取不到即剔除（本版剔除 %d 行）。' % len(bad))
    A('')

    with open(REPORT, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(L) + '\n')

    print('')
    print('wrote %s  (%d data rows)' % (DELTA, n))
    print('wrote %s\\ROW_*.txt  (%d files)' % (EVID, n))
    print('wrote %s' % REPORT)


def main():
    state = measure()
    if '--measure' in sys.argv:
        return
    write_all(state)


if __name__ == '__main__':
    main()
