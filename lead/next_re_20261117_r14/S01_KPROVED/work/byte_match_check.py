# -*- coding: utf-8 -*-
import os,re,struct
YRPP=r"D:\Project\ra2-campaign-forge\YRpp"
patterns=['A8B238','A8B230','A8ED6B','284C','34BD','A8DA78','AC4F58','7E2AC0','A8E9C0']
for pat in patterns:
  found=[]
  for root,dirs,files in os.walk(YRPP):
    for fn in files:
      if not re.search(r'\.(h|hpp|cpp|c|cc)$',fn,re.I): continue
      fp=os.path.join(root,fn)
      try: txt=open(fp,encoding='utf8',errors='replace').read()
      except: continue
      for ln,line in enumerate(txt.splitlines(),1):
        if re.search(pat,line,re.I): found.append((os.path.basename(fp),ln,line.strip()[:110]))
  print(f'pat {pat}: {len(found)} hits {found[:4]}')
import pefile
from capstone import *
from capstone.x86 import *
EXE=r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
PE=pefile.PE(EXE,fast_load=False); IB=PE.OPTIONAL_HEADER.ImageBase; DATA=PE.__data__
SECS=[(s.Name.rstrip(b'\x00').decode('latin1'),s.VirtualAddress,s.Misc_VirtualSize,s.SizeOfRawData,s.PointerToRawData) for s in PE.sections]
def rd(va,n):
  r=va-IB
  for nm,va0,vs,rs,rp in SECS:
    if va0<=r<va0+rs: return DATA[rp+(r-va0):rp+(r-va0)+n]
  return b''
MD=Cs(CS_ARCH_X86,CS_MODE_32); MD.detail=True
sites=[0x4ad011,0x4ad0af,0x534a63,0x598b30,0x5a51ff]
print('\nverify direct call boundaries:')
for site in sites:
  code=rd(site,8); ins=list(MD.disasm(code,site)); ok=False; detail='noins'
  if ins:
    i=ins[0]
    if i.id==X86_INS_CALL and i.bytes[0]==0xE8:
      rel=struct.unpack('<i',i.bytes[1:5])[0]; tgt=(site+5+rel)&0xFFFFFFFF
      ok=(tgt==0x69AE90); detail=f'{i.mnemonic} {i.op_str} -> {tgt:08X}'
  print(f'  {site:08X}: {code[:5].hex()} {detail} OK={ok}')
