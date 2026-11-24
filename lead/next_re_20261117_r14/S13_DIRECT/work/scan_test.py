import sys,io,pefile,hashlib,time
from capstone import *
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8',errors='replace')
pe=pefile.PE(r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe')
sec=[s for s in pe.sections if s.Name.rstrip(b'\x00')==b'.text'][0]
base=pe.OPTIONAL_HEADER.ImageBase+sec.VirtualAddress
data=open(r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe','rb').read()[sec.PointerToRawData:sec.PointerToRawData+sec.SizeOfRawData]
print('base',hex(base),'rawlen',len(data),'vsize',hex(sec.Misc_VirtualSize))
md=Cs(CS_ARCH_X86,CS_MODE_32); md.skipdata=True
for label,nbytes in [('RAWSIZE',len(data)),('VSIZE',sec.Misc_VirtualSize)]:
    t=time.time(); nins=0; ne8=0; nskip=0
    code=data[:nbytes]
    for ins in md.disasm(code,base):
        nins+=1
        if ins.mnemonic.startswith('.') : nskip+=1
        if ins.bytes and ins.bytes[0]==0xE8: ne8+=1
    print(label,'nbytes',nbytes,'instructions(incl skip)',nins,'skipdata',nskip,'real',nins-nskip,'E8-at-boundary',ne8,'sec=%.1f'%(time.time()-t))
# raw E8 byte count
print('raw E8 byte count in .text',data[:sec.Misc_VirtualSize].count(0xE8)); print('raw E8 byte count full raw',data.count(0xE8))
