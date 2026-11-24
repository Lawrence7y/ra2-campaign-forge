from re_core import PE
from func_analyze import disasm_range, load_a_rows
import re
pe=PE()
rows={int(r['entry'],16):r for r in load_a_rows()}
RE_MREAD=re.compile(r'mov\s+\w+,\s*(?:byte|word|dword|qword) ptr \[')
RE_MWRITE=re.compile(r'mov\s+(?:byte|word|dword|qword) ptr \[')
for e in [0x4D85D0,0x4DB3C0]:
    hi=int(rows[e]['ext_hi'],16)
    insns=disasm_range(pe,e,hi)
    print(f'=== {e:08X} n={len(insns)} ext_hi={hi:08X}')
    for i,ins in enumerate(insns):
        if ins.mnemonic.startswith('j'):
            mm=re.search(r'0x([0-9a-fA-F]+)',ins.op_str)
            if mm:
                t=int(mm.group(1),16)
                if e<=t<=ins.address:
                    body=insns[max(0,i-45):i]
                    hr=[x.op_str for x in body if x.mnemonic=='mov' and RE_MREAD.search(x.op_str)]
                    hw=[x.op_str for x in body if x.mnemonic=='mov' and RE_MWRITE.search(x.op_str)]
                    ha=[x.mnemonic+' '+x.op_str for x in body if x.mnemonic in ('inc','dec','add','sub')]
                    print(f'  BACK at +{ins.address-e:04x} {ins.mnemonic} {ins.op_str}: read={len(hr)} write={len(hw)} adv={len(ha)}')
                    print('     reads:',hr[:3])
                    print('     writes:',hw[:3])
                    print('     adv:',ha[:3])
