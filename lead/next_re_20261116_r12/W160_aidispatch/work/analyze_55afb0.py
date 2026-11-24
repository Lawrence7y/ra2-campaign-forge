"""Independent stack-frame and loop analysis for 0x55AFB0 (task A/C/E)."""
import json, os, re
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86_const import X86_OP_MEM, X86_REG_ESP
EV=r"D:\Project\ra2-campaign-forge\lead\next_re_20261116_r12\W160_aidispatch\EVIDENCE"
BIN=r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
import pefile
pe=pefile.PE(BIN, fast_load=True)
ts=next(s for s in pe.sections if s.Name.rstrip(b'\0')==b'.text')
base=0x400000+ts.VirtualAddress; data=open(BIN,'rb').read()
blob=data[ts.PointerToRawData:ts.PointerToRawData+ts.SizeOfRawData]
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True; md.skipdata=True

# linear disasm from atlas entry 0x55AFB0, size 1901 decimal
start=0x55AFB0; size=1901
ins=list(md.disasm(blob[start-base:start-base+size],start))
with open(os.path.join(EV,'W160_55AFB0_disasm.txt'),'w',encoding='utf-8') as f:
    for x in ins: f.write(f'{x.address:08X}  {x.bytes.hex():<20} {x.mnemonic:<8} {x.op_str}\n')

# stack offsets (esp-based) used in function
offs=set()
for x in ins:
    for op in x.operands:
        if op.type==X86_OP_MEM and op.mem.base==X86_REG_ESP:
            offs.add(op.mem.disp & 0xffffffff)
print('ESP offsets dec:',sorted(offs),'hex:',[hex(o) for o in sorted(offs)])
print('max offset:',hex(max(offs)),'stack param threshold: 0x38')

# all call [..+0x5c] sites in this function
for i,x in enumerate(ins):
    if x.mnemonic=='call' and x.operands and x.operands[0].type==X86_OP_MEM and (x.operands[0].mem.disp&0xffffffff)==0x5c:
        # print ±20 instructions context
        print(f'\n=== slot-5C site {x.address:08X} ===')
        for y in ins[max(0,i-18):i+9]:
            print(f'{y.address:08X} {y.mnemonic:<8} {y.op_str}')

# backedges: any jump target <= source within function
print('\n=== backedges ===')
for x in ins:
    if x.group(1):  # jump group (CS_GRP_JUMP == 1)
        try: t=int(x.op_str,16)
        except: continue
        if t<=x.address and start<=t<start+size:
            print(f'{x.address:08X} {x.mnemonic} -> {t:08X}')
