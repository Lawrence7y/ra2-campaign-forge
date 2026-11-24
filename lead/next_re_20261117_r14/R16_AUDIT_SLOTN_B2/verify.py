#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
R16-AUDIT-SLOTN-B2 —— 审计员独立复核脚本（自写；不复用执行器 scan_fields.py / gen_delta.py，
也不把执行器的 verify_summary.json / scan_raw.json 当判据）

只读打开：
  ../COVERAGE/coverage.tsv
  ../R16_SLOTN_B2/delta.tsv
  ../../../ra2youli/gamemd.exe        (4,825,360 B, SHA-256 73201CC0...7476)
  ../R14_COMMON.md                    (只用来核对披露指针落点)
  ../R16_SLOTN_B1/delta.tsv           (只用来做 §E 同类先例对照)

判据：任务卡 R16-AUDIT-SLOTN-B2 §3 A–F；背景裁决 D-47(A) 已裁 ⇒「②④ 共槽」不作为 FAIL 理由。

输出：bytecheck.tsv（15 行 × 6 项，格式 `判定:实测值`）+ 控制台/日志摘要
用法：python verify.py
"""

import os
import re
import struct
import sys
import hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
COV = os.path.join(R14, 'COVERAGE', 'coverage.tsv')
DELTA = os.path.join(R14, 'R16_SLOTN_B2', 'delta.tsv')
GAMEMD = os.path.abspath(os.path.join(R14, '..', '..', 'ra2youli', 'gamemd.exe'))
COMMON = os.path.join(R14, 'R14_COMMON.md')
B1DELTA = os.path.join(R14, 'R16_SLOTN_B1', 'delta.tsv')

IMAGE_BASE = 0x400000
EXPECT_SHA256 = '73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476'
TEXT_LO, TEXT_HI = 0x401000, 0x7E038D
PRECEDENT = ['00464AC0', '004DE630', '004F42F0']

ROW30_ENTRY = '005B2FD0'
ROW30_SCAN_SITE = '0043B71F'      # work_scan.json A_agg.site_of[005B2FD0]（执行器弃用值）
ROW30_USED_VT = '007EB058'        # 执行器改取的 InfantryClass 表
ROW30_USED_SITE = '00517D9D'      # 执行器改取的装表点
ROW30_USED_FUNC = '00517D90'


# --------------------------------------------------------------------- PE 读取（只读）
class Image(object):
    def __init__(self, path):
        with open(path, 'rb') as f:
            self.data = f.read()
        d = self.data
        if d[:2] != b'MZ':
            raise SystemExit('not MZ')
        e_lfanew = struct.unpack_from('<I', d, 0x3C)[0]
        if d[e_lfanew:e_lfanew + 4] != b'PE\0\0':
            raise SystemExit('not PE')
        coff = e_lfanew + 4
        nsec = struct.unpack_from('<H', d, coff + 2)[0]
        opt_size = struct.unpack_from('<H', d, coff + 16)[0]
        opt = coff + 20
        if struct.unpack_from('<H', d, opt)[0] != 0x10b:
            raise SystemExit('not PE32')
        self.image_base = struct.unpack_from('<I', d, opt + 28)[0]
        self.sections = []
        sec = opt + opt_size
        for i in range(nsec):
            off = sec + i * 40
            name = d[off:off + 8].rstrip(b'\0').decode('latin-1')
            vsize = struct.unpack_from('<I', d, off + 8)[0]
            vaddr = struct.unpack_from('<I', d, off + 12)[0]
            rawsize = struct.unpack_from('<I', d, off + 16)[0]
            rawptr = struct.unpack_from('<I', d, off + 20)[0]
            self.sections.append(dict(name=name, va=self.image_base + vaddr, vsize=vsize,
                                      rawsize=rawsize, rawptr=rawptr))

    def sect_of(self, va):
        for s in self.sections:
            span = max(s['vsize'], s['rawsize'])
            if s['va'] <= va < s['va'] + span:
                return s
        return None

    def off(self, va):
        s = self.sect_of(va)
        if s is None:
            raise KeyError('VA %08X unmapped' % va)
        d = va - s['va']
        if d >= s['rawsize']:
            raise KeyError('VA %08X beyond raw of %s' % (va, s['name']))
        return s['rawptr'] + d

    def mapped(self, va):
        try:
            o = self.off(va)
        except KeyError:
            return False
        return 0 <= o < len(self.data)

    def u32(self, va):
        return struct.unpack_from('<I', self.data, self.off(va))[0]

    def cstr(self, va, limit=400):
        o = self.off(va)
        end = self.data.find(b'\0', o, o + limit)
        if end < 0:
            end = o + limit
        return self.data[o:end].decode('latin-1')

    def raw(self, va, n):
        o = self.off(va)
        return self.data[o:o + n]


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest().upper()


# --------------------------------------------------------------------- 读表
def read_lines(path):
    raw = open(path, 'rb').read()
    txt = raw.decode('utf-8')
    L = txt.split('\n')
    if L and L[-1] == '':
        L.pop()
    return L, raw


def build_coverage(L):
    m, ln = {}, {}
    for i, l in enumerate(L):
        if i == 0 or not l:
            continue
        f = l.split('\t')
        if len(f) != 8:
            continue
        m.setdefault(f[0], f)
        ln.setdefault(f[0], i + 1)
    return m, ln


# --------------------------------------------------------------------- ④ 文本解析
RE_VT = re.compile(r'vt=([0-9A-F]{8})')
RE_SLOTVAL = re.compile(r'槽 (\d+) 值=([0-9A-F]{8})')
RE_COL = re.compile(r'COL=([0-9A-F]{8}) offset=(\d+)')
RE_RTTI = re.compile(r'RTTI=([0-9A-F]{8})→([^；）]*)')
RE_SITE = re.compile(r'装表点 ([0-9A-F]{8}) 位于 ([0-9A-F]{8}) 体内')
RE_UPGRADE = re.compile(r'④升级句：([^（]+)（④ 表属类与行名类一致，均为 ([^；）]+)；'
                        r'该槽即其 vt=([0-9A-F]{8}) 表 slot(\d+)，无归属歧义）')
RE_D47 = re.compile(r'（D-47\(A\) 裁决：[^）]*）')
RE_SEC = re.compile(r'§\s*12\s*\.\s*(\d+)')


def parse4(seg):
    o = {}
    m = RE_VT.search(seg);      o['vt'] = m.group(1) if m else None
    m = RE_SLOTVAL.search(seg); o['slotval_n'] = int(m.group(1)) if m else None
    o['slotval'] = m.group(2) if m else None
    m = RE_COL.search(seg);     o['col'] = m.group(1) if m else None
    o['offset'] = int(m.group(2)) if m else None
    m = RE_RTTI.search(seg);    o['td'] = m.group(1) if m else None
    o['mangled'] = m.group(2).strip() if m else None
    m = RE_SITE.search(seg);    o['site'] = m.group(1) if m else None
    o['func'] = m.group(2) if m else None
    m = RE_UPGRADE.search(seg)
    o['up_name'] = m.group(1).strip() if m else None
    o['up_class'] = m.group(2).strip() if m else None
    o['up_vt'] = m.group(3) if m else None
    o['up_slot'] = int(m.group(4)) if m else None
    m = RE_D47.search(seg)
    o['d47'] = m.group(0) if m else None
    o['secs'] = RE_SEC.findall(seg)
    return o


def name_slot(name):
    m = re.search(r'::slot(\d+)$', name)
    return int(m.group(1)) if m else None


def name_class(name):
    """类名 = '::' 之前的第一段。
    注意先例行的 name 可能是 `BuildingTypeClass::CanPlaceHere`（非 ::slotN），
    所以不能用 '::slot' 作切点。"""
    return name.split('::')[0]


# --------------------------------------------------------------------- RTTI
def rtti_class_of_table(img, vt):
    """vt-4 -> COL; COL+12 -> TD; TD+8 -> 内联装饰名（不是解引用指针）"""
    col = img.u32(vt - 4)
    td = img.u32(col + 12)
    man = img.cstr(td + 8)
    return col, td, man


def looks_like_rtti(img, vt):
    try:
        col, td, man = rtti_class_of_table(img, vt)
    except Exception:
        return False
    return man.startswith('.?A') and len(man) > 4


def demangle_class(mangled):
    s = mangled
    if s.startswith('.?AV'):
        s = s[4:]
    if s.endswith('@@'):
        s = s[:-2]
    return s


def col_name_match_row_class(row_class, mangled):
    """与 PROBE_802/probe.py:col_name_match 同口径的独立重写：
    非模板 = 类名须为装饰名子串；T_ 模板伪名 = 去 T_、去尾 _ 、按 _ 切分各段均须出现在装饰名中"""
    m = mangled
    if row_class.startswith('T_'):
        core = row_class[2:]
        if core.endswith('_'):
            core = core[:-1]
        parts = [p for p in core.split('_') if p]
        return all(p in m for p in parts)
    return row_class in m


# --------------------------------------------------------------------- capstone
def make_cs():
    import capstone
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = True
    return md


def decode_one(md, img, va, maxlen=15):
    try:
        code = img.raw(va, maxlen)
    except KeyError:
        return None
    for insn in md.disasm(code, va):
        return insn
    return None


def is_mov_mem_imm(insn, want_imm, CM):
    if insn is None:
        return False, 'decode 失败'
    if insn.mnemonic != 'mov':
        return False, '非 mov'
    ops = insn.operands
    if len(ops) != 2:
        return False, '操作数非 2'
    if ops[0].type != CM.X86_OP_MEM:
        return False, 'op0 非 mem'
    if ops[1].type != CM.X86_OP_IMM:
        return False, 'op1 非 imm'
    got = ops[1].imm & 0xFFFFFFFF
    if got != want_imm:
        return False, 'imm=%08X != vt=%08X' % (got, want_imm)
    return True, ''


def body_range(md, img, start, cap=8000):
    """从 start 线性解码，遇 ret / 无条件 jmp 即止；返回 [start, end)"""
    n = 0
    while n < cap:
        insn = decode_one(md, img, start + n)
        if insn is None:
            return start, start + n
        # 必须逐条无缝衔接
        if insn.address != start + n:
            return start, start + n
        n += insn.size
        if insn.mnemonic.startswith('ret'):
            return start, start + n
        if insn.mnemonic == 'jmp':
            return start, start + n
    return start, start + n


# --------------------------------------------------------------------- 独立枚举：活表表头
def is_text_ptr(v):
    return TEXT_LO <= v < TEXT_HI


def table_start_of(img, A, maxslot=400):
    """从承载 entry 的槽地址 A 向上回溯到**表头**：
    只要前一个 dword 是 .text 代码指针（或 0 空槽）就继续退；退不动时
    要求 vt-4 恰为合法的 RTTI COL。这样可排除 "表内任意偏移 + 假 COL" 的过生成。"""
    p = A
    steps = 0
    while steps < maxslot:
        prev = p - 4
        if not img.mapped(prev):
            break
        v = img.u32(prev)
        if is_text_ptr(v) or v == 0:
            p = prev
            steps += 1
        else:
            break
    if not img.mapped(p - 4):
        return None
    try:
        col, td, man = rtti_class_of_table(img, p)
    except Exception:
        return None
    if not man.startswith('.?A'):
        return None
    return dict(vt=p, slot=(A - p) // 4, col=col, td=td, mangled=man)


def entry_hits(img, entry):
    """.data/.rdata 里 4 字节 == entry 的所有位置（VA）"""
    out = []
    for s in img.sections:
        if s['name'] not in ('.data', '.rdata') or s['rawsize'] == 0:
            continue
        n = min(s['rawsize'], s['vsize'] or s['rawsize'])
        for i in range(0, n // 4 * 4, 4):
            if struct.unpack_from('<I', img.data, s['rawptr'] + i)[0] == entry:
                out.append(s['va'] + i)
    return out


def tables_containing(img, entry):
    """独立枚举：含该 entry 的所有活表（表头 vt + 槽号 + RTTI 类）。完全不看文本。"""
    out = []
    for A in entry_hits(img, entry):
        t = table_start_of(img, A)
        if t:
            t['hit'] = A
            out.append(t)
    return out


def slot_of_entry(img, vt, entry, maxslot=400):
    for n in range(maxslot):
        if not img.mapped(vt + 4 * n):
            return None
        if img.u32(vt + 4 * n) == entry:
            return n
    return None


def find_install_sites(img, md, CM, want):
    """在 .text 里按**立即数字节模式**定位 `mov <mem>, imm32`（imm==want）。
    不用全 .text 线性反汇编（4MB 会失步），改用：找到 imm 的 4 字节 LE 位置 X，
    在 X-2..X-7 起逐点试解码，要求单条指令恰好在 X+4 结束且形态为 mov mem,imm32。"""
    pat = struct.pack('<I', want)
    s = img.sect_of(TEXT_LO)
    blob = img.data[s['rawptr']: s['rawptr'] + (TEXT_HI - TEXT_LO)]
    out = []
    pos = blob.find(pat)
    while pos >= 0:
        X = TEXT_LO + pos
        for k in range(2, 8):
            st = X - k
            if st < TEXT_LO:
                continue
            try:
                code = img.raw(st, k + 4)
            except KeyError:
                continue
            got = list(md.disasm(code, st))
            if not got:
                continue
            ins = got[0]
            if ins.address + ins.size != X + 4:
                continue
            ops = ins.operands
            if (ins.mnemonic == 'mov' and len(ops) == 2
                    and ops[0].type == CM.X86_OP_MEM and ops[1].type == CM.X86_OP_IMM):
                out.append((st, '%s %s' % (ins.mnemonic, ins.op_str)))
                break
        pos = blob.find(pat, pos + 1)
    return out


def writes_to_same_slot(img, md, CM, func, site):
    """宿主函数体内，与该装表点写**同一目标操作数**（同 base+disp / 同绝对地址）的
    其它 mov imm 写入。用于判断装表点是否为该指针的"最终主表"。
    解码窗口严格限定在 func 的定界 body 内（否则会串进后续函数，误报）。
    返回 (target_desc, [(addr, imm, mangled_or_None), ...])"""
    ins = decode_one(md, img, site)
    if ins is None or len(ins.operands) != 2 or ins.operands[0].type != CM.X86_OP_MEM:
        return None, []
    m = ins.operands[0].mem
    base, disp = m.base, m.disp
    bs, be = body_range(md, img, func)
    same = []
    for x in md.disasm(img.raw(bs, be - bs), bs):
        ops = x.operands
        if x.mnemonic != 'mov' or len(ops) != 2:
            continue
        if ops[0].type != CM.X86_OP_MEM or ops[1].type != CM.X86_OP_IMM:
            continue
        mm = ops[0].mem
        if mm.base == base and mm.disp == disp:
            imm = ops[1].imm & 0xFFFFFFFF
            man = None
            if imm > IMAGE_BASE:
                try:
                    col, td, mann = rtti_class_of_table(img, imm)
                    if mann.startswith('.?A'):
                        man = mann
                except Exception:
                    man = None
            same.append((x.address, imm, man))
    return 'base=%d disp=0x%X' % (base, disp & 0xFFFFFFFF), same


# --------------------------------------------------------------------- 归一化（§E）
def norm_drop_d47(seg):
    return RE_D47.sub('', seg).rstrip()


def norm_skeleton(seg, cls):
    t = seg
    if cls:
        t = t.replace(cls, '<CLS>')
    t = re.sub(r'\.\?[A-Za-z0-9_@$?<>]*_+@@*', '<MANT>', t)   # 模板装饰名
    t = re.sub(r'\.\?[A-Za-z0-9_@$?<>]*@@+', '<MAN>', t)      # 普通装饰名
    t = re.sub(r'[0-9A-F]{8}', '<H>', t)
    t = re.sub(r'\d+', '<N>', t)
    return t


# --------------------------------------------------------------------- main
def main():
    img = Image(GAMEMD)
    md = make_cs()
    import capstone
    CM = capstone.x86

    log = []

    def P(s=''):
        log.append(s)
        print(s)

    P('=' * 78)
    P('R16-AUDIT-SLOTN-B2 · 独立复核（审计员自写脚本，判据全来自字节）')
    P('=' * 78)

    gsha = sha256_file(GAMEMD)
    P('gamemd.exe   %d B  sha256=%s  %s' % (len(img.data), gsha,
                                            'MATCH 卡面' if gsha == EXPECT_SHA256 else 'MISMATCH!'))
    if gsha != EXPECT_SHA256:
        raise SystemExit('binary hash mismatch')
    P('ImageBase=%08X' % img.image_base)
    for s in img.sections:
        P('  %-8s VA=[%08X,%08X) raw=%d@%d' % (s['name'], s['va'], s['va'] + s['vsize'],
                                               s['rawsize'], s['rawptr']))
    P('coverage.tsv %d B sha256=%s  mtime=%s' %
      (os.path.getsize(COV), sha256_file(COV),
       __import__('datetime').datetime.fromtimestamp(os.path.getmtime(COV)).strftime('%Y-%m-%d %H:%M:%S')))
    P('delta.tsv    %d B sha256=%s  mtime=%s' %
      (os.path.getsize(DELTA), sha256_file(DELTA),
       __import__('datetime').datetime.fromtimestamp(os.path.getmtime(DELTA)).strftime('%Y-%m-%d %H:%M:%S')))
    P('')

    CL, _ = read_lines(COV)
    cov, covln = build_coverage(CL)
    DL, _ = read_lines(DELTA)
    rows = []
    for i, l in enumerate(DL):
        if i == 0 or not l:
            continue
        f = l.split('\t')
        if len(f) != 8:
            raise SystemExit('delta 第 %d 行列数 %d != 8' % (i + 1, len(f)))
        rows.append(f)
    P('delta 数据行 %d（8 列）；coverage entry 总数 %d' % (len(rows), len(cov)))
    P('')

    # ---------------------------------------------------------------- §0 前置（加做）
    P('-' * 78)
    P('§0 前置核对（卡面未强制，我加做：确认被审对象确实是 slotN43 数据行 16–30）')
    P('-' * 78)
    SLOTN43 = os.path.join(R14, 'PROBE_802', 'slotN43.tsv')
    pre_ok = {}
    if os.path.exists(SLOTN43):
        SL, _ = read_lines(SLOTN43)
        sdata = [l.split('\t') for l in SL[1:] if l.strip()]
        P('  slotN43.tsv：表头 1 + 数据 %d 行' % len(sdata))
        win = sdata[15:30]
        P('  取数据行 16–30 = %d 行' % len(win))
        pair_ok = all(w[0] == r[0] and w[2] == r[2] for w, r in zip(win, rows))
        P('  与 delta 的 (entry, name) 逐行对齐 ? %s' % pair_ok)
        pre_ok['slotn43_pairs'] = pair_ok
        pre_ok['slotn43_rows'] = len(sdata)
    ents = [r[0] for r in rows]
    P('  本批 15 entry 互不重复 ? %s（%d 个不同值）' % (len(set(ents)) == len(ents), len(set(ents))))
    pre_ok['entries_unique'] = (len(set(ents)) == len(ents))
    if os.path.exists(B1DELTA):
        L1, _ = read_lines(B1DELTA)
        b1 = [l.split('\t')[0] for l in L1[1:] if l.strip()]
        inter = set(b1) & set(ents)
        P('  与批次 1 交集 ? %s（%s）' % ('空' if not inter else '非空', sorted(inter) or '-'))
        pre_ok['batch1_intersection_empty'] = not inter
    P('')

    # ---------------------------------------------------------------- §A
    P('-' * 78)
    P('§A 最小改动与原文保全（第 4 列严格前缀 + 其余 6 列逐字节）')
    P('-' * 78)
    a_bad = 0
    a_rows = []
    for idx, f in enumerate(rows, 1):
        e = f[0]
        if e not in cov:
            a_rows.append(dict(idx=idx, entry=e, ok=False, note='coverage 无此 entry'))
            a_bad += 1
            continue
        cf = cov[e]
        cv4 = cf[3].encode('utf-8')
        dl4 = f[3].encode('utf-8')
        pref = dl4.startswith(cv4)
        cols_ok = all(f[k] == cf[k] for k in (0, 1, 2, 4, 5, 6, 7))
        ok = pref and cols_ok
        if not ok:
            a_bad += 1
        add = f[3][len(cf[3]):]
        a_rows.append(dict(idx=idx, entry=e, ok=ok, prefix=pref, cols_ok=cols_ok,
                           cov_lineno=covln[e], orig_len=len(cv4), add_len=len(dl4) - len(cv4),
                           orig_last=cf[3][-1:], add_head=add[:12]))
        P('  #%-2d %-9s cov:L%-5d 原 %3d B 末=%s | 追加 %3d B 起=%s | 前缀=%s 其余列=%s ⇒ %s' %
          (idx, e, covln[e], len(cv4), cf[3][-1:], len(dl4) - len(cv4), add[:1],
           pref, cols_ok, 'PASS' if ok else 'FAIL'))
    P('  ⇒ §A 不合格 %d/15' % a_bad)
    P('')

    # ---------------------------------------------------------------- §B
    P('-' * 78)
    P('§B 6 项字节事实（每项都由本脚本从镜像字节复算）')
    P('-' * 78)
    bc, d_rows = [], []
    for idx, f in enumerate(rows, 1):
        e, name = f[0], f[2]
        slot, cls = name_slot(name), name_class(name)
        seg = f[3]
        i4 = seg.find('④ 活表槽位见证')
        seg4 = seg[i4:] if i4 >= 0 else ''
        o = parse4(seg4)
        vt = int(o['vt'], 16) if o['vt'] else None
        col = int(o['col'], 16) if o['col'] else None
        td = int(o['td'], 16) if o['td'] else None
        site = int(o['site'], 16) if o['site'] else None
        entry = int(e, 16)

        chk, det = {}, {}
        try:
            v = img.u32(vt + slot * 4); det[1] = '%08X' % v; chk[1] = (v == entry)
        except Exception as ex:
            det[1] = 'ERR %s' % ex; chk[1] = False
        try:
            v = img.u32(vt - 4); det[2] = '%08X' % v; chk[2] = (v == col)
        except Exception as ex:
            det[2] = 'ERR %s' % ex; chk[2] = False
        try:
            v = img.u32(col + 4); det[3] = str(v); chk[3] = (v == o['offset'])
        except Exception as ex:
            det[3] = 'ERR %s' % ex; chk[3] = False
        try:
            v = img.u32(col + 12); det[4] = '%08X' % v; chk[4] = (v == td)
        except Exception as ex:
            det[4] = 'ERR %s' % ex; chk[4] = False
        try:
            v = img.cstr(td + 8); det[5] = v; chk[5] = (v == o['mangled'])
        except Exception as ex:
            det[5] = 'ERR %s' % ex; chk[5] = False
        insn = decode_one(md, img, site)
        ok6, why6 = is_mov_mem_imm(insn, vt, CM)
        det[6] = ('%s %s' % (insn.mnemonic, insn.op_str)) if insn else 'decode 失败'
        if not ok6:
            det[6] = det[6] + ' [%s]' % why6
        chk[6] = ok6

        n_ok = sum(1 for k in chk if chk[k])
        # 辅助：体内/体外
        iok = None
        if o['func']:
            fs = int(o['func'], 16)
            bs, be = body_range(md, img, fs)
            det['body'] = '[%08X,%08X)' % (bs, be)
            iok = (bs <= site < be) and not (bs <= entry < be)
            det['inbody'] = iok
        # 辅助：独立枚举含该 entry 的活表
        tabs = tables_containing(img, entry)
        same_slot = [t for t in tabs if t['slot'] == slot]
        det['tables'] = ','.join('%08X/%s' % (t['vt'], demangle_class(t['mangled']))
                                 for t in sorted(same_slot, key=lambda x: -x['vt']))
        det['n_tables'] = len(same_slot)
        cls_consistent = any(t['vt'] == vt for t in same_slot)
        det['chosen_is_class_consistent'] = cls_consistent
        # 辅助：该 vt 的装表点是否唯一 + 宿主函数内是否被二次覆写
        sites = find_install_sites(img, md, CM, vt)
        det['install_sites'] = ', '.join('%08X' % a for a, _t in sites)
        det['n_sites'] = len(sites)
        tgt, same_writes = writes_to_same_slot(img, md, CM, int(o['func'], 16), site)
        other = [w for w in same_writes if w[0] != site]
        det['final_primary'] = (len(same_writes) == 1)
        det['same_slot_writes'] = ';'.join('%08X=%08X' % (a, i) for a, i, _m in same_writes)

        bc.append(dict(idx=idx, entry=e, slot=slot, vt=o['vt'], col=o['col'],
                       offset=o['offset'], td=o['td'], mangled=o['mangled'],
                       site=o['site'], func=o['func'], chk=chk, det=det, n_ok=n_ok))
        d_rows.append(dict(idx=idx, entry=e, cls=cls, slot=slot, o=o, seg4=seg4,
                           vt=o['vt'], name=name, inbody=iok, tables=same_slot,
                           cls_consistent=cls_consistent))

        P('  #%-2d %s %s' % (idx, e, name))
        P('      ① u32(%s + %d*4) = %s  ⇒ %s' % (o['vt'], slot, det[1], 'True' if chk[1] else 'False'))
        P('      ② u32(%s - 4)   = %s  vs 文本 COL=%s  ⇒ %s' % (o['vt'], det[2], o['col'], 'True' if chk[2] else 'False'))
        P('      ③ u32(%s + 4)   = %s  vs 文本 offset=%s  ⇒ %s' % (o['col'], det[3], o['offset'], 'True' if chk[3] else 'False'))
        P('      ④ u32(%s + 12)  = %s  vs 文本 RTTI=%s  ⇒ %s' % (o['col'], det[4], o['td'], 'True' if chk[4] else 'False'))
        P('      ⑤ cstr(%s + 8)  = "%s"  ⇒ %s' % (o['td'], det[5], 'True' if chk[5] else 'False'))
        P('      ⑥ %s : %s  ⇒ %s' % (o['site'], det[6], 'True' if chk[6] else 'False'))
        P('      [辅助] 宿主 body=%s site 在体内/entry 体外=%s' % (det.get('body', '-'), iok))
        P('      [辅助] 独立枚举：含该 entry 且同槽(%d) 的活表 %d 张 = %s；所选 vt 在类一致集合内=%s' %
          (slot, det['n_tables'], det['tables'], cls_consistent))
        P('      [辅助] vt=%s 的装表点共 %d 处：%s；宿主内对该目标的写入=%s（唯一即"最终主表"=%s）' %
          (o['vt'], det['n_sites'], det['install_sites'], det['same_slot_writes'], det['final_primary']))
    b_bad = sum(1 for r in bc if r['n_ok'] != 6)
    P('  ⇒ 6/6 全真的行 %d/15；任一项不符的行 %d' % (15 - b_bad, b_bad))
    for k in range(1, 7):
        bad = [r['idx'] for r in bc if not r['chk'][k]]
        P('     小项 B%d 不符行：%s' % (k, bad if bad else '无'))
    P('')

    # ---------------------------------------------------------------- §C
    P('-' * 78)
    P('§C【本批最高优先级】行 30（%s）的「表改选」四问四答' % ROW30_ENTRY)
    P('-' * 78)
    c = {}
    entry30 = int(ROW30_ENTRY, 16)

    # Q1
    ss = int(ROW30_SCAN_SITE, 16)
    i1 = decode_one(md, img, ss)
    t1 = ('%s %s' % (i1.mnemonic, i1.op_str)) if i1 else 'decode 失败'
    imm1 = None
    if i1 and len(i1.operands) == 2 and i1.operands[1].type == CM.X86_OP_IMM:
        imm1 = i1.operands[1].imm & 0xFFFFFFFF
    P('Q1  %s 处装的是什么表？该表 RTTI 解出什么类？是否确为 BuildingClass？' % ROW30_SCAN_SITE)
    P('    实测指令: %08X  %s' % (ss, t1))
    P('    xxd     : %s' % img.raw(ss, 6).hex(' ').upper())
    if imm1 is not None:
        col1, td1, man1 = rtti_class_of_table(img, imm1)
        P('    imm32   = %08X ⇒ 被装的表头 vt = %08X' % (imm1, imm1))
        P('    RTTI    : vt-4 = %08X (COL) → COL+12 = %08X (TD) → cstr(TD+8) = "%s"' %
          (col1, td1, man1))
        P('    解出类  = %s' % demangle_class(man1))
        c['q1'] = dict(site=ROW30_SCAN_SITE, op=t1, imm='%08X' % imm1,
                       col='%08X' % col1, td='%08X' % td1, mangled=man1,
                       cls=demangle_class(man1), is_building=('BuildingClass' in man1))
        n_b = slot_of_entry(img, imm1, entry30)
        P('    且 %s 确在该表 slot%d（u32(%08X + %d*4) = %08X）' %
          (ROW30_ENTRY, n_b, imm1, n_b, img.u32(imm1 + 4 * n_b)))
        c['q1']['slot_of_entry'] = n_b
        P('    ⇒ 答：0043B71F 装的是 vt=%08X 的表，RTTI 类 = %s，%s' %
          (imm1, demangle_class(man1),
           '**确为 BuildingClass**' if 'BuildingClass' in man1 else '**不是 BuildingClass**'))
    P('')

    # Q2
    used_vt = int(ROW30_USED_VT, 16)
    P('Q2  %s 在 %s 表里是第几槽？在 BuildingClass 表里也在某槽吗？' % (ROW30_ENTRY, ROW30_USED_VT))
    col2, td2, man2 = rtti_class_of_table(img, used_vt)
    n2 = slot_of_entry(img, used_vt, entry30)
    P('    表 vt=%s：u32(vt-4)=%08X (COL) → +12=%08X (TD) → "%s" ⇒ 类 = %s' %
      (ROW30_USED_VT, col2, td2, man2, demangle_class(man2)))
    P('    u32(%08X + %d*4) = %08X  == entry %s  ⇒ %s 表的 **slot%d**' %
      (used_vt, n2, img.u32(used_vt + 4 * n2), ROW30_ENTRY, ROW30_USED_VT, n2))
    tabs30 = tables_containing(img, entry30)
    tabs30s = sorted(tabs30, key=lambda x: -x['vt'])
    P('    独立枚举（不看文本、回溯表头 + 校验 vt-4 为真 COL）：含 %s 的活表共 %d 张，槽位如下' %
      (ROW30_ENTRY, len(tabs30s)))
    for t in tabs30s:
        P('      vt=%08X  slot%-4d  %s' % (t['vt'], t['slot'], t['mangled']))
    n_b_slots = [t['slot'] for t in tabs30s if t['vt'] == (imm1 if imm1 else 0)]
    c['q2'] = dict(vt=ROW30_USED_VT, slot=n2, col='%08X' % col2, td='%08X' % td2,
                   mangled=man2, cls=demangle_class(man2),
                   n_tables=len(tabs30s),
                   tables=[dict(vt='%08X' % t['vt'], slot=t['slot'], mangled=t['mangled'])
                           for t in tabs30s],
                   building_slot=(n_b_slots[0] if n_b_slots else None))
    P('    ⇒ 答：在 %s 表是 slot%d；在 BuildingClass 表(vt=%s)也是 slot%s —— %s' %
      (ROW30_USED_VT, n2, ('%08X' % imm1) if imm1 else '?',
       ('%d' % n_b_slots[0]) if n_b_slots else '（不在）',
       '**两表同槽，多表持有成立**' if n_b_slots else '不在该表'))
    P('       全部命中表的槽号一致 ? %s' % (len(set(t['slot'] for t in tabs30s)) == 1))
    P('')

    # Q3
    us = int(ROW30_USED_SITE, 16)
    fs = int(ROW30_USED_FUNC, 16)
    i3 = decode_one(md, img, us)
    t3 = ('%s %s' % (i3.mnemonic, i3.op_str)) if i3 else 'decode 失败'
    ok3, why3 = is_mov_mem_imm(i3, used_vt, CM)
    P('Q3  %s 处 capstone 是否确为 mov <mem>, imm32 且 imm32 == %s？'
      '是否位于 %s 体内、且 %s 不是 %s 自身？' %
      (ROW30_USED_SITE, ROW30_USED_VT, ROW30_USED_FUNC, ROW30_USED_FUNC, ROW30_ENTRY))
    P('    实测指令: %08X  %s   （xxd: %s）' % (us, t3, img.raw(us, 6).hex(' ').upper()))
    P('    ⇒ mov<mem>,imm32 且 imm32==%s ? %s %s' % (ROW30_USED_VT, ok3, why3))
    bs, be = body_range(md, img, fs)
    P('    %s 函数头字节 %s（合法 prologue）' % (ROW30_USED_FUNC, img.raw(fs, 12).hex(' ').upper()))
    P('    线性定界 body = [%08X, %08X)' % (bs, be))
    P('    site %08X ∈ body ? %s ； entry %08X ∈ body ? %s' %
      (us, bs <= us < be, entry30, bs <= entry30 < be))
    P('    %s != %s ? %s （%08X vs %08X）' %
      (ROW30_USED_FUNC, ROW30_ENTRY, fs != entry30, fs, entry30))
    tgt, sw = writes_to_same_slot(img, md, CM, fs, us)
    P('    宿主内对同一目标(%s)的全部 imm 写入：%s ⇒ 是"最终主表"=%s' %
      (tgt, ';'.join('%08X=%08X' % (a, v) for a, v, _m in sw), len(sw) == 1))
    sites2 = find_install_sites(img, md, CM, used_vt)
    P('    %s 表的装表点全集（立即数模式精确定位）：%s' %
      (ROW30_USED_VT, ', '.join('%08X' % a for a, _t in sites2)))
    P('    其中 0043B71F 的 imm=%s != %s ⇒ 不能当本表装表点（B⑥ 要求 imm32==vt）' %
      (('%08X' % imm1) if imm1 else '?', ROW30_USED_VT))
    c['q3'] = dict(site=ROW30_USED_SITE, op=t3, ok=ok3, why=why3,
                   func=ROW30_USED_FUNC, body='[%08X,%08X)' % (bs, be),
                   site_in_body=bs <= us < be, entry_in_body=bs <= entry30 < be,
                   func_ne_entry=fs != entry30, final_primary=len(sw) == 1,
                   same_slot_writes=[('%08X' % a, '%08X' % v) for a, v, _m in sw],
                   install_sites=['%08X' % a for a, _t in sites2])
    P('')

    # Q4
    r30 = [r for r in d_rows if r['entry'] == ROW30_ENTRY][0]
    ok_q1 = bool(c['q1'].get('is_building'))
    ok_q2 = (c['q2']['slot'] == r30['slot'] and c['q2']['building_slot'] == r30['slot']
             and len(set(t['slot'] for t in tabs30s)) == 1)
    ok_q3 = (c['q3']['ok'] and c['q3']['site_in_body'] and (not c['q3']['entry_in_body'])
             and c['q3']['func_ne_entry'])
    cls_ok = (demangle_class(man2) == r30['cls'])
    verdict_c = ok_q1 and ok_q2 and ok_q3 and cls_ok
    P('Q4  结论：改选%s' % ('**成立**' if verdict_c else '**不成立**'))
    P('    ① 扫描点 0043B71F 装的是 BuildingClass 表 ⇒ %s' % ok_q1)
    P('    ② 007EB058 表 slot%d == 行名 slot%d，且 BuildingClass 表也 slot%d ⇒ %s' %
      (c['q2']['slot'], r30['slot'], c['q2']['building_slot'] or -1, ok_q2))
    P('    ③ 00517D9D 是 mov [esi],imm32(007EB058)，在 00517D90 体内、00517D90≠entry ⇒ %s' % ok_q3)
    P('    ④ 007EB058 的 RTTI 类 %s == 行名类 %s ⇒ %s' %
      (demangle_class(man2), r30['cls'], cls_ok))
    c['q4'] = dict(holds=verdict_c, q1=ok_q1, q2=ok_q2, q3=ok_q3, cls=cls_ok)
    P('')

    # ---------------------------------------------------------------- §D
    P('-' * 78)
    P('§D 文本与事实一致（地址逐字段 / <Class> / D-47 披露指针是否指 §12.6）')
    P('-' * 78)
    d_bad = 0
    d_detail = []
    for r in d_rows:
        o, idx = r['o'], r['idx']
        notes = []
        addr_ok = all(o.get(k) for k in ('vt', 'col', 'td', 'site', 'func'))
        if not addr_ok:
            notes.append('地址字段缺')
        # 地址与实测相等（实测即 bc 同序 det）
        b = bc[idx - 1]
        if not (b['chk'][1] and b['chk'][6]):
            addr_ok = False; notes.append('地址链与字节不符')
        slot_ok = (o['slotval_n'] == r['slot'] and o['up_slot'] == r['slot']
                   and o['up_name'] == '%s::slot%d' % (r['cls'], r['slot'])
                   and o['slotval'] == r['entry'] and o['up_vt'] == r['vt'])
        if not slot_ok:
            notes.append('槽号/槽值/升级句不一致')
        cls_ok = (o['up_class'] == r['cls'])
        if not cls_ok:
            notes.append('<Class>≠行名前缀(%s)' % r['cls'])
        man = o['mangled'] or ''
        cls_man_ok = col_name_match_row_class(r['cls'], man)
        if not cls_man_ok:
            notes.append('<Class>↔TD+8 装饰名不匹配')
        has_d47 = o['d47'] is not None
        if not has_d47:
            notes.append('缺 D-47 披露句')
        d47 = o['d47'] or ''
        ptr_126 = ('§12.6' in d47) or ('12.6' in o['secs'])
        ptr_124 = ('§12.4' in d47) or ('12.4' in o['secs'])
        ptr_ok = ptr_126 and not ptr_124
        if not ptr_ok:
            notes.append('披露指针未指 §12.6' + ('（本行写的是 §12.4，已过时编号）' if ptr_124 else ''))
        ok = addr_ok and slot_ok and cls_ok and cls_man_ok and has_d47 and ptr_ok
        if not ok:
            d_bad += 1
        d_detail.append(dict(idx=idx, entry=r['entry'], cls=r['cls'], slot=r['slot'],
                             ok=ok, addr=addr_ok, slot_ok=slot_ok, cls_ok=cls_ok,
                             cls_man=cls_man_ok, has_d47=has_d47, ptr_ok=ptr_ok,
                             ptr_124=ptr_124, notes=notes, d47=d47, secs=o['secs']))
        P('  #%-2d %-46s addr=%s slot=%s <Cls>=%s Cls↔MAN=%s D47=%s 指§12.6=%s ⇒ %s' %
          (idx, '%s::slot%d' % (r['cls'], r['slot']), 'Y' if addr_ok else 'N',
           'Y' if slot_ok else 'N', 'Y' if cls_ok else 'N', 'Y' if cls_man_ok else 'N',
           'Y' if has_d47 else 'N', 'Y' if ptr_ok else 'N', 'PASS' if ok else 'FAIL'))
        if notes:
            P('       ↳ %s' % '；'.join(notes))
            P('       ↳ 本行披露句: %s' % (d47 or '（缺失）'))
    P('  ⇒ §D 不合格 %d/15' % d_bad)
    n124 = sum(1 for x in d_detail if x['ptr_124'])
    n126 = sum(1 for x in d_detail if x['ptr_ok'])
    P('  ⇒ 披露指针指 §12.6 的行数：%d/15；写成 §12.4 的行数：%d/15' % (n126, n124))
    P('')
    P('  披露指针落点核对（R14_COMMON.md 现盘的真实标题）：')
    ctxt = open(COMMON, 'rb').read().decode('utf-8').split('\n')
    for i, l in enumerate(ctxt, 1):
        if re.match(r'^#{1,6}\s*§?12\.[0-9]', l.strip()):
            P('    L%-5d %s' % (i, l.strip()[:100]))
    P('')

    # ---------------------------------------------------------------- §E
    P('-' * 78)
    P('§E 格式合先例（盘上 3 条既有 ④ 先例 + 批次 1 的 15 行）')
    P('-' * 78)
    prec_sk = []
    for e in PRECEDENT:
        if e not in cov:
            P('  !! 先例 %s 不在 coverage' % e); continue
        f = cov[e]
        i4 = f[3].find('④ 活表槽位见证')
        sk = norm_skeleton(norm_drop_d47(f[3][i4:]), name_class(f[2]))
        prec_sk.append((e, f[2], sk))
    for e, nm, sk in prec_sk:
        P('  先例 %s (%s) 骨架:' % (e, nm))
        P('    ' + sk)
    base = prec_sk[0][2] if prec_sk else None
    same_prec = all(sk == base for _e, _n, sk in prec_sk)
    P('  3 条先例归一后同骨架 ? %s' % same_prec)
    if os.path.exists(B1DELTA):
        L1, _ = read_lines(B1DELTA)
        n1 = k1 = 0
        for i, l in enumerate(L1):
            if i == 0 or not l:
                continue
            f = l.split('\t')
            if len(f) != 8:
                continue
            n1 += 1
            i4 = f[3].find('④ 活表槽位见证')
            if norm_skeleton(norm_drop_d47(f[3][i4:]), name_class(f[2])) == base:
                k1 += 1
        P('  批次 1 (%s)：%d 行，骨架与先例相同 %d 行' % (B1DELTA, n1, k1))
    e_bad = 0
    for r in d_rows:
        sk = norm_skeleton(norm_drop_d47(r['seg4']), r['cls'])
        ok = (sk == base)
        if not ok:
            e_bad += 1
        P('  #%-2d %-9s 骨架子=先例 ? %s' % (r['idx'], r['entry'], ok))
        if not ok:
            P('      本行: ' + sk)
            P('      先例: ' + (base or ''))
    P('  ⇒ §E 不合格 %d/15' % e_bad)
    P('  （骨架归一：<CLS>=类名、<N>=任何数字、<H>=8 位十六进制、<MAN>/<MANT>=RTTI 装饰名；'
      '标点/全角括号/半角空格全部保留 ⇒ 骨架相等即分隔符体例相同）')
    P('')

    # ---------------------------------------------------------------- §F
    P('-' * 78)
    P('§F 反抄袭（卡面判据：entry 归一为占位符后两两比较）')
    P('-' * 78)
    g1 = {}
    for r in d_rows:
        g1.setdefault(r['seg4'].replace(r['entry'], '<ENTRY>'), []).append(r['idx'])
    dup1 = {k: v for k, v in g1.items() if len(v) > 1}
    P('  (i) 仅把本行 entry 归一为占位符：%d 条互异 / 15，重复组 %d' % (len(g1), len(dup1)))
    for k, v in dup1.items():
        P('      重复组: %s' % v)
    g2 = {}
    for r in d_rows:
        g2.setdefault(re.sub(r'[0-9A-F]{8}', '<H>', r['seg4']), []).append(r['idx'])
    dup2 = {k: v for k, v in g2.items() if len(v) > 1}
    P('  (ii) 全 8 位十六进制归一（更严）：%d 条互异 / 15，重复组 %d' % (len(g2), len(dup2)))
    for k, v in dup2.items():
        P('      重复组: %s' % v)
    g3 = {}
    for r in d_rows:
        t = re.sub(r'[0-9A-F]{8}', '<H>', r['seg4'])
        t = re.sub(r'\d+', '<N>', t)
        g3.setdefault(t, []).append(r['idx'])
    dup3 = {k: v for k, v in g3.items() if len(v) > 1}
    P('  (iii) 再把槽号也归一（最严，仅作区分依据说明）：%d 条互异，同组 %d 组' % (len(g3), len(dup3)))
    for k, v in dup3.items():
        P('      同组: %s' % v)
    P('  字段多样性：vt=%d 种 / slot=%d 种 / class=%d 种 / site=%d 种' %
      (len(set(r['vt'] for r in d_rows)), len(set(r['slot'] for r in d_rows)),
       len(set(r['cls'] for r in d_rows)), len(set(r['o']['site'] for r in d_rows))))
    f_bad = len(dup1)
    P('  ⇒ §F 按卡面判据不合格组数：%d' % f_bad)
    P('')

    # ---------------------------------------------------------------- bytecheck.tsv
    out = os.path.join(HERE, 'bytecheck.tsv')
    with open(out, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write('row\tentry\tslot\tvt\tCOL\toffset\tTD\tsite\tfunc\t'
                 'check1_u32_vt_plus_slot4_eq_entry\tcheck2_u32_vt_minus4_eq_COL\t'
                 'check3_u32_COL_plus4_eq_offset\tcheck4_u32_COL_plus12_eq_TD\t'
                 'check5_cstr_TD_plus8_eq_mangled\tcheck6_site_mov_mem_imm32_eq_vt\t'
                 'n_ok\tverdict\n')
        for r in bc:
            cells = ['%s:%s' % ('True' if r['chk'][k] else 'False', r['det'][k]) for k in range(1, 7)]
            fh.write('\t'.join([str(r['idx']), r['entry'], str(r['slot']), r['vt'],
                                r['col'], str(r['offset']), r['td'], r['site'], r['func']]
                               + cells + [str(r['n_ok']), 'PASS' if r['n_ok'] == 6 else 'FAIL'])
                     + '\n')
    P('bytecheck.tsv 已写：%s（15 行 × 6 项，单元格为 `判定:实测值`）' % out)

    # ---------------------------------------------------------------- tables.md（附录证据表）
    tmd = os.path.join(HERE, 'tables.md')
    with open(tmd, 'w', encoding='utf-8', newline='\n') as fh:
        w = fh.write
        w('# R16-AUDIT-SLOTN-B2 · 机械生成的逐行证据表\n\n')
        w('> 由 `verify.py` 生成，勿手改。所有数值均来自脚本对 `gamemd.exe` / `coverage.tsv` / `delta.tsv` 的只读实测。\n\n')
        w('## 基线\n\n')
        w('| 对象 | 实测 |\n|---|---|\n')
        w('| `ra2youli\\gamemd.exe` | %d B，SHA-256 `%s` |\n' % (len(img.data), gsha))
        w('| `COVERAGE\\coverage.tsv` | %d B，SHA-256 `%s` |\n' % (os.path.getsize(COV), sha256_file(COV)))
        w('| `R16_SLOTN_B2\\delta.tsv` | %d B，SHA-256 `%s` |\n\n' % (os.path.getsize(DELTA), sha256_file(DELTA)))
        w('## §A 最小改动（原第 4 列严格前缀 + 其余 6 列逐字节）\n\n')
        w('| # | entry | coverage 行号 | 原第4列 B | 原句末 | 追加 B | 追加首字符 | 严格前缀 | 其余6列 | 判 |\n')
        w('|---|---|---|---|---|---|---|---|---|---|\n')
        for r in a_rows:
            w('| %d | %s | %s | %s | %s | %s | %s | %s | %s | %s |\n' %
              (r['idx'], r['entry'], r.get('cov_lineno', '-'), r.get('orig_len', '-'),
               r.get('orig_last', '-'), r.get('add_len', '-'), r.get('add_head', '-')[:1],
               r.get('prefix'), r.get('cols_ok'), 'PASS' if r['ok'] else 'FAIL'))
        w('\n## §B 六项实测值\n\n')
        w('| # | entry | slot | ①u32(vt+slot*4) | ②u32(vt-4)=COL | ③u32(COL+4)=offset | '
          '④u32(COL+12)=TD | ⑤cstr(TD+8) | ⑥装表点解码 | 6/6 |\n')
        w('|---|---|---|---|---|---|---|---|---|---|\n')
        for r in bc:
            w('| %d | %s | %d | `%s` | `%s` | `%s` | `%s` | `%s` | `%s` | %s |\n' %
              (r['idx'], r['entry'], r['slot'], r['det'][1], r['det'][2], r['det'][3],
               r['det'][4], r['det'][5], r['det'][6], r['n_ok']))
        w('\n## §B 辅助：体内/体外、独立枚举活表、装表点全集\n\n')
        w('| # | entry | 宿主 body | site 体内/entry 体外 | 同槽活表（独立枚举） | 该 vt 装表点全集 | 宿主内唯一写入 |\n')
        w('|---|---|---|---|---|---|---|\n')
        for r in bc:
            w('| %d | %s | `%s` | %s | %s | %s | %s |\n' %
              (r['idx'], r['entry'], r['det'].get('body', '-'), r['det'].get('inbody', '-'),
               r['det']['tables'], r['det']['install_sites'], r['det']['final_primary']))
        w('\n## §D 文本与事实一致\n\n')
        w('| # | entry | 行名 | addr | slot 自洽 | <Class>=行名前缀 | <Class>↔TD+8 | 有 D-47 句 | 指 §12.6 | 判 | 备注 |\n')
        w('|---|---|---|---|---|---|---|---|---|---|---|\n')
        for x in d_detail:
            w('| %d | %s | %s::slot%d | %s | %s | %s | %s | %s | %s | %s | %s |\n' %
              (x['idx'], x['entry'], x['cls'], x['slot'], x['addr'], x['slot_ok'],
               x['cls_ok'], x['cls_man'], x['has_d47'], x['ptr_ok'],
               'PASS' if x['ok'] else 'FAIL', '；'.join(x['notes']) or '-'))
        w('\n## §E 骨架归一（先例 3 条）\n\n```text\n%s\n```\n\n' % (base or ''))
        w('| # | entry | 骨架子=先例 |\n|---|---|---|\n')
        for r in d_rows:
            sk = norm_skeleton(norm_drop_d47(r['seg4']), r['cls'])
            w('| %d | %s | %s |\n' % (r['idx'], r['entry'], sk == base))
        w('\n## §F 归一化分组\n\n')
        w('- (i) 仅归一 entry：%d 条互异，重复组 %d\n' % (len(g1), len(dup1)))
        w('- (ii) 全 8 位十六进制归一：%d 条互异，重复组 %d\n' % (len(g2), len(dup2)))
        w('- (iii) 再归一槽号（最严）：同组 %d 组\n' % len(dup3))
        for k, v in dup3.items():
            w('  - %s\n' % v)
    P('tables.md 已写：%s' % tmd)

    # ---------------------------------------------------------------- 汇总
    P('')
    P('=' * 78)
    P('汇总  §A 不符 %d | §B 6/6 不全 %d | §D 不符 %d（其中披露指针 §12.4 过时 %d）'
      ' | §E 不符 %d | §F 重复组 %d' % (a_bad, b_bad, d_bad, n124, e_bad, f_bad))
    P('行 30 改选：%s' % ('成立' if verdict_c else '不成立'))
    P('=' * 78)

    import json
    with open(os.path.join(HERE, 'verify_out.json'), 'w', encoding='utf-8') as fh:
        json.dump(dict(
            gamemd=dict(size=len(img.data), sha256=gsha),
            coverage=dict(size=os.path.getsize(COV), sha256=sha256_file(COV)),
            delta=dict(size=os.path.getsize(DELTA), sha256=sha256_file(DELTA)),
            A=dict(bad=a_bad, rows=a_rows),
            B=dict(bad=b_bad, rows=[dict(idx=r['idx'], entry=r['entry'], n_ok=r['n_ok'],
                                         chk=r['chk'], det=r['det']) for r in bc]),
            C=c, C_verdict=verdict_c,
            D=dict(bad=d_bad, rows=d_detail, n_126=n126, n_124=n124),
            E=dict(bad=e_bad, base=base),
            F=dict(bad=f_bad, dups={k: v for k, v in dup1.items()},
                   dups_hex={k: v for k, v in dup2.items()}),
        ), fh, ensure_ascii=False, indent=1)
    P('verify_out.json 已写')
    return 0


if __name__ == '__main__':
    sys.exit(main())
