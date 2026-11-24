"""
S11-K2 T1 CLSID check (independent byte-level, confirm S11-K1 audit):
- .rdata 0x7E9A20..0x7E9B00 GUID array: count 16B GUIDs, find where it ends.
- Are there adjacent function pointers forming a {GUID -> class -> factory} static table? (expect NO)
- registration fn 0x6BB9A0: find push <CLSID ptr> / call <factory ctor> pairs -> mapping lives in CODE.
"""
import struct
from pehelp import u32, rd, disasm, section_of, is_code
from capstone.x86 import X86_OP_IMM

OUT=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S11-K2\EVIDENCE\t1_clsid_check.txt'
L=[]
def P(s=''):
    L.append(str(s)); print(s)

P('=== .rdata GUID region 0x7E9A20..0x7E9B00 (raw dwords) ===')
for va in range(0x7E9A20,0x7E9B00,16):
    d=rd(va,16)
    g1,g2,g3=struct.unpack('<IHH',d[:8])
    tail=d[8:].hex().upper()
    P('%08X  %08X-%04X-%04X-%s'%(va,g1,g2,g3,tail))

P('\n=== search for a STATIC {GUID -> factory ptr} table: any .rdata dword equal to a factory ctor 0x6C3F40..0x6C4E40? ===')
found=0
for va in range(0x7E1000,0x811074-4,4):
    try: v=u32(va)
    except: continue
    if 0x6C3F40<=v<=0x6C5000:
        P('  .rdata %08X -> %08X (factory code ptr)'%(va,v)); found+=1
P('  count = %d (0 => no static factory-pointer table in .rdata)'%found)

P('\n=== registration fn 0x6BB9A0: push <CLSID> + call <factory_ctor> pairs (mapping in CODE) ===')
# CLSID pointers are in .rdata around 0x7E9A30..0x7E9AD0; find push imm where imm in that range
clsids=[0x7E9A30+0x10*i for i in range(11)]
pairs=[]
ins=list(disasm(0x6BB9A0,0x1D00))
for j,i in enumerate(ins):
    try: ops=i.operands
    except: continue
    if i.mnemonic=='push' and ops and ops[0].type==X86_OP_IMM:
        v=ops[0].imm&0xffffffff
        if v in clsids:
            # look ahead for call to factory ctor
            ctor=None
            for k in range(j+1,min(j+30,len(ins))):
                try: o2=ins[k].operands
                except: continue
                if ins[k].mnemonic=='call' and o2 and o2[0].type==X86_OP_IMM:
                    t=o2[0].imm&0xffffffff
                    if 0x6C3F00<=t<=0x6C5000: ctor=t; break
            pairs.append((i.address,v,ctor))
for a,v,c in pairs:
    P('  push CLSID %08X @%08X  -> factory ctor %s'%(v,a,('%08X'%c) if c else '?'))
P('  pairs = %d'%len(pairs))

with open(OUT,'w',encoding='utf-8') as f: f.write('\n'.join(L)+'\n')
print('\nWROTE',OUT)
