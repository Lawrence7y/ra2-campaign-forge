#!/usr/bin/env python3
"""R107: CFG recursive descent over .text with per-instruction function-root tagging.

Seeds : PE entry point, every byte-scanned `E8 rel32` call target landing in .text, and every
        padding boundary (first byte after a run of 0xCC or of 0x90) - MSVC pads function
        entries that way.
Descends with capstone (detail=False, one instruction at a time; no object lists retained).
Outputs (all under _r107/_exec/):
  cfg.bin      u32 size + reach bitmap (1 byte per .text byte)
  func_of.bin  u32 size + int32 per .text byte: root VA of the descent that first reached the
               instruction starting there (0 = not an instruction start)
  cfg_jt.json  jump tables found (holding insn / table VA / entry count / targets)
  reach_stats.json

Run: python3 _r107/_exec/cfg.py      (~100 s)
"""
import sys, os, re, json, struct
from array import array
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from r107_lib import DATA, TEXT, TEXT_VA, TEXT_END, va2off, off2va, IMAGEBASE, PE

from capstone import Cs, CS_ARCH_X86, CS_MODE_32

HERE = os.path.dirname(os.path.abspath(__file__))
SIZE = TEXT_END - TEXT_VA
MD = Cs(CS_ARCH_X86, CS_MODE_32)
MD.detail = False

RE_IMM = re.compile(r'^0x([0-9a-f]+)$')
RE_JT = re.compile(r'^(?:dword ptr )?\[(e[a-d]x|e[sd]i|e[bp]p|e[sd]p)\*4 \+ (0x[0-9a-f]+)\]$')


def decode1(va):
    for ins in MD.disasm(DATA[va2off(va):va2off(va) + 15], va):
        if ins.address == va:
            return ins
        return None
    return None


def text_ok(va, n=1):
    return TEXT_VA <= va < TEXT_END - n


def seeds():
    out = set()
    out.add(IMAGEBASE + PE.OPTIONAL_HEADER.AddressOfEntryPoint)
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
        if text_ok(t):
            out.add(t)
    # function-boundary padding: byte after a run of 0xCC, or after a 0x90 fill that directly
    # follows an unconditional terminator (ret / ret imm16 / jmp rel / int3).
    i = base
    while i < base + SIZE - 1:
        b = DATA[i]
        if b == 0xCC:
            j = i
            while j < base + SIZE and DATA[j] == b:
                j += 1
            out.add(off2va(j))
            i = j
        elif b == 0x90:
            j = i
            while j < base + SIZE and DATA[j] == b:
                j += 1
            if preceded_by_terminator(i):
                out.add(off2va(j))
            i = j
        else:
            i += 1
    return out


def preceded_by_terminator(i):
    """True if the bytes ending right before file offset `i` are an unconditional control
    transfer (ret / ret imm16 / jmp rel8 / jmp rel32 / int3), so an 0x90 run starting at `i`
    is padding rather than code."""
    if i < 1:
        return False
    if DATA[i - 1] in (0xC3, 0xCB, 0xE9, 0xEB, 0xCC):
        return True
    if i >= 3 and DATA[i - 3] == 0xC2:      # C2 imm16
        return True
    return False


def descend(seed_list):
    reach = bytearray(SIZE)
    fof = array('i', bytes(4 * SIZE))
    jt = {}
    work = [(a, a) for a in seed_list]
    while work:
        a, root = work.pop()
        cur = a
        while True:
            if not text_ok(cur) or reach[cur - TEXT_VA]:
                break
            ins = decode1(cur)
            if ins is None:
                break
            reach[cur - TEXT_VA] = 1
            fof[cur - TEXT_VA] = root
            mn, op = ins.mnemonic, ins.op_str
            nxt = ins.address + ins.size
            if mn == 'call':
                m = RE_IMM.match(op)
                if m:
                    t = int(m.group(1), 16)
                    if text_ok(t):
                        work.append((t, t))
                work.append((nxt, root))
                break
            if mn == 'jmp':
                m = RE_JT.match(op)
                if m:
                    basev = int(m.group(2), 16)
                    targets = []
                    for k in range(400):
                        o = va2off(basev) + 4 * k
                        v = struct.unpack('<I', DATA[o:o + 4])[0]
                        if not text_ok(v):
                            break
                        targets.append(v)
                    jt[cur] = {'ins': cur, 'slot_reg': m.group(1), 'table': basev,
                               'targets': targets}
                    for t in targets:
                        work.append((t, root))
                    break
                m = RE_IMM.match(op)
                if m:
                    work.append((int(m.group(1), 16), root))
                break
            if mn.startswith('j') and len(mn) > 1:
                m = RE_IMM.match(op)
                if m:
                    work.append((int(m.group(1), 16), root))
                cur = nxt
                continue
            if mn in ('ret', 'retn', 'iretd', 'hlt', 'int3'):
                break
            cur = nxt
    return reach, fof, jt


if __name__ == '__main__':
    S = seeds()
    print('seeds=%d' % len(S))
    reach, fof, jt = descend(S)
    with open(os.path.join(HERE, 'cfg.bin'), 'wb') as f:
        f.write(SIZE.to_bytes(4, 'little'))
        f.write(bytes(reach))
    with open(os.path.join(HERE, 'func_of.bin'), 'wb') as f:
        f.write(SIZE.to_bytes(4, 'little'))
        fof.tofile(f)
    jtout = [{'ins': hex(a), 'table': hex(d['table']), 'n': len(d['targets']),
              'targets': [hex(x) for x in d['targets']]} for a, d in sorted(jt.items())]
    json.dump(jtout, open(os.path.join(HERE, 'cfg_jt.json'), 'w'), indent=1)
    json.dump({'entrypoint': hex(IMAGEBASE + PE.OPTIONAL_HEADER.AddressOfEntryPoint),
               'seeds': len(S), 'reach_insns': sum(reach), 'jumptables': len(jt)},
              open(os.path.join(HERE, 'reach_stats.json'), 'w'), indent=1)
    print('reach_insns=%d jumptables=%d' % (sum(reach), len(jt)))
    for t in (0x4c6ccd, 0x69af2c, 0x6a8e0c, 0x6dd8da, 0x708c44, 0x728c0d, 0x728e62):
        print('dec %08x reached=%d func=%08x' % (t, reach[t - TEXT_VA], fof[t - TEXT_VA]))
