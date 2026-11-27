import sys,struct,collections,capstone
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
for va,n in ((0x410450,60),(0x410580,24),(0x410590,24),(0x4C9150,80),(0x410210,20),(0x410220,16),(0x410230,16),(0x4105e0,20),(0x410600,20),(0x4f4240,40),(0x6d1770,40),(0x41bc30,24)):
    o=P.r2o(va)
    print('== %08x bytes %s'%(va,P.RAW[o:o+16].hex()))
    for ins in md.disasm(P.RAW[o:o+n],va):
        print('   %08x %-24s %s %s'%(ins.address,ins.bytes.hex(),ins.mnemonic,ins.op_str))
