#!/usr/bin/env python3
# W61 Q2 final: harvest real UI art filenames from MIX-contained INIs,
# extract CAMPAIGN.PCX, parse its PCX header, and check for any 3rd-badge art.
import sys, os, glob, re, struct, zlib, hashlib
sys.path.insert(0, r"D:\Project\ra2-campaign-forge")
from ra2forge.mixlib import westwood_decrypt_key_block, Blowfish
OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r02\W61_third_badge_route\work"
BENCH = r"D:\Project\ra2-campaign-forge\ra2bench"

def parse_mix(buf):
    if len(buf) < 10 or struct.unpack_from("<H",buf,0)[0]!=0: return None
    flags = struct.unpack_from("<H",buf,2)[0]
    if flags & 0x2:
        if len(buf)<92: return None
        fish = Blowfish(westwood_decrypt_key_block(buf[4:84]))
        nf = struct.unpack("<H", fish.decrypt_block(buf[84:92])[:2])[0]
        bc = (13+nf*12)//8
        if 84+bc*8>len(buf): return None
        raw = fish.decrypt(buf[84:84+bc*8])[6:]
        ds = 84+bc*8
    else:
        nf = struct.unpack_from("<H",buf,4)[0]
        raw = buf[10:10+nf*12]; ds = 10+nf*12
    ents=[]
    for i in range(nf):
        if 12*i+12>len(raw): break
        ents.append(struct.unpack_from("<III",raw,i*12))
    return ents, ds

pat = re.compile(rb"[ -~]{3,64}\.(?:PCX|SHP|PAL|VQA|BIK)\b", re.I)
kw = re.compile(rb"(?i)campaign|camp|boot|tut|badge|emblem|sel|icon|highlight|background")
artnames=set(); ini_hits=[]
visited=set()
def walk(buf,label,depth=0):
    r=parse_mix(buf)
    if r is None: return
    ents,ds=r
    for hid,off,size in ents:
        if ds+off+size>len(buf): continue
        blob=buf[ds+off:ds+off+size]
        key=(label,hid)
        if blob[:2]==b"\x00\x00" and key not in visited:
            visited.add(key); walk(blob,label+"/%08X"%hid,depth+1)
        if 0<size<400000:
            # gather art filenames from any text-ish entry
            istext = sum(1 for c in blob[:512] if 0x20<=c<0x7f or c in (9,10,13)) > 400
            if istext:
                found=set(m.group().decode("latin1") for m in pat.finditer(blob))
                artnames.update(found)
                if kw.search(blob):
                    ini_hits.append((label, "%08X"%hid, size, [f for f in sorted(found) if kw.search(f.encode())][:15]))
                if b"CAMPAIGN.PCX" in blob.upper():
                    print("  [CAMPAIGN.PCX referenced in] %s entry %08X size=%d" % (label,hid,size))
                    open(os.path.join(OUT,"ini_with_CAMPAIGN_PCX_%08X.txt"%hid),"wb").write(blob[:20000])
        if hid == 0x6177B5BE and size>1000:  # crc("CAMPAIGN.PCX")
            p=os.path.join(OUT,"CAMPAIGN.PCX")
            open(p,"wb").write(blob)
            print("  [extracted] CAMPAIGN.PCX from %s size=%d sha256=%s" % (label,size,hashlib.sha256(blob).hexdigest()))

print("=== recursive harvest ===")
for mp in sorted(glob.glob(os.path.join(BENCH,"*.mix"))):
    try: buf=open(mp,"rb").read()
    except: continue
    if parse_mix(buf) is None: continue
    walk(buf,os.path.basename(mp))
print("  total harvested art filenames: %d" % len(artnames))

print("\n=== PCX header of extracted CAMPAIGN.PCX ===")
p=os.path.join(OUT,"CAMPAIGN.PCX")
if os.path.exists(p):
    b=open(p,"rb").read()
    man,bpp,enc,bpp2,xmin,ymin,xmax,ymax,hres,vres = struct.unpack_from("<BBBBHHHHHH",b,0)
    print("  manufacturer=0x%02X version=%d encoding=%d bpp=%d" % (man,bpp,enc,bpp2))
    print("  xmin=%d ymin=%d xmax=%d ymax=%d  => %dx%d pixels" % (xmin,ymin,xmax,ymax,xmax-xmin+1,ymax-ymin+1))
    print("  bytes=%d" % len(b))
else:
    print("  NOT EXTRACTED")

print("\n=== harvested filenames matching campaign/boot/tut/badge/sel/icon keywords ===")
sel=sorted(n for n in artnames if re.search(r"(?i)camp|camp|boot|tut|badge|emblem|sel|icon|bkgd|scr",n))
for n in sel: print("  %s" % n)
print("  total: %d" % len(sel))

print("\n=== INI-like entries mentioning campaign/boot/tut/badge (first 25) ===")
for label,hid,size,names in ini_hits[:25]:
    print("  %-40s %s %7d  %s" % (label,hid,size,names[:6]))
print("  total keyword INI entries: %d" % len(ini_hits))
