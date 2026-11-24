import capstone, pefile, os
EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\W176_place81\EVIDENCE"
pe = pefile.PE(EXE, fast_load=True)
ib = pe.OPTIONAL_HEADER.ImageBase

def read(va, n):
    for s in pe.sections:
        v = ib + s.VirtualAddress
        if v <= va and va+n <= v + s.SizeOfRawData:
            off = s.PointerToRawData + (va-v)
            return pe.__data__[off:off+n]
    raise ValueError(hex(va))

def dump(start, nbytes, path, title):
    m = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    m.detail = True
    m.skipdata = True
    lines = [title]
    for ins in m.disasm(read(start, nbytes), start):
        lines.append("  %08X %-9s %s" % (ins.address, ins.mnemonic, ins.op_str))
    open(os.path.join(OUT, path), "w", encoding="utf-8").write("\n".join(lines)+"\n")
    print("wrote", path, "insns", len(lines)-1)

dump(0x5F5038, 0x200, "T1_disasm_005F4EC0_tail.txt", "Unlimbo 0x5F4EC0 tail from 0x5F5038 (beyond atlas end 0x5F522F)")
dump(0x5F5210, 0x60, "T1_disasm_005F5210.txt", "from 0x5F5210")
