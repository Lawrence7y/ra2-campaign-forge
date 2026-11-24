
import pefile, capstone, struct
EXE=r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
pe=pefile.PE(EXE)
base=pe.OPTIONAL_HEADER.ImageBase
print('ImageBase',hex(base))
data=open(EXE,'rb').read()
def rva2off(rva):
    for s in pe.sections:
        if s.VirtualAddress<=rva<s.VirtualAddress+max(s.Misc_VirtualSize,s.SizeOfRawData):
            return s.PointerToRawData+(rva-s.VirtualAddress)
    return None
def va2off(va): return rva2off(va-base)
md=capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail=False

def disas(va, count):
    off=va2off(va)
    code=data[off:off+2048]
    out=[]
    for i in md.disasm(code, va):
        out.append(f'{i.address:08X}  {i.bytes.hex():<20} {i.mnemonic:<8} {i.op_str}')
        if len(out)>=count: break
    return out

va=0x53AF40
print('\n===== DISASM 0x53AF40 (first 70 insns) =====')
for l in disas(va,70): print(l)

print('\n===== PsyDom global refs within 0x53AF40 function =====')
gs=[0xA9FAC0,0xA9FA48,0xA9FAC8,0xA9FAC4,0xA9FAB4,0xA9FAD0]
off=va2off(va); code=data[off:off+0x500]
for i in md.disasm(code,va):
    up=i.op_str.upper().replace('0X','0x')
    hit=[hex(g) for g in gs if f'{g:08X}' in up or f'{g:X}' in up or hex(g).upper() in up]
    if hit: print(f'{i.address:08X}: {i.mnemonic} {i.op_str}  <-- {hit}')
    if i.address-va>0x400: break

print('\n===== E8 call sites -> 0x53AF40 =====')
for s in pe.sections:
    if b'.text' not in s.Name: continue
    raw=data[s.PointerToRawData:s.PointerToRawData+s.SizeOfRawData]
    for j in range(len(raw)-4):
        if raw[j]==0xE8:
            rel=struct.unpack('<i',raw[j+1:j+5])[0]
            site=base+s.VirtualAddress+j
            if site+5+rel==0x53AF40: print(f'  {site:08X} -> 0x53AF40')
