# -*- coding: utf-8 -*-
"""
PROBE_802 — 只读测量员。

问题：`coverage.tsv` 里 802 行 `[已证]`，其 `evidence_path` **只含** `classification_trace`
（分类追踪不是四环证据）。按名字形态分三组：
    slotN 形态 43 行 / 真名 723 行 / sub_ 伪名 36 行 / 空 0
问：这 802 行里有多少能**低成本补出真证据**（补 ④ 被使用见证）。

三件事：
  A. 43 行 slotN —— 全量测。每行判：被活虚表槽持有？（vt_count / slot_no）COL 可解？
     装表点是否在 entry 体外？④ 能否成文？
  B. 723 行真名 —— 抽 20 行（entry 升序：最小 1 + 最大 1 + 中间均匀 18），
     判有无 V1/V2/V3 见证，给基础率。
  C. 36 行 sub_ 伪名 —— 只报数，说明为何预期为 0（② 物理不可得）。

判定方法（全部回二进制，复用 R4_DERIVABILITY 的已验证方法）：
  * RTTI：`[vt-4]=COL(绝对 VA)` → `[COL+0]=signature==0` → `[COL+0xC]=TD(绝对 VA)`
    → `TD+8` 内联装饰名 `.?A...`。**COL.pSelf 本镜像恒为 0，不用它判表起点。**
  * 装表点：capstone 5.0.7 `skipdata=True` 线性反汇编整个 .text，收
    `mov [reg(+disp)], imm32` 且 imm∈镜像 ⇒ 构造器装表点。落在本 entry 体内 = ctor 自己装
    （② 同源）；落在体外 = 本 entry 是**别人的**活表的槽占用者。
  * ④ 判据（**照 R14_COMMON §8.6 条 1 + §12.3，本卡不另立口径**）：
      条 1：④ = direct call（E8 边界 + site+5+rel32==entry + 非自环）或
            活 vtable 槽位派发（构造器装的活表 + vt[slot]==entry + site 不共用）。
      §12.3：**② 与 ④ 必须来自两条独立证据链**——同一个虚表槽不能既证明「属于哪个类」
            又证明「被用过」。
      ⇒ 对 `Class::slotN` 行：②（类属）本身来自 vt[slot]==entry ⇒ **④ 不可再用同一槽**，
        只能另找一条与虚表槽无关的链（V3 函数指针入全局表 / direct call）。
      ⇒ 对真名行：② 来自 YRpp/kb 地址名或子系统区域，与虚表槽无因果关系 ⇒ **V1 可用**。
      （这正是 848 行那批 91 行能补的原因，也是 43 行 slotN 结构上更差的原因。）
  * 纪律：**direct-only 不算 ④ 成立**（D-39 实证虚函数 direct call 恒 0；D-40 已作废
    「direct call ⇒ [已证]」）。本卡不靠 direct 给任何一行判「可补」。

只读：本脚本只写 `PROBE_802\\`，不写 coverage / PANEL / R14_COMMON / 台账 / 其它卡目录。
跑法：
    python probe.py             # 全流程：A 43 行 + B 抽 20 行 + C 报数，写 slotN43.tsv / sample20.tsv
    python probe.py --subs      # 只打印三个子集的清单与计数
    python probe.py --json      # 额外把汇总写 work_scan.json
"""
import os
import sys
import re
import json
import hashlib
import collections

sys.dont_write_bytecode = True                   # 只读纪律：不留 .pyc

HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(R14))
COV = os.path.join(R14, 'COVERAGE', 'coverage.tsv')
EXE = os.path.join(ROOT, 'ra2youli', 'gamemd.exe')
ATLAS = os.path.join(ROOT, 'lead', 'next_re_20261112_r10', 'W130_atlas',
                     'function_atlas.tsv')

EXPECT_SHA = '73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476'
IMAGE_BASE = 0x400000
TEXT_LO, TEXT_HI = 0x401000, 0x7E038D           # .text = [0x401000, 0x7E038D)

# ---- 方法保真度锚点：R4_DERIVABILITY 已公开的 direct 计数（用于自检本卡的 TextScan）----
ANCHORS = {'004011C0': 1, '0054F5C0': 44, '007DC720': 437}


# --------------------------------------------------------------------------- 输入
def load_proved_trace_only():
    """grade == [已证] 且 evidence_path 的每个 token 都含 classification_trace。"""
    rows = []
    with open(COV, encoding='utf-8-sig') as f:
        for i, ln in enumerate(f):
            if i == 0:                            # 表头是逗号分隔（文件里已知的坑）
                continue
            c = ln.rstrip('\r\n').split('\t')
            if len(c) < 6:
                continue
            rows.append(dict(entry=c[0].strip().upper(), subsystem=c[1].strip(),
                             name=c[2].strip(), sem=c[3], grade=c[4],
                             evid=c[5], n_src=c[6] if len(c) > 6 else '',
                             conflict=c[7] if len(c) > 7 else ''))
    proved = [r for r in rows if r['grade'] == '[已证]']

    def toks(ep):
        # EVID_RESOLVE 的分割口径：; | , 三种都切，再去 #anchor
        return [p.strip().split('#')[0] for p in re.split(r'[;|,]', ep) if p.strip()]

    out = [r for r in proved
           if toks(r['evid']) and all('classification_trace' in t for t in toks(r['evid']))]
    out.sort(key=lambda r: int(r['entry'], 16))
    return out, proved, rows


def subgroup(name):
    """三组按 Lead 的口径：slotN / sub_ / 真名。顺序有讲究（TechnoClass::sub_70DE00 属 sub_）。"""
    if re.search(r'slot\d+', name, re.I):
        return 'slotN'
    if re.search(r'sub_[0-9A-Fa-f]+', name):
        return 'sub'
    return 'realname'


def slot_from_name(name):
    m = re.search(r'slot(\d+)', name, re.I)
    return int(m.group(1)) if m else None


def class_from_name(name):
    if '::' not in name:
        return None
    return name.rsplit('::', 1)[0]


def load_yrpp_idents():
    """YRpp 源码里出现过的全部标识符。用作「② 是否另有名字源」的机械代理。

    依据 R14_COMMON §8.6 条 2 的 ② 合法通道 2（YRpp 地址绑定）：名字若能在 YRpp 里
    找到同类同方法声明，则 ② 不必依赖虚表 COL ⇒ 与 V1 是两条独立链（§12.3 允许）。
    """
    idx = set()
    root = os.path.join(ROOT, 'YRpp')
    if not os.path.isdir(root):
        return idx
    for dp, _dn, fn in os.walk(root):
        for f in fn:
            if not f.lower().endswith(('.h', '.hpp', '.cpp', '.c')):
                continue
            try:
                s = open(os.path.join(dp, f), encoding='utf-8', errors='ignore').read()
            except OSError:
                continue
            idx.update(re.findall(r'[A-Za-z_][A-Za-z0-9_]*', s))
    return idx


def yrpp_anchor(name, idx):
    """返回 (类锚定, 方法锚定)。类名做 Class 后缀容错（DriveLocomotion → DriveLocomotionClass）。"""
    if not idx or '::' not in name:
        return False, False
    cls, meth = name.rsplit('::', 1)
    cls_ok = (cls in idx) or ((cls + 'Class') in idx)
    meth_ok = bool(meth) and (meth in idx)
    return cls_ok, meth_ok


# --------------------------------------------------------------------------- PE 底图
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
        try:
            return self.buf[off:e].decode('latin-1')
        except Exception:
            return None

    def sections_named(self, *names):
        want = set(names)
        return [s for s in self.secs if s['name'] in want]

    def in_image(self, va):
        return va is not None and IMAGE_BASE <= va < IMAGE_BASE + len(self.buf)


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest().upper()


def load_atlas_sizes():
    """entry -> 函数体字节数（atlas 第 2 列 size），用于判「装表点是否在 entry 体内」。"""
    out = {}
    if not os.path.isfile(ATLAS):
        return out
    with open(ATLAS, encoding='utf-8-sig') as f:
        for i, ln in enumerate(f):
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


def body_ranges(atlas_sizes):
    """[(start, end)] 按 start 升序，用于判「这个调用点是否落在某个已知函数体内」。"""
    out = sorted((int(k, 16), int(k, 16) + v) for k, v in atlas_sizes.items() if v)
    return out


def which_body(ranges, va):
    """返回包含 va 的函数体起点（atlas 命中则说明该指令解码对齐在真实函数体内）。"""
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


# --------------------------------------------------------------------------- RTTI
def col_of(img, vt_start):
    """vt_start-4 必须是 COL 绝对 VA；signature==0；TD+8 是内联 .?A 装饰名。"""
    col_va = img.u32(vt_start - 4)
    if not img.in_image(col_va):
        return None
    if col_va - IMAGE_BASE + 20 > len(img.buf):
        return None
    if img.u32(col_va) != 0:                      # signature 必须为 0
        return None
    td_va = img.u32(col_va + 12)                  # pTypeDescriptor：绝对 VA
    if not img.in_image(td_va):
        return None
    nm = img.cstr(td_va + 8, 256)                 # 装饰名在 TD+8（内联串，不是指针）
    if not nm or not nm.startswith('.?A'):
        return None
    return dict(col=col_va, name=nm, td=td_va, pchd=img.u32(col_va + 16))


def vtable_start(img, hit_va, max_walk=0x1000):
    """从命中地址往回走到表起点；取走得最远的合法候选（越过起点后 COL 校验必然失败）。"""
    best = None
    k = 0
    while k * 4 <= max_walk:
        v = hit_va - k * 4
        if v <= IMAGE_BASE + 4:
            break
        if img.sec_of(v) is None or img.sec_of(v - 4) is None:
            k += 1
            continue
        c = col_of(img, v)
        if c is not None:
            best = (v, c)
        else:
            if best is not None:
                break
        k += 1
    return best


# --------------------------------------------------------------------------- .text 全扫
class TextScan(object):
    """一次反汇编 .text，供所有 entry 查表。"""

    def __init__(self, img, lo=TEXT_LO, hi=TEXT_HI):
        import capstone
        self.cs = capstone
        t = img.sections_named('.text')[0]
        self.lo = t['va']
        n = min(len(t['data']), t['vsize'] or len(t['data']), TEXT_HI - t['va'])
        self.code = bytes(t['data'][:n])
        self.hi = self.lo + len(self.code)
        self.direct = collections.Counter()        # 落点 -> call rel32 次数
        self.direct_sites = collections.defaultdict(list)   # 落点 -> [site_va]
        self.disp = collections.Counter()          # disp -> call [reg+disp] 站点数
        self.disp_sites = collections.defaultdict(list)
        self.stores = collections.defaultdict(list)  # imm -> [(site_va, obj_disp)]
        self.n_insn = 0
        self.n_skip = 0
        md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
        md.detail = True
        md.skipdata = True                         # 必须：数据字面量会让线性反汇编跑飞
        X = capstone.x86
        for insn in md.disasm(self.code, self.lo):
            if insn.id == 0:
                self.n_skip += 1
                continue
            self.n_insn += 1
            ops = insn.operands
            if insn.mnemonic == 'call' and len(ops) >= 1:
                o = ops[0]
                if o.type == X.X86_OP_IMM:
                    tgt = o.imm & 0xFFFFFFFF
                    self.direct[tgt] += 1
                    if len(self.direct_sites[tgt]) < 256:
                        self.direct_sites[tgt].append(insn.address)
                elif o.type == X.X86_OP_MEM:
                    r = o.mem.base
                    if r not in (X.X86_REG_INVALID, X.X86_REG_ESP, X.X86_REG_EBP):
                        d = o.mem.disp & 0xFFFFFFFF
                        self.disp[d] += 1
                        if len(self.disp_sites[d]) < 400:
                            self.disp_sites[d].append(insn.address)
            elif insn.mnemonic == 'mov' and len(ops) == 2:
                a, b = ops
                if a.type == X.X86_OP_MEM and b.type == X.X86_OP_IMM:
                    imm = b.imm & 0xFFFFFFFF
                    if IMAGE_BASE <= imm < IMAGE_BASE + 0x800000:
                        if len(self.stores[imm]) < 64:
                            self.stores[imm].append((insn.address, a.mem.disp))

    def installs_of(self, vt_va):
        return self.stores.get(vt_va, [])


# --------------------------------------------------------------------------- 引用扫描
def scan_dd(img, value, secnames=('.rdata', '.data')):
    """在指定段里扫 4 字节对齐的 `dd value`。"""
    hits = []
    pat = value.to_bytes(4, 'little')
    for s in img.sections_named(*secnames):
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


def scan_refs(img, va, secname):
    """原始 imm32 引用计数（任意对齐），只看「地址被取用」。"""
    out = 0
    for s in img.sections_named(secname):
        d = s['data']
        pat = va.to_bytes(4, 'little')
        i = d.find(pat)
        while i >= 0:
            out += 1
            i = d.find(pat, i + 1)
    return out


def looks_like_ptr_table(img, va, span=3):
    """va 所在位置是不是「一串连续代码指针」——用来把函数指针表与散落 imm 区分开。"""
    n = 0
    for k in range(-span, span + 1):
        v = img.u32(va + k * 4)
        if v is not None and TEXT_LO <= v < TEXT_HI:
            n += 1
    return n >= span + 1


def col_name_match(name_cls, mangled):
    """行名里的类 与 RTTI 解出的装饰名是否对得上。"""
    if not name_cls or not mangled:
        return 'none'
    if name_cls.startswith('T_'):                 # 模板伪名 T_DynamicVectorClass_PAVInfantryClass__
        inner = name_cls[2:].rstrip('_')
        parts = [p for p in inner.split('_') if p]
        return 'match' if all(p in mangled for p in parts) else 'nomatch'
    return 'match' if name_cls in mangled else 'nomatch'


# --------------------------------------------------------------------------- 单行分析
def analyze(img, ts, row, atlas_sizes, ranges=None):
    entry = row['entry']
    e = int(entry, 16)
    size = atlas_sizes.get(entry)
    body = (e, e + size) if size else None

    vt = []
    for hit in scan_dd(img, e):
        ws = vtable_start(img, hit)
        if ws is None:
            vt.append(dict(hit=hit, vt=None, slot=None, col_name=None, col=None))
        else:
            v, c = ws
            vt.append(dict(hit=hit, vt=v, slot=(hit - v) // 4,
                           col_name=c['name'], col=c['col'], col_td=c['td']))

    slots = [x['slot'] for x in vt if x['slot'] is not None]
    name_slot = slot_from_name(row['name'])
    name_cls = class_from_name(row['name'])

    # 活表 + 装表点（体内 = ctor 自装 → ② 同源；体外 = 别人装 → 本行是槽占用者）
    live, self_inst, ext_inst = {}, [], []
    for x in vt:
        if x['vt'] is None:
            continue
        ins = ts.installs_of(x['vt'])
        live[x['vt']] = ins
        for site_va, _disp in ins:
            (self_inst if (body and body[0] <= site_va < body[1]) else ext_inst).append(
                (x['vt'], site_va))

    # 静态 vptr（.data 里存着表起点 ⇒ 静态初始化对象 ⇒ 实例可钉）
    static_vptr = []
    for x in vt:
        if x['vt'] is None:
            continue
        for off in scan_dd(img, x['vt'], ('.data',)):
            static_vptr.append((x['vt'], off))

    # 派发点：call [reg + slot*4]
    disp_hits = []
    for s in sorted(set(slots)):
        if ts.disp.get(s * 4, 0):
            disp_hits.append((s, ts.disp[s * 4], ts.disp_sites[s * 4][:6]))

    direct = ts.direct.get(e, 0)
    # direct 校验（条 1 的「E8 指令边界 + 非自环」）：只认落在已知函数体内、且不在本 entry
    # 自己体内的 call 站点。capstone 线性扫 + skipdata 可能把数据里的 E8 误当 call，
    # 用 atlas 函数体包含性做一次对齐过滤。
    direct_v = 0
    direct_sites = ts.direct_sites.get(e, [])
    if ranges is not None:
        for s in direct_sites:
            b = which_body(ranges, s)
            if b is None:
                continue
            if body and body[0] <= s < body[1]:
                continue                            # 自环/体内调用，不计
            direct_v += 1
    else:
        direct_v = direct
    unr = [x for x in vt if x['vt'] is None]       # 定了不表起点（RTTI fail-closed / 非虚表 dd）
    v3_hits = [x['hit'] for x in unr if looks_like_ptr_table(img, x['hit'])]

    col_status = [col_name_match(name_cls, x['col_name']) for x in vt if x['col_name']]
    if not col_status:
        col_ok = 'none'
    elif 'match' in col_status:
        col_ok = 'match'
    else:
        col_ok = 'nomatch'

    return dict(entry=entry, subsystem=row['subsystem'], name=row['name'], sem=row['sem'],
                entry_va=e, body_size=size, vt=vt, vt_count=len(vt),
                slots=sorted(set(slots)), slot_no=','.join(str(s) for s in sorted(set(slots))) or '-',
                name_slot=name_slot, name_cls=name_cls, col_ok=col_ok,
                col_names=[x['col_name'] for x in vt if x['col_name']],
                live=live, live_any=any(bool(v) for v in live.values()),
                self_inst=self_inst, ext_inst=ext_inst,
                has_ext=bool(ext_inst),
                direct=direct, direct_v=direct_v, direct_sites=direct_sites[:8],
                disp_hits=disp_hits,
                static_vptr=static_vptr, v3_hits=v3_hits,
                text_imm_refs=scan_refs(img, e, '.text'),
                data_imm_refs=scan_refs(img, e, '.data'),
                unrev=len(unr))


def judge_slotn(a):
    """43 行 slotN：④ 能否成文。返回 (ring4_ok, reason)。

    关键：② 来自 vt[slot]==entry（名字就是槽号）⇒ §12.3 禁止 ④ 再用同一槽。
    唯一合法的独立链 = V3（entry 进非虚表的全局函数指针表）。
    direct call 按纪律不算 ④（D-39：虚函数 direct 恒 0；本卡实测见 slotN43.tsv 的 direct 计数）。
    """
    if a['vt_count'] == 0:
        if a['v3_hits']:
            return 'y', ('V3 函数指针入全局表 @%s ⇒ ④ 独立链成立（虚表槽缺席也不影响）'
                         % ','.join('%08X' % h for h in a['v3_hits'][:2]))
        return 'n', '全镜像无活虚表槽持有 ⇒ 名字里的 slot%d 无二进制支撑，② 本身也缺' % (
            a['name_slot'] if a['name_slot'] is not None else -1)
    ok_slot = bool(a['slots']) and a['live_any']
    if not ok_slot:
        return 'n', '有 dd 命中但表不活/槽号定不出 ⇒ 槽位形态不成立'
    if a['col_ok'] == 'nomatch':
        return 'n', 'RTTI 类名与行名不一致（%s）⇒ ② 本身有冲突，先查②' % \
                    ','.join(a['col_names'][:2])
    if a['v3_hits']:
        return 'y', 'V3 函数指针入全局表 @%s ⇒ 另有独立 ④ 链（不受 §12.3 约束）' % \
                    ','.join('%08X' % h for h in a['v3_hits'][:2])
    # 这才是绝大多数：槽位形态齐备，但 ②④ 同源
    ex = ('ext@%08X' % a['ext_inst'][0][1]) if a['ext_inst'] else \
         (('self@%08X' % a['self_inst'][0][1]) if a['self_inst'] else 'no-install')
    extra = ''
    if a['disp_hits']:
        extra = '；槽偏移派发点 ×%d（未绑定类型，D-43(A) 不计）' % sum(
            n for _s, n, _x in a['disp_hits'])
    if a['vt_count'] >= 2:
        extra += '；另被 %d 张表持有（同一静态扫描派生，非独立链）' % a['vt_count']
    if a['direct_v']:
        extra += '；另有 %d 处已校验 direct 调用点（按 §8.6 条 1 字面可作 ④，' \
                 '按 D-39/D-40 方向与本卡纪律不计——见 REPORT §5）' % a['direct_v']
    return 'n', ('④② 同源：② 靠 vt[%s]==entry 定类，④ 只能用同一槽（装表点 %s%s）；'
                 '§12.3 明令「同一个虚表槽不能顶两个环」，且本条**不提供替代通道**'
                 % (a['slot_no'], ex, extra))


def judge_real(a, yrpp_idx=None):
    """真名行：V1/V2/V3 三形态。

    V1 可用性看 ② 的来源：若行名能在 YRpp 里找到同类同方法（条 2 通道 2），② 与虚表槽
    无因果关系 ⇒ V1 是独立链（§12.3 允许）。否则 ② 只能来自该表 COL ⇒ 与 V1 同源 ⇒ 不计。
    """
    cls_ok, meth_ok = yrpp_anchor(a['name'], yrpp_idx)
    anchored = cls_ok and meth_ok
    v1 = 'y' if (a['slots'] and a['live_any'] and a['has_ext']) else 'n'
    v2 = 'y' if (a['slots'] and a['disp_hits'] and a['static_vptr']) else 'n'
    v3 = 'y' if a['v3_hits'] else 'n'
    forms = []
    if v1 == 'y':
        forms.append('V1')
    if v2 == 'y':
        forms.append('V2')
    if v3 == 'y':
        forms.append('V3')
    if not forms:
        return v1, v2, v3, 'none', 'no', (
            '无任何非 direct-only 见证（direct=%d，vt=%d）' % (a['direct'], a['vt_count'])), anchored
    why = []
    if v1 == 'y':
        why.append('V1 活表槽 %s 装表点 %s' % (
            a['slot_no'],
            ('ext@%08X' % a['ext_inst'][0][1]) if a['ext_inst'] else 'self'))
    if v2 == 'y':
        why.append('V2 派发 site slot%s ×%d + 静态 vptr@%08X'
                   % (','.join(str(s) for s, _n, _s in a['disp_hits'][:2]),
                      a['disp_hits'][0][1], a['static_vptr'][0][1]))
    if v3 == 'y':
        why.append('V3 函数指针表 @%s' % ','.join('%08X' % h for h in a['v3_hits'][:2]))
    verdict = 'yes'
    note = ''
    if anchored:
        note = '；② 由 YRpp 名字锚定（%s%s）⇒ 与见证独立' % (
            '类✓' if cls_ok else '类✗', '方法✓' if meth_ok else '方法✗')
    else:
        note = '；⚠ 名字未在 YRpp 锚定（%s%s）⇒ ② 只能来自该表 COL，与见证同源（§12.3）' % (
            '类✓' if cls_ok else '类✗', '方法✓' if meth_ok else '方法✗')
        verdict = 'risk'
    if verdict == 'yes' and '[未证]' in a['sem']:
        note += '；⚠ 语义栏自陈[未证] ⇒ ③ 仍敞口，补 ④ 也不改 strict 档'
    return v1, v2, v3, '+'.join(forms), verdict, '；'.join(why) + note, anchored


# --------------------------------------------------------------------------- 抽样
def sample_idx(n, k=20):
    """最小 1 + 最大 1 + 中间均匀 18（保证 18 个内部下标互不相同）。"""
    if n <= k:
        return list(range(n))
    inner = k - 2                                  # 18
    idx = {0, n - 1}
    span = n - 3                                   # 内部可用范围 [1, n-2] 宽 n-3
    for j in range(inner):
        idx.add(1 + int(round(span * j / float(inner - 1))))
    if len(idx) != k:                              # 极端小 n 的兜底：退化为均分
        return [int(round(i * (n - 1) / float(k - 1))) for i in range(k)]
    return sorted(idx)


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else '--all'
    sha = sha256(EXE)
    if sha != EXPECT_SHA:
        print('!! binary sha mismatch: %s' % sha)
        return 2
    print('sha256 ok             :', sha)

    only, proved, allrows = load_proved_trace_only()
    grp = collections.OrderedDict((k, [r for r in only if subgroup(r['name']) == k])
                                 for k in ('slotN', 'realname', 'sub'))
    print('coverage rows         : %d ; proved %d ; trace-only %d'
          % (len(allrows), len(proved), len(only)))
    print('subgroups             : slotN %d / realname %d / sub_ %d / empty 0'
          % (len(grp['slotN']), len(grp['realname']), len(grp['sub'])))
    if mode == '--subs':
        for k, v in grp.items():
            print('---', k)
            for r in v:
                print(r['entry'], r['subsystem'], r['name'])
        return 0

    atlas_sizes = load_atlas_sizes()
    img = Image(EXE)
    ts = TextScan(img)
    ranges = body_ranges(atlas_sizes)
    print('.text                 : insns %d (skip %d) [%08X,%08X)'
          % (ts.n_insn, ts.n_skip, ts.lo, ts.hi))
    bad = [(k, ts.direct.get(int(k, 16), 0), v) for k, v in ANCHORS.items()
           if ts.direct.get(int(k, 16), 0) != v]
    print('method anchors        : %s'
          % ('OK (%d/%d)' % (len(ANCHORS) - len(bad), len(ANCHORS)) if not bad
             else 'MISMATCH %s' % bad))

    # ---------------- A. 43 行 slotN ----------------
    ranges = body_ranges(atlas_sizes)
    A = [analyze(img, ts, r, atlas_sizes, ranges) for r in grp['slotN']]
    rowsA = []
    for a in A:
        ok, reason = judge_slotn(a)
        rowsA.append(dict(entry=a['entry'], subsystem=a['subsystem'], name=a['name'],
                          vt_count=a['vt_count'], slot_no=a['slot_no'],
                          col_ok=a['col_ok'],
                          install_ext=('y' if a['has_ext'] else
                                       ('self-only' if a['self_inst'] else 'n')),
                          ring4_ok=ok, reason=reason))
    with open(os.path.join(HERE, 'slotN43.tsv'), 'w', encoding='utf-8', newline='') as f:
        f.write('entry\tsubsystem\tname\tvt_count\tslot_no\tcol_ok\tinstall_ext\t'
                'ring4_ok\treason\n')
        for r in rowsA:
            f.write('%s\t%s\t%s\t%d\t%s\t%s\t%s\t%s\t%s\n' % (
                r['entry'], r['subsystem'], r['name'], r['vt_count'], r['slot_no'],
                r['col_ok'], r['install_ext'], r['ring4_ok'], r['reason']))

    aggA = dict(n=len(A),                vt_gt0=sum(1 for a in A if a['vt_count'] > 0),
                slot_ok=sum(1 for a in A if a['slots']),
                live=sum(1 for a in A if a['live_any']),
                slot_live=sum(1 for a in A if a['slots'] and a['live_any']),
                ext=sum(1 for a in A if a['has_ext']),
                col_match=sum(1 for a in A if a['col_ok'] == 'match'),
                col_none=sum(1 for a in A if a['col_ok'] == 'none'),
                col_nomatch=sum(1 for a in A if a['col_ok'] == 'nomatch'),
                slot_eq_name=sum(1 for a in A if a['name_slot'] in a['slots']),
                slot_ne_name=sum(1 for a in A if a['slots'] and a['name_slot'] not in a['slots']),
                direct_gt0=sum(1 for a in A if a['direct'] > 0),
                direct_v_gt0=sum(1 for a in A if a['direct_v'] > 0),
                disp_gt0=sum(1 for a in A if a['disp_hits']),
                v3=sum(1 for a in A if a['v3_hits']),
                ring4=sum(1 for r in rowsA if r['ring4_ok'] == 'y'),
                vt_ge2=sum(1 for a in A if a['vt_count'] >= 2),
                static_vptr=sum(1 for a in A if a['static_vptr']),
                sem_unproved=sum(1 for a in A if '[未证]' in a['sem']),
                no_atlas=sum(1 for a in A if not a['body_size']))
    # 装表点共用：§8.6 条 1 的「site 不共用」= 不同行之间不得共用同一装表站点
    site_of_a = {a['entry']: (a['ext_inst'][0][1] if a['ext_inst'] else None) for a in A}
    share_a = collections.Counter(s for s in site_of_a.values() if s)
    aggA['sites_distinct'] = len(set(s for s in site_of_a.values() if s))
    aggA['rows_exclusive_site'] = sum(1 for e, s in site_of_a.items() if s and share_a[s] == 1)
    aggA['rows_shared_site'] = sum(1 for e, s in site_of_a.items() if s and share_a[s] > 1)
    aggA['site_of'] = {k: ('%08X' % v if v else None) for k, v in site_of_a.items()}
    aggA['vtables_distinct'] = len(set(x['vt'] for a in A for x in a['vt'] if x['vt']))

    print('\n[A] 43 slotN          : vt>0 %d / slot_ok %d / live %d / slot&live %d / ext %d'
          % (aggA['vt_gt0'], aggA['slot_ok'], aggA['live'],
             aggA['slot_live'], aggA['ext']))
    print('    col match/none/nomatch : %d / %d / %d ; slot==name %d ; != %d'
          % (aggA['col_match'], aggA['col_none'], aggA['col_nomatch'],
             aggA['slot_eq_name'], aggA['slot_ne_name']))
    print('    direct>0 %d ; **direct 已校验(体外+指令边界) %d** ; disp>0 %d ; V3 %d ;'
          ' **ring4_ok = %d** ; not-in-atlas %d'
          % (aggA['direct_gt0'], aggA['direct_v_gt0'], aggA['disp_gt0'], aggA['v3'],
             aggA['ring4'], aggA['no_atlas']))
    print('    aux: vt>=2 %d ; 静态 vptr %d ; 语义自带[未证] %d'
          % (aggA['vt_ge2'], aggA['static_vptr'], aggA['sem_unproved']))
    print('    install sites: distinct %d ; 独占 %d 行 / 共用 %d 行 ; tables distinct %d'
          % (aggA['sites_distinct'], aggA['rows_exclusive_site'],
             aggA['rows_shared_site'], aggA['vtables_distinct']))

    # ---------------- B. 723 行真名 抽样 20 ----------------
    real = grp['realname']
    yrpp_idx = load_yrpp_idents()
    print('\nYRpp idents           : %d（② 另有名字源的机械代理）' % len(yrpp_idx))
    idxB = sample_idx(len(real))
    B = [analyze(img, ts, real[i], atlas_sizes, ranges) for i in idxB]
    rowsB = []
    for a in B:
        v1, v2, v3, form, verdict, reason, anchored = judge_real(a, yrpp_idx)
        rowsB.append(dict(entry=a['entry'], subsystem=a['subsystem'], name=a['name'],
                          V1=v1, V2=v2, V3=v3, witness_form=form,
                          verdict=verdict, reason=reason))
    with open(os.path.join(HERE, 'sample20.tsv'), 'w', encoding='utf-8', newline='') as f:
        f.write('entry\tsubsystem\tname\tV1\tV2\tV3\twitness_form\tverdict\treason\n')
        for r in rowsB:
            f.write('%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' % (
                r['entry'], r['subsystem'], r['name'], r['V1'], r['V2'], r['V3'],
                r['witness_form'], r['verdict'], r['reason']))

    aggB = dict(n=len(B), idx=idxB,
                V1=sum(1 for r in rowsB if r['V1'] == 'y'),
                V2=sum(1 for r in rowsB if r['V2'] == 'y'),
                V3=sum(1 for r in rowsB if r['V3'] == 'y'),
                any_w=sum(1 for r in rowsB if r['witness_form'] != 'none'),
                yes=sum(1 for r in rowsB if r['verdict'] == 'yes'),
                risk=sum(1 for r in rowsB if r['verdict'] == 'risk'),
                direct_gt0=sum(1 for a in B if a['direct'] > 0),
                direct_zero=sum(1 for a in B if a['direct'] == 0),
                sem_unproved=sum(1 for a in B if '[未证]' in a['sem']))
    print('\n[B] realname %d, sample %d at idx %s' % (len(real), len(B), idxB))
    print('    V1 %d / V2 %d / V3 %d ; any witness %d ; verdict yes %d (risk %d)'
          % (aggB['V1'], aggB['V2'], aggB['V3'], aggB['any_w'],
             aggB['yes'], aggB['risk']))
    print('    direct>0 %d / direct==0 %d ; 语义自带[未证] %d'
          % (aggB['direct_gt0'], aggB['direct_zero'], aggB['sem_unproved']))
    for r in rowsB:
        print('    %s %-5s %-46s V1=%s V2=%s V3=%s %-10s %s'
              % (r['entry'], r['subsystem'], r['name'][:46], r['V1'], r['V2'],
                 r['V3'], r['witness_form'], r['verdict']))

    # ---------------- B2. 723 行真名 全量实扫（把外推换成本数；成本仅一次 .text 扫描后的查表）----
    fullB = [analyze(img, ts, r, atlas_sizes, ranges) for r in real]
    fb = []
    for a in fullB:
        v1, v2, v3, form, verdict, reason, anchored = judge_real(a, yrpp_idx)
        fb.append(dict(entry=a['entry'], name=a['name'], verdict=verdict, form=form,
                       v1=v1, v2=v2, v3=v3, anchored=anchored,
                       sem_unproved=('[未证]' in a['sem'])))
    aggB2 = dict(n=len(fb),
                 V1=sum(1 for r in fb if r['v1'] == 'y'),
                 V2=sum(1 for r in fb if r['v2'] == 'y'),
                 V3=sum(1 for r in fb if r['v3'] == 'y'),
                 any_w=sum(1 for r in fb if r['form'] != 'none'),
                 yes=sum(1 for r in fb if r['verdict'] == 'yes'),
                 risk=sum(1 for r in fb if r['verdict'] == 'risk'),
                 V1_anchored=sum(1 for r in fb if r['v1'] == 'y' and r['anchored']),
                 V1_unanchored=sum(1 for r in fb if r['v1'] == 'y' and not r['anchored']),
                 anchored=sum(1 for r in fb if r['anchored']),
                 sem_unproved=sum(1 for r in fb if r['sem_unproved']),
                 yes_and_sem_unproved=sum(1 for r in fb
                                          if r['verdict'] == 'yes' and r['sem_unproved']),
                 yes_rows=[(r['entry'], r['name'], r['form']) for r in fb
                           if r['verdict'] == 'yes'],
                 risk_rows=[r['entry'] for r in fb if r['verdict'] == 'risk'])
    print('\n[B2] 723 全量实扫（本卡附加，替代外推）:')
    print('     V1 %d (锚定 %d / 未锚定 %d) / V2 %d / V3 %d ; 任一见证 %d ; yes %d ; risk %d'
          % (aggB2['V1'], aggB2['V1_anchored'], aggB2['V1_unanchored'],
             aggB2['V2'], aggB2['V3'], aggB2['any_w'],
             aggB2['yes'], aggB2['risk']))
    print('     名字可在 YRpp 锚定 %d/723 ; 语义自带[未证] %d ; yes 行：%s'
          % (aggB2['anchored'], aggB2['sem_unproved'],
             '; '.join('%s %s [%s]' % t for t in aggB2['yes_rows'][:12]) or '-'))

    # ---------------- C. 36 行 sub_ 只报数 ----------------
    C = [analyze(img, ts, r, atlas_sizes, ranges) for r in grp['sub']]
    aggC = dict(n=len(C),
                vt_gt0=sum(1 for a in C if a['vt_count'] > 0),
                slot_live=sum(1 for a in C if a['slots'] and a['live_any']),
                direct_gt0=sum(1 for a in C if a['direct'] > 0),
                v3=sum(1 for a in C if a['v3_hits']),
                col_match=sum(1 for a in C if a['col_ok'] == 'match'))
    print('\n[C] sub_ %d (只报数)   : vt>0 %d / slot&live %d / direct>0 %d / V3 %d / col match %d'
          % (aggC['n'], aggC['vt_gt0'], aggC['slot_live'], aggC['direct_gt0'],
             aggC['v3'], aggC['col_match']))

    res = dict(sha=sha, n_trace_only=len(only),
               groups={k: len(v) for k, v in grp.items()},
               A_agg=aggA, A_rows=rowsA,
               B_agg=aggB, B_rows=rowsB, B2_agg=aggB2,
               C_agg=aggC)
    if mode == '--json':
        with open(os.path.join(HERE, 'work_scan.json'), 'w', encoding='utf-8') as f:
            json.dump(res, f, ensure_ascii=False, indent=1)
    print('\nwrote slotN43.tsv / sample20.tsv' + (' / work_scan.json' if mode == '--json' else ''))
    return 0


if __name__ == '__main__':
    sys.exit(main())
