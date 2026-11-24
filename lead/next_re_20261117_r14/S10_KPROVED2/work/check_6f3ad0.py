from re_core import PE
from func_analyze import disasm_range
pe=PE()
# dump 0x7dc720 head
print('=== 0x7dc720 ===')
for ins in disasm_range(pe,0x7dc720,0x7dc780)[:20]:
    print(f'  {ins.address:08X}: {ins.mnemonic} {ins.op_str}')
# dump 006F3AD0 tail (last 60 insns)
from func_analyze import load_a_rows
rows={int(r['entry'],16):r for r in load_a_rows()}
e=0x6F3AD0; hi=int(rows[e]['ext_hi'],16)
insns=disasm_range(pe,e,hi)
print(f'=== 006F3AD0 tail (total {len(insns)}) last 70 ===')
for ins in insns[-70:]:
    print(f'  {ins.address:08X} +{ins.address-e:04x}: {ins.mnemonic} {ins.op_str}')
