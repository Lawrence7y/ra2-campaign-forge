import sys, capstone
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.detail=True
def dump(a,b,tag):
    print('=== %s %08X..%08X ==='%(tag,a,b))
    o=P.r2o(a)
    for i in md.disasm(P.RAW[o:P.r2o(b)],a):
        print('%08X  %-24s %-8s %s'%(i.address,P.RAW[P.r2o(i.address):P.r2o(i.address)+i.size].hex(' ').upper(),i.mnemonic,i.op_str))
dump(0x4A1E55,0x4A1F49,'0x4A1DE0 mid')
dump(0x4A1FB0,0x4A2160,'0x4A1FB0')
