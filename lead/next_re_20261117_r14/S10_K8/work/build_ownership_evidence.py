import datetime, hashlib, struct, pefile
from capstone import *
EXE=r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
OUT=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10_K8\EVIDENCE\OWNERSHIP_004E0E80.txt'
pe=pefile.PE(EXE); base=pe.OPTIONAL_HEADER.ImageBase; data=pe.__data__
def off(va): return pe.get_offset_from_rva(va-base)
def u32(va): return struct.unpack_from('<I',data,off(va))[0]
def cstr(va):
    o=off(va); e=data.find(b'\x00',o); return data[o:e].decode('ascii','replace')
md=Cs(CS_ARCH_X86,CS_MODE_32); md.skipdata=True
L=[]
def w(s=''): L.append(s)
def dis(start,size,indent='  '):
    w(indent+'RAW '+data[off(start):off(start)+size].hex())
    for i in md.disasm(data[off(start):off(start)+size],start):
        w(indent+'%08X  %-24s %s'%(i.address,i.bytes.hex(),i.mnemonic+' '+i.op_str))
w('S10-K8 004E0E80 OWNERSHIP-PENDING EVIDENCE')
w('SAMPLE='+datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat())
w('EXE_SHA256='+hashlib.sha256(open(EXE,'rb').read()).hexdigest().upper())
w('=== ROW 004E0E80 ===')
vt=0x7E920C; col=u32(vt-4); td=u32(col+0xC)
w('VT %08X COL=%08X TD=%08X NAME=%r'%(vt,col,td,cstr(td+8)))
dis(0x4E0E80,0x4A)
text=[s for s in pe.sections if s.Name.rstrip(b'\x00')==b'.text'][0]
t0=base+text.VirtualAddress
hits=[]
for i in md.disasm(data[text.PointerToRawData:text.PointerToRawData+text.SizeOfRawData],t0):
    if i.mnemonic=='call' and i.op_str.startswith('0x'):
        try: v=int(i.op_str,16)
        except ValueError: continue
        if v==0x4E0E80: hits.append('%08X'%i.address)
w('Direct E8 callers (%d): %s'%(len(hits),','.join(hits)))
w('OWNERSHIP: coverage_README assigns container template instances to S22; D-37 is still pending. Per Lead, delta temporarily keeps S10 and marks 归属待 D-37; no final ownership decision is made here.')
open(OUT,'w',encoding='utf-8',newline='\n').write('\n'.join(L)+'\n')
print('WROTE',OUT,'lines',len(L))
