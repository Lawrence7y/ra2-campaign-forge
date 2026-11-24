from pehelp import *
VT=0x7e4eec
for i in range(35,60):
    f=u32(VT+i*4)
    s=section_of(f) if f else None
    sec=s[4] if s else '-'
    print(f"vt{i}: {f and hex(f)} ({sec})")
