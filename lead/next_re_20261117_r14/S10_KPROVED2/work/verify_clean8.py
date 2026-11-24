"""Verify ④ sites + inspect ③b loops for the 8 clean-attribution candidates."""
from re_core import PE
from func_analyze import disasm_range, load_a_rows
from call_sweep import full_text_sweep
import re

pe=PE()
insns_all,e8_sites,e8_site_vas,n=full_text_sweep(pe)
rows={int(r['entry'],16):r for r in load_a_rows()}

FINAL=[0x004D7170,0x004D74E0,0x004D7D50,0x004D85D0,0x004DB3C0,0x004D9960,0x004DB690,0x004DF040]

RE_MREAD=re.compile(r'^\w+,\s*(?:byte|word|dword|qword) ptr \[')
RE_MWRITE=re.compile(r'^(?:byte|word|dword|qword) ptr \[')

for e in FINAL:
    r=rows[e]; hi=int(r['ext_hi'],16)
    sites=[s.strip() for s in r['ring4_direct_sites'].split(';') if s.strip()]
    print(f'===== {e:08X} {r["name"]} body[{e:08X},{hi:08X}) sites={sites}')
    for s in sites:
        sv=int(s,16)
        b=pe.bytesva(sv,5)
        rel=int.from_bytes(b[1:5],'little',signed=True) if b else None
        tgt=sv+5+rel if rel is not None else None
        print(f'   site {s}: E8={b[0]==0xE8 if b else False} boundary={sv in e8_site_vas} tgt={tgt:08X} ok={tgt==e} outside={not(e<=sv<hi)}')
    # loops
    insns=disasm_range(pe,e,hi)
    for i,ins in enumerate(insns):
        if ins.mnemonic.startswith('j'):
            mm=re.search(r'0x([0-9a-fA-F]+)',ins.op_str)
            if mm:
                t=int(mm.group(1),16)
                if e<=t<=ins.address:
                    body=insns[max(0,i-45):i]
                    hr=any(x.mnemonic=='mov' and RE_MREAD.search(x.op_str) for x in body)
                    hw=any(x.mnemonic=='mov' and RE_MWRITE.search(x.op_str) for x in body)
                    ha=any(x.mnemonic in ('inc','dec','add','sub') for x in body)
                    if hr and hw and ha:
                        print(f'   LOOP back@{ins.address-e:#x} {ins.mnemonic} -> {t-e:#x}: read+write+advance OK')
    print()
