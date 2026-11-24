from __future__ import annotations
import os,re,sys
ROOT=r'D:\Project\ra2-campaign-forge'
CARD=ROOT+r'\lead\next_re_20261117_r14\S17_K6'
TARGETS=['004068E0','0040E340','00427940','0042E410','00433CF0','004355B0','0043AE50','0049F740','0049F8B0','00773450']
NAMES=['MemoryBuffer::Clear','ColorStruct::ColorStruct','ColorStruct::Set','RectangleStruct::Set','LTRBStruct::Set','Clear_OwnedBuffer','ColorStruct_ctor','BufferMemory::Clear']
variants=[]
for t in TARGETS:
 variants.append((t,t)); variants.append((t,t.lower())); variants.append((t,'0x'+t.lower())); variants.append((t,'0x'+t.upper())); variants.append((t,t[2:].lower()))
namevars=[]
for n in NAMES: namevars.append((n,n)); namevars.append((n.lower(),n))
hits={t:[] for t in TARGETS}; nhits={n:[] for n in NAMES}
files=0
for dp,dns,fns in os.walk(ROOT):
 dns[:]=[d for d in dns if d not in ('.git','node_modules','__pycache__')]
 for fn in fns:
  p=os.path.join(dp,fn)
  if p.startswith(CARD):continue
  try:
   sz=os.path.getsize(p)
   if sz>80*1024*1024:continue
   b=open(p,'rb').read()
  except:continue
  files+=1
  text=b.decode('utf-8',errors='ignore')
  lines=text.splitlines()
  for needle,key in variants:
   if needle and needle.lower() in text.lower():
    for i,ln in enumerate(lines,1):
     if needle.lower() in ln.lower():hits[key].append((p,i,ln.strip()[:300]))
    if needle.lower() in b.decode('latin1').lower() and not any(p==x[0] for x in hits[key]):hits[key].append((p,0,'<binary-or-nonutf8 hit>'))
  for needle,key in namevars:
   if needle.lower() in text.lower():
    for i,ln in enumerate(lines,1):
     if needle.lower() in ln.lower():nhits[key].append((p,i,ln.strip()[:300]))
out=['S17-K6 repository-wide conflict/source scan','files_scanned='+str(files),'']
for t in TARGETS:
 hs=hits[t]
 out.append('ADDRESS '+t+' hits='+str(len(hs)))
 for p,i,ln in hs[:40]:out.append('  '+os.path.relpath(p,ROOT)+':'+str(i)+' | '+ln)
 out.append('')
out.append('NAME CONFLICTS / PRIOR SOURCES')
for n in NAMES:
 hs=nhits[n]
 out.append('NAME '+n+' hits='+str(len(hs)))
 for p,i,ln in hs[:40]:out.append('  '+os.path.relpath(p,ROOT)+':'+str(i)+' | '+ln)
 out.append('')
open(CARD+r'\EVIDENCE\conflict_address_scan.txt','w',encoding='utf-8').write('\n'.join(out)+'\n')
print('files',files)
for t in TARGETS:print(t,len(hits[t]))
for n in NAMES:print(n,len(nhits[n]))
