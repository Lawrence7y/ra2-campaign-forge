
import pefile
pe=pefile.PE(r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe')
m={}
for e in pe.DIRECTORY_ENTRY_IMPORT:
    for imp in e.imports:
        if imp.address: m[imp.address]=imp.name.decode() if imp.name else (e.dll.decode()+f'#{imp.ordinal}')
for a in (0x7E10E0,0x7E1200,0x7E11B8,0x7E11A8,0x7E1208,0x7E120C,0x7E1300):
    print(hex(a), m.get(a))
