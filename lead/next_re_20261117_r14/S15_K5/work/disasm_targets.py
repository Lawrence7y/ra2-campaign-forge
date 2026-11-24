from pathlib import Path
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(Path(__file__).resolve().parent))
from pe_common import read_va, atlas_entries, containing_func
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
md=Cs(CS_ARCH_X86, CS_MODE_32); md.detail=True; md.skipdata=True
atlas=atlas_entries()
args=sys.argv[1:]
if not args:
    args=['006D0F00','006D6070','006E1830','006E4790','006E47C0','006E6310','006EA3E0','006F1920','0070F120','00721270','00727AA0','0072DDB0','0072DEF0','00751590','00752460','00763610','00763690']
outdir=Path(__file__).resolve().parents[1]/'EVIDENCE'/'disasm_targets'
outdir.mkdir(parents=True,exist_ok=True)
all_lines=[]
for a in args:
    va=int(a,16) if not a.startswith('0x') else int(a,16)
    size=atlas.get(va)
    if size is None:
        lines=[f'entry {va:08X} NOT_IN_ATLAS']
    else:
        code=read_va(va,size)
        lines=[f'entry {va:08X} atlas_size {size}']
        n=0; skipped=0
        for ins in md.disasm(code,va):
            if ins.id==0: skipped+=1
            lines.append(f'{ins.address:08X}: {ins.mnemonic:8s} {ins.op_str}')
            n+=1
        lines.insert(1,f'instructions {n} skipped {skipped}')
    (outdir/f'{va:08X}.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    all_lines += lines + ['']
allout=Path(__file__).resolve().parents[1]/'EVIDENCE'/'disasm_residual_targets.txt'
allout.write_text('\n'.join(all_lines),encoding='utf-8')
print('wrote',outdir,'and',allout,'lines',len(all_lines))
