
import pefile, capstone
EXE = r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
pe = pefile.PE(EXE, fast_load=True); IMAGE = pe.OPTIONAL_HEADER.ImageBase
for s in pe.sections:
    if s.Name.rstrip(b'\x00') == b'.text': text = s
raw = open(EXE,'rb').read()
TB = text.VirtualAddress + IMAGE; TS = text.Misc_VirtualSize
tdata = raw[text.PointerToRawData:text.PointerToRawData+text.SizeOfRawData]

for skip in (False, True):
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = True; md.skipdata = skip
    n=0; e8=0; off=0
    while off < TS:
        ok=False
        for insn in md.disasm(tdata[off:off+16], TB+off):
            n+=1
            if insn.bytes[0]==0xE8: e8+=1
            off += insn.size; ok=True; break
        if not ok: off += 1
    print('skipdata',skip,'instrs',n,'E8',e8)
