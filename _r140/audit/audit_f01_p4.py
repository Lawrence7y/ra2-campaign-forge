#!/usr/bin/env python3
# R140-F01-AUDIT part 4 : final robustness checks.
# 4a per-class mdisp0 distribution   4b C1 filter variants   4c COL alignment
import struct, os, collections, json, hashlib
ROOT='/home/t628/projects/ra2-campaign-forge'; EXE=os.path.join(ROOT,'ra2bench','gamemd.exe')
OUT=os.path.join(ROOT,'_r140','audit'); data=open(EXE,'rb').read()
pe=struct.unpack_from('<I',data,0x3c)[0]; nsec=struct.unpack_from('<H',data,pe+6)[0]
optsz=struct.unpack_from('<H',data,pe+20)[0]; opt=pe+24
IMAGEBASE=struct.unpack_from('<I',data,opt+28)[0]; sectab=opt+optsz
SECS=[]
for i in range(nsec):
    o=sectab+40*i; nm=data[o:o+8].rstrip(b'\0').decode('latin1')
    vs,va,rs,rp=struct.unpack_from('<IIII',data,o+8)
    SECS.append(dict(name=nm,vs=vs,rva=va,rs=rs,rp=rp,va_lo=IMAGEBASE+va,
                     va_hi=IMAGEBASE+va+max(vs,rs)))
S={s['name']:s for s in SECS}; TEXT,RDATA,DATA=S['.text'],S['.rdata'],S['.data']
def raw2va(o):
    for s in SECS:
        if s['rp']<=o<s['rp']+s['rs']: return IMAGEBASE+s['rva']+(o-s['rp'])
def va2raw(va):
    for s in SECS:
        if s['va_lo']<=va<s['va_lo']+s['rs']: return s['rp']+(va-s['va_lo'])
def rd32(va):
    o=va2raw(va)
    return None if o is None or o+4>len(data) else struct.unpack_from('<I',data,o)[0]
def inse(va,s): return s['va_lo']<=va<s['va_hi']

def build(td_filter):
    tds={}
    for s in (RDATA,DATA):
        buf=data[s['rp']:s['rp']+s['rs']]
        for tag in (b'.?AV',b'.?AU'):
            i=buf.find(tag)
            while i!=-1:
                e=i
                while e<len(buf) and e-i<256 and 0x20<=buf[e]<=0x7e: e+=1
                st=buf[i:e].decode('latin1')
                if st.endswith('@@') and len(st)>=8 and td_filter(buf,i,e,st):
                    sv=raw2va(s['rp']+i); v8,v4=rd32(sv-8),rd32(sv-4)
                    if v8 is not None and v4 is not None and (inse(v8,RDATA) or inse(v8,DATA)) and v4==0:
                        tds[sv-8]=st
                i=buf.find(tag,i+1)
    return tds
dw={}
for s in SECS:
    for o in range(s['rp'],s['rp']+s['rs']-3,4): dw[o]=struct.unpack_from('<I',data,o)[0]
def build_cols(tds):
    out=[]
    for o,v in dw.items():
        if v in tds:
            pv=raw2va(o); c=pv-12
            if dw.get(va2raw(c))==0 and rd32(c+12)==v: out.append(c)
    return sorted(set(out))

print('='*78); print('PART 4 robustness')
print('4a C1 filter variants (TD total / V / U):')
main=build(lambda b,i,e,st: True)
print('   base (ends @@, >=8 chars, dword[S-8] in rdata/data, dword[S-4]==0) -> %d (V=%d U=%d)'
      % (len(main),sum(1 for v in main.values() if v.startswith('.?AV')),
         sum(1 for v in main.values() if v.startswith('.?AU'))))
v2=build(lambda b,i,e,st: e<len(b) and b[e]==0)
print('   + require NUL terminator after @@                                    -> %d'%len(v2))
v3=build(lambda b,i,e,st: st.count('@@')==1)
print('   + exactly one @@ in string                                           -> %d'%len(v3))
v4=build(lambda b,i,e,st: True)  # identical, sanity
# TD VA uniqueness
print('   distinct TD VA=%d ; strings sharing one TD VA=%d'
      % (len(main), len(main)-len(set(main))))
# all TD in .rdata vs .data
print('   TD VA section: %s'%dict(collections.Counter(
    'rdata' if inse(v,RDATA) else 'data' for v in main)))

tds=main; cols=build_cols(tds)
kept=[c for c in cols if rd32(c+16)!=0]; K=set(kept)
print('\n4c COL alignment: total=%d; all 4-aligned=%s; all-TD 4-aligned=%s; all in .rdata/.data=%s'
      % (len(cols), all(c%4==0 for c in cols), all(rd32(c+12)%4==0 for c in cols),
         all(inse(c,RDATA) or inse(c,DATA) for c in cols)))
print('   COL VA section: %s'%dict(collections.Counter(
    'rdata' if inse(c,RDATA) else 'data' for c in cols)))

byclass=collections.defaultdict(list)
for c in kept: byclass[rd32(c+12)].append(c)
dist=collections.Counter(sum(1 for c in v if rd32(c+4)==0) for v in byclass.values())
print('\n4d per-class #mdisp0 distribution over 1214 (classes=%d): %s'
      % (len(byclass), dict(sorted(dist.items()))))
print('   classes with 0 mdisp0 -> %d ; with 2 -> %d'
      % (dist.get(0,0), dist.get(2,0)))
low={min(v) for v in byclass.values()}; md0={c for c in kept if rd32(c+4)==0}
rr={}
for c in kept:
    rr[c]=c
print('   |A|=%d |B|=%d equal=%s sym=%d'%(len(low),len(md0),low==md0,len(low^md0)))
print('   every multi class: mdisp0 COL == max VA COL ? %s'
      % all(max([c for c in v if rd32(c+4)==0] or [0])==max(v)
            for v in byclass.values() if len(v)>1))

# C4(b) restated under every natural reading, on 1214
refs=collections.defaultdict(list)
for o,v in dw.items():
    if v in K: refs[v].append(raw2va(o)+4)
n_all={c:len(refs.get(c,()))for c in kept}
def sn(va):
    for s in SECS:
        if s['va_lo']<=va<s['va_hi']: return s['name']
n_rd={c:sum(1 for v in refs.get(c,()) if sn(v-4)=='.rdata')for c in kept}
def nm(c): return tds.get(rd32(c+12),'?')
print('\n4e C4(b) restated on 1214 (target 1211):')
for tag,cnt in (('all-sec refs',n_all),('rdata refs',n_rd)):
    for au in ('.?AV only', 'any'):
        for eq in ('==1','<=1','==0'):
            s={c for c in kept if (nm(c).startswith('.?AV') if au=='.?AV only' else True)
               and (cnt[c]==1 if eq=='==1' else (cnt[c]<=1 if eq=='<=1' else cnt[c]==0))}
            print('   %-14s %-9s %-4s -> %-5d'%(tag,au,eq,len(s)))
print('   (a) kept & mdisp<=0x1000 -> %d'%sum(1 for c in kept if rd32(c+4)<=0x1000))

# vtable count sanity
allref=[v for L in refs.values() for v in L]
print('\n4f vtables pointing at kept COLs=%d ; distinct vt=%d'%(len(allref),len(set(allref))))
print('   refs by pos section: %s'%dict(collections.Counter(sn(v-4) for v in allref)))
json.dump({'c1':len(main),'classes':len(byclass),'mdisp0_dist':dict(dist),
           'A':len(low),'B':len(md0)},
          open(os.path.join(OUT,'audit_f01_p4.json'),'w'),indent=1)
print('\n-> audit_f01_p4.json')
