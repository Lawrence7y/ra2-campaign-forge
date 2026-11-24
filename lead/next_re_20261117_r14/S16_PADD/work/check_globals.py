import sys, struct
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S16_PADD\work")
import re_lib as R
for g in [0x7E9580,0x7E9584,0x7E9588,0x7E958C,0x7E9570,0x7E9574,0x7E9578,0x7E957C]:
    b=R.read_bytes(g,4)
    if not b:
        print(hex(g),"NOBYTES"); continue
    val=struct.unpack("<I",b)[0]
    b2=R.read_bytes(val,16)
    print("%s -> %s sec=%s bytes=%s"%(hex(g),hex(val),R.section_of(val), b2.hex() if b2 else "NONE"))
