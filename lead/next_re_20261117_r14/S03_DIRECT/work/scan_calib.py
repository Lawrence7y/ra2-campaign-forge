import pefile
from capstone import *
from capstone.x86 import *
p = r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
data = open(p,'rb').read()
pe = pefile.PE(p)
s = [x for x in pe.sections if x.Name.rstrip(b'\x00')==b'.text'][0]
base = pe.OPTIONAL_HEADER.ImageBase + s.VirtualAddress   # 0x401000
vsize = s.Misc_VirtualSize   # 0x3df38d
rsize = s.SizeOfRawData
rawptr = s.PointerToRawData
print('base',hex(base),'vsize',hex(vsize),'rsize',hex(rsize))
for label,n in [('vsize',vsize),('rsize',rsize)]:
    code = data[rawptr:rawptr+n]
    raw_e8 = code.count(0xE8)
    print(label,'len',len(code),'raw E8 count',raw_e8)
