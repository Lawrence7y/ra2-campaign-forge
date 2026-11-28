import sys, capstone
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.detail=True
def dump(va,n=200):
    o=P.r2o(va)
    for i in md.disasm(P.RAW[o:o+n],va):
        b=P.RAW[P.r2o(i.address):P.r2o(i.address)+i.size]
        print('%08X  %-14s %-8s %s' % (i.address,b.hex(' ').upper(),i.mnemonic,i.op_str))
        if i.mnemonic.startswith('ret'): break
print('=== 0x4A1CA0 ==='); dump(0x4A1CA0,200)
print('=== 0x4A1D50 ==='); dump(0x4A1D50,64)
print('=== 0x4A1DE0 (first 120) ==='); dump(0x4A1DE0,260)
