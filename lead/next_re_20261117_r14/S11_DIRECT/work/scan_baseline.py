import capstone, pefile, time
p = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
pe = pefile.PE(p)
data = open(p,"rb").read()
sec = [s for s in pe.sections if s.Name.rstrip(b"\x00")==b".text"][0]
base_va = pe.OPTIONAL_HEADER.ImageBase + sec.VirtualAddress
for label, nbytes in [("rawsize", sec.SizeOfRawData), ("virtsize", sec.Misc_VirtualSize)]:
    code = data[sec.PointerToRawData: sec.PointerToRawData+nbytes]
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.skipdata = True
    t=time.time()
    n_all=0; n_real=0; n_e8=0; n_e8_call=0; max_addr=0
    for ins in md.disasm(code, base_va):
        n_all+=1
        max_addr = ins.address + ins.size
        if ins.id != 0 and ins.mnemonic != ".byte":
            n_real+=1
        # count raw E8 at instruction start
        off = ins.address - base_va
        if off>=0 and off < len(code) and code[off]==0xE8:
            n_e8+=1
            if ins.mnemonic=="call" and ins.size==5:
                n_e8_call+=1
    print(label, "nbytes",hex(nbytes), "n_all", n_all, "n_real", n_real, "n_e8_at_boundary", n_e8, "n_e8_call", n_e8_call, "max_addr", hex(max_addr), "sec_end", hex(base_va+len(code)), "secs", round(time.time()-t,2))