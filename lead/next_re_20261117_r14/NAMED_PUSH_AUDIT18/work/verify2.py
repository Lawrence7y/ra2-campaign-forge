"""Classify install-site host functions (ctor/dtor/atexit) and verify container vt slot4 + wrapper full body."""
from re_lib import *

out=[]
def P(s=''):
    out.append(str(s)); print(s)

# install sites (imm32 VA, instruction start = a bit before; search backward for the mov)
def find_instr_for_imm(immva):
    """Find instruction in .text whose imm32 == immva and returns (instr_va, text)."""
    res=[]
    pat=immva.to_bytes(4,'little')
    data=bytes_at(TEXT_VA,TEXT_END-TEXT_VA); start=0
    while True:
        i=data.find(pat,start)
        if i<0: break
        imm_at=TEXT_VA+i
        # try instruction starts imm_at-7..imm_at-1 (mov r/m32,imm32 with modrm+SIB possible)
        found=None
        for back in range(1,8):
            s=imm_at-back
            if s<TEXT_VA: continue
            ins=disasm_one(s)
            if ins and ins.address==s:
                # does this insn's bytes contain immva at imm_at?
                e=s+len(ins.bytes)
                if e==imm_at+4 and immva.to_bytes(4,'little') in ins.bytes:
                    found=(s,ins.mnemonic,ins.op_str,ins.bytes.hex()); break
        res.append((imm_at, found))
        start=i+1
    return res

def classify_host(instr_va):
    """Disassemble window before+after, detect base-ctor call before, dtor signature after."""
    lo=max(TEXT_VA,instr_va-0x60)
    win=disasm(lo,0xC0)
    idx=None
    for i,(a,m,o,b,t) in enumerate(win):
        if a==instr_va: idx=i;break
    before=win[:idx] if idx else []
    after=win[idx:] if idx else []
    has_base_call=[t for a,m,o,b,t in before if m=='call' and ('0x410170' in o or '0x4101c0' in o or '0x410800' in o or '0x410960' in o or '0x7258d0' in o)]
    dtor_sig=[t for a,m,o,b,t in after if ('0x7c8b3d' in o and m=='call') or ('test' in m and 'byte ptr' in o and ', 1' in o)]
    return [t.split('  ',1)[-1] for t in has_base_call], [t.split('  ',1)[-1] for t in dtor_sig], before, after

P('=== INSTALL-SITE HOST CLASSIFICATION (primary vtables) ===')
P()
prim = {
 0x006E3E30:0x007F443C, 0x006E57A0:0x007F44E0, 0x006E6470:0x007F45C4,
 0x0071F930:0x007F5578, 0x0071FA80:0x007F5578,
 0x00726860:0x007F5858, 0x007268D0:0x007F5858, 0x00726950:0x007F5858,
 0x00727BF0:0x007F5904, 0x00727C80:0x007F5904,
}
seen=set()
for e,vt in prim.items():
    if vt in seen: 
        continue
    seen.add(vt)
    P('# vt=%08X (entries: %s)'%(vt,' '.join('%08X'%x for x,v in prim.items() if v==vt)))
    for imm_at,found in find_instr_for_imm(vt):
        if not found:
            P('  imm@%08X  (no clean mov found)'%imm_at); continue
        s,m,o,bx=found
        basecalls,dtor,before,after=classify_host(s)
        P('  instr@%08X  %s %s [%s] ; base-ctor-call-before=%s ; dtor-sig-after=%s'%(
            s,m,o,bx, basecalls if basecalls else 'NONE', dtor if dtor else 'NONE'))
    P()

P('=== WRITE WRAPPER 00410320 FULL BODY (multi-value passthrough) ===')
for a,m,o,b,t in disasm(0x00410320,0x80):
    P('  '+t)
    if m.startswith('ret'): 
        # continue to see multiple rets
        pass
P()

P('=== CONTAINER vptr slot4 (Find) check ===')
# For each container global in the two destructor functions, read vptr and slot4
containers=[0x00B0F658,0x00B0F670,0x00B0F1A0,0x00A8EAE8,0x00B0F708]
for g in containers:
    vptr=u32(g)
    slot4=u32(vptr+0x10) if mapped(vptr,0x14) else None
    P('global %08X vptr=%08X slot4(+0x10)=%s'%(g,vptr,'%08X'%slot4 if slot4 else 'unmapped'))
P()

open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT18\work\verify2.txt','w',encoding='utf-8').write('\n'.join(out))
print('WROTE verify2.txt')
