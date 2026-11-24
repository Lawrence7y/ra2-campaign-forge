import struct, pefile, capstone
EXE=r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
pe=pefile.PE(EXE, fast_load=True); base=pe.OPTIONAL_HEADER.ImageBase; data=pe.get_memory_mapped_image()
TGT=0x55B8F0
for s in pe.sections:
    if s.Name.startswith(b'.text'):
        rva,off,size=s.VirtualAddress,s.PointerToRawData,s.Misc_VirtualSize
code=data[off:off+size]
cs=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
CFLOW=set("call jmp je jne jz jnz ja jae jb jbe jg jge jl jle js jns jo jno jp jnp jecxz loop loope loopne".split())
hits=[]; prev=None
for ins in cs.disasm(code, base+rva):
    if ins.address==TGT: prev=("INS_AT_TGT",None)
    if ins.mnemonic in CFLOW:
        op=ins.op_str
        if op.startswith("0x"):
            try:
                if int(op,16)==TGT: hits.append((ins.address,ins.mnemonic))
            except: pass
print("=== all control-flow transfers (incl. jcc) targeting 0x%X : %d ==="%(TGT,len(hits)))
for a,m in hits[:20]: print("   0x%X  %s"%(a,m))
# find the enclosing code before 0x55B8F0 and check fall-through
start=None
for s2 in pe.sections:
    if s2.Name.startswith(b'.text'):
        start=s2.VirtualAddress
win=[ins for ins in cs.disasm(code, base+rva) if 0x55B860<=ins.address<=0x55B905]
print("\n=== disassembly 0x55B860 .. 0x55B905 ===")
for ins in win:
    mark=" <<< TGT" if ins.address==TGT else ""
    print("  0x%X  %-24s %s%s"%(ins.address, ins.bytes.hex(), ins.mnemonic+" "+ins.op_str, mark))
