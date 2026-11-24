"""Detailed ring dump for the 10 STRICT candidates (to select final 8).
Card S05-KPROVED3."""
import sys, os, json, pickle, struct
sys.path.insert(0, os.path.dirname(__file__))
from pe_helpers import *

CFG=json.load(open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S05_KPROVED3\work\cfg_features.json"))
HOLD=json.load(open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S05_KPROVED3\work\rtti_holders.json"))
D=pickle.load(open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S05_KPROVED3\work\call_sites.pkl",'rb'))
call_sites=D['call_sites']

CAND=['005F9720','006F3330','006F8DF0','006FC0B0','006FFEC0','00703860','00704350','0070BF50','00712170','00716150']

for k in CAND:
    x=CFG[k]; f=x['features']; e=int(k,16)
    print("="*100)
    print(f"ENTRY {k}  name={x['name']}  nins={x['nins']} extent {x['lo']}..{x['hi']}  16Balign={e%16==0}")
    hs=HOLD.get(k,[])
    print(f"  ② holders={len(hs)}:")
    for h in hs:
        print(f"      vt={h['vt']} slot={h['slot']:>3} col={h['col']} {h['name']}")
    print(f"     DV/V trap check: DV={sum('DynamicVector' in h['name'] for h in hs)} V={sum('?$Vector' in h['name'] and 'Dynamic' not in h['name'] for h in hs)}")
    print(f"  ③b backedges({len(f['backedges'])}): {f['backedges'][:20]}")
    print(f"  ③b jumptables({len(f['jumptables'])}): {f['jumptables'][:10]}")
    print(f"  ③b errcmp(-1)({len(f['errcmp'])}): {f['errcmp'][:20]}")
    print(f"  ③b memwrites({len(f['memwrites'])}): first20={f['memwrites'][:20]}")
    print(f"  ③b guards({len(f['guards'])}): first12={f['guards'][:12]}")
    sites=call_sites.get(e,[])
    lo=int(x['lo'],16); hi=int(x['hi'],16)
    valid=[]
    for s in sites:
        b=bytes_at(s,5); rel=struct.unpack('<i',b[1:5])[0]; tgt=s+5+rel
        ok=(b[0]==0xE8 and tgt==e and not(lo<=s<hi) and s!=e)
        if ok: valid.append(s)
    print(f"  ④ direct sites total={len(sites)} valid={len(valid)}: {[f'{s:08X}' for s in valid[:12]]}")
