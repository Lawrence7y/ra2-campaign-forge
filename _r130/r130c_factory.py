#!/usr/bin/env python3
# R130 r130c: is 0x7f3710 the ONLY class-factory table of its kind?
#
# R129 proved the loop at 0x6bc34d walks exactly one entry {CLSID 0x7e9500, "blowfish.dll"}
# and calls the wrapper 0x6bedb0 (CoCreateInstance + OleRun + call[ecx] + call[edx+8]).
# R129's open question: why only ONE entry -- is there a SECOND table of the same kind,
# i.e. another loop that feeds the SAME wrapper 0x6bedb0?
#
# Method (byte facts only):
#   (a) find every call whose target is 0x6bedb0            -> call sites
#   (b) for each call site, find the enclosing function and the table-iteration loop
#       (per r130b's census) whose body contains it          -> which loops feed it
#   (c) for a feeding loop, recover the table head from the hoisted mov and
#       walk the entries to read (CLSID ptr, DLL name ptr) pairs
# Control: the known 0x6bc34d loop must be recovered, and a call to a DIFFERENT
#   wrapper (0x6c61c0, the local-var cleanup, which sits in the same function) must
#   NOT be counted as a wrapper call.
# Memory: disasm_lite streaming, bounded history, no detail=True.
import collections
import io
import json
import re
import sys

import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = '/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe'
OUT = '/home/t628/projects/ra2-campaign-forge/_r130/r130c_factory.json'
TDATA = '/home/t628/projects/ra2-campaign-forge/_r130/r130b_tables.json'

WRAPPER = 0x6bedb0
LOOKBACK = 0x1000
MAX_BODY = 0x800
_IMMRE = re.compile(r'^(0[xX][0-9a-fA-F]+|\d+)$')


def imm(op):
    s = op.strip()
    if not _IMMRE.match(s):
        return None
    return int(s, 16) if s[:2].lower() == '0x' else int(s, 10)


def load_pe():
    pe = pefile.PE(EXE, fast_load=True)
    base = pe.OPTIONAL_HEADER.ImageBase
    secs, text = {}, None
    for s in pe.sections:
        nm = s.Name.rstrip(b'\x00').decode('latin-1')
        lo = base + s.VirtualAddress
        secs[nm] = (lo, lo + max(s.Misc_VirtualSize, s.SizeOfRawData), s)
        if nm == '.text':
            text = (lo, s.get_data())
    return pe, secs, text


def read_ptr(data, text_va, secs, va, size=4):
    """Read `size` bytes at virtual address va, or None if not raw-backed."""
    for nm, (lo, hi, s) in secs.items():
        if lo <= va < hi:
            off = va - (pe_base + s.VirtualAddress)
            raw = s.SizeOfRawData
            if off < 0 or off + size > raw or off >= len(s.get_data()):
                return None       # in BSS / not backed by file bytes
            d = s.get_data()
            return d[off:off + size]
    return None


pe_base = 0


def cstr(data, text_va, secs, va, limit=128):
    b = read_ptr(data, text_va, secs, va, limit)
    if b is None:
        return None
    z = b.find(b'\x00')
    if z <= 0:
        return None
    try:
        s = b[:z].decode('ascii')
    except UnicodeDecodeError:
        return None
    return s if all(32 <= ord(c) < 127 for c in s) else None


def main():
    global pe_base
    pe, secs, (text_va, data) = load_pe()
    pe_base = pe.OPTIONAL_HEADER.ImageBase

    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = False
    md.skipdata = True

    # (a) call sites of the wrapper
    calls = []
    n_insn = 0
    for addr, size, mnem, op in md.disasm_lite(data, text_va):
        n_insn += 1
        if mnem == 'call':
            t = imm(op)
            if t == WRAPPER:
                calls.append(addr)

    # (b) which census loops contain a wrapper call
    cen = json.load(io.open(TDATA, encoding='utf-8'))
    loops = []
    for h in cen['hits']:
        lh, be = int(h['loop_head'], 16), int(h['back_edge'], 16)
        inside = [c for c in calls if lh <= c <= be]
        loops.append({'head': h['table_head'], 'bound': h['bound'],
                      'step': h['step'], 'count': h['count'],
                      'loop_head': h['loop_head'], 'back_edge': h['back_edge'],
                      'wrapper_calls': [hex(c) for c in inside]})

    feeding = [l for l in loops if l['wrapper_calls']]

    # (c) walk entries of each feeding table
    for l in feeding:
        hv = int(l['head'], 16)
        bv = int(l['bound'], 16)
        step = l['step']
        ents = []
        va = hv
        while va < bv:
            clsid_b = read_ptr(data, text_va, secs, va, 4)
            dll_b = read_ptr(data, text_va, secs, va + 4, 4) if step >= 8 else None
            e = {'at': hex(va)}
            e['rclsid_ptr'] = hex(int.from_bytes(clsid_b, 'little')) if clsid_b else None
            e['dll_ptr'] = hex(int.from_bytes(dll_b, 'little')) if dll_b else None
            if e['rclsid_ptr']:
                g = read_ptr(data, text_va, secs, int(e['rclsid_ptr'], 16), 16)
                e['guid_bytes'] = g.hex() if g else None
            if e['dll_ptr']:
                e['dll_name'] = cstr(data, text_va, secs, int(e['dll_ptr'], 16))
            ents.append(e)
            va += step
        l['entries'] = ents

    rec = {
        'insn_count': n_insn,
        'wrapper_va': hex(WRAPPER),
        'wrapper_call_sites': [hex(c) for c in calls],
        'census_loops': len(loops),
        'feeding_loops': feeding,
    }
    # ---- controls ----
    rec['ctl_known_loop_feeds_wrapper'] = any(
        l['loop_head'] == '0x6bc34d' and l['head'] == '0x7f3710' for l in feeding)
    rec['ctl_known_table_has_1_entry'] = any(
        l['head'] == '0x7f3710' and l['count'] == 1 and
        l.get('entries', [{}])[0].get('dll_name') == 'blowfish.dll'
        for l in feeding)
    with io.open(OUT, 'w', encoding='utf-8') as f:
        json.dump(rec, f, ensure_ascii=False, indent=1)

    print('insn', n_insn, 'wrapper call sites', len(calls))
    for c in calls:
        print('  call at', hex(c))
    print('census loops', len(loops), 'feeding loops', len(feeding))
    for l in feeding:
        print('  loop', l['loop_head'], 'table', l['head'], '->', l['bound'],
              'step', l['step'], 'n', l['count'],
              'calls', l['wrapper_calls'])
        for e in l.get('entries', []):
            print('     ', e)
    print('ctl known loop feeds wrapper:', rec['ctl_known_loop_feeds_wrapper'])
    print('ctl known table 1 entry blowfish:', rec['ctl_known_table_has_1_entry'])
    ok = rec['ctl_known_loop_feeds_wrapper'] and rec['ctl_known_table_has_1_entry']
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
