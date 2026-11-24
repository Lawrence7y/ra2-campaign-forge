import sys,struct,json,collections
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r109/_exec')
from pe import *
from pe import _img

# ---------- TD ----------
needle=struct.pack('<I',0x7f9594)
tds={}; i=0
while True:
    i=_img.find(needle,i)
    if i<0: break
    raw=_img[i+8:i+228]; z=raw.find(b'\0')
    if 2<z<228 and raw[:z].startswith(b'.?A') and all(0x20<=c<=0x7e for c in raw[:z]):
        for s in SECS:
            if s['raw']<=i<s['raw']+s['rsize']:
                tds[i+s['rdelta']]=raw[:z].decode(); break
    i+=1
TD_SET=set(tds)

# ---------- COL: [0]sig in(0,1) [4]offset [8]==0 [12]pTD [16]pCHD [20]==0 ----------
cols={}
for s in SECS:
    if s['name'] not in ('.data','.rdata'): continue
    for va in range(s['va'],s['vend'],4):
        td=u32(va+12)
        if td not in TD_SET: continue
        sig=u32(va); off=u32(va+4)
        if sig not in (0,1): continue
        if off is None or off>0x10000: continue
        chd=u32(va+16)
        if chd is None or not (0x401000<=chd<0xb96000): continue
        cols[va]=dict(td=td,cls=tds[td],offset=off,chd=chd,sig=sig)

# ---------- vtables: u32 == COL address, followed by >=1 text ptr ----------
vt={}
for c in cols:
    nb=struct.pack('<I',c); st=0
    while True:
        o=_img.find(nb,st)
        if o<0: break
        st=o+1
        va=None
        for s in SECS:
            if s['raw']<=o<s['raw']+s['rsize']: va=o+s['rdelta']; break
        if va is None: continue
        base=va+4
        if not in_text(u32(base)): continue
        # count slot entries until non-text
        n=0
        while in_text(u32(base+4*n)): n+=1
        vt[base]=dict(col=c,cls=cols[c]['cls'],offset=cols[c]['offset'],td=cols[c]['td'],chd=cols[c]['chd'],slots=n)
print(json.dumps(dict(td=len(tds),col=len(cols),vtables=len(vt),
                      classes=len({v['cls'] for v in vt.values()})),indent=1))
json.dump(dict(tds={hex(k):v for k,v in tds.items()},cols={hex(k):v for k,v in cols.items()},
               vtables={hex(k):v for k,v in sorted(vt.items())}),
          open('/home/t628/projects/ra2-campaign-forge/_r109/_exec/_vt_raw.json','w'))
# sanity sample
for b,v in list(sorted(vt.items()))[:4]:
    print(hex(b),v['cls'],'off',v['offset'],'slots',v['slots'],
          [hex(u32(b+4*k)) for k in range(min(v['slots'],4))])
