import sys,io,pefile
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8',errors='replace')
pe=pefile.PE(r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe')
for s in pe.sections:
    print(s.Name.decode(errors='replace').rstrip(chr(0)), hex(s.VirtualAddress), hex(s.Misc_VirtualSize), hex(s.SizeOfRawData), hex(s.PointerToRawData))
print('ImageBase',hex(pe.OPTIONAL_HEADER.ImageBase),'FileAlign',hex(pe.OPTIONAL_HEADER.FileAlignment),'SectionAlign',hex(pe.OPTIONAL_HEADER.SectionAlignment))
