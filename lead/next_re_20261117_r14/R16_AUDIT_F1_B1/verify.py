# -*- coding: utf-8 -*-
"""R16-AUDIT-F1-B1 · F1 缺口 ④ 补写批次 1 独立审计（只读）

审计对象 : lead\\next_re_20261117_r14\\R16_F1_B1\\{delta.tsv, fields.tsv, REPORT.md}
产出      : bytecheck.tsv / tables.md / verify_out.json（本目录，不写别处）
纪律      : gamemd.exe、coverage.tsv、PROBE_4GAP、R16_F1_B1 全部 **只读** 打开；
            不 import 执行器脚本、不读 scan_raw.json / verify_summary.json 作判据。

方法（本脚本自己实现，非调用执行器）:
  * PE32 自解析：按节表做 VA → 节内偏移映射（不假设 IB+rva 线性）。
  * RTTI：u32(vt-4)=COL（绝对 VA）→ u32(COL)==0 签名 → u32(COL+12)=TD → cstr(TD+8) 内联装饰名。
  * 装表点：capstone 5.0.7 CS_ARCH_X86/CS_MODE_32 detail+skipdata 线性反汇编 .text，
            收 `mov <mem>, imm32`（imm 落在镜像内）为装表候选；站点处另做定点重解码。
  * 表枚举：在 .rdata/.data 扫 4 字节对齐 dd entry，命中点往回走表起点（COL 校验），
            得 slot=(hit-vt)/4，保留 u32(vt+slot*4)==entry 者 —— 用于 §C「同槽多表」独立计数。
  * 函数体：lead\\next_re_20261112_r10\\W130_atlas\\function_atlas.tsv（entry→size），
            用于判「装表点在 entry 体外」与「站点宿主函数」。另做独立旁证：site 是否落在
            entry 的 atlas 体内、site 与 entry 的字节距离、宿主函数首指令形态。

跑法: python verify.py            # 全流程，写 3 个产物并打印汇总
      python verify.py --quiet    # 只写产物
"""
import io
import os
import re
import sys
import json
import hashlib
import collections

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(R14))

COV = os.path.join(R14, 'COVERAGE', 'coverage.tsv')
EXE = os.path.join(ROOT, 'ra2youli', 'gamemd.exe')
ATLAS = os.path.join(ROOT, 'lead', 'next_re_20261112_r10', 'W130_atlas',
                     'function_atlas.tsv')
SCAN4GAP = os.path.join(R14, 'R16_PROBE_4GAP', 'scan_F1_audit.tsv')
EXEC = os.path.join(R14, 'R16_F1_B1')
DELTA = os.path.join(EXEC, 'delta.tsv')
FIELDS = os.path.join(EXEC, 'fields.tsv')

OUT_BYTECHECK = os.path.join(HERE, 'bytecheck.tsv')
OUT_TABLES = os.path.join(HERE, 'tables.md')
OUT_JSON = os.path.join(HERE, 'verify_out.json')

EXPECT_SHA = '73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476'
IMAGE_BASE = 0x400000
TEXT_LO, TEXT_HI = 0x401000, 0x7E038D
WITNESS = '④ 活表槽位见证'

# B1 = 派生集合按 entry 升序第 1–18 行（执行器 REPORT §1 自述；本脚本独立复算比对）
EXPECT_B1 = ['00421730', '00428EA0', '004370C0', '004684E0', '00491210',
             '004A7C90', '004AF720', '004B6470', '004C5A30', '004C5AC0',
             '004F45B0', '00524D70', '0054DC60', '005550C0', '00555110',
             '00555150', '005F44A0', '005F9950']
# §C 指定主题的两行
TOPIC_ROWS = ['004F45B0', '005F44A0']

TPL_HEAD = ('④ 活表槽位见证：{CLS}::slot{N}（vt={VT}，槽 {N} 值={E}，COL={COL} '
            'offset={OFF}，RTTI={TD}→{M}；装表点 {SITE} 位于 {HOST} 体内，entry 体外）'
            ' ④升级句：{CLS}::slot{N}（④ 表属类与行名类一致，均为 {CLS}；'
            '该槽即其 vt={VT} 表 slot{N}，无归属歧义）')
DISCLOSE = ('（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，'
            '见 R14_COMMON §12.6 与 PANEL 对应披露）')


# --------------------------------------------------------------------- 基础 IO
def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest().upper()


def text_lines(path):
    """原样按行读（保留列内字符），只去行尾 CR/LF。"""
    with io.open(path, encoding='utf-8-sig', newline='') as f:
        return [ln.rstrip('\r\n') for ln in f]


def load_tsv(path):
    lines = text_lines(path)
    hdr = lines[0].split('\t')
    out = []
    for ln in lines[1:]:
        if not ln.strip():
            continue
        out.append(ln.split('\t'))
    return hdr, out


# ------------------------------------------------------------------ PE 底图
class Pe(object):
    """只读 PE32 映射：VA -> 节内偏移（按节表，不用 IB+rva 线性假设）。"""

    def __init__(self, path):
        import pefile
        self.pe = pefile.PE(path, fast_load=True)
        self.base = self.pe.OPTIONAL_HEADER.ImageBase
        self.size_of_image = self.pe.OPTIONAL_HEADER.SizeOfImage
        self.secs = []
        for s in self.pe.sections:
            nm = s.Name.rstrip(b'\x00').decode('latin-1')
            self.secs.append(dict(name=nm,
                                  va=self.base + s.VirtualAddress,
                                  vsize=s.Misc_VirtualSize,
                                  rsize=s.SizeOfRawData,
                                  data=s.get_data()))

    def sec(self, va):
        for s in self.secs:
            if s['va'] <= va < s['va'] + max(s['vsize'], s['rsize']):
                return s
        return None

    def sec_of(self, va):
        s = self.sec(va)
        return s['name'] if s else None

    def _loc(self, va, n):
        s = self.sec(va)
        if s is None:
            return None
        off = va - s['va']
        if off + n > len(s['data']):
            return None
        return s['data'], off

    def u32(self, va):
        r = self._loc(va, 4)
        if r is None:
            return None
        d, o = r
        return int.from_bytes(d[o:o + 4], 'little')

    def cstr(self, va, n=256):
        r = self._loc(va, 1)
        if r is None:
            return None
        d, o = r
        e = d.find(b'\x00', o, min(o + n, len(d)))
        if e < 0:
            return None
        return d[o:e].decode('latin-1')

    def in_image(self, va):
        return va is not None and self.base <= va < self.base + self.size_of_image


def col_of(img, vt):
    """vt-4 = COL(绝对 VA)；COL 签名 0；COL+12 = TD；TD+8 内联装饰名以 .?A 开头。"""
    col = img.u32(vt - 4)
    if not img.in_image(col):
        return None
    if img.u32(col) != 0:
        return None
    td = img.u32(col + 12)
    if not img.in_image(td):
        return None
    nm = img.cstr(td + 8)
    if not nm or not nm.startswith('.?A'):
        return None
    return dict(col=col, td=td, mangled=nm, off=img.u32(col + 4),
                cd=img.u32(col + 8), pchd=img.u32(col + 16))


def vtable_start(img, hit, max_walk=0x2000):
    """从 hit 往回 ×4 步进，取走得最远的合法表起点（越过起点后 COL 校验必失败）。"""
    best = None
    k = 0
    while k * 4 <= max_walk:
        v = hit - k * 4
        if v <= img.base + 4:
            break
        if img.sec(v) is None or img.sec(v - 4) is None:
            k += 1
            continue
        c = col_of(img, v)
        if c is not None:
            best = (v, c)
        elif best is not None:
            break
        k += 1
    return best


# --------------------------------------------------------------- .text 反汇编
class TextScan(object):

    def __init__(self, img):
        import capstone
        self.cs = capstone
        self.X = capstone.x86
        s = [x for x in img.secs if x['name'] == '.text'][0]
        n = min(len(s['data']), s['vsize'] or len(s['data']), TEXT_HI - s['va'])
        self.lo = s['va']
        self.code = bytes(s['data'][:n])
        self.hi = self.lo + len(self.code)
        self.stores = collections.defaultdict(list)   # imm -> [(site, disp_base, disp)]
        self.at = {}                                  # site -> insn 摘要
        self.n_insn = 0
        self.n_skip = 0
        md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
        md.detail = True
        md.skipdata = True
        X = self.X
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
                        bn = insn.reg_name(a.mem.base)
                        self.stores[imm].append((insn.address, bn,
                                                 a.mem.disp & 0xFFFFFFFF))
                        if len(self.at) < 4000000:
                            self.at[insn.address] = insn.op_str

    def decode_at(self, site):
        """定点重解码（线性 sweep 可能 skipdata 错位，判 B⑥ 必须定点）。"""
        off = site - self.lo
        if off < 0 or off >= len(self.code):
            return None
        md = self.cs.Cs(self.cs.CS_ARCH_X86, self.cs.CS_MODE_32)
        md.detail = True
        for insn in md.disasm(self.code[off:off + 16], site):
            return insn
        return None

    def install_sites(self, vt):
        return [t for t in self.stores.get(vt, [])]


def scan_dd_align(img, value, secnames=('.rdata', '.data')):
    """在指定节里扫 4 字节对齐的 dd value。"""
    hits = []
    pat = value.to_bytes(4, 'little')
    for s in img.secs:
        if s['name'] not in secnames:
            continue
        d = s['data']
        i = d.find(pat)
        while i >= 0:
            if i % 4 == 0:
                hits.append(s['va'] + i)
            i = d.find(pat, i + 1)
    return hits


def load_atlas():
    out = {}
    if not os.path.isfile(ATLAS):
        return out
    for i, ln in enumerate(text_lines(ATLAS)):
        if i == 0:
            continue
        c = ln.split('\t')
        if len(c) < 2:
            continue
        try:
            out[c[0].strip().upper()] = int(c[1])
        except ValueError:
            continue
    return out


def body_of(atlas, entry):
    n = atlas.get(entry)
    if not n:
        return None
    return (int(entry, 16), int(entry, 16) + n)


def which_body(ranges, va):
    import bisect
    i = bisect.bisect_right(ranges, (va, 1 << 62)) - 1
    while i >= 0:
        s, e = ranges[i]
        if s <= va < e:
            return s
        if e <= va:
            return None
        i -= 1
    return None


# ------------------------------------------------------------------ 名字口径
def split_name(name):
    cls, _, meth = name.rpartition('::')
    m = re.search(r'slot(\d+)', meth, re.I)
    return cls, (int(m.group(1)) if m else None)


def ring4_site(s):
    """从 scan_F1_audit.tsv 的 ring4_at 散文里取主站点绝对 VA。"""
    s = s.strip()
    if not s:
        return None
    m = re.match(r'ctor\s+([0-9A-Fa-f]{8})\s*:\s*([0-9A-Fa-f]{8})\s+mov', s)
    if m:
        return m.group(2).upper()
    m = re.search(r'@([0-9A-Fa-f]{8})\b', s)
    if m:
        return m.group(1).upper()
    m = re.match(r'^([0-9A-Fa-f]{8})$', s)
    if m:
        return m.group(1).upper()
    return None


# ------------------------------------------------------------ ④ 文本字段提取
RE_HEAD = re.compile(
    r'活表槽位见证：([^\s（:]+)::slot(\d+)（vt=([0-9A-F]{8})，槽 (\d+) 值=([0-9A-F]{8})，'
    r'COL=([0-9A-F]{8}) offset=(\d+)，RTTI=([0-9A-F]{8})→([^；]+?)；'
    r'装表点 ([0-9A-F]{8}) 位于 ([0-9A-F]{8}) 体内，entry 体外）')
RE_UP = re.compile(
    r'④升级句：([^\s（:]+)::slot(\d+)（④ 表属类与行名类一致，均为 ([^\s；]+)；'
    r'该槽即其 vt=([0-9A-F]{8}) 表 slot(\d+)，无归属歧义）')


def parse_witness(col4):
    d = {}
    t = col4
    i = t.find(WITNESS)
    if i < 0:
        return None
    tail = t[i:]
    m = RE_HEAD.search(tail)
    if m:
        d.update(cls=m.group(1), slot=int(m.group(2)), vt=m.group(3),
                 slot2=int(m.group(4)), entry=m.group(5), col=m.group(6),
                 off=int(m.group(7)), td=m.group(8), mangled=m.group(9),
                 site=m.group(10), host=m.group(11))
    m = RE_UP.search(tail)
    if m:
        d.update(up_cls=m.group(1), up_slot=int(m.group(2)),
                 up_same=m.group(3), up_vt=m.group(4), up_slot2=int(m.group(5)))
    d['text'] = tail
    d['head_ok'] = bool(RE_HEAD.search(tail))
    d['up_ok'] = bool(RE_UP.search(tail))
    return d


def indep_entry_body(ts, entry, maxlen=0x1000):
    """不靠 atlas 的 entry 函数体上界。

    本镜像的函数间填充是 **0x90(NOP)** 而不是 0xCC（实测），故取
    「首个 ≥4 连续 0x90」处为上界，并要求该处紧跟在 `ret` 之后（`C3 90 90 ..`）。
    用于独立复核「装表点在 entry 体外」。
    """
    off = entry - ts.lo
    if off < 0 or off >= len(ts.code):
        return None
    blob = ts.code[off:off + maxlen]
    ends = []
    for i in range(2, len(blob) - 6):
        if blob[i] in (0xC3, 0xC2):
            j = i + (3 if blob[i] == 0xC2 else 1)
            if blob[j:j + 4] == b'\x90\x90\x90\x90':
                ends.append(entry + j)
                break
    return ends[0] if ends else None


def indep_func_start_before(ts, va, back=0x4000):
    """site 之前最近一次「ret 后接 NOP 填充」之后的首字节 = 含 site 的函数起点。

    本镜像函数间填充为 `C3 90 90 ..`（NOP），故取「ret(+NOP run)」后第一条指令地址。
    返回的是下界意义上最贴近的候选；与 atlas 宿主交叉核对（见 main 的 8b2）。
    """
    off = va - ts.lo
    if off <= 0 or off > len(ts.code):
        return None
    lo = max(0, off - back)
    blob = ts.code[lo:off]
    best = None
    for i in range(len(blob) - 1):
        if blob[i] not in (0xC3, 0xC2):
            continue
        j = i + (3 if blob[i] == 0xC2 else 1)
        if j >= len(blob) or blob[j] != 0x90:
            continue
        while j < len(blob) and blob[j] == 0x90:
            j += 1
        best = ts.lo + lo + j
    return best


def vtable_len(img, vt, cap=2048):
    """表槽数 = 从 vt 起连续「落在 .text 内的 4 字节指针」的个数。

    比「找下一个表起点」更稳：表尾通常接 0/非代码数据，而 COL 校验在表外会出现
    偶发假阳性（实测 007EC258 在 +609 槽处就有一次假阳性）。
    """
    n = 0
    while n < cap:
        v = img.u32(vt + n * 4)
        if v is None or not (TEXT_LO <= v < TEXT_HI):
            break
        n += 1
    return n


def secondary_same_td(img, vt, td, cap=400):
    """同 TD（同装饰名）的相邻次表：清点 vt 之前紧邻的、共 TD 的短表及其槽数。

    用途：§C 的「同槽类一致表数」若把主表之外的次表也算进来，是否可能多出候选。
    """
    out = []
    k = 1
    while k <= 32:
        v = vt - k * 4
        c = col_of(img, v)
        if c is not None:
            if c['td'] == td:
                out.append(dict(vt=v, col=c['col'], td=c['td'],
                                mangled=c['mangled'], slots=vtable_len(img, v)))
            break
        k += 1
    return out


def raw_hex(img, va, n=16):
    s = img.sec(va)
    if s is None:
        return None
    off = va - s['va']
    if off < 0 or off + n > len(s['data']):
        return None
    return ' '.join('%02X' % b for b in s['data'][off:off + n])


def norm_text(s):
    """entry 归一：8 位十六进制 -> <HEX>。"""
    return re.sub(r'[0-9A-F]{8}', '<HEX>', s)


def precedent_selfcheck(cov):
    """用盘上 3 条既有「④ 活表槽位见证」先例反推并自校 TPL_HEAD 骨架。

    做法：把先例正文里**它自己的**取值代回 TPL_HEAD，若逐字符重现先例原文，
    则说明本审计用的骨架 = 盘上先例骨架（不是自造模板）。
    """
    out = {}
    for e in ('00464AC0', '004DE630', '004F42F0'):
        cr = cov.get(e)
        if cr is None:
            out[e] = dict(ok=False, why='missing')
            continue
        w = parse_witness(cr[3])
        if not w or not w.get('head_ok') or not w.get('up_ok'):
            out[e] = dict(ok=False, why='parse_fail')
            continue
        exp = TPL_HEAD.format(CLS=w['cls'], N=w['slot'], VT=w['vt'],
                              E=w['entry'], COL=w['col'], OFF=w['off'],
                              TD=w['td'], M=w['mangled'],
                              SITE=w['site'], HOST=w['host'])
        out[e] = dict(ok=(w['text'].rstrip() == exp),
                      has_126=('§12.6' in w['text']),
                      why='' if w['text'].rstrip() == exp else 'skeleton_diff')
    return out


def witness_tail_check(cov):
    """已并表的 R16_SLOTN_B1/B3 行：其 ④ 段尾是否与本批同一条 D-47 披露句。"""
    out = dict(checked=0, with_witness=0, tail_exact=0, tails={}, joins={})
    for grp in ('R16_SLOTN_B1', 'R16_SLOTN_B3'):
        p = os.path.join(R14, grp, 'delta.tsv')
        if not os.path.isfile(p):
            continue
        for c in load_tsv(p)[1]:
            e = c[0].strip().upper()
            out['checked'] += 1
            cr = cov.get(e)
            if cr is None or WITNESS not in cr[3]:
                continue
            out['with_witness'] += 1
            t = cr[3][cr[3].find(WITNESS):].rstrip()
            tail = t[len(t) - len(DISCLOSE):] if len(t) >= len(DISCLOSE) else t
            out['tails'][tail] = out['tails'].get(tail, 0) + 1
            if t.endswith(DISCLOSE):
                out['tail_exact'] += 1
            i = cr[3].find(WITNESS)
            j = cr[3][i - 1:i + 1]
            out['joins'][j] = out['joins'].get(j, 0) + 1
    return out


# ------------------------------------------------------------------------ main
def main():
    quiet = '--quiet' in sys.argv
    log = []

    def say(*a):
        s = ' '.join(str(x) for x in a)
        log.append(s)
        if not quiet:
            print(s)

    # ---- 0. 基线 sha
    sha_exe = sha256(EXE)
    sha_cov = sha256(COV)
    sha_delta = sha256(DELTA)
    size_cov = os.path.getsize(COV)
    say('[0] gamemd.exe sha=%s  cov sha=%s (%d B)  delta sha=%s' %
        (sha_exe, sha_cov, size_cov, sha_delta))

    img = Pe(EXE)
    ts = TextScan(img)
    atlas = load_atlas()
    ranges = sorted((int(k, 16), int(k, 16) + v)
                    for k, v in atlas.items() if v)
    say('[0] .text 反汇编 %d 条 / skip %d ; atlas 函数体 %d 条' %
        (ts.n_insn, ts.n_skip, len(ranges)))

    # ---- 1. 输入
    cov_hdr, cov_rows = load_tsv(COV)
    cov = {c[0].strip().upper(): c for c in cov_rows}
    say('[1] coverage.tsv 列数 %d，数据行 %d（entry 唯一）' % (len(cov_hdr), len(cov_rows)))

    dhdr, drows = load_tsv(DELTA)
    fhdr, frows = load_tsv(FIELDS)
    fields = {c[0].strip().upper(): c for c in frows}
    fi = {n: i for i, n in enumerate(fhdr)}

    scan_hdr, scan_rows = load_tsv(SCAN4GAP)
    si = {n: i for i, n in enumerate(scan_hdr)}
    scan = {c[si['entry']].strip().upper(): c for c in scan_rows}

    # ---- 1b. §E 先例骨架自校 + 已并表行披露尾一致性
    prec = precedent_selfcheck(cov)
    say('[1b] 先例骨架自校: %s' % {k: v['ok'] for k, v in prec.items()})
    wtail = witness_tail_check(cov)
    say('[1b] 已并表 SLOTN 行：核 %d 行，其中带 ④ 见证 %d 行，尾披露逐字相同 %d 行；'
        '尾串分布 %s；④ 前一字分布 %s'
        % (wtail['checked'], wtail['with_witness'],
           wtail['tail_exact'],
           {k[-24:]: v for k, v in wtail['tails'].items()},
           wtail['joins']))
    say('[1c] coverage 表头: %s' % cov_hdr)

    # ---- 2. 独立复现派生集合（卡面 §2 四判据 + ③ 干净）
    derived = []
    reject = collections.Counter()
    for c in scan_rows:
        e = c[si['entry']].strip().upper()
        ss = c[si['same_source']].strip()
        dec = c[si['n_install_decoded']].strip()
        outside = c[si['n_install_outside_body']].strip()
        sem = c[si['sem_unproved']].strip()
        ok = True
        if ss != 'no':
            reject['same_source!=no'] += 1
            ok = False
        if dec in ('', '0'):
            reject['no_install_decoded'] += 1
            ok = False
        if outside in ('', '0'):
            reject['no_install_outside_body'] += 1
            ok = False
        if sem not in ('', '0'):
            reject['sem_unproved'] += 1
            ok = False
        cr = cov.get(e)
        if cr is None:
            reject['not_in_cov'] += 1
            ok = False
        else:
            if cr[4].strip() != '[已证]':
                reject['grade_not_proved'] += 1
                ok = False
            if WITNESS in cr[3]:
                reject['already_has_witness'] += 1
                ok = False
        if ok:
            derived.append(e)
    derived.sort(key=lambda x: int(x, 16))
    say('[2] 派生集合 %d 行（卡面预期 76）; 拒绝计次 %s' %
        (len(derived), dict(reject)))

    b1_derived = derived[:18]
    b1_delta = [c[0].strip().upper() for c in drows]
    set_ok = (b1_derived == b1_delta == EXPECT_B1)
    say('[2] B1 切片 = delta entry 序列 = 卡面 B1 18 行 ? %s' % set_ok)
    if not set_ok:
        say('    derived[:18]=%s' % b1_derived)
        say('    delta     =%s' % b1_delta)

    # ---- 3. 逐行审计
    results = []
    tables_md = []
    for row in drows:
        e = row[0].strip().upper()
        if e not in cov:
            results.append(dict(entry=e, fatal='entry 不在 coverage.tsv'))
            continue
        cr = cov[e]
        name = cr[2].strip()
        cls, slot = split_name(name)
        f = fields.get(e)
        r = dict(entry=e, name=name, cls=cls, slot=slot, checks={}, notes=[],
                 fail=[], nit=[])

        # ---------- §A 最小改动与原文保全
        a_ok = True
        if len(row) != 8:
            r['fail'].append('§A 列数=%d' % len(row))
            a_ok = False
        if not row[3].startswith(cr[3]):
            r['fail'].append('§A 第4列非原第4列严格前缀')
            a_ok = False
        diff_cols = []
        for k in (0, 1, 2, 4, 5, 6, 7):
            if k >= len(row):
                diff_cols.append(k + 1)
                continue
            if row[k].encode('utf-8') != cr[k].encode('utf-8'):
                diff_cols.append(k + 1)
        if diff_cols:
            r['fail'].append('§A 列 %s 与盘上不同' % diff_cols)
            a_ok = False
        r['checks']['A_prefix'] = row[3].startswith(cr[3])
        r['checks']['A_cols'] = not diff_cols
        r['appended'] = row[3][len(cr[3]):]
        r['orig4'] = cr[3]
        r['grade'] = cr[4]

        # ---------- ④ 文本解析
        w = parse_witness(row[3])
        r['w'] = w
        if not w:
            r['fail'].append('§D 第4列无「%s」段' % WITNESS)
        else:
            if not w['head_ok']:
                r['fail'].append('§D ④ 见证句骨架不可解析')
            if not w['up_ok']:
                r['fail'].append('§D ④升级句骨架不可解析')

        # 所选表：优先取 ④ 正文自述，再与 fields.tsv 交叉
        sel_vt = w['vt'] if w and w.get('vt') else (
            f[fi['vtaddr']].strip().upper() if f else None)
        sel_site = w['site'] if w and w.get('site') else (
            f[fi['install_site']].strip().upper() if f else None)
        sel_col = w['col'] if w and w.get('col') else None
        sel_td = w['td'] if w and w.get('td') else None
        sel_off = w['off'] if w and w.get('off') is not None else None
        r['sel'] = dict(vt=sel_vt, site=sel_site, col=sel_col, td=sel_td,
                        off=sel_off)
        if f:
            fvt = f[fi['vtaddr']].strip().upper()
            fsite = f[fi['install_site']].strip().upper()
            if sel_vt and fvt != sel_vt:
                r['fail'].append('§D 正文 vt=%s 与 fields.tsv=%s 不一致' % (sel_vt, fvt))
            if sel_site and fsite != sel_site:
                r['fail'].append('§D 正文 site=%s 与 fields.tsv=%s 不一致' % (sel_site, fsite))
            r['fields'] = dict(vt=fvt, site=fsite,
                               col=f[fi['coladdr']].strip().upper(),
                               off=f[fi['col_offset']].strip(),
                               td=f[fi['rtti_addr']].strip().upper(),
                               mangled=f[fi['rtti_mangled']].strip(),
                               host=f[fi['install_func']].strip().upper(),
                               same_source=f[fi['same_source']].strip(),
                               status=f[fi['status(OK|SKIP)']].strip())

        # ---------- §B 8 项独立复算
        vt = int(sel_vt, 16) if sel_vt else None
        entry = int(e, 16)
        site = int(sel_site, 16) if sel_site else None
        # B1
        v_slot = img.u32(vt + slot * 4) if vt else None
        r['checks']['B1'] = (v_slot == entry)
        # B2
        v_col = img.u32(vt - 4) if vt else None
        r['checks']['B2'] = (v_col is not None and sel_col is not None
                             and v_col == int(sel_col, 16))
        # B3
        v_off = img.u32(v_col + 4) if v_col else None
        r['checks']['B3'] = (v_off is not None and sel_off is not None
                             and v_off == sel_off)
        # B4
        v_td = img.u32(v_col + 12) if v_col else None
        r['checks']['B4'] = (v_td is not None and sel_td is not None
                             and v_td == int(sel_td, 16))
        # B5
        v_m = img.cstr(v_td + 8) if v_td else None
        r['checks']['B5'] = (v_m is not None and w is not None
                             and v_m == w.get('mangled'))
        # B6 定点重解码: mov <mem>, imm32 且 imm==vt
        insn = ts.decode_at(site) if site else None
        X = ts.X
        b6 = False
        site_desc = None
        if insn is not None and insn.mnemonic == 'mov' and len(insn.operands) == 2:
            a, b = insn.operands
            if (a.type == X.X86_OP_MEM and b.type == X.X86_OP_IMM
                    and (b.imm & 0xFFFFFFFF) == vt):
                b6 = True
                site_desc = 'mov %s, %s' % (insn.op_str.split(',')[0].strip(),
                                            hex(vt))
        r['checks']['B6'] = b6
        r['site_desc'] = site_desc
        r['insn'] = ('%08X: %s %s' % (site, insn.mnemonic, insn.op_str)
                     if insn is not None else None)
        # B7 装表点所在函数 != entry
        host_atlas = which_body(ranges, site) if site else None
        eb = body_of(atlas, e)
        site_in_entry_body = bool(eb and eb[0] <= site < eb[1])
        r['checks']['B7'] = (site is not None and site != entry
                             and not site_in_entry_body
                             and (host_atlas is None or host_atlas != entry))
        r['host_atlas'] = ('%08X' % host_atlas) if host_atlas else None
        r['entry_body'] = ('[%08X,%08X)' % eb) if eb else None
        r['site_in_entry_body'] = site_in_entry_body
        # 旁证：宿主函数体是否把 entry 也吞进去（atlas 合并块会让 B7 假阳）
        hb = body_of(atlas, '%08X' % host_atlas) if host_atlas else None
        r['host_body'] = ('[%08X,%08X)' % hb) if hb else None
        r['entry_in_host_body'] = bool(hb and hb[0] <= entry < hb[1])
        r['site_off_from_entry'] = (site - entry) if site else None
        # B7 独立旁证（不靠 atlas）
        ib = indep_entry_body(ts, entry) if site else None
        r['indep_body'] = ('[%08X,%08X)' % (entry, ib)) if ib else None
        ifb = indep_func_start_before(ts, site) if site else None
        r['indep_func_start'] = ('%08X' % ifb) if ifb else None
        # atlas 尺寸旁证：atlas 体尾之后是否紧跟 NOP 填充（体尾字节 +1 处是 0x90）
        if eb:
            r['atlas_end_pad'] = raw_hex(img, eb[1], 4)
            r['atlas_end_pad_ok'] = (r['atlas_end_pad'] or '').startswith('90')
            nop_run = 0
            # 单字节取法
            s = img.sec(eb[1])
            if s is not None:
                o = eb[1] - s['va']
                while o + nop_run < len(s['data']) and s['data'][o + nop_run] == 0x90:
                    nop_run += 1
            r['atlas_end_nop_run'] = nop_run
        else:
            r['atlas_end_pad'] = None
            r['atlas_end_pad_ok'] = None
            r['atlas_end_nop_run'] = None
        b7i = False
        if site is not None:
            if site < entry:
                # entry 本身是函数起点 ⇒ 没有函数能跨过它；site 在 entry 之前 ⇒ 必属另一函数
                b7i = True
            elif ib is not None and site >= ib:
                b7i = True
            if ifb is not None and ifb > entry:
                b7i = True
            if site == entry:
                b7i = False
        r['checks']['B7_indep'] = b7i
        # B8 TD+8 类名与行名前缀同类（精确装饰名）
        want_m = '.?AV%s@@' % cls
        r['checks']['B8'] = (v_m == want_m)
        r['want_mangled'] = want_m

        # ---------- §C 同槽多表独立枚举（全 18 行都做，重点行展开）
        cand = []
        for hit in scan_dd_align(img, entry):
            st = vtable_start(img, hit)
            if not st:
                continue
            cvt, cinfo = st
            if (hit - cvt) % 4:
                continue
            cslot = (hit - cvt) // 4
            if img.u32(cvt + cslot * 4) != entry:
                continue
            cand.append(dict(vt=cvt, slot=cslot, col=cinfo['col'],
                             td=cinfo['td'], mangled=cinfo['mangled'],
                             installs=[t[0] for t in ts.install_sites(cvt)]))
        # 同槽（行名槽号）持有的表
        same_slot = [c for c in cand if c['slot'] == slot]
        same_slot.sort(key=lambda c: c['vt'])
        r['n_cand_all_slot'] = len(cand)
        r['n_same_slot'] = len(same_slot)
        r['n_same_slot_live'] = len([c for c in same_slot if c['installs']])
        r['tables'] = same_slot
        cs_cls = ['.?AV%s@@' % cls]
        class_consistent = [c for c in same_slot if c['mangled'] in cs_cls]
        r['n_class_consistent'] = len(class_consistent)
        r['same_slot_classes'] = sorted({c['mangled'] for c in same_slot})
        # 所选表落在候选里？
        r['chosen_in_same_slot'] = any(vt and c['vt'] == vt for c in same_slot)
        # 归属健全性：所选表槽数必须 > 槽号；且 vt 之前不能再是另一张表起点
        # （否则「回走取表起点」可能越过紧邻的短表而误归属）
        r['chosen_slots'] = vtable_len(img, vt) if vt else None
        r['slot_in_range'] = bool(r['chosen_slots'] and r['chosen_slots'] > slot)
        r['prev_not_table'] = (col_of(img, vt - 4) is None) if vt else False
        for c in same_slot:
            c['slots'] = vtable_len(img, c['vt'])
        r['cands_slot_in_range'] = all(
            (c['slots'] or 0) > slot for c in same_slot)        # 站点是否只落在所选表
        site_val = int(sel_site, 16) if sel_site else None
        r['site_only_on_chosen'] = bool(
            site_val is not None and any(
                site_val in c['installs'] for c in same_slot if c['vt'] == vt)
            and not any(site_val in c['installs']
                        for c in same_slot if c['vt'] != vt))
        # ring4_at 主站点一致性
        rr = scan.get(e)
        r4 = ring4_site(rr[si['ring4_at']]) if rr else None
        r['ring4'] = r4
        r['checks']['C_ring4'] = (r4 is not None and sel_site is not None
                                  and r4 == sel_site)

        # ---------- §D 文本与事实一致
        d_ok = True
        if w and w.get('head_ok'):
            if w['cls'] != cls:
                r['fail'].append('§D ④ 正文类 %s ≠ 行名类 %s' % (w['cls'], cls))
                d_ok = False
            if w['slot'] != slot or w['slot2'] != slot:
                r['fail'].append('§D ④ 正文槽号/槽值槽号 ≠ 行名槽 %d' % slot)
                d_ok = False
            if w['entry'] != e:
                r['fail'].append('§D ④ 正文「槽 N 值」≠ entry')
                d_ok = False
            if sel_vt and w['vt'] != sel_vt:
                d_ok = False
            if v_col is not None and w['col'] != '%08X' % v_col:
                r['fail'].append('§D COL 文本 ≠ 实测 u32(vt-4)')
                d_ok = False
            if v_off is not None and w['off'] != v_off:
                r['fail'].append('§D offset 文本 ≠ 实测 u32(COL+4)')
                d_ok = False
            if v_td is not None and w['td'] != '%08X' % v_td:
                r['fail'].append('§D RTTI 文本 ≠ 实测 u32(COL+12)')
                d_ok = False
            if v_m is not None and w['mangled'] != v_m:
                r['fail'].append('§D 装饰名文本 ≠ 实测 cstr(TD+8)')
                d_ok = False
            if site_val is not None and w['site'] != sel_site:
                d_ok = False
            if host_atlas is not None and w['host'] != '%08X' % host_atlas:
                r['fail'].append('§D 宿主 %s ≠ atlas 实测 %08X'
                                 % (w['host'], host_atlas))
                d_ok = False
        if w and w.get('up_ok'):
            if w['up_cls'] != cls or w['up_same'] != cls:
                r['fail'].append('§D ④升级句类名 ≠ 行名类')
                d_ok = False
            if w['up_slot'] != slot or w['up_slot2'] != slot:
                r['fail'].append('§D ④升级句槽号 ≠ 行名槽')
                d_ok = False
            if sel_vt and w['up_vt'] != sel_vt:
                r['fail'].append('§D ④升级句 vt ≠ ④ 见证 vt')
                d_ok = False
        txt = row[3]
        r['has_126'] = '§12.6' in txt
        r['has_124'] = '§12.4' in txt
        r['per_row_disclose'] = DISCLOSE in txt
        if not r['has_126']:
            r['fail'].append('§D 缺 §12.6 披露指针')
            d_ok = False
        if r['has_124']:
            r['fail'].append('§D 出现 §12.4（错节号）')
            d_ok = False
        if 'D-47(A)' not in txt:
            r['fail'].append('§D 缺 D-47(A) 字样')
            d_ok = False
        if 'PANEL' not in txt:
            r['fail'].append('§D 缺 PANEL 对应披露指针（§12.6 引用纪律要求）')
            d_ok = False
        # §D 强校验：追加段内出现的每一个 8 位 hex 令牌都必须是实测地址之一
        allowed = {e, '%08X' % vt if vt else '', '%08X' % v_col if v_col else '',
                   '%08X' % v_td if v_td else '', sel_site or '',
                   ('%08X' % host_atlas) if host_atlas else ''}
        allowed = {a.upper() for a in allowed if a}
        toks = set(t.upper() for t in re.findall(r'[0-9A-F]{8}', r['appended']))
        extra = sorted(toks - allowed)
        r['hex_tokens_ok'] = not extra
        r['hex_extra'] = extra
        if extra:
            r['fail'].append('§D 追加段含未验证地址 %s' % extra)
            d_ok = False
        r['checks']['D'] = d_ok

        # ---------- §E 格式合先例（骨架逐字符模板比对）
        # 模板 TPL_HEAD 由盘上 3 条先例反推并逐字符自校（见 precedent_skeleton_ok）
        if w and w.get('head_ok'):
            expect_full = TPL_HEAD.format(CLS=cls, N=slot, VT=sel_vt, E=e,
                                          COL=w['col'], OFF=w['off'],
                                          TD=w['td'], M=w['mangled'],
                                          SITE=sel_site, HOST=w['host'])
            r['e_head_exact'] = (w['text'] == expect_full + DISCLOSE)
            r['e_head_tail'] = w['text'][len(expect_full):] if r['e_head_exact'] else w['text'][-80:]
            # 追加段首字符
            r['append_first'] = r['appended'][:1]
            # 分隔：原第4列末尾字符 + 追加首字符
            r['join'] = (r['orig4'][-1:] or '') + r['append_first']
            e_ok = r['e_head_exact']
        else:
            r['e_head_exact'] = False
            e_ok = False
        r['checks']['E'] = e_ok

        results.append(r)

    # ---------- §F 反抄袭
    bodies = [r['appended'] for r in results if r.get('appended')]
    uniq_raw = len(set(bodies)) == len(bodies)
    nb = [norm_text(b) for b in bodies]
    uniq_norm = len(set(nb)) == len(nb)
    dup_norm = [k for k, v in collections.Counter(nb).items() if v > 1]
    # 四字段多样性
    div = dict(
        vt=len({r['w'].get('vt') for r in results if r.get('w')}),
        slot=len({r['slot'] for r in results}),
        cls=len({r['cls'] for r in results}),
        site=len({r['sel'].get('site') for r in results}),
        host=len({r['host_atlas'] for r in results}),
    )
    for r in results:
        r['checks']['F'] = (uniq_raw and uniq_norm)

    # ---------- fields.tsv 完整性旁证
    f_int = dict(rows=len(frows), cols=len(fhdr),
                 same_source_all_no=all(
                     f[fi['same_source']].strip() == 'no' for f in frows),
                 status_all_ok=all(
                     f[fi['status(OK|SKIP)']].strip() == 'OK' for f in frows),
                 entry_set_eq=([f[0].strip().upper() for f in frows] ==
                               [c[0].strip().upper() for c in drows]))
    say('[4b] fields.tsv: %s' % f_int)

    # ---------- 原始字节抽样证据（给 VERDICT 用，非执行器产物）
    raw_ev = {}
    for r in results:
        if r['entry'] not in ('00421730', '005F9950') + tuple(TOPIC_ROWS):
            continue
        vt = int(r['sel']['vt'], 16)
        site = int(r['sel']['site'], 16)
        col = int(r['sel']['col'], 16)
        td = int(r['sel']['td'], 16)
        raw_ev[r['entry']] = dict(
            slot_word_va='%08X' % (vt + r['slot'] * 4),
            slot_word=raw_hex(img, vt + r['slot'] * 4, 4),
            vt_m4=raw_hex(img, vt - 4, 4),
            col=raw_hex(img, col, 20),
            td8_str=img.cstr(td + 8, 64),
            td8_bytes=raw_hex(img, td + 8, 16),
            site=raw_hex(img, site, 8),
            site_insn=r['insn'],
        )

    # ---------- 汇总
    def nfail(key):
        return len([r for r in results if r.get('checks', {}).get(key) is False])

    keys = ['A_prefix', 'A_cols', 'B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7',
            'B7_indep', 'B8', 'C_ring4', 'D', 'E', 'F']
    per = {k: nfail(k) for k in keys}
    fail_rows = [r['entry'] for r in results if r.get('fail')]

    say('[3] 逐项不合格行数: %s' % per)
    say('[4] §F 追加正文不同=%s，entry 归一组数=%d，四字段多样性=%s'
        % (uniq_raw, len(dup_norm), div))
    say('[5] 有 FAIL 理由的行: %s' % (fail_rows or '无'))
    say('[6] 披露指针 §12.6: %d/18  逐行固定披露句: %d/18  含 §12.4: %d'
        % (len([r for r in results if r.get('has_126')]),
           len([r for r in results if r.get('per_row_disclose')]),
           len([r for r in results if r.get('has_124')])))
    say('[7] 骨架逐字符合模板: %d/18 ; 追加段首字符分布 %s'
        % (len([r for r in results if r.get('e_head_exact')]),
           dict(collections.Counter(
               (r.get('orig4') or ' ')[-1:] + (r.get('append_first') or '?')
               for r in results))))
    say('[8] 同槽持有表数（§C 独立计数）: %s'
        % {r['entry']: (r['n_same_slot'], r['n_same_slot_live'],
                        r['n_class_consistent']) for r in results
           if r['n_same_slot'] > 1})
    say('[8b] entry 落在站点宿主函数体内（atlas 合并块警报）: %s'
        % ([r['entry'] for r in results if r.get('entry_in_host_body')] or '无'))
    say('[8b2] B7 独立旁证（NOP 填充分界）: %s'
        % {r['entry']: (r.get('indep_body'), r.get('indep_func_start'))
           for r in results})
    say('[8b3] atlas 体尾 NOP 填充吻合: %d/18 ; 各体尾 NOP 长度 %s'
        % (len([r for r in results if r.get('atlas_end_pad_ok')]),
           {r['entry']: r.get('atlas_end_nop_run') for r in results}))
    say('[8b4] 独立函数起点 vs atlas 宿主: 一致 %d/18 ; 不一致 %s'
        % (len([r for r in results
                if r.get('indep_func_start') == r.get('host_atlas')]),
           {r['entry']: (r.get('indep_func_start'), r.get('host_atlas'))
            for r in results
            if r.get('indep_func_start') != r.get('host_atlas')}))
    say('[8d] 归属健全性（所选表槽数 > 槽号；vt 前不再有表起点；候选表槽数全 > 槽号）: %s'
        % {r['entry']: (r.get('chosen_slots'), r.get('slot_in_range'),
                        r.get('prev_not_table'), r.get('cands_slot_in_range'))
           for r in results})
    say('[8c] 站点与 entry 字节距离: %s'
        % {r['entry']: r.get('site_off_from_entry') for r in results})

    # ---------- 产物：bytecheck.tsv
    cols = ['entry', 'name', 'slot_no', 'vt', 'col', 'offset', 'td', 'mangled',
            'site', 'host_func', 'entry_body', 'A_prefix', 'A_cols',
            'B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8',
            'ring4==site', 'n_same_slot_tables', 'n_same_slot_live',
            'n_class_consistent', 'chosen_slots', 'slot_in_range',
            'prev_not_table', 'cands_slot_in_range',
            'B7_indep', 'indep_body', 'D', 'E_head_exact',
            'E_disclose', 'F', 'verdict', 'note']
    lines = ['\t'.join(cols)]

    def tb(v):
        return 'T' if v is True else ('F' if v is False else '-')

    for r in results:
        w = r.get('w') or {}
        ck = r.get('checks', {})
        note = []
        if r.get('fail'):
            note.append('FAIL:' + ' | '.join(r['fail']))
        note.append('site_instr=%s' % (r.get('insn') or '-'))
        note.append('cands_all_slot=%s' % r.get('n_cand_all_slot'))
        note.append('site_only_on_chosen=%s' % r.get('site_only_on_chosen'))
        note.append('classes_in_slot=%s' % ','.join(
            c.split('@@')[0].replace('.?AV', '') for c in
            (r.get('same_slot_classes') or [])))
        row = [r['entry'], r.get('name', ''), str(r.get('slot')),
               r.get('sel', {}).get('vt') or '-',
               r.get('sel', {}).get('col') or '-',
               str(r.get('sel', {}).get('off')),
               r.get('sel', {}).get('td') or '-',
               w.get('mangled') or '-',
               r.get('sel', {}).get('site') or '-',
               w.get('host') or '-',
               r.get('entry_body') or '-',
               tb(ck.get('A_prefix')), tb(ck.get('A_cols')),
               tb(ck.get('B1')), tb(ck.get('B2')), tb(ck.get('B3')),
               tb(ck.get('B4')), tb(ck.get('B5')), tb(ck.get('B6')),
               tb(ck.get('B7')), tb(ck.get('B8')),
               tb(ck.get('C_ring4')),
               str(r.get('n_same_slot')), str(r.get('n_same_slot_live')),
               str(r.get('n_class_consistent')),
               str(r.get('chosen_slots')),
               tb(r.get('slot_in_range')), tb(r.get('prev_not_table')),
               tb(r.get('cands_slot_in_range')),
               tb(ck.get('B7_indep')), r.get('indep_body') or '-',
               tb(ck.get('D')), tb(r.get('e_head_exact')),
               tb(r.get('per_row_disclose')), tb(ck.get('F')),
               'FAIL' if r.get('fail') else 'PASS',
               ';'.join(note).replace('\t', ' ')]
        lines.append('\t'.join(row))
    with io.open(OUT_BYTECHECK, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(lines) + '\n')

    # ---------- 产物：tables.md（§C 同槽多表证据）
    md = ['# R16-AUDIT-F1-B1 · §C 同槽多表独立枚举', '',
          '> 由 `verify.py` 只读复算生成。判据：在 `.rdata`/`.data` 扫 4 字节对齐 `dd <entry>`，',
          '> 命中点回走表起点（COL 签名/`COL+12`=TD/`TD+8` 装饰名校验），',
          '> `slot=(hit-vt)/4`，保留 `u32(vt+slot*4)==entry` 者。',
          '> 「活」= 该表在 `.text` 内至少有一处 `mov <mem>, imm32(==vt)` 装表点。', '']
    for r in results:
        if r.get('n_same_slot', 0) <= 1 and r['entry'] not in TOPIC_ROWS:
            continue
        md.append('## %s · %s（slot %s）' %
                  (r['entry'], r.get('name', ''), r.get('slot')))
        md.append('')
        md.append('- 同槽（slot %s）持有该 entry 的表：**%d 张**，其中「活表」**%d 张**；'
                  '类一致（`%s`）**%d 张**'
                  % (r.get('slot'), r.get('n_same_slot'), r.get('n_same_slot_live'),
                     '.?AV%s@@' % r.get('cls'), r.get('n_class_consistent')))
        md.append('- 执行器所选：vt=`%s` site=`%s`（ring4_at=`%s`，相符=%s）'
                  % (r.get('sel', {}).get('vt'), r.get('sel', {}).get('site'),
                     r.get('ring4'), r.get('checks', {}).get('C_ring4')))
        md.append('')
        md.append('| vt | 槽数 | COL | TD | TD+8 装饰名 | 类一致 | 装表点（前 6） | 本文所选 |')
        md.append('|---|---|---|---|---|---|---|---|')
        for c in r.get('tables', []):
            inst = ', '.join('%08X' % s for s in sorted(c['installs'])[:6]) or '（无装表点）'
            md.append('| `%08X` | %s | `%08X` | `%08X` | `%s` | %s | %s | %s |'
                      % (c['vt'], c.get('slots'), c['col'], c['td'], c['mangled'],
                         'Y' if c['mangled'] == '.?AV%s@@' % r.get('cls') else 'n',
                         inst,
                         '←' if ('%08X' % c['vt']) == r.get('sel', {}).get('vt') else ''))
        md.append('')
    with io.open(OUT_TABLES, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(md) + '\n')

    # ---------- 产物：verify_out.json
    summary = dict(
        baseline=dict(exe_sha=sha_exe, exe_sha_expect=EXPECT_SHA,
                      exe_sha_ok=(sha_exe == EXPECT_SHA),
                      cov_sha=sha_cov, cov_size=size_cov, delta_sha=sha_delta),
        derived=dict(n=len(derived), expect=76, reject=dict(reject),
                     b1_slice_ok=set_ok, b1=b1_derived),
        texts_scan=dict(n_insn=ts.n_insn, n_skip=ts.n_skip),
        precedent_skeleton=prec,
        merged_tail=wtail,
        fields_integrity=f_int,
        raw_evidence=raw_ev,
        per_check_fail_rows=per,
        fail_rows=fail_rows,
        plagiarism=dict(uniq_raw=uniq_raw, uniq_norm=uniq_norm,
                        dup_norm_groups=len(dup_norm), diversity=div),
        rows=[dict(entry=r['entry'], name=r.get('name'), slot=r.get('slot'),
                   checks=r.get('checks'), sel=r.get('sel'),
                   ring4=r.get('ring4'), host_atlas=r.get('host_atlas'),
                   entry_body=r.get('entry_body'),
                   site_in_entry_body=r.get('site_in_entry_body'),
                   n_same_slot=r.get('n_same_slot'),
                   n_same_slot_live=r.get('n_same_slot_live'),
                   n_class_consistent=r.get('n_class_consistent'),
                   n_cand_all_slot=r.get('n_cand_all_slot'),
                   chosen_in_same_slot=r.get('chosen_in_same_slot'),
                   site_only_on_chosen=r.get('site_only_on_chosen'),
                   same_slot_classes=r.get('same_slot_classes'),
                   insn=r.get('insn'), fail=r.get('fail'),
                   host_body=r.get('host_body'),
                   entry_in_host_body=r.get('entry_in_host_body'),
                   site_off_from_entry=r.get('site_off_from_entry'),
                   join=r.get('join'))
              for r in results],
    )
    with io.open(OUT_JSON, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(summary, f, ensure_ascii=False, indent=1)

    say('[9] 产物: bytecheck.tsv / tables.md / verify_out.json')
    return 0


if __name__ == '__main__':
    sys.exit(main())
