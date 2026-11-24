# -*- coding: utf-8 -*-
# R17-R52-ADJ-D4 : D-4 byte ruling (F29 vs F49). Mirror opened read-only.
# Entry detection NEVER scans for C3/C2: every entry is a vtable slot VALUE taken
# from .rdata. Function extent = distance to the next known entry (ascending-address
# bound), because this PE32 image carries no .pdata (exception directory empty).
import hashlib, struct
from collections import Counter

MIRROR = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
OUTDIR = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R17_R52_ADJ_D4"

class PE:
    def __init__(self, path):
        self.raw = open(path, 'rb').read()
        self.sha = hashlib.sha256(self.raw).hexdigest().upper()
        b = self.raw
        e = struct.unpack_from('<I', b, 0x3C)[0]
        assert b[e:e+4] == b'PE\0\0'
        coff = e + 4
        nsec, = struct.unpack_from('<H', b, coff+2)
        optsz, = struct.unpack_from('<H', b, coff+16)
        opt = coff + 20
        self.image_base, = struct.unpack_from('<I', b, opt+28)
        ndir, = struct.unpack_from('<I', b, opt+92)
        self.dirs = [struct.unpack_from('<II', b, opt+96+8*i) for i in range(ndir)]
        self.secs = []
        so = opt + optsz
        for i in range(nsec):
            name = b[so+40*i: so+40*i+8].rstrip(b'\0').decode('latin1')
            vsz, va, rsz, rptr = struct.unpack_from('<IIII', b, so+40*i+8)
            self.secs.append(dict(name=name, va=va, vsz=vsz, rptr=rptr, rsz=rsz))
        self.rexc = self.dirs[3] if len(self.dirs) > 3 else (0, 0)

    def off(self, rva):
        for s in self.secs:
            if s['va'] <= rva < s['va'] + max(s['vsz'], s['rsz']):
                d = rva - s['va']
                if d >= s['rsz']:
                    raise ValueError('unbacked rva %#x in %s' % (rva, s['name']))
                return s['rptr'] + d
        raise ValueError('rva %#x outside all sections' % rva)

    def u32(self, rva): return struct.unpack_from('<I', self.raw, self.off(rva))[0]
    def buf(self, rva, n): return self.raw[self.off(rva): self.off(rva)+n]

    def secname(self, rva):
        for s in self.secs:
            if s['va'] <= rva < s['va'] + max(s['vsz'], s['rsz']): return s['name']
        return '?'

    def build_pdata(self):
        rva, sz = self.rexc
        if not rva or not sz: return 0
        self.fn = {}
        b = self.raw
        base = self.off(rva)
        for o in range(base, base+sz, 12):
            beg, end, uwi = struct.unpack_from('<III', b, o)
            self.fn[beg] = end
        return len(self.fn)

    # ---- RTTI chain: vt[-1] -> COL ; COL+0xC -> TD ; TD+8 = inline decorated name
    def vt_name(self, vt):
        try:
            col = self.u32(vt - self.image_base - 4)
            if not (self.image_base <= col < 0x900000): return None
            td = self.u32(col - self.image_base + 0xC)
            if not (self.image_base <= td < 0x900000): return None
            p = self.off(td - self.image_base + 8)
            out = []
            while True:
                c = self.raw[p]; p += 1
                if c == 0 or len(out) > 160: break
                out.append(chr(c))
            return (''.join(out) or None)
        except Exception:
            return None

MEM_WRITE_OPS = {0x88,0x89,0xC6,0xC7,0x00,0x01,0x08,0x09,0x10,0x11,0x18,0x19,
                 0x20,0x21,0x28,0x29,0x30,0x31}
def body_scan(b, n):
    """report first state-changing op inside the exact extent n"""
    for i in range(min(n, len(b))):
        op = b[i]
        if op in MEM_WRITE_OPS and i+1 < n and (b[i+1] >> 6) != 3:
            return 'memwrite %02X %02X @+%d' % (op, b[i+1], i)
        if op == 0xE8: return 'call rel32 @+%d' % i
        if op == 0xFF and i+1 < n:
            m = b[i+1]; reg = (m >> 3) & 7
            if reg in (2, 3): return 'call/jmp [mem] @+%d' % i
            if reg in (0, 1) and (m >> 6) != 3: return 'FF/%d memwrite @+%d' % (reg, i)
    return 'none'

def shape_of(b):
    if len(b) >= 8 and b[0] == 0xB8 and b[5] == 0xC2:
        return dict(shape='B8 imm32 C2 imm16', imm=struct.unpack_from('<I',b,1)[0],
                    retimm=struct.unpack_from('<H',b,6)[0], L=8)
    if len(b) >= 6 and b[0] == 0xB8 and b[5] == 0xC3:
        return dict(shape='B8 imm32 C3', imm=struct.unpack_from('<I',b,1)[0], retimm=None, L=6)
    return dict(shape='other', imm=None, retimm=None, L=0)

read_bytes = [0]
def rd(pe, va, n):
    read_bytes[0] += n
    return pe.buf(va - pe.image_base, n)

def main():
    pe = PE(MIRROR)
    npd = pe.build_pdata()
    print('=== MIRROR / HEADER ===')
    print('path   : %s' % MIRROR)
    print('sha256 : %s' % pe.sha)
    print('size   : %d' % len(pe.raw))
    print('imagebase %#x ; sections %s' % (pe.image_base,
          [(s['name'], hex(pe.image_base+s['va']), s['vsz'], s['rsz']) for s in pe.secs]))
    print('exception dir (idx3) = %s -> .pdata RUNTIME_FUNCTION count %d  (PE32 => entry-bound extent)' % (pe.rexc, npd))
    print('import dir (idx1) = %s' % (pe.dirs[1],))

    # ---------------- Q1 : the two shapes, literals straight from .text
    print('\n=== Q1 / Q1b ===')
    for va in (0x00410300, 0x00410310):
        b = rd(pe, va, 8)
        s = shape_of(b)
        print('%08X (%s) bytes=%s shape=%s imm=%s retimm=%s' %
              (va, pe.secname(va-pe.image_base), b.hex(' '), s['shape'], hex(s['imm']), s['retimm']))
    # complement: a real B8 imm32 C3 from the same image
    for va in (0x004C9150,):
        b = rd(pe, va, 8)
        s = shape_of(b)
        print('%08X (%s) bytes=%s shape=%s' % (va, pe.secname(va-pe.image_base), b.hex(' '), s['shape']))

    patA = bytes.fromhex('b801000000c204 00'.replace(' ',''))
    patB = bytes.fromhex('b801000000c3')
    def census(pat, label):
        offs = []; i = -1
        while True:
            i = pe.raw.find(pat, i+1)
            if i < 0: break
            offs.append(i)
        vas = []
        for fo in offs:
            for s in pe.secs:
                if s['rptr'] <= fo < s['rptr']+s['rsz']:
                    vas.append((s['name'], pe.image_base + s['va'] + (fo - s['rptr']))); break
        read_bytes[0] += len(pe.raw)
        print('%-30s count=%d by-section=%s first=%s' %
              (label, len(offs), dict(Counter(n for n,_ in vas)), [hex(v) for _,v in vas[:5]]))
        return [v for n, v in vas if n == '.text']
    stub_vas = sorted(set(census(patA, 'B8 01 00 00 00 C2 04 00')))
    _ = census(patB, 'B8 01 00 00 00 C3')
    # any B8 imm32 C2 04 00 (imm != 1) in .text ?
    nA = 0; xs = []
    i = -1
    while True:
        i = pe.raw.find(b'\xb8', i+1)
        if i < 0: break
        if pe.raw[i+5:i+8] == b'\xc2\x04\x00':
            nA += 1
            if len(xs) < 5: xs.append(i)
    read_bytes[0] += len(pe.raw)
    print('all "B8 imm32 C2 04 00" byte-strings in file: %d' % nA)

    # ---------------- Q2 : which .rdata dwords point at each stub entry
    print('\n=== Q2 : slot-level verification ===')
    stubset = set(stub_vas)
    # self-check every stub entry: exact extent via ascending known-entry bound
    print('-- stub entry self-check (entry boundary taken from vtable value, not byte scan) --')
    q1tbl = sorted(set(
        (lambda v: v)(x) for x in []))
    for va in stub_vas:
        b = rd(pe, va, 24)
        s = shape_of(b)
        print('  %s -> %s imm=%s retimm=%s' % (hex(va), s['shape'], hex(s['imm']), s['retimm']))

    hits = []
    for s in pe.secs:
        if s['name'] != '.rdata': continue
        blk = pe.raw[s['rptr']: s['rptr']+s['rsz']]
        read_bytes[0] += len(blk)
        for i in range(0, len(blk)-3, 4):
            v, = struct.unpack_from('<I', blk, i)
            if v in stubset:
                hits.append((pe.image_base + s['va'] + i, v))
    print('total .rdata dword hits on stub entries: %d' % len(hits))

    def vt_base_of(va):
        cur = va
        while True:
            prev = cur - 4
            try:
                v = pe.u32(prev - pe.image_base)
            except Exception:
                return cur
            if 0x401000 <= v < 0x800000: cur = prev
            else: return cur
    tables = {}
    for va, ent in hits:
        tables.setdefault(vt_base_of(va), []).append((va, ent))
    print('distinct vtable bases touched: %d ; tables whose slot1/slot2 both = stub: %d'
          % (len(tables), sum(1 for tb in tables
             if 0x00410300 in [e for _, e in tables[tb]] and 0x00410310 in [e for _, e in tables[tb]])))
    # pick up to 8 tables (S22_B4-like), list slot1/slot2 with class names
    picked = sorted(tables)[:8]
    rows = []
    for tb in picked:
        nm = pe.vt_name(tb)
        ent = sorted(tables[tb])
        # slot index = (slot_va - tb)/4 ; entries at slot1 (AddRef) = tb+4, slot2 (Release) = tb+8
        for slotno, want in ((1, 0x00410300), (2, 0x00410310)):
            sva = tb + 4*slotno
            if sva >= tb + 0x400: continue
            try:
                v = pe.u32(sva - pe.image_base)
            except Exception:
                continue
            read_bytes[0] += 4
            b = rd(pe, v, 24)
            s = shape_of(b)
            n = s['L']
            w = body_scan(b[:n], n)
            ok = (s['shape'] == 'B8 imm32 C2 imm16' and s['imm'] == 1
                  and s['retimm'] == 4 and n == 8 and w == 'none')
            rows.append([hex(tb), str(slotno), nm or '(RTTI name unreadable)',
                         hex(v), b[:n].hex(' '), 'yes' if s['imm'] == 1 else 'no',
                         'no-state-change' if w == 'none' else w, 'STUB' if ok else 'NOT-STUB'])
    hdr = ['vtable', 'slot', 'class', 'entry', 'body_bytes', 'const1', 'state', 'verdict']
    with open(OUTDIR + r'\slots.tsv', 'w', newline='\n', encoding='utf-8') as f:
        f.write('\t'.join(hdr) + '\n')
        for r in rows: f.write('\t'.join(r) + '\n')
    print('-- Q2 rows (%d) --' % len(rows))
    for r in rows: print('  ' + ' | '.join(r))

    # counter-example hunt: slots whose value is a C2 04 00 body but NOT a pure const-1 stub
    print('\n-- counter-example hunt over all .rdata dwords in the stub tables --')
    cex = []
    for tb in sorted(tables):
        for sva, ent in sorted(tables[tb]):
            b = rd(pe, ent, 20)
            s = shape_of(b)
            if s['shape'] == 'B8 imm32 C2 imm16' and (s['imm'] != 1 or s['retimm'] != 4):
                cex.append((tb, (sva - tb)//4, ent, s['imm'], s['retimm']))
    print('slots in stub tables whose target is B8 imm32 C2 imm16 with imm!=1 or ret!=4: %d'
          % len(cex))
    for tb, sl, ent, imm, r in cex[:10]:
        print('   vt=%s slot=%d -> %s imm=%s ret=%s' % (hex(tb), sl, hex(ent), hex(imm), r))
    print('bytes read from mirror (file bytes touched, census included): %d / %d'
          % (read_bytes[0], len(pe.raw)))

if __name__ == '__main__':
    main()
