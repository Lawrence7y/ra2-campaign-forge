import sys, struct
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S21-F1\work")
import ra2 as R
import audit_lib as A

data=R.BIN.pe.__data__
def va_of_off(off):
    for s in R.BIN.sections:
        if s["raw"]<=off<s["raw"]+s["rawsize"]:
            return s["va"]+(off-s["raw"])
    return None

# where is COL 0x7FC968 / 0x7FC9B0 stored? (vtable[-1])
for col in [0x7FC968,0x7FC9B0,0x7FCBF8,0x808DA0,0x808D70]:
    needle=struct.pack("<I",col)
    start=0; locs=[]
    while True:
        i=data.find(needle,start)
        if i<0: break
        va=va_of_off(i)
        if va is not None: locs.append(va)
        start=i+1
    print(f"COL {col:08X} stored at: {[hex(x) for x in locs]}")

# dump .rdata around those locations to read the vtable slots
for vt in [0x7FC96C, 0x7FC9B4]:
    print(f"\n=== possible vtable @ {vt:08X} (after COL) ===")
    for i in range(0,12):
        try: print(f"  +0x{i*4:X}: {R.u32(vt+i*4):08X}")
        except Exception as e: print("  ERR",e)

# find callers (via vtable dispatch) - who references these vtable addresses as data
# sweep for mov reg, <vt> patterns is harder; use sweep_disps won't work. Do targeted: search dword vt in .text
for vt in [0x7FC96C, 0x7FC9B4, 0x7E4AA8, 0x7E4AAC, 0x7E4AB0, 0x7E4AB8]:
    needle=struct.pack("<I",vt)
    start=0; locs=[]
    while True:
        i=data.find(needle,start)
        if i<0: break
        va=va_of_off(i)
        if va is not None: locs.append(va)
        start=i+1
    print(f"vt/addr {vt:08X} referenced at: {[hex(x) for x in locs[:20]]}")
