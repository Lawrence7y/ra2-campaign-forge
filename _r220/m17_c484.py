import sys,struct
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge')
import _r185.pe185 as P
R=P.RAW
o=P.r2o(0x87c480)
print("bytes 0x87c480..0x87c560:")
b=R[o:o+0xe0]
for i in range(0,0xe0,16):
    print("  %#x  %s"%(0x87c480+i,' '.join('%02x'%x for x in b[i:i+16])))
print()
print("dwords 0x87c480..0x87c520:",[hex(x) for x in struct.unpack_from('<40I',R,o)])
# 12-byte records at 0x87c488
for k in range(6):
    base=0x87c488+k*12
    print("rec%d @%#x:"%(k,base),[hex(P.dw(base+j*4)) for j in range(3)], "where:",[P.where(P.dw(base+j*4)) for j in range(3)])
# 4-byte array at 0x87c484
print("dword array @0x87c484:",[hex(P.dw(0x87c484+j*4)) for j in range(8)], "where:",[P.where(P.dw(0x87c484+j*4)) for j in range(8)])
# record-count check for TAB162
print("2576/16 =",2576/16, " 2576/12 =",2576/12)
