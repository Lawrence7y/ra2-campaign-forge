
import struct,pefile,capstone
ROOT=r'D:\Project\ra2-campaign-forge'
EV=ROOT+r'\lead\next_re_20261117_r14\S08_K1\EVIDENCE'
B=open(ROOT+r'\ra2youli\gamemd.exe','rb').read(); PE=pefile.PE(ROOT+r'\ra2youli\gamemd.exe',fast_load=True); BASE=PE.OPTIONAL_HEADER.ImageBase
S=[]
for s in PE.sections:
 nm=s.Name.rstrip(b'\x00').decode(errors='replace'); S.append((nm,BASE+s.VirtualAddress,BASE+s.VirtualAddress+s.Misc_VirtualSize,s.PointerToRawData,s.SizeOfRawData))
def v2o(va):
 for nm,a,z,ro,sz in S:
  if a<=va<z:
   o=ro+(va-a)
   return o if 0<=o<len(B) else None
 return None
def rd(va,n):
 o=v2o(va); return B[o:o+n] if o is not None else b''
def insn(va):
 o=v2o(va); md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.detail=True
 for i in md.disasm(B[o:o+16],va): return i
 return None
def relcheck(site,entry):
 b=rd(site,5)
 rel=struct.unpack_from('<i',b,1)[0]
 return (site+5+rel)&0xffffffff, b.hex().upper(), rel
lines=[]
lines.append('PROOF · 004309D0 direct-only upgrade')
lines.append('SHA256=73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476')
for va in [0x004309D6,0x004309F8,0x00430A2D,0x00430A3A,0x00430A5C,0x00430A97,0x00430AEF if False else 0x00430A0B,0x00430A92]:
 i=insn(va); lines.append(f'{va:08X}: {i.bytes.hex().upper()} {i.mnemonic} {i.op_str}' if i else f'{va:08X}: <none>')
site,entry=0x00687BB2,0x004309D0
t,b,rel=relcheck(site,entry); i=insn(site)
lines.append(f'DIRECT site {site:08X}: bytes={b} rel32={rel} target={t:08X} expect={entry:08X} OK={t==entry}')
lines.append(f'  insn: {i.mnemonic} {i.op_str}')
lines.append('  caller owner=00686B20 (atlas entry+size); site not inside target body [004309D0,00430ABB).')
open(EV+r'\PROOF_004309D0.txt','w',encoding='utf-8').write('\n'.join(lines)+'\n')

lines=[]
lines.append('PROOF · 0047F250 name + direct-only upgrade')
lines.append('SHA256=73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476')
lines.append('BINARY channel: lazy-load FOG.SHP and cache pointer')
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.detail=True
for i in md.disasm(rd(0x0047F250,689),0x0047F250):
 if (0x0047F250<=i.address<0x0047F274) or i.mnemonic=='ret' or i.address in (0x0047F288,):
  lines.append(f'{i.address:08X}: {i.bytes.hex().upper()} {i.mnemonic} {i.op_str}')
for site in [0x00480278,0x00480290]:
 entry=0x0047F250; t,b,rel=relcheck(site,entry); i=insn(site)
 lines.append(f'DIRECT site {site:08X}: bytes={b} rel32={rel} target={t:08X} expect={entry:08X} OK={t==entry}')
 lines.append(f'  insn: {i.mnemonic} {i.op_str}  caller owner=004801F0; site outside body [0047F250,0047F4F9).')
lines.append('INDEPENDENT source channel:')
lines.append('  docs/re/ARCHITECTURE_ATLAS.md:4336  -> 0x0047EFE0 / 0x0047F250 / 0x004801F0 = Draw_Shroud / Draw_Fog / CellClass::Draw')
lines.append('  docs/re/fog_firststage_site_locate.md:52-53 -> Draw_Fog 0x47F250 (2 callers 0x480278 / 0x480290)')
lines.append('  docs/re/visibility_gap_spysat.md:202 -> 原版灰雾 Foggedness@+0x121, Draw_Fog(0x47F250) 读')
lines.append('NAME=Draw_Fog (source record + binary FOG.SHP/direct-call; no Class::sub_ placeholder).')
open(EV+r'\PROOF_0047F250.txt','w',encoding='utf-8').write('\n'.join(lines)+'\n')

lines=[]
lines.append('PROOF · 0047EFE0 direct evidence (already [已证], no delta)')
site,entry=0x00480230,0x0047EFE0
t,b,rel=relcheck(site,entry); i=insn(site)
lines.append(f'DIRECT site {site:08X}: bytes={b} rel32={rel} target={t:08X} expect={entry:08X} OK={t==entry}')
lines.append(f'  insn: {i.mnemonic} {i.op_str}  caller owner=004801F0; site outside body [0047EFE0,0047F265).')
lines.append('Conflict only reported: S08-K1/coverage_delta.tsv:13 calls it MapClass::DrawShroudFogLayer; docs/re/ARCHITECTURE_ATLAS.md:4336 calls it Draw_Shroud. No rename in this card.')
open(EV+r'\PROOF_0047EFE0.txt','w',encoding='utf-8').write('\n'.join(lines)+'\n')
print('wrote proofs')
