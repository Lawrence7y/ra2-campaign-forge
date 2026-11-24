"""Verify container vtable install -> Find slot4 returns -1; verify 4-anchor hosts not destructors."""
from re_lib import *
out=[]
def P(s=''):
    out.append(str(s)); print(s)

P('=== CONTAINER VTABLE INSTALL POINTS (executor hints, independently verified) ===')
# claim: global <- vtable via mov [global], imm32
installs=[(0x00B0F658,0x007E91EC,0x007255ED),(0x00B0F658,0x007E920C,0x00725618),
          (0x00B0F1A0,0x007F550C,0x0071E63D),(0x00B0F1A0,0x007F552C,0x0071E668),
          (0x00A8EAE8,0x007E9BE4,0x004E65FD),(0x00A8EAE8,0x007E9C04,0x004E6628),
          (0x00B0F670,0x007E91EC,None),(0x00B0F708,0x007E9BE4,None)]
for g,vt,hint in installs:
    P('global %08X <- vt %08X hint_instr=%s'%(g,vt,'%08X'%hint if hint else '?'))
    # find all instrs writing vt imm32 anywhere, esp near globals used
    for imm_at,found in find_instr_for_imm(vt) if False else []:
        pass
    # direct: scan text for mov [abs], vt
    pat=vt.to_bytes(4,'little'); data=bytes_at(TEXT_VA,TEXT_END-TEXT_VA); start=0
    while True:
        i=data.find(pat,start)
        if i<0: break
        imm_at=TEXT_VA+i
        # check if preceding bytes reference global g (c7 05 <abs> <imm>)
        ctx=bytes_at(max(TEXT_VA,imm_at-8),8)
        P('   imm32@%08X ctx=%s'%(imm_at,ctx.hex()))
        start=i+1
    # slot4 of vt
    if mapped(vt,0x14):
        P('   vt slot4(+0x10)=%08X'%u32(vt+0x10))
    P()

P('=== 4-ANCHOR HOST FULL CLASSIFICATION (longer window, check dtor signature) ===')
anchors=[0x006DD036,0x006E4E07,0x006E5B8E,0x0071E6C1,0x00725FCE,0x00726CD2]
for a in anchors:
    ins=disasm_one(a)
    P('anchor %08X : %s %s [%s]'%(a,ins.mnemonic,ins.op_str,ins.bytes.hex()))
    # scan 0x200 bytes around for dtor signature
    lo=max(TEXT_VA,a-0x10)
    win=disasm(a,0x120)
    sig=[t for aa,m,o,b,t in win if (m=='call' and '0x7c8b3d' in o) or (m=='test' and 'byte ptr' in o and ', 1' in o)]
    P('   dtor-sig in +0x120 window: %s'%(sig if sig else 'NONE'))
P()

P('=== SECOND-VARIANT FIND full bodies ===')
for fva in [0x004E0440,0x0071FD20,0x004EA540]:
    P('Find %08X:'%fva)
    for a,m,o,b,t in disasm(fva,0x80):
        P('  '+t)
        if m.startswith('ret'): break
    P()

open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT18\work\verify3.txt','w',encoding='utf-8').write('\n'.join(out))
print('WROTE verify3.txt')
