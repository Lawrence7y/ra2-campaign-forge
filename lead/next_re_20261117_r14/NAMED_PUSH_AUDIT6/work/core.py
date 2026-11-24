"""AUDIT6 core: self-contained PE + capstone helpers. Only my own disassembly."""
import struct, pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
IMAGEBASE = 0x400000
TEXT_LO, TEXT_HI = 0x401000, 0x7E038D

_pe = pefile.PE(EXE, fast_load=False)
DATA = open(EXE, 'rb').read()
SECTIONS = []
for s in _pe.sections:
    name = s.Name.rstrip(b'\x00').decode('latin1')
    va = IMAGEBASE + s.VirtualAddress
    vsz = s.Misc_VirtualSize
    rawsz = s.SizeOfRawData
    off = s.PointerToRawData
    SECTIONS.append((name, va, vsz, off, rawsz))

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True
md.skipdata = True


def sections():
    return SECTIONS


def sec_of(va):
    for name, sva, vsz, off, rawsz in SECTIONS:
        if sva <= va < sva + max(vsz, rawsz):
            return name
    return None


def va2off(va):
    for name, sva, vsz, off, rawsz in SECTIONS:
        if sva <= va < sva + rawsz:
            return off + (va - sva)
    return None


def read(va, n):
    o = va2off(va)
    if o is None:
        return None
    return DATA[o:o + n]


def u32(va):
    b = read(va, 4)
    return struct.unpack('<I', b)[0] if b and len(b) == 4 else None


def u16(va):
    b = read(va, 2)
    return struct.unpack('<H', b)[0] if b and len(b) == 2 else None


def hexb(va, n):
    b = read(va, n)
    return b.hex(' ') if b else None


def cstr(va, maxlen=200):
    b = read(va, maxlen)
    if not b:
        return None
    e = b.find(b'\x00')
    if e >= 0:
        b = b[:e]
    try:
        return b.decode('latin1')
    except Exception:
        return None


def in_text(va):
    return TEXT_LO <= va < TEXT_HI


def dis(va, count=2000, stop_at_ret=False):
    """Linear disassembly from va. Returns list of dicts."""
    o = va2off(va)
    if o is None:
        return []
    out = []
    skipdata_seen = 0
    for insn in md.disasm(DATA[o:o + 5000], va):
        out.append({'a': insn.address, 'b': insn.bytes.hex(),
                    't': insn.mnemonic + (' ' + insn.op_str if insn.op_str else ''),
                    'i': insn, 'skip': insn.id == 0})
        if insn.id == 0:
            skipdata_seen += 1
        if len(out) >= count:
            break
        if stop_at_ret and insn.mnemonic.startswith('ret'):
            break
    return out


def func_body(entry, max_insn=4000):
    """Disassemble function starting at entry until the closing ret (heuristic:
    stop at a ret/ret-imm whose next bytes are padding or which ends the block)."""
    o = va2off(entry)
    insns = []
    for insn in md.disasm(DATA[o:o + 20000], entry):
        insns.append({'a': insn.address, 'b': insn.bytes.hex(),
                      't': insn.mnemonic + (' ' + insn.op_str if insn.op_str else ''),
                      'i': insn, 'skip': insn.id == 0})
        if len(insns) >= max_insn:
            break
        if insn.mnemonic.startswith('ret'):
            # look ahead: if the next bytes are padding (cc / 90 runs) then this is the end
            nxt = DATA[va2off(insn.address) + insn.size:
                       va2off(insn.address) + insn.size + 4]
            if all(x in (0xCC, 0x90, 0x00) for x in nxt) or len(nxt) < 4:
                break
    return insns


def find_dword(val, align4=True):
    """All VAs whose 4-byte little-endian dword equals val (per section)."""
    pat = struct.pack('<I', val)
    hits = []
    for name, sva, vsz, off, rawsz in SECTIONS:
        blob = DATA[off:off + rawsz]
        i = blob.find(pat)
        while i >= 0:
            if (not align4) or (i % 4 == 0):
                hits.append((name, sva + i))
            i = blob.find(pat, i + 1)
    return hits


def rtti_of_vtable(vt):
    """Given vtable VA, walk the RTTI complete-object-locator at vt-4."""
    res = {'vt': vt, 'col': None, 'sig': None, 'td': None, 'name': None,
           'col_sec': None, 'td_sec': None, 'err': None}
    col = u32(vt - 4)
    if col is None:
        res['err'] = 'no col slot'
        return res
    res['col'] = col
    res['col_sec'] = sec_of(col)
    res['sig'] = u32(col)
    td = u32(col + 0xC)
    res['td'] = td
    if td:
        res['td_sec'] = sec_of(td)
        # MSVC 32-bit TypeDescriptor: vftable(4), spare(4), name[] at +8 (inline chars)
        res['name'] = cstr(td + 8)
    return res


def vtable_containing(slot_va):
    """Walk back from slot_va over contiguous .text pointers; return (vt_start, index)."""
    p = slot_va
    while True:
        prev = u32(p - 4)
        if prev is None or not in_text(prev):
            break
        p -= 4
    return p, (slot_va - p) // 4


def vt_first_slots(vt, n=8):
    return [(vt + 4 * i, u32(vt + 4 * i)) for i in range(n)]


def iat_name_for_slot(va):
    """Given a VA holding a dword (an IAT slot), map to import name if resolvable."""
    # find import entry whose IAT address == va
    try:
        for entry in _pe.DIRECTORY_ENTRY_IMPORT:
            for imp in entry.imports:
                if imp.address == va:
                    return entry.dll.decode() + '!' + (imp.name.decode() if imp.name else '#%d' % imp.ordinal)
    except Exception:
        pass
    return None


def import_at(va):
    return iat_name_for_slot(va)
