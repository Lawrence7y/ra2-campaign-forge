import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S21-F1\work")
import ra2 as R
import audit_lib as A
import struct

print("=== 0x46D360 (CampScor.cpp, sets CampaignScoreClass vtable) ===")
R.dump(0x46D360, 0x120)
print("\n=== 0x470C90 (CampScor.cpp, sets CampaignEndScoreClass vtable) ===")
R.dump(0x470C90, 0x160)

# xrefs to key strings
data=R.BIN.pe.__data__
def va_of_off(off):
    for s in R.BIN.sections:
        if s["raw"]<=off<s["raw"]+s["rawsize"]: return s["va"]+(off-s["raw"])
    return None

print("\n=== key INI/CSF strings and xrefs ===")
for kw in [b"NextScenario", b"EndOfGame", b"Campaign", b"SinglePlayer", b"NewCampaign"]:
    idxs=[]; st=0
    while True:
        i=data.find(kw,st)
        if i<0: break
        idxs.append(i); st=i+1
    print(f"\n{kw.decode()} ({len(idxs)}):")
    for i in idxs[:8]:
        va=va_of_off(i)
        if va:
            # find code refs to va (absolute addressing)
            try:
                f=A.sweep_disps(R.BIN,va)
                print(f"   str@{va:08X} {R.cstr(va,40)!r}: {len(f)} refs {[hex(x['va']) for x in f[:6]]}")
            except Exception as e:
                print(f"   str@{va:08X}: sweep err")
