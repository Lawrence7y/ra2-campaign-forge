import sys, capstone
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.detail=True
o=P.r2o(0x4A1DE0); n=0
for i in md.disasm(P.RAW[o:o+900],0x4A1DE0):
    n+=1
    if n>140:
        print('%08X  %-24s %-8s %s' % (i.address,P.RAW[P.r2o(i.address):P.r2o(i.address)+i.size].hex(' ').upper(),i.mnemonic,i.op_str))
    if i.mnemonic.startswith('ret'):
        print('FIRST RET at %08X after %d insns, offset %d bytes' % (i.address,n,i.address-0x4A1DE0)); break
