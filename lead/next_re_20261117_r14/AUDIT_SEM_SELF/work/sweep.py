
import pefile, capstone, sys, json

EXE = r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
pe = pefile.PE(EXE, fast_load=True)
IMAGE = pe.OPTIONAL_HEADER.ImageBase
text = None
for s in pe.sections:
    if s.Name.rstrip(b'\x00') == b'.text':
        text = s; break
raw = open(EXE,'rb').read()
TB = text.VirtualAddress + IMAGE
TS = text.Misc_VirtualSize
TP = text.PointerToRawData
tdata = raw[TP:TP+text.SizeOfRawData]

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = True
md.skipdata = False

# full sweep
n_instr = 0
e8_sites = []
off = 0
end = TS
while off < end:
    got = False
    for insn in md.disasm(tdata[off:off+16], TB+off):
        n_instr += 1
        if insn.mnemonic == 'call' and insn.op_str and not insn.op_str.startswith(('e','dword','[')):
            pass
        if insn.bytes[0] == 0xE8:
            e8_sites.append(insn.address)
        off += insn.size
        got = True
        break
    if not got:
        off += 1
print('instrs', n_instr)
print('E8', len(e8_sites))
print('textbase', hex(TB), 'size', TS)
