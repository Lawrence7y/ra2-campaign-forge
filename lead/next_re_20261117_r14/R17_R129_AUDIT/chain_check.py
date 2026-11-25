#!/usr/bin/env python3
# R129 auditor consolidated verification: CLSID -> class object -> class name chain.
# Reproduces every number quoted in R129-AUDIT-deepseek.md.
# Rules honoured: streaming disasm_lite only, skipdata=True, no detail=True objects,
# no full-instruction-list residency, no backtick characters in output.
import struct, re, hashlib, sys
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = '/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe'
IB  = 0x400000
EXPECT_SHA = '73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476'

pe = pefile.PE(EXE, fast_load=False)
D  = bytes(pe.__data__)
MD = Cs(CS_ARCH_X86, CS_MODE_32); MD.skipdata = True

def sec_of(va):
    rva = va - IB
    for s in pe.sections:
        if s.VirtualAddress <= rva < s.VirtualAddress + max(s.Misc_VirtualSize, s.SizeOfRawData):
            return s, rva - s.VirtualAddress
    return None, None

def roff(va):
    s, d = sec_of(va)
    if s is None or d >= s.SizeOfRawData:
        return None
    return s.PointerToRawData + d

def rd(va, n):
    o = roff(va)
    return None if o is None else D[o:o + n]

def u32(va):
    b = rd(va, 4)
    return None if b is None else struct.unpack('<I', b)[0]

def cstr(va, n=200):
    b = rd(va, n)
    if b is None:
        return None
    z = b.find(b'\0')
    return b[:z] if z >= 0 else b

def dis(a, b):
    o = roff(a)
    data = D[o:o + (b - a)]
    for ad, sz, m, op in MD.disasm_lite(data, a):
        yield ad, sz, m, op, D[roff(ad):roff(ad) + sz].hex()

def import_of(iat_va):
    for d in pe.DIRECTORY_ENTRY_IMPORT:
        for i in d.imports:
            if i.address == iat_va:
                return d.dll.decode(), (i.name.decode() if i.name else 'ordinal %d' % i.ordinal), i.ordinal
    return None, None, None

def is_msvc_vtable_head(imm):
    """imm-4 must hold a plausible Complete Object Locator and its TypeDescriptor name must start .?A"""
    if not (0x7e1000 <= imm < 0x812000):
        return False
    col = u32(imm - 4)
    if col is None:
        return False
    o = roff(col)
    if o is None:
        return False
    sig, offc, cd, ptd, pchd = struct.unpack('<IIIII', D[o:o + 20])
    if sig != 0 or offc != 0 or cd != 0:
        return False
    nm = cstr(ptd + 8)
    return bool(nm and nm.startswith(b'.?A'))

def rtti(vt):
    col = u32(vt - 4)
    sig, offc, cd, ptd, pchd = struct.unpack('<IIIII', rd(col, 20))
    csig, cattr, nbase, pbca = struct.unpack('<IIII', rd(pchd, 16))
    rows = []
    for i in range(nbase):
        bcd = u32(pbca + i * 4)
        ptd2, ncb, mdisp, pdisp, vdisp, attr = struct.unpack('<IIiiiI', rd(bcd, 24))
        rows.append((bcd, cstr(ptd2 + 8), ncb, mdisp, pdisp, vdisp, attr))
    return dict(col=col, sig=sig, offc=offc, cd=cd, ptd=ptd, name=cstr(ptd + 8),
                chd=pchd, nbase=nbase, bca=pbca, rows=rows)

def text_section():
    return [s for s in pe.sections if s.Name.rstrip(b'\0') == b'.text'][0]

def guid(b):
    return '{%08X-%04X-%04X-%s-%s}' % (struct.unpack_from('<I', b, 0)[0],
                                       struct.unpack_from('<H', b, 4)[0],
                                       struct.unpack_from('<H', b, 6)[0],
                                       b[8:10].hex().upper(), b[10:16].hex().upper())

def raw_dword_hits(val):
    pat = struct.pack('<I', val)
    out = []
    for s in pe.sections:
        b = D[s.PointerToRawData:s.PointerToRawData + s.SizeOfRawData]
        i = 0
        while True:
            i = b.find(pat, i)
            if i < 0:
                break
            out.append((s.Name.rstrip(b'\0').decode(), IB + s.VirtualAddress + i))
            i += 1
    return out

def main():
    print('== ENV')
    sha = hashlib.sha256(D).hexdigest()
    print('sha256', sha, 'match', sha == EXPECT_SHA)
    print('ImageBase', hex(pe.OPTIONAL_HEADER.ImageBase), 'SizeOfImage', hex(pe.OPTIONAL_HEADER.SizeOfImage))
    for s in pe.sections:
        print('  %-8s VA %08x VSize %08x RawPtr %08x RawSize %08x' %
              (s.Name.rstrip(b'\0').decode(), s.VirtualAddress, s.Misc_VirtualSize,
               s.PointerToRawData, s.SizeOfRawData))

    print()
    print('== SEG1 0x6bc425..0x6bc447')
    for ad, sz, m, op, hx in dis(0x6bc425, 0x6bc447):
        print('  %08x %-16s %-32s %s' % (ad, hx, m + ' ' + op, ''))
    dll, nm, ordn = import_of(0x7e15d8)
    print('  IAT 0x7e15d8 =', dll, nm, 'ordinal', ordn)
    for iat in (0x7e15d4, 0x7e15dc):
        print('  neighbour IAT', hex(iat), import_of(iat)[:2])
    print('  rclsid string at 0x7e9520:', guid(rd(0x7e9520, 16)))

    print()
    print('== SEG2')
    s = text_section()
    ownd = 0x412000
    print('  0xa8e8c8 section offset in .data:', hex(0xa8e8c8 - IB - ownd),
          ' SizeOfRawData:', hex([x for x in pe.sections if x.Name.rstrip(b'\0') == b'.data'][0].SizeOfRawData),
          ' VirtualSize:', hex([x for x in pe.sections if x.Name.rstrip(b'\0') == b'.data'][0].Misc_VirtualSize))
    hits = raw_dword_hits(0xa8e8c8)
    print('  raw dword occurrences of 0x00a8e8c8 in whole image:', len(hits), hits)
    base = IB + s.VirtualAddress
    data = D[s.PointerToRawData:s.PointerToRawData + s.SizeOfRawData]
    dec = []
    for a, sz, m, op in MD.disasm_lite(data, base):
        t = m + ' ' + op
        if re.search(r'(?<![0-9a-fA-F])0xa8e8c8(?![0-9a-fA-F])', t):
            dec.append((a, t, data[a - base:a - base + sz].hex()))
    print('  decoded .text sites mentioning 0xa8e8c8:', len(dec))
    for a, t, hx in dec:
        print('    %08x %-40s %s' % (a, hx, t))

    print()
    print('== SEG3 RTTI of the immediate written into 0xa8e8c8')
    imm = u32_or_scan = None
    for a, t, hx in dec:
        mm = re.match(r'^mov dword ptr \[0xa8e8c8\], (0x[0-9a-f]+)$', t)
        if mm:
            imm = int(mm.group(1), 16)
            print('  vptr write site %08x stores imm 0x%08x' % (a, imm))
    r = rtti(imm)
    print('  COL at', hex(r['col']), ' signature', r['sig'], 'offset', r['offc'], 'cdOffset', r['cd'])
    print('  pTypeDescriptor', hex(r['ptd']), 'name', r['name'])
    print('  pClassDescriptor', hex(r['chd']), 'numBaseClasses', r['nbase'], 'pBaseClassArray', hex(r['bca']))
    for bcd, nm2, ncb, mdisp, pdisp, vdisp, attr in r['rows']:
        print('    BCD %08x %-34r ncb=%d mdisp=%d pdisp=%d vdisp=%d attr=%08x' %
              (bcd, nm2, ncb, mdisp, pdisp, vdisp, attr))

    print()
    print('== SEG4')
    xr = raw_dword_hits(0x7e9520)
    print('  raw dword occurrences of 0x007e9520 in whole image:', len(xr), xr)
    for a, t, hx in [(a, m + ' ' + op, data[a - base:a - base + sz].hex())
                     for a, sz, m, op in MD.disasm_lite(data, base)
                     if re.search(r'(?<![0-9a-fA-F])0x7e9520(?![0-9a-fA-F])', m + ' ' + op)]:
        print('    %08x %-16s %s' % (a, hx, t))
    print('  ebx definition:')
    for ad, sz, m, op, hx in dis(0x6bd6b1, 0x6bd6d0):
        print('    %08x %-16s %s' % (ad, hx, m + ' ' + op))
    dll, nm, ordn = import_of(0x7e1370)
    print('  IAT 0x7e1370 =', dll, nm, 'ordinal', ordn)
    print('  four pushes before 0x6bd945 call ebx:')
    for ad, sz, m, op, hx in dis(0x6bd934, 0x6bd947):
        print('    %08x %-16s %s' % (ad, hx, m + ' ' + op))

    print()
    print('== CONTROL 1 adjacent .rdata GUIDs around rclsid')
    for va in (0x7e94f0, 0x7e9500, 0x7e9510, 0x7e9520, 0x7e9530, 0x7e9540):
        b = rd(va, 16)
        diff = [i for i in range(16) if b[i] != rd(0x7e9520, 16)[i]]
        print('  %08x %s  differing byte offsets vs 0x7e9520: %s' % (va, guid(b), diff))

    print()
    print('== CONTROL 2 relaxed criterion: any mov dword ptr [abs], imm32 in .text')
    mab = []
    for a, sz, m, op in MD.disasm_lite(data, base):
        if m == 'mov':
            mm = re.match(r'^dword ptr \[(0x[0-9a-f]+)\], (0x[0-9a-f]+)$', op)
            if mm:
                mab.append((a, int(mm.group(1), 16), int(mm.group(2), 16)))
    print('  decoded mov [abs],imm32 sites:', len(mab))
    print('  distinct target addresses:', len(set(t for a, t, i in mab)))
    print('  of which imm is a validated vtable head:', sum(1 for a, t, i in mab if is_msvc_vtable_head(i)))
    print('  of which target == 0xa8e8c8:', [(hex(a), hex(i)) for a, t, i in mab if t == 0xa8e8c8])
    raws = []
    i = 0
    while True:
        i = data.find(b'\xc7\x05', i)
        if i < 0:
            break
        raws.append(base + i); i += 1
    starts = set(a for a, t, im in mab)
    print('  raw byte pattern c7 05 in .text:', len(raws),
          ' real instruction starts:', sum(1 for a in raws if a in starts),
          ' mid-instruction coincidences:', len(raws) - sum(1 for a in raws if a in starts))

    print()
    print('== CONTROL 3 other real vtables')
    for vt in (0x7ea564, 0x7ea57c, 0x7e36d4, 0x7e1964):
        r = rtti(vt)
        print('  vtable %08x COL %08x class %r nbase %d' % (vt, r['col'], r['name'], r['nbase']))

    print()
    print('== SUPPORT: static-ctor table entry for 0x4e7ce0')
    tb = 0x812000
    i = 0
    ent = []
    while tb + i * 4 < 0x815da4:
        v = u32(tb + i * 4)
        if v == 0x4e7ce0:
            ent.append(tb + i * 4)
        i += 1
    print('  entries equal to 0x4e7ce0 inside [0x812000,0x815da4):', [hex(x) for x in ent])

if __name__ == '__main__':
    main()
