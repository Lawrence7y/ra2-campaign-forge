import pefile, time
from capstone import *
p = r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
data = open(p,'rb').read()
pe = pefile.PE(p)
s = [x for x in pe.sections if x.Name.rstrip(b'\x00')==b'.text'][0]
base = pe.OPTIONAL_HEADER.ImageBase + s.VirtualAddress
vsize = s.Misc_VirtualSize
rawptr = s.PointerToRawData
md = Cs(CS_ARCH_X86, CS_MODE_32)
md.skipdata = True
md.detail = False
for label,n in [('vsize',vsize)]:
    code = data[rawptr:rawptr+n]
    t=time.time()
    ninsn=0; e8b=0
    for insn in md.disasm(code, base):
        ninsn+=1
        if insn.bytes and insn.bytes[0]==0xE8:
            e8b+=1
    print(label,'instructions',ninsn,'E8@boundary(firstbyte)',e8b,'elapsed %.1fs'%(time.time()-t))
