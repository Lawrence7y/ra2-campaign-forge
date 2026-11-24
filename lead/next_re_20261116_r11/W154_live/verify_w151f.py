import pefile, capstone
EXE=r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
pe=pefile.PE(EXE, fast_load=True); base=pe.OPTIONAL_HEADER.ImageBase; data=pe.get_memory_mapped_image()
sec=[s for s in pe.sections if s.Name.startswith(b'.text')][0]
rva,off,size=sec.VirtualAddress,sec.PointerToRawData,sec.Misc_VirtualSize
code=data[off:off+size]
cs=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
st=0x55B880; sof=off+(st-base-rva)
term=[]
print("=== 0x55B880 .. 0x55B960 : looking for function-terminating control flow ===")
for ins in cs.disasm(code[sof:sof+0xE0], st):
    if ins.address>0x55B95C: break
    if ins.mnemonic in ("ret","retf") or (ins.mnemonic=="jmp" and not ins.op_str.startswith("0x55")):
        term.append((ins.address,ins.mnemonic,ins.op_str))
    print("  0x%X  %-16s %s %s"%(ins.address,ins.bytes.hex()[:16],ins.mnemonic,ins.op_str))
print("\nterminators in window:", term if term else "NONE (straight-line continues)")
