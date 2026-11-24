
#!/usr/bin/env python3
# R17-R9 read-only static reproducer. Only reads gamemd.exe; writes only in this dir.
# Usage: python work.py
import hashlib, struct, os, sys

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
IB = 0x400000
SECS = {}  # name -> (va, rawptr, size)

def load():
    with open(EXE, 'rb') as f:
        data = f.read()
    return data

def parse(data):
    e = struct.unpack_from('<I', data, 0x3C)[0]
    nsec = struct.unpack_from('<H', data, e + 6)[0]
    opt = e + 24
    ib = struct.unpack_from('<I', data, opt + 28)[0]
    secoff = opt + struct.unpack_from('<H', data, e + 20)[0]
    out = []
    for i in range(nsec):
        o = secoff + i * 40
        name = data[o:o+8].rstrip(b'\0').decode('latin1')
        vsize, vaddr, rsize, raddr = struct.unpack_from('<IIII', data, o+8)
        out.append((name, ib+vaddr, raddr, rsize, vsize))
    return ib, out

def va2off(secs, va):
    for n, sva, raw, rs, vs in secs:
        if sva <= va < sva + rs:
            return raw + (va - sva)
    raise ValueError(hex(va))

def all_refs(data, secs, target):
    nb = struct.pack('<I', target)
    hits = []
    for n, sva, raw, rs, vs in secs:
        blk = data[raw:raw+rs]
        i = blk.find(nb)
        while i >= 0:
            hits.append((n, sva + i))
            i = blk.find(nb, i + 1)
    return hits

def vtable_blob(rd_va, rd_blk, lo, hi):
    """Maximal run of dwords that are image pointers (.text or .rdata or .data)."""
    def isptr(v):
        return 0x401000 <= v < 0xB79BE4
    i = (lo - rd_va)//4
    while isptr(struct.unpack_from('<I', rd_blk, (i-1)*4)[0]) and i > 0:
        i -= 1
    start = i
    while isptr(struct.unpack_from('<I', rd_blk, i*4)[0]):
        i += 1
    return rd_va + start*4, rd_va + i*4

def main():
    data = load()
    print('SHA256', hashlib.sha256(data).hexdigest().upper())
    ib, secs = parse(data)
    rd = [s for s in secs if s[0] == '.rdata'][0]
    rd_off = rd[2]; rd_va = rd[1]; rd_size = rd[3]
    rd_blk = data[rd_off:rd_off+rd_size]
    for t in (0x43F180, 0x449440):
        print('unique static refs for', hex(t), [(n, hex(a)) for n, a in all_refs(data, secs, t)])
    s, e = vtable_blob(rd_va, rd_blk, 0x7E3FE0, 0x7E4400)
    print('pointer-run containing 0x7E3FE0:', hex(s), '..', hex(e-1), 'slots', (e-s)//4)
    for t in (0x7E3FE0, 0x7E4050, 0x7E4068, 0x7E4054, 0x7E4058, 0x7E405C, 0x7E4060, 0x7E4064):
        r = all_refs(data, secs, t)
        print('refs to', hex(t), '=>', len(r), r[:6])
    # .data globals that point into the run
    dt = [x for x in secs if x[0] == '.data'][0]
    o = dt[2]; n = 0
    while o + 4 <= dt[2] + dt[3]:
        v = struct.unpack_from('<I', data, o)[0]
        if s <= v < e:
            gva = dt[1] + (o - dt[2])
            print('  .data global', hex(gva), '->', hex(v), 'refs to global:', len(all_refs(data, secs, gva)))
        o += 4

if __name__ == '__main__':
    main()
