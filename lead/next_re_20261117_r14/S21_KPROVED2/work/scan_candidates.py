import json,os,re,struct,hashlib,collections
import pefile,capstone
EXE=r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
BASE=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
OUT=os.path.join(BASE,'S21_KPROVED2')
pe=pefile.PE(EXE,fast_load=False); blob=open(EXE,'rb').read(); ib=pe.OPTIONAL_HEADER.ImageBase
sec={s.Name.rstrip(b'\0').decode():s for s in pe.sections}
t=sec['.text']; base=ib+t.VirtualAddress; code=t.get_data()[:t.Misc_VirtualSize]
def off(va): return pe.get_offset_from_rva(va-ib)
def dword(va):
 o=off(va); return struct.unpack('<I',blob[o:o+4])[0] if 0<=o<=len(blob)-4 else None
def cstr(va,n=96):
 o=off(va); b=blob[o:o+n]; z=b.find(b'\0'); return b[:z if z>=0 else len(b)].decode('ascii','replace')
def in_sec(va,name):
 s=sec.get(name); return s is not None and ib+s.VirtualAddress<=va<ib+s.VirtualAddress+(s.Misc_VirtualSize or s.SizeOfRawData)
def rtti_for_target(v):
 needle=struct.pack('<I',v); occ=[]
 for nm in ('.rdata','.data'):
  s=sec.get(nm)
  if not s: continue
  o=s.PointerToRawData; data=blob[o:o+s.SizeOfRawData]; st=0
  while True:
   i=data.find(needle,st)
   if i<0: break
   occ.append(ib+s.VirtualAddress+i); st=i+1
 res=[]
 for ova in occ:
  vts=[ova]; p=ova-4
  while len(vts)<80:
   q=dword(p)
   if q is None or not in_sec(q,'.text'): break
   vts.append(p); p-=4
  for vt in vts:
   col=dword(vt-4); td=dword(col+0xC) if col and 0x400000<=col<0x900000 else None
   nm=cstr(td+8) if td and 0x400000<=td<0x900000 else ''
   if nm.startswith(('.?AV','.?AU')):
    res.append(dict(vt=vt,slot=(ova-vt)//4,col=col,td=td,name=nm)); break
 return occ,res
cs=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); cs.detail=True; cs.skipdata=True
ins=[]; e8=0
for i in cs.disasm(code,base):
 ins.append((i.address,i.size,i.mnemonic,i.op_str,bytes(i.bytes).hex()))
 if i.mnemonic=='call' and i.size==5 and i.bytes[0]==0xE8: e8+=1
by={a:(s,m,o,b) for a,s,m,o,b in ins}
direct=collections.defaultdict(list)
for a,s,m,o,b in ins:
 if m=='call' and s==5 and b.startswith('e8'):
  rel=int.from_bytes(bytes.fromhex(b[2:]),'little',signed=True); direct[a+5+rel].append(a)
# 19 selfcheck
noindex=0; zeroindex=0; memops=0
cs2=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); cs2.detail=True
for a,s,m,o,b in ins:
 if b in ('00',): continue
 i=next(cs2.disasm(bytes.fromhex(b),a),None)
 if not i: continue
 for op in i.operands:
  if op.type==capstone.x86.X86_OP_MEM:
   memops+=1
   if not hasattr(op,'index'): noindex+=1
   if op.mem.index==0: zeroindex+=1
cov=[]
with open(os.path.join(BASE,'COVERAGE','coverage.tsv'),encoding='utf-8') as f:
 h=f.readline().rstrip('\n').split(',')
 for line in f:
  if line.strip(): cov.append(dict(zip(h,line.rstrip('\n').split('\t'))))
atlas=set()
with open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv',encoding='utf-8') as f:
 f.readline()
 for line in f:
  if line.strip(): atlas.add(line.split('\t')[0].upper().replace('0X',''))
s21a=[r for r in cov if r['subsystem'].upper()=='S21' and r['entry'].upper().replace('0X','') in atlas]
s21raw=[r for r in cov if r['subsystem'].upper()=='S21']
cnt=lambda rows:dict(collections.Counter(r['grade'] for r in rows))
# function extents from atlas entry+size (recomputed direct)
atlas_rows={}
with open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv',encoding='utf-8') as f:
 f.readline()
 for line in f:
  c=line.rstrip('\n').split('\t'); atlas_rows[c[0].upper().replace('0X','')]=int(c[1],0) if c[1].lower().startswith('0x') else int(c[1])
def body(e,sz):
 arr=[];a=e;lim=e+sz
 while a<lim:
  v=by.get(a)
  if not v: break
  arr.append((a,)+v); a+=v[0]
 return arr
outrows=[]
for r in s21a:
 e=int(r['entry'],16); sz=atlas_rows.get(r['entry'].upper().replace('0X',''),0)
 arr=body(e,sz) if sz else []
 # fall back to next-entry extent for no-atlas-size
 if not arr: continue
 txt='\n'.join(f'{m} {o}' for _,_,m,o,_ in arr)
 # jumps / loops / guards / mem shape / error codes
 jumps=[(a,o) for a,s,m,o,b in arr if m in ('jmp','je','jne','jz','jnz','jg','jge','jl','jle','ja','jae','jb','jbe','js','jns') and re.fullmatch(r'0x[0-9a-f]+',o)]
 backward=[(a,o) for a,o in jumps if int(o,16)<=a]
 guard_cmp=[(a,m,o) for a,s,m,o,b in arr if m.startswith('cmp')]
 # indirect jump tables: jmp with mem operand
 ijump=[(a,o) for a,s,m,o,b in arr if m=='jmp' and 'ptr [' in o]
 # memory shape: vt writes or many distinct field writes
 vtwr=set(); fields=set()
 for a,s,m,o,b in arr:
  if m=='mov' and o.startswith('dword ptr ['):
   mm=re.search(r'\], (0x[0-9a-f]+)$',o)
   if mm:
    v=int(mm.group(1),16)
    if 0x7d0000<=v<0x850000: vtwr.add(v)
   mm=re.search(r'\+ (0x[0-9a-f]+)\]',o)
   if mm: fields.add(int(mm.group(1),16))
 err=bool(re.search(r'\bor eax, 0xffffffff\b|\bmov eax, 0xffffffff\b|\bcmp .*, -1\b|\bcmp .*, 0xffffffff\b',txt))
 occ,rtti=rtti_for_target(e)
 ext=sorted(set(direct.get(e,[])))
 outrows.append(dict(entry=r['entry'],name=r['name'],grade=r['grade'],sem=r['one_line_semantics'],size=sz,n=len(arr),
   n_jump=len(jumps),n_back=len(backward),n_cmp=len(guard_cmp),n_ijump=len(ijump),
   vtwr=sorted(hex(x) for x in vtwr),n_field=len(fields),err=err,n_direct=len(ext),direct=ext[:12],
   occ=len(occ),rtti=rtti[:4],calls=sorted(set(o for _,_,m,o,_ in arr if m=='call' and re.fullmatch(r'0x[0-9a-f]+',o)))[:40]))
out=dict(instructions=len(ins),e8=e8,sha256=hashlib.sha256(blob).hexdigest(),text_va=hex(base),text_vsize=hex(t.Misc_VirtualSize),memops=memops,noindex=noindex,zeroindex=zeroindex,raw=dict(collections.Counter(r['grade'] for r in s21raw)),atlas=dict(collections.Counter(r['grade'] for r in s21a)),atlas_n=len(s21a),raw_n=len(s21raw),rows=outrows)
json.dump(out,open(os.path.join(OUT,'work','candidates.json'),'w',encoding='utf-8'),indent=2,ensure_ascii=False)
print('instructions',len(ins),'E8',e8,'sha',out['sha256'][:8],'memops',memops,'noindex',noindex,'zeroindex',zeroindex)
print('raw',out['raw'],'atlas',out['atlas'],'n',len(s21a))
# print top candidates by likely 3b
rank=sorted(outrows,key=lambda x:(x['n_ijump']>0,x['n_back']>=1 and x['n_field']>=6,x['err'],x['n_cmp']>=3,x['n_direct']>0,x['n']),reverse=True)
for x in rank[:35]:
 print(x['entry'],x['grade'][:6],'n',x['n'],'jmp',x['n_jump'],'back',x['n_back'],'ijmp',x['n_ijump'],'cmp',x['n_cmp'],'vt',len(x['vtwr']),'fld',x['n_field'],'err',int(x['err']),'dir',x['n_direct'],'occ',x['occ'],x['name'][:38])
