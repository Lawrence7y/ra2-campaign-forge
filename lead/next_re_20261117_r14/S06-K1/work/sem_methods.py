from pehelp import *
for f,label in [(0x557e10,'vt41'),(0x4886e0,'vt38'),(0x486840,'vt18'),(0x4867e0,'vt20')]:
    print(f"\n=== {label} {f:#x} ===")
    for ins in disasm(f,0x90,count=40):
        print("   ",fmt(ins))
        if ins.mnemonic=='ret': break
