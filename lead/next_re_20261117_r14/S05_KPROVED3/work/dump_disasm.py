"""Dump full entry-relative disassembly for the 10 STRICT candidates into work files."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
CFG=json.load(open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S05_KPROVED3\work\cfg_features.json"))
CAND=['005F9720','006F3330','006F8DF0','006FC0B0','006FFEC0','00703860','00704350','0070BF50','00712170','00716150']
OUT=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S05_KPROVED3\work\disasm"
os.makedirs(OUT,exist_ok=True)
for k in CAND:
    x=CFG[k]
    lines=[f"# {k} {x['name']} nins={x['nins']} extent {x['lo']}..{x['hi']}"]
    for off,m,o,hx in x['body']:
        lines.append(f"{off:>9}  {hx:<24} {m:<8} {o}")
    open(os.path.join(OUT,f"DIS_{k}.txt"),'w',encoding='utf-8').write('\n'.join(lines))
    print("wrote",k,len(x['body']))
