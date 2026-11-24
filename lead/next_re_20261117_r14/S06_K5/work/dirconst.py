
import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
import k5_lib as K
# 1e-5 constant
b=K.at(0x7E3810,8)
print("1e-5 const @0x7E3810 bytes=",b.hex(),"double=",struct.unpack('<d',b)[0])
# direction table at 0x89F688: 8 entries x 2 words = 32 bytes (used as [eax*4+0x89F688], [..+2])
b=K.at(0x89F688,32)
print("dir table 0x89F688 bytes=",b.hex())
for i in range(8):
    x,y=struct.unpack_from('<hh',b,i*4)
    print(f"  dir[{i}] = (dx={x}, dy={y})")
# full 4838E0
print("\n=== 004838E0 full ===")
for i in K.dis(0x4838E0,272): print(K.fmt(i))
