"""Step 11: SuperClass charge functions full disassembly + field access inventory."""
import sys, os, re, struct
sys.path.insert(0, os.path.dirname(__file__))
from re_lib import *
b=Bin(); out=[]
emit=out.append
rows,hdr=load_atlas()

funcs=[
 ('ctor',0x6CAF90),('SetOnHold',0x6CB4D0),('Grant',0x6CB560),
 ('SetReadiness',0x6CB820),('ClickFire',0x6CB920),
 ('HasChargeProgressed',0x6CBCA0),('GetCameoChargeState',0x6CBEE0),
 ('SetCharge',0x6CC1E0),('GetRechargeTime',0x6CC260),
 ('SetRechargeTime',0x6CC280),('ResetRechargeTime',0x6CC290),
 ('CanFire',0x6CC360),('Launch',0x6CC390),('ShouldFlashTab',0x6CE1A0),
 ('CalculateChecksum',0x6CE020),
]
# field access regex on op_str: [reg + 0xNN] or [reg - 0xNN]
field_re=re.compile(r'\[(?:e(?:ax|bx|cx|dx|si|di|bp|sp)|[a-z]{3})\s*\+\s*(0x[0-9a-f]+)\]')
for name,va in funcs:
    r=func_containing(rows,va)
    if r and r[0]==va: end=va+r[1]
    else: end=va+0x900  # fallback generous
    ins=disasm_range(b,va,min(end,va+0x2000))
    emit(f"\n===== {name} @ {va:08X} .. {va+(end-va):08X} ({len(ins)} decoded items) =====")
    # list accesses to offsets in 0x00..0xFF (SuperClass fields)
    seen=[]
    for i in ins:
        if i.id==0: continue
        m=field_re.search(i.op_str)
        if m:
            off=int(m.group(1),16)
            if off<=0x100:
                seen.append(f"  {i.address:08X} {i.mnemonic:<7} {i.op_str:<40} [{off:02X}] {i.bytes.hex()}")
        if '0x8871e0' in i.op_str.lower():
            seen.append(f"  RULES {i.address:08X} {i.mnemonic:<7} {i.op_str:<40} {i.bytes.hex()}")
    emit("\n".join(seen[:220]))

text="\n".join(out)
open(os.path.join(os.path.dirname(__file__),'..','EVIDENCE','E11_super_fields.txt'),'w',encoding='utf-8').write(text)
print("wrote",len(text),"bytes")
