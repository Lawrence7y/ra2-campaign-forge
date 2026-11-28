import sys,struct
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge')
import _r185.pe185 as P
R=P.RAW
def s(va,m=64):
    c=P.cstr(va,m); return c
for va in (0x7f97dc,0x7f97d0,0x7f97c4,0x7f97b8,0x7f97ac,0x7f97a4,0x7f9858,0x7f9848,0x87c370):
    print(hex(va), P.where(va), repr(s(va,48)), [hex(P.dw(va+j*4)) for j in range(3)])
# 0x87c370 content
o=P.r2o(0x87c370)
print("0x87c370 bytes:",R[o:o+64].hex())
print("0x87c370 dwords:",[hex(x) for x in struct.unpack_from('<16I',R,o)])
# the 6 identical 0x7d7ed2 entries at 0x87c4d0 region
print("0x87c4c0..0x87c500 dwords:",[hex(P.dw(0x87c4c0+i*4)) for i in range(16)])
