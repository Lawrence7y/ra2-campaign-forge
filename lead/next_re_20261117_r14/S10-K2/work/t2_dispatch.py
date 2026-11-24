"""
S10-K2 T2-dispatch: re-derive Mission dispatch table (32 entries) from bytes,
map mission index -> vtable slot via stub disassembly. Verify stub step and count.
No atlas for discovery. capstone skipdata=True.
"""
import os, json
from pehelp import (IMAGE_BASE, rd, u32, sections, section_of, is_code, disasm)
from capstone.x86 import X86_OP_MEM

OUT = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10-K2'
EVID = os.path.join(OUT,'EVIDENCE')
L=[]
def P(s=''):
    L.append(str(s)); print(s)

TBL=0x5B34E8
P('===== T2 DISPATCH TABLE @ %08X (32 entries) =====' % TBL)
stubs=[u32(TBL+4*i) for i in range(32)]
P('entry[0..31] = %s' % ', '.join('%08X'%s for s in stubs))
P('entry[32] (past end) = %08X' % u32(TBL+128))
# stub region: each stub calls [vptr+slot] where slot disp in 0x204..0x270
# find the call [reg+disp] inside each stub (bounded by next stub or 0x80 bytes)
def slot_of_stub(va, limit=0x100):
    code=rd(va,limit)
    from capstone import Cs, CS_ARCH_X86, CS_MODE_32
    md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True; md.skipdata=True
    found=[]
    for ins in md.disasm(code,va):
        if ins.mnemonic in ('call','jmp') and ins.operands and ins.operands[0].type==X86_OP_MEM:
            m=ins.operands[0].mem
            disp=m.disp
            if 0x200<=disp<=0x280:
                found.append((ins.address,ins.mnemonic,disp,disp//4,ins.bytes.hex()))
        if ins.mnemonic=='ret' and found: break
    return found

MISSION_NAMES=['Sleep','Attack','Move','QMove','Retreat','Guard','Sticky','Enter',
 'Capture','Eaten','Harvest','Area Guard','Return','Stop','Ambush','Hunt','Unload',
 'Sabotage','Construction','Selling','Repair','Rescue','Missile','Harmless','Open',
 'Patrol','Paradrop Approach','Paradrop Overfly','Wait','Attack Move',
 'Spyplane Approach','Spyplane Overfly']

P('\n===== MISSION ID -> SLOT (from stub call [vptr+disp]) =====')
rows=[]
for i,stub in enumerate(stubs):
    found=slot_of_stub(stub)
    if not found:
        P('  mission[%2d] %-20s stub=%08X : NO CALL FOUND' % (i,MISSION_NAMES[i],stub))
        rows.append(dict(mid=i,name=MISSION_NAMES[i],stub='%08X'%stub,slot=None))
    else:
        # usually exactly one
        for (a,mn,disp,slot,bb) in found[:1]:
            P('  mission[%2d] %-20s stub=%08X : %s @%08X [%s] disp=0x%X -> v[%d]' %
              (i,MISSION_NAMES[i],stub,mn,a,bb,disp,slot))
            rows.append(dict(mid=i,name=MISSION_NAMES[i],stub='%08X'%stub,slot=slot,call='%08X'%a,disp='0x%X'%disp))

# Also dump full disasm of first 3 stubs + one all-stub-mission stub to verify
P('\n===== STUB BODY SAMPLES =====')
for idx in [0,1,2,12,13]:
    stub=stubs[idx]
    P('\n-- mission[%d] %s stub %08X --' % (idx,MISSION_NAMES[idx],stub))
    for ins in disasm(stub,0x90):
        P('  %s' % ('%08X  %-20s %-6s %s'%(ins.address,ins.bytes.hex(),ins.mnemonic,ins.op_str)))
        if ins.mnemonic=='ret': break

with open(os.path.join(EVID,'t2_dispatch.txt'),'w',encoding='utf-8') as f: f.write('\n'.join(L)+'\n')
with open(os.path.join(EVID,'t2_dispatch.json'),'w') as f: json.dump(rows,f,indent=2)
print('\nWROTE t2_dispatch.txt/.json')
