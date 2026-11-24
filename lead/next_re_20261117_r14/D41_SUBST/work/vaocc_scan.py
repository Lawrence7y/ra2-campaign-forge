import struct, json, os
exe = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
data = open(exe,"rb").read()
print("exe_size", len(data))
cand = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\D41_SUBST\work\si_candidates.tsv"
rows=[]
for line in open(cand,encoding="utf-8"):
    f=line.rstrip("\n").split("\t")
    if len(f)<5: continue
    rows.append(f)
print("candidates", len(rows))
# count 4-byte VA occurrences anywhere in the whole file
res=[]
for f in rows:
    entry=f[0]; sub=f[1]; name=f[2]
    va=int(entry,16)
    pat=struct.pack("<I",va)
    # count all (possibly overlapping) occurrences across whole file
    cnt=0; pos=0; offs=[]
    while True:
        i=data.find(pat,pos)
        if i<0: break
        cnt+=1; offs.append(i); pos=i+1
    res.append({"entry":entry,"sub":sub,"name":name,"vaocc":cnt,"offs":[hex(o) for o in offs[:20]]})
# summary
import collections
for sub in ("S02","S19"):
    rr=[r for r in res if r["sub"]==sub]
    zero=[r for r in rr if r["vaocc"]==0]
    nz=[r for r in rr if r["vaocc"]>0]
    print(sub,"candidates",len(rr),"vaocc=0",len(zero),"vaocc>0",len(nz))
    print("  ZERO:", ", ".join(r["entry"]+"("+r["name"]+")" for r in zero))
    print("  NONZERO:", ", ".join(r["entry"]+":"+str(r["vaocc"]) for r in nz))
json.dump(res, open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\D41_SUBST\work\vaocc.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)
print("wrote vaocc.json")
