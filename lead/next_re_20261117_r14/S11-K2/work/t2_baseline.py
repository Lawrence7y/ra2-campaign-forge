"""
S11-K2 T2 baseline (discipline '先测基线' / §969):
- raw image-wide count of B8 imm32 C3 (mov eax,imm32; ret) byte pattern in .text
- how many land in the 12 Locomotion classes' vtable slots vs elsewhere
- §972: encoding-form distribution of allocation pushes
"""
from pehelp import rd, sections, IMAGE_BASE, section_of, u32, is_code
import json

# raw byte scan over .text raw bytes
nm,vaoff,vsize,rsize,praw=[s for s in sections() if s[0]=='.text'][0]
blob=rd(IMAGE_BASE+vaoff, rsize)
cnt=0
locs=[]
for i in range(len(blob)-5):
    if blob[i]==0xB8 and blob[i+5]==0xC3:
        cnt+=1
        locs.append(IMAGE_BASE+vaoff+i)
print('raw B8 imm32 C3 candidates in .text =',cnt)

# how many are in any of the 3 interface vtables of the 12 classes (all slots)
J=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S11-K2\EVIDENCE\t1_rtti_enum.json'
obj=json.load(open(J,encoding='utf-8'))
slots=set()
for name,ss in obj['classes'].items():
    for s in ss:
        for i in range(s['slots']):
            slots.add(u32(s['vt']+4*i))
in_slot=sum(1 for a in locs if a in slots)
print('of those, address is a value in a Locomotion vtable slot =',in_slot)
print('  (the 11 GetSize funcs are exactly these; base 0x4C9150 xor-eax-ret is NOT B8)')

# getsize values & where
gs=json.load(open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S11-K2\work\getsize_hits.json'))
print('GetSize funcs (B8 @ off0 slot9):')
for k,v in sorted(gs.items()):
    if v: print('  %-42s %08X size=%d' % (k,v[0][2],v[0][3]))

# §972 encoding distribution
mp=json.load(open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S11-K2\work\getsize_closure.json'))
from pehelp import disasm
from capstone.x86 import X86_OP_IMM
n6a=0;n68=0
for m in mp:
    for ins in disasm(m['ci'],0xD0):
        if ins.mnemonic=='push' and ins.operands and ins.operands[0].type==X86_OP_IMM:
            v=ins.operands[0].imm&0xffffffff
            if 0x20<=v<=0x1000:
                n6a+= ins.bytes.hex().startswith('6a')
                n68+= ins.bytes.hex().startswith('68')
                break
print('alloc push enc: 6A imm8=%d, 68 imm32=%d (imm32-only would miss %d/%d)'%(n6a,n68,n6a,n6a+n68))
