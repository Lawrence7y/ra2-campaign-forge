import sys,os,re,struct
sys.path.insert(0,r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S17-F1\work')
import pe_util as pu
CARD=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
pe=pu._pe
imports={}
for ent in pe.DIRECTORY_ENTRY_IMPORT:
 dll=ent.dll.decode('latin1') if isinstance(ent.dll,bytes) else ent.dll
 for imp in ent.imports:
  if imp.address:
   nm=imp.name.decode('latin1') if imp.name else ('ordinal:'+str(imp.ordinal))
   imports[imp.address]=f'{dll}!{nm}'
def iat(va): return imports.get(va,'?')
ATL=r'D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv'
ints=[]
for ln in open(ATL,'r',encoding='utf-8-sig').read().splitlines()[1:]:
 p=ln.split('\t')
 if len(p)>=2: ints.append((int(p[0],16),int(p[0],16)+int(p[1])))
ints.sort()
def owner(va):
 for a,b in ints:
  if a<=va<b:return (a,b)
 return None
lines=[]
lines.append('S17-K5 copy-protection detail')
lines.append('=== strings 0x81F400-0x81F600 ===')
data=pu.read(0x81F400,0x200)
for m in re.finditer(rb'[ -~]{3,}',data):
 va=0x81F400+m.start(); lines.append(f'  0x{va:X}: {m.group().decode("latin1")!r}')
lines.append('\n=== target IAT calls ===')
for va,size in [(0x49F740,88),(0x49F8B0,101)]:
 lines.append(f'-- 0x{va:X} --')
 for ins in pu.disasm(va,size):
  if ins.mnemonic in ('call','jmp') and ins.operands and ins.operands[0].type==pu.X86_OP_MEM:
   target=ins.operands[0].mem.disp & 0xffffffff
   lines.append(f'  0x{ins.address:X}: {ins.mnemonic} {ins.op_str} -> {iat(target)}')
  if ins.mnemonic in ('call','jmp') and ins.operands and ins.operands[0].type==pu.X86_OP_IMM:
   target=ins.operands[0].imm & 0xffffffff
   lines.append(f'  0x{ins.address:X}: {ins.mnemonic} {ins.op_str} (direct)')
lines.append('\n=== direct call/xrefs to target entries ===')
for target in [0x49F740,0x49F8B0,0x49F798,0x49F820,0x49F840,0x49F8A0,0x49F915]:
 refs=pu.scan_rel32_calls(target)
 imm=pu.scan_imm32_refs(target)
 lines.append(f'0x{target:X}: E8/E9 refs={[hex(a) for a,_ in refs]} dword refs={[hex(a) for a,_ in imm]}')
 for a,_ in refs:
  o=owner(a); lines.append(f'   callsite 0x{a:X} owner={o and (hex(o[0]),hex(o[1]))}')
lines.append('\n=== atlas functions in 0x49F500-0x49F980 ===')
for a,b in ints:
 if 0x49F500<=a<0x49F980:
  lines.append(f'-- 0x{a:X} size={b-a} --')
  for ins in pu.disasm(a,b-a):
   extra=''
   if ins.operands:
    op=ins.operands[0]
    if op.type==pu.X86_OP_IMM and (0x81f400<=op.imm<0x81f600): extra=' ; STR '+repr((pu.read(op.imm & 0xffffffff,80) or b'').split(b'\0')[0].decode('latin1','replace'))
    if ins.mnemonic in ('call','jmp') and op.type==pu.X86_OP_MEM and (op.mem.disp & 0xffffffff) in imports: extra=' ; IAT '+iat(op.mem.disp & 0xffffffff)
    if ins.mnemonic in ('call','jmp') and op.type==pu.X86_OP_IMM and (op.imm & 0xffffffff) in [0x49F5C0,0x49F620,0x49F740,0x49F798,0x49F820,0x49F840,0x49F8A0,0x49F8B0,0x49F915]: extra=' ; LOCALCALL'
   lines.append(f'0x{ins.address:X}: {ins.mnemonic:<7} {ins.op_str}{extra}')
text='\n'.join(lines)+'\n'
open(CARD+r'\EVIDENCE\copyprotect_detail.txt','w',encoding='utf-8').write(text)
print(text[:18000])
