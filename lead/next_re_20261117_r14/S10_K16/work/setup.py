import os,sys,json,collections,struct,re
sys.path.insert(0,os.path.dirname(__file__))
import common
rows,cov,atl=common.load_rows()
def dump(a,n=512,size=None):
 if size is None: size=min(n,1024)
 for i in common.disasm(a,size)[:n]: print(common.fmt(i))
def covrow(a):
 r=cov.get(f'{a:08X}'); return (r[1],r[2],r[4]) if r else None
def slots(a): return common.class_at_slot(a)
