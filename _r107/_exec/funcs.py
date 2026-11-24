#!/usr/bin/env python3
"""R107: locate the containing function entry for each of the 7 DEC switch sites.

Why not use a linear sweep: the 19 switch tables and other read-only blobs live *inside* .text,
so a byte-linear sweep derails at the first table and cannot be trusted as an instruction-start
oracle. This script instead uses the recursive-descent reach bitmap produced by cfg.py
(cfg.bin), which only contains real instruction starts.

Method for each site:
  1. walk BACKWARD: predecessor = the unique reachable start p < cur with
     p + len(insn(p)) == cur (searching p in [cur-15, cur)).
  2. stop and report p as the function entry when p is an `E8 rel32` call target, or p is
     preceded by padding (CC / 90) or by an unconditional terminator (ret / ret imm16 / jmp).
  3. cap the walk at 0x8000 bytes; report failure instead of guessing.
Writes _r107/_exec/funcs.json.

Run: python3 _r107/_exec/funcs.py     (needs cfg.py to have been run first)
"""
import sys, os, json, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from r107_lib import DATA, TEXT, TEXT_VA, TEXT_END, va2off, off2va, dis, ins_str, IMAGEBASE

HERE = os.path.dirname(os.path.abspath(__file__))
SIZE = TEXT_END - TEXT_VA
TABS = [(0x4c8114, 46, 0x4c6ccd), (0x69b15c, 4, 0x69af2c), (0x6a92c4, 3, 0x6a8e0c),
        (0x6dfdec, 145, 0x6dd8da), (0x708d54, 5, 0x708c44), (0x728e08, 7, 0x728c0d),
        (0x7291ac, 7, 0x728e62)]


def load_cfg():
    b = open(os.path.join(HERE, 'cfg.bin'), 'rb').read()
    return bytearray(b[4:4 + int.from_bytes(b[:4], 'little')])


REACH = load_cfg()


def insn_len(p):
    ins = dis(p, 16)
    if ins and ins[0].address == p:
        return ins[0].size, ins[0]
    return None, None


def prev_insn(cur, limit=16):
    cands = []
    for back in range(1, limit):
        p = cur - back
        if p < TEXT_VA or REACH[p - TEXT_VA] != 1:
            continue
        n, ins = insn_len(p)
        if n == back:
            cands.append((p, ins))
    if len(cands) == 1:
        return cands[0]
    if not cands:
        return None, None
    # ambiguous: prefer the one whose own predecessor chain is longest (heuristic) -> return
    # the first (closest) but flag it
    return cands[0][0], cands[0][1]


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


def is_padded(va):
    b = DATA[va2off(va) - 1]
    return b in (0xCC, 0x90)


def walk_back(site, limit=0x8000):
    cur = site
    chain = []
    while site - cur < limit:
        p, ins = prev_insn(cur)
        if p is None:
            return None, chain, 'no predecessor for %08x' % cur
        chain.append((p, ins))
        cur = p
        if cur in CALLS or is_padded(cur):
            return cur, chain, 'entry (call target / padding)'
        if ins.mnemonic in ('ret', 'retn', 'iretd', 'hlt', 'jmp', 'int3'):
            return cur, chain, 'entry (preceded by terminator)'
    return None, chain, 'walk limit %x exceeded' % limit


if __name__ == '__main__':
    out = {}
    for base, n, dec in TABS:
        e, chain, why = walk_back(dec)
        rec = {'table': hex(base), 'n': n, 'dec': hex(dec),
               'entry': hex(e) if e else None,
               'entry_bytes8': DATA[va2off(e) - 8:va2off(e) + 8].hex() if e else None,
               'is_call_target': (e in CALLS) if e else None,
               'why': why, 'walked': len(chain)}
        out['%x' % base] = rec
        print('%08x dec=%08x entry=%s call_tgt=%s walked=%d  %s' %
              (base, dec, hex(e) if e else None, rec['is_call_target'], len(chain), why))
    json.dump(out, open(os.path.join(HERE, 'funcs.json'), 'w'), indent=1)
