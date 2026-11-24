#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""W29 recon5: parse UNENCRYPTED langmd.mix index (read-only) to confirm
whether a RA2MD.CSF entry exists inside the MIX. NOT an engine-behaviour proof;
just a fixture fact for the minimal live experiment.
Layout derived (and independently re-derived) from MixFileClass ctor 0x5B3C20:
  0..3   : word0(format)==0, word1(flags)
  4..9   : u16 numFiles, u32 bodySize   (Straw::Get 6 bytes @0x5B3D3F)
  10..   : numFiles * 12 = {u32 id; u32 offset; u32 size}
Only valid when flags&2 == 0 (unencrypted).
"""
import struct, zlib, os
p=r"D:\Project\ra2-campaign-forge\ra2bench\langmd.mix"
with open(p,"rb") as f:
    head=f.read(10)
    w0,w1=struct.unpack_from("<HH",head,0)
    num,body=struct.unpack_from("<HI",head,4)
    print("langmd.mix size=%d word0=0x%04X flags=0x%04X numFiles=%d bodySize=%d"%(os.path.getsize(p),w0,w1,num,body))
    print("flags&2 (encrypted) =",bool(w1&2))
    if w1&2:
        print("ENCRYPTED -> index cannot be read in plaintext; stop.")
        raise SystemExit(0)
    f.seek(10)
    tbl=f.read(num*12)
print("index bytes read =",len(tbl),"(expected %d)"%(num*12))
ents=[]
for i in range(num):
    eid,off,sz=struct.unpack_from("<III",tbl,i*12)
    ents.append((eid,off,sz))
print("entries parsed =",len(ents))
ids={e[0]:e for e in ents}
for nm in ["RA2MD.CSF","RA2.CSF","RA2MD.STR","RA2.STR"]:
    crc=zlib.crc32(nm.encode("ascii"))&0xffffffff
    e=ids.get(crc)
    print("  %-12s crc=0x%08X  %s"%(nm,crc,("FOUND entry(off=0x%X size=%d)"%(e[1],e[2])) if e else "NOT in langmd.mix index"))
# sanity: show first 6 entries + sorted-id monotonic check (binary search requires sorted)
print("first 6 entries (id, off, size):",[(hex(a),hex(b),c) for a,b,c in ents[:6]])
mono=all(ents[i][0]<=ents[i+1][0] for i in range(len(ents)-1))
print("index sorted by id ascending? ",mono)
print("DONE recon5")
