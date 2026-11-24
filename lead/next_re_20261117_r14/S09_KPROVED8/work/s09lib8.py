#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Self-implemented RE helpers for S09-KPROVED8, from R14_COMMON documented algorithms
(RTTI chain COL->TD+8, CFG extent, full .text E8 sweep, ③b feature detection).
Read-only on target. Writes only inside S09_KPROVED8/work/ and EVIDENCE/.
"""
from __future__ import annotations
import struct, os
import pefile
from capstone import CS_ARCH_X86, CS_MODE_32, CS_OPT_SKIPDATA, CS_OPT_SKIPDATA_SETUP, Cs
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_OP_REG, X86_GRP_JUMP, X86_GRP_CALL

BASE = r'D:\Project\ra2-campaign-forge'
EXE = os.path.join(BASE, 'ra2youli', 'gamemd.exe')
IB = 0x400000
DATA = open(EXE, 'rb').read()
PE = pefile.PE(EXE, fast_load=True)

SECS = []
for s in PE.sections:
    SECS.append(dict(name=s.Name.rstrip(b'\0').decode('ascii', 'replace'),
                     va=IB + s.VirtualAddress, vsize=s.Misc_VirtualSize,
                     raw=s.PointerToRawData, rsize=s.SizeOfRawData))
TEXT = next(s for s in SECS if s['name'] == '.text')
TEXT_LO, TEXT_HI = TEXT['va'], TEXT['va'] + TEXT['vsize']

MD = Cs(CS_ARCH_X86, CS_MODE_32)
MD.detail = True
MD.skipdata = True
SKIPDATA_SETUP = Cs(CS_ARCH_X86, CS_MODE_32)
SKIPDATA_SETUP.detail = True
SKIPDATA_SETUP.skipdata = True


def va_off(va):
    if va is None:
        return None
    for s in SECS:
        if s['va'] <= va < s['va'] + max(s['vsize'], s['rsize']):
            o = s['raw'] + (va - s['va'])
            if 0 <= o < min(s['raw'] + s['rsize'], len(DATA)):
                return o
    return None


def sec_of(va):
    for s in SECS:
        if s['va'] <= va < s['va'] + max(s['vsize'], s['rsize']):
            return s['name']
    return None


def u32(va):
    o = va_off(va)
    if o is None or o + 4 > len(DATA):
        return None
    return struct.unpack_from('<I', DATA, o)[0]


def i32(va):
    x = u32(va)
    return None if x is None else (x - 0x100000000 if x >= 0x80000000 else x)


def u8(va):
    o = va_off(va)
    return None if o is None else DATA[o]


def cstr(va, maxlen=200):
    o = va_off(va)
    if o is None:
        return None
    e = DATA.find(b'\0', o, min(o + maxlen, len(DATA)))
    if e < 0:
        return None
    try:
        return DATA[o:e].decode('ascii')
    except UnicodeDecodeError:
        return None


def is_text(va):
    return va is not None and TEXT_LO <= va < TEXT_HI


def is_ro(va):
    return sec_of(va) in ('.rdata', '.data')


def decode_one(va):
    o = va_off(va)
    if o is None:
        return None
    return next(MD.disasm(DATA[o:o + 16], va, count=1), None)


def decode_range(start, end):
    o = va_off(start)
    if o is None:
        return []
    size = min(end, TEXT_HI) - start
    if size <= 0:
        return []
    return list(MD.disasm(DATA[o:o + size], start))


def imm_ops(insn):
    return [op.imm for op in insn.operands if op.type == X86_OP_IMM]


def op_imm(insn):
    v = imm_ops(insn)
    return v[0] if v else None


def rtti_tables(max_slots=1024):
    """Enumerate every RTTI vtable: valid COL -> [vt-4]=COL -> TD=[COL+0xC] in ro,
    name=cstr(TD+8) starts .?AV/.?AU; then slot run from vt while value in .text."""
    valid = {}
    for s in SECS:
        if s['name'] not in ('.rdata', '.data', '.rsrc'):
            continue
        st, en = s['raw'], min(s['raw'] + s['rsize'], len(DATA))
        for o in range(st + (-st % 4), en - 4, 4):
            col = s['va'] + (o - st)
            td = u32(col + 0xC)
            if not td or not is_ro(td):
                continue
            nm = cstr(td + 8)
            if nm and (nm.startswith('.?AV') or nm.startswith('.?AU')):
                valid[col] = (td, nm)
    tables = []
    for s in SECS:
        if s['name'] not in ('.rdata', '.data', '.rsrc'):
            continue
        st, en = s['raw'], min(s['raw'] + s['rsize'], len(DATA))
        for o in range(st + (-st % 4), en - 4, 4):
            pa = s['va'] + (o - st)
            col = u32(pa)
            if col not in valid:
                continue
            td, nm = valid[col]
            vt = pa + 4
            slots = []
            for i in range(max_slots):
                v = u32(vt + 4 * i)
                if not is_text(v):
                    break
                slots.append(v)
            if slots:
                tables.append(dict(vt=vt, col=col, col_slot=pa, td=td, name=nm, slots=slots))
    return tables


def tables_holding(tables, entry):
    """All (table, slot_index) where slot value == entry."""
    hits = []
    for t in tables:
        for i, v in enumerate(t['slots']):
            if v == entry:
                hits.append((t, i))
    return hits


def cfg_extent(entry, cap=8000):
    """CFG extent from entry via all jump/call imm targets + fallthrough; no atlas dependency."""
    work, seen = [entry], {}
    while work and len(seen) < cap:
        va = work.pop()
        if va in seen or not is_text(va):
            continue
        ins = decode_one(va)
        if ins is None or ins.mnemonic == '.byte':
            continue
        seen[va] = ins
        nxt = va + ins.size
        if ins.mnemonic.startswith('ret'):
            continue
        if ins.group(X86_GRP_JUMP):
            for t in imm_ops(ins):
                if is_text(t):
                    work.append(t)
            if ins.mnemonic != 'jmp':
                work.append(nxt)
        elif ins.group(X86_GRP_CALL):
            work.append(nxt)
        else:
            work.append(nxt)
    if not seen:
        return entry, entry, [], {}
    lo = min(seen)
    hi = max(a + i.size for a, i in seen.items())
    ordered = [seen[a] for a in sorted(seen)]
    return lo, hi, ordered, seen


def full_e8_sweep():
    off = TEXT['raw']
    insns = list(MD.disasm(DATA[off:off + TEXT['vsize']], TEXT_LO))
    calls = []
    for ins in insns:
        if len(ins.bytes) >= 5 and ins.bytes[0] == 0xE8 and ins.mnemonic == 'call':
            t = op_imm(ins)
            if t is not None:
                calls.append(dict(site=ins.address, target=t,
                                  rel=struct.unpack_from('<i', ins.bytes, 1)[0],
                                  raw=ins.bytes.hex()))
    return insns, calls


def direct_sites_for(entry, calls, lo, hi):
    sites = []
    for c in calls:
        if c['target'] != entry:
            continue
        s = c['site']
        in_body = lo <= s < hi
        selfloop = (s == entry)
        sites.append({**c, 'in_body': in_body, 'selfloop': selfloop,
                      'ok': (not in_body) and not selfloop})
    return sites
