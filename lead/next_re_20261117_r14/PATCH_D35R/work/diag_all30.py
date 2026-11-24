# -*- coding: utf-8 -*-
"""DIAGNOSTIC only: wire ALL 30 call sites to the shared counter stub to
discover which are reachable via bounded GUI. NOT the deliverable."""
import os, struct, hashlib
SRC=r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
OUT=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\PATCH_D35R\work\diag_all30\gamemd.exe"
IB=0x400000; CAVE_VA=0x7DF781; CAVE_OFF=0x3DF781
CTR_LAST,CTR_COUNT=0x9F5000,0x9F5004
SITES=[0x4A8B75,0x640427,0x654413,0x654469,0x6AC00B,0x6AC03E,0x6AC0ED,0x6AC140,
       0x6AC193,0x6AC1E6,0x6D059B,0x6D0619,0x6D0634,0x6D0664,0x6D089D,0x6D08B3,
       0x6D0940,0x6D09FA,0x6D1293,0x6D1308,0x6D137E,0x6D13F3,0x6D1541,0x6D155C,
       0x6D15CB,0x6D1605,0x6D1632,0x6D16C2,0x6D16DD,0x6D1744]
def rel32(t,v,l=5):return (t-(v+l))&0xffffffff
d=bytearray(open(SRC,'rb').read())
stub=bytearray()
stub+=bytes.fromhex("50")+bytes.fromhex("8B442404")
stub+=b"\xA3"+struct.pack("<I",CTR_LAST)+b"\xFF\x05"+struct.pack("<I",CTR_COUNT)
stub+=bytes.fromhex("58")+bytes.fromhex("85C9")+bytes.fromhex("7405")
stub+=b"\xE9"+struct.pack("<I",rel32(0x724730,CAVE_VA+21))
stub+=bytes.fromhex("83C404")+bytes.fromhex("C3")
assert len(stub)==30
bg=bytearray(bytes.fromhex("A1E0718800")+bytes.fromhex("85C0")+bytes.fromhex("7405"))
bg+=b"\xE9"+struct.pack("<I",rel32(0x6CD8C7,CAVE_VA+30+9))
bg+=b"\xE9"+struct.pack("<I",rel32(0x6CD8D8,CAVE_VA+30+14))
d[CAVE_OFF:CAVE_OFF+49]=bytes(stub)+bytes(bg)
n=0
for s in SITES:
    o=s-IB
    assert d[o]==0xE8
    d[o+1:o+5]=struct.pack("<I",rel32(CAVE_VA,s));n+=1
os.makedirs(os.path.dirname(OUT),exist_ok=True)
open(OUT,'wb').write(d)
print("diag exe:",OUT,"sha",hashlib.sha256(bytes(d)).hexdigest().upper(),"sites",n)
