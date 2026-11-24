import sys,os,struct,re
sys.path.insert(0,r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S17-F1\work')
import pe_util as pu
CARD=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STRS=[0x81F408,0x81F4C0,0x81F51C,0x81F554,0x81F55A,0x81F598,0x81F5B8]
# atlas intervals
ATL=r'D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv'
ints=[]
for ln in open(ATL,'r',encoding='utf-8-sig').read().splitlines()[1:]:
 p=ln.split('\t')
 if len(p)>=2: ints.append((int(p[0],16),int(p[0],16)+int(p[1])))
ints.sort()
def owner(va):
 lo,hi=0,len(ints)
 # linear ok for few refs
 for a,b in ints:
  if a<=va<b: return a,b
 return None
lines=[]
lines.append('S17-K5 xrefs to COPYPROTECTION/WChat strings')
for va in STRS:
 raw=pu.read(va,96) or b''
 s=raw.split(b'\0')[0].decode('latin1','replace')
 lines.append(f'\n=== STRING 0x{va:X}: {s!r} ===')
 refs=pu.scan_imm32_refs(va)
 lines.append('raw dword refs count='+str(len(refs)))
 for loc,sec in refs:
  own=owner(loc)
  prefix=pu.read(max(0,loc-8),24) or b''
  lines.append(f'  ref@0x{loc:X} section={sec} owner={own and (hex(own[0]),hex(own[1]))} bytes[-8:+16]={prefix.hex(" ")}')
# decode target functions and look for push imm32 string refs or any immediate in STRS
TARGETS=[0x49F740,0x49F8B0,0x773450]
lines.append('\n=== TARGET FUNCTION DISASM ===')
for va in TARGETS:
 size=None
 for a,b in ints:
  if a==va: size=b-a;break
 if size is None: size=256
 b=pu.read(va,size)
 lines.append(f'\n--- 0x{va:X} size={size} bytes={b.hex(" ")} ---')
 for ins in pu.disasm(va,size):
  imm=[]
  for op in ins.operands:
   if op.type==pu.X86_OP_IMM: imm.append(hex(op.imm & 0xffffffff))
   elif op.type==pu.X86_OP_MEM and op.mem.disp: imm.append('mem:'+hex(op.mem.disp & 0xffffffff))
  tag=''
  for x in imm:
   try:
    n=int(x.split(':')[-1],16)
    if n in STRS: tag=' <<<STRINGREF'
   except: pass
  iat=pu.iat_name(ins.operands[0].imm & 0xffffffff) if ins.operands and ins.operands[0].type==pu.X86_OP_IMM and ins.mnemonic in ('call','jmp') else ''
  lines.append(f'  0x{ins.address:X}: {ins.mnemonic:<7} {ins.op_str}'+('  ; IAT '+iat if iat else '')+tag)
# broad region refs 0x81f400..0x81f600 grouped by call site owner
lines.append('\n=== ALL .DATA REFS INTO 0x81F400-0x81F600 BY OWNER ===')
owners={}
for secname,vbase,vsize,praw,rawsize,ch in pu.sections():
 data=pu.read(vbase, rawsize)
 if data is None: continue
 for i in range(len(data)-3):
  val=struct.unpack_from('<I',data,i)[0]
  if 0x81F400<=val<0x81F600:
   loc=vbase+i; own=owner(loc)
   key=(own[0] if own else None,secname)
   owners.setdefault(key,[]).append((loc,val))
for (o,sec),lst in sorted(owners.items(),key=lambda kv:(kv[0][0] is None,kv[0][0] or 0)):
 lines.append(f'owner={o and hex(o)} section={sec} count={len(lst)} vals='+','.join(hex(v) for _,v in lst[:20]))
 txt='\n'.join(lines)+'\n'
 open(CARD+r'\EVIDENCE\xref_copyprotect.txt','w',encoding='utf-8').write(txt)
 print(txt)
