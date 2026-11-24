from pathlib import Path
import sys,re
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,str(Path(__file__).resolve().parent))
from pe_common import PE, IMAGE_BASE, read_va, containing_func, ROOT
from capstone import Cs,CS_ARCH_X86,CS_MODE_32,x86_const
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True; md.skipdata=True
text=None
for s in PE.sections:
    if s.Name.rstrip(b'\x00').decode()=='.text': text=s
base=IMAGE_BASE+text.VirtualAddress
size=text.SizeOfRawData
code=read_va(base,size)
targets=set(int(a,16) for a in sys.argv[1:]) if len(sys.argv)>1 else set([0x006D0F00,0x006D6070,0x006E1830,0x006E4790,0x006E47C0,0x006E6310,0x006EA3E0,0x006F1920,0x0070F120,0x00721270,0x00727AA0,0x0072DDB0,0x0072DEF0,0x00751590,0x00752460,0x00763610,0x00763690])
# coverage names
cov={}
p=ROOT/'lead'/'next_re_20261117_r14'/'COVERAGE'/'coverage.tsv'
with p.open('r',encoding='utf-8-sig',errors='replace') as f:
    for ln in f:
        r=ln.rstrip('\r\n').split('\t')
        if r and re.fullmatch(r'[0-9a-fA-F]{8}',r[0].strip()): cov[int(r[0],16)]=r[2] if len(r)>2 else ''
def nm(e): return cov.get(e,'')
lines=[]; total=0; skipped=0
for ins in md.disasm(code,base):
    total+=1
    if ins.id==0: skipped+=1; continue
    if ins.id in (x86_const.X86_INS_CALL,x86_const.X86_INS_JMP) and ins.operands and ins.operands[0].type==x86_const.X86_OP_IMM:
        t=ins.operands[0].imm
        if t in targets:
            cf=containing_func(ins.address)
            cfs='NONE' if cf is None else f'{cf[0]:08X}+{cf[1]} (name={nm(cf[0])})'
            lines.append(f'{t:08X}\t{ins.mnemonic}\t{ins.address:08X}\t{cfs}\t{ins.bytes.hex()}')
out=Path(__file__).resolve().parents[1]/'EVIDENCE'/'call_xrefs_residual_targets.tsv'
out.write_text(f'# total_instructions {total} skipped {skipped}\n'+'\n'.join(lines)+'\n',encoding='utf-8')
from collections import Counter
c=Counter(l.split('\t')[0] for l in lines)
print('wrote',out,'total',total,'skipped',skipped,'hits',len(lines))
for t in sorted(targets): print(f'{t:08X} {c[t]}')
for l in lines: print(l)
