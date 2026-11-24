from pehelp import *
print("=== context 0x6ac863 (vft 0x7e6114 write) ===")
for ins in disasm(0x6ac840, 0x50, count=25):
    print("   ", fmt(ins))
print("\n=== 0x652960 region (ctor calling 0x4a8730) ===")
for ins in disasm(0x652960, 0x40, count=25):
    print("   ", fmt(ins))
