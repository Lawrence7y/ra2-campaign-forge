import sys
sys.path.insert(0,r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13_K9\work')
from common import *
from capstone import *
md=Cs(CS_ARCH_X86,CS_MODE_32)
for st,en in [(0x438630,0x438670),(0x438690,0x4386d0),(0x438f20,0x438f60),(0x439410,0x439450),(0x67e380,0x67e3b0)]:
    print('===',hex(st),'===')
    for i in md.disasm(rd(st,en-st),st):
        print(hex(i.address),i.mnemonic,i.op_str,'|',i.bytes.hex())
