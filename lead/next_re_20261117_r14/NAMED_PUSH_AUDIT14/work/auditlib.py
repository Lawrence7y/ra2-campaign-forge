import sys, struct, os
import pefile
from capstone import *
from capstone.x86 import *

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
IB = 0x400000
pe = pefile.PE(EXE, fast_load=True)
pe.parse_data_directories()
DATA = pe.__data__
MD = Cs(CS_ARCH_X86, CS_MODE_32)
MD.skipdata = True
MD.detail = True

def rva2off(rva):
    return pe.get_offset_from_rva(rva)

def va2off(va):
    return rva2off(va - IB)

def is_va(va):
    rva = va - IB
    for s in pe.sections:
        if s.VirtualAddress <= rva < s.VirtualAddress + s.Misc_VirtualSize:
            return True
    return False

def rd(va, n):
    off = va2off(va)
    return DATA[off:off+n]

def u32(va):
    return struct.unpack('<I', rd(va, 4))[0]

def u16(va):
    return struct.unpack('<H', rd(va, 2))[0]

def u8(va):
    return rd(va, 1)[0]

def hexb(va, n):
    return rd(va, n).hex()

def disasm(va, n, base=None):
    code = rd(va, n)
    return list(MD.disasm(code, va))

def fmt_insn(i):
    return f"{i.address:08X}: {i.bytes.hex():<20} {i.mnemonic:<7} {i.op_str}"

def dump(va, n):
    for i in disasm(va, n):
        print(fmt_insn(i))

def cstring(va, maxn=200):
    off = va2off(va)
    end = DATA.find(b'\0', off, off+maxn)
    if end < 0: end = off+maxn
    return DATA[off:end].decode('latin1', 'replace')

# ---- RTTI ----
def parse_col(vtable_va):
    col_va = vtable_va - 4
    sig = u32(col_va + 0)
    offset = u32(col_va + 4)
    cd = u32(col_va + 8)
    ptd_rva = u32(col_va + 12)
    pchd_rva = u32(col_va + 16)
    res = dict(col_va=col_va, sig=sig, offset=offset, cd=cd,
               ptd_rva=ptd_rva, pchd_rva=pchd_rva)
    if is_va(IB + ptd_rva):
        td_va = IB + ptd_rva
        res['td_va'] = td_va
        res['td_vftable'] = u32(td_va + 0)
        res['td_spare'] = u32(td_va + 4)
        res['td_name'] = cstring(td_va + 8)
    return res

def print_col(vtable_va):
    r = parse_col(vtable_va)
    print(f"COL @ {r['col_va']:08X}: sig={r['sig']} offset={r['offset']} cd={r['cd']} pTD_rva=0x{r['ptd_rva']:X} pCHD_rva=0x{r['pchd_rva']:X}")
    if 'td_va' in r:
        print(f"  TD @ {r['td_va']:08X}: name='{r['td_name']}'")
    return r

def find_u32_va(value):
    pat = struct.pack('<I', value)
    hits = []
    start = 0
    while True:
        idx = DATA.find(pat, start)
        if idx < 0: break
        for s in pe.sections:
            if s.PointerToRawData <= idx < s.PointerToRawData + s.SizeOfRawData:
                rva = s.VirtualAddress + (idx - s.PointerToRawData)
                hits.append(IB + rva)
                break
        start = idx + 1
    return hits

def find_rel_calls(target_va):
    hits = []
    for s in pe.sections:
        if s.Name.rstrip(b'\0') != b'.text': continue
        code = DATA[s.PointerToRawData:s.PointerToRawData+s.SizeOfRawData]
        sec_va = IB + s.VirtualAddress
        md2 = Cs(CS_ARCH_X86, CS_MODE_32)
        md2.skipdata = True
        for i in md2.disasm(code, sec_va):
            if i.mnemonic in ('call','jmp') and i.op_str:
                op = i.op_str.strip()
                if op.startswith('0x'):
                    try:
                        tv = int(op, 16)
                        if tv == target_va:
                            hits.append((i.address, i.mnemonic, i.bytes.hex()))
                    except ValueError:
                        pass
    return hits

if __name__ == '__main__':
    for va in [0x4AF720, 0x4B62C0, 0x4B6470, 0x54DC60]:
        print('='*70)
        print(f"ENTRY {va:08X}")
        dump(va, 112)
