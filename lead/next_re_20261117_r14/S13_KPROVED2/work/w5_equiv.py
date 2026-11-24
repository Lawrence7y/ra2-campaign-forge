"""Final verification: E9 tail-jmp equivalent forms of ④ + candidate composition sanity.
Card S13-KPROVED2.
"""
import json
from s13lib import MD, DATA, TEXT_VA, TEXT_VS, va2off

BASE = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13_KPROVED2"
pool = json.load(open(BASE + r'\work\pool.json', encoding='utf-8'))
cands = pool['candidates']
cset = {int(r['entry'],16) for r in cands}

print('=== 47 candidate names ===')
for r in cands:
    print(' ', r['entry'], r['name'])

# E9 jmp rel32 and EB short jmp targets at instruction boundaries (equivalent dispatch form)
raw = DATA(va2off(TEXT_VA), TEXT_VS)
e9hit={}; ebhit={}
for ins in MD.disasm(raw, TEXT_VA):
    if ins.mnemonic == 'jmp' and ins.op_str.startswith('0x'):
        t = int(ins.op_str,16)
        # E9 rel32 vs EB rel8 not distinguished by mnemonic; note the byte
        o = va2off(ins.address)
        b0 = DATA(o,1)[0]
        if t in cset:
            (e9hit if b0==0xE9 else ebhit).setdefault(t,[]).append(ins.address)
print('=== E9 tail-jmp targets hitting candidates ===', [hex(x) for x in e9hit])
print('=== EB short-jmp targets hitting candidates ===', [hex(x) for x in ebhit])

json.dump({'e9':{hex(t):[hex(s) for s in v] for t,v in e9hit.items()},
           'eb':{hex(t):[hex(s) for s in v] for t,v in ebhit.items()}},
          open(BASE + r'\work\ring4_equiv.json','w',encoding='utf-8'), indent=2)
print('wrote work/ring4_equiv.json')
