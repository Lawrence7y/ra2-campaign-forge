
import sys, struct, json
import pefile
from capstone import *
from capstone.x86 import *

EXE = r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
pe = pefile.PE(EXE, fast_load=True)
pe.parse_data_directories([pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_BASERELOC']])
IB = pe.OPTIONAL_HEADER.ImageBase
# sections
secs=[]
for s in pe.sections:
    secs.append((s.Name.rstrip(b'\0').decode('latin1'), s.VirtualAddress, s.Misc_VirtualSize, s.PointerToRawData, s.SizeOfRawData))

def va2off(va):
    rva = va - IB
    for name,va0,vsz,raw,rsz in secs:
        if va0 <= rva < va0 + max(vsz,rsz):
            return raw + (rva - va0)
    return None

def read(va,n):
    off=va2off(va)
    if off is None: return None
    with open(EXE,'rb') as f:
        f.seek(off); return f.read(n)

def u32(va):
    b=read(va,4)
    return struct.unpack('<I',b)[0] if b and len(b)==4 else None

def cstr(va, n=80):
    b=read(va,n)
    if b is None: return None
    s=b.split(b'\0')[0]
    try: return s.decode('latin1')
    except: return repr(s)

# ⑲ self-check
md=Cs(CS_ARCH_X86,CS_MODE_32)
md.detail=True
ins=list(md.disasm(b'\xff\x10',0x400000))  # call [eax]
op=ins[0].operands[0]
print('SELFCHECK19 has_op_index=', hasattr(op,'index'), 'op.mem.index=', op.mem.index, 'is None?', op.mem.index is None)

targets = {
 '0065CAC0':0x65CAC0, '004324B0':0x4324B0, '00552490':0x552490,
 '006C9890':0x6C9890, '00631CC0':0x631CC0, '0065D150':0x65D150, '00431E80':0x431E80,
}
sizes = {'0065CAC0':111,'004324B0':234,'00552490':346,'006C9890':67,'00631CC0':75,'0065D150':56,'00431E80':131}
out={}
for k,va in targets.items():
    n=sizes[k]
    code=read(va,n)
    out[k]={'va':va,'n':n,'bytes':code.hex(),'ninstr':0,'insns':[]}
    for i in md.disasm(code,va):
        out[k]['insns'].append({'off':i.address-va,'addr':i.address,'bytes':i.bytes.hex(),'mn':i.mnemonic,'op':i.op_str})
    out[k]['ninstr']=len(out[k]['insns'])
with open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S03_C3\EVIDENCE\disasm_verified.json','w') as f:
    json.dump({'imagebase':IB,'sections':secs,'selfcheck19':{'has_op_index':hasattr(op,'index'),'mem_index':op.mem.index},'targets':out},f,indent=1)
for k,v in out.items():
    print('\n###',k,'size',v['n'],'ninstr',v['ninstr'])
    for ins in v['insns']:
        print('  +0x%02X %08X %-24s %s %s'%(ins['off'],ins['addr'],ins['bytes'],ins['mn'],ins['op']))
