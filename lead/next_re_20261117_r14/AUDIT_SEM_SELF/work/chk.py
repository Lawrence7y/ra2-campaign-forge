
import pefile, capstone
EXE=r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
pe=pefile.PE(EXE,fast_load=True); IMAGE=pe.OPTIONAL_HEADER.ImageBase
for s in pe.sections:
    if s.Name.rstrip(b'\x00')==b'.text': text=s
TB=text.VirtualAddress+IMAGE; TS=text.Misc_VirtualSize
RAW=open(EXE,'rb').read(); tdata=RAW[text.PointerToRawData:text.PointerToRawData+text.SizeOfRawData]
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.detail=True; md.skipdata=True
insns=[]; off=0
while off<TS:
    ok=False
    for x in md.disasm(tdata[off:off+16],TB+off):
        insns.append(x); off+=x.size; ok=True; break
    if not ok: off+=1
def ops_of(x):
    if x.mnemonic=='.byte': return []
    try: return x.operands
    except Exception: return []
for want in (0x1c2, 0x148):
    sites=[]
    for x in insns:
        for op in ops_of(x):
            if op.type==capstone.x86.X86_OP_IMM and op.imm==want:
                sites.append((hex(x.address), x.mnemonic+' '+x.op_str)); break
    print(hex(want),'imm occurrences:',len(sites), sites[:8])
for k,x in enumerate(insns):
    ops=ops_of(x)
    if x.mnemonic=='push' and ops and ops[0].type==capstone.x86.X86_OP_IMM and ops[0].imm==0x148:
        nxt=[insns[j].mnemonic+' '+insns[j].op_str for j in range(k+1,min(k+4,len(insns)))]
        print('push 0x148 @',hex(x.address),'->',nxt)
