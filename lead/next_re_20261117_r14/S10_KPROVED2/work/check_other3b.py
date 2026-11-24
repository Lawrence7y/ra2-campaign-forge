from re_core import PE
from func_analyze import disasm_range, load_a_rows
import re
pe=PE()
rows={int(r['entry'],16):r for r in load_a_rows()}
for e in [0x004D94B0,0x004D9C10,0x004DA2B0,0x004DB690]:
    r=rows[e]; hi=int(r['ext_hi'],16)
    if hi-e>20000: hi=e+4000
    insns=disasm_range(pe,e,hi)
    print(f'===== {e:08X} {r["name"]} ext_hi={r["ext_hi"]} n={len(insns)}')
    for ins in insns:
        off=ins.address-e; m=ins.mnemonic; ops=ins.op_str
        if re.search(r'0x8000[0-9a-fA-F]{4}',ops) or (m in ('mov','or','push','cmp') and re.search(r'\b-1\b',ops)):
            print(f'   ERRCODE +{off:#x}: {m} {ops}')
        mm=re.match(r'dword ptr \[\w+[^\]]*\],\s*(0x[0-9a-fA-F]+)',ops)
        if m=='mov' and mm:
            imm=int(mm.group(1),16)
            print(f'   MEMIMM +{off:#x}: mov {ops}  {"VT" if 0x7e0000<=imm<=0x810000 else ""}')
    print()
