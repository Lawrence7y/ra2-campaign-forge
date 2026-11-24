#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""W29 recon6: layout-independent search for CSF in ra2bench MIX files.
Read-only. NOT an engine-behaviour proof -- fixture facts only."""
import os, struct, zlib
base=r"D:\Project\ra2-campaign-forge\ra2bench"
print("==== CRC32 algorithm cross-check against known project fixture ====")
# deep doc: expandmd98.mix contains BATTLEMD.INI with id 0x07E280DD (measured on real artifact)
for nm in [b"BATTLEMD.INI",b"ECH01.MAP",b"RA2MD.CSF",b"RA2.CSF"]:
    print("  crc32(%-14r) = 0x%08X"%(nm,zlib.crc32(nm)&0xffffffff))

needles={
 "id RA2MD.CSF":struct.pack("<I",zlib.crc32(b"RA2MD.CSF")&0xffffffff),
 "id RA2.CSF":struct.pack("<I",zlib.crc32(b"RA2.CSF")&0xffffffff),
 "CSF magic ' FSC'":b" FSC",
 "str 'ra2md.csf'":b"ra2md.csf",
}
print("\n==== full-file search (first 5 hits per needle, offsets in hex) ====")
for fn in ["langmd.mix","language.mix","ra2md.mix","ra2.mix","expandmd01.mix"]:
    p=os.path.join(base,fn)
    sz=os.path.getsize(p)
    print("\n  -- %s (%d bytes) --"%(fn,sz))
    with open(p,"rb") as f:
        blob=f.read()   # up to ~281MB; acceptable once
    for label,nd in needles.items():
        hits=[];s=0
        while len(hits)<5:
            i=blob.find(nd,s)
            if i<0:break
            hits.append(i);s=i+1
        # count total for id needles (cheap enough)
        total=blob.count(nd)
        print("     %-20s total=%d  first=%s"%(label,total,", ".join("0x%X"%h for h in hits) if hits else "NONE"))
    del blob

print("\n==== loose .csf / .str files in game dir? ====")
for f in sorted(os.listdir(base)):
    if f.lower().endswith((".csf",".str")):
        print("  LOOSE:",f,os.path.getsize(os.path.join(base,f)))
print("  (none listed above means no loose CSF/STR in ra2bench)")
print("\nDONE recon6")
