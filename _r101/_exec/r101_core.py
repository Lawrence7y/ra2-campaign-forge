#!/usr/bin/env python3
"""R101-T1 exec: independently rebuild the 88 non-elided capstone-only starts and answer A/B/C.
Read-only inputs: /tmp/r93_disasm.txt, ra2bench/gamemd.exe, _r100/*.json (data only, never executed).
Outputs: r101_core.json in this directory. No writes outside this directory.
"""
import os, re, json, hashlib, random, statistics, struct
from collections import Counter, defaultdict
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
import pefile

ROOT = '/home/t628/projects/ra2-campaign-forge'
OUT = os.path.dirname(os.path.abspath(__file__))
DIS = '/tmp/r93_disasm.txt'
EXE = os.path.join(ROOT, 'ra2bench/gamemd.exe')
R100 = os.path.join(ROOT, '_r100')

def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()

def load_text():
    """Parse objdump text into instruction lines, wrap/continuation lines, elide lines."""
    ins = {}           # addr -> (bytes, text, rawlen)
    order = []
    wraps = 0
    elides = []
    with open(DIS, 'r', encoding='utf-8', errors='replace') as f:
        for line in f:
            if not line.startswith('  ') and not line.startswith('\t'):
                continue
            parts = line.rstrip('\n').split('\t')
            if len(parts) < 2:
                continue
            m = re.match(r'^\s*([0-9a-f]+):$', parts[0])
            if not m:
                continue
            a = int(m.group(1), 16)
            if line.strip() == '...':
                elides.append('bare')
                continue
            bs = parts[1].strip() if len(parts) > 1 else ''
            if bs == '...':
                elides.append(a)
                continue
            if len(parts) < 3:
                wraps += 1
                continue
            raw = bytes.fromhex(bs)
            if a in ins:
                raise ValueError('duplicate instruction line at %x' % a)
            ins[a] = (raw, parts[2].strip(), len(raw))
            order.append(a)
    return ins, order, wraps, elides

def load_pe():
    pe = pefile.PE(EXE, fast_load=True)
    sec = next(s for s in pe.sections if s.Name.rstrip(b'\x00') == b'.text')
    base = pe.OPTIONAL_HEADER.ImageBase + sec.VirtualAddress
    end = base + sec.Misc_VirtualSize
    raw = sec.PointerToRawData
    with open(EXE, 'rb') as f:
        f.seek(raw)
        code = f.read(sec.SizeOfRawData)
    def va2off(va):
        return raw + (va - base)
    # all sections, for A3 DWORD scan
    secs = []
    for s in pe.sections:
        secs.append((pe.OPTIONAL_HEADER.ImageBase + s.VirtualAddress,
                     s.Misc_VirtualSize, s.PointerToRawData, s.SizeOfRawData,
                     s.Name.rstrip(b'\x00').decode('ascii', 'replace')))
    return base, end, code, va2off, secs, pe.OPTIONAL_HEADER.ImageBase

def cap_linear(base, end, code):
    """Streaming linear sweep: capstone detail=False, never materialize all units."""
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = False
    ok = set(); bad = []
    n = len(code)
    i = 0
    while i < n:
        va = base + i
        if va >= end:
            break
        insn = next(md.disasm(code[i:i+15], va, count=1), None)
        if insn is None:
            bad.append(va)
            i += 1
        else:
            ok.add(va)
            i += insn.size
    return ok, bad

def build_refs(ins, order, base, end, code, va2off, secs, imagebase):
    """A1/A2 from printed instruction lines; A3 from non-.text aligned DWORDs."""
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = False
    jmps = set(); imm = set()
    # A1: control-flow immediate targets; A2: any immediate operand resembling .text VA.
    # objdump textual parsing is used instead of capstone detail so we see all printed lines.
    jmnem = re.compile(r'^(?:j[a-z]+|call|loop[a-z]*)\b', re.I)
    # hex literal in operand text; objdump prints absolute .text targets as 0x7xxxxx
    hexlit = re.compile(r'0x([0-9a-f]{4,8})\b', re.I)
    for a in order:
        raw, txt, _ = ins[a]
        m = jmnem.match(txt)
        for h in hexlit.findall(txt):
            v = int(h, 16)
            if base <= v < end:
                imm.add(v)
                if m:
                    jmps.add(v)
    # A3: non-.text sections, 4-byte aligned reads
    dwords = set()
    with open(EXE, 'rb') as f:
        for va, vsize, rawptr, rawsize, name in secs:
            if name == '.text':
                continue
            n = min(vsize, rawsize) // 4 * 4
            f.seek(rawptr)
            buf = f.read(n)
            for off in range(0, len(buf), 4):
                v = struct.unpack_from('<I', buf, off)[0]
                if base <= v < end:
                    dwords.add(v)
    return jmps, imm, dwords

def main():
    ins, order, wraps, elides = load_text()
    base, end, code, va2off, secs, imagebase = load_pe()
    cap_ok, cap_bad = cap_linear(base, end, code)
    starts = set(order)
    only_cap = sorted(cap_ok - starts)
    # classify elided membership from _r100 data (read-only JSON)
    el = json.load(open(os.path.join(R100, 'r100a_elide.json')))
    elided_spans = [(int(x['at'], 16), int(x['to'], 16)) for x in el['elided_bytes']]
    def in_elided(a):
        return any(lo <= a < hi for lo, hi in elided_spans)
    only_cap_ne = [a for a in only_cap if not in_elided(a)]
    jmps, imm, dwords = build_refs(ins, order, base, end, code, va2off, secs, imagebase)
    union = jmps | imm | dwords
    # host lookup: preceding printed instruction line
    # host = last printed instruction whose [a, a+truelen) contains the address.
    # truelen is derived from the printed byte-count field (not the display width).
    host = {}
    sorted_starts = order  # already ascending
    import bisect
    for a in only_cap_ne:
        idx = bisect.bisect_right(sorted_starts, a) - 1
        h = sorted_starts[idx] if idx >= 0 else None
        host[a] = h
    result = {
        'sha_dis': sha256(DIS), 'sha_exe': sha256(EXE),
        'base': hex(base), 'end': hex(end),
        'printed': len(order), 'wraps': wraps, 'elides': elides,
        'cap_ok': len(cap_ok), 'cap_bad': len(cap_bad),
        'only_cap': len(only_cap), 'only_cap_elided': len(only_cap) - len(only_cap_ne),
        'only_cap_ne': len(only_cap_ne),
        'ref_sizes': {'A1_jmp': len(jmps), 'A2_imm': len(imm), 'A3_dword': len(dwords), 'union': len(union)},
        'hit88': {
            'A1': sum(a in jmps for a in only_cap_ne),
            'A2': sum(a in imm for a in only_cap_ne),
            'A3': sum(a in dwords for a in only_cap_ne),
            'union': sum(a in union for a in only_cap_ne),
        },
        'hit_all_starts_jmp': sum(a in jmps for a in starts),
        'nc2_capbad_jmp': [hex(a) for a in cap_bad if a in jmps],
        'only_cap_ne_list': [hex(a) for a in only_cap_ne],
        'cap_bad_list': [hex(a) for a in cap_bad],
        'host_of_88': {hex(a): hex(host.get(a, 0)) for a in only_cap_ne},
        'host_len_dist': dict(sorted(Counter(ins[host[a]][2] for a in only_cap_ne if a in host).items())),
        'elided_spans': [[hex(lo), hex(hi)] for lo, hi in elided_spans],
    }
    json.dump(result, open(os.path.join(OUT, 'r101_core.json'), 'w'), indent=2)
    print(json.dumps({k: v for k, v in result.items() if k not in ('only_cap_ne_list', 'cap_bad_list', 'host_of_88', 'union_list_sample')}, indent=2))

if __name__ == '__main__':
    main()
