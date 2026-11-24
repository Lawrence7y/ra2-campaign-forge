import sys, json
CFG=json.load(open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S05_KPROVED3\work\cfg_features.json"))
def ctx(k, offs, before=8, after=12):
    x=CFG[k]; body=x['body']; idx={int(o.replace('+0x',''),16):i for i,(o,m,op,hx) in enumerate(body)}
    print("="*90); print(f"{k} {x['name']}")
    for off in offs:
        print(f"--- around +0x{off:04X} ---")
        i=idx.get(off)
        if i is None:
            ks=sorted(idx); i=idx[min(ks,key=lambda z:abs(z-off))]
        for o,m,op,hx in body[max(0,i-before):i+after]:
            print(f"  {o:>9}  {m:<8} {op}")
    print()
# 006F8DF0 backedges targets 1020(0x3FC),1518(0x5EE),2429(0x97D),1955(0x7A3),1489(0x5D1),3485(0xDA1),3722(0xE8A)
ctx('006F8DF0',[0x3FC,0x5EE,0x7A3,0xDA1],before=6,after=10)
# 00716150 loop target 94(0x5E)
ctx('00716150',[0x5E,0xA2],before=6,after=14)
# 00703860 backedge target 78(0x4E) - check if ret block
ctx('00703860',[0x4E,0xA0],before=6,after=14)
