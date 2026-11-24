
import pefile, capstone, json
EXE=r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
pe=pefile.PE(EXE,fast_load=True); IMAGE=pe.OPTIONAL_HEADER.ImageBase
for s in pe.sections:
    if s.Name.rstrip(b'\x00')==b'.text': text=s
TB=text.VirtualAddress+IMAGE; TS=text.Misc_VirtualSize
RAW=open(EXE,'rb').read(); tdata=RAW[text.PointerToRawData:text.PointerToRawData+text.SizeOfRawData]
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.detail=True; md.skipdata=True
# 收集所有 push imm32 紧接 call 0x7C8E17 (operator new) 的对象大小
sizes={}
prev=None; off=0; insns=[]
while off<TS:
    ok=False
    for i in md.disasm(tdata[off:off+16], TB+off):
        insns.append(i); off+=i.size; ok=True; break
    if not ok: off+=1
print('insns', len(insns))
for k,i in enumerate(insns):
    if i.mnemonic=='push' and i.operands and i.operands[0].type==capstone.x86.X86_OP_IMM:
        v=i.operands[0].imm
        # 看后面 1-2 条是否为 call 0x7C8E17
        for j in range(k+1, min(k+3,k+3)):
            if j>=len(insns): break
            ii=insns[j]
            if ii.mnemonic=='call' and ii.operands and ii.operands[0].type==capstone.x86.X86_OP_IMM and ii.operands[0].imm==0x7C8E17:
                sizes.setdefault(v,[]).append(hex(i.address))
json.dump({hex(k):v for k,v in sizes.items()}, open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\AUDIT_SEM_SELF\work\alloc_sizes.json','w'))
for want in (0x148,0x1c2,0x520):
    print(hex(want), 'sites:', sizes.get(want, [])[:5], 'count', len(sizes.get(want,[])))
print('total distinct sizes', len(sizes))
