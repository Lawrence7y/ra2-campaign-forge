# -*- coding: utf-8 -*-
"""
R4-DERIVABILITY — 只读测量员。

问题：`coverage.tsv` 里 848 行 `name_only_no_ring4`（语义栏只写「YRpp/kb 地址名…」）的 ④
（使用见证）到底能不能补？补的代价是「文档缺口」还是「新取证」？

方法（三步，全部回二进制）：
  A. 虚表持有：在 .rdata/.data 里扫 `dd entry`（4 字节 LE == entry）。每命中一处，
     用 RTTI 反向解析出该表的起点：表起点 V 满足 u32(V-4) 是一个合法 COL
     （signature==0，pTypeDescriptor 指向 `.?A` 装饰名）⇒ 槽号 = (hit-V)/4。
     额外给出 COL 里的装饰名，用来判「这张表是不是行名里那个类的表」。
  B. 真实调用者：capstone 5.0.7（skipdata=True）反汇编整个 .text，收集
       - `call rel32` 的落点（direct 调用者）
       - `call [reg+disp]` 的 disp（虚派发点，不绑定类型）
       - `mov [reg(+disp)], imm32` 且 imm 落在镜像内（候选装表指令）
     对每个 entry：direct_callers = call rel32 落点 == entry 的个数；
     via_vtable = 该表若是「活表」（.text 里存在 mov [*],V 装表），
                  .text 里 disp == slot*4 的 `call [reg+disp]` 点数（注明不绑定类型）。
  C. ④ 能否成立（按卡片规则）：
       vt_count>0 且 表是活的  -> OK_SLOT          （槽位形态，D-43(A) 口径可立）
       vt_count==0 且 direct>0 -> INSUFF_D40       （direct-only，D-40 明确不足）
       两者都无                -> NOT_DERIVABLE

只读：本脚本不写除 R4_DERIVABILITY\\ 以外的任何路径。
跑法：
    python probe.py            # 全流程：抽 12 行 + 全 848 行实扫 + 写 sample.tsv
    python probe.py --sample   # 只出抽样表
    python probe.py --list     # 只打印 848 行清单
"""
import io
import os
import sys
import re
import json
import collections
import hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(R14))
SURF = os.path.join(R14, 'D47_SURFACE')
COV = os.path.join(R14, 'COVERAGE', 'coverage.tsv')
EXE = os.path.join(ROOT, 'ra2youli', 'gamemd.exe')
ATLAS = os.path.join(ROOT, 'lead', 'next_re_20261112_r10', 'W130_atlas',
                     'function_atlas.tsv')

EXPECT_SHA = '73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476'
IMAGE_BASE = 0x400000
TEXT_LO, TEXT_HI = 0x401000, 0x7E038D          # .text = [0x401000, 0x7E038D)

sys.path.insert(0, SURF)
sys.dont_write_bytecode = True                  # 只读纪律：import D47_SURFACE 不得留下 .pyc
import surface as S                             # noqa: E402  (只读复用 D47 的分类器)

import pefile                                    # noqa: E402
import capstone                                  # noqa: E402


# --------------------------------------------------------------------------- PE 底图
class Image(object):
    def __init__(self, path):
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


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest().upper()


def load_atlas_sizes():
    """entry -> 函数体字节数（atlas 第 2 列 size）。用来判「装表点是否在本 entry 体内」。"""
    out = {}
    for i, ln in enumerate(open(ATLAS, encoding='utf-8-sig')):
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


# --------------------------------------------------------------------------- RTTI
def col_of(img, vt_start):
    """vt_start 是表起点；表起点 -4 应当是 COL 指针（绝对 VA）。返回 COL 信息或 None。"""
    col_va = img.u32(vt_start - 4)
    if col_va is None or not (IMAGE_BASE <= col_va < IMAGE_BASE + len(img.buf)):
        return None
    if col_va - IMAGE_BASE + 20 > len(img.buf):
        return None
    sig = img.u32(col_va)
    if sig != 0:                                  # signature 必须为 0
        return None
    td_va = img.u32(col_va + 12)                  # pTypeDescriptor：绝对 VA（不是 RVA）
    if td_va is None or not (IMAGE_BASE <= td_va < IMAGE_BASE + len(img.buf)):
        return None
    nm = img.cstr(td_va + 8, 256)                 # 装饰名在 TD+8，内联串（不是指针）
    if not nm or not nm.startswith('.?A'):
        return None
    cd = img.u32(col_va + 16)
    return dict(col=col_va, name=nm, td=td_va, pchd=cd)


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
                break                             # 已找到起点，再往回就不合法 -> 停
        k += 1
    return best


# --------------------------------------------------------------------------- .text 全扫
class TextScan(object):
    """一次反汇编 .text，供所有 entry 查表。"""

    def __init__(self, img, lo=TEXT_LO, hi=TEXT_HI):
        t = img.sections_named('.text')[0]
        self.lo = t['va']
        # 裁到 VirtualSize 与题面 .text 上界（0x7E038D），不把尾部对齐填充当代码
        n = min(len(t['data']), t['vsize'] if t['vsize'] else len(t['data']),
                TEXT_HI - t['va'])
        self.code = bytes(t['data'][:n])
        self.hi = self.lo + len(self.code)
        self.direct = collections.Counter()       # 落点 -> call rel32 次数
        self.disp = collections.Counter()         # disp -> call [reg+disp] 点数
        self.disp_sites = collections.defaultdict(list)
        self.stores = collections.defaultdict(list)   # imm -> [(site_va, base, disp)]
        self.n_insn = 0
        self.n_skip = 0

        md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
        md.detail = True
        md.skipdata = True                        # 必须：数据字面量会让线性反汇编跑飞
        base = self.lo
        for insn in md.disasm(self.code, base):
            if insn.id == 0:
                self.n_skip += 1
                continue
            self.n_insn += 1
            mn = insn.mnemonic
            ops = insn.operands
            if mn == 'call' and len(ops) >= 1:
                o = ops[0]
                if o.type == capstone.x86.X86_OP_IMM:
                    self.direct[o.imm & 0xFFFFFFFF] += 1
                elif o.type == capstone.x86.X86_OP_MEM:
                    r = o.mem.base
                    if r != capstone.x86.X86_REG_INVALID and \
                       r != capstone.x86.X86_REG_ESP and \
                       r != capstone.x86.X86_REG_EBP:
                        d = o.mem.disp & 0xFFFFFFFF
                        self.disp[d] += 1
                        if len(self.disp_sites[d]) < 400:
                            self.disp_sites[d].append(insn.address)
            elif mn == 'mov' and len(ops) == 2:
                a, b = ops
                if a.type == capstone.x86.X86_OP_MEM and \
                   b.type == capstone.x86.X86_OP_IMM:
                    imm = b.imm & 0xFFFFFFFF
                    if IMAGE_BASE <= imm < IMAGE_BASE + 0x800000:
                        if len(self.stores[imm]) < 64:
                            self.stores[imm].append((insn.address, a.mem.disp))

    def installs_of(self, vt_va):
        """在 .text 里找 mov [reg(+disp)], vt_va —— 构造器装表点。"""
        return self.stores.get(vt_va, [])


# --------------------------------------------------------------------------- A / B / C
def scan_dd(img, entry_va, secnames=('.rdata', '.data')):
    """A 步：在指定段里扫 `dd entry`。"""
    hits = []
    for s in img.sections_named(*secnames):
        d = s['data']
        pat = entry_va.to_bytes(4, 'little')
        i = 0
        while True:
            i = d.find(pat, i)
            if i < 0:
                break
            if i % 4 == 0:                        # 必须 4 字节对齐（dd）
                hits.append(s['va'] + i)
            i += 1
    return hits


def scan_refs(img, va, secname):
    """原始 imm32 引用计数（任意对齐）：用于看「地址被取用」而不只是被 call。"""
    s = img.sections_named(secname)[0]
    pat = va.to_bytes(4, 'little')
    d = s['data']
    n = 0
    i = d.find(pat)
    while i >= 0:
        n += 1
        i = d.find(pat, i + 1)
    return n


def analyze(img, ts, row, atlas_sizes=None):
    entry = row['entry']
    e = int(entry, 16)
    size = (atlas_sizes or {}).get(entry)
    body = (e, e + size) if size else None
    vt = []
    for hit in scan_dd(img, e):
        ws = vtable_start(img, hit)
        if ws is None:
            vt.append(dict(hit=hit, vt=None, slot=None, col_name=None))
        else:
            v, c = ws
            vt.append(dict(hit=hit, vt=v, slot=(hit - v) // 4,
                           col_name=c['name'], col=c['col']))
    # 只保留槽号可定的
    slots = [x['slot'] for x in vt if x['slot'] is not None]
    # 表是否活：该表起点在 .text 里被 mov [*],V 装过
    live = {}
    for x in vt:
        if x['vt'] is not None:
            ins = ts.installs_of(x['vt'])
            live[x['vt']] = ins
    live_any = any(bool(v) for v in live.values())
    # 装表点分「本 entry 体内」与「别处」：ctor/dtor 自己装自己的表是 ②（同源），
    # 由另一个函数装表才是「本 entry 是别的活表的槽占用者」。
    self_inst = []
    ext_inst = []
    for v, sites in live.items():
        for site_va, disp in sites:
            if body and body[0] <= site_va < body[1]:
                self_inst.append((v, site_va))
            else:
                ext_inst.append((v, site_va))
    has_ext = bool(ext_inst)
    has_self_only = bool(self_inst) and not has_ext
    direct = ts.direct.get(e, 0)
    # via_vtable：活表槽位的 disp 在 .text 里被 call [reg+disp] 过几次（不绑定类型）
    via = 0
    via_detail = []
    for x in vt:
        if x['slot'] is None:
            continue
        if not live.get(x['vt']):
            continue
        dsp = x['slot'] * 4
        n = ts.disp.get(dsp, 0)
        if n:
            via += n
            via_detail.append((dsp, n))
    if slots and live_any:
        form = 'OK_SLOT'
        tier = 'EXT_INSTALL' if has_ext else 'SELF_INSTALL'
    elif direct > 0:
        form = 'INSUFF_D40'
        tier = '-'
    else:
        form = 'NOT_DERIVABLE'
        tier = '-'
    cls_name = row['name'].split('::')[-2] if row['name'].count('::') >= 1 else ''
    col_match = [x['col_name'] for x in vt if x['col_name']]
    # COL 装饰名 vs 行名里的类名（强校验：这表是不是「那个类」的表）
    def nm_ok(mangled):
        if not cls_name or not mangled:
            return None
        return cls_name in mangled
    col_ok = [nm_ok(c) for c in col_match]
    text_imm_refs = scan_refs(img, e, '.text')
    data_imm_refs = scan_refs(img, e, '.data')
    static_vptr = []
    for x in vt:
        if x['vt'] is None:
            continue
        for off in scan_dd(img, x['vt'], ('.data',)):
            static_vptr.append(off)               # 静态 vptr 写（全局对象静态初始化）
    return dict(entry=entry, subsystem=row['subsystem'], name=row['name'],
                vt=vt, slots=slots, live=live, live_any=live_any,
                self_inst=self_inst, ext_inst=ext_inst, body_size=size,
                direct=direct, via=via, via_detail=via_detail,
                form=form, tier=tier, cls=cls_name, col_names=col_match,
                col_ok=col_ok,
                text_imm_refs=text_imm_refs, data_imm_refs=data_imm_refs,
                static_vptr=static_vptr,
                sem=row['sem'])


# --------------------------------------------------------------------------- 抽样
def load_class():
    rows = S.load_coverage()
    atlas = S.load_atlas()
    audit = S.load_audit_records()
    trace = S.load_census_trace()
    proved = [r for r in rows if r['grade'] == S.GRADE_PROVED]
    recs = [(r, S.classify(r, audit, trace)) for r in proved]
    cls = [r for r, d in recs if d['reason'] == 'name_only_no_ring4']
    cls.sort(key=lambda r: int(r['entry'], 16))
    return cls, rows, recs


def sample12(cls):
    n = len(cls)
    idx = [0, n - 1]
    for k in range(1, 11):
        i = int(round(k * (n - 1) / 11.0))
        idx.append(i)
    idx = sorted(set(idx))
    return [cls[i] for i in idx], idx


def slot_str(slots):
    if not slots:
        return '-'
    return ','.join(str(s) for s in sorted(set(slots)))


def ring4_form(a):
    if a['form'] == 'OK_SLOT':
        parts = []
        for x in a['vt']:
            if x['slot'] is None:
                continue
            ins = a['live'].get(x['vt']) or []
            ext = [s for s in ins if not (a['body_size'] and
                                          a['entry'] and
                                          int(a['entry'], 16) <= s[0] <
                                          int(a['entry'], 16) + a['body_size'])]
            tag = ('ext@%08X' % ext[0][0]) if ext else \
                  (('self@%08X' % ins[0][0]) if ins else 'no-install')
            parts.append('slot%d@vt%08X %s' % (x['slot'], x['vt'], tag))
        return '%s[%s]' % (a['tier'], ';'.join(parts))
    if a['form'] == 'INSUFF_D40':
        return 'direct-only(x%d)' % a['direct']
    if a['vt']:
        return 'vt-hit-but-not-ctor-installed'
    return 'none'


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else '--all'
    sha = sha256(EXE)
    assert sha == EXPECT_SHA, 'binary sha mismatch: %s' % sha

    cls, rows, recs = load_class()
    print('class size            :', len(cls))
    atlas_sizes = load_atlas_sizes()

    if mode == '--list':
        for r in cls:
            print(r['entry'], r['subsystem'], r['name'])
        return

    img = Image(EXE)
    print('sections              :', [(s['name'], hex(s['va']), hex(s['rsize']))
                                      for s in img.secs])
    ts = TextScan(img)
    print('.text insns           : %d (skip %d)  lo=%08X hi=%08X'
          % (ts.n_insn, ts.n_skip, ts.lo, ts.hi))
    print('call rel32 targets    : %d distinct' % len(ts.direct))
    print('call [reg+disp] disps : %d distinct' % len(ts.disp))
    print('mov-store imms (img)  : %d distinct' % len(ts.stores))

    samp, idx = sample12(cls)
    print('sample idx            :', idx)

    # ---- 12 行 ----
    out = []
    for r in samp:
        a = analyze(img, ts, r, atlas_sizes)
        out.append(a)
    # ---- 全 848 行（附加：把外推换成实数）----
    full = []
    for r in cls:
        full.append(analyze(img, ts, r, atlas_sizes))

    if mode == '--detail':
        for a in full:
            if a['vt'] or a['text_imm_refs']:
                pass
        for a in full:
            if a['form'] != 'OK_SLOT':
                continue
            print('%s %s %s vt=%s slot=%s install=%s via=%s col=%s col_ok=%s'
                  % (a['entry'], a['subsystem'], a['name'], len(a['vt']),
                     slot_str(a['slots']), ring4_form(a), a['via'],
                     a['col_names'][:2], a['col_ok'][:2]))
        print('--- vt-hit but unresolved slot ---')
        for a in full:
            if a['vt'] and not a['slots']:
                print(a['entry'], a['subsystem'], a['name'], a['vt'])
        print('--- NOT_DERIVABLE ---')
        for a in full:
            if a['form'] == 'NOT_DERIVABLE':
                print(a['entry'], a['subsystem'], a['name'],
                      'textrefs=%d datarefs=%d' % (a['text_imm_refs'], a['data_imm_refs']))
        print('--- INSUFF_D40 with text imm refs > direct callers (address-taken) ---')
        n = 0
        for a in full:
            if a['form'] == 'INSUFF_D40' and a['text_imm_refs'] > a['direct']:
                n += 1
                if n <= 15:
                    print(a['entry'], a['subsystem'], a['name'],
                          'direct=%d textrefs=%d' % (a['direct'], a['text_imm_refs']))
        print('count:', n)

    with open(os.path.join(HERE, 'sample.tsv'), 'w', encoding='utf-8', newline='') as f:
        f.write('entry\tsubsystem\tname\tvt_count\tslot_no\tdirect_callers\t'
                'via_vtable\tring4_form\tverdict\n')
        for a in out:
            f.write('%s\t%s\t%s\t%d\t%s\t%d\t%d\t%s\t%s\n' % (
                a['entry'], a['subsystem'], a['name'], len(a['vt']),
                slot_str(a['slots']), a['direct'], a['via'],
                ring4_form(a), a['form']))

    # ---- 汇总 ----
    def agg(lst):
        c = collections.Counter(a['form'] for a in lst)
        t = collections.Counter(a['tier'] for a in lst if a['form'] == 'OK_SLOT')
        return dict(n=len(lst),
                    vt_gt0=sum(1 for a in lst if a['vt']),
                    slot_ok=sum(1 for a in lst if a['slots']),
                    live=sum(1 for a in lst if a['live_any']),
                    direct_gt0=sum(1 for a in lst if a['direct'] > 0),
                    via_gt0=sum(1 for a in lst if a['via'] > 0),
                    OK_SLOT=c['OK_SLOT'], INSUFF_D40=c['INSUFF_D40'],
                    NOT_DERIVABLE=c['NOT_DERIVABLE'],
                    EXT_INSTALL=t['EXT_INSTALL'], SELF_INSTALL=t['SELF_INSTALL'],
                    also_self=sum(1 for a in lst if a['form'] == 'OK_SLOT'
                                  and a['self_inst']),
                    col_match=sum(1 for a in lst if a['form'] == 'OK_SLOT'
                                  and any(a['col_ok'])),
                    col_mismatch=sum(1 for a in lst if a['form'] == 'OK_SLOT'
                                     and a['col_ok'] and not any(a['col_ok'])),
                    insuff_data_refs=sum(1 for a in lst
                                         if a['form'] == 'INSUFF_D40'
                                         and a['data_imm_refs'] > 0),
                    insuff_extra_textrefs=sum(1 for a in lst
                                              if a['form'] == 'INSUFF_D40'
                                              and a['text_imm_refs'] > a['direct']),
                    no_body_size=sum(1 for a in lst if not a['body_size']))

    res = dict(sha=sha, n_class=len(cls), sample_idx=idx,
               sample=[{k: v for k, v in a.items() if k not in ('live',)}
                       for a in out],
               sample_agg=agg(out), full_agg=agg(full),
               full_form=collections.Counter(a['form'] for a in full),
               full_by_sub=dict(collections.Counter(
                   a['subsystem'] for a in full if a['form'] == 'OK_SLOT')),
               full_vt0_but_direct=sum(1 for a in full
                                       if not a['vt'] and a['direct'] > 0),
               full_none=sum(1 for a in full
                             if not a['vt'] and a['direct'] == 0),
               full_vt_hit=sum(1 for a in full if a['vt']),
               full_vt_hit_no_install=sum(1 for a in full
                                          if a['vt'] and not a['live_any']),
               ok_col_match=sum(1 for a in full if a['form'] == 'OK_SLOT'
                                and any(a['col_ok'])),
               ok_col_nomatch=sum(1 for a in full if a['form'] == 'OK_SLOT'
                                  and a['col_ok'] and not any(a['col_ok'])),
               ok_col_unknown=sum(1 for a in full if a['form'] == 'OK_SLOT'
                                  and not a['col_ok']),
               ok_static_vptr=sum(1 for a in full if a['form'] == 'OK_SLOT'
                                  and a['static_vptr']),
               insuff_with_extra_refs=sum(1 for a in full
                                          if a['form'] == 'INSUFF_D40'
                                          and a['text_imm_refs'] > a['direct']),
               slotname_rows=sum(1 for a in cls
                                 if re.search(r'slot\d+|vslot', a['name'], re.I)),
               )
    # 聚集性：OK_SLOT 行在 848 行按 entry 升序里的位置分布
    pos_ok = [i for i, a in enumerate(full) if a['form'] == 'OK_SLOT']
    runs = []
    for i in pos_ok:
        if runs and i == runs[-1][1] + 1:
            runs[-1][1] = i
        else:
            runs.append([i, i])
    res['ok_positions'] = pos_ok
    res['ok_runs'] = runs
    res['ok_run_span'] = sum(b - a + 1 for a, b in runs)

    # ③ 也敞着口？语义栏含字面 [未证] ⇒ strict 也不满足（㉘ 模板行）
    res['sem_has_unproved'] = sum(1 for r in cls if '[未证]' in r['sem'])
    res['ok_slot_but_sem_unproved'] = sum(
        1 for a in full if a['form'] == 'OK_SLOT' and '[未证]' in a['sem'])
    res['insuff_but_sem_unproved'] = sum(
        1 for a in full if a['form'] == 'INSUFF_D40' and '[未证]' in a['sem'])

    # §8.6 条 1「site 不共用」：若按「不同行之间不得共用装表站点」解释，
    # 同一虚表的所有槽位行共享同一个装表点 ⇒ 只有独占站点的行才算
    site_of = {}
    for a in full:
        if a['form'] != 'OK_SLOT':
            continue
        e = int(a['entry'], 16)
        ext = [s for s in a['ext_inst']]
        site_of[a['entry']] = ext[0][1] if ext else None
    share = collections.Counter(v for v in site_of.values() if v)
    res['ok_site_counts'] = dict(collections.Counter(
        share.get(site_of[e], 0) for e in site_of))
    res['ok_sites_distinct'] = len(set(v for v in site_of.values() if v))
    res['ok_rows_exclusive_site'] = sum(
        1 for e, s in site_of.items() if s and share[s] == 1)
    res['ok_rows_shared_site'] = sum(
        1 for e, s in site_of.items() if s and share[s] > 1)
    res['site_of'] = site_of

    # 全表落盘（848 行，便于 Lead 复核每一行）
    with open(os.path.join(HERE, 'all848.tsv'), 'w', encoding='utf-8',
              newline='') as f:
        f.write('idx\tentry\tsubsystem\tname\tvt_count\tslot_no\tcol_class\t'
                'install_site(ext/self)\tdirect_callers\tvia_vtable\t'
                'text_imm_refs\tdata_imm_refs\tring4_form\tverdict\ttier\n')
        for i, a in enumerate(full):
            cols = [c for c in a['col_names'] if c]
            f.write('%d\t%s\t%s\t%s\t%d\t%s\t%s\t%s\t%d\t%d\t%d\t%d\t%s\t%s\t%s\n' % (
                i, a['entry'], a['subsystem'], a['name'], len(a['vt']),
                slot_str(a['slots']), ','.join(cols[:3]) or '-',
                ring4_form(a), a['direct'], a['via'], a['text_imm_refs'],
                a['data_imm_refs'], ring4_form(a), a['form'], a['tier']))
    with open(os.path.join(HERE, 'work_scan.json'), 'w', encoding='utf-8') as f:
        json.dump({k: v for k, v in res.items()}, f, ensure_ascii=False, indent=1,
                  default=str)
    print(json.dumps({k: res[k] for k in ('sample_agg', 'full_agg')},
                     ensure_ascii=False, indent=1, default=str))
    print('full by subsystem (OK_SLOT):', res['full_by_sub'])
    print('sem has [未证]         :', res['sem_has_unproved'], '/ 848')
    print('OK_SLOT & sem [未证]   :', res['ok_slot_but_sem_unproved'])
    print('INSUFF & sem [未证]    :', res['insuff_but_sem_unproved'])
    print('distinct install sites :', res['ok_sites_distinct'])
    print('exclusive site rows    :', res['ok_rows_exclusive_site'],
          ' shared site rows:', res['ok_rows_shared_site'])
    print('wrote sample.tsv / all848.tsv / work_scan.json')


if __name__ == '__main__':
    main()
