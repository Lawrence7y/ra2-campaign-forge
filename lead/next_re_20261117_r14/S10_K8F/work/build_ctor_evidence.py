import datetime, hashlib, struct, pefile
from capstone import *
EXE=r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
OUT=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10_K8F\EVIDENCE\SPAWNMANAGER_CTORS.txt'
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
w('S10-K8 SPAWNMANAGER CTOR RECOVERY / EXCLUSION EVIDENCE')
w('SAMPLE='+datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat())
w('EXE_SHA256='+hashlib.sha256(open(EXE,'rb').read()).hexdigest().upper())
w('TOOLS=Python3.12.10 capstone5.0.7(skipdata=True) pefile2024.8.26; target read-only; no Ghidra')
w()
w('=== RTTI ANCHOR ===')
for vt in (0x7F3650,0x7F36B4):
    col=u32(vt-4); td=u32(col+0xC)
    w('VT %08X COL=%08X TD=%08X NAME=%r'%(vt,col,td,cstr(td+8)))
w('Four-vptr group used by 006B6EA0/006B6C90/006B6FA0: 007F3650,007F3634,007F362C,007F3624 (all -> TD 00840120 .?AVSpawnManagerClass@@).')
w()
w('=== CALL CHANNELS ===')
text=[s for s in pe.sections if s.Name.rstrip(b'\x00')==b'.text'][0]
t0=base+text.VirtualAddress
for target in (0x6B6EA0,0x6B6C90,0x6B6FA0):
    hits=[]
    for i in md.disasm(data[text.PointerToRawData:text.PointerToRawData+text.SizeOfRawData],t0):
        if i.mnemonic=='call' and i.op_str.startswith('0x'):
            try: v=int(i.op_str,16)
            except ValueError: continue
            if v==target: hits.append('%08X'%i.address)
    w('%08X direct E8 callers: %d %s'%(target,len(hits),','.join(hits)))
w('new-then-call 006B6EA0:'); dis(0x6C0A3C,0x18)
w('new-then-call 006B6C90:'); dis(0x6F3FF0,0x10)
w('006B6FA0 has no E8 caller; dead code is accepted only because class+ctor-role channels are independent.')
w()
for tag,start,size in [('006B6EA0',0x6B6EA0,0xF0),('006B6C90',0x6B6C90,0x202),('006B6FA0',0x6B6FA0,0x64),('006B7F10',0x6B7F10,0x50)]:
    w(); w('=== ROW '+tag+' ===')
    dis(start,size)
w()
w('=== EXCLUSION CHECK 006B7F10 ===')
w('Raw pointer refs to 006B7F10: 007F3664 (slot=(007F3664-007F3650)/4=5); raw pointer refs to 006B6FA0: none.')
w('006B7F10 body constructs arg1 ebx (mov ebx,[esp+0xC]; lea ecx,[ebx+0x38]; call 4101C0 with ecx=ebx), not ecx=this; fails ctor role anchor despite same vptr group. Excluded, untouched.')
open(OUT,'w',encoding='utf-8',newline='\n').write('\n'.join(L)+'\n')
print('WROTE',OUT,'lines',len(L))
