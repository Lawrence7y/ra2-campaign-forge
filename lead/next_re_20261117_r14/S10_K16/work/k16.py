
import os,sys,json,collections,struct,re
sys.path.insert(0,os.path.dirname(__file__))
import common
rows,cov,atl=common.load_rows()
def load_atl():
 out=[]
 for k,r in atl.items():
  if k=='entry': continue
  try: out.append((int(k,16),int(r[1])))
  except: pass
 return sorted(out)
FUNCS=load_atl()
def row(a): return cov.get(f'{a:08X}')
def cls(a): return common.class_at_slot(a)
def direct_calls_in(a,size):
 return [(i.address,common.call_target(i)) for i in common.disasm(a,size) if common.call_target(i) is not None]
def callers_of(targets):
 targets=set(targets); by=collections.defaultdict(list)
 for a,size in FUNCS:
  for site,t in direct_calls_in(a,size):
   if t in targets: by[t].append((site,a))
 return by
def vcall_sites(disp):
 out=[]
 cand=re.compile(r'\[\w+ \+ 0x'+f'{disp:x}'+r'\]')
 for a,size in FUNCS:
  for j,i in enumerate(common.disasm(a,size)):
   if i.mnemonic=='call' and cand.search(i.op_str): out.append((i.address,a,j))
 return out
