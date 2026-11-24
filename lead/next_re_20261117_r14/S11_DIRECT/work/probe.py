import sys, hashlib
print("python", sys.version.split()[0])
import capstone; print("capstone", capstone.__version__)
import pefile; print("pefile", pefile.__version__)
p = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
pe = pefile.PE(p)
data = open(p,"rb").read()
print("sha256", hashlib.sha256(data).hexdigest().upper())
for s in pe.sections:
    print(s.Name.decode(errors="replace").rstrip("\x00"), hex(s.VirtualAddress), hex(s.Misc_VirtualSize), hex(s.PointerToRawData), hex(s.SizeOfRawData))