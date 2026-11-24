"""NAMED_PUSH_AUDIT4 independent toolkit. Own code, no executor imports."""
import pefile, struct
from capstone import Cs, CS_ARCH_X86, CS_MODE_32, CS_OPT_SKIPDATA, CS_OPT_DETAIL

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
IMAGEBASE = 0x400000

class Img:
    def __init__(self, path=EXE):
        self.pe = pefile.PE(path, fast_load=True)
        self.pe.parse_data_directories()
        self.data = open(path, 'rb').read()
        self.sections = []
        for s in self.pe.sections:
            name = s.Name.rstrip(b'\x00').decode('latin1')
            self.sections.append((name, IMAGEBASE + s.VirtualAddress,
                                  s.Misc_VirtualSize, s.PointerToRawData,
                                  s.SizeOfRawData))
        self.md = Cs(CS_ARCH_X86, CS_MODE_32)
        self.md.detail = True
        self.md.skipdata = True
        self.mdds = Cs(CS_ARCH_X86, CS_MODE_32)
        self.mdds.detail = True
        self.mdds.skipdata = True
        self.exports = {}
        if hasattr(self.pe, 'DIRECTORY_ENTRY_EXPORT'):
            for e in self.pe.DIRECTORY_ENTRY_EXPORT.symbols:
                if e.name:
                    self.exports[e.name.decode('latin1')] = IMAGEBASE + e.address

    def sec_of(self, va):
        for name, base, vsz, praw, rsz in self.sections:
            if base <= va < base + max(vsz, rsz):
                return name, base, vsz, praw
        return None, None, None, None

    def off(self, va):
        name, base, vsz, praw = self.sec_of(va)
        if base is None:
            return None
        return praw + (va - base)

    def read(self, va, n):
        o = self.off(va)
        if o is None:
            return None
        return self.data[o:o + n]

    def u32(self, va):
        b = self.read(va, 4)
        return None if b is None or len(b) < 4 else struct.unpack('<I', b)[0]

    def u16(self, va):
        b = self.read(va, 2)
        return None if b is None or len(b) < 2 else struct.unpack('<H', b)[0]

    def i32(self, va):
        b = self.read(va, 4)
        return None if b is None or len(b) < 4 else struct.unpack('<i', b)[0]

    def u8(self, va):
        b = self.read(va, 1)
        return None if b is None else b[0]

    def hexb(self, va, n):
        b = self.read(va, n)
        return '' if b is None else b.hex(' ')

    def cstr(self, va, maxn=260):
        b = self.read(va, maxn)
        if b is None:
            return None
        z = b.find(b'\x00')
        if z >= 0:
            b = b[:z]
        try:
            return b.decode('latin1')
        except Exception:
            return None

    def is_text(self, va):
        name, _, _, _ = self.sec_of(va)
        return name == '.text'

    def dis(self, va, nbytes, detail=True):
        b = self.read(va, nbytes)
        if b is None:
            return []
        mdd = self.md if detail else self.mdds
        return list(mdd.disasm(b, va))

    # ---- function discovery ----
    def funcs(self):
        """Map of entry -> last_va, from pdata-less 32bit PE: use .text scan of
        call targets? Instead use explicit function starts from a linear sweep
        seeded at every `call rel32` target and export. Cached."""
        if hasattr(self, '_funcs'):
            return self._funcs
        starts = set()
        name, base, vsz, praw = self.sec_of(0x401000)
        end = 0x7E038D
        # linear sweep the whole text, no skipdata, to find call rel32 targets
        b = self.read(0x401000, end - 0x401000)
        md = Cs(CS_ARCH_X86, CS_MODE_32)
        md.detail = False
        md.skipdata = True
        for ins in md.disasm(b, 0x401000):
            if ins.mnemonic == 'call' and ins.op_str.startswith('0x'):
                t = int(ins.op_str, 16)
                if 0x401000 <= t < end:
                    starts.add(t)
        for v in self.exports.values():
            starts.add(v)
        self._funcs = starts
        return starts

    def body(self, entry, limit=0x400, stop_at=None):
        """Recursive-descent body: follow direct jcc/jmp, stop at ret/jmp-indirect.
        Returns list of insns sorted by address."""
        seen = {}
        work = [entry]
        visited = set()
        while work:
            a = work.pop()
            while a not in visited and len(visited) < 4000:
                visited.add(a)
                ins_list = self.dis(a, 16, detail=True)
                if not ins_list:
                    break
                ins = ins_list[0]
                seen[a] = ins
                mn = ins.mnemonic
                if mn.startswith('ret'):
                    break
                if mn == 'jmp':
                    if ins.op_str.startswith('0x'):
                        a = int(ins.op_str, 16)
                        continue
                    break
                if mn.startswith('j') and ins.op_str.startswith('0x'):
                    work.append(int(ins.op_str, 16))
                if mn == 'call' and ins.op_str.startswith('0x'):
                    pass  # do not descend
                if 'hlt' == mn or 'int3' == mn:
                    break
                a = ins.address + ins.size
                if a - entry > limit:
                    break
        return [seen[k] for k in sorted(seen)]


def fmt(ins):
    return "%08X  %-20s %-8s %s" % (ins.address, ins.bytes.hex(' ').upper(), ins.mnemonic, ins.op_str)
