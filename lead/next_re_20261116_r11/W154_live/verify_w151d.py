import pefile, capstone
EXE=r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
pe=pefile.PE(EXE, fast_load=True); base=pe.OPTIONAL_HEADER.ImageBase; data=pe.get_memory_mapped_image()
sec=[s for s in pe.sections if s.Name.startswith(b'.text')][0]
rva,off,size=sec.VirtualAddress,sec.PointerToRawData,sec.Misc_VirtualSize
code=data[off:off+size]
cs=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
st=0x55B8C3; sof=off+(st-base-rva)
prev_end=st
print("=== 0x%X .. 0x55B920 (checking flow into 0x55B8F0) ==="%st)
for ins in cs.disasm(code[sof:sof+0xC0], st):
    mark=""
    if ins.address==0x55B8F0: mark="  <<< TGT (ladder start)"
    if ins.address>0x55B91C: break
    print("  0x%X  %-18s %s %s%s"%(ins.address, ins.bytes.hex()[:18], ins.mnemonic, ins.op_str, mark))
