import sys, struct
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S16_PADD\work")
import re_lib as R

VTS = {
    0x7EC07C:"Vector<IonBlast*> vt",
    0x7EC05C:"DynVector<IonBlast*> vt",
    0x7F3FE8:"SuperClass vt",
    0x7F4090:"SWType vt",
    0x7F5180:"TemporalClass vt",
}
data = R.all_bytes()
def off_to_va(off):
    for s in R.pe().sections:
        if s.PointerToRawData <= off < s.PointerToRawData + s.SizeOfRawData:
            return R.IMAGE_BASE + s.VirtualAddress + (off - s.PointerToRawData), s.Name.decode(errors="replace").rstrip("\0")
    return None, None
for vt,label in VTS.items():
    pat = struct.pack("<I", vt)
    hits=[]
    start=0
    while True:
        idx = data.find(pat, start)
        if idx<0: break
        va,sec = off_to_va(idx)
        if va is not None:
            hits.append((idx,va,sec))
        start=idx+1
    print("=== %s %s : %d raw hits ===" % (hex(vt),label,len(hits)))
    for idx,va,sec in hits:
        ctx = data[max(0,idx-8):idx+8].hex()
        print("   off=%X va=%s sec=%s ctx=%s" % (idx, (("%08X"%va) if va else "?"), sec, ctx))
    print()
