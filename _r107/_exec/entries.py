#!/usr/bin/env python3
"""R107: containing-function entry for each DEC switch site, by forward-decode validation.

The .text section embeds read-only jump tables, so a byte-linear sweep is not a sound
instruction-start oracle; recursive descent alone also misses functions only reached through
vtables. So each site is resolved this way:

  candidate entry b  :=  b in [site-0x8000, site) and the byte before b is 0xCC or 0x90
  b is validated      :=  a forward linear decode STARTING AT b reaches address == site
                          (generator is abandoned as soon as the address passes the site)

Every validated candidate is reported with its evidence (CC padding / E8 call target /
its 4-byte VA present as a word in .rdata or .data, i.e. a vtable slot) and its first bytes,
so ambiguity stays visible in the report.

Run: python3 _r107/_exec/entries.py    -> _r107/_exec/entries.json
"""
import sys, os, json, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from r107_lib import DATA, TEXT, TEXT_VA, TEXT_END, va2off, off2va, IMAGEBASE, _S

from capstone import Cs, CS_ARCH_X86, CS_MODE_32

HERE = os.path.dirname(os.path.abspath(__file__))
SIZE = TEXT_END - TEXT_VA
TABS = [(0x4c8114, 46, 0x4c6ccd), (0x69b15c, 4, 0x69af2c), (0x6a92c4, 3, 0x6a8e0c),
        (0x6dfdec, 145, 0x6dd8da), (0x708d54, 5, 0x708c44), (0x728e08, 7, 0x728c0d),
        (0x7291ac, 7, 0x728e62)]
WINDOW = 0x8000
MD = Cs(CS_ARCH_X86, CS_MODE_32)
MD.detail = False


def reaches(src, dst):
    """does a linear decode from src hit address dst before passing it?"""
    code = DATA[va2off(src):va2off(src) + (dst - src) + 16]
    for x in MD.disasm(code, src):
        if x.address == dst:
            return True
        if x.address > dst:
            return False
    return False


def call_targets():
    out = set()
    base = va2off(TEXT_VA)
    end = base + SIZE - 5
    off = base
    while True:
        i = DATA.find(b'\xe8', off, end)
        if i < 0:
            break
        off = i + 1
        rel = struct.unpack_from('<i', DATA, i + 1)[0]
        t = off2va(i) + 5 + rel
        if TEXT_VA <= t < TEXT_END:
            out.add(t)
    return out


CALLS = call_targets()


def data_words():
    w = set()
    for nm in ('.rdata', '.data'):
        s = _S[nm]
        raw = DATA[s.PointerToRawData:s.PointerToRawData + s.SizeOfRawData]
        for i in range(0, len(raw) - 3, 4):
            w.add(struct.unpack_from('<I', raw, i)[0])
    return w


WORDS = data_words()


def evidence(b):
    ev = []
    prev = DATA[va2off(b) - 1]
    if prev == 0xCC:
        ev.append('CC-padding')
    elif prev == 0x90:
        ev.append('NOP-padding')
    if b in CALLS:
        ev.append('E8-call-target')
    if b in WORDS:
        ev.append('VA-is-a-word-in-.rdata/.data')
    return ev


def candidates(site, window=WINDOW):
    out = []
    for b in range(max(TEXT_VA + 1, site - window), site):
        if DATA[va2off(b) - 1] not in (0xCC, 0x90):
            continue
        if reaches(b, site):
            out.append(b)
    return out


if __name__ == '__main__':
    out = {}
    for base, n, dec in TABS:
        cs = candidates(dec)
        recs = [{'entry': hex(b), 'evidence': evidence(b),
                 'first16': DATA[va2off(b):va2off(b) + 16].hex()} for b in cs]
        out['%x' % base] = {'table': hex(base), 'n': n, 'dec': hex(dec), 'candidates': recs}
        print('%08x dec=%08x validated_candidates=%d' % (base, dec, len(cs)))
        for r in recs:
            print('    %s  %-40s %s' % (r['entry'], ','.join(r['evidence']), r['first16']))
    json.dump(out, open(os.path.join(HERE, 'entries.json'), 'w'), indent=1)
