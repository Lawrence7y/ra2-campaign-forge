from re_core import PE
from func_analyze import disasm_range, load_a_rows
pe=PE()
rows={int(r['entry'],16):r for r in load_a_rows()}
e=0x004D94B0; hi=int(rows[e]['ext_hi'],16)
insns=disasm_range(pe,e,hi)
print(f'===== {e:08X} {rows[e]["name"]} n={len(insns)}')
for ins in insns:
    off=ins.address-e
    print(f'  {ins.address:08X} +{off:04x}: {ins.mnemonic} {ins.op_str}')
