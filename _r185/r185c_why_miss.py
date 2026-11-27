import struct,os,re
ROOT='/home/t628/projects/ra2-campaign-forge'; os.chdir(ROOT)
raw=open('ra2bench/gamemd.exe','rb').read()
IB=0x400000
def r2o(va): return 0x1000-0x401000+va if 0x401000<=va<0x7E038D else 0x3E1000-0x7E1000+va if 0x7E1000<=va<0x811074 else None
T=(0x401000,0x7E038D); R=(0x7E1000,0x811074)
def ok(v): return (T[0]<=v<T[1]) or (R[0]<=v<R[1])
# class_ids vtables
ci=open('re_atlas/evidence/class_ids.txt',encoding='utf-8',errors='replace').read().splitlines()
rows=[]
for ln in ci:
    m=re.match(r'^(0x[0-9A-Fa-f]{2})\s+(\d+)\s+(\S+)\s+(0x[0-9A-Fa-f]{8})\s',ln)
    if m: rows.append((m.group(3),int(m.group(2)),int(m.group(4),16)))
print('rows',len(rows))
def rundesc(vt):
    o=r2o(vt)
    ds=[]
    for i in range(0,40):
        v=struct.unpack_from('<I',raw,o+4*i)[0]
        ds.append(v)
        if v==0: break
    return ds
bad_rows=[]
for nm,sz,vt in rows:
    ds=rundesc(vt)
    # maximal in-.text run from start
    n=0
    while n<len(ds) and T[0]<=ds[n]<T[1] and ds[n]%4==0: n+=1
    tail=ds[n:]
    okall=all(ok(v) for v in ds[:-1]) and ds[-1]==0
    if n<4 or not okall:
        bad_rows.append((nm,vt,n,ds[:6],ds[n:n+3]))
print('rows failing strict-J1:',len(bad_rows))
for b in bad_rows[:12]: print(hex(b[1]),b[0],'intext_run',b[2],[hex(x) for x in b[3]],'->',[hex(x) for x in b[4]])
# distribution: how many slots until first out-of-.text for the 69
import collections
starts=collections.Counter()
for nm,sz,vt in rows:
    ds=rundesc(vt)
    n=0
    while n<len(ds) and T[0]<=ds[n]<T[1] and ds[n]%4==0: n+=1
    starts[n]+=1
print('first-nontext-index histogram',dict(sorted(starts.items())))
