from __future__ import annotations
import sys,struct
sys.path.insert(0,r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S17-F1\work')
import pe_util as pu
ATL=r'D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv'
raw=open(ATL,'r',encoding='utf-8-sig').read().splitlines(); hdr=raw[0].split('\t'); meta={}; ints=[]
for ln in raw[1:]:
 p=ln.split('\t'); p+=['']*(len(hdr)-len(p)); d=dict(zip(hdr,p))
 try:a=int(d['entry'],16); b=a+int(d.get('size','0'))
 except:continue
 meta[a]=d; ints.append((a,b))
ints.sort()
def owner(va):
 for a,b in ints:
  if a<=va<b:return a
 return None
def td_name(td):
 b=pu.read(td+8,200) or b''; s=b.split(b'\0')[0]
 try:n=s.decode('ascii')
 except:return None
 return n if n.startswith('.?AV') and n.endswith('@@') else None
def col_td(col):
 for off in (8,0xC,4):
  td=pu.u32(col+off)
  if td and td_name(td):return off,td,td_name(td)
 return None
rows=[]
for name,vb,vs,pr,rs,ch in pu.sections():
 if ch & 0x20000000: continue
 data=pu.read(vb,rs) or b''
 for i in range(0,len(data)-4,4):
  a=vb+i; col=struct.unpack_from('<I',data,i)[0]
  if not col:continue
  rr=col_td(col)
  if not rr:continue
  off,td,n=rr; mem=[]
  for k in range(0,400):
   v=pu.u32(a+4+4*k)
   if v is None or owner(v) is None:break
   o=owner(v); mem.append((a+4+4*k,v,o,meta[o].get('name','')))
  if mem: rows.append((a,col,off,td,n,mem))
lines=['S17-K6 RTTI/vtable census','vtable_count='+str(len(rows))]
for a,col,off,td,n,mem in rows:
 if any(x in n.lower() for x in ['file','swizzle','buffer','straw','pipe','rect','color','point','stream']):
  lines.append('\nVT %08X COL %08X off +%X TD %08X %s slots=%d'%(a,col,off,td,n,len(mem)))
  for k,(addr,v,o,nm) in enumerate(mem[:80]):
   lines.append('  slot%-3d %08X -> %08X %s'%(k,v,o,nm))
out=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S17_K6\EVIDENCE\rtti_vtables_relevant.txt'
open(out,'w',encoding='utf-8').write('\n'.join(lines)+'\n')
print('\n'.join(lines[:20000]))