"""s3: dump detailed disassembly + ③b evidence for candidates with loops/error paths."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from core import Bin, disasm_window, holding_tables, build_rtti
from capstone.x86 import X86_OP_MEM, X86_OP_IMM

HERE = os.path.dirname(__file__)
b = Bin()
rtti = build_rtti(b)

# Candidates with loops or error paths from s2
CAND = ['004D9920','004DB250','00517CC0','006F3D60',  # loops
        '004D9C10','004DA2B0','004DBAD0','006FB010','00708E00','007099E0',  # error paths
        '0070E140','0070E1A0','004DC030','004DBED0','006F77B0','006F9DD0',  # more EP / others
        '005F5E80','006F3AD0','004D8F40','004D55C0','004D55F0']

os.makedirs(os.path.join(HERE, '..', 'EVIDENCE', 'disasm'), exist_ok=True)
for e in CAND:
    ea = int(e, 16)
    insns = disasm_window(b, ea, max_bytes=16384)
    lines = []
    for ins in insns:
        lines.append(f'{ins.address:08X} +{ins.address-ea:04X}  {ins.bytes.hex():<20s} {ins.mnemonic:<8s} {ins.op_str}')
    open(os.path.join(HERE,'..','EVIDENCE','disasm',f'{e}.txt'),'w',encoding='utf-8').write('\n'.join(lines))
    print(e, 'lines', len(lines))
print('done')
