"""Print disassembly context around selected relative offsets for verifying ③b features."""
import sys, json
CFG=json.load(open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S05_KPROVED3\work\cfg_features.json"))

def ctx(k, offs, before=6, after=10):
    x=CFG[k]; body=x['body']
    idx={int(o.replace('+0x',''),16):i for i,(o,m,op,hx) in enumerate(body)}
    print("="*90); print(f"{k} {x['name']}")
    for off in offs:
        print(f"--- around +0x{off:04X} ---")
        i=idx.get(off)
        if i is None:
            # nearest
            ks=sorted(idx)
            i=idx[min(ks,key=lambda z:abs(z-off))]
        for o,m,op,hx in body[max(0,i-before):i+after]:
            print(f"  {o:>9}  {m:<8} {op}")
    print()

# 006F3330: errcmp 189, 1144; backedge 1149 target
ctx('006F3330',[0xBD,0x478,0x47D,0x4CD])
# 006FC0B0: errcmp 1815(0x717), 2172(0x87C), 2183(0x887), 2219(0x8AB)
ctx('006FC0B0',[0x717,0x87C,0x887,0x8AB],before=4,after=8)
# 006FFEC0: errcmp 979(0x3D3); backedges 505(0x1F9),568(0x238),578(0x242)
ctx('006FFEC0',[0x1F9,0x238,0x242,0x3D3],before=5,after=9)
# 00704350: errcmp 424(0x1A8),469(0x1D5),513(0x201); backedges 1463(0x5B7)->? 1480(0x5C8) jl->1463; 1493(0x5D5),1593(0x639)
ctx('00704350',[0x1A8,0x1D5,0x201,0x5B7,0x5C8,0x5D5,0x639],before=4,after=8)
