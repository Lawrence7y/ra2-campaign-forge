import json,os,struct
import pefile,capstone
EXE=r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
OUT=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S21_KPROVED2'
c=json.load(open(os.path.join(OUT,'work','candidates.json'),encoding='utf-8'))
st=[r for r in c['rows'] if r['grade']=='[静态推断]' and r['vtwr']]
pe=pefile.PE(EXE,fast_load=False); blob=open(EXE,'rb').read(); ib=pe.OPTIONAL_HEADER.ImageBase
def off(va): return pe.get_offset_from_rva(va-ib)
def dword(va):
 o=off(va); return struct.unpack('<I',blob[o:o+4])[0] if 0<=o<=len(blob)-4 else None
# for each vt write value, check if it contains this entry at any slot
res=[]
for r in st:
 e=int(r['entry'],16); hits=[]
 for vh in r['vtwr']:
  vt=int(vh,16)
  for slot in range(0,400):
   q=dword(vt+4*slot)
   if q is None or not (0x400000<=q<0x800000): break
   if q==e: hits.append((vh,slot))
 res.append((r['entry'],r['name'],hits,r['occ'],r['n_direct']))
json.dump(res,open(os.path.join(OUT,'EVIDENCE','ctor_live_vtable_check.json'),'w',encoding='utf-8'),indent=2,ensure_ascii=False)
for x in res: print(x)
