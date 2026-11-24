#!/usr/bin/env python3
"""Brute-force the exact tail rule for Westwood CRC hash 0x4A1DE0."""
import sys, os, zlib
sys.path.insert(0, os.path.dirname(__file__))
from pehelper import u32
TBL = [u32(0x81F7B4+4*i) for i in range(256)]

def crc(b):
    c=0xFFFFFFFF
    for x in b:
        c=(c>>8)^TBL[(c^x)&0xFF]
    return (c^0xFFFFFFFF)&0xFFFFFFFF

expect={'KEYBOARDMD.INI':0x930BE675,'RA2MD.CSF':0xBD835079,'GLSMD.PAL':0x366CBDFB,
        'CREDITSMD.TXT':0x373A7BC1,'AUDIOMD.MIX':0xFE9DF3BE,'CAMEOMD.MIX':0x16A802B6,
        'GLSLMD.SHP':0xB11D7C29,'MISSIONSMD.PKT':0x480B82E4}
names=list(expect)

def variants(nm):
    b=bytearray(nm.encode())
    L=len(b); r=L%4
    out={}
    out['plain']=bytes(b)
    out['plain+NUL']=bytes(b)+b'\0'
    if r:
        # A: pad [r] then leftover[0]=b[L-r] repeated
        x=bytearray(b); x+=bytes([r])+bytes([b[L-r]])*(3-r); out['r,leftover0']=bytes(x)
        # B: pad [r] then b[0] repeated
        x=bytearray(b); x+=bytes([r])+bytes([b[0]])*(3-r); out['r,b0']=bytes(x)
        # C: pad [r] then zeros
        x=bytearray(b); x+=bytes([r])+bytes(3-r); out['r,zeros']=bytes(x)
        # D: overwrite within last dword: last dword = [b[L-r..], r, b[L-r]..]
        x=bytearray(b); x+=bytes(4-r); x[L]=r
        for j in range(L+1,L+4-r): x[j]=b[L-r]
        out['overwrite-leftover0']=bytes(x)
        # E: overwrite: b[L]=r, rest b[0]
        x=bytearray(b); x+=bytes(4-r); x[L]=r
        for j in range(L+1,L+4-r): x[j]=b[0]
        out['overwrite-b0']=bytes(x)
        # F: buf[r]=r then buf[r+1..3]=buf[0] applied to local 4-byte buffer holding LAST r bytes,
        #    then hash = full name prefix (L-r bytes) + that 4-byte dword
        d=bytearray(4); d[0:r]=b[L-r:L]; d[r]=r
        for j in range(r+1,4): d[j]=d[0]
        out['prefix+buf']=bytes(b[:L-r])+bytes(d)
        # G: like F but buf0 = b[0]
        d=bytearray(4); d[0:r]=b[L-r:L]; d[r]=r
        for j in range(r+1,4): d[j]=b[0]
        out['prefix+buf(b0)']=bytes(b[:L-r])+bytes(d)
    return out

# score each variant
keys=None
for nm in names:
    vs=variants(nm)
    if keys is None: keys=list(vs)
    for k in keys:
        if k not in vs: continue
        h=crc(vs[k])
        vs[k]=(h, h==expect[nm])
# recompute scores
scores={k:0 for k in keys}
for nm in names:
    vs=variants(nm)
    for k,v in vs.items():
        if isinstance(v,tuple) and v[1]: scores[k]+=1
print("Scores (out of 8):")
for k in sorted(scores,key=lambda x:-scores[x]):
    print(f"  {k:24} {scores[k]}/8")

# Detail for best
best=max(scores,key=lambda x:scores[x])
print(f"\nBest variant: {best}")
for nm in names:
    h=crc(variants(nm)[best])
    print(f"  {nm:<18} got={h:08X} exp={expect[nm]:08X} {'OK' if h==expect[nm] else 'XX'}")
