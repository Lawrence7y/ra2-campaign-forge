import struct
raw=open('ra2bench/gamemd.exe','rb').read()
def r2o(va):
    if 0x401000<=va<0x7E038D: return 0x1000-0x401000+va
    if 0x7E1000<=va<0x811074: return 0x3E1000-0x7E1000+va
    if 0x812000<=va<0x849BE4: return 0x412000-0x812000+va
    return None
def dw(va):
    o=r2o(va); return None if o is None else struct.unpack_from('<I',raw,o)[0]
def isT(v): return v is not None and 0x401000<=v<0x7E038D
def isR(v): return v is not None and 0x7E1000<=v<0x811074
def isD(v): return v is not None and 0x812000<=v<0x849BE4
def cstr(va,m=200):
    o=r2o(va)
    if o is None: return None
    e=raw.find(b'\0',o,o+m); return raw[o:e]
def valid_col(a):
    if not isR(a): return None
    d=[dw(a+4*i) for i in range(5)]
    if None in d: return None
    if d[0] not in (0,1) or d[1]!=0 or d[2]!=0: return None
    if not isD(d[3]) or not isR(d[4]): return None
    nm=cstr(d[3]+8)
    if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): return None
    return nm
# enumerate all vtable starts
vts=[]
lo,hi=0x7E1004,0x811074
for V in range(lo,hi,4):
    if not isT(dw(V)): continue
    pre=dw(V-4)
    if not valid_col(pre): continue
    k=0
    while isT(dw(V+4*k)): k+=1
    term=dw(V+4*k)
    if k>=4 and (term==0 or valid_col(term)):
        nm=valid_col(pre)
        vts.append((V,k,term,nm.decode('latin1')))
print('total vtable starts',len(vts))
print('with term==0',sum(1 for v in vts if v[2]==0),' with term=COL(又一层接口)',sum(1 for v in vts if v[2]!=0))
import collections
print('slot-count hist',dict(sorted(collections.Counter(v[1] for v in vts).items())))
vset={v[0] for v in vts}
import re
rows=[]
for ln in open('re_atlas/evidence/class_ids.txt',encoding='utf-8',errors='replace'):
    m=re.match(r'^(0x[0-9A-Fa-f]{2})\s+(\d+)\s+(\S+)\s+(0x[0-9A-Fa-f]{8})\s+(.*)$',ln.rstrip('\n'))
    if m: rows.append((m.group(3),int(m.group(4),16)))
miss=[(n,hex(v)) for n,v in rows if v not in vset]
print('class vtables',len(rows),'missing',len(miss),miss[:5])
