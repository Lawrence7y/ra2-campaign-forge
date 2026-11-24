#!/usr/bin/env python3
# W61: raw scan of all MIX entries for CAMPAIGN.PCX / Background= / third-badge art.
import sys, os, glob, re, struct
sys.path.insert(0, r"D:\Project\ra2-campaign-forge")
from ra2forge.mixlib import westwood_decrypt_key_block, Blowfish
OUT=r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r02\W61_third_badge_route\work"
BENCH=r"D:\Project\ra2-campaign-forge\ra2bench"
def parse_mix(buf):
    if len(buf)<10 or struct.unpack_from("<H",buf,0)[0]!=0: return None
    fl=struct.unpack_from("<H",buf,2)[0]
    if fl&2:
        if len(buf)<92: return None
        f=Blowfish(westwood_decrypt_key_block(buf[4:84]))
        nf=struct.unpack("<H",f.decrypt_block(buf[84:92])[:2])[0]; bc=(13+nf*12)//8
        if 84+bc*8>len(buf): return None
        raw=f.decrypt(buf[84:84+bc*8])[6:]; ds=84+bc*8
    else:
        nf=struct.unpack_from("<H",buf,4)[0]; raw=buf[10:10+nf*12]; ds=10+nf*12
    return [struct.unpack_from("<III",raw,i*12) for i in range(nf) if 12*i+12<=len(raw)], ds
needles=[b"CAMPAIGN.PCX",b"Background=",b"Highlighted=",b"BootCamp",b"Tutorial",b"TUT1",b"ItemMax",b"GraphicMenu"]
vis=set(); found={n:[] for n in needles}
def walk(buf,label):
    r=parse_mix(buf)
    if r is None: return
    ents,ds=r
    for hid,off,size in ents:
        if ds+off+size>len(buf) or size==0 or size>2_000_000: continue
        blob=buf[ds+off:ds+off+size]
        k=(label,hid)
        if blob[:2]==b"\x00\x00" and k not in vis:
            vis.add(k); walk(blob,label+"/%08X"%hid)
        up=blob.upper()
        for n in needles:
            if (n.upper() if n!=b"Background=" else n) in up:
                found[n].append((label,"%08X"%hid,size))
print("=== raw MIX scan for UI-definition strings ===")
for mp in sorted(glob.glob(os.path.join(BENCH,"*.mix"))):
    try: b=open(mp,"rb").read()
    except: continue
    if parse_mix(b) is None: continue
    walk(b,os.path.basename(mp))
for n,loc in found.items():
    print("  %-16s : %d entries" % (n.decode("latin1"),len(loc)))
    for l,h,s in loc[:12]: print("      %-45s %s %d" % (l,h,s))
