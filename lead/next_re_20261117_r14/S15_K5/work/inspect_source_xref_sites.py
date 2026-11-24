from pathlib import Path
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,str(Path(__file__).resolve().parent))
from pe_common import read_va, containing_func
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True; md.skipdata=True
sites=[0x6DE10D,0x6DE68A,0x6E0DC5,0x6E1647,0x4C6E71,0x4C7976,0x4C7A60,0x4C7A87,0x4C7AA9,0x4C7B26,0x4C7F83]
lines=[]
for va in sites:
    cf=containing_func(va); lines.append(f'===== site {va:08X} contains {cf} =====')
    start=va-0x28; code=read_va(start,0x60)
    for ins in md.disasm(code,start):
        mark='>>>' if ins.address<=va<ins.address+ins.size else '   '
        lines.append(f'{mark} {ins.address:08X}: {ins.mnemonic:8s} {ins.op_str}')
out=Path(__file__).resolve().parents[1]/'EVIDENCE'/'source_string_xref_sites.txt'
out.write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('\n'.join(lines))
