"""x121lib.py - self-written minimal 32-bit PE parser + helpers.

Only stdlib + system capstone. No imports from this repo's libraries.
"""
import struct


class PE:
    def __init__(self, path):
        with open(path, 'rb') as f:
            self.buf = f.read()
        b = self.buf
        assert b[:2] == b'MZ', 'no MZ'
        self.e_lfanew = struct.unpack_from('<I', b, 0x3c)[0]
        self.pe_off = self.e_lfanew
        assert b[self.e_lfanew:self.e_lfanew + 4] == b'PE\0\0', 'no PE sig'
        coff = self.e_lfanew + 4
        (self.machine, self.nsec, self.timestamp, self.psymptr, self.nsym,
         self.opt_size, self.chars) = struct.unpack_from('<HHIIIHH', b, coff)
        opt = coff + 20
        self.magic = struct.unpack_from('<H', b, opt)[0]
        assert self.magic == 0x10b, 'not PE32: %x' % self.magic
        self.image_base = struct.unpack_from('<I', b, opt + 28)[0]
        self.size_of_image = struct.unpack_from('<I', b, opt + 56)[0]
        self.size_of_headers = struct.unpack_from('<I', b, opt + 60)[0]
        ndir_off = opt + 92
        self.ndirs = struct.unpack_from('<I', b, ndir_off)[0]
        self.dirs = []
        for i in range(self.ndirs):
            rva, sz = struct.unpack_from('<II', b, ndir_off + 4 + i * 8)
            self.dirs.append((rva, sz))
        sec = opt + self.opt_size
        self.sections = []
        for i in range(self.nsec):
            o = sec + i * 40
            name = b[o:o + 8].rstrip(b'\0').decode('latin1')
            vsize, vaddr, rawsize, rawptr = struct.unpack_from('<IIII', b, o + 8)
            ch = struct.unpack_from('<I', b, o + 36)[0]
            self.sections.append(dict(name=name, vsize=vsize, va=vaddr,
                                      rawsize=rawsize, raw=rawptr, chars=ch))
        self.iat = {}       # slot VA -> (dll, name)
        self.imports = []   # (dll, name, slot_va)
        self._parse_imports()

    def section_of_rva(self, rva):
        for s in self.sections:
            if s['va'] <= rva < s['va'] + max(s['vsize'], s['rawsize']):
                return s
        return None

    def off(self, rva):
        s = self.section_of_rva(rva)
        if s is None:
            return None
        d = rva - s['va']
        if d < s['rawsize']:
            return s['raw'] + d
        return None

    def off_va(self, va):
        return self.off(va - self.image_base)

    def read(self, rva, n):
        o = self.off(rva)
        if o is None or o + n > len(self.buf):
            return None
        return self.buf[o:o + n]

    def read_va(self, va, n):
        return self.read(va - self.image_base, n)

    def u32(self, rva):
        d = self.read(rva, 4)
        return struct.unpack('<I', d)[0] if d else None

    def u32_va(self, va):
        d = self.read_va(va, 4)
        return struct.unpack('<I', d)[0] if d else None

    def cstr(self, rva, maxlen=220):
        d = self.read(rva, maxlen)
        if d is None:
            return None
        e = d.find(b'\0')
        return d[:e if e >= 0 else maxlen].decode('latin1')

    def _parse_imports(self):
        if len(self.dirs) < 2 or self.dirs[1][0] == 0:
            return
        d = self.dirs[1][0]
        guard = 0
        while guard < 4096:
            guard += 1
            ent = self.read(d, 20)
            if ent is None:
                break
            oft, ts, fwd, name_rva, ft = struct.unpack('<IIIII', ent)
            if (oft, ts, fwd, name_rva, ft) == (0, 0, 0, 0, 0):
                break
            dll = self.cstr(name_rva) or '?'
            thunk_rva = oft if oft else ft
            i = 0
            while i < 8192:
                t = self.u32(thunk_rva + i * 4)
                if not t:
                    break
                slot_va = self.image_base + ft + i * 4
                if t & 0x80000000:
                    nm = 'ORDINAL:%d' % (t & 0xffff)
                else:
                    nm = self.cstr((t & 0x7fffffff) + 2) or '?'
                self.iat[slot_va] = (dll, nm)
                self.imports.append((dll, nm, slot_va))
                i += 1
            d += 20

    def iat_name(self, va):
        e = self.iat.get(va)
        return e[1] if e else None

    def iat_qual(self, va):
        e = self.iat.get(va)
        return '%s!%s' % e if e else None


def find_cc_func_start(pe, va, max_back=0x40000):
    """Function start = first byte after nearest preceding run of >=2 x 0xCC."""
    s = next(x for x in pe.sections if x['name'] == '.text')
    o = pe.off_va(va)
    if o is None:
        return None
    lo = max(s['raw'], o - max_back)
    i = o - 1
    while i >= lo:
        if pe.buf[i] == 0xcc:
            j = i
            while j > lo and pe.buf[j - 1] == 0xcc:
                j -= 1
            if i - j + 1 >= 2:
                return pe.image_base + (i + 1 - s['raw']) + s['va']
        i -= 1
    return None
