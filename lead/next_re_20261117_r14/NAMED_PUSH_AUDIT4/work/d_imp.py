"""Resolve imports (ole32 etc.) to IAT slots, so ④ can be checked by name."""
import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT4\work")
from lib import Img, IMAGEBASE

img = Img()
want = ('CoRegisterClassObject', 'CoCreateInstance', 'CoGetClassObject', 'OleRun',
        'CoCreateInstanceEx', 'CoInitialize')
for mod in img.pe.DIRECTORY_ENTRY_IMPORT:
    dll = mod.dll.decode('latin1')
    if 'ole32' not in dll.lower() and 'oleaut' not in dll.lower():
        continue
    for imp in mod.imports:
        nm = imp.name.decode('latin1') if imp.name else ('#%d' % imp.ordinal)
        if nm in want:
            print("%-28s %s  IAT=%08X" % (dll, nm, imp.address))
