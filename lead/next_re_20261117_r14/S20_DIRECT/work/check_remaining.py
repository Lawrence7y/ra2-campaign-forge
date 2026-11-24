#!/usr/bin/env python3
import os,sys,io,struct,json
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8',errors='replace')
import pefile
ROOT=r"D:\Project\ra2-campaign-forge";OUT=os.path.join(ROOT,"lead","next_re_20261117_r14","S20_DIRECT")
WK=os.path.join(OUT,"work");EV=os.path.join(OUT,"EVIDENCE");EXE=os.path.join(ROOT,"ra2youli","gamemd.exe")
COV=os.path.join(ROOT,"lead","next_re_20261117_r14","COVERAGE","coverage.tsv")
data=open(EXE,'rb').read();pe=pefile.PE(EXE,fast_load=True);ib=pe.OPTIONAL_HEADER.ImageBase
s=[x for x in pe.sections if x.Name.rstrip(b'\x00').decode()=='.rdata'][0]
raw=data[s.PointerToRawData:s.PointerToRawData+s.SizeOfRawData];base=ib+s.VirtualAddress
ds=set()
for off in range(0,len(raw)-3,4):ds.add(struct.unpack_from('<I',raw,off)[0])
rows=[]
for l in open(COV,encoding='utf-8').read().splitlines()[1:]:
    if not l.strip():continue
    f=l.split('\t')
    if f[1]=='S20':rows.append(dict(entry=f[0],name=f[2],sem=f[3],grade=f[4]))
upg=set()
for l in open(os.path.join(WK,'s20_direct_hits.tsv'),encoding='utf-8').read().splitlines()[1:]:
    f=l.split('\t')
    if int(f[3])>0 and f[1]!='[已证]':upg.add(f[0])
virt=json.load(open(os.path.join(EV,'virtual_reachable_rows.json'),encoding='utf-8'))
vset=set(v['entry'] for v in virt)
nonproved=[r for r in rows if r['grade']!='[已证]']
remain=[r for r in nonproved if r['entry'] not in upg and r['entry'] not in vset]
print('non-proved total',len(nonproved),'upgraded',len(upg),'virt',len(vset),'remaining(unresolved neither):',len(remain))
for r in remain:print('  ',r['entry'],r['grade'],r['name'],r['sem'][:50])
# of upgraded, how many also vtable reachable
both=[e for e in upg if int(e,16) in ds]
print('upgraded rows ALSO vtable-reachable (direct chosen as stronger):',len(both),sorted(both))
