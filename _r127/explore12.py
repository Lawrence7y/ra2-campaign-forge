import struct
import pefile
pe=pefile.PE('ra2bench/gamemd.exe'); IB=pe.OPTIONAL_HEADER.ImageBase
for e in pe.DIRECTORY_ENTRY_IMPORT:
    for imp in e.imports:
        va=imp.address  # VA of IAT slot
        if 0x7e15c0<=va<=0x7e1620:
            print('0x%x %s!%s'%(va,e.dll.decode(),imp.name.decode() if imp.name else 'ord%d'%imp.ordinal))
print('--- all ole32/oleaut entries sorted ---')
for e in pe.DIRECTORY_ENTRY_IMPORT:
    if e.dll.decode().lower() not in ('ole32.dll','oleaut32.dll'): continue
    for imp in e.imports:
        print('0x%x %s!%s'%(imp.address,e.dll.decode(),imp.name.decode() if imp.name else 'ord'))
