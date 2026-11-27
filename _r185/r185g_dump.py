import struct,os
raw=open('ra2bench/gamemd.exe','rb').read()
def r2o(va):
    if 0x401000<=va<0x7E038D: return 0x1000-0x401000+va
    if 0x7E1000<=va<0x811074: return 0x3E1000-0x7E1000+va
    if 0x812000<=va<0x849BE4: return 0x412000-0x812000+va
    return None
lo,hi=0x7E1F00,0x7E2000
o=r2o(lo)
for i in range((hi-lo)//4):
    va=lo+4*i
    v=struct.unpack_from('<I',raw,o+4*i)[0]
    tag=''
    if 0x401000<=v<0x7E038D: tag='TEXT'
    elif 0x7E1000<=v<0x811074: tag='RDATA'
    elif 0x812000<=v<0x849BE4: tag='DATA'
    elif v==0: tag='ZERO'
    print('%08x %08x %s'%(va,v,tag))
