"""Full ④ direct-site verification + thiscall ecx source trace for the 8 delivered rows.
Card S05-KPROVED3."""
import sys, os, json, pickle, struct
sys.path.insert(0, os.path.dirname(__file__))
from pe_helpers import *

CFG=json.load(open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S05_KPROVED3\work\cfg_features.json"))
D=pickle.load(open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S05_KPROVED3\work\call_sites.pkl",'rb'))
call_sites=D['call_sites']; insns=D['insns']; addr2i=D['addr2i']

ROWS=['006F3330','006F8DF0','006FC0B0','006FFEC0','00704350','0070BF50','00712170','00716150']

def insns_around(site, before=8):
    i=addr2i.get(site)
    if i is None: return []
    return insns[max(0,i-before):i+1]

summary={}
for k in ROWS:
    e=int(k,16); x=CFG[k]; lo=int(x['lo'],16); hi=int(x['hi'],16)
    sites=call_sites.get(e,[])
    print("="*95); print(f"{k} {x['name']} extent {lo:08X}..{hi:08X}")
    val=[]
    for s in sites:
        b=bytes_at(s,5); rel=struct.unpack('<i',b[1:5])[0]; tgt=s+5+rel
        inside=lo<=s<hi; selflp=(s==e); ok=(b[0]==0xE8 and tgt==e and not inside and not selflp)
        ctx=insns_around(s,6)
        ecx=[f"{a:08X}:{m} {o}" for a,sz,m,o,bb in ctx if ('ecx' in o or m.startswith('mov'))]
        print(f"  site {s:08X} bytes={b.hex()} rel={rel} tgt={tgt:08X} inside={inside} self={selflp} OK={ok}")
        print(f"     ctx: "+" | ".join(f"{a:08X} {m} {o}" for a,sz,m,o,bb in ctx))
        if ok: val.append(s)
    summary[k]=dict(n_total=len(sites),n_valid=len(valid) if False else len(val),
                    sites=[f'{s:08X}' for s in val], extent_lo=x['lo'], extent_hi=x['hi'])
json.dump(summary,open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S05_KPROVED3\work\site_verify.json",'w'),indent=1)
print("\nSUMMARY:",json.dumps(summary,indent=1))
