"""Precisely list backward conditional jumps and their loop bodies for 004D5690."""
from re_core import PE
from func_analyze import disasm_range, load_a_rows
import re
pe=PE()
rows={int(r['entry'],16):r for r in load_a_rows()}
for e in [0x4D5690]:
    hi=int(rows[e]['ext_hi'],16)
    insns=disasm_range(pe,e,hi)
    for i,ins in enumerate(insns):
        ops=ins.op_str
        if ins.mnemonic.startswith('j'):
            mm=re.search(r'0x([0-9a-fA-F]+)',ops)
            if mm:
                t=int(mm.group(1),16)
                if t<=ins.address and t>=e:
                    print(f'BACK JUMP at {ins.address:08X} +{ins.address-e:04x}: {ins.mnemonic} {ops} -> {t:08X} (+{t-e:04x})')
                    # print loop body from t to ins.address (cap 40)
                    for j in range(i-40,i+1):
                        if j<0: continue
                        x=insns[j]
                        print(f'   {x.address:08X} +{x.address-e:04x}: {x.mnemonic} {x.op_str}')
                    print('---')
