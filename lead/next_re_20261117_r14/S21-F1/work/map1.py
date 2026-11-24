import sys, csv
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S21-F1\work")
import ra2 as R
import audit_lib as A

atlas_path = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv"
entries=[]
with open(atlas_path, encoding="utf-8", errors="replace") as f:
    hdr=f.readline().rstrip("\n").split("\t")
    for line in f:
        p=line.rstrip("\n").split("\t")
        if len(p)<2: continue
        try: e=int(p[0],16)
        except: continue
        try: sz=int(p[1]) if not p[1].startswith("0x") else int(p[1],16)
        except: sz=0
        entries.append((e,sz,p))
entries.sort()

def find_container(va):
    best=None
    for e,sz,p in entries:
        if e<=va:
            if best is None or e>best[0]: best=(e,sz,p)
        else: break
    if best:
        e,sz,p=best
        if sz==0 or e+sz>va: return (e,sz,p)
    return None

for va in [0x52F260, 0x685609, 0x685560, 0x52CC67]:
    c=find_container(va)
    print(f"container of {va:08X}: {c}")

calls, jmps, stats = A.sweep_calls(R.BIN)
print("\n=== callers of 0x52F000-ish functions ===")
for t in range(0x52F000,0x52F400,0x10):
    s=calls.get(t,[])
    if s:
        print(f"  {t:08X}: {len(s)} -> {[hex(x) for x in s[:6]]}")

c=find_container(0x685609)
print(f"\n=== callers of container {hex(c[0])} ===")
print([hex(x) for x in calls.get(c[0],[])])

for t in [0x46D360,0x470C90,0x471420,0x471500,0x471520,0x473920,0x556620,0x556630,0x690C00,0x690D60,0x5C97B0]:
    s=calls.get(t,[])
    print(f"callers of {t:08X}: {len(s)} -> {[hex(x) for x in s[:10]]}")
