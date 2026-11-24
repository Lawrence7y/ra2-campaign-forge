"""Detailed dump for 004D5690 / 004D85D0 / 006F3AD0 / 004DB3C0 / 004DBAD0."""
from re_core import PE
from func_analyze import disasm_range, load_a_rows

pe=PE()
rows={int(r['entry'],16):r for r in load_a_rows()}
TARGETS=[0x004D5690,0x004D85D0,0x006F3AD0,0x004DB3C0,0x004DBAD0]
for e in TARGETS:
    r=rows[e]; hi=int(r['ext_hi'],16)
    insns=disasm_range(pe,e,hi)
    print(f'=========== {e:08X} {r["name"]} body to {hi:08X} n={len(insns)}')
    # dump all (cap at 260 lines) with backward-jump markers
    for ins in insns[:300]:
        off=ins.address-e; m=ins.mnemonic; ops=ins.op_str
        mark=''
        if m.startswith('j') or m.startswith('ret') or m=='call':
            # mark backward
            import re as _re
            mm=_re.search(r'0x([0-9a-fA-F]+)',ops)
            if mm and m.startswith('j'):
                t=int(mm.group(1),16)
                if t<=ins.address: mark=' <BACK'
        print(f'  {ins.address:08X} +{off:04x}: {m:6s} {ops}{mark}')
    print(f'  ... (total {len(insns)} insns)')
    print()
