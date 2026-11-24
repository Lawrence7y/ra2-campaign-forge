#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
R16-DESIGN-D48 / plan.py —— 只读静态统计（不启动、不 attach、不写进程内存）

产出（本目录）：
  disp_stats.tsv   按 disp 分组的全量统计（卡面 §5.2）
  summary.json     全部计数
  sites_base_only.tsv  `call [reg+disp]` 站点明细（base 寄存器、无 index、非栈基）

口径（写死，复跑同一套数）：
  · 站点：`.text` 线性反汇编（capstone x86-32，skipdata），`call` 且操作数为内存，
          基址存在、无 index、基址不是 esp/ebp。`call [reg]`（disp=0）计入。
          另用「从 atlas 函数入口递归下降」确认指令边界（列 n_sites_confirmed）。
  · 表：`.rdata`/`.data` 里 4 字节对齐、`vt-4` 处是合法 RTTI COL（sig==0、TD+8 是 `.?A`）。
  · 活表：
      宽口径 = 有 >=1 个 `mov [mem], imm32==vt` 装表点的表；
      窄口径 = 装表点落在**已知非 atexit 函数体**内的表（R14_COMMON ㉓ 的细化）；
    本脚本两个口径都算，结论一致（见 summary.json 的 unamb.wide / unamb.narrow）。
    注：㉓ 的 atexit 判据在本镜像上几乎不触发（见 summary.json 的 atexit_*），
    因此「宽口径」是歧义方向上的保守超集 —— 无歧义数只会被低估，不会被高估。
  · 无歧义：
      strict = 该偏移上「恰有 1 张活表」有 entry（卡面字面读法）
      value  = 该偏移上「所有有 entry 的活表」值相同（唯一的 entry 值）
  · 收益：见 summary.json 的 benefit 段。

只读性：`pefile` 只读打开 gamemd.exe；不写任何既有产物，只写本目录。
复跑： python plan.py            （默认带递归下降确认，约 60–90 s）
       python plan.py --quick    （跳过确认与落盘）
"""
import os
import sys
import json
import collections
import hashlib
import bisect

sys.dont_write_bytecode = True

try:
    import pefile
    import capstone
    from capstone import x86 as X
except ImportError as e:                     # pragma: no cover
    sys.exit('need pefile + capstone: %s' % e)

HERE = os.path.dirname(os.path.abspath(__file__))
EXE = r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
COV = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv'
ATLAS = r'D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv'

IMAGE_BASE = 0x400000
TEXT_LO, TEXT_HI = 0x401000, 0x7E038D
ATEXIT = 0x7C978A
PROVED = '\u5df2\u8bc1'      # 已证
RING4 = '\u2463'             # ④


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest().upper()


class Image(object):
    def __init__(self, path):
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
            self.buf[off:off + len(s['data'])] = s['data']

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


def col_of(img, vt):
    col = img.u32(vt - 4)
    if not col or not (IMAGE_BASE <= col < IMAGE_BASE + 0x800000):
        return None
    if img.u32(col) != 0:
        return None
    td = img.u32(col + 12)
    if not td or not (IMAGE_BASE <= td < IMAGE_BASE + 0x800000):
        return None
    nm = img.cstr(td + 8, 256)
    if not nm or not nm.startswith('.?A'):
        return None
    return dict(col=col, name=nm)


class Text(object):
    def __init__(self, img):
        t = img.section('.text')
        n = min(len(t['data']), t['vsize'] or len(t['data']))
        self.lo = t['va']
        self.code = bytes(t['data'][:n])
        self.hi = self.lo + len(self.code)
        assert (self.lo, self.hi) == (TEXT_LO, TEXT_HI), (hex(self.lo), hex(self.hi))
        self.n_insn = 0
        self.n_skip = 0
        self.sites = []
        self.stores = collections.defaultdict(list)
        self.atexit_fn = set()
        md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
        md.detail = True
        md.skipdata = True
        for insn in md.disasm(self.code, self.lo):
            if insn.id == 0:
                self.n_skip += 1
                continue
            self.n_insn += 1
            ops = insn.operands
            if insn.mnemonic == 'call' and ops and ops[0].type == X.X86_OP_MEM:
                m = ops[0].mem
                self.sites.append(dict(va=insn.address, size=insn.size,
                                       base=insn.reg_name(m.base) if m.base else '',
                                       index=insn.reg_name(m.index) if m.index else '',
                                       disp=m.disp or 0,
                                       text='%s %s' % (insn.mnemonic, insn.op_str)))
            elif insn.mnemonic == 'mov' and len(ops) == 2 and \
                    ops[0].type == X.X86_OP_MEM and ops[1].type == X.X86_OP_IMM:
                imm = ops[1].imm & 0xFFFFFFFF
                if IMAGE_BASE <= imm < IMAGE_BASE + 0x800000:
                    self.stores[imm].append((insn.address, ops[0].mem.disp))
        # atexit: `push <fn>` 之后 4 条窗口内出现 `call 0x7C978A`
        wins = collections.deque(maxlen=4)
        for insn in md.disasm(self.code, self.lo):
            if insn.id == 0:
                wins.clear()
                continue
            ops = insn.operands
            if insn.mnemonic == 'call' and ops and ops[0].type == X.X86_OP_IMM and \
                    (ops[0].imm & 0xFFFFFFFF) == ATEXIT:
                for _, imm in wins:
                    if TEXT_LO <= imm < TEXT_HI:
                        self.atexit_fn.add(imm)
                wins.clear()
                continue
            if insn.mnemonic == 'push' and ops and ops[0].type == X.X86_OP_IMM:
                wins.append((insn.address, ops[0].imm & 0xFFFFFFFF))
            elif insn.mnemonic == 'ret':
                wins.clear()


def enumerate_tables(img):
    tabs = {}
    for s in img.secs:
        if s['name'] not in ('.rdata', '.data'):
            continue
        for k in range(len(s['data']) // 4):
            va = s['va'] + k * 4
            c = col_of(img, va)
            if c:
                tabs[va] = dict(vt=va, col=c['col'], cls=c['name'], section=s['name'])
    return tabs


def table_len(img, vt, stop_set, max_slots=4000):
    n = 0
    while n < max_slots:
        va = vt + n * 4
        if va != vt and va in stop_set:
            break
        v = img.u32(va)
        if v is None:
            break
        if v == 0 or TEXT_LO <= v < TEXT_HI:
            n += 1
            continue
        break
    return n


def load_coverage():
    rows = []
    with open(COV, encoding='utf-8-sig') as f:
        for ln in f:
            c = ln.rstrip('\n').split('\t')
            if len(c) != 8:
                continue
            rows.append(dict(entry=c[0], sub=c[1], name=c[2], sem=c[3],
                             grade=c[4], ev=c[5], ns=c[6], conflict=c[7]))
    return rows


def load_atlas():
    out = {}
    with open(ATLAS, encoding='utf-8-sig') as f:
        for i, ln in enumerate(f):
            if i == 0:
                continue
            c = ln.rstrip('\n').split('\t')
            if len(c) < 2:
                continue
            try:
                out[int(c[0], 16)] = int(c[1])
            except ValueError:
                continue
    return out


def body_of(sizes, starts, va):
    i = bisect.bisect_right(starts, va) - 1
    if i < 0:
        return None
    s = starts[i]
    if s <= va < s + sizes[i]:
        return s
    return None


def confirm_boundaries(img, atlas, text, sites):
    """从 atlas 函数入口递归下降，返回「确认为真指令边界」的站点地址集合。
    只对含站点的函数做（省时间）。"""
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = True
    code, LO = text.code, text.lo
    starts = sorted(atlas)
    asz = [atlas[s] for s in starts]
    need = set()
    for s in sites:
        f = body_of(asz, starts, s['va'])
        if f is not None:
            need.add(f)
    ok = set()
    for entry in need:
        end = entry + atlas[entry]
        work = [entry]
        seen = set()
        guard = 0
        while work and guard < 200000:
            guard += 1
            a = work.pop()
            while entry <= a < end:
                if a in seen:
                    break
                seen.add(a)
                o = a - LO
                ins = next(md.disasm(code[o:o + 15], a), None)
                if ins is None or ins.size == 0:
                    break
                ok.add(a)
                nx = a + ins.size
                ops = ins.operands
                mn = ins.mnemonic
                if mn in ('ret', 'retf', 'int3'):
                    break
                if mn == 'jmp' and ops and ops[0].type == X.X86_OP_IMM:
                    t = ops[0].imm & 0xFFFFFFFF
                    if entry <= t < end:
                        work.append(t)
                    break
                if mn.startswith('j') and ops and ops[0].type == X.X86_OP_IMM:
                    t = ops[0].imm & 0xFFFFFFFF
                    if entry <= t < end:
                        work.append(t)
                a = nx
    return ok, len(need)


def main():
    quick = '--quick' in sys.argv
    print('[1/7] image ...', flush=True)
    img = Image(EXE)
    exe_sha = sha256(EXE)
    print('      sha256 =', exe_sha)

    print('[2/7] .text disasm ...', flush=True)
    text = Text(img)
    print('      insn=%d skipdata=%d call-mem sites=%d atexit_fn=%d'
          % (text.n_insn, text.n_skip, len(text.sites), len(text.atexit_fn)))

    print('[3/7] tables ...', flush=True)
    tabs = enumerate_tables(img)
    stop = set(tabs)
    for vt, t in tabs.items():
        t['n_slots'] = table_len(img, vt, stop)
    print('      tables=%d slots=%d' % (len(tabs), sum(t['n_slots'] for t in tabs.values())))

    atlas = load_atlas()
    starts = sorted(atlas)
    asz = [atlas[s] for s in starts]

    installs = collections.defaultdict(list)
    for imm, lst in text.stores.items():
        if imm in tabs:
            installs[imm].extend(lst)
    wide, narrow = [], []
    n_inst_sites = sum(len(v) for v in installs.values())
    n_atexit_sites = 0
    for vt, ins in installs.items():
        wide.append(vt)
        for site, _ in ins:
            fn = body_of(asz, starts, site)
            if fn is not None and fn in text.atexit_fn:
                n_atexit_sites += 1
                continue
            narrow.append(vt)
            break
    print('      tables with imm-install=%d (narrow ctor-installed=%d)  install sites=%d (atexit-provenance=%d)'
          % (len(wide), len(narrow), n_inst_sites, n_atexit_sites))

    def slot_map(vt):
        m = {}
        for k in range(tabs[vt]['n_slots']):
            v = img.u32(vt + k * 4)
            if v is not None and TEXT_LO <= v < TEXT_HI:
                m[k * 4] = v
        return m

    print('[4/7] slot maps ...', flush=True)
    maps_wide = {vt: slot_map(vt) for vt in wide}
    maps_narrow = {vt: slot_map(vt) for vt in narrow}

    print('[5/7] coverage ...', flush=True)
    cov = load_coverage()
    cov_by_entry = {int(r['entry'], 16): r for r in cov}
    proved = [r for r in cov if r['grade'] == '[' + PROVED + ']']
    no4 = [r for r in proved if RING4 not in r['sem']]
    print('      rows=%d proved=%d proved_no4=%d' % (len(cov), len(proved), len(no4)))

    # 站点分类
    st = text.sites
    base_only = [s for s in st if s['base'] and not s['index']
                 and s['base'] not in ('esp', 'ebp')]
    stack = [s for s in st if s['base'] in ('esp', 'ebp')]
    indexed = [s for s in st if s['index']]
    absolute = [s for s in st if not s['base']]

    print('[6/7] boundary confirmation (recursive descent) ...', flush=True)
    if quick:
        confirmed, nfn = set(), 0
    else:
        confirmed, nfn = confirm_boundaries(img, atlas, text, base_only)
    n_conf = sum(1 for s in base_only if s['va'] in confirmed)
    print('      funcs=%d confirmed sites=%d/%d' % (nfn, n_conf, len(base_only)))

    # 每个 disp
    by_disp = collections.defaultdict(list)
    for s in base_only:
        by_disp[s['disp']].append(s)

    def stat_at(d, mp):
        ents = collections.Counter()
        holders = 0
        for vt, m in mp.items():
            if d in m:
                ents[m[d]] += 1
                holders += 1
        return ents, holders

    rows = []
    for d in sorted(by_disp):
        sites = by_disp[d]
        e_w, h_w = stat_at(d, maps_wide)
        e_n, h_n = stat_at(d, maps_narrow)
        rows.append(dict(disp=d, n_sites=len(sites),
                         n_conf=sum(1 for s in sites if s['va'] in confirmed),
                         nt_w=h_w, nu_w=len(e_w), nt_n=h_n, nu_n=len(e_n),
                         entry_w=(list(e_w)[0] if len(e_w) == 1 else None),
                         entry_n=(list(e_n)[0] if len(e_n) == 1 else None)))

    def unamb(mp_key_tabs, mp_key_uniq):
        strict = [r for r in rows if r[mp_key_tabs] == 1]
        value = [r for r in rows if r[mp_key_uniq] == 1]
        return strict, value

    strict_w, value_w = unamb('nt_w', 'nu_w')
    strict_n, value_n = unamb('nt_n', 'nu_n')

    def W(rs, key):
        return set(r[key] for r in rs if r[key] is not None)

    proved_set = {int(r['entry'], 16) for r in proved}
    no4_set = {int(r['entry'], 16) for r in no4}
    cov_set = set(cov_by_entry)

    def hits(s):
        return dict(in_coverage=len(s & cov_set), in_proved=len(s & proved_set),
                    in_proved_no4=len(s & no4_set))

    # 收益：链闭合时的上限（entry 落在任一有站点的偏移上）
    disps = set(by_disp)
    entries_by_disp = collections.defaultdict(set)
    for vt, m in maps_wide.items():
        for d, e in m.items():
            if d in disps:
                entries_by_disp[d].add(e)
    reach = set().union(*entries_by_disp.values()) if entries_by_disp else set()
    ceiling = no4_set & reach
    disp_needed = set(d for d, es in entries_by_disp.items() if es & ceiling)
    sites_needed = sum(by_disp[d].__len__() for d in disp_needed)

    summary = dict(
        exe=EXE, sha256=exe_sha,
        coverage=dict(rows=len(cov), proved=len(proved), proved_no4=len(no4),
                      ring4_any=len([r for r in proved if RING4 in r['sem']]),
                      ring4_slot=len([r for r in proved
                                      if (RING4 + ' \u6d3b\u8868\u69fd\u4f4d\u89c1\u8bc1') in r['sem']])),
        text=dict(lo=hex(text.lo), hi=hex(text.hi), insn=text.n_insn, skipdata=text.n_skip),
        sites=dict(all=len(st), base_only=len(base_only), confirmed=n_conf,
                   stack=len(stack), indexed=len(indexed), absolute=len(absolute),
                   distinct_disp=len(rows)),
        tables=dict(total=len(tabs), wide=len(wide), narrow=len(narrow),
                    slots=sum(t['n_slots'] for t in tabs.values())),
        atexit=dict(functions=len(text.atexit_fn), install_sites=n_atexit_sites),
        unamb=dict(
            wide=dict(strict=dict(n_disp=len(strict_w), entries=len(W(strict_w, 'entry_w')),
                                  **hits(W(strict_w, 'entry_w'))),
                      value=dict(n_disp=len(value_w), entries=len(W(value_w, 'entry_w')),
                                 n_sites=sum(r['n_sites'] for r in value_w),
                                 **hits(W(value_w, 'entry_w')))),
            narrow=dict(strict=dict(n_disp=len(strict_n), entries=len(W(strict_n, 'entry_n'))),
                        value=dict(n_disp=len(value_n), entries=len(W(value_n, 'entry_n')))),
        ),
        benefit=dict(
            closed_chain_ceiling_rows=len(ceiling),
            closed_chain_disp_needed=len(disp_needed),
            closed_chain_sites_needed=sites_needed,
            degrade_rows=sorted('%08X' % e for e in (W(value_w, 'entry_w') & no4_set)),
        ),
    )

    print('[7/7] done', flush=True)
    print(json.dumps(summary, ensure_ascii=False, indent=1))

    if quick:
        return

    with open(os.path.join(HERE, 'summary.json'), 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=1)

    p = os.path.join(HERE, 'disp_stats.tsv')
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write('disp_hex\tdisp_dec\tslot\tn_sites\tn_sites_confirmed\t'
                'n_tables_live\tn_uniq_entries_live\tn_tables_narrow\tn_uniq_narrow\t'
                'unamb_strict\tunamb_value\twitness_entry\tin_coverage\tgrade_has4\n')
        for r in rows:
            e = r['entry_w']
            co = cov_by_entry.get(e) if e else None
            f.write('%08X\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%s\t%s\t%s\t%s\t%s\n' % (
                r['disp'] & 0xFFFFFFFF, r['disp'], (r['disp'] >> 2) & 0xFFFFFFFF,
                r['n_sites'], r['n_conf'], r['nt_w'], r['nu_w'], r['nt_n'], r['nu_n'],
                'Y' if r in strict_w else 'N', 'Y' if r in value_w else 'N',
                ('%08X' % e) if e else '-',
                ('%s/%s' % (co['sub'], co['name'])) if co else '-',
                (('Y' if RING4 in co['sem'] else 'N') + '/' + co['grade']) if co else '-'))
    print('wrote', p)

    p2 = os.path.join(HERE, 'sites_base_only.tsv')
    with open(p2, 'w', encoding='utf-8', newline='') as f:
        f.write('site\tsize\tdisp_hex\tconfirmed\tin_func\tinsn\n')
        for s in base_only:
            fn = body_of(asz, starts, s['va'])
            f.write('%08X\t%d\t%08X\t%s\t%s\t%s\n' % (
                s['va'], s['size'], s['disp'] & 0xFFFFFFFF,
                'Y' if s['va'] in confirmed else 'N',
                ('%08X' % fn) if fn else '-', s['text']))
    print('wrote', p2)


if __name__ == '__main__':
    main()
