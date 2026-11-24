"""Task 1 step 7: dump raw dwords around candidate vftable addresses; find valid RTTI COL chains."""
import sys, os, struct
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261116_r12\_lead_audit")
import audit_lib as A
sys.path.insert(0, os.path.dirname(__file__))
from wbase import BIN

EVID=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\W175_global8871\EVIDENCE"
out=[]
def P(s=""): out.append(str(s))

cands=[0x7e4db8,0x7e4dd8,0x7e4df8,0x7eabe8,0x7eabc8,0x7eac08,0x7ed90c,0x7f0cfc,0x7f0d3c,0x7eb6d4]
P("=== raw dwords around candidate vftables ===")
for vft in cands:
    words=[]
    for off in range(-0x14,0x10,4):
        try: words.append(BIN.u32(vft+off))
        except Exception: words.append(None)
    P("  vft %08X: %s" % (vft, " ".join("%08X"%(w or 0) for w in words)))

# Proper MSVC RTTI chain: try both vft-4 and vft-8 as COL; validate COL.signature==0
P("\n=== try COL chain validation ===")
def parse_col(col):
    try:
        sig=BIN.u32(col); off=BIN.u32(col+4); cd=BIN.u32(col+8); ti=BIN.u32(col+0xC)
        if sig!=0: return None
        np=BIN.u32(ti+8)
        name=BIN.read(np,100).split(b"\x00")[0]
        return (off,cd,ti,name)
    except Exception:
        return None
for vft in cands:
    for cpos in [vft-4, vft-8]:
        r=parse_col(cpos)
        if r:
            P("  vft=%08X COL@%08X off=%d ti=%08X name=%r"%(vft,cpos,r[0],r[2],r[3]))

# Go reverse: for each RTTI name string in .data, find TypeDescriptor that points to it,
# then find COL pointing to that TD, then find vftable whose [-4]==COL. Print a few class names.
P("\n=== map vftable -> RTTI name by scanning all COLs in .rdata ===")
rdata=BIN.sec(".rdata")
# COL signature=0, +C=typeinfo ptr in .data; scan aligned dwords
name2vft={}
for va in range(rdata["va"], rdata["va"]+rdata["rawsize"]-0x20, 4):
    try:
        sig=BIN.u32(va)
        if sig!=0: continue
        ti=BIN.u32(va+0xC)
        if not (0x812000<=ti<0xB78000): continue
        np=BIN.u32(ti+8)
        name=BIN.read(np,120).split(b"\x00")[0]
        if not name.startswith(b".?A"): continue
        # this va is COL; find vftable that points back to it: vft-4==va => vft=va+4
        vft=va+4
        if 0x7E1000<=vft<0x811000:
            name2vft[vft]=name
    except Exception:
        pass
P("COL->vftable pairs found: %d"%len(name2vft))
for vft in cands:
    if vft in name2vft:
        P("  *** vft %08X -> %r"%(vft,name2vft[vft]))
    else:
        # find nearest
        P("  vft %08X not a direct COL+4; near: %s"%(vft,[ (hex(k),v) for k,v in sorted(name2vft.items()) if abs(k-vft)<0x100 ][:3]))

with open(EVID+r"\t1_vft_rtti_raw.txt","w",encoding="utf-8") as f: f.write("\n".join(out)+"\n")
print("\n".join(out[:60]))
