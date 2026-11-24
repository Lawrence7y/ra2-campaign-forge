from pehelp import *
for f in [0x4f43f0, 0x4f4410, 0x4f4450, 0x4f4240, 0x5656d0]:
    print(f"--- {f:#x} ---")
    for ins in disasm(f, 40, count=12):
        print("   ", fmt(ins))
