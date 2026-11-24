import sys, struct
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT14\work")
from auditlib import *

def sec(t): print("\n"+"="*72); print(t); print("="*72)

def col_info(vt):
    colptr = u32(vt - 4)         # pointer stored at vt[-4]
    print(f"vt {vt:08X}: vt[-4] raw = 0x{colptr:08X}")
    # try as VA then as RVA
    for base,label in [(0,'VA'),(0x400000,'RVA->VA')]:
        colva = colptr + base
        if not is_va(colva): 
            print(f"   {label} 0x{colva:08X}: not in section"); continue
        raw = hexb(colva, 20)
        sig=struct.unpack('<I',rd(colva,4))[0]
        off=struct.unpack('<I',rd(colva+4,4))[0]
        cd=struct.unpack('<I',rd(colva+8,4))[0]
        ptd=struct.unpack('<I',rd(colva+12,4))[0]
        pchd=struct.unpack('<I',rd(colva+16,4))[0]
        print(f"   {label} COL @0x{colva:08X}: raw={raw}")
        print(f"      sig={sig} offset={off} cd={cd} pTD=0x{ptd:X} pCHD=0x{pchd:X}")
        # TypeDescriptor pointer: try ptd as VA and as RVA
        for tb,tl in [(0,'VA'),(0x400000,'RVA')]:
            tdva=ptd+tb
            if is_va(tdva):
                try:
                    name=cstring(tdva+8,120)
                    print(f"      TD via {tl} @0x{tdva:08X}: name='{name}'")
                except Exception as ex:
                    print(f"      TD via {tl} @0x{tdva:08X}: err {ex}")

for vt in [0x7E7F7C, 0x7E8344, 0x7ECE34]:
    sec(f"vtable {vt:08X}")
    col_info(vt)
