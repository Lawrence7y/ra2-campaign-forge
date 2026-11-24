import sys,json,struct
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r109/_exec')
from pe import *
from pe import _img, _pe
# ---- TypeDescriptors: [0]=type_info vftable ptr, then name ----
TIVFT=0x7f9594
needle=struct.pack('<I',TIVFT)
tds={}
i=0
while True:
    i=_img.find(needle,i)
    if i<0: break
    nm_off=i+8
    raw=_img[nm_off:nm_off+220]
    z=raw.find(b'\0')
    if 2<z<220:
        nm=raw[:z]
        if nm.startswith(b'.?A') and all(0x20<=c<=0x7e for c in nm):
            for s in SECS:
                if s['raw']<=i<s['raw']+s['rsize']:
                    tds[i+s['rdelta']]=nm.decode(); break
    i+=1
TD_SET=set(tds)
STAT={'td_count':len(tds)}

# ---- BCD: pTypeDescriptor, numContainedBases, {pmdisp,pmdisp}, attrs, pCHD ----
def bcd_ok(va):
    if va is None or u32(va) not in TD_SET: return False
    n=u32(va+4)
    if n is None or n>64: return False
    for k in range(3):
        v=u32(va+8+4*k)
        if v is None or v>0x10000: return False
    a=u32(va+0x14)
    if a is None or a>0x10000: return False
    return True
# CHD: sig,attributes,numBaseClasses,pBaseClassArray,pClassDescriptor{...}
def array_ok(va):
    n=u32(va)
    if n is None or not (1<=n<=64): return False
    for j in range(n):
        if not bcd_ok(u32(va+4+4*j)): return False
    return True
chds={}
for s in SECS:
    if s['name'] not in ('.data','.rdata','.text'): continue
    for va in range(s['va'],s['vend'],4):
        sig=u32(va)
        if sig not in (0,1): continue
        arr=u32(va+12)
        if arr is None or not array_ok(arr): continue
        n=u32(arr)
        # last BCD must point back to this CHD at +0x18
        back=u32(u32(arr+4+4*(n-1))+0x18)
        if back!=va: continue
        chds[va]=dict(sig=sig,attributes=u32(va+4),nbc=n,arr=arr,
                      tds=[tds[u32(u32(arr+4+4*j))] for j in range(n)])
STAT['chd_count']=len(chds)

# ---- COL ----
cols={}
for s in SECS:
    if s['name'] not in ('.data','.rdata','.text'): continue
    for va in range(s['va'],s['vend'],4):
        td=u32(va+12)
        if td is None or td not in TD_SET: continue
        if u32(va) not in (0,1): continue
        off=u32(va+4)
        if off is None or off>0x10000: continue
        chd=u32(va+16)
        if chd not in chds: continue
        cols[va]=dict(td=td,cls=tds[td],offset=off,chd=chd,sig=u32(va),cdsig=u32(va+20))
STAT['col_count']=len(cols)

# ---- vtables: COL pointer at vt-4 ----
vts={}
for c in cols:
    nb=struct.pack('<I',c)
    st=0
    while True:
        o=_img.find(nb,st)
        if o<0: break
        st=o+1
        va=None
        for s in SECS:
            if s['raw']<=o<s['raw']+s['rsize']:
                va=o+s['rdelta'];break
        if va is None: continue
        vt=va+4
        e0=u32(vt)
        if not in_text(e0): continue
        vts[vt]=dict(col=c,cls=cols[c]['cls'],offset=cols[c]['offset'],td=cols[c]['td'],chd=cols[c]['chd'])
STAT['vtable_count']=len(vts)
STAT['vtable_classes']=len({v['cls'] for v in vts.values()})
print(json.dumps(STAT,indent=1))
json.dump(dict(stat=STAT,tds={hex(k):v for k,v in tds.items()},
               chds={hex(k):v for k,v in chds.items()},
               cols={hex(k):v for k,v in cols.items()},
               vtables={hex(k):v for k,v in sorted(vts.items())}),
          open('/home/t628/projects/ra2-campaign-forge/_r109/_exec/_rtti_raw.json','w'),indent=0)
