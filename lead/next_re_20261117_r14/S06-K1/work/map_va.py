from pehelp import *
print("sections (VA, VSize, PtrRaw, SizeRaw, name):")
for s in SECTIONS:
    print(f"  {s[4]:8} VA {s[0]:#x} VSize {s[1]:#x} PtrRaw {s[2]:#x} SizeRaw {s[3]:#x}")
# which section contains file offset 0x41cd78 and 0x416bc8
for fo in [0x41cd78, 0x416bc8]:
    for s in SECTIONS:
        if s[2] <= fo < s[2]+s[3]:
            va = s[0] + (fo - s[2])
            print(f"fileoff {fo:#x} -> VA {va:#x} in {s[4]}")
