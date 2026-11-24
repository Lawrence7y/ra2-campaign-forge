import struct

P = r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
data = open(P, 'rb').read()

e_lfanew = struct.unpack_from('<I', data, 0x3C)[0]
coff = e_lfanew + 4
machine, nsec, _, _, _, optsize, chars = struct.unpack_from('<HHIIIHH', data, coff)
opt = coff + 20
magic = struct.unpack_from('<H', data, opt)[0]
imagebase = struct.unpack_from('<I', data, opt + 28)[0]
sec = opt + optsize
sections = []
for i in range(nsec):
    off = sec + i * 40
    name = data[off:off + 8].rstrip(b'\x00').decode(errors='replace')
    vsize, va, rawsize, rawptr = struct.unpack_from('<IIII', data, off + 8)
    sections.append((name, va, vsize, rawptr, rawsize))

print(f'imagebase={imagebase:08X} magic={magic:04X} nsec={nsec}')
for name, va, vsize, rawptr, rawsize in sections:
    print(f'  {name:8s} VA={imagebase+va:08X} vsize={vsize:06X} raw={rawptr:06X} rawsz={rawsize:06X}')

def off2va(o):
    for name, sva, vsize, rawptr, rawsize in sections:
        if rawptr <= o < rawptr + rawsize:
            return imagebase + sva + (o - rawptr), name
    return None, None

def va2off(va):
    rva = va - imagebase
    for name, sva, vsize, rawptr, rawsize in sections:
        if sva <= rva < sva + max(vsize, rawsize):
            d = rva - sva
            if d < rawsize:
                return rawptr + d
    return None

# 0) verify premise: vtable 0x7E3EBC slot 11 == 0x459EC0 and that fn is B8 06 C3
vt = 0x7E3EBC
vo = va2off(vt)
print(f'\nvtable {vt:08X} file offset = {vo:08X}')
for k in [0, 11, 107]:
    v = struct.unpack_from('<I', data, vo + 4 * k)[0]
    print(f'  slot {k:3d} @ +{4*k:#06x} -> {v:08X}')
wi = va2off(0x459EC0)
print(f'WhatAmI@0x459EC0 bytes: {data[wi:wi+8].hex()}  (expect b806000000c3)')

# 1) scan whole file for references to vtable base and possible secondary vptr writes
targets = [vt + 4 * k for k in range(0, 8)]
for t in targets:
    pat = struct.pack('<I', t)
    idx = 0
    hits = []
    while True:
        i = data.find(pat, idx)
        if i < 0:
            break
        idx = i + 1
        va, secn = off2va(i)
        hits.append((i, va, secn))
    print(f'\ntarget {t:08X}: {len(hits)} raw hits')
    for i, va, secn in hits:
        prev = data[max(0, i - 10):i].hex()
        nxt = data[i + 4:i + 10].hex()
        print(f'  off={i:08X} va={va:08X} sec={secn} prev={prev} next={nxt}')

# 2) dump vtable slots for class6 and class15 and compare
def dump_vt(base, n):
    o = va2off(base)
    return [struct.unpack_from('<I', data, o + 4 * k)[0] for k in range(n)]

n = 130
v6 = dump_vt(vt, n)
v15 = dump_vt(0x7EB058, n)
print(f'\n--- slot table (slot, func6, func15, same?) ---')
same = []
for k in range(n):
    m = (v6[k] == v15[k])
    if m and v6[k] != 0:
        same.append(k)
    print(f'{k:3d}  {v6[k]:08X}  {v15[k]:08X}  {"SAME" if m else ""}')
print(f'\nshared non-null slots (6 vs 15): {len(same)}')
print(same[:60])

# 3) find preceding vtable start: walk back while dwords point into .text
def is_code_ptr(v):
    va, secn = off2va(va2off(v)) if va2off(v) is not None else (None, None)
    return secn == '.text'

def va_sec(v):
    rva = v - imagebase
    for name, sva, vsize, rawptr, rawsize in sections:
        if sva <= rva < sva + max(vsize, rawsize):
            return name
    return None

o = va2off(vt)
start = vt
while True:
    pv = struct.unpack_from('<I', data, o - 4)[0]
    if va_sec(pv) == '.text':
        start -= 4
        o -= 4
    else:
        break
end = vt
o = va2off(vt)
while True:
    nv = struct.unpack_from('<I', data, o)
    if va_sec(nv) == '.text':
        end += 4
        o += 4
    else:
        break
print(f'\ncontiguous code-ptr run containing 0x7E3EBC: {start:08X} .. {end-4:08X} (len {(end-start)//4+1} slots)')
