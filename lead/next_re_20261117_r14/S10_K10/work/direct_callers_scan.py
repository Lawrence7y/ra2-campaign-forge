from pathlib import Path
import sys,csv,struct,bisect
sys.path.insert(0,str(Path(__file__).parent))
from scan_candidates import load,feats
cov,atl,names,pe,data,image,off,string_at,md,dis=load()
textsec=next(s for s in pe.sections if s.Name.rstrip(b'\0')==b'.text')
tva=image+textsec.VirtualAddress; traw=textsec.PointerToRawData; tsize=textsec.SizeOfRawData
funcs=sorted((int(e,16),int(a['size'])) for e,a in atl.items())
def containing(va):
 i=bisect.bisect_right(funcs,(va,10**9))-1
 return format(funcs[i][0],'08X') if i>=0 and funcs[i][0]<=va<funcs[i][0]+funcs[i][1] else ''
calls={}
for o in range(traw,traw+tsize-5):
 if data[o]!=0xE8:continue
 rel=struct.unpack_from('<i',data,o+1)[0]
 site=tva+(o-traw); target=(site+5+rel)&0xffffffff
 calls.setdefault(target,[]).append((site,containing(site)))
prev={'0051D6F0','0051DAF0','0051B1F0','0051BAB0','00522340'}
rows=[]
for r in cov:
 if r['subsystem']!='S10' or r['grade']=='[已证]' or r['entry'].upper() in prev:continue
 e=r['entry'].strip().lower(); va=int(e,16)
 ins=dis(e); f=feats(ins,off,string_at,names)
 cs=calls.get(va,[]); known=[c for c in f['calls'] if c[1] and not c[1].startswith('sub_')]
 if cs:
  rows.append((len(cs),r['entry'],r['name'],atl[e]['size'],len(known),';'.join(sorted(set(c[1] for c in cs)))[:100],';'.join(x[1] for x in known[:8])))
rows.sort(reverse=True)
out=R if False else Path(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10_K10\EVIDENCE\DIRECT_CALLERS_SCAN.tsv')
with out.open('w',encoding='utf-8',newline='') as h:
 w=csv.writer(h,delimiter='\t',lineterminator='\n');w.writerow(['n_direct','entry','cov_name','size','known_callees','caller_entries','callees']);w.writerows(rows)
print('rows',len(rows))
for x in rows[:150]:print('\t'.join(map(str,x)))
