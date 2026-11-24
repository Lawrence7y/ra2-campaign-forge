import pathlib
import pefile
pe=pefile.PE(str(pathlib.Path(r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe")),fast_load=False)
for s in pe.sections:
 print(s.Name.rstrip(b"\x00").decode(errors='replace'),hex(pe.OPTIONAL_HEADER.ImageBase+s.VirtualAddress),hex(s.VirtualAddress),hex(s.Misc_VirtualSize),hex(s.PointerToRawData),hex(s.SizeOfRawData))
