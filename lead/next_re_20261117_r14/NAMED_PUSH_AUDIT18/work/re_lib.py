"""Independent PE/RE helper for NAMED_PUSH_AUDIT18.
Self-written: VA<->offset via pefile, u8/u32 reads, capstone disasm with skipdata=True.
No use of executor artifacts as evidence.
"""
import pefile
from capstone import *
from capstone.x86 import *

PE_PATH = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
pe = pefile.PE(PE_PATH, fast_load=True)
pe.parse_data_directories()
IMAGE_BASE = pe.OPTIONAL_HEADER.ImageBase
TEXT_VA   = IMAGE_BASE + pe.sections[0].VirtualAddress
TEXT_END  = TEXT_VA + pe.sections[0].Misc_VirtualSize
# section list
SECS = []
for s in pe.sections:
    name = s.Name.rstrip(b'\0').decode('latin1')
    SECS.append((name, IMAGE_BASE+s.VirtualAddress, IMAGE_BASE+s.VirtualAddress+s.Misc_VirtualSize,
                 s.VirtualAddress, s.Misc_VirtualSize, s.PointerToRawData, s.SizeOfRawData))

def section_of(va):
    for name,v0,v1,rva,vsz,raw,rsz in SECS:
        if v0 <= va < v1:
            return name
    return None

def mapped(va, n=1):
    for name,v0,v1,rva,vsz,raw,rsz in SECS:
        if v0 <= va and va+n <= v1:
            off = raw + (va - v0)
            if 0 <= off < len(pe.__data__) and off+n <= len(pe.__data__):
                return True
    return False

def off_of(va):
    for name,v0,v1,rva,vsz,raw,rsz in SECS:
        if v0 <= va < v1:
            return raw + (va - v0)
    raise ValueError('VA not in any section: %08X' % va)

def u8(va):
    o = off_of(va); return pe.__data__[o]

def u16(va):
    o = off_of(va); return int.from_bytes(pe.__data__[o:o+2],'little')

def u32(va):
    o = off_of(va); return int.from_bytes(pe.__data__[o:o+4],'little')

def bytes_at(va, n):
    o = off_of(va); return pe.__data__[o:o+n]

def cstr(va, maxn=200):
    o = off_of(va); d = pe.__data__
    end = o
    while end < len(d) and end-o < maxn and d[end] != 0:
        end += 1
    return d[o:end].decode('latin1')

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True
md.skipdata = True

def disasm(va, size, stop_on_ret=False):
    out = []
    for ins in md.disasm(bytes_at(va,size), va):
        txt = '%08X  %-20s %s %s' % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str)
        out.append((ins.address, ins.mnemonic, ins.op_str, ins.bytes, txt))
        if stop_on_ret and ins.mnemonic.startswith('ret'):
            break
    return out

def disasm_one(va):
    for ins in md.disasm(bytes_at(va,16), va):
        return ins
    return None

# RTTI: vt -> COL -> TD (absolute VA) -> inline name at TD+8
def rtti(vt):
    col = u32(vt-4)
    res = {'vt':vt, 'col':col}
    if not mapped(col,20):
        res['err']='COL unmapped'; return res
    sig, offv, cd, ptd, pchd = [u32(col+4*i) for i in range(5)]
    res.update(sig=sig, off=offv, cd=cd, ptd=ptd, pchd=pchd,
               ptd_abs=ptd>=IMAGE_BASE, pchd_abs=pchd>=IMAGE_BASE)
    if mapped(ptd, 8):
        magic = bytes_at(ptd+8,4)
        res['td_magic']=magic.hex()
        if magic[:3] == b'.?A' or magic[:2]==b'.?':
            res['name_inline']=cstr(ptd+8)
        res['td_vftable']=u32(ptd)
        res['td_spare']=u32(ptd+4)
        # what u32(TD+8) would be if misread as pointer
        res['u32_td8']=u32(ptd+8)
        res['td8_as_ptr_mapped']= mapped(u32(ptd+8),1)
    else:
        res['err']='TD unmapped at abs VA %08X'%ptd
    return res

def vtable(vt, nslots=12):
    return [u32(vt+4*i) for i in range(nslots)]

if __name__ == '__main__':
    print('IMAGE_BASE=%08X TEXT=[%08X,%08X)'%(IMAGE_BASE,TEXT_VA,TEXT_END))
    for n,v0,v1,rva,vsz,raw,rsz in SECS:
        print('  %-8s VA %08X-%08X raw %08X size %08X'%(n,v0,v1,raw,rsz))
