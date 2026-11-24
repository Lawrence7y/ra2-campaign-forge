from pathlib import Path
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,str(Path(__file__).resolve().parent))
from pe_common import read_va, atlas_entries
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True; md.skipdata=True
REQUESTS=[
 (0x6DD300,0x6DD3B0,0x6DD570),
 (0x6DD5B0,0x6DD600,0x6DD700),
 (0x7514D0,0x7514D0,0x751590+0x40),
 (0x752480,0x752460,0x7524D0),
 (0x753330,0x753330,0x753390),
]
lines=[]
for start,lo,hi in REQUESTS:
    lines.append(f'===== region from {start:08X} slice {lo:08X}..{hi:08X} =====')
    code=read_va(start,hi-start)
    for ins in md.disasm(code,start):
        if lo<=ins.address<hi:
            lines.append(f'{ins.address:08X}: {ins.mnemonic:8s} {ins.op_str}')
out=Path(__file__).resolve().parents[1]/'EVIDENCE'/'save_load_call_sites.txt'
out.write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('\n'.join(lines))
