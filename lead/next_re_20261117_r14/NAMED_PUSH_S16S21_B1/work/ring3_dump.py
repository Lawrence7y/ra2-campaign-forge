import sys, os
sys.path.insert(0, ".")
import np_core
from np_core import *
def ins_at(va):
    for i in np_core._md.disasm(va_read(va,16), va):
        return "%s %-20s %s %s" % (hx(i.address), va_read(i.address,i.size).hex(" ").upper(), i.mnemonic, i.op_str)
    return "?"
print("--- ROW 0046D000 ③b② 锚点 ---")
for a in (0x0046D00B,0x0046D010,0x0046D012,0x0046D014,0x0046D016,0x0046D01F,0x0046D03F,0x0046D041):
    print("  ", ins_at(a))
print("  被调 0x410380 体内：")
for a in (0x00410389,0x0041038E,0x00410392,0x0041039E,0x004103A1,0x004103A3,0x004103CD,0x004103D6):
    print("  ", ins_at(a))
print()
print("--- ROW 0046D090 ③b② 锚点 ---")
for a in (0x0046D0B6,0x0046D0C1,0x0046D0C6,0x0046D0CA,0x0046D0CD,0x0046D0D0,0x0046D0D2,0x0046D0E7,0x0046D0EE,0x0046D0F1,0x0046D0FB,0x0046D0FF):
    print("  ", ins_at(a))
print("  被调(活表 007E9FE4 slot4) 004EC530：")
for a in (0x004EC530,0x004EC543,0x004EC545,0x004EC547,0x004EC54D,0x004EC54F,0x004EC552,0x004EC553):
    print("  ", ins_at(a))
print()
print("--- ROW 0071B1B0 ③b② 锚点 ---")
for a in (0x0071B1D8,0x0071B1DF,0x0071B1E3,0x0071B1E6,0x0071B1E9,0x0071B1EB,0x0071B200,0x0071B207,0x0071B20A,0x0071B214,0x0071B216,0x0071B218):
    print("  ", ins_at(a))
print("  被调(活表 007F5114 slot4) 0071B4D0：")
for a in (0x0071B4D0,0x0071B4E3,0x0071B4E5,0x0071B4E7,0x0071B4ED,0x0071B4EF,0x0071B4F2,0x0071B4F3):
    print("  ", ins_at(a))
