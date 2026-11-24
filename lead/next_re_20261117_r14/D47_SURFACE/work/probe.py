# -*- coding: utf-8 -*-
"""D-47 surface measurement: byte-level anchor decoder probe."""
import struct, sys, io

EXE = r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
IB = 0x00400000
TEXT_LO, TEXT_HI = 0x00401000, 0x00796000      # .text
RDATA_LO, RDATA_HI = 0x007E1000, 0x00812000    # .rdata
DATA_LO, DATA_HI = 0x00812000, 0x00796000

_buf = None

def load():
    global _buf
    if _buf is None:
        _buf = open(EXE, 'rb').read()
    return _buf

# PE section table parse (minimal)
def sections():
    b = load()
    e_lfanew = struct.unpack_from('<I', b, 0x3C)[0]
    nsec = struct.unpack_from('<H', b, e_lfanew + 6)[0]
    optsz = struct.unpack_from('<H', b, e_lfanew + 20)[0]
    base = e_lfanew + 24 + optsz
    out = []
    for i in range(nsec):
        o = base + i * 40
        name = b[o:o+8].rstrip(b'\0').decode('latin1')
        vsize, rva, rawsize, rawptr = struct.unpack_from('<IIII', b, o + 8)
        out.append((name, rva + IB, vsize, rawptr, rawsize))
    return out

def rd(va, n):
    b = load()
    for name, sva, vsize, rawptr, rawsize in sections():
        if sva <= va < sva + max(vsize, rawsize):
            off = rawptr + (va - sva)
            return b[off:off+n]
    return b''

def u32(va):
    d = rd(va, 4)
    return struct.unpack('<I', d)[0] if len(d) == 4 else None

def in_rdata(x):
    return x is not None and RDATA_LO <= x < 0x00812000

MOV_IMM_PATTERNS = []  # (bytes, length, reg-desc)

def decode_at(va):
    """Classify the instruction at va. Returns (kind, detail)."""
    b = rd(va, 12)
    if len(b) < 2:
        return ('UNREADABLE', '')
    # mov dword ptr [reg(+disp)], imm32  -> c7 /0
    if b[0] == 0xC7:
        modrm = b[1]
        mod = modrm >> 6
        rm = modrm & 7
        # offset of imm32 depends on addressing form
        if mod == 0 and rm == 5:            # [disp32]
            doff, form = 2, 'mov [disp32],imm32'
        elif mod == 0 and rm == 4:          # SIB
            sib = b[2]
            doff = 3 if (sib & 7) != 5 else 7
            form = 'mov [sib],imm32'
        elif mod == 0:
            doff, form = 2, 'mov [reg],imm32'
        elif mod == 1 and rm == 4:          # SIB + disp8
            doff, form = 3, 'mov [sib+disp8],imm32'
        elif mod == 1:
            doff, form = 3, 'mov [reg+disp8],imm32'
        elif mod == 2 and rm == 4:          # SIB + disp32
            doff, form = 6, 'mov [sib+disp32],imm32'
        elif mod == 2:
            doff, form = 6, 'mov [reg+disp32],imm32'
        else:
            return ('OTHER', 'c7 mod3')
        imm = struct.unpack_from('<I', b, doff)[0]
        return ('MOV_IMM', {'form': form, 'imm': imm, 'vt': in_rdata(imm),
                            'len': doff + 4})
    # call dword ptr [reg(+disp)]  -> ff /2 ; distinguish IAT ([disp32]) from virtual ([reg+disp])
    if b[0] == 0xFF and (b[1] >> 3) & 7 == 2:
        modrm = b[1]; mod = modrm >> 6; rm = modrm & 7
        if mod == 0 and rm == 5:            # ff 15 <disp32>  == call [IAT]
            tgt = struct.unpack_from('<I', b, 2)[0]
            return ('CALL_IAT', {'target': tgt, 'len': 6})
        if mod == 0:
            return ('CALL_VT', {'form': 'call [reg]', 'disp': 0, 'len': 2})
        if mod == 1:
            return ('CALL_VT', {'form': 'call [reg+disp8]', 'disp': b[2], 'len': 3})
        if mod == 2:
            return ('CALL_VT', {'form': 'call [reg+disp32]',
                                'disp': struct.unpack_from('<I', b, 2)[0], 'len': 6})
        return ('OTHER', 'ff mod3')
    # call rel32
    if b[0] == 0xE8:
        rel = struct.unpack_from('<i', b, 1)[0]
        return ('CALL_REL', {'target': (va + 5 + rel) & 0xFFFFFFFF, 'len': 5})
    if b[0] == 0xE9:
        rel = struct.unpack_from('<i', b, 1)[0]
        return ('JMP_REL', {'target': (va + 5 + rel) & 0xFFFFFFFF, 'len': 5})
    if b[0] == 0x8B:
        return ('MOV_LOAD', {'modrm': b[1], 'len': 2})
    if b[0] in (0x89, 0x88, 0x8A):
        return ('MOV_STORE_REG', {'modrm': b[1], 'len': 2})
    return ('OTHER', b[:4].hex())

if __name__ == '__main__':
    print('sections:')
    for s in sections():
        print('  %-8s va=0x%08X vsize=0x%X raw=0x%X/0x%X' % (s[0], s[1], s[2], s[3], s[4]))
    for t in sys.argv[1:]:
        va = int(t, 16)
        print('%08X -> %r' % (va, decode_at(va)))
