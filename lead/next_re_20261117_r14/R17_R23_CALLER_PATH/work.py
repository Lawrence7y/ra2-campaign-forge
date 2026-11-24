import hashlib,struct,bisect,json,os
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32,CS_OP_MEM,CS_OP_REG,CS_OP_IMM,CS_GRP_JUMP,CS_GRP_CALL,CS_GRP_RET
IMG=r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
data=open(IMG,'rb').read(); sha=hashlib.sha256(data).hexdigest().upper()
pe=pefile.PE(data=data); ib=pe.OPTIONAL_HEADER.ImageBase
text=[s for s in pe.sections if s.Name.decode('latin1').rstrip('\0')=='.text'][0]
base=ib+text.VirtualAddress; raw=text.PointerToRawData; tsize=text.SizeOfRawData; vsize=text.Misc_VirtualSize
code=data[raw:raw+tsize]
def off(va): return va-base
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True
CTORS={0x43B740:'BuildingClassCtor_A',0x43B680:'BuildingClassCtor_B'}
SLOTS={0x124:'#73/0x43F180',0x1AC:'#107/0x449440'}
# Direct E8 calls in raw .text
calls=[]
for i in range(tsize-4):
 if code[i]!=0xE8: continue
 rel=struct.unpack_from('<i',code,i+1)[0]
 site=base+i; dst=site+5+rel
 calls.append((site,dst,i))
call_targets=sorted({d for s,d,i in calls if base<=d<base+vsize})
ctor_sites=[(s,d,i) for s,d,i in calls if d in CTORS]
# candidate function starts: direct call targets + after padding runs + section start
starts={base}
starts.update(call_targets)
i=0
while i<tsize-3:
 if code[i] in (0x90,0xCC):
  j=i
  while j<tsize and code[j]==code[i]: j+=1
  run=j-i
  if (code[i]==0x90 and run>=4) or (code[i]==0xCC and run>=2):
   if base+j<base+vsize: starts.add(base+j)
  i=j
 else: i+=1
starts=sorted(s for s in starts if base<=s<base+vsize)
def pick_host(site):
 cands=[x for x in starts if x<=site]
 return (max(cands),None) if cands else (None,None)
def fn_bounds(host,site):
 nxt=None
 for s in starts:
  if s>site: nxt=s; break
 if nxt is None: nxt=base+vsize
 ins=list(md.disasm(code[off(host):min(off(nxt),raw+tsize)],host,count=10000))
 rets=[x.address+x.size for x in ins if x.mnemonic.startswith('ret') and host<=x.address<min(nxt,base+vsize)]
 fnend=max(rets) if rets else nxt
 return fnend,nxt,ins
# Step 1 rows
site_rows=[]; hosts=[]
for site,dst,idx in sorted(ctor_sites):
 h,ins=pick_host(site)
 if not h: site_rows.append([hex(site),hex(dst),'UNKNOWN','UNKNOWN','FAIL']); continue
 fnend,nxt,allins=fn_bounds(h,site)
 host_ins=[x for x in allins if h<=x.address<fnend]
 assert h<=site<fnend, (h,site,fnend)
 site_rows.append([hex(site),hex(dst),hex(h),hex(fnend),'PASS %X <= %X < %X'%(h,site,fnend)])
 hosts.append((h,fnend,nxt,site,dst,host_ins,allins))
uniq={}
for h,fnend,nxt,site,dst,host_ins,allins in hosts:
 uniq.setdefault(h,(fnend,nxt,[site]))
# Step 2: all fixed-offset dispatch forms in each unique host
hits=[]
def mem_info(op):
 if op.type!=CS_OP_MEM: return None
 if op.mem.base==0: return None
 return op.mem.base,op.mem.disp
for h,(fnend,nxt,ctors) in uniq.items():
 ins=[x for x in md.disasm(code[off(h):min(off(fnend),raw+tsize)],h,count=10000) if h<=x.address<fnend]
 for j,x in enumerate(ins):
  if x.mnemonic=='call' and x.operands and x.operands[0].type==CS_OP_MEM:
   mi=mem_info(x.operands[0])
   if mi and mi[1] in SLOTS:
    hits.append((x.address,h,fnend,'call [base+disp]',md.reg_name(mi[0]),x.bytes.hex(),SLOTS[mi[1]],ctors))
  if x.mnemonic=='mov' and len(x.operands)>=2 and x.operands[0].type==CS_OP_REG and x.operands[1].type==CS_OP_MEM:
   mi=mem_info(x.operands[1]); dst=x.operands[0]
   if mi and mi[1] in SLOTS and dst.type==CS_OP_REG:
    for y in ins[j+1:j+9]:
     if y.mnemonic=='call' and y.operands and y.operands[0].type==CS_OP_REG and y.operands[0].reg==dst.reg:
      hits.append((x.address,h,fnend,'mov reg2,[base+disp]; call reg2',md.reg_name(mi[0]),x.bytes.hex()+' | '+y.bytes.hex(),SLOTS[mi[1]],ctors))
      break
# report
print('IMAGE',IMG); print('SHA',sha); print('TEXT',hex(base),hex(base+vsize),'SCAN_BYTES',tsize)
print('CTOR_SITES',len(site_rows))
for r in site_rows: print('CTOR','\t'.join(r))
print('UNIQUE_STEP2_FUNCS',len(uniq))
for h,(fe,nx,cts) in sorted(uniq.items()): print('FUNC',hex(h),hex(fe),'ctors',','.join(hex(c) for c in cts))
print('DISPATCH_HITS',len(hits))
for hit in hits: print('HIT','\t'.join([hex(hit[0]),hex(hit[1]),hex(hit[2]),hit[3],hit[4],hit[5],hit[6],','.join(hex(c) for c in hit[7])]))
# save machine-readable
with open(os.path.join(os.path.dirname(__file__),'_result.json'),'w',encoding='utf8') as f:
 json.dump({'image':IMG,'sha':sha,'text_base':hex(base),'scan_bytes':tsize,'ctor_sites':site_rows,'hosts':{hex(k):[hex(v[0]),hex(v[1]),[hex(c) for c in v[2]]] for k,v in uniq.items()},'hits':[[hex(x[0]),hex(x[1]),hex(x[2]),x[3],x[4],x[5],x[6],[hex(c) for c in x[7]]] for x in hits]},f,indent=2)
