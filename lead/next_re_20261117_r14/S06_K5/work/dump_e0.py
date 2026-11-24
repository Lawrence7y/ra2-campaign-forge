
import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
import k5_lib as K
b=K.at(0x7E3810,8)
print("CONST @0x7E3810:",b.hex(),"=",struct.unpack('<d',b)[0])
print("DIRTABLE @0x89F688:", "raw" if K.at(0x89F688,32) else "BSS/runtime-init")
print("=== 004838E0 (272 bytes) full ===")
for i in K.dis(0x4838E0,272): print(K.fmt(i))
