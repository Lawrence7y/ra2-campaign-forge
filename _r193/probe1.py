import sys, struct, capstone
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185'); import pe185 as P
md=capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
def dis(va,n=120):
    o=P.r2o(va); code=P.RAW[o:o+n]
    out=[]
    for i in md.disasm(code,va):
        out.append('%08X  %-24s %s %s'%(i.address,i.bytes.hex(),i.mnemonic,i.op_str))
        if i.mnemonic in ('ret','retn') and i.address>=va: 
            break
        if i.mnemonic=='jmp' and i.address>va: pass
    return '\n'.join(out)
for va in (0x410260,0x410300,0x410310,0x410320,0x410450,0x410410,0x4C9150):
    print('==== %08X'%va); print(dis(va,160)); print()
