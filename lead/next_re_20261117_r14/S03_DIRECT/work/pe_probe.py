import pefile
p = r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
pe = pefile.PE(p)
print('ImageBase', hex(pe.OPTIONAL_HEADER.ImageBase))
print('AddressOfEntryPoint', hex(pe.OPTIONAL_HEADER.AddressOfEntryPoint))
print('FileAlignment', hex(pe.OPTIONAL_HEADER.FileAlignment), 'SectionAlignment', hex(pe.OPTIONAL_HEADER.SectionAlignment))
print('sections:')
for s in pe.sections:
    name = s.Name.rstrip(b'\x00').decode('latin1')
    va = pe.OPTIONAL_HEADER.ImageBase + s.VirtualAddress
    print('  %-8s VA=%#x VSize=%#x RawSize=%#x RawPtr=%#x chars=%#x' % (name, va, s.Misc_VirtualSize, s.SizeOfRawData, s.PointerToRawData, s.Characteristics))
