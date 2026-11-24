import sys, struct
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S21-F1\work")
import ra2 as R
import capstone

# Scan .rdata for COL structures: COL{+0xC}=TD ptr, TD+8 name. Find TD names with Score/Campaign/Carryover/Save
rdata = R.BIN.sec(".rdata")
base = rdata["va"]; raw = rdata["raw"]; rawsize = rdata["rawsize"]
buf = R.BIN.pe.__data__[raw:raw+rawsize]

def raw_va(va):
    for s in R.BIN.sections:
        if s["va"] <= va < s["va"]+s["vsize"]:
            off=s["raw"]+(va-s["va"])
            if off<s["raw"]+s["rawsize"]: return off
    return None

def read_cstr(va, maxn=100):
    off=raw_va(va)
    if off is None: return None
    b=buf[off:off+maxn] if buf is not None else R.BIN.pe.__data__[off:off+maxn]
    z=b.find(b"\x00")
    if z<0: return None
    try: return b[:z].decode("latin-1")
    except: return None

found=[]
# scan .rdata for TD name strings starting with .?A mentioning classes of interest
for i in range(len(buf)-16):
    if buf[i:i+3]==b".?A":
        # get string
        end=buf.find(b"\x00", i)
        if end<0 or end-i>120: continue
        s=buf[i:end].decode("latin-1", errors="replace")
        if any(k in s for k in ["Score","Campaign","Carryover","MapSeed","Battle","Scenario"]):
            found.append((base+i, s))
for va,s in sorted(set(found)):
    print(f"TD-name @{va:08X}: {s}")
