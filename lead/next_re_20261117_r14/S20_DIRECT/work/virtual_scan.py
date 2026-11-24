#!/usr/bin/env python3
# Determine vtable-reachability of S20 rows via .rdata aligned dword scan.
import os,sys,io,struct,json
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8',errors='replace')
import pefile
ROOT=r"D:\Project\ra2-campaign-forge"; OUT=os.path.join(ROOT,"lead","next_re_20261117_r14","S20_DIRECT")
WK=os.path.join(OUT,"work"); EV=os.path.join(OUT,"EVIDENCE"); EXE=os.path.join(ROOT,"ra2youli","gamemd.exe")
COV=os.path.join(ROOT,"lead","next_re_20261117_r14","COVERAGE","coverage.tsv")
data=open(EXE,'rb').read(); pe=pefile.PE(EXE,fast_load=True); ib=pe.OPTIONAL_HEADER.ImageBase
# collect all data sections rdata + data (vtables live in .rdata)
rdata=None
for s in pe.sections:
    nm=s.Name.rstrip(b'\x00').decode()
    if nm=='.rdata':
        rdata=(ib+s.VirtualAddress, data[s.PointerToRawData:s.PointerToRawData+s.SizeOfRawData])
print('rdata VA',hex(rdata[0]),'size',hex(len(rdata[1])))
# S20 rows
rows=[]
for l in open(COV,encoding='utf-8').read().splitlines()[1:]:
    if not l.strip():continue
    f=l.split('\t')
    if f[1]=='S20': rows.append(dict(entry=f[0],name=f[2],sem=f[3],grade=f[4]))
# upgraded set (from direct hits)
upgraded=set()
for l in open(os.path.join(WK,'s20_direct_hits.tsv'),encoding='utf-8').read().splitlines()[1:]:
    f=l.split('\t')
    if int(f[3])>0 and f[1]!='[已证]': upgraded.add(f[0])
print('to-upgrade:',len(upgraded))
# scan rdata aligned dwords
rva,raw=rdata; base=rva
dword_set={}
for off in range(0,len(raw)-3,4):
    v=struct.unpack_from('<I',raw,off)[0]
    dword_set.setdefault(v,[]).append(base+off)
# check each S20 non-proved, non-upgraded row
virt=[]
for r in rows:
    if r['entry'] in upgraded or r['grade']=='[已证]':continue
    e=int(r['entry'],16)
    locs=dword_set.get(e,[])
    if locs:
        virt.append(dict(entry=r['entry'],name=r['name'],sem=r['sem'],grade=r['grade'],vrefs=[f'{x:08X}' for x in locs[:6]],nvrefs=len(locs)))
print('S20 rows vtable/dword-reachable in .rdata:',len(virt))
json.dump(virt,open(os.path.join(EV,'virtual_reachable_rows.json'),'w',encoding='utf-8'),indent=2,ensure_ascii=False)
for v in virt[:20]:print('  ',v['entry'],v['grade'],v['name'],'nvrefs',v['nvrefs'],v['vrefs'][:3])
print('wrote virtual_reachable_rows.json')
