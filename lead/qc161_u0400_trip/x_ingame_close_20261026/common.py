import struct, sys

PATH = r'D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip\_src_L1_sf8_20261020\gamemd.exe'

class Image:
    def __init__(self, path):
        self.d = open(path, 'rb').read()
        pe = struct.unpack_from('<I', self.d, 0x3c)[0]
        # PE32 (magic 0x10b): ImageBase is at optional header offset 0x1C = pe+0x18+0x1C = pe+0x34
        assert struct.unpack_from('<H', self.d, pe + 0x18)[0] == 0x10B
        self.imagebase = struct.unpack_from('<I', self.d, pe + 0x34)[0]
        nsec = struct.unpack_from('<H', self.d, pe + 6)[0]
        opt = struct.unpack_from('<H', self.d, pe + 0x14)[0]
        sec = pe + 0x18 + opt
        self.sections = []
        for i in range(nsec):
            o = sec + i * 40
            name = self.d[o:o+8].rstrip(b'\x00').decode('latin1')
            vsize = struct.unpack_from('<I', self.d, o+8)[0]
            va = struct.unpack_from('<I', self.d, o+12)[0]
            rawsize = struct.unpack_from('<I', self.d, o+16)[0]
            rawoff = struct.unpack_from('<I', self.d, o+20)[0]
            self.sections.append((name, self.imagebase + va, vsize, rawoff, rawsize))

    def read(self, va, n):
        for name, sva, vsize, rawoff, rawsize in self.sections:
            # include virtual tail beyond rawsize (zero filled) for .text/.data
            if sva <= va < sva + max(vsize, rawsize):
                off = rawoff + (va - sva)
                avail = rawsize - (va - sva)
                if avail <= 0:
                    return b'\x00' * n
                b = self.d[off:off + min(n, avail)]
                if len(b) < n:
                    b = b + b'\x00' * (n - len(b))
                return b
        return None

    def sec_of(self, va):
        for name, sva, vsize, rawoff, rawsize in self.sections:
            if sva <= va < sva + max(vsize, rawsize):
                return name
        return None

    def data_range(self, va, n):
        """read with 0-fill, no bounds check for data sections"""
        for name, sva, vsize, rawoff, rawsize in self.sections:
            if sva <= va < sva + vsize:
                off = rawoff + (va - sva)
                avail = rawsize - (va - sva)
                b = self.d[off:off + max(0, min(n, avail))]
                return b + b'\x00' * (n - len(b))
        return b'\x00' * n

IMG = Image(PATH)
