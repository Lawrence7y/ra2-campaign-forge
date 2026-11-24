import struct,pefile
from capstone import *
pe=pefile.PE(r'D:/Project/ra2-campaign-forge/ra2youli/gamemd.exe');base=pe.OPTIONAL_HEADER.ImageBase;d=pe.__data__
text=[s for s in pe.sections if s.Name.rstrip(b'\x00')==b'.text'][0]
st=base+text.VirtualAddress;en=st+text.SizeOfRawData
cs=Cs(CS_ARCH_X86,CS_MODE_32);cs.skipdata=True
targets=[0x41ba90,0x5b35e0,0x6b6ea0,0x6b6c90,0x6b6fa0,0x6b7f10]
byva={t:[] for t in targets}
for ins in cs.disasm(d[text.PointerToRawData:text.PointerToRawData+text.SizeOfRawData],st):
 if ins.mnemonic=='call' and ins.op_str.startswith('0x'):
  try:v=int(ins.op_str,16)
  except:continue
  if v in byva:byva[v].append(ins.address)
for t in targets:
 hits=byva[t]
 print(hex(t),'E8-callers',len(hits),[hex(x) for x in hits[:30]])
