
"""Detect vptr installs written as  mov [abs], reg  (moffs A3 / 89 05 forms),
which store_imm (C7 05) misses. Traces the source register back a few insns."""
import pefile, capstone, pickle, os, sys
from capstone import *
from capstone.x86 import *
EXE=r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
OUT=os.path.dirname(os.path.abspath(__file__))
pe=pefile.PE(EXE,fast_load=True); IB=pe.OPTIONAL_HEADER.ImageBase
blob=open(EXE,'rb').read()
sec=[x for x in pe.sections if x.Name.decode().rstrip('\x00')=='.text'][0]
SVA=IB+sec.VirtualAddress; SRAW=sec.PointerToRawData; VS=sec.Misc_VirtualSize
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True; md.skipdata=True
insn=[]
for ins in md.disasm(blob[SRAW:SRAW+VS], SVA):
    if ins.id==0: insn.append(None); continue
    insn.append(ins)
print('insns',len(insn),file=sys.stderr)
addrs=[i.address if i else None for i in insn]
idx={a:k for k,a in enumerate(addrs) if a is not None}
found=[]   # (site, vt, destabs, src_reg, loader_site)
for k,ins in enumerate(insn):
    if ins is None: continue
    ops=ins.operands
    if len(ops)==2 and ins.mnemonic.startswith('mov') and ops[0].type==X86_OP_MEM \
       and ops[0].mem.base==0 and ops[0].mem.index==0 and ops[1].type==X86_OP_REG and ops[1].size==4:
        dest=ops[0].mem.disp; reg=ops[1].reg
        # trace back: mov reg, imm  (up to 8 insns, stop at branch/ret)
        for j in range(k-1,max(-1,k-9),-1):
            p=insn[j]
            if p is None: break
            if p.mnemonic.startswith(('ret','jmp','call')): break
            po=p.operands
            if len(po)==2 and p.mnemonic=='mov' and po[0].type==X86_OP_REG and po[0].reg==reg \
               and po[1].type==X86_OP_IMM and 0x400000<=po[1].imm<0xC00000:
                found.append((ins.address,po[1].imm,dest,p.address)); break
print('mov [abs], reg  with vt-immediate traced:',len(found),file=sys.stderr)
pickle.dump(found,open(os.path.join(OUT,'absreg_stores.pkl'),'wb'))
import collections
c=collections.Counter(f[2] for f in found)
print('distinct destination globals',len(c),file=sys.stderr)
print('top dests',[(hex(k),v) for k,v in c.most_common(10)],file=sys.stderr)
if 0x87F7E8 in c:
    print('*** global 0x87F7E8 also written by mov [abs],reg at:',
          [(hex(f[0]),hex(f[1]),hex(f[3])) for f in found if f[2]==0x87F7E8],file=sys.stderr)
else:
    print('*** global 0x87F7E8 NOT written by any mov [abs],reg-with-vt',file=sys.stderr)
