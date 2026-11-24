import datetime, hashlib, struct, pefile
from capstone import *
EXE=r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
OUT=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10_K8\EVIDENCE\QUEUE_DISPATCH_AND_FALSE_KILLS.txt'
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
w('S10-K8 QUEUE DISPATCH / FALSE-KILL RECOVERY EVIDENCE')
w('SAMPLE='+datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat())
w('EXE_SHA256='+hashlib.sha256(open(EXE,'rb').read()).hexdigest().upper())
w('TOOLS=Python3.12.10 capstone5.0.7(skipdata=True) pefile2024.8.26; target read-only; no Ghidra')
w()
w('=== DISPATCH TABLES ===')
for vt in (0x7E22A4,0x7EB058):
    col=u32(vt-4); td=u32(col+0xC); nm=cstr(td+8)
    w('VTABLE %08X COL=%08X TD=%08X NAME=%r'%(vt,col,td,nm))
    for o in (0x1E8,0x1EC): w('  slot +0x%X -> %08X'%(o,u32(vt+o)))
w()
w('=== RING3/4 CHAIN: AircraftClass [v+0x1E8] -> 0041BA90 -> 005B35E0 ===')
w('0041BA90 outer idx bytes @41BAEC[4..31] = '+','.join(str(data[off(0x41BAEC+i)]) for i in range(28)))
w('0041BA90 outer jump table @41BAE4 = '+','.join('%08X'%u32(0x41BAE4+4*i) for i in range(4)))
w('0041BAB2 inner jump table @41BB08 = '+','.join('%08X'%u32(0x41BB08+4*i) for i in range(2)))
w('0041BAB2 inner idx bytes @41BB10[4..31] = '+','.join(str(data[off(0x41BB10+i)]) for i in range(28)))
drop=[c for c in range(4,32) if data[off(0x41BAEC+c-4)]==0]
w('DROP_SET cur='+str(drop)+' ; if [this+0x294]==0 inner index 0 -> 41BADE (pop esi; ret 8): +0xB4/+0xB8 write swallowed')
w('All other cur (or [this+0x294]!=0) -> 41BAD3 -> 005B35E0.')
dis(0x41BA90,0x54); dis(0x41BAB2,0x21); dis(0x41BAD3,0x0B); dis(0x41BADE,0x06)
w()
w('=== BASE QueueMission 005B35E0 conditional write ===')
w('Early-outs: cur==0x1C&&id==5, cur==0x13, id==-1, or cur==id&&queued!=-1. Only otherwise writes +B4=id and clears +B8.')
dis(0x5B35E0,0x63)
w()
w('=== target=1 promotion chain 0041B870 -> 005B3570 ===')
w('0041B870 clears [this+0x6D2] unless cur==0x1E, then jumps to 005B3570. 005B3570 promotes +B4 -> +AC and clears +B4 unless queued==-1.')
dis(0x41B870,0x15); dis(0x5B3570,0x62)
rows=[
 ('004DF320',[(0x004DF320,0x78)]),
 ('004DF3A0',[(0x004DF3A0,0x110)]),
 ('006F4960',[(0x006F4960,0xE0)]),
 ('004DFB70',[(0x004DFB70,0x140)]),
 ('004DFCB0',[(0x004DFCB0,0x150)]),
 ('004DFE00',[(0x004DFE00,0x140)]),
]
for name,ranges in rows:
    w(); w('=== ROW '+name+' ===')
    for a,n in ranges: dis(a,n)
open(OUT,'w',encoding='utf-8',newline='\n').write('\n'.join(L)+'\n')
print('WROTE',OUT,'lines',len(L))
