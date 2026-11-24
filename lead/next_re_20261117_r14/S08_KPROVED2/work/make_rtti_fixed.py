import json,struct,pefile,os
EXE=r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
SYM=r'D:\Project\ra2-campaign-forge\re_atlas\evidence\rtti\symbols.json'
OUT=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S08_KPROVED2\EVIDENCE\S08_RTTI_FIXED.tsv'
pe=pefile.PE(EXE); base=pe.OPTIONAL_HEADER.ImageBase; buf=open(EXE,'rb').read()
def off(va):
 for s in pe.sections:
  v=base+s.VirtualAddress
  if v<=va<v+max(s.Misc_VirtualSize,s.SizeOfRawData): return s.PointerToRawData+va-v
 return None
def u32(va):
 o=off(va); return struct.unpack('<I',buf[o:o+4])[0] if o is not None else None
def cstr(va):
 o=off(va); b=buf[o:o+160]; z=b.find(b'\x00'); return b[:z if z>=0 else len(b)].decode('latin1','replace')
sym=json.load(open(SYM,encoding='utf-8'))
entries=['0040D250','0045A070','0045A0A0','0045A0C0','0045A640','0045A680','0045A730','0045AB00','0045AB50','0045AC00','0045AC30','0045AC70','0045AC90','004D24A0','004D2510','004D27B0','004D27D0','004D2810','004D2910']
pref={'0040D250':'MouseClass','0045AB50':'?$DynamicVectorClass@PAVFoggedObjectClass@@','0045AC30':'?$DynamicVectorClass@PAVFoggedObjectClass@@'}
with open(OUT,'w',encoding='utf-8') as f:
 f.write('entry\tclass\tslot\tvt\tcol_raw\ttd_raw\trtti_name_raw\tslot_val\tchain_ok\tpreferred\n')
 for e in entries:
  a=int(e,16); hits=[]
  for cname,c in sym['classes'].items():
   for i,v in enumerate(c.get('vfuncs',[])):
    if int(v,16)!=a: continue
    vt=int(c['vtable_va'],16); col=u32(vt-4); td=u32(col+0xC) if col else None
    name=cstr(td+8) if td else ''
    slotval=u32(vt+4*i) if vt else None
    hits.append((cname,i,vt,col,td,name,slotval,bool(col and td and slotval==a)))
  for h in hits:
   cname,i,vt,col,td,name,slotval,ok=h
   is_pref=(pref.get(e)==cname) or (e not in pref and h==hits[0])
   f.write('\t'.join([e,cname,str(i),f'{vt:08X}',f'{col:08X}' if col else '',f'{td:08X}' if td else '',name,f'{slotval:08X}' if slotval else '',str(ok).lower(),str(is_pref).lower()])+'\n')
print('wrote',OUT)
