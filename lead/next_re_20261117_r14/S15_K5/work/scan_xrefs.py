from pathlib import Path
import sys, struct, re
sys.stdout.reconfigure(encoding='utf-8')
from pe_common import PE, IMAGE_BASE, read_va, va_to_off, off_to_va, containing_func
sys.path.insert(0, str(Path(__file__).resolve().parent))
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
md=Cs(CS_ARCH_X86, CS_MODE_32); md.detail=True; md.skipdata=True
args=sys.argv[1:]
if not args:
    args=['006D0F00','006D6070','006E1830','006E4790','006E47C0','006E6310','006EA3E0','006F1920','0070F120','00721270','00727AA0','0072DDB0','0072DEF0','00751590','00752460','00763610','00763690']
targets=[int(a,16) if not a.startswith('0x') else int(a,16) for a in args]
data=PE.__data__
lines=[]
for va in targets:
    needle=struct.pack('<I',va)
    hits=[]; pos=0
    while True:
        i=data.find(needle,pos)
        if i<0: break
        hva,sec=off_to_va(i)
        hits.append((i,hva,sec)); pos=i+1
    lines.append(f'===== target {va:08X} raw_dword_hits {len(hits)} =====')
    for off,hva,sec in hits:
        lines.append(f'raw fileoff=0x{off:X} va={hva:08X} sec={sec}')
        if sec != '.text' or hva is None: continue
        # local instruction-boundary candidates: start up to 15 bytes before hit, one instruction must cover hit and reference va
        for delta in range(15,-1,-1):
            start=hva-delta
            code=read_va(start, 32)
            if code is None: continue
            ins=next(md.disasm(code,start,1),None)
            if not ins or ins.size<=delta: continue
            hitbytes=code[delta:delta+4]
            refs=[]
            for op in ins.operands:
                if op.type==3 and op.imm==va: refs.append('imm')
                if op.type==2 and op.mem.base==0 and op.mem.index==0 and op.mem.disp==va: refs.append('disp')
            if refs:
                cf=containing_func(ins.address)
                cfs='none' if cf is None else f'{cf[0]:08X}+{cf[1]}'
                lines.append(f'  ins {ins.address:08X}: {ins.mnemonic} {ins.op_str} | {" ".join(f"{b:02X}" for b in ins.bytes)} | refs={",".join(refs)} | contains={cfs}')
                break
out=Path(__file__).resolve().parents[1]/'EVIDENCE'/'xrefs_residual_targets.txt'
out.write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('wrote',out,'lines',len(lines))
print('\n'.join(lines[:300]))
