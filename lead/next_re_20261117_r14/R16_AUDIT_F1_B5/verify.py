# -*- coding: utf-8 -*-
"""
R16_AUDIT_F1_B5 — 独立审计复算器（B5 收官批，4 行）。

卡面：_cards/R16-AUDIT-F1.md
被审：R16_F1_B5/{delta.tsv,fields.tsv,REPORT.md,...}（只读）
写域：R16_AUDIT_F1_B5/（本脚本只写本目录：bytecheck.tsv / verify_out.json）

独立性声明（本脚本**不 import 执行器脚本，也不复用 PROBE_802/probe.py 的取数逻辑**）：
  * PE 段表只用 pefile 做解析；u32/cstr/RTTI 三步、vtable 回溯、装表点全扫、函数体
    定界、atexit 注册识别、删除析构器签名识别，全部在本文件内重新实现。
  * capstone 5.0.7 自行驱动（CS_MODE_32 + skipdata 全扫 .text）。
  * 函数归属用 project atlas（W130_atlas）作辅助，另用**自定界**（从 entry 线性反汇编
    到首个 ret 为止）做交叉验证，二者冲突即报。

跑法：python verify.py
"""
import os
import sys
import re
import json
import bisect
import hashlib

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(R14))

EXE = os.path.join(ROOT, 'ra2youli', 'gamemd.exe')
COV = os.path.join(R14, 'COVERAGE', 'coverage.tsv')
ATLAS = os.path.join(ROOT, 'lead', 'next_re_20261112_r10', 'W130_atlas',
                     'function_atlas.tsv')
SCAN4GAP = os.path.join(R14, 'R16_PROBE_4GAP', 'scan_F1_audit.tsv')
BATCH = os.path.join(R14, 'R16_F1_B5')
DELTA = os.path.join(BATCH, 'delta.tsv')
FIELDS = os.path.join(BATCH, 'fields.tsv')

OUT_TSV = os.path.join(HERE, 'bytecheck.tsv')
OUT_JSON = os.path.join(HERE, 'verify_out.json')

EXPECT_SHA = '73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476'
IMAGE_BASE = 0x400000
TEXT_LO, TEXT_HI = 0x401000, 0x7E038D
ATEXIT_REG = 0x7C978A          # push <fn>; call 0x7C978A  = atexit 注册（§8.1 ㉓）
FREE_STUB = 0x7C8B3D           # 删除析构器 free 桩（§13.5 (b) 特征三件套之一）
BASE_CTOR = 0x5F3900           # 基类构造（WaveClass 族）
DISC_S12_6 = ('（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，'
              '见 R14_COMMON §12.6 与 PANEL 对应披露）')
WITNESS = '④ 活表槽位见证'

# 卡面 §4 E：先例三行
PRECEDENTS = ['00464AC0', '004DE630', '004F42F0']


# --------------------------------------------------------------------- 基础工具
def sha256p(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest().upper()


def load_atlas():
    out = {}
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


class Img(object):
    """只读镜像底图：按段拼虚拟地址空间，u32/cstr 自查。"""

    def __init__(self, path):
        import pefile
        self.raw = open(path, 'rb').read()
        pe = pefile.PE(data=self.raw, fast_load=True)
        self.base = pe.OPTIONAL_HEADER.ImageBase
        self.secs = []
        for s in pe.sections:
            nm = s.Name.rstrip(b'\x00').decode('latin-1')
            self.secs.append(dict(name=nm, va=self.base + s.VirtualAddress,
                                  vsize=s.Misc_VirtualSize,
                                  rsize=s.SizeOfRawData, data=s.get_data()))
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
        return self.buf[off:e].decode('latin-1')

    def in_image(self, va):
        return va is not None and self.base <= va < self.base + len(self.buf)

    def byte_at(self, va, n):
        off = va - self.base
        return bytes(self.buf[off:off + n])

    def sec_of(self, va):
        for s in self.secs:
            if s['va'] <= va < s['va'] + max(s['vsize'], s['rsize']):
                return s['name']
        return None


def rtti_triplet(img, vt):
    """§13.1/§13.2：COL=u32(vt-4)（绝对 VA）→ u32(COL)==0 → TD=u32(COL+0xC) → TD+8 内联名。"""
    col = img.u32(vt - 4)
    if not img.in_image(col):
        return None
    if img.u32(col) != 0:
        return None
    td = img.u32(col + 12)
    if not img.in_image(td):
        return None
    nm = img.cstr(td + 8, 256)
    if not nm or not nm.startswith('.?A'):
        return None
    return dict(col=col, td=td, mangled=nm, pchd=img.u32(col + 16))


def vtable_start(img, hit, max_walk=0x1000):
    """从 dd 命中处往回走到表起点：取走得最远的合法 COL 候选。"""
    best = None
    k = 0
    while k * 4 <= max_walk:
        v = hit - k * 4
        if v <= IMAGE_BASE + 4:
            break
        if img.sec_of(v) is None or img.sec_of(v - 4) is None:
            k += 1
            continue
        t = rtti_triplet(img, v)
        if t is not None:
            best = (v, t)
        elif best is not None:
            break
        k += 1
    return best


def decor_class(mangled):
    """`.?AVWaveClass@@` -> 'WaveClass'；`.?AUIFoo@@` -> 'IFoo'；解不出返 None。"""
    if not mangled:
        return None
    m = re.match(r'^\.\?A[VU]([A-Za-z_][A-Za-z0-9_@?$]*)@@$', mangled)
    return m.group(1) if m else None


def dd_hits(img, value, secnames=('.rdata', '.data')):
    """段内 4 字节对齐的 `dd value` 命中（= 该地址被这些表/槽持有）。"""
    out = []
    pat = value.to_bytes(4, 'little')
    for s in img.secs:
        if s['name'] not in secnames:
            continue
        d = s['data']
        i = 0
        while True:
            i = d.find(pat, i)
            if i < 0:
                break
            if i % 4 == 0:
                out.append(s['va'] + i)
            i += 1
    return out


class TextScan(object):
    """一次 skipdata 全扫 .text：收 `mov <mem>, imm32` 装表点与 `push imm32`。"""

    def __init__(self, img):
        import capstone
        self.cap = capstone
        t = [s for s in img.secs if s['name'] == '.text'][0]
        n = min(len(t['data']), t['vsize'] or len(t['data']), TEXT_HI - t['va'])
        self.lo = t['va']
        self.code = bytes(t['data'][:n])
        self.hi = self.lo + len(self.code)
        self.stores = {}        # imm -> [(insn_va, disp)]
        self.pushes = {}        # imm -> [insn_va]
        self.n_insn = 0
        self.n_skip = 0
        md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
        md.detail = True
        md.skipdata = True
        X = capstone.x86
        for ins in md.disasm(self.code, self.lo):
            if ins.id == 0:
                self.n_skip += 1
                continue
            self.n_insn += 1
            ops = ins.operands
            if ins.mnemonic == 'mov' and len(ops) == 2:
                a, b = ops
                if a.type == X.X86_OP_MEM and b.type == X.X86_OP_IMM:
                    imm = b.imm & 0xFFFFFFFF
                    if IMAGE_BASE <= imm < IMAGE_BASE + 0x800000:
                        self.stores.setdefault(imm, []).append(
                            (ins.address, a.mem.disp))
            elif ins.mnemonic == 'push' and len(ops) == 1:
                o = ops[0]
                if o.type == X.X86_OP_IMM:
                    imm = o.imm & 0xFFFFFFFF
                    if TEXT_LO <= imm < TEXT_HI:
                        self.pushes.setdefault(imm, []).append(ins.address)
        self.md = md

    def insn_at(self, va, n=1):
        code = bytes(self.code[va - self.lo:va - self.lo + 16])
        out = []
        for ins in self.md.disasm(code, va):
            out.append(ins)
            if len(out) >= n:
                break
        return out


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


def body_extent(ts, img, start, maxlen=0x1000):
    """自定界：从 start 线性反汇编到首个 ret/retf 为止（不看 atlas）。"""
    code = img.byte_at(start, maxlen)
    end = start
    for ins in ts.md.disasm(code, start):
        end = ins.address + ins.size
        if ins.mnemonic.startswith('ret') or ins.mnemonic == 'retf':
            break
    return end


def func_profile(ts, img, start, end):
    """函数体征：基类构造/析构调用、delete-flag 测试、free 桩、ret imm、有无自身装表。"""
    prof = dict(base_ctor=None, base_dtor=None, flag_test=None, free_call=None,
                ret_imm=None, callees=[])
    code = img.byte_at(start, end - start)
    import capstone
    for ins in ts.md.disasm(code, start):
        if ins.mnemonic == 'call' and ins.operands:
            o = ins.operands[0]
            if o.type == capstone.x86.X86_OP_IMM:
                t = o.imm & 0xFFFFFFFF
                prof['callees'].append(t)
                if t == BASE_CTOR:
                    prof['base_ctor'] = ins.address
                if t == 0x5F3B80:
                    prof['base_dtor'] = ins.address
                if t == FREE_STUB:
                    prof['free_call'] = ins.address
        # §13.5 (b) 的 delete 标志测试：`test <op>, 1`。本批 00763200 的形态是
        # `test al,1`（寄存器），不是 `test byte ptr [esp+X],1`，故不能只认 [esp。
        if ins.mnemonic == 'test' and ins.op_str.rstrip().endswith(', 1'):
            prof['flag_test'] = ins.address
            prof['flag_test_form'] = ins.op_str
        if ins.mnemonic == 'ret' and ins.op_str.strip():
            prof['ret_imm'] = ins.address
    prof['del_dtor'] = bool(prof['flag_test'] and prof['free_call'] and prof['ret_imm'])
    return prof


def atexit_sites(ts, img, fn):
    """`push <fn>` 后 16 字节内出现 `call 0x7C978A` ⇒ fn 是 atexit 注册的全局析构器。"""
    out = []
    import capstone
    for site in ts.pushes.get(fn, []):
        for ins in ts.insn_at(site, 4):
            if ins.mnemonic == 'call' and ins.operands and \
                    ins.operands[0].type == capstone.x86.X86_OP_IMM and \
                    (ins.operands[0].imm & 0xFFFFFFFF) == ATEXIT_REG:
                out.append((site, ins.address))
                break
            if ins.address > site + 16:
                break
    return out


# --------------------------------------------------------- ④ 正文解析（骨架同先例）
RE_A = re.compile(
    r'^④ 活表槽位见证：(?P<ident>\S+?)（vt=(?P<vt>[0-9A-F]{8})，槽 (?P<slot>\d+) '
    r'值=(?P<entry>[0-9A-F]{8})，COL=(?P<col>[0-9A-F]{8}) offset=(?P<off>-?\d+)，'
    r'RTTI=(?P<td>[0-9A-F]{8})→(?P<mg>.+?)；装表点 (?P<site>[0-9A-F]{8}) 位于 '
    r'(?P<func>.+?) 体内，entry 体外）$')
RE_B = re.compile(
    r'^ ④升级句：(?P<ident>\S+?)（④ 表属类与行名类一致，均为 (?P<cls>.+?)；'
    r'该槽即其 vt=(?P<vt>[0-9A-F]{8}) 表 slot(?P<slot>\d+)，无归属歧义）'
    r'(?P<disc>.*)$')


def parse_witness(text):
    """把 ④ 成文拆成字段；不匹配返回 None。"""
    j = text.find(WITNESS)
    if j < 0:
        return None
    seg = text[j:]
    m = RE_A.match(seg[:seg.find(' ④升级句：')] if ' ④升级句：' in seg else seg)
    if not m:
        return None
    rest = seg[m.end():]
    mb = RE_B.match(rest)
    if not mb:
        return None
    d = m.groupdict()
    d.update({('b_' + k): v for k, v in mb.groupdict().items()})
    return d


def witness_template(text):
    """把 ④ 正文的骨架抽成模板（把每个可变字段换成 <>），用于与先例逐字比对格式。"""
    j = text.find(WITNESS)
    if j < 0:
        return None
    seg = text[j:]
    k = seg.find(' ④升级句：')
    if k < 0:
        return None
    a_txt, rest = seg[:k], seg[k:]
    ma = RE_A.match(a_txt)
    if not ma:
        return None
    t = a_txt
    spans = sorted((ma.span(g) for g in ('ident', 'vt', 'slot', 'entry', 'col',
                                         'off', 'td', 'mg', 'site', 'func')),
                   reverse=True)
    for s, e in spans:
        t = t[:s] + '<>' + t[e:]
    mb = RE_B.match(rest)
    if not mb:
        return None
    # disc 段（D-47 披露）本批有、先例无 ⇒ 先按原文偏移截掉 disc，再做占位替换
    u = rest[:mb.start('disc')]
    spans = sorted((mb.span(g) for g in ('ident', 'cls', 'vt', 'slot')),
                   reverse=True)
    for s, e in spans:
        u = u[:s] + '<>' + u[e:]
    return t + u


# --------------------------------------------------------------------- 主流程
def main():
    rep = dict(batch='R16_F1_B5', rows=[], problems=[])
    exe_sha = sha256p(EXE)
    cov_sha = sha256p(COV)
    rep['exe_sha'] = exe_sha
    rep['cov_sha'] = cov_sha
    rep['cov_bytes'] = os.path.getsize(COV)
    rep['exe_bytes'] = os.path.getsize(EXE)
    print('gamemd.exe  : %d B  %s  %s' % (rep['exe_bytes'], exe_sha[:16], 'OK' if exe_sha == EXPECT_SHA else 'MISMATCH'))
    print('coverage.tsv: %d B  %s' % (rep['cov_bytes'], cov_sha))

    atlas = load_atlas()
    ranges = sorted((int(k, 16), int(k, 16) + v) for k, v in atlas.items() if v)
    # 只读纪律：把复核时刻的盘上 coverage 钉一份进本目录（已存在则不覆盖），
    # 防止并发并表把「复核基准」冲掉（本期实测发生过一次，见 VERDICT §A）。
    import shutil
    pin = os.path.join(HERE, '_pin_coverage_%s.tsv' % cov_sha[:8])
    if not os.path.isfile(pin):
        shutil.copyfile(COV, pin)
    rep['cov_pin'] = os.path.basename(pin)
    img = Img(EXE)
    ts = TextScan(img)
    print('.text scan  : insn %d skip %d [%08X,%08X)' % (ts.n_insn, ts.n_skip, ts.lo, ts.hi))

    # ---- S0 · 方法正控（证明 ㉓ 两个检测器不是恒 False/恒 True）----
    #  (a) atexit 注册识别：R14_COMMON §13.5 已知 `0040D19A push 0x40d1b0` + `0040D19F
    #      call 0x7c978a`；我的检测器必须命中这一对。
    #  (b) 删除析构器识别：§13.5 已知 `004CA770`（FactoryClass）与 `006DC470`（Tactical）
    #      为删除析构器；必须为 True，且本批 00763D90（流写出，非 dtor）必须为 False。
    #  (c) RTTI/槽位复算：已并表先例 00464AC0 的表 007E4570 slot42 必须复现。
    ctl = {}
    ctl['atexit_sites(0040D1B0)'] = atexit_sites(ts, img, 0x40D1B0)
    ctl['atexit_ok'] = any(p == 0x40D19A for p, _c in ctl['atexit_sites(0040D1B0)'])
    for fn, want in ((0x4CA770, True), (0x6DC470, True), (0x763D90, False)):
        end = body_extent(ts, img, fn)
        p = func_profile(ts, img, fn, end)
        ctl['del_dtor(%08X)' % fn] = p['del_dtor']
        ctl['del_dtor_ok(%08X)' % fn] = (p['del_dtor'] == want)
    vt0 = 0x7E4570
    r0 = rtti_triplet(img, vt0)
    ctl['rtti(007E4570)'] = dict(col='%08X' % r0['col'], td='%08X' % r0['td'],
                                 manged=r0['mangled']) if r0 else None
    ctl['slot42==00464AC0'] = bool(r0) and img.u32(vt0 + 42 * 4) == 0x464AC0
    ctl['all_ok'] = (ctl['atexit_ok'] and
                     all(v for k, v in ctl.items() if k.startswith('del_dtor_ok')) and
                     ctl['slot42==00464AC0'])
    rep['controls'] = ctl
    print('正控        : atexit=%s del_dtor=%s slot42=%s => %s' % (
        ctl['atexit_ok'],
        [v for k, v in ctl.items() if k.startswith('del_dtor_ok')],
        ctl['slot42==00464AC0'], 'OK' if ctl['all_ok'] else 'CONTROL FAILED'))

    # ---- 派生集合位置自核（判据 1-3 与盘无关，位置应稳定）----
    dset = []
    s4row = {}
    with open(SCAN4GAP, encoding='utf-8-sig') as f:
        hdr = f.readline().rstrip('\r\n').split('\t')
        for ln in f:
            c = ln.rstrip('\r\n').split('\t')
            if len(c) < 12:
                continue
            r = dict(zip(hdr, c))
            if r['same_source'] != 'no':
                continue
            try:
                nd = int(r['n_install_decoded'] or 0)
                no = int(r['n_install_outside_body'] or 0)
            except ValueError:
                continue
            if nd >= 1 and no >= 1:
                dset.append(r['entry'].upper())
                s4row[r['entry'].upper()] = r
    dset.sort(key=lambda e: int(e, 16))
    rep['dset_n'] = len(dset)
    rep['dset_pos'] = {e: i + 1 for i, e in enumerate(dset)}
    print('derived set: %d rows (card says 76); rows 73-76 = %s'
          % (len(dset), dset[72:76]))
    # 分批边界与合集自核：本批 4 行必须是派生基集第 73-76 行，且 B1-B4 与本批无交集
    with open(os.path.join(DELTA), 'rb') as f:
        _dl = [x for x in f.read().split(b'\n') if x.strip()][1:]
    dorder = [x.split(b'\t')[0].decode('ascii').upper() for x in _dl]
    rep['delta_order'] = dorder
    rep['delta_order_ok'] = (dorder == dset[72:76])
    print('delta order == dset[73..76]:', rep['delta_order_ok'], dorder)
    union_prev = {}
    for b in ('R16_F1_B1', 'R16_F1_B2', 'R16_F1_B3', 'R16_F1_B4'):
        p = os.path.join(R14, b, 'fields.tsv')
        if not os.path.isfile(p):
            continue
        with open(p, encoding='utf-8') as f:
            fl = [x for x in f.read().split('\n') if x.strip()][1:]
        union_prev[b] = [x.split('\t')[0] for x in fl]
    rep['overlap_with_prev'] = {b: sorted(set(v) & set(dorder))
                                for b, v in union_prev.items()}
    allprev = set(x for v in union_prev.values() for x in v)
    rep['union_prev_n'] = len(allprev)
    rep['union_covers_76'] = (len(allprev | set(dorder)) == len(dset))
    print('overlap with B1-B4:', rep['overlap_with_prev'],
          '; union covers 76:', rep['union_covers_76'])

    # ---- 读被审产物 ----
    with open(DELTA, 'rb') as f:
        draw = f.read()
    with open(COV, 'rb') as f:
        craw = f.read()
    dlines = [x for x in draw.split(b'\n') if x.strip()]
    rep['delta_header_ok'] = dlines[0] == (
        b'entry\tsubsystem\tname\tone_line_semantics\tgrade\tevidence_path\t'
        b'n_sources\tconflict')
    drows = [x.split(b'\t') for x in dlines[1:]]
    covmap = {}
    for x in craw.split(b'\n'):
        if not x.strip():
            continue
        c = x.split(b'\t')
        if len(c) == 8:
            covmap[c[0].decode('ascii', 'ignore').strip().upper()] = c
    print('delta rows  : %d ; header ok %s' % (len(drows), rep['delta_header_ok']))

    # 同 (site,slot) 争抢检查：先收集既有盘上 ④ 正文里的 (site, slot)
    existing_site_slot = {}
    RE_SITE = re.compile(r'装表点 ([0-9A-F]{8}) 位于')
    RE_SLOT = re.compile(r'表 slot(\d+)')
    for e, c in covmap.items():
        t = c[3].decode('utf-8', 'ignore')
        sm = RE_SITE.findall(t)
        sl = RE_SLOT.findall(t)
        if sm and sl:
            existing_site_slot.setdefault((sm[0], int(sl[-1])), []).append(e)

    for c in drows:
        entry = c[0].decode('ascii').strip().upper()
        name = c[2].decode('utf-8')
        row = dict(entry=entry, name=name, deltas=c[3].decode('utf-8'),
                   dcols=list(c))
        e = int(entry, 16)
        cls = name.rsplit('::', 1)[0] if '::' in name else None
        slot_name = int(re.search(r'slot(\d+)', name).group(1))

        # ---------- A · 最小改动与原文保全 ----------
        orig = covmap.get(entry)
        row['A_found_on_disk'] = orig is not None
        if orig:
            o_sem = orig[3]
            n_sem = c[3]
            o_txt = o_sem.decode('utf-8', 'ignore')
            n_txt = n_sem.decode('utf-8', 'ignore')
            row['A_disk_has_witness'] = WITNESS in o_txt
            if not row['A_disk_has_witness']:
                row['A_state'] = 'unmerged'
                row['A_col4_prefix'] = (n_txt.startswith(o_txt) and
                                        len(n_txt) > len(o_txt))
            else:
                # 卡面 §A 并发分支：并表员已把该行写成含 witness ⇒ 与 delta 逐字节比
                row['A_state'] = 'merged_by_concurrent_writer'
                row['A_merged_equal'] = (n_txt == o_txt)
                row['A_col4_prefix'] = row['A_merged_equal']
            row['A_others_identical'] = all(c[i] == orig[i]
                                            for i in (0, 1, 2, 4, 5, 6, 7))
            row['A_grade'] = orig[4].decode('utf-8', 'ignore')
            row['A_grade_ok'] = orig[4].decode('utf-8', 'ignore') == '[已证]'
            row['A_orig_had_witness'] = WITNESS in o_txt
            row['A_orig_4count'] = o_txt.count('④')
            # 追加段（对 F 反抄袭与 D 解析都用这一段，两种盘状态下都可取）
            jw = n_txt.find(WITNESS)
            row['A_appended'] = n_txt[max(0, jw - 2):] if jw >= 0 else ''

        # ---------- D · 文本解析 ----------
        wit = parse_witness(row['deltas'])
        row['D_parsed'] = wit is not None
        if not wit:
            rep['rows'].append(row)
            rep['problems'].append((entry, 'D', '④ 正文无法按先例骨架解析'))
            continue
        row.update(dict(wit))

        vt = int(wit['vt'], 16)
        slot = int(wit['slot'])
        col = int(wit['col'], 16)
        off = int(wit['off'])
        td = int(wit['td'], 16)
        site = int(wit['site'], 16)

        # ---------- B · 8 项独立复算 ----------
        meas = {}
        meas['vt_slot_value'] = img.u32(vt + slot * 4)
        meas['vt_minus4'] = img.u32(vt - 4)
        meas['col_plus4'] = img.u32(col + 4)
        meas['col_plus12'] = img.u32(col + 12)
        meas['td_plus8'] = img.cstr(td + 8, 256)
        meas['site_insn'] = None
        meas['site_imm'] = None
        insl = ts.insn_at(site, 1)
        if insl:
            ins = insl[0]
            meas['site_insn'] = '%s %s' % (ins.mnemonic, ins.op_str)
            import capstone
            ops = ins.operands
            if ins.mnemonic == 'mov' and len(ops) == 2 and \
                    ops[0].type == capstone.x86.X86_OP_MEM and \
                    ops[1].type == capstone.x86.X86_OP_IMM:
                meas['site_imm'] = ops[1].imm & 0xFFFFFFFF
        b = {}
        b['1 u32(vt+slot*4)==entry'] = meas['vt_slot_value'] == e
        b['2 u32(vt-4)==COL'] = meas['vt_minus4'] == col
        b['3 u32(COL+4)==offset'] = meas['col_plus4'] == off
        b['4 u32(COL+12)==TD'] = meas['col_plus12'] == td
        b['5 cstr(TD+8)==mangled'] = meas['td_plus8'] == wit['mg']
        b['6 site mov,imm32==vt'] = meas['site_imm'] == vt
        # 7: 装表点所在函数 != entry（atlas + 自定界双证）
        esize = atlas.get(entry)
        f_atlas = which_body(ranges, site)
        own_end = body_extent(ts, img, e)
        row['B_entry_atlas_size'] = esize
        row['B_entry_selfend'] = '%08X' % own_end
        own_prof = func_profile(ts, img, e, own_end)
        row['B_entry_profile'] = dict(
            del_dtor=own_prof['del_dtor'],
            flag_form=own_prof.get('flag_test_form'),
            free_call='%08X' % own_prof['free_call'] if own_prof['free_call'] else None,
            ret_imm='%08X' % own_prof['ret_imm'] if own_prof['ret_imm'] else None,
            base_ctor='%08X' % own_prof['base_ctor'] if own_prof['base_ctor'] else None,
            base_dtor='%08X' % own_prof['base_dtor'] if own_prof['base_dtor'] else None,
            self_installs=['%08X' % s for s, _d in ts.stores.get(vt, [])
                           if e <= s < max(own_end, e + (esize or 0))])
        b['7 site_func!=entry'] = (f_atlas is not None and f_atlas != e)
        b['7b site_outside_own_body'] = not (e <= site < own_end) and \
            (esize is None or not (e <= site < e + esize))
        row['B_site_func_atlas'] = '%08X' % f_atlas if f_atlas else None
        # 8: TD+8 类名与行名前缀同类（精确解析装饰名）
        dec = decor_class(wit['mg'])
        b['8 TD+8 class==row class'] = (dec == cls)
        row['B_decor_class'] = dec
        row['B_checks'] = b
        row['B_meas'] = {'vt_slot_value': '%08X' % meas['vt_slot_value'],
                         'vt_minus4': '%08X' % meas['vt_minus4'],
                         'col_plus4': meas['col_plus4'],
                         'col_plus12': '%08X' % meas['col_plus12'],
                         'td_plus8': meas['td_plus8'],
                         'site_insn': meas['site_insn'],
                         'site_imm': '%08X' % meas['site_imm'] if meas['site_imm'] else None}

        # 文本一致性（D）：文本里的地址 vs 实测
        d_ok = {}
        d_ok['ident==name'] = (wit['ident'] == name and wit['b_ident'] == name)
        d_ok['text_entry==row'] = (wit['entry'] == entry)
        d_ok['text_slot==name_slot'] = (slot == slot_name and int(wit['b_slot']) == slot)
        d_ok['text_vt==meas_vt'] = (int(wit['b_vt'], 16) == vt)
        d_ok['text_slot_value==entry'] = (meas['vt_slot_value'] == e)
        d_ok['text_col==u32(vt-4)'] = (meas['vt_minus4'] == col)
        d_ok['text_td==u32(col+12)'] = (meas['col_plus12'] == td)
        d_ok['text_mg==cstr(td+8)'] = (meas['td_plus8'] == wit['mg'])
        d_ok['text_cls==name_cls'] = (wit['b_cls'] == cls)
        d_ok['text_func==site_body'] = (row['B_site_func_atlas'] is not None and
                                        wit['func'] == row['B_site_func_atlas'])
        d_ok['disc==consensus'] = (wit['b_disc'] == DISC_S12_6)
        d_ok['has_12.6'] = ('§12.6' in row['deltas'])
        d_ok['no_12.4'] = ('§12.4' not in row['deltas'])
        row['D_checks'] = d_ok

        # ---------- C · 定表唯一性（该 entry 被几张活表在同一槽号持有）----------
        cands = []
        hits = dd_hits(img, e)
        for hit in hits:
            ws = vtable_start(img, hit)
            if ws is None:
                cands.append(dict(hit=hit, vt=None, slot=None, mg=None,
                                  cls=None, live=False, sites=0))
                continue
            v, t = ws
            inst = ts.stores.get(v, [])
            cands.append(dict(hit=hit, vt=v, slot=(hit - v) // 4, mg=t['mangled'],
                              cls=decor_class(t['mangled']), live=bool(inst),
                              sites=len(inst),
                              site_list=['%08X' % s for s, _d in inst],
                              cls_match=(decor_class(t['mangled']) == cls)))
        row['C_dd_hits'] = len(hits)
        row['C_cands'] = [{k: (('%08X' % v) if k in ('hit', 'vt') and v else v)
                           for k, v in cd.items() if k not in ('site_list', 'cls')}
                          for cd in cands]
        row['C_n_tables'] = len(set(cd['vt'] for cd in cands if cd['vt']))
        elig = [cd for cd in cands if cd['vt'] and cd['live'] and
                cd['slot'] == slot_name and cd['cls_match']]
        row['C_n_eligible_at_slot'] = len(elig)
        row['C_eligible_vts'] = ['%08X' % cd['vt'] for cd in elig]
        # 同 vt 但别的槽号（说明表里还有本 entry 的其他槽）
        row['C_other_slots_same_vt'] = sorted(set(
            cd['slot'] for cd in cands if cd['vt'] == vt and cd['slot'] != slot))
        # 同 (site,slot) 争抢（含既有已并表行）
        key = ('%08X' % site, slot)
        row['C_site_slot_conflict'] = [x for x in existing_site_slot.get(key, [])
                                       if x != entry]
        # 本批内共用同一装表点
        row['C_site'] = key[0]

        # ---------- §C Q3 · 选中的装表点是否 ring4_at 指定站点 ----------
        ra = (s4row.get(entry) or {}).get('ring4_at', '')
        toks = re.findall(r'[0-9A-Fa-f]{8}', ra)
        row['C_ring4_tokens'] = [t.upper() for t in toks]
        row['C_chosen_in_ring4'] = wit['site'] in row['C_ring4_tokens']
        row['C_func_in_ring4'] = (row['B_site_func_atlas'] in row['C_ring4_tokens'])
        row['C_ring4_at'] = ra
        # ring4_at 里被本行排除的其他 token（应落在 entry 体内）
        row['C_ring4_excluded'] = [t for t in row['C_ring4_tokens']
                                   if t != wit['site']]

        # ---------- ㉓ · 该表全部写点枚举与分类（§13.5 判据）----------
        all_sites = ts.stores.get(vt, [])
        enum = []
        for s_va, _disp in all_sites:
            f = which_body(ranges, s_va)
            in_entry = (f == e) or (e <= s_va < own_end)
            fn = f if f is not None else None
            at = atexit_sites(ts, img, fn) if fn else []
            prof = None
            if fn is not None:
                fend = fn + atlas.get('%08X' % fn, 0)
                prof = func_profile(ts, img, fn, fend)
            kind = []
            if in_entry:
                kind.append('行自身体内')
            if at:
                kind.append('atexit 全局析构器体内')
            if prof and prof['del_dtor']:
                kind.append('删除析构器体内')
            enum.append(dict(site='%08X' % s_va,
                             func='%08X' % fn if fn else None,
                             in_entry=in_entry,
                             atexit=bool(at),
                             atexit_reg=['%08X' % p for p in at],
                             del_dtor=bool(prof and prof['del_dtor']),
                             flag_test='%08X' % prof['flag_test'] if prof and prof['flag_test'] else None,
                             flag_form=(prof.get('flag_test_form') if prof else None),
                             free_call='%08X' % prof['free_call'] if prof and prof['free_call'] else None,
                             base_ctor='%08X' % prof['base_ctor'] if prof and prof['base_ctor'] else None,
                             base_dtor='%08X' % prof['base_dtor'] if prof and prof['base_dtor'] else None,
                             excluded=bool(kind),
                             kind='+'.join(kind) or '构造器侧/可采'))
        row['T_sites'] = enum
        # 选中的这一处：必须不被排除
        chosen = [x for x in enum if x['site'] == wit['site']]
        row['T_chosen'] = chosen[0] if chosen else None
        row['T_chosen_admissible'] = bool(chosen) and not chosen[0]['excluded']

        rep['rows'].append(row)
        print('\n[%s] %s  slot=%d vt=%s site=%s func=%s' % (
            entry, name, slot, wit['vt'], wit['site'], row['B_site_func_atlas']))
        print('   A  : state=%s prefix=%s others_same=%s grade=%s grade_ok=%s '
              'pre4count=%d appended_len=%d' % (
                  row.get('A_state'), row.get('A_col4_prefix'),
                  row.get('A_others_identical'), row.get('A_grade'),
                  row.get('A_grade_ok'), row.get('A_orig_4count', -1),
                  len(row.get('A_appended') or '')))
        print('   B8 :', ' '.join('%s=%s' % (k, 'T' if v else 'F') for k, v in b.items()))
        print('   B* : atlas_size=%s self_end=%s entry_profile=%s' % (
            esize, '%08X' % own_end, row['B_entry_profile']))
        print('   D  :', ' '.join('%s=%s' % (k, 'T' if v else 'F') for k, v in d_ok.items()))
        print('   C  : dd_hits=%d tables=%d eligible@slot%d=%d other_slots=%s site_slot_conflict=%s'
              % (row['C_dd_hits'], row['C_n_tables'], slot_name,
                 row['C_n_eligible_at_slot'], row['C_other_slots_same_vt'],
                 row['C_site_slot_conflict']))
        print('   C* : ring4_at=%r chosen_in_ring4=%s func_in_ring4=%s excluded_tokens=%s'
              % (row['C_ring4_at'], row['C_chosen_in_ring4'], row['C_func_in_ring4'],
                 row['C_ring4_excluded']))
        print('   T  : table %s write points = %s' % (wit['vt'], len(enum)))
        for x in enum:
            print('        %s func=%s %s%s%s -> %s' % (
                x['site'], x['func'],
                'IN_ENTRY ' if x['in_entry'] else '',
                'ATEXIT(%s) ' % ','.join(x['atexit_reg']) if x['atexit'] else '',
                'DEL_DTOR ' if x['del_dtor'] else '',
                'EXCLUDED' if x['excluded'] else 'admissible'))

    # ---------- A' · 多快照稳定性矩阵（盘被并发并表反复改写时的必备证据）----------
    def snap_cols(raw):
        m = {}
        for x in raw.split(b'\n'):
            if not x.strip():
                continue
            c = x.split(b'\t')
            if len(c) == 8:
                m.setdefault(c[0].decode('ascii', 'ignore').strip().upper(), c)
        return m

    snaps = [('live', cov_sha, craw)]
    for fn in sorted(os.listdir(HERE)):
        if fn.startswith('_pin_coverage_') and fn.endswith('.tsv'):
            p = os.path.join(HERE, fn)
            with open(p, 'rb') as f:
                rb = f.read()
            snaps.append((fn, sha256p(p), rb))
    matrix = {}
    for tag, sha, raw in snaps:
        sc = snap_cols(raw)
        per = {}
        for r in rep['rows']:
            e = r['entry']
            o = sc.get(e)
            if o is None:
                per[e] = 'absent'
                continue
            o_t = o[3].decode('utf-8', 'ignore')
            n_t = r['deltas']
            has_w = WITNESS in o_t
            if has_w:
                ok = (n_t == o_t)
                st = 'merged_equal' if ok else 'merged_conflict'
            else:
                ok = n_t.startswith(o_t) and len(n_t) > len(o_t)
                st = 'unmerged_prefix' if ok else 'prefix_broken'
            same_other = all(r['dcols'][i] == o[i] for i in (0, 1, 2, 4, 5, 6, 7))
            per[e] = '%s|others=%s|grade=%s' % (
                st, 'same' if same_other else 'DIFF',
                o[4].decode('utf-8', 'ignore'))
        matrix['%s@%s' % (tag, sha[:8])] = dict(sha=sha, bytes=len(raw), rows=per)
    rep['A_matrix'] = matrix
    print('\n[A\'] 多快照矩阵（本批 4 行在每一份观测快照上的状态）:')
    for k, v in matrix.items():
        print('   %-28s %d B' % (k, v['bytes']))
        for e, s in v['rows'].items():
            print('       %s  %s' % (e, s))
    rep['A_matrix_all_ok'] = all(
        s.split('|')[0] in ('unmerged_prefix', 'merged_equal') and
        s.split('|')[1] == 'others=same' and s.split('|')[2] == 'grade=[已证]'
        for v in matrix.values() for s in v['rows'].values())
    print("   => all snapshots ok:", rep['A_matrix_all_ok'])

    # ---------- E · 格式合先例（用同一骨架正则回解先例三行 + 模板逐字比对）----------
    eprec = {}
    prec_tpl = {}
    for p in PRECEDENTS:
        cc = covmap.get(p)
        if not cc:
            eprec[p] = 'NOT_ON_DISK'
            continue
        t = cc[3].decode('utf-8', 'ignore')
        eprec[p] = 'parsed_ok' if parse_witness(t) else 'parse_fail'
        prec_tpl[p] = witness_template(t)
    rep['E_precedent_skeleton'] = eprec
    rep['E_precedent_template'] = prec_tpl
    my_tpl = {}
    for r in rep['rows']:
        my_tpl[r['entry']] = witness_template(r['deltas'])
    rep['E_my_template'] = my_tpl
    uniq_prec = set(v for v in prec_tpl.values() if v)
    rep['E_template_matches_precedent'] = {
        e: (t is not None and len(uniq_prec) == 1 and t == list(uniq_prec)[0])
        for e, t in my_tpl.items()}
    print('\n[E] precedent skeleton parse:', eprec)
    print('[E] template identical to precedent (values aside):',
          rep['E_template_matches_precedent'],
          '; precedent templates distinct =', len(uniq_prec))

    # E2 · 卡面点名的 R16_SLOTN_B1 / B3 已并表行也回解一遍（加宽先例面）
    e2 = {}
    for b in ('R16_SLOTN_B1', 'R16_SLOTN_B3'):
        p = os.path.join(R14, b, 'fields.tsv')
        if not os.path.isfile(p):
            continue
        with open(p, encoding='utf-8') as f:
            ent = [x.split('\t')[0] for x in f.read().split('\n')[1:] if x.strip()]
        ok = tpl_ok = miss = 0
        for en in ent:
            cc = covmap.get(en.upper())
            if not cc:
                miss += 1
                continue
            t = cc[3].decode('utf-8', 'ignore')
            if parse_witness(t):
                ok += 1
                if witness_template(t) in uniq_prec and len(uniq_prec) == 1:
                    tpl_ok += 1
        e2[b] = dict(entries=len(ent), parsed=ok, template_same=tpl_ok, absent=miss)
    rep['E_slotn_precedent'] = e2
    print('[E2] SLOTN 并表行回解:', e2)

    # ---------- F · 反抄袭 ----------
    texts = [r.get('A_appended') for r in rep['rows']]
    norm = [re.sub(r'[0-9A-F]{8}', 'E', t or '') for t in texts]
    rep['F_distinct_full'] = len(set(texts))
    rep['F_distinct_norm'] = len(set(norm))
    pairs = []
    for i in range(len(norm)):
        for j in range(i + 1, len(norm)):
            if norm[i] == norm[j]:
                pairs.append((rep['rows'][i]['entry'], rep['rows'][j]['entry']))
    rep['F_dup_pairs'] = pairs
    print('[F] distinct full %d/%d ; entry-normalized %d/%d ; dup pairs %s'
          % (len(set(texts)), len(texts), len(set(norm)), len(norm), pairs))

    # 槽值互换检查（00772CD0 / 00772EB0）
    rep['F_slot_swap_check'] = {}
    for r in rep['rows']:
        rep['F_slot_swap_check'][r['entry']] = dict(
            name_slot=int(re.search(r'slot(\d+)', r['name']).group(1)),
            text_slot=int(r['slot']),
            table_slot_value=r['B_meas']['vt_slot_value'],
            equals_entry=(int(r['B_meas']['vt_slot_value'], 16) == int(r['entry'], 16)))

    # 同 vt 两行（slot5/slot6）的正文差异点定位：必须只差在槽号处
    import difflib
    byvt = {}
    for r in rep['rows']:
        byvt.setdefault(r['vt'], []).append(r)
    rep['F_same_vt_groups'] = {}
    for vt, rs in byvt.items():
        if len(rs) < 2:
            continue
        a = re.sub(r'[0-9A-F]{8}', 'E', rs[0]['A_appended'])
        b2 = re.sub(r'[0-9A-F]{8}', 'E', rs[1]['A_appended'])
        sm = difflib.SequenceMatcher(None, a, b2)
        diffs = [(a[i1:i2], b2[j1:j2]) for tag, i1, i2, j1, j2 in
                 sm.get_opcodes() if tag != 'equal']
        rep['F_same_vt_groups'][vt] = dict(
            entries=[rs[0]['entry'], rs[1]['entry']],
            n_diff_blocks=len(diffs),
            diff_blocks=[list(x) for x in diffs],
            only_slot_differs=all(set(x[0]) <= set('sl ot0123456789')
                                  for x in diffs) or all(
                ('slot' in x[0] or '槽' in x[0] or x[0].strip().isdigit())
                for x in diffs))
    print('[F] same-vt groups:', json.dumps(rep['F_same_vt_groups'],
                                           ensure_ascii=False))

    # ---------- fields.tsv 结构自核（卡面 §2 被审对象）----------
    fcheck = dict(rows=0, header_cols=0, problems=[])
    with open(FIELDS, encoding='utf-8') as f:
        fl = [x for x in f.read().split('\n') if x.strip()]
    if fl:
        fcheck['header_cols'] = len(fl[0].split('\t'))
        for ln in fl[1:]:
            c = ln.split('\t')
            fcheck['rows'] += 1
            if len(c) != 14:
                fcheck['problems'].append((c[0], 'cols=%d' % len(c)))
                continue
            r = [x for x in rep['rows'] if x['entry'] == c[0]]
            if not r:
                continue
            r = r[0]
            if c[12] != 'no':
                fcheck['problems'].append((c[0], 'same_source=%s' % c[12]))
            for idx, key in ((3, 'vt'), (5, 'col'), (6, 'off'), (7, 'td'),
                             (8, 'mg'), (9, 'site')):
                if c[idx] != str(r[key]):
                    fcheck['problems'].append(
                        (c[0], '字段%d %r!=%r' % (idx + 1, c[idx], str(r[key]))))
            if c[10] != str(r.get('B_site_func_atlas')):
                fcheck['problems'].append(
                    (c[0], 'install_func %r!=%r' % (c[10], r.get('B_site_func_atlas'))))
            if c[11] != 'OK':
                fcheck['problems'].append((c[0], 'status=%s' % c[11]))
    rep['fields_check'] = fcheck
    print('[fields] rows=%d header_cols=%d problems=%s'
          % (fcheck['rows'], fcheck['header_cols'], fcheck['problems']))

    # ---------- 写 bytecheck.tsv ----------
    cols = ['entry', 'name', 'slot', 'vt', 'col', 'off', 'td', 'mangled',
            'site', 'site_func', 'entry_atlas_size', 'entry_self_end',
            'meas_u32(vt+slot*4)', 'meas_u32(vt-4)', 'meas_u32(COL+4)',
            'meas_u32(COL+12)', 'meas_cstr(TD+8)', 'meas_site_insn',
            'meas_site_imm', 'b1', 'b2', 'b3', 'b4', 'b5', 'b6', 'b7', 'b7b', 'b8',
            'A_col4_prefix', 'A_others_identical', 'A_grade_ok',
            'D_all_ok', 'C_dd_hits', 'C_tables', 'C_eligible_at_slot',
            'T_write_points', 'T_chosen_admissible', 'T_chosen_kind']
    with open(OUT_TSV, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\t'.join(cols) + '\n')
        for r in rep['rows']:
            m = r['B_meas']
            b = r['B_checks']
            f.write('\t'.join([
                r['entry'], r['name'], str(r['slot']), r['vt'], r['col'],
                str(r['off']), r['td'], r['mg'], r['site'],
                str(r.get('B_site_func_atlas')), str(r.get('B_entry_atlas_size')),
                str(r.get('B_entry_selfend')),
                m['vt_slot_value'], m['vt_minus4'], str(m['col_plus4']),
                m['col_plus12'], str(m['td_plus8']), str(m['site_insn']),
                str(m['site_imm']),
                *['T' if b[k] else 'F' for k in
                  ['1 u32(vt+slot*4)==entry', '2 u32(vt-4)==COL',
                   '3 u32(COL+4)==offset', '4 u32(COL+12)==TD',
                   '5 cstr(TD+8)==mangled', '6 site mov,imm32==vt',
                   '7 site_func!=entry', '7b site_outside_own_body',
                   '8 TD+8 class==row class']],
                'T' if r.get('A_col4_prefix') else 'F',
                'T' if r.get('A_others_identical') else 'F',
                'T' if r.get('A_grade_ok') else 'F',
                'T' if all(r['D_checks'].values()) else 'F',
                str(r['C_dd_hits']), str(r['C_n_tables']),
                str(r['C_n_eligible_at_slot']),
                str(len(r['T_sites'])),
                'T' if r['T_chosen_admissible'] else 'F',
                (r['T_chosen']['kind'] if r['T_chosen'] else 'MISSING'),
            ]) + '\n')

    with open(OUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(rep, f, ensure_ascii=False, indent=1, default=str)
    print('\nwrote', OUT_TSV)
    print('wrote', OUT_JSON)
    return 0


if __name__ == '__main__':
    sys.exit(main())
