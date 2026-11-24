# -*- coding: utf-8 -*-
"""
R16-AUDIT-OTHER14 — 独立复算脚本（审计员自写；不 import 执行器的 scan.py / gen_products.py）。

只读输入：
    ra2youli/gamemd.exe
    lead/next_re_20261117_r14/COVERAGE/coverage.tsv
    lead/next_re_20261117_r14/R16_F1_OTHER14/{delta.tsv,fields.tsv}
    lead/next_re_20261112_r10/W130_atlas/function_atlas.tsv
只写本目录：check14.tsv / verify_out.json

独立性：
  * PE 映射、u32/cstr、.text 线性反汇编、atlas 区间查表本脚本自实现（不调 probe.py）。
  * §B 装表点不采信执行器记录的 install，自己全扫 .text 收 `mov [mem],imm32==vt` 再判声明站点
    是否在集合内、是否在 entry 体外。
  * §C「填充定界反推」不采信执行器的 derive_host，独立做四件事：
      1) 从声明宿主向前数连续 0x90/0xCC，要求 >=2 且 run 前一字节是终止指令(C3/C2/E9/EB)；
      2) 从宿主**不带 skipdata**线性反汇编到站点，要求精确落在站点、无 (bad)；
      3) 确认 host..site 之间没有别的填充 run（即这就是"最近的前一个函数边界"）；
      4) 交叉验证：.data 起始检出升序 .text 代码指针表（静态初始化表），看宿主是否成员、
         并核宿主函数形态（是否 ret 结尾 + 写全局）。
  * §D 用「④ 里所有 8 位十六进制 token 必须能被实测值解释」做兜底。

跑法： python verify.py
"""
import os
import sys
import re
import json
import bisect
import hashlib

sys.dont_write_bytecode = True
import pefile
import capstone

HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(R14))
EXE = os.path.join(ROOT, 'ra2youli', 'gamemd.exe')
COV = os.path.join(R14, 'COVERAGE', 'coverage.tsv')
SRC = os.path.join(R14, 'R16_F1_OTHER14')
DELTA = os.path.join(SRC, 'delta.tsv')
FIELDS = os.path.join(SRC, 'fields.tsv')
ATLAS = os.path.join(ROOT, 'lead', 'next_re_20261112_r10', 'W130_atlas',
                     'function_atlas.tsv')
OUT_TSV = os.path.join(HERE, 'check14.tsv')
OUT_JSON = os.path.join(HERE, 'verify_out.json')

EXPECT_EXE_SHA = '73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476'
X = capstone.x86


# --------------------------------------------------------------------------- 基础
def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest().upper()


class Img(object):
    """自实现 PE 平铺映射（VA -> 镜像字节）。"""

    def __init__(self, path):
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
            o = s['va'] - self.base
            self.buf[o:o + len(s['data'])] = s['data']

    def sec_of(self, va):
        for s in self.secs:
            if s['va'] <= va < s['va'] + max(s['vsize'], s['rsize']):
                return s['name']
        return None

    def sec_by_name(self, nm):
        for s in self.secs:
            if s['name'] == nm:
                return s
        return None

    def ok(self, va):
        return va is not None and self.base <= va < self.base + len(self.buf)

    def u32(self, va):
        if not self.ok(va):
            return None
        o = va - self.base
        return int.from_bytes(self.buf[o:o + 4], 'little')

    def raw(self, va, n):
        o = va - self.base
        if o < 0:
            return b''
        return bytes(self.buf[o:o + n])

    def cstr(self, va, n=256):
        o = va - self.base
        if o < 0 or o >= len(self.buf):
            return None
        e = self.buf.find(b'\x00', o, min(o + n, len(self.buf)))
        if e < 0:
            return None
        return self.buf[o:e].decode('latin-1')


class Text(object):
    """.text 一次线性反汇编（skipdata，供装表点检索）。"""

    def __init__(self, img):
        t = img.sec_by_name('.text')
        self.lo = t['va']
        n = min(len(t['data']), t['vsize'] or len(t['data']))
        self.code = bytes(t['data'][:n])
        self.hi = self.lo + len(self.code)
        self.stores = {}
        self.n_insn = 0
        self.n_skip = 0
        md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
        md.detail = True
        md.skipdata = True
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
                    if 0x400000 <= imm < 0x800000:
                        self.stores.setdefault(imm, []).append((ins.address, a.mem.disp))
        self.direct_sites = {}

    def installs_of(self, vt):
        return self.stores.get(vt, [])


def load_atlas():
    sizes = {}
    with open(ATLAS, encoding='utf-8-sig') as f:
        f.readline()
        for ln in f:
            c = ln.rstrip('\r\n').split('\t')
            if len(c) < 2:
                continue
            try:
                sizes[c[0].strip().upper()] = int(c[1])
            except ValueError:
                pass
    ranges = sorted((int(k, 16), int(k, 16) + v) for k, v in sizes.items() if v)
    return sizes, ranges


def body_of(ranges, va):
    i = bisect.bisect_right(ranges, (va, 1 << 62)) - 1
    while i >= 0:
        s, e = ranges[i]
        if s <= va < e:
            return s
        if e <= va:
            return None
        i -= 1
    return None


def find_init_table(img):
    """在 .data 里找升序 .text 代码指针连段；取起始地址最小且够长的那个 = 静态初始化表。

    独立于填充反推的第三方证据：初始化表里装的是**函数入口**；非入口地址不会被装表。
    """
    d = img.sec_by_name('.data')
    tv = img.sec_by_name('.text')
    tlo, thi = tv['va'], tv['va'] + len(tv['data'])
    base_va, data = d['va'], d['data']
    n = len(data) // 4
    vals = [int.from_bytes(data[4 * i:4 * i + 4], 'little') for i in range(n)]

    def is_text(v):
        return tlo <= v < thi

    runs = []
    i = 0
    while i < n:
        if not is_text(vals[i]):
            i += 1
            continue
        j = i
        while j + 1 < n and is_text(vals[j + 1]) and vals[j + 1] > vals[j]:
            j += 1
        if j - i + 1 >= 50:
            runs.append((j - i + 1, i, j))
        i = j + 1
    if not runs:
        return dict(n=0, lo=None, hi=None, members=set(), runs=[])
    runs.sort(key=lambda t: t[1])          # 起始下标最小者
    ln, s, e = runs[0]
    return dict(n=ln, lo=base_va + 4 * s, hi=base_va + 4 * e,
                members=set(vals[s:e + 1]),
                runs=[(base_va + 4 * a, base_va + 4 * b, c) for c, a, b in runs])


# --------------------------------------------------------------------------- 输入
def read_tsv(path):
    with open(path, 'rb') as f:
        raw = f.read()
    lines = raw.split(b'\n')
    hdr = [c.decode('utf-8', 'replace') for c in lines[0].rstrip(b'\r').split(b'\t')]
    rows = [ln.rstrip(b'\r').split(b'\t') for ln in lines[1:] if ln.strip()]
    return hdr, rows


def load_coverage():
    with open(COV, 'rb') as f:
        raw = f.read()
    cov, dup = {}, []
    for ln in raw.split(b'\n'):
        if not ln:
            continue
        c = ln.rstrip(b'\r').split(b'\t')
        if len(c) != 8:
            continue
        try:
            e = c[0].decode('ascii').strip().upper()
        except Exception:
            continue
        if e in cov:
            dup.append(e)
        cov[e] = c
    return cov, len(raw), dup


# --------------------------------------------------------------------------- 文本解析
RE_SLOT = re.compile(r'slot(\d+)（vt=([0-9A-Fa-f]{8})，槽 (\d+) 值=([0-9A-Fa-f]{8})，'
                     r'COL=([0-9A-Fa-f]{8}) offset=(\d+)，RTTI=([0-9A-Fa-f]{8})→([^；）]+)')
RE_INST = re.compile(r'装表点 ([0-9A-Fa-f]{8}) 位于 ([0-9A-Fa-f]{8}) 体内')
RE_SITE = re.compile(r'调用站点 ([0-9A-Fa-f]{8}) 处指令 ((?:[0-9A-Fa-f]{2} ?)+?)（')
RE_REL = re.compile(r'site\+5\+rel32==([0-9A-Fa-f]{8})')
RE_ENTRY = re.compile(r'被调 entry=([0-9A-Fa-f]{8})')
RE_HOSTF = re.compile(r'站点位于工厂 ([0-9A-Fa-f]{8}) 体内')
RE_HEX8 = re.compile(r'(?<![0-9A-Fa-f])[0-9A-Fa-f]{8}(?![0-9A-Fa-f])')


def parse_slot_text(seg):
    m = RE_SLOT.search(seg)
    if not m:
        return None
    inst = RE_INST.search(seg)
    return dict(slot=int(m.group(3)), vt=int(m.group(2), 16),
                slot_val=int(m.group(4), 16), col=int(m.group(5), 16),
                offset=int(m.group(6)), td=int(m.group(7), 16),
                mangled=m.group(8).strip(),
                install=(int(inst.group(1), 16) if inst else None),
                host=(int(inst.group(2), 16) if inst else None))


def parse_direct_text(seg):
    s = RE_SITE.search(seg)
    return dict(site=(int(s.group(1), 16) if s else None),
                bytes_txt=(''.join(s.group(2).split()).upper() if s else None),
                rel_target=(lambda m: int(m.group(1), 16) if m else None)(RE_REL.search(seg)),
                entry_txt=(lambda m: int(m.group(1), 16) if m else None)(RE_ENTRY.search(seg)),
                host=(lambda m: int(m.group(1), 16) if m else None)(RE_HOSTF.search(seg)))


# --------------------------------------------------------------------------- 反汇编工具
def decode_at(img, va):
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = True
    return next(md.disasm(img.raw(va, 16), va), None)


def disasm_clean(img, lo, hi):
    """不带 skipdata 的干净反汇编；出现 (bad) 即失败。"""
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = True
    out, ok = [], True
    for ins in md.disasm(img.raw(lo, hi - lo), lo):
        if ins.id == 0:
            ok = False
            break
        out.append(ins)
        if ins.address + ins.size > hi:
            break
    return out, ok


def padding_runs(img, va, max_back=1024):
    o = va - img.base
    runs, i = [], max(0, o - max_back)
    while i < o:
        if img.buf[i] in (0xCC, 0x90):
            j = i
            while j < o and img.buf[j] in (0xCC, 0x90):
                j += 1
            if j - i >= 2:
                runs.append(dict(start=img.base + i, end=img.base + j, length=j - i,
                                 byte=img.buf[i],
                                 prev=(img.buf[i - 1] if i >= 1 else None)))
            i = j
        else:
            i += 1
    return runs


def fn_shape(img, va, horizon=200):
    """宿主函数形态：是否 ret 结尾、是否写全局。"""
    ins, ok = disasm_clean(img, va, va + horizon)
    has_ret = any(i.mnemonic.startswith('ret') for i in ins)
    n_write = 0
    for i in ins:
        if i.mnemonic == 'mov' and len(i.operands) == 2:
            a = i.operands[0]
            if a.type == X.X86_OP_MEM and a.mem.base == X.X86_REG_INVALID:
                n_write += 1
    return dict(clean=ok, has_ret=has_ret, n_global_write=n_write, n_insn=len(ins))


# --------------------------------------------------------------------------- 主流程
def main():
    exe_sha = sha256(EXE)
    cov_sha = sha256(COV)
    if exe_sha != EXPECT_EXE_SHA:
        raise RuntimeError('gamemd.exe sha 与基线不符: %s' % exe_sha)

    img = Img(EXE)
    ts = Text(img)
    atlas, ranges = load_atlas()
    itab = find_init_table(img)
    cov, cov_len, cov_dup = load_coverage()
    dhdr, drows = read_tsv(DELTA)
    fhdr, frows = read_tsv(FIELDS)

    # 执行器 scan 时的快照（用于判「并发写者是否动过这 14 行」）
    snap = {}
    snap_meta = {}
    snap_path = os.path.join(SRC, 'scan_raw.json')
    if os.path.isfile(snap_path):
        with open(snap_path, encoding='utf-8') as f:
            sj = json.load(f)
        snap_meta = dict(cov_sha_before=sj.get('cov_sha_before'),
                         cov_bytes=sj.get('cov_bytes'))
        for r in sj.get('rows', []):
            snap[r['entry'].upper()] = dict(pre_sem=r.get('pre_sem'),
                                            cov_cols=r.get('cov_cols'))

    print('exe  : %d B sha %s' % (os.path.getsize(EXE), exe_sha))
    print('cov  : %d B sha %s rows=%d dup=%d' % (cov_len, cov_sha, len(cov), len(cov_dup)))
    print('.text: %08X..%08X insn=%d skip=%d' % (ts.lo, ts.hi, ts.n_insn, ts.n_skip))
    print('atlas: %d fn' % len(atlas))
    print('init tables in .data: %s' % '; '.join(
        '%08X..%08X n=%d' % t for t in itab['runs']))

    # 表的性质抽检：成员是否都是「ret 结尾、写全局」的初始化体
    members_sorted = sorted(itab['members'])
    step = max(1, len(members_sorted) // 40)
    sampled = members_sorted[::step][:40]
    shp = [fn_shape(img, m) for m in sampled]
    print('init table shape sample: n=%d, ret 结尾 %d, 至少写 1 个全局 %d'
          % (len(shp), sum(1 for s in shp if s['has_ret']),
             sum(1 for s in shp if s['n_global_write'] > 0)))

    assert dhdr[0] == 'entry' and len(dhdr) == 8, dhdr
    assert dhdr[3] == 'one_line_semantics'
    assert len(drows) == 14, len(drows)
    fmap = {c[0].decode().strip().upper(): c for c in frows}

    recs = []
    for c in drows:
        entry = c[0].decode().strip().upper()
        e = int(entry, 16)
        r = dict(entry=entry, notes=[])
        delta_sem = c[3]
        cov_row = cov.get(entry)

        # -------- §A 最小改动 / 原文保全
        if cov_row is None:
            r['A_prefix_ok'] = r['A_cols_ok'] = False
            r['A_cov_has4'] = None
            cov_sem = b''
            r['notes'].append('entry 不在盘上 coverage.tsv')
        else:
            cov_sem = cov_row[3]
            r['A_prefix_ok'] = delta_sem.startswith(cov_sem) and len(cov_sem) > 0
            same = {i: (c[i] == cov_row[i]) for i in (0, 1, 2, 4, 5, 6, 7)}
            r['A_cols_ok'] = all(same.values())
            r['A_cols_bad'] = [i for i, v in same.items() if not v]
            r['A_cov_has4'] = '④' in cov_sem.decode('utf-8', 'replace')
            if r['A_cov_has4']:
                r['notes'].append('盘上 coverage 该行第 4 列已含 ④（可能是并发写者）')
        seg = delta_sem[len(cov_sem):] if delta_sem.startswith(cov_sem) and cov_sem else delta_sem
        seg_txt = seg.decode('utf-8', 'replace')
        r['A_appended'] = seg_txt
        r['A_cov_sem_len'] = len(cov_sem)

        # 并发写者检测：与执行器 scan 时的快照逐列比对
        sn = snap.get(entry)
        if sn and sn.get('cov_cols') and cov_row is not None:
            cur = [x.decode('utf-8', 'replace') for x in cov_row]
            r['A_snap_cols_same'] = (cur == sn['cov_cols'])
            r['A_snap_pre_sem_same'] = (cur[3] == sn.get('pre_sem'))
            if not r['A_snap_cols_same']:
                diffcols = [i for i in range(8) if cur[i] != sn['cov_cols'][i]]
                r['notes'].append('并发写者改过本行第 %s 列（执行器 scan 时值不同）' % diffcols)
        else:
            r['A_snap_cols_same'] = None
            r['A_snap_pre_sem_same'] = None

        # -------- 形态
        r['form'] = 'direct_call' if 'direct call' in seg_txt else 'slot_witness'
        frow = fmap.get(entry)
        flds = {}
        if frow and len(frow) > 5:
            for kv in frow[5].decode('utf-8', 'replace').split(','):
                if '=' in kv:
                    k, v = kv.split('=', 1)
                    flds[k.strip()] = v.strip()
        r['field_host_raw'] = flds.get('host')

        if r['form'] == 'slot_witness':
            p = parse_slot_text(seg_txt)
            r['text'] = p
            if p is None:
                r['notes'].append('④ 槽位骨架解析失败')
                r['B'] = {}
                r['B_all'] = False
                r['C'] = {}
            else:
                vt, slot = p['vt'], p['slot']
                col = img.u32(vt - 4)
                off = img.u32(col + 4) if img.ok(col) else None
                td = img.u32(col + 12) if img.ok(col) else None
                mangled = img.cstr(td + 8, 256) if td and img.ok(td) else None
                c1 = img.u32(vt + slot * 4) == e
                c2 = (col == p['col']) and (img.u32(vt - 4) == col)
                c3 = (off == p['offset'])
                c4 = (td == p['td']) and (img.u32(col + 12) == td)
                c5 = (mangled == p['mangled'])
                sites_all = ts.installs_of(vt)
                body_e = (e, e + atlas[entry]) if entry in atlas else None
                inside = [(s, dsp) for s, dsp in sites_all
                          if body_e and body_e[0] <= s < body_e[1]]
                outside = [(s, dsp) for s, dsp in sites_all
                           if not (body_e and body_e[0] <= s < body_e[1])]
                sm = p['install']
                ins = decode_at(img, sm) if sm else None
                imm_ok = bool(ins and ins.mnemonic == 'mov' and len(ins.operands) == 2
                              and ins.operands[0].type == X.X86_OP_MEM
                              and ins.operands[1].type == X.X86_OP_IMM
                              and (ins.operands[1].imm & 0xFFFFFFFF) == vt)
                in_scan = any(s == sm for s, _ in sites_all)
                out_ok = any(s == sm for s, _ in outside)
                c6 = bool(imm_ok and in_scan and out_ok)
                r['B'] = dict(vt='%08X' % vt, slot=slot,
                              col='%08X' % col if col else None, off=off,
                              td='%08X' % td if td else None, mangled=mangled,
                              install='%08X' % sm if sm else None,
                              install_ins=(ins.mnemonic + ' ' + ins.op_str) if ins else None,
                              n_sites=len(sites_all), n_inside=len(inside),
                              n_outside=len(outside),
                              c1=c1, c2=c2, c3=c3, c4=c4, c5=c5, c6=c6)
                r['B_all'] = all([c1, c2, c3, c4, c5, c6])

                # -------- §C 宿主定界
                h = p['host']
                src = ''
                fh = flds.get('host', '')
                m = re.match(r'^([0-9A-Fa-f]{8})\((.*)\)$', fh)
                if m:
                    src = m.group(2)
                C = dict(claimed_txt='%08X' % h if h else None,
                         claimed_field=m.group(1).upper() if m else (fh or None),
                         src_declared=src,
                         in_atlas=('%08X' % h) in atlas if h else None,
                         is_entry=(h == e),
                         match_txt=(h == p['host']),
                         match_field=bool(m and int(m.group(1), 16) == h),
                         site_in_text=(img.sec_of(sm) == '.text') if sm else False,
                         site_before_entry=(sm is not None and sm < e),
                         host_body_ok=None)
                if h and ('%08X' % h) in atlas:
                    C['host_body_ok'] = (body_of(ranges, sm) == h)
                runs = padding_runs(img, sm) if sm else []
                near = max(runs, key=lambda x: x['end']) if runs else None
                if near:
                    C['pad_start'] = '%08X' % near['start']
                    C['pad_end'] = '%08X' % near['end']
                    C['pad_len'] = near['length']
                    C['pad_byte'] = '%02X' % near['byte']
                    C['pad_prev'] = ('%02X' % near['prev']) if near['prev'] is not None else None
                    C['pad_ends_at_host'] = (near['end'] == h)
                    C['pad_prev_is_term'] = near['prev'] in (0xC3, 0xC2, 0xE9, 0xEB)
                    C['pad_none_inside'] = not any(h <= x['start'] < sm for x in runs)
                if h:
                    ins2, dok = disasm_clean(img, h, sm + 16)
                    addrs = [i.address for i in ins2]
                    C['disasm_clean'] = dok
                    C['disasm_hits_site'] = sm in addrs
                    C['n_insn_to_site'] = len([a for a in addrs if a <= sm])
                    C['in_init_table'] = h in itab['members']
                    C['init_idx'] = (sorted(itab['members']).index(h)
                                     if h in itab['members'] else None)
                    C['shape'] = fn_shape(img, h)
                    # 严格性自曝：从 host-1, host-2 ... 起反汇编是否也能「落到站点」。
                    # 有 nop 填充时时，答案恒为能 —— 说明「线性反汇编命中站点」这条判据
                    # 对边界只有 ±run 长度的分辨力，真正定界靠「填充run结束于宿主 + run
                    # 前一字节是终止指令 + 该地址被装进初始化表」。
                    tol = 0
                    for k in range(1, (C.get('pad_len') or 0) + 1):
                        _i, _ok = disasm_clean(img, h - k, sm + 16)
                        if _ok and sm in [x.address for x in _i]:
                            tol = k
                        else:
                            break
                    C['disasm_tolerance'] = tol
                r['C'] = C
        else:
            p = parse_direct_text(seg_txt)
            r['text'] = p
            sm = p['site']
            raw = img.raw(sm, 5) if sm else b''
            ins = decode_at(img, sm) if sm else None
            rel32 = int.from_bytes(raw[1:5], 'little', signed=True) if len(raw) == 5 else None
            d1 = (len(raw) == 5 and raw[0] == 0xE8)
            d2 = (rel32 is not None and sm + 5 + rel32 == e)
            d3 = bool(ins and ins.mnemonic == 'call' and ins.operands
                      and ins.operands[0].type == X.X86_OP_IMM
                      and (ins.operands[0].imm & 0xFFFFFFFF) == e)
            site_body = body_of(ranges, sm) if sm else None
            body_e = (e, e + atlas[entry]) if entry in atlas else None
            inside_entry = bool(body_e and body_e[0] <= sm < body_e[1])
            d4 = (not inside_entry) and site_body is not None and site_body != e
            r['B'] = dict(site='%08X' % sm if sm else None, raw=raw.hex().upper(),
                          rel32=rel32,
                          capstone=(ins.mnemonic + ' ' + ins.op_str) if ins else None,
                          site_body='%08X' % site_body if site_body else None,
                          d1=d1, d2=d2, d3=d3, d4=d4,
                          text_bytes=p['bytes_txt'],
                          text_rel=('%08X' % p['rel_target']) if p['rel_target'] else None,
                          text_entry=('%08X' % p['entry_txt']) if p['entry_txt'] else None,
                          text_host=('%08X' % p['host']) if p['host'] else None)
            r['B_all'] = all([d1, d2, d3, d4])
            r['C'] = dict(skipped='direct_call：无填充定界项')
            if p['bytes_txt'] and p['bytes_txt'] != raw.hex().upper():
                r['notes'].append('④ 字节 %s != 实测 %s' % (p['bytes_txt'], raw.hex().upper()))
            if p['rel_target'] and p['rel_target'] != e:
                r['notes'].append('④ site+5+rel32=%08X != entry' % p['rel_target'])
            if p['entry_txt'] and p['entry_txt'] != e:
                r['notes'].append('④ entry=%08X != 行 entry' % p['entry_txt'])
            if p['host'] and site_body and p['host'] != site_body:
                r['notes'].append('④ 宿主 %08X != 实测 %08X' % (p['host'], site_body))

        # -------- §D 文本纪律
        T = r['text'] or {}
        if r['form'] == 'slot_witness':
            five = dict(vt=bool(T.get('vt')), slot=T.get('slot') is not None,
                        col=bool(T.get('col')), rtti=bool(T.get('td')) and bool(T.get('mangled')),
                        install=bool(T.get('install')) and bool(T.get('host')))
            r['D_five'] = all(five.values())
            r['D_five_detail'] = ' '.join('%s=%s' % (k, 'Y' if v else 'N')
                                          for k, v in five.items())
            ok_a = []
            if T.get('vt'):
                ok_a.append(T['vt'] == int(r['B']['vt'], 16))
            if T.get('slot') is not None:
                ok_a.append(T['slot'] == r['B']['slot'])
                ok_a.append(T['slot_val'] == e)
            if T.get('col'):
                ok_a.append(T['col'] == int(r['B']['col'], 16) if r['B']['col'] else False)
            ok_a.append(T['offset'] == r['B']['off'])
            if T.get('td'):
                ok_a.append(T['td'] == int(r['B']['td'], 16) if r['B']['td'] else False)
            if T.get('mangled') and r['B']['mangled']:
                ok_a.append(T['mangled'] == r['B']['mangled'])
            if T.get('install'):
                ok_a.append(T['install'] == int(r['B']['install'], 16) if r['B']['install'] else False)
            ok_a.append(bool((r.get('C') or {}).get('match_txt')))
            r['D_addrs_match'] = all(ok_a)
            # 兜底：④ 里所有 8-hex token 必须能由实测解释
            allowed = {e, int(r['B']['vt'], 16)}
            if r['B']['col']:
                allowed.add(int(r['B']['col'], 16))
            if r['B']['td']:
                allowed.add(int(r['B']['td'], 16))
            if r['B']['install']:
                allowed.add(int(r['B']['install'], 16))
            if T.get('host'):
                allowed.add(T['host'])
            toks = [int(t, 16) for t in RE_HEX8.findall(seg_txt)]
            unexplained = [t for t in toks if t not in allowed]
            r['D_unexplained'] = sorted({'%08X' % t for t in unexplained})
            r['D_no_slot_phrase'] = None
        else:
            r['D_five'] = None
            r['D_five_detail'] = 'direct_call：不适用'
            r['D_no_slot_phrase'] = ('活表槽位见证' not in seg_txt)
            r['D_addrs_match'] = bool(T.get('site') and T.get('entry_txt') and r['B_all'])
            allowed = {e}
            if T.get('site'):
                allowed.add(T['site'])
            if T.get('host'):
                allowed.add(T['host'])
            unexplained = [int(t, 16) for t in RE_HEX8.findall(seg_txt)]
            r['D_unexplained'] = sorted({'%08X' % t for t in unexplained if t not in allowed})
        r['D_ptr_12_6'] = ('§12.6' in seg_txt)
        r['D_no_12_4'] = ('§12.4' not in seg_txt)
        r['D_ok'] = bool((r['D_five'] is not False) and r['D_addrs_match']
                         and not r['D_unexplained']
                         and r['D_ptr_12_6'] and r['D_no_12_4']
                         and (r['D_no_slot_phrase'] is not False))

        # -------- §E same_source 独立性
        if r['form'] == 'slot_witness':
            isec = img.sec_of(int(r['B']['install'], 16)) if r['B']['install'] else None
            csec = img.sec_of(int(r['B']['col'], 16)) if r['B']['col'] else None
            tsec = img.sec_of(int(r['B']['td'], 16)) if r['B']['td'] else None
            r['E'] = dict(r4_section=isec, r2_col_section=csec, r2_td_section=tsec,
                          distinct_sections=(isec != csec),
                          ok=(isec == '.text' and csec in ('.rdata', '.data')))
            r['E_note'] = ('④=.text 装表指令；②=.rdata COL→TD→装饰名链；槽位占用部分按 D-47(A) '
                           '让位口径引用，不计入 ④ 链')
        else:
            sb = img.sec_of(int(r['B']['site'], 16)) if r['B']['site'] else None
            r['E'] = dict(r4_section=sb, r2_section='语义栏(ctor canonical vptr)',
                          distinct_sections=True, ok=(sb == '.text'))
            r['E_note'] = '④=.text E8 调用站点；②=构造器 canonical vptr 装表'
        recs.append(r)

    # -------- 装表点/站点是否跨行共用（§8.6 条 1「site 不共用」）
    inst_sites = [r['B'].get('install') or r['B'].get('site') for r in recs]
    share = {}
    for s in inst_sites:
        share[s] = share.get(s, 0) + 1
    for r in recs:
        s = r['B'].get('install') or r['B'].get('site')
        r['E']['site_exclusive'] = (share.get(s) == 1)

    # -------- §F 反抄袭
    segs = [r['A_appended'] for r in recs]
    norm = [RE_HEX8.sub('ENTRY', s) for s in segs]
    for i, r in enumerate(recs):
        r['F_unique_full'] = segs.count(segs[i]) == 1
        r['F_unique_norm'] = norm.count(norm[i]) == 1
    F = dict(n=len(segs), unique_full=len(set(segs)), unique_norm=len(set(norm)),
             dup_full=[s[:60] for s in segs if segs.count(s) > 1],
             dup_norm=[s[:60] for s in norm if norm.count(s) > 1])

    # -------- 判定
    pad_rows = [r for r in recs if r['form'] == 'slot_witness'
                and (r.get('C') or {}).get('src_declared') == 'disasm-padding']
    for r in recs:
        ok = bool(r.get('A_prefix_ok') and r.get('A_cols_ok') and r.get('B_all'))
        C = r.get('C') or {}
        if r['form'] == 'slot_witness':
            if C.get('src_declared') == 'disasm-padding':
                ok = ok and all([C.get('site_in_text'), C.get('pad_ends_at_host'),
                                 C.get('pad_prev_is_term'), C.get('pad_none_inside'),
                                 C.get('disasm_clean'), C.get('disasm_hits_site'),
                                 not C.get('is_entry'), C.get('match_txt'),
                                 C.get('match_field')])
            else:
                ok = ok and all([C.get('in_atlas'), C.get('host_body_ok'),
                                 C.get('match_txt'), C.get('match_field'),
                                 not C.get('is_entry')])
        ok = ok and r.get('D_ok') and (r.get('E') or {}).get('ok') \
            and (r.get('E') or {}).get('site_exclusive') \
            and r.get('F_unique_full') and r.get('F_unique_norm')
        r['verdict'] = 'PASS' if ok else 'FAIL'

    # -------- check14.tsv
    cols = ['entry', 'form', 'verdict',
            'A_prefix_ok', 'A_cols_ok', 'A_cov_col4_has_ring4',
            'A_snap_cols_same', 'A_snap_pre_sem_same',
            'B_all', 'B_detail',
            'C_host_src', 'C_host_in_atlas', 'C_pad_run', 'C_pad_prev_term',
            'C_pad_ends_at_host', 'C_pad_none_inside', 'C_disasm_clean_hits_site',
            'C_host_eq_entry', 'C_host_match_text', 'C_host_match_fields',
            'C_host_body_ok', 'C_in_init_table', 'C_init_idx', 'C_fn_ret', 'C_fn_global_writes',
            'C_disasm_tolerance',
            'D_five', 'D_addrs_match', 'D_unexplained', 'D_ptr_12_6', 'D_no_12_4', 'D_ok',
            'E_r4_sec', 'E_r2_sec', 'E_distinct', 'E_site_exclusive', 'E_ok',
            'F_unique_full', 'F_unique_norm', 'notes']
    with open(OUT_TSV, 'w', encoding='utf-8', newline='') as f:
        f.write('\t'.join(cols) + '\n')
        for r in recs:
            B, C, E = r['B'], (r.get('C') or {}), (r.get('E') or {})
            if r['form'] == 'slot_witness':
                bd = 'c1..c6=%s; sites=%d in=%d out=%d; ins=%s' % (
                    ''.join('T' if B.get(k) else 'F' for k in ('c1', 'c2', 'c3', 'c4', 'c5', 'c6')),
                    B.get('n_sites', -1), B.get('n_inside', -1), B.get('n_outside', -1),
                    B.get('install_ins'))
            else:
                bd = 'd1..d4=%s; bytes=%s; rel32=%s; target=%s; site_body=%s' % (
                    ''.join('T' if B.get(k) else 'F' for k in ('d1', 'd2', 'd3', 'd4')),
                    B.get('raw'), B.get('rel32'), B.get('capstone'), B.get('site_body'))
            pad = ('%s..%s len=%d byte=%s' % (C.get('pad_start'), C.get('pad_end'),
                                              C.get('pad_len'), C.get('pad_byte'))
                   if C.get('pad_start') else '-')
            shp = C.get('shape') or {}
            row = [r['entry'], r['form'], r['verdict'],
                   str(r.get('A_prefix_ok')), str(r.get('A_cols_ok')),
                   str(r.get('A_cov_has4')),
                   str(r.get('A_snap_cols_same')), str(r.get('A_snap_pre_sem_same')),
                   str(r.get('B_all')), bd,
                   str(C.get('src_declared')), str(C.get('in_atlas')), pad,
                   str(C.get('pad_prev')), str(C.get('pad_ends_at_host')),
                   str(C.get('pad_none_inside')),
                   '%s/%s' % (C.get('disasm_clean'), C.get('disasm_hits_site')),
                   str(C.get('is_entry')), str(C.get('match_txt')),
                   str(C.get('match_field')), str(C.get('host_body_ok')),
                   str(C.get('in_init_table')), str(C.get('init_idx')),
                   str(shp.get('has_ret')), str(shp.get('n_global_write')),
                   str(C.get('disasm_tolerance')),
                   str(r.get('D_five')), str(r.get('D_addrs_match')),
                   ','.join(r.get('D_unexplained') or []) or '-',
                   str(r.get('D_ptr_12_6')), str(r.get('D_no_12_4')), str(r.get('D_ok')),
                   str(E.get('r4_section')), str(E.get('r2_col_section') or E.get('r2_section')),
                   str(E.get('distinct_sections')), str(E.get('site_exclusive')),
                   str(E.get('ok')),
                   str(r.get('F_unique_full')), str(r.get('F_unique_norm')),
                   ' | '.join(r['notes'])]
            f.write('\t'.join(row) + '\n')

    summary = dict(
        exe_sha=exe_sha, cov_sha=cov_sha, cov_bytes=cov_len,
        cov_sha_at_executor_scan=snap_meta.get('cov_sha_before'),
        cov_bytes_at_executor_scan=snap_meta.get('cov_bytes'),
        cov_drifted=(snap_meta.get('cov_sha_before') not in (None, cov_sha)),
        rows14_snapshot_same=all(r.get('A_snap_cols_same') in (True, None) for r in recs),
        text_insns=ts.n_insn, text_skip=ts.n_skip, atlas_n=len(atlas),
        init_tables=[dict(lo='%08X' % a, hi='%08X' % b, n=c) for a, b, c in itab['runs']],
        n=len(recs),
        pass_n=sum(1 for r in recs if r['verdict'] == 'PASS'),
        fail_n=sum(1 for r in recs if r['verdict'] == 'FAIL'),
        padding_row_entries=[r['entry'] for r in pad_rows],
        padding_ok=sum(1 for r in pad_rows
                       if r['C'].get('pad_ends_at_host') and r['C'].get('pad_prev_is_term')
                       and r['C'].get('pad_none_inside') and r['C'].get('disasm_hits_site')
                       and r['C'].get('site_in_text') and not r['C'].get('is_entry')
                       and r['C'].get('match_txt') and r['C'].get('match_field')),
        direct_entries=[r['entry'] for r in recs if r['form'] == 'direct_call'],
        direct_ok=sum(1 for r in recs if r['form'] == 'direct_call' and r['B_all']),
        same_source_yes=0,
        ptr12_6=sum(1 for r in recs if r.get('D_ptr_12_6')),
        F=F,
        rows=[{k: v for k, v in r.items() if k != 'A_appended'} for r in recs],
    )
    with open(OUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=1, default=str)

    print('\n=== 逐行 ===')
    for r in recs:
        print('%s %-13s %-4s %s' % (r['entry'], r['form'], r['verdict'],
                                    '; '.join(r['notes'])[:80]))
    print('\nPASS %d / FAIL %d' % (summary['pass_n'], summary['fail_n']))
    print('§C 填充行 %d 行，成立 %d 行: %s' % (len(pad_rows), summary['padding_ok'],
                                          ' '.join(summary['padding_row_entries'])))
    print('§C 中 in_init_table: %d/%d' % (
        sum(1 for r in pad_rows if r['C'].get('in_init_table')), len(pad_rows)))
    print('§B direct_call 成立 %d/%d' % (summary['direct_ok'], len(summary['direct_entries'])))
    print('§F 唯一: full %d/%d norm %d/%d' % (F['unique_full'], F['n'],
                                              F['unique_norm'], F['n']))
    print('§D §12.6 指针 %d/%d' % (summary['ptr12_6'], len(recs)))
    print('并发核对: 执行器 scan 时 cov %s / %s B ; 本次 %s / %d B ; drifted=%s ; 14 行快照一致=%s'
          % (str(snap_meta.get('cov_sha_before'))[:16], snap_meta.get('cov_bytes'),
             cov_sha[:16], cov_len, summary['cov_drifted'],
             summary['rows14_snapshot_same']))
    print('wrote', OUT_TSV)
    return 0


if __name__ == '__main__':
    sys.exit(main())
