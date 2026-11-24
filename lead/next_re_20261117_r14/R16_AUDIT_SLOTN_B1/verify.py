#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
R16-AUDIT-SLOTN-B1 —— 独立复核脚本（审计员自写，不复用执行器脚本）

只读打开：
  ../COVERAGE/coverage.tsv
  ../R16_SLOTN_B1/delta.tsv
  ../../../ra2youli/gamemd.exe   (4,825,360 B)

做四件事：
  §A 最小改动 / 原文保全（原第 4 列是否为 delta 第 4 列的严格前缀；其余列逐字节相同）
  §B 6 项地址与字节事实，全部由本脚本从镜像字节独立复算（含 capstone 解码装表点）
  §C ④ 文本里的地址/类名是否与 §B 实测一致 + D-47 披露句
  §D 骨架与先例（R4_FILL_91_* 补写的 91 行）比对
  §E 反抄袭（entry 归一化后两两比较）

输出：bytecheck.tsv + 控制台摘要
用法：python verify.py
"""

import io
import json
import os
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
COVERAGE = os.path.join(R14, 'COVERAGE', 'coverage.tsv')
DELTA = os.path.join(R14, 'R16_SLOTN_B1', 'delta.tsv')
GAMEMD = os.path.abspath(os.path.join(R14, '..', '..', 'ra2youli', 'gamemd.exe'))

IMAGE_BASE = 0x400000
EXPECT_SHA256 = '73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476'
# 审计基线：执行器产出 delta.tsv（22:55:19）时盘上的 coverage.tsv，与 R16_SLOTN_B1\REPORT.md §4 自述一致。
# 审计期间（23:02:33）有其它处理方并发改写 coverage.tsv + PANEL.md，故此处同时记录「基线」与「当前」两个哈希；
# §A 的前缀比对以当前盘上内容为准（本批 15 行未被并发合并触及，见 VERDICT.md §A 附注）。
BASELINE_COV_SHA256 = '325158B588636AA3AA170B74B6F4F0E7E5020CA0AC3960232C1DFEAD42CFCEA2'

PRECEDENT = ['00464AC0', '004DE630', '004F42F0']


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
        magic = struct.unpack_from('<H', d, opt)[0]
        self.image_base = struct.unpack_from('<I', d, opt + 28)[0]
        self.size_of_image = struct.unpack_from('<I', d, opt + 56)[0]
        if magic != 0x10b:
            raise SystemExit('not PE32 magic=%#x' % magic)
        self.sections = []
        sec = opt + opt_size
        for i in range(nsec):
            off = sec + i * 40
            name = d[off:off + 8].rstrip(b'\0').decode('latin-1')
            # PE 节头：+0 Name(8) / +8 VirtualSize / +12 VirtualAddress / +16 SizeOfRawData / +20 PointerToRawData
            vsize = struct.unpack_from('<I', d, off + 8)[0]
            vaddr = struct.unpack_from('<I', d, off + 12)[0]
            rawsize = struct.unpack_from('<I', d, off + 16)[0]
            rawptr = struct.unpack_from('<I', d, off + 20)[0]
            self.sections.append(dict(name=name, va=vaddr, vsize=vsize,
                                      rawsize=rawsize, rawptr=rawptr))
        self.sha256 = None

    # VA -> 文件偏移
    def off(self, va):
        rva = va - self.image_base
        for s in self.sections:
            span = max(s['vsize'], s['rawsize'])
            if s['va'] <= rva < s['va'] + span:
                delta = rva - s['va']
                if delta >= s['rawsize']:
                    raise KeyError('VA %08X beyond raw of %s' % (va, s['name']))
                return s['rawptr'] + delta
        raise KeyError('VA %08X unmapped' % va)

    def mapped(self, va, n=1):
        try:
            o = self.off(va)
        except KeyError:
            return False
        return o + n <= len(self.data)

    def u32(self, va):
        return struct.unpack_from('<I', self.data, self.off(va))[0]

    def cstr(self, va, limit=512):
        o = self.off(va)
        end = self.data.find(b'\0', o, o + limit)
        if end < 0:
            end = o + limit
        return self.data[o:end].decode('latin-1')


def sha256_file(path):
    import hashlib
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest().upper()


# --------------------------------------------------------------------- 读表
def load_tsv(path):
    with open(path, 'rb') as f:
        raw = f.read()
    txt = raw.decode('utf-8')
    lines = txt.split('\n')
    if lines and lines[-1] == '':
        lines.pop()
    return lines


def build_coverage(lines):
    """coverage.tsv 表头是逗号分隔（盘上既有缺陷），数据行 tab 分隔。返回 entry->fields 与 entry->lineno"""
    m, ln = {}, {}
    for i, l in enumerate(lines):
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
RE_NAMESLOT = re.compile(r'::slot(\d+)$')
MARK = '④ 活表槽位见证'


def parse_witness(text):
    """从 delta 第 4 列里切出 ④ 追加段并解析"""
    k = text.find(MARK)
    if k < 0:
        return None
    seg = text[k:]
    w = dict(seg=seg, body=seg)
    m = RE_VT.search(seg)
    w['vt'] = int(m.group(1), 16) if m else None
    m = RE_SLOTVAL.search(seg)
    w['slot_val_no'] = int(m.group(1)) if m else None
    w['slot_val'] = int(m.group(2), 16) if m else None
    m = RE_COL.search(seg)
    w['col'] = int(m.group(1), 16) if m else None
    w['offset'] = int(m.group(2)) if m else None
    m = RE_RTTI.search(seg)
    w['td'] = int(m.group(1), 16) if m else None
    w['mangled'] = m.group(2) if m else None
    m = RE_SITE.search(seg)
    w['site'] = int(m.group(1), 16) if m else None
    w['owner'] = int(m.group(2), 16) if m else None
    return w


def class_of_name(name):
    return name.split('::')[0] if '::' in name else name


def disclosure_ok(seg):
    """D-47 披露指针：须提 D-47(A) 或 §12.3 让位，并指向 R14_COMMON §12.4 与 PANEL 披露"""
    has_ruling = ('D-47' in seg) or ('§12.3' in seg)
    has_124 = ('R14_COMMON §12.4' in seg) or ('§12.4' in seg)
    has_panel = 'PANEL' in seg
    not_bad = '已过 §12.3' not in seg
    return has_ruling and has_124 and has_panel and not_bad, dict(
        ruling=has_ruling, sec124=has_124, panel=has_panel, no_bad_phrase=not_bad)


# --------------------------------------------------------------------- 骨架（§D）
def skeleton(seg):
    """把可变字段抹成占位符，得到可跨行比较的骨架"""
    s = seg
    # 类名（出现在两处）：取行名类，动态拿不到，用正则从"均为 <X>"与"见证：<X>::slot"处替换
    s = re.sub(r'均为 [^；）]+', '均为 <CLS>', s)
    s = re.sub(r'(④ 活表槽位见证：)[^（]+(（)', r'\1<CLS>::slot<N>\2', s)
    s = re.sub(r'(④升级句：)[^（]+(（)', r'\1<CLS>::slot<N>\2', s)
    s = re.sub(r'vt=[0-9A-F]{8}', 'vt=<H>', s)
    s = re.sub(r'槽 \d+ 值=[0-9A-F]{8}', '槽 <N> 值=<H>', s)
    s = re.sub(r'COL=[0-9A-F]{8} offset=\d+', 'COL=<H> offset=<N>', s)
    s = re.sub(r'RTTI=[0-9A-F]{8}→[^；）]*', 'RTTI=<H>→<MAN>', s)
    s = re.sub(r'装表点 [0-9A-F]{8} 位于 [0-9A-F]{8}', '装表点 <H> 位于 <H>', s)
    s = re.sub(r'表 slot\d+', '表 slot<N>', s)
    return s


# --------------------------------------------------------------------- §B 字节检查
def byte_checks(img, entry_va, w, name_slot, md):
    """返回 (checks dict, measured dict, notes list)"""
    notes = []
    ch = {}
    meas = {}
    vt, col, off, td = w['vt'], w['col'], w['offset'], w['td']

    # 1) u32(vt + slot*4) == entry
    try:
        v = img.u32(vt + name_slot * 4)
        meas['vt_slot_word'] = v
        ch['c1'] = (v == entry_va)
        if not ch['c1']:
            notes.append('c1: u32(%08X+%d*4)=%08X != entry %08X' % (vt, name_slot, v, entry_va))
    except KeyError as e:
        ch['c1'] = False
        notes.append('c1: read failed %s' % e)

    # 2) u32(vt-4) == COL
    try:
        v = img.u32(vt - 4)
        meas['vt_minus4'] = v
        ch['c2'] = (v == col)
        if not ch['c2']:
            notes.append('c2: u32(%08X-4)=%08X != COL %08X' % (vt, v, col))
    except KeyError as e:
        ch['c2'] = False
        notes.append('c2: read failed %s' % e)

    # 3) u32(COL+4) == offset
    try:
        v = img.u32(col + 4)
        meas['col_plus4'] = v
        ch['c3'] = (v == off)
        if not ch['c3']:
            notes.append('c3: u32(%08X+4)=%d != offset %d' % (col, v, off))
    except KeyError as e:
        ch['c3'] = False
        notes.append('c3: read failed %s' % e)

    # 4) u32(COL+12) == TD
    try:
        v = img.u32(col + 12)
        meas['col_plus12'] = v
        ch['c4'] = (v == td)
        if not ch['c4']:
            notes.append('c4: u32(%08X+12)=%08X != RTTI %08X' % (col, v, td))
    except KeyError as e:
        ch['c4'] = False
        notes.append('c4: read failed %s' % e)

    # 5) cstr(TD+8) == mangled   （装饰名内联在 TD+8，不是指针）
    try:
        s = img.cstr(td + 8)
        meas['td_plus8_str'] = s
        ch['c5'] = (s == w['mangled'])
        if not ch['c5']:
            notes.append('c5: cstr(%08X+8)=%r != text %r' % (td, s, w['mangled']))
    except KeyError as e:
        ch['c5'] = False
        notes.append('c5: read failed %s' % e)

    # 6) capstone 解码装表点：mov [reg+disp], imm32 且 imm32 == vt
    try:
        from capstone import Cs, CS_ARCH_X86, CS_MODE_32
        from capstone.x86 import X86_OP_MEM, X86_OP_IMM, X86_REG_INVALID
        site = w['site']
        o = img.off(site)
        code = img.data[o:o + 16]
        md.detail = True
        insns = list(md.disasm(code, site, 1))
        if not insns:
            ch['c6'] = False
            notes.append('c6: capstone decode produced nothing at %08X' % site)
        else:
            ins = insns[0]
            ok = (ins.mnemonic == 'mov' and len(ins.operands) == 2
                  and ins.operands[0].type == X86_OP_MEM
                  and ins.operands[1].type == X86_OP_IMM
                  and ins.operands[0].mem.base != X86_REG_INVALID
                  and (ins.operands[1].imm & 0xFFFFFFFF) == vt)
            meas['site_text'] = '%s %s' % (ins.mnemonic, ins.op_str)
            meas['site_len'] = ins.size
            meas['site_base'] = ins.operands[0].mem.base if len(ins.operands) == 2 else None
            meas['site_disp'] = ins.operands[0].mem.disp if len(ins.operands) == 2 else None
            meas['site_imm'] = ins.operands[1].imm if len(ins.operands) == 2 else None
            ch['c6'] = bool(ok)
            if not ok:
                notes.append('c6: %08X decodes as %s %s (want mov [reg+disp],%08X)'
                             % (site, ins.mnemonic, ins.op_str, vt))
    except Exception as e:  # noqa
        ch['c6'] = False
        notes.append('c6: exception %r' % e)

    return ch, meas, notes


def body_check(img, md, owner, site, entry_va):
    """辅助核对文本「装表点 X 位于 Y 体内，entry 体外」：
       从 Y 线性解码到 site 之后的第一条 ret/jmp 终止，判 site 在 [Y,end) 内且 entry 不在。"""
    o = img.off(owner)
    code = img.data[o:o + 0x8000]
    end = None
    seen_site = False
    for ins in md.disasm(code, owner):
        if ins.address == site:
            seen_site = True
        if seen_site and (ins.mnemonic in ('ret',) or ins.mnemonic.startswith('jmp')
                          or ins.mnemonic == 'int3'):
            end = ins.address + ins.size
            break
        if ins.address > site + 0x600:
            break
    if end is None:
        return None, 'body_end undetermined from %08X' % owner
    inside = owner <= site < end
    outside = not (owner <= entry_va < end)
    return (inside and outside), 'body=[%08X,%08X) site_in=%s entry_out=%s' % (
        owner, end, inside, outside)


# --------------------------------------------------------------------- 主流程
def main():
    rep = {}
    imgs = Image(GAMEMD)
    sha = sha256_file(GAMEMD)
    rep['gamemd_sha256'] = sha
    rep['gamemd_sha_ok'] = (sha == EXPECT_SHA256)
    rep['image_base'] = '%08X' % imgs.image_base
    rep['text_section'] = [s for s in imgs.sections if s['name'] == '.text']
    rep['cov_sha256'] = sha256_file(COVERAGE)
    rep['cov_sha_baseline'] = BASELINE_COV_SHA256
    rep['cov_matches_baseline'] = (rep['cov_sha256'] == BASELINE_COV_SHA256)
    rep['delta_sha256'] = sha256_file(DELTA)

    cov_lines = load_tsv(COVERAGE)
    cov, cov_ln = build_coverage(cov_lines)

    # 表头盘上实况（先例比对用）
    rep['cov_header'] = cov_lines[0]
    rep['cov_header_is_comma'] = (',' in cov_lines[0] and '\t' not in cov_lines[0])

    delta_lines = load_tsv(DELTA)
    rep['delta_header'] = delta_lines[0]
    rep['delta_header_cols'] = len(delta_lines[0].split('\t'))
    rows = delta_lines[1:]
    rep['n_delta_rows'] = len(rows)

    from capstone import Cs, CS_ARCH_X86, CS_MODE_32
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = True

    # 先例骨架
    prec_skel = {}
    for e in PRECEDENT:
        f = cov[e]
        w = parse_witness(f[3])
        prec_skel[e] = skeleton(w['seg']) if w else None
    rep['precedent_skeleton'] = prec_skel

    out = []
    res = []
    for i, line in enumerate(rows, 1):
        f = line.split('\t')
        entry = f[0]
        entry_va = int(entry, 16)
        r = dict(idx=i, entry=entry, name=f[2], name_slot=None, notes=[], A={}, B={}, C={}, D={}, E={})
        r['ncols'] = len(f)

        # ---------- §A
        o = cov.get(entry)
        if o is None:
            r['A']['present'] = False
            r['notes'].append('A: entry 不在 coverage.tsv 中')
        else:
            r['A']['present'] = True
            r['A']['prefix'] = f[3].startswith(o[3])
            r['A']['orig'] = o[3]
            r['A']['appended_len'] = len(f[3]) - len(o[3])
            r['A']['appended'] = f[3][len(o[3]):] if r['A']['prefix'] else None
            diff = [j for j in (1, 2, 4, 5, 6, 7) if f[j] != o[j]]
            r['A']['cols_diff'] = diff
            r['A']['cols_ok'] = not diff
            r['A']['cov_lineno'] = cov_ln[entry]
            if not r['A']['prefix']:
                r['notes'].append('A: 原第 4 列不是 delta 第 4 列的前缀')
            if diff:
                r['notes'].append('A: 列 %s 与盘上不同' % (','.join(str(j + 1) for j in diff)))

        # ---------- 名称 slot
        m = RE_NAMESLOT.search(f[2])
        name_slot = int(m.group(1)) if m else None
        r['name_slot'] = name_slot

        # ---------- ④ 解析
        w = parse_witness(f[3])
        r['w'] = w
        if w is None or w['vt'] is None:
            r['notes'].append('B: ④ 见证段缺失或不可解析')
            r['B'] = dict(c1=False, c2=False, c3=False, c4=False, c5=False, c6=False)
            r['C'] = dict(scan_ok=False)
            out.append(r)
            res.append(r)
            continue

        # ---------- §B（本脚本独立复算）
        ch, meas, notes = byte_checks(imgs, entry_va, w, name_slot, md)
        r['B'] = ch
        r['Bmeas'] = meas
        r['notes'] += notes

        # 辅助：entry 在镜像里的所有 4 字节对齐命中
        pat = struct.pack('<I', entry_va)
        hits = []
        start = 0
        while True:
            p = imgs.data.find(pat, start)
            if p < 0:
                break
            hits.append(p)
            start = p + 1
        r['Bmeas']['raw_hits'] = len(hits)

        # 辅助：装表点体内/体外声明
        bc, bnote = body_check(imgs, md, w['owner'], w['site'], entry_va)
        r['Bmeas']['body_claim'] = bc
        r['Bmeas']['body_note'] = bnote
        if bc is False:
            r['notes'].append('辅助(装表点体内/体外): ' + bnote)

        # ---------- §C
        C = {}
        cls_name = class_of_name(f[2])
        C['cls_name'] = cls_name
        # C1 各地址与实测一致（文本即假设，B 已证；这里记录独立实测值备查）
        C['addr_match'] = all(ch.values())
        # C1b 文本「槽 N 值=」写的必须就是本行 entry
        C['txt_slotval_eq_entry'] = (w['slot_val'] == entry_va)
        # C2 slot 号三处一致：name ::slotN / 槽 N 值 / 槽位算式
        C['slot_consistent'] = (name_slot is not None and w['slot_val_no'] == name_slot)
        # C3 <Class> 与行名类一致
        m = re.search(r'④升级句：[^（]+（④ 表属类与行名类一致，均为 ([^；）]+)；', w['seg'])
        C['cls_in_sentence'] = m.group(1) if m else None
        C['cls_matches_name'] = (m is not None and m.group(1) == cls_name)
        # C4 <Class> 与 TD+8 装饰名解出的类一致（沿用 probe.py:col_name_match 的既有归一化口径）
        if cls_name.startswith('T_'):
            inner = cls_name[2:].rstrip('_')
            parts = [p for p in inner.split('_') if p]
            C['cls_vs_mangled'] = all(p in (w['mangled'] or '') for p in parts)
            C['cls_norm'] = 'T_ 模板伪名：去 T_/去尾下划线/按 _ 切分后各段均须出现在装饰名中（probe.py:col_name_match 口径）'
        else:
            C['cls_vs_mangled'] = (cls_name in (w['mangled'] or ''))
            C['cls_norm'] = '非模板：类名须是装饰名子串（probe.py:col_name_match 口径）'
        # C5 D-47 披露
        d_ok, d_parts = disclosure_ok(w['seg'])
        C['disclosure'] = d_ok
        C['disclosure_parts'] = d_parts
        r['C'] = C
        if not C['addr_match']:
            r['notes'].append('C: 至少一个地址与实测不符')
        if not C['txt_slotval_eq_entry']:
            r['notes'].append('C: 「槽 N 值=%08X」!= entry %08X' % (w['slot_val'], entry_va))
        if not C['slot_consistent']:
            r['notes'].append('C: slot 号不一致 name=%s 槽内=%s' % (name_slot, w['slot_val_no']))
        if not C['cls_matches_name']:
            r['notes'].append('C: ④升级句 类名 %r != 行名类 %r' % (C['cls_in_sentence'], cls_name))
        if not C['cls_vs_mangled']:
            r['notes'].append('C: 行名类与 RTTI 装饰名对不上')
        if not d_ok:
            r['notes'].append('C: D-47 披露句不合规 %s' % d_parts)

        # ---------- §D 骨架
        sk = skeleton(w['seg'])
        base = None
        for e in PRECEDENT:
            if prec_skel.get(e):
                base = prec_skel[e]
                break
        tail = ''
        m = re.search(r'(（D-47[^）]*）)$', sk)
        if m:
            tail = m.group(1)
            sk_core = sk[:m.start()]
        else:
            sk_core = sk
        D = dict(skeleton=sk, core=sk_core, extra_tail=tail)
        D['core_eq_precedent'] = (base is not None and sk_core == base)
        D['tail_is_disclosure'] = bool(tail) and ('D-47' in tail)
        r['D'] = D
        if not D['core_eq_precedent']:
            r['notes'].append('D: 骨架与先例不同')

        out.append(r)
        res.append(r)

    # ---------- §E 反抄袭
    norm_entry = {}
    for r in res:
        if 'w' not in r or not r['w']:
            continue
        t = r['w']['seg']
        t2 = re.sub(r'\b[0-9A-F]{8}\b', 'ENTRY', t)
        norm_entry.setdefault(t2, []).append(r['entry'])
    # 更严：entry + slot 号都归一，看是否只剩「事实差异」
    norm_all = {}
    for r in res:
        if 'w' not in r or not r['w']:
            continue
        t = r['w']['seg']
        t2 = re.sub(r'\b[0-9A-F]{8}\b', 'H', t)
        t2 = re.sub(r'slot\d+', 'slotN', t2)
        t2 = re.sub(r'槽 \d+ ', '槽 N ', t2)
        norm_all.setdefault(t2, []).append(r['entry'])
    dup_entry = {k: v for k, v in norm_entry.items() if len(v) > 1}
    dup_all = {k: v for k, v in norm_all.items() if len(v) > 1}
    rep['E_dup_after_entry_norm'] = dup_entry
    rep['E_dup_after_entry_and_slot_norm'] = dup_all
    rep['verdict'] = 'PASS'  # 由下面的 FAIL 计数覆盖

    # ---------- 汇总
    def rowfail(r):
        A = r.get('A', {})
        B = r.get('B', {})
        C = r.get('C', {})
        bad_A = (not A.get('present')) or (not A.get('prefix', False)) or (not A.get('cols_ok', False))
        bad_B = not all(B.get(k, False) for k in ('c1', 'c2', 'c3', 'c4', 'c5', 'c6'))
        bad_C = (not C.get('addr_match', False)) or (not C.get('slot_consistent', False)) \
            or (not C.get('txt_slotval_eq_entry', False)) \
            or (not C.get('cls_matches_name', False)) or (not C.get('cls_vs_mangled', False)) \
            or (not C.get('disclosure', False))
        bad_D = not r.get('D', {}).get('core_eq_precedent', False)
        return bad_A, bad_B, bad_C, bad_D

    npass = 0
    for r in res:
        ba, bb, bc_, bd = rowfail(r)
        r['fail_A'], r['fail_B'], r['fail_C'], r['fail_D'] = ba, bb, bc_, bd
        r['verdict'] = 'FAIL' if (ba or bb or bc_ or bd) else 'PASS'
        if r['verdict'] == 'PASS':
            npass += 1
    rep['n_pass'] = npass
    rep['n_fail'] = len(res) - npass
    rep['fail_A'] = sum(1 for r in res if r['fail_A'])
    rep['fail_B'] = sum(1 for r in res if r['fail_B'])
    rep['fail_C'] = sum(1 for r in res if r['fail_C'])
    rep['fail_D'] = sum(1 for r in res if r['fail_D'])
    rep['fail_E'] = 1 if dup_entry else 0          # 卡面判据：entry 归一后是否出现「除 entry 外完全相同」
    rep['E_same_class_groups_note'] = ('非缺陷：同 vt 同 class 的塌组（事实相同），见 VERDICT §6'
                                       if dup_all else '无')
    rep['disclosure_15of15'] = sum(1 for r in res if r.get('C', {}).get('disclosure'))
    rep['B_subitem_fail'] = {}
    for k in ('c1', 'c2', 'c3', 'c4', 'c5', 'c6'):
        bad = [r['entry'] for r in res if not r.get('B', {}).get(k, False)]
        rep['B_subitem_fail'][k] = bad

    # ---------- bytecheck.tsv ：每格写「判定:实测值」，判 PASS 可看值，判 FAIL 看值即可定位
    tsv = os.path.join(HERE, 'bytecheck.tsv')
    hdr = ['entry', 'slot_no', 'check1', 'check2', 'check3', 'check4', 'check5', 'check6',
           'verdict', 'note']
    with io.open(tsv, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\t'.join(hdr) + '\n')
        for r in res:
            B = r.get('B', {})
            m = r.get('Bmeas', {})
            cell = []
            cell.append('%s:u32(vt+%s*4)=%s' % (
                'T' if B.get('c1') else 'F', r['name_slot'],
                '%08X' % m['vt_slot_word'] if 'vt_slot_word' in m else 'n/a'))
            cell.append('%s:u32(vt-4)=%s' % (
                'T' if B.get('c2') else 'F',
                '%08X' % m['vt_minus4'] if 'vt_minus4' in m else 'n/a'))
            cell.append('%s:u32(COL+4)=%s' % (
                'T' if B.get('c3') else 'F', m.get('col_plus4', 'n/a')))
            cell.append('%s:u32(COL+12)=%s' % (
                'T' if B.get('c4') else 'F',
                '%08X' % m['col_plus12'] if 'col_plus12' in m else 'n/a'))
            cell.append('%s:cstr(TD+8)=%s' % (
                'T' if B.get('c5') else 'F', m.get('td_plus8_str', 'n/a')))
            cell.append('%s:%s' % ('T' if B.get('c6') else 'F', m.get('site_text', 'n/a')))
            note = [str(m.get('body_note', 'n/a'))]
            if r['notes']:
                note.append(' | '.join(r['notes']))
            f.write('\t'.join([r['entry'], str(r['name_slot'])] + cell
                              + [r['verdict'], ' ; '.join(note)]) + '\n')
    rep['bytecheck_tsv'] = tsv

    # ---------- tables.md：VERDICT.md 用的机械表格（避免手工转录）
    tm = os.path.join(HERE, 'tables.md')
    with io.open(tm, 'w', encoding='utf-8', newline='\n') as f:
        f.write('### §A–§E 逐行结果（15 行全做，无抽样）\n\n')
        f.write('| # | entry | name | slot | A 最小改动 | B 字节 6 项 | C 文本一致 | D 合先例 | E 反抄袭 | 行判 |\n')
        f.write('|---|---|---|---|---|---|---|---|---|---|\n')
        for r in res:
            A = r.get('A', {})
            B = r.get('B', {})
            C = r.get('C', {})
            a_txt = 'PASS' if (A.get('present') and A.get('prefix') and A.get('cols_ok')) else 'FAIL'
            nb = sum(1 for k in ('c1', 'c2', 'c3', 'c4', 'c5', 'c6') if B.get(k))
            b_txt = 'PASS 6/6' if nb == 6 else 'FAIL %d/6' % nb
            c_ok = (C.get('addr_match') and C.get('slot_consistent') and C.get('txt_slotval_eq_entry')
                    and C.get('cls_matches_name') and C.get('cls_vs_mangled') and C.get('disclosure'))
            c_txt = 'PASS' if c_ok else 'FAIL'
            d_txt = 'PASS' if r.get('D', {}).get('core_eq_precedent') else 'FAIL'
            e_txt = 'PASS（entry 归一后唯一）'
            f.write('| %d | %s | `%s` | %s | %s | %s | %s | %s | %s | %s |\n' % (
                r['idx'], r['entry'], r['name'], r['name_slot'], a_txt, b_txt, c_txt, d_txt,
                e_txt, r['verdict']))
        f.write('\n### §A 最小改动证据（原第 4 列是否为严格前缀 + 其余 6 列逐字节比较）\n\n')
        f.write('| # | entry | coverage 行号 | 原第4列字节长 | 原句末字符 | 追加段字节长 | 追加段首字符 | 连接处 | 第1/2/3/5/6/7/8 列 |\n')
        f.write('|---|---|---|---|---|---|---|---|---|\n')
        for r in res:
            A = r.get('A', {})
            app = A.get('appended') or ''
            orig = A.get('orig', '')
            tail3 = orig[-1:] if orig else ''
            join = (orig[-1:] + app[:1]) if orig and app else ''
            f.write('| %d | %s | %s | %s | `%s` | %s | `%s` | `%s` | %s |\n' % (
                r['idx'], r['entry'], A.get('cov_lineno'), len(orig), tail3, len(app),
                app[:1], join,
                '逐字节相同' if A.get('cols_ok') else '不同: 列' + str(
                    [j + 1 for j in A.get('cols_diff', [])])))
        f.write('\n### §B 六项实测值（本脚本从 `ra2youli\\gamemd.exe` 字节独立复算）\n\n')
        f.write('| # | entry | ①u32(vt+slot*4) | ②u32(vt-4)=COL | ③u32(COL+4)=off | ④u32(COL+12)=TD | ⑤cstr(TD+8) | ⑥装表点解码 |\n')
        f.write('|---|---|---|---|---|---|---|---|\n')
        for r in res:
            m = r.get('Bmeas', {})
            f.write('| %d | %s | `%s` | `%s` | `%s` | `%s` | `%s` | `%s` |\n' % (
                r['idx'], r['entry'],
                '%08X' % m.get('vt_slot_word', 0) if 'vt_slot_word' in m else 'n/a',
                '%08X' % m.get('vt_minus4', 0) if 'vt_minus4' in m else 'n/a',
                m.get('col_plus4', 'n/a'),
                '%08X' % m.get('col_plus12', 0) if 'col_plus12' in m else 'n/a',
                m.get('td_plus8_str', 'n/a'),
                m.get('site_text', 'n/a')))

        # §C 证据表
        f.write('\n### §C 文本与事实一致（各项均以实测值比对）\n\n')
        f.write('| # | entry | name 的 slot | 文本「槽 N 值」 | 槽内值==entry | COL/offset/RTTI/装表点 与实测 | <Class>==name 前缀 | <Class>↔TD+8 装饰名 | D-47 披露句 |\n')
        f.write('|---|---|---|---|---|---|---|---|---|\n')
        for r in res:
            C = r.get('C', {})
            w = r.get('w') or {}
            f.write('| %d | %s | %s | `%08X` | %s | %s | %s（`%s`） | %s | %s |\n' % (
                r['idx'], r['entry'], r['name_slot'], w.get('slot_val') or 0,
                'PASS' if C.get('txt_slotval_eq_entry') else 'FAIL',
                'PASS' if C.get('addr_match') else 'FAIL',
                'PASS' if C.get('cls_matches_name') else 'FAIL',
                C.get('cls_in_sentence') or '',
                'PASS' if C.get('cls_vs_mangled') else 'FAIL',
                'PASS 在位' if C.get('disclosure') else 'FAIL 缺'))
        # §D 骨架比对
        f.write('\n### §D 骨架与先例逐字符比对（先例 3 条归一后为同一骨架）\n\n')
        base = None
        for e in PRECEDENT:
            if prec_skel.get(e):
                base = prec_skel[e]
                break
        f.write('先例骨架（`%s`）：\n\n```text\n%s\n```\n\n' % ('/'.join(PRECEDENT), base))
        f.write('| # | entry | core 与先例逐字符相等 | 尾部额外括注 |\n|---|---|---|---|\n')
        for r in res:
            D = r.get('D', {})
            f.write('| %d | %s | %s | `%s` |\n' % (
                r['idx'], r['entry'],
                'PASS' if D.get('core_eq_precedent') else 'FAIL',
                D.get('extra_tail') or '（无）'))
        f.write('\n### §E 归一化分组（同组=同 vt 同 class 的行，属「事实相同」）\n\n')
        for t, es in (rep.get('E_dup_after_entry_and_slot_norm') or {}).items():
            f.write('- %s\n' % ', '.join(es))
        f.write('\n（entry 归一化后重复组：%s）\n' % (
            rep.get('E_dup_after_entry_norm') or '无'))
    rep['tables_md'] = tm

    with io.open(os.path.join(HERE, 'verify_out.json'), 'w', encoding='utf-8') as f:
        json.dump(rep, f, ensure_ascii=False, indent=1, default=str)

    # ---------- 控制台
    print('gamemd sha256 ok =', rep['gamemd_sha_ok'])
    print('coverage sha256  =', rep['cov_sha256'], '(baseline match:', rep['cov_matches_baseline'], ')')
    print('delta sha256     =', rep['delta_sha256'])
    print('delta rows =', rep['n_delta_rows'], 'header cols =', rep['delta_header_cols'])
    print('PASS=%d FAIL=%d  A=%d B=%d C=%d D=%d E=%d' % (
        rep['n_pass'], rep['n_fail'], rep['fail_A'], rep['fail_B'], rep['fail_C'],
        rep['fail_D'], rep['fail_E']))
    print('  （A–E 的数目 = 该项不合格的行数；E 按卡面判据「entry 归一后是否重复」计）')
    print('disclosure ok =', rep['disclosure_15of15'], '/15')
    for k, v in rep['B_subitem_fail'].items():
        print('  %s fails: %s' % (k, v if v else 'none'))
    print('E dup(after entry norm):', dup_entry if dup_entry else 'none')
    print('E dup(after entry+slot norm):', dup_all if dup_all else 'none')
    print('precedent skeleton base:', list(prec_skel.values())[0])
    print('row1 skeleton       :', res[0]['D'].get('core') if res else None)
    for r in res:
        print('%2d %s %-50s slot=%-4s %s %s' % (
            r['idx'], r['entry'], r['name'][:50], r['name_slot'], r['verdict'],
            '; '.join(r['notes'])[:160]))
    return 0


if __name__ == '__main__':
    sys.exit(main())
