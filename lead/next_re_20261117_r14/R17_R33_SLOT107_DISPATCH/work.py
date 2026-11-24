#!/usr/bin/env python3
# R17-R33-SLOT107-DISPATCH: static read-only audit. Writes only this directory.
import os,re,csv,json,struct,hashlib,collections,pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
import capstone.x86_const as xc
IMG=r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
BASE=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
R12=os.path.join(BASE,"R17_R12_VT_OFFSET"); R28=os.path.join(BASE,"R17_R28_R12_REPAIR")
OUT=os.path.dirname(os.path.abspath(__file__))
EXPECT="73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476"
MD=Cs(CS_ARCH_X86,CS_MODE_32); MD.detail=True; REGS=('eax','ecx','edx','ebx','esp','ebp','esi','edi')
KNOWN={0x43B680,0x43B740,0x6F2B40,0x65A750,0x5B2DA0,0x6F4300,0x65A7E0,0x5F3B50,0x5A6510}
LIM=200
RID={r:getattr(xc,'X86_REG_'+r.upper()) for r in REGS}
def hx(x): return '0x%X'%x if x is not None else 'UNRESOLVED'
def load():
 b=open(IMG,'rb').read(); sha=hashlib.sha256(b).hexdigest().upper()
 if sha!=EXPECT: raise SystemExit('SHA mismatch '+sha)
 pe=pefile.PE(data=b); ib=pe.OPTIONAL_HEADER.ImageBase; ss={}
 for s in pe.sections:
  n=s.Name.decode('latin1').rstrip(chr(0))
  ss[n]=dict(va=ib+s.VirtualAddress,rva=s.VirtualAddress,raw=s.PointerToRawData,size=s.SizeOfRawData,vsize=s.Misc_VirtualSize)
 return b,sha,ib,ss
def off(ss,va):
 r=va-ss['.text']['va']+ss['.text']['rva']
 for s in ss.values():
  if s['rva']<=r<s['rva']+s['size']: return s['raw']+r-s['rva']
 return None
def u32(b,o): return struct.unpack_from('<I',b,o)[0] if o is not None and 0<=o+4<=len(b) else None
def vt(b,ss):
 t,rd,da=ss['.text'],ss['.rdata'],ss['.data']; lo,hi=t['va'],t['va']+t['vsize']; pr=bytes(range(32,127))
 def uv(va): return u32(b,off(ss,va))
 td={}; s,e=da['raw'],da['raw']+da['size']
 for o in range(s,e-8):
  if b[o:o+3]!=b'.?A': continue
  j=o+3
  while j<e and b[j] in pr and j-o<300: j+=1
  if j<e and b[j]==0 and j-o>=8:
   v=da['va']+o-s-8
   if uv(v)==0x7F9594 and uv(v+4)==0: td.setdefault(v,b[o:j].decode('ascii'))
 col={}; s,e=rd['raw'],rd['raw']+rd['size']
 for o in range(s,e-24,4):
  p=u32(b,o+12)
  if p not in td: continue
  co=off(ss,u32(b,o+16))
  if co is None or co+16>len(b): continue
  sig,attr,nb,ba=struct.unpack_from('<IIII',b,co)
  if sig==0 and attr<256 and 0<nb<4096 and off(ss,ba) is not None: col.setdefault(rd['va']+o-s,td[p])
 ent=set(); vtables=slots=0
 for o in range(s,e-4,4):
  if u32(b,o) not in col: continue
  vo=off(ss,rd['va']+o-s+4)
  if vo is None or vo<s or vo>=e: continue
  n=0; p=vo
  while p+4<=e:
   v=u32(b,p)
   if v is None or not lo<=v<hi: break
   ent.add(v); n+=1; p+=4
  if n: vtables+=1
  slots+=n
 return ent,dict(vtables=vtables,slots=slots,td=len(td),col=len(col),rdata_bytes=e-s,data_bytes=da['size'])
def structent(b,ss):
 t=ss['.text']; s,e=t['raw'],t['raw']+t['size']; lo,hi=t['va'],t['va']+t['vsize']; out=set(); calls=0
 for i in range(s,e-4):
  if b[i]!=0xE8: continue
  site=lo+i-s; d=site+5+struct.unpack_from('<i',b,i+1)[0]
  if lo<=d<hi: out.add(d); calls+=1
 pads=0; i=s
 while i<len(b):
  c=b[i]
  if c in (0x90,0xCC):
   j=i
   while j<len(b) and b[j]==c: j+=1
   if (c==0x90 and j-i>=4) or (c==0xCC and j-i>=2):
    va=lo+j-s
    if lo<=va<hi: out.add(va); pads+=1
   i=j
  else: i+=1
 return out,dict(direct_call_targets=calls,padding_starts=pads)
def trusted(b,ss):
 e,vi=vt(b,ss); se,si=structent(b,ss); t=ss['.text']; k={x for x in KNOWN if t['va']<=x<t['va']+t['vsize']}
 return e|se|k,dict(vinfo=vi,structural=si,vtable_unique=len(e),known=sorted(k),total=len(e|se|k))
def tsv(p):
 with open(p,newline='',encoding='utf8') as f: return list(csv.DictReader(f,delimiter='\t'))
def dis(b,ss,a,stop=None,end=False):
 o=off(ss,a)
 if o is None: return [],0
 t=ss['.text']; lim=min(t['raw']+t['size'],o+0x10000); r=[]; nb=0
 for x in MD.disasm(b[o:lim],a):
  nb+=x.size; r.append(x)
  if stop is not None and x.address>=stop: break
  if len(r)>=LIM: break
  if not end and x.mnemonic in ('ret','retf'): break
 return r,nb
def probe(b,ss,host,site):
 o=off(ss,host)
 if o is None: return False,None,0,0
 xs=list(MD.disasm(b[o:o+0x8000],host)); rr=next((x for x in xs if x.mnemonic in ('ret','retf')),None)
 reach=any(x.address==site for x in xs); ok=reach and rr is not None and rr.address>=site
 return ok,rr.address+rr.size if rr else None,len(xs),sum(x.address<=site for x in xs)
def mem(x):
 m=re.search(r'\[([^\]]+)\]',x.op_str)
 return m.group(1).strip() if m else ''
def scaled(m): return bool(re.search(r'\*\s*[248]\b',m,re.I))
def writers(xs,r,up):
 return [x for x in xs if x.address<up and x.operands and x.operands[0].type==1 and x.operands[0].reg==RID.get(r,r) and x.mnemonic not in ('cmp','test','push')]
def loopback(xs):
 a={x.address for x in xs}
 for x in xs:
  if x.mnemonic.startswith('j') and x.op_str.startswith('0x'):
   try:
    d=int(x.op_str.split()[0],16)
    if d<=x.address and d in a: return True
   except: pass
 return False
def classify(xs,base,site):
 near=writers(xs,base,site); ch=[]; cur=base; seen=set(); loop=loopback([x for x in xs if x.address<site]); sc=False; regs=[]
 for _ in range(5):
  if cur in seen: break
  seen.add(cur); wl=writers(xs,cur,site)
  if not wl: break
  w=wl[-1]; ch.append(hx(w.address)+' '+w.mnemonic+' '+w.op_str)
  if w.mnemonic in ('mov','lea') and len(w.operands)>=2:
   op=w.operands[1]
   if op.type==1: cur=MD.reg_name(op.reg) or op.reg; continue
   if op.type==2:
    m=w.op_str.split(',',1)[1].strip().strip('[]'); sc|=scaled(m); regs += [r for r in REGS if re.search(r'(?<![a-z0-9])'+r+r'(?![a-z0-9])',m,re.I)]
  break
 txt=ch[0] if ch else 'NO_WRITER_IN_PREFIX'; joined=' | '.join(ch)
 if near and near[-1].mnemonic=='mov' and re.search(r'\b'+base+r'\s*,\s*eax\b',near[-1].op_str,re.I):
  ct=None
  for x in reversed(xs):
   if x.address<near[-1].address and x.mnemonic=='call' and x.op_str.startswith('0x'):
    try: ct=int(x.op_str.split()[0],16)
    except: pass
    break
  if ct in (0x43B740,0x43B680): return 'a',joined+' CTOR='+hx(ct),txt
 if re.search(r'call\s+0x(43B740|43B680)\b',joined,re.I): return 'a',joined,txt
 if sc or (loop and any(r in ('eax','ecx','edx','ebx','esi','edi') for r in regs)): return 'b',joined+' LOOP='+str(loop)+' SCALED='+str(sc),txt
 if re.search(r'\b(esp|ebp)\b',txt,re.I):
  m=re.search(r'\[(esp|ebp)(?:\s*([+-])\s*(0x[0-9A-Fa-f]+|\d+))?\]',txt,re.I)
  if m:
   reg=m.group(1).lower(); sign=m.group(2) or '+'; v=m.group(3); v=int(v,16) if v and v.startswith('0x') else int(v) if v else 0
   if reg=='esp' or (reg=='ebp' and sign=='+' and 0<v<=0x20): return 'c',joined+' STACK_OR_ARG',txt
 if near and near[-1].mnemonic=='pop': return 'c',joined+' POP',txt
 if base in ('esp','ebp'): return 'c',joined+' BASE_IS_STACK',txt
 if re.search(r'\[(?:eax|ecx|edx|ebx|esi|edi)\b',txt,re.I): return 'd',joined+' MEMBER_CHAIN',txt
 return 'e',joined,txt
def feats(xs):
 offs=set(); ds=set(); n=0
 for x in xs:
  m=mem(x)
  if m:
   for h in re.findall(r'0x([0-9A-Fa-f]+)',m):
    if int(h,16) in (0x520,0x408,0x74): offs.add(int(h,16))
   n+=scaled(m)
  if x.mnemonic=='call' and x.op_str.startswith('dword ptr ['):
   m2=re.search(r'\+\s*(0x[0-9A-Fa-f]+)\]',x.op_str)
   if m2 and int(m2.group(1),16) in (0x124,0x1AC): ds.add(int(m2.group(1),16))
 return offs,ds,n
def wt(p,h,rows):
 with open(p,'w',newline='',encoding='utf8') as f:
  w=csv.writer(f,delimiter='\t',lineterminator='\n'); w.writerow(h); w.writerows(rows)
def main():
 b,sha,ib,ss=load(); tr,meta=trusted(b,ss)
 hf=tsv(os.path.join(R28,'host_fix.tsv')); hits={r['site']:r for r in tsv(os.path.join(R12,'hits.tsv'))}
 sites=sorted([r for r in hf if r['class']=='call' and r['disp']=='disp=0x1AC'],key=lambda r:int(r['site'],16))
 idx=sorted(set(int(i*85/11) for i in range(12)))
 while len(idx)<12:
  for j in range(86):
   if j not in idx: idx.append(j); break
 q=[]; bad=0; insetn=0
 for j in idx:
  r=sites[j]; site=int(r['site'],16); host=int(r['new_host'],16); ins=host in tr; insetn+=ins
  strict,fn,total,prefix=probe(b,ss,host,site); ok=(ins or strict) and fn is not None and host<=site<fn; bad+=not ok
  q.append([r['site'],hx(host),str(ins),str(strict),hx(fn),str(fn is not None and host<=site<fn),'OK' if ok else 'BAD','trusted_set='+str(ins)+'; strict_decode='+str(strict)+'; prefix_insns='+str(prefix)])
 if bad>=3:
  open(os.path.join(OUT,'REPORT.md'),'w',encoding='utf8').write(IMG+'\tsha256 '+sha+'\n\n输入不可信、本卡作废。\n')
  wt(os.path.join(OUT,'sites86.tsv'),['site','new_host','base_reg','source_class','evidence'],[])
  wt(os.path.join(OUT,'candidates.tsv'),['site','host','base_reg','evidence','offsets','disps','scaled','dual','verdict'],[])
  raise SystemExit('input untrusted '+str(bad))
 cat=collections.Counter(); rows=[]; fs=[]; funcs=set(); ni=nb=0
 for r in sites:
  site=int(r['site'],16); host=int(r['new_host'],16); base=hits[r['site']]['base_reg'].lower()
  xs,tb=dis(b,ss,host,stop=site); funcs.add(host); ni+=len(xs); nb+=tb
  c,ev,tx=classify(xs,base,site); cat[c]+=1; rows.append([r['site'],hx(host),base,'('+c+')',tx,ev[:600]]); fs.append((site,host,base,c,ev))
 rk=[]
 for site,host,base,c,ev in fs:
  if c!='b': continue
  rk.append(((3 if 'SCALED=True' in ev else 0)+(2 if 'LOOP=True' in ev else 0),site,host,base,ev))
 rk.sort(key=lambda x:(-x[0],x[1])); ck=rk[:8]; cr=[]; cn=0
 for sc,site,host,base,ev in ck:
  xs,tb=dis(b,ss,host,end=True); funcs.add(host); ni+=len(xs); nb+=tb
  os_,ds,sn=feats(xs); dual=0x124 in ds and 0x1AC in ds; cand=bool(os_ or dual); cn+=cand
  cr.append([hx(site),hx(host),base,ev[:280],','.join(hx(x) for x in sorted(os_)) or '-',','.join(hx(x) for x in sorted(ds)) or '-',str(sn),str(dual),'候选，需进一步验证' if cand else '未见Q3特征'])
 wt(os.path.join(OUT,'sites86.tsv'),['site','new_host','base_reg','来源类目','依据'],rows)
 wt(os.path.join(OUT,'candidates.tsv'),['site','host','base_reg','container_evidence','feature_offsets','disps','scaled_count','dual_dispatch','verdict'],cr)
 dist=', '.join('('+k+'):'+str(cat.get(k,0)) for k in 'abcde')
 L=[IMG+'\tsha256 '+sha,'','# R17-R33-SLOT107-DISPATCH 报告','','## 范围与边界','','- 纯静态只读；未建进程、未调试、未启动 gamemd；未改 R12/R28 目录；产物只写本目录。','- 入口集独立重建：RTTI 槽值 '+str(meta['vtable_unique'])+'（RTTI '+str(meta['vinfo'])+'）+ E8 目标 '+str(meta['structural']['direct_call_targets'])+' + padding '+str(meta['structural']['padding_starts'])+' + 构造器 '+str(len(meta['known']))+'，总计 '+str(meta['total'])+'；未用 C3/C2 字节扫入口。','- 反汇编 '+str(len(funcs))+' 个函数、'+str(ni)+' 条指令、'+str(nb)+' 字节；每函数上限 '+str(LIM)+' 条。','','## Q1','','等距抽样 12 条，成立 '+str(12-bad)+'，不成立 '+str(bad)+'；基础可信集命中 '+str(insetn)+' 条，其余由严格解码锚定；未触发停手阈值。','','| site | new_host | 在基础可信集 | 严格解码ret在site后 | fn_end | 范围内 | 判定 | 依据 |','|---|---|---|---|---|---|---|---|']
 L += ['| '+' | '.join(x)+' |' for x in q]
 L += ['','## Q2','','分布：'+dist+'。容器遍历类 (b) 共 '+str(cat.get('b',0))+' 条；全量见 sites86.tsv。','','## Q3','','从 (b) 类按 scaled/loop 排序抽查 '+str(len(ck))+' 点；检查 [obj+0x520]/[obj+0x408]/[obj+0x74] 和同 host 的 0x124+0x1AC 双派发。候选 '+str(cn)+' 个。','','| site | host | base_reg | 容器证据 | 特征偏移 | 派发偏移 | scaled | 双派发 | 判定 |','|---|---|---|---|---|---|---:|---|---|']
 L += ['| '+' | '.join(x)+' |' for x in cr]
 L += ['','## Q4','']
 L += ['取得高优先候选 '+str(cn)+' 个，均标候选、需进一步验证、待审计；未直接认定为 0x449440 的调用方。'] if cn else ['经容器遍历路径亦未取得 0x449440 的调用方。']
 L += ['','只证存在至少一个或未发现，不证唯一，不证运行期真的执行到；不改变 ②-b 的 [静态推断] 收口（D-53(A)，\u00A72.9 + \u00A72.10 的 (a\u2032) 不可拆）。','','## 产物','','REPORT.md、sites86.tsv、candidates.tsv、work.py。']
 open(os.path.join(OUT,'REPORT.md'),'w',encoding='utf8').write('\n'.join(L)+'\n')
 print(json.dumps(dict(sha=sha,sites=len(sites),q1_ok=12-bad,q1_bad=bad,cat=dict(cat),b=cat.get('b',0),checked=len(ck),candidates=cn,funcs=len(funcs),insns=ni,bytes=nb,meta=meta),indent=2,ensure_ascii=False))
if __name__=='__main__': main()
