#!/usr/bin/env python3
"""Brute-force CRC init/final/xor and tail rules for Westwood hash 0x4A1DE0."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from pehelper import u32
TBL=[u32(0x81F7B4+4*i) for i in range(256)]
expect={'KEYBOARDMD.INI':0x930BE675,'RA2MD.CSF':0xBD835079,'GLSMD.PAL':0x366CBDFB,
        'CREDITSMD.TXT':0x373A7BC1,'AUDIOMD.MIX':0xFE9DF3BE,'CAMEOMD.MIX':0x16A802B6,
        'GLSLMD.SHP':0xB11D7C29,'MISSIONSMD.PKT':0x480B82E4}
names=list(expect)

def crc_init(b, init, final):
    c=init
    for x in b:
        c=(c>>8)^TBL[(c^x)&0xFF]
    return (c^final)&0xFFFFFFFF

def stream(nm, tailmode):
    b=bytearray(nm.encode()); L=len(b); r=L%4
    if r and tailmode=='leftover0':
        x=bytearray(b); x+=bytes(4-r); x[L]=r
        for j in range(L+1,L+4-r): x[j]=b[L-r]
        return bytes(x)
    if r and tailmode=='b0':
        x=bytearray(b); x+=bytes(4-r); x[L]=r
        for j in range(L+1,L+4-r): x[j]=b[0]
        return bytes(x)
    if r and tailmode=='zeros':
        return bytes(b)+bytes([r])+bytes(3-r)
    return bytes(b)

for tail in ['none','leftover0','b0','zeros']:
    for init in [0xFFFFFFFF,0]:
        for final in [0xFFFFFFFF,0]:
            score=sum(1 for nm in names if crc_init(stream(nm,tail),init,final)==expect[nm])
            if score>=1:
                print(f"tail={tail:10} init={init:08X} final={final:08X} score={score}/8")
# Also test: hash computed over name bytes but with byte-wise table on (c ^ byte) where
# c is NOT shifted first (a different CRC variant) - plus case toggles
print('--- case/extension variants, init=FFFFFFFF final=FFFFFFFF tail=none ---')
for nm in names:
    for cand in [nm, nm.lower(), nm.split('.')[0], nm.split('.')[0].lower(), nm+'\0']:
        h=crc_init(cand.encode(),0xFFFFFFFF,0xFFFFFFFF)
        if h==expect[nm]:
            print(f"  MATCH {nm} -> {cand!r}")
