import sys, struct
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S16_PADD\work")
import re_lib as R

CANDS = {
    "0053DBC0":("V_IonBlast::slot4 FindItemIndex",0x7EC07C,4),
    "0053DCD0":("DV_IonBlast::slot4 FindItemIndex",0x7EC05C,4),
    "0053DAA0":("DV_IonBlast::slot1 operator==",0x7EC05C,1),
    "006CDEB0":("SuperClass::slot3",0x7F3FE8,3),
    "006CDFF0":("SuperClass::slot10",0x7F3FE8,10),
    "006CE7C0":("SWType::slot3",0x7F4090,3),
    "006CE800":("SWType::slot5",0x7F4090,5),
    "006CEA10":("SWType::slot16",0x7F4090,16),
    "006CEF80":("SWType::slot27",0x7F4090,27),
    "0071A650":("Temporal::slot13",0x7F5180,13),
    "0071A660":("Temporal::slot5",0x7F5180,5),
    "0071A700":("Temporal::slot6",0x7F5180,6),
    "0071A720":("Temporal::slot3",0x7F5180,3),
    "0071A760":("Temporal::slot23",0x7F5180,23),
    "0071B190":("Temporal::slot12",0x7F5180,12),
    "0071B1A0":("Temporal::slot11",0x7F5180,11),
    "0071B1B0":("Temporal::slot8",0x7F5180,8),
}
# Build section VA ranges
secs = []
for s in R.pe().sections:
    lo = R.IMAGE_BASE + s.VirtualAddress
    hi = lo + max(s.Misc_VirtualSize, s.SizeOfRawData)
    secs.append((lo, hi, s.Name.decode(errors="replace").rstrip("\0")))

def off_to_va(off):
    for s in R.pe().sections:
        if s.PointerToRawData <= off < s.PointerToRawData + s.SizeOfRawData:
            return R.IMAGE_BASE + s.VirtualAddress + (off - s.PointerToRawData), s.Name.decode(errors="replace").rstrip("\0")
    return None, None

data = R.all_bytes()
# index positions of E8/E9 for speed
for hx,(label,vt,slot) in CANDS.items():
    entry = int(hx,16)
    sites=[]
    for i in range(len(data)-5):
        b = data[i]
        if b != 0xE8 and b != 0xE9:
            continue
        rel = struct.unpack("<i", data[i+1:i+5])[0]
        ins_va, sec = off_to_va(i)
        if ins_va is None: continue
        tgt = ins_va + 5 + rel
        if tgt == entry:
            sites.append((ins_va, sec, chr(b)))
    print("%s %s: %d direct E8/E9 sites" % (hx, label, len(sites)))
    for s_va, sec, op in sites[:20]:
        print("    %08X %s op=%s" % (s_va, sec, op))
