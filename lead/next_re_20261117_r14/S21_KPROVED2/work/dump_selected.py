import json,os,re,struct
import pefile,capstone
EXE=r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
BASE=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
OUT=os.path.join(BASE,'S21_KPROVED2')
c=json.load(open(os.path.join(OUT,'work','candidates.json'),encoding='utf-8'))
sel=['00596300','00686B20','00599650','00684620','00638120','00687F10','0063A5A0','0049DB00','0049C0D0','00685670','00685DC0','0063AD50']
pe=pefile.PE(EXE,fast_load=False); blob=open(EXE,'rb').read(); ib=pe.OPTIONAL_HEADER.ImageBase
t=[s for s in pe.sections if s.Name.rstrip(b'\0')==b'.text'][0]; base=ib+t.VirtualAddress; code=t.get_data()[:t.Misc_VirtualSize]
cs=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); cs.detail=True; cs.skipdata=True
by={i.address:(i.size,i.mnemonic,i.op_str,bytes(i.bytes).hex()) for i in cs.disasm(code,base)}
atlas={}
with open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv',encoding='utf-8') as f:
 f.readline()
 for l in f:
  q=l.rstrip('\n').split('\t'); atlas[q[0]]=int(q[1],0)
allf='\n'.join(f'### {r["entry"]} {r["grade"]} {r["name"]}\n'+ '\n'.join(f'{a:08X} +{a-int(r["entry"],16):04X} {b:<20} {m} {o}' for a,s,m,o,b in []) for r in c['rows'] if r['entry'] in sel)
with open(os.path.join(OUT,'EVIDENCE','selected_bodies.txt'),'w',encoding='utf-8') as f:
 for e in sel:
  v=int(e,16); sz=atlas.get(e,0)
  f.write(f'\n### {e} size={sz:#x}\n')
  a=v
  while a<v+sz:
   z=by.get(a)
   if not z: break
   s,m,o,b=z
   f.write(f'{a:08X} +{a-v:04X} {b:<20} {m} {o}\n')
   a+=s
print('wrote',os.path.join(OUT,'EVIDENCE','selected_bodies.txt'))
