import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S21-F1\work")
import ra2 as R

data = R.BIN.pe.__data__
# scan whole file for .?A type names
found=[]
i=0
n=len(data)
while True:
    i=data.find(b".?A", i)
    if i<0: break
    end=data.find(b"\x00", i)
    if end<0 or end-i>140:
        i+=3; continue
    s=data[i:end].decode("latin-1", errors="replace")
    if any(k in s for k in ["Score","Campaign","Carryover","MapSeed","Battle","Scenario","WorldDomination"]):
        # file offset -> VA
        va=None
        for sec in R.BIN.sections:
            if sec["raw"]<=i<sec["raw"]+sec["rawsize"]:
                va=sec["va"]+(i-sec["raw"])
                break
        found.append((va, s))
    i+=3
for va,s in sorted(found, key=lambda x:(x[0] or 0)):
    print(f"{va:08X}: {s}" if va else f"?: {s}")
