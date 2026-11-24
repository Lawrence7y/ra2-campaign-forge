#!/usr/bin/env python3
"""Dump non-upgraded S10 semantic candidates and all 28 mission stubs status."""
from pathlib import Path
import csv,pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
ROOT=Path(r'D:\Project\ra2-campaign-forge'); CARD=ROOT/'lead/next_re_20261117_r14/S10_K3'
EXE=ROOT/'ra2youli/gamemd.exe'; COV=ROOT/'lead/next_re_20261117_r14/COVERAGE/coverage.tsv'
ATL=ROOT/'lead/next_re_20261112_r10/W130_atlas/function_atlas.tsv'
data=EXE.read_bytes(); pe=pefile.PE(str(EXE),fast_load=True); IB=pe.OPTIONAL_HEADER.ImageBase
secs=[]
for s in pe.sections: secs.append((IB+s.VirtualAddress,IB+s.VirtualAddress+max(s.Misc_VirtualSize,s.SizeOfRawData),s.PointerToRawData,s.SizeOfRawData))
def off(va):
 for a,b,r,z in secs:
  if a<=va<b and va-a<z: return r+va-a
def read(va,n):
 o=off(va); return None if o is None or o+n>len(data) else data[o:o+n]
md=Cs(CS_ARCH_X86,CS_MODE_32); md.skipdata=True
def dis(va,n=60):
 b=read(va,600); return list(md.disasm(b,va,count=n)) if b else []
cov={r['entry'].strip().upper():r for r in csv.DictReader(COV.open(encoding='utf-8',newline=''),delimiter='\t')}
atl={r['entry'].strip().upper() for r in csv.DictReader(ATL.open(encoding='utf-8',newline=''),delimiter='\t')}
delta={l.split('\t')[0].strip().upper() for l in (CARD/'coverage_delta.tsv').read_text(encoding='utf-8').splitlines() if l}
lines=['S10-K3 NON-UPGRADED / FAIL-CLOSED CANDIDATE DUMP','ALL 28 BASE MISSION STUB STATUS']
for i in range(28):
 va=0x5B2E10+0x10*i; e=format(va,'08X'); r=cov.get(e)
 if e in delta: status='UPGRADED_BY_CARD'
 elif r and r['subsystem'].strip().upper()=='S10' and r['grade'].strip()=='[已证]': status='ALREADY_PROVED_BASELINE'
 elif r: status='IN_COVERAGE_BUT_NOT_S10_OR_NOT_UPGRADED: '+r['subsystem']+'/'+r['grade']
 else: status='NOT_IN_COVERAGE'
 lines.append('%s\t%s\t%s'%(e,status,read(va,16).hex() if read(va,16) else 'UNMAPPED'))
lines += ['','KEY NON-UPGRADED CANDIDATES (NOT PROMOTED; listed names/semantics remain original)']
for va,why in [(0x5B3970,'MissionClass slot13: serializes fields; method-name Save not bound by an allowed proof type without slot inference'),
               (0x5B3A60,'MissionClass v8: writes 4 vtables + base dtor + conditional operator delete; destructor name not bound by an allowed proof type'),
               (0x5F5E80,'ObjectClass v5 inherited row: field loading pattern; not Mission_* behavior-level proof'),
               (0x70DD90,'AircraftClass slot250: B8 01 00 00 00 C3; imm=1 is enum Unit but RTTI is Aircraft, so WhatAmI semantic mismatch; not slot11/12 GetSize')]:
 lines.append('\nENTRY %08X REASON %s'%(va,why))
 for it in dis(va,80):
  lines.append('  %08X  %-22s %-8s %s'%(it.address,it.bytes.hex(),it.mnemonic,it.op_str))
  if it.mnemonic=='ret': break
(CARD/'EVIDENCE/nonupgraded_candidates.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('wrote',len(lines),'lines')
