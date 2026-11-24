import struct, json
exe = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
data = open(exe,"rb").read()
p = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv"
rows=[]
for line in open(p,encoding="utf-8"):
    f=line.rstrip("\n").split("\t")
    if len(f)<5: continue
    if f[1] not in ("S02","S19"): continue
    rows.append(f)
# VA occ for all S02/S19 rows
res=[]
for f in rows:
    entry=f[0]; va=int(entry,16); pat=struct.pack("<I",va)
    cnt=data.count(pat)
    res.append((entry,f[1],f[4],cnt))
for sub in ("S02","S19"):
    rr=[r for r in res if r[1]==sub]
    zero=[r for r in rr if r[3]==0]
    print(sub,"ALL rows=",len(rr),"VAocc=0=",len(zero))
    for g in ("[已证]","[静态推断]","[未证]"):
        gg=[r for r in rr if r[2]==g]
        gz=[r for r in gg if r[3]==0]
        print("   ",g,"total",len(gg),"zero",len(gz))
