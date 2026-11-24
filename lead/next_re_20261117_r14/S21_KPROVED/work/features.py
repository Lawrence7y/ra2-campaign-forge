import json,os,re
import pefile,capstone
EXE=r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
BASE=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
OUT=os.path.join(BASE,'S21_KPROVED','work')
pe=pefile.PE(EXE); ib=pe.OPTIONAL_HEADER.ImageBase
t=[s for s in pe.sections if s.Name.rstrip(b'\0')==b'.text'][0]
base=ib+t.VirtualAddress; code=t.get_data()[:t.Misc_VirtualSize]
cs=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); cs.skipdata=True
by={i.address:(i.size,i.mnemonic,i.op_str,bytes(i.bytes).hex()) for i in cs.disasm(code,base)}
cov=[]
with open(os.path.join(BASE,'COVERAGE','coverage.tsv'),encoding='utf-8') as f:
 h=f.readline().rstrip('\n').split(',')
 for line in f:
  if line.strip():
   c=line.rstrip('\n').split('\t'); cov.append(dict(zip(h,c)))
entries=sorted(int(r['entry'],16) for r in cov)
nextent={e:next((x for x in entries if x>e),base+len(code)) for e in entries}
s21=[r for r in cov if r['subsystem']=='S21']
res=[]
for r in s21:
 e=int(r['entry'],16); end=min(nextent[e],e+0x1800)
 arr=[]; a=e
 while a<end and len(arr)<900:
  v=by.get(a)
  if not v: break
  arr.append((a,v[1],v[2],v[3]))
  a+=by[a][0]
 txt='\n'.join(f'{m} {o}' for _,m,o,_ in arr)
 loops=[]; calls=[]; wdisp=set(); vts=set()
 for a,m,o,b in arr:
  if m in ('jmp','jl','jle','jg','jge','jb','jbe','ja','jae','jne','je','loop') and o.startswith('0x'):
   tgt=int(o,16)
   if tgt<=a: loops.append((a,tgt,m))
  if m=='call' and o.startswith('0x'):
   calls.append(int(o,16))
  mm=re.match(r'mov dword ptr \[(?:[a-z]+|[^]]*)\], (0x[0-9a-f]+)$',o)
  if mm:
   val=int(mm.group(1),16)
   if 0x7e0000<=val<0x850000: vts.add(val)
  mm=re.match(r'mov (?:dword|byte|word) ptr \[[^]]*\+ (0x[0-9a-f]+)\],',o)
  if mm: wdisp.add(mm.group(1))
 feat={
  'entry':r['entry'],'name':r['name'],'grade':r['grade'],'n':len(arr),'bytes':end-e,
  'loops':len(loops),'calls':calls[:20],'n_calls':len(calls),
  'or_minus1':('or eax, 0xffffffff' in txt or 'or eax, -1' in txt or 'mov eax, 0xffffffff' in txt),
  'cmp_minus1':('cmp eax, -1' in txt or 'cmp dword' in txt and '0xffffffff' in txt),
  'eq_loop':('mov al, 1' in txt and len(loops)>=1 and 'cmp esi, dword ptr [edi + 8]' in txt),
  'find_loop':(('or eax, 0xffffffff' in txt) and len(loops)>=1),
  'copy_loop':(len(loops)>=1 and sum(1 for _,m,o,_ in arr if m=='mov' and re.search(r'mov dword ptr \[[a-z]+[^]]*\], [a-z]+',o))>=2),
  'delete_loop':(len(loops)>=1 and 0x7c8b3d in calls),
  'alloc0x7c8e17':(0x7c8e17 in calls),
  'vts':sorted(hex(x) for x in vts),'wdisp':sorted(wdisp),
 }
 feat['strong_candidate']=feat['eq_loop'] or feat['find_loop'] or feat['copy_loop'] or feat['delete_loop']
 res.append(feat)
with open(os.path.join(OUT,'features.json'),'w',encoding='utf-8') as f: json.dump(res,f,indent=2,ensure_ascii=False)
with open(os.path.join(OUT,'features.tsv'),'w',encoding='utf-8') as f:
 f.write('entry\tgrade\tname\tn\tloops\tn_calls\tor_minus1\teq_loop\tfind_loop\tcopy_loop\tdelete_loop\tstrong_candidate\tvts\n')
 for x in res:
  f.write('\t'.join(map(str,[x['entry'],x['grade'],x['name'],x['n'],x['loops'],x['n_calls'],int(x['or_minus1']),int(x['eq_loop']),int(x['find_loop']),int(x['copy_loop']),int(x['delete_loop']),int(x['strong_candidate']),','.join(x['vts'])]))+'\n')
print('rows',len(res),'strong',sum(x['strong_candidate'] for x in res))
