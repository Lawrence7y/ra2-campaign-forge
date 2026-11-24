import pefile, json, sys
p = pefile.PE(sys.argv[1])
print(json.dumps([{'n':s.Name.decode().rstrip(chr(0)),'va':s.VirtualAddress,'vs':s.Misc_VirtualSize,'raw':s.PointerToRawData,'rs':s.SizeOfRawData} for s in p.sections]))
