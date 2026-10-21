"""PE loader + capstone helpers for offline gamemd.exe analysis (read-only).

Key facts honoured:
  * Section VirtualAddress in the PE header is an RVA; absolute VA = ImageBase + RVA.
  * capstone md.disasm() aborts on invalid bytes (e.g. 0xC5 VEX prefix near 0x46F5A0),
    so we always disassemble in small blocks and re-sync byte-by-byte.
"""
import struct
import capstone

IMAGE_BASE_DEFAULT = 0x400000


class PE:
    def __init__(self, path):
        with open(path, 'rb') as f:
            self.data = f.read()
        d = self.data
        if d[:2] != b'MZ':
            raise ValueError('not MZ')
        e_lfanew = struct.unpack_from('<I', d, 0x3C)[0]
        if d[e_lfanew:e_lfanew + 4] != b'PE\0\0':
            raise ValueError('not PE')
        coff = e_lfanew + 4
        self.machine, self.nsec = struct.unpack_from('<HH', d, coff)
        self.opt_size = struct.unpack_from('<H', d, coff + 16)[0]
        opt = coff + 20
        self.magic = struct.unpack_from('<H', d, opt)[0]
        self.image_base = struct.unpack_from('<I', d, opt + 28)[0]
        self.entry_rva = struct.unpack_from('<I', d, opt + 16)[0]
        self.size_of_image = struct.unpack_from('<I', d, opt + 56)[0]
        self.sections = []
        sec = opt + self.opt_size
        for i in range(self.nsec):
            off = sec + i * 40
            name = d[off:off + 8].rstrip(b'\0').decode('latin-1')
            vsize, vaddr, rsize, raddr = struct.unpack_from('<IIII', d, off + 8)
            chars = struct.unpack_from('<I', d, off + 36)[0]
            self.sections.append(dict(name=name, vsize=vsize, vaddr=vaddr,
                                      rawsize=rsize, rawptr=raddr, chars=chars,
                                      va=self.image_base + vaddr,
                                      vend=self.image_base + vaddr + max(vsize, rsize)))
        self.text_lo, self.text_hi = self._text_range()

    def _text_range(self):
        lo, hi = None, None
        for s in self.sections:
            if s['name'] in ('.text', 'CODE'):
                lo = s['va'] if lo is None else min(lo, s['va'])
                hi = s['vend'] if hi is None else max(hi, s['vend'])
        if lo is None:
            lo, hi = 0x401000, 0x7EFFFF
        return lo, hi

    def section_of(self, va):
        rva = va - self.image_base
        for s in self.sections:
            if s['vaddr'] <= rva < s['vaddr'] + max(s['vsize'], s['rawsize']):
                return s
        return None

    def va_to_off(self, va):
        rva = va - self.image_base
        s = self.section_of(va)
        if s is None:
            return None
        delta = rva - s['vaddr']
        if delta >= s['rawsize']:
            return None
        return s['rawptr'] + delta

    def read(self, va, n):
        off = self.va_to_off(va)
        if off is None:
            return None
        return self.data[off:off + n]

    def dword(self, va):
        b = self.read(va, 4)
        if b is None or len(b) < 4:
            return None
        return struct.unpack('<I', b)[0]

    def is_text(self, va):
        return self.text_lo <= va <= self.text_hi

    def dump_sections(self):
        out = []
        for s in self.sections:
            out.append('% -9s VA=%08X-%08X raw=0x%06X size=0x%06X chars=%08X' % (
                s['name'], s['va'], s['vend'], s['rawptr'], s['rawsize'], s['chars']))
        return '\n'.join(out)


def make_md():
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = True
    md.skipdata = False
    return md


def disasm_range(pe, md, start_va, end_va, max_insn=200000):
    """Disassemble [start_va, end_va) with byte-level resync on bad bytes."""
    out = []
    va = start_va
    while va < end_va and len(out) < max_insn:
        off = pe.va_to_off(va)
        if off is None:
            va += 1
            continue
        chunk = pe.data[off:off + (end_va - va)]
        got = False
        for insn in md.disasm(chunk, va):
            out.append(insn)
            got = True
            va = insn.address + insn.size
            if va >= end_va:
                break
        if not got:
            # illegal byte: emit a data pseudo-insn and advance 1
            out.append(PseudoInsn(va, chunk[0] if chunk else 0))
            va += 1
        else:
            # md.disasm stopped early (illegal opcode after valid ones); advance 1
            if va < end_va and out and out[-1].address + out[-1].size == va:
                # check whether next byte decodes; if not, skip it
                off2 = pe.va_to_off(va)
                if off2 is not None:
                    trial = list(md.disasm(pe.data[off2:off2 + 16], va))
                    if not trial:
                        out.append(PseudoInsn(va, pe.data[off2]))
                        va += 1
    return out


class PseudoInsn:
    def __init__(self, address, byte):
        self.address = address
        self.size = 1
        self.byte = byte
        self.mnemonic = 'db'
        self.op_str = '0x%02X' % byte
        self.bytes = bytes([byte])

    def __repr__(self):
        return '%08X  db 0x%02X' % (self.address, self.byte)


def fmt(insns, lo=None, hi=None, mark=()):
    lines = []
    for i in insns:
        if lo is not None and i.address < lo:
            continue
        if hi is not None and i.address >= hi:
            continue
        b = i.bytes.hex() if hasattr(i, 'bytes') else ''
        tag = ' <<<' if i.address in mark else ''
        lines.append('%08X  %-24s %-8s %s%s' % (i.address, b, i.mnemonic, i.op_str, tag))
    return '\n'.join(lines)
