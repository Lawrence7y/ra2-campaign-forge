#!/usr/bin/env python3
"""S10-K4 task-3 exhaustive candidate census and fail-closed explanations."""
from pathlib import Path
import csv,json,struct,re,hashlib
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
ROOT=Path(r'D:\Project\ra2-campaign-forge'); CARD=ROOT/'lead/next_re_20261117_r14/S10_K4'
WORK=CARD/'work'; EVID=CARD/'EVIDENCE'
EXE=ROOT/'ra2youli/gamemd.exe'; COV=ROOT/'lead/next_re_20261117_r14/COVERAGE/coverage.tsv'
ATL=ROOT/'lead/next_re_20261112_r10/W130_atlas/function_atlas.tsv'
data=EXE.read_bytes(); pe=pefile.PE(str(EXE),fast_load=True); IB=pe.OPTIONAL_HEADER.ImageBase
secs=[]
for s in pe.sections: secs.append((IB+s.VirtualAddress,IB+s.VirtualAddress+max(s.Misc_VirtualSize,s.SizeOfRawData),s.PointerToRawData,s.SizeOfRawData))
def rd(va,n):
 for a,b,r,z in secs:
  if a<=va<b and va-a<z: return data[r+va-a:r+va-a+n]
 return None
md=Cs(CS_ARCH_X86,CS_MODE_32); md.skipdata=True
def dis(a,n,c=40):
 b=rd(a,n); return list(md.disasm(b,a,count=c)) if b else []
def shape(va):
 b=rd(va,6)
 if b and len(b)==6 and b[0]==0xB8 and b[5]==0xC3: return ('B8_IMM32_C3',struct.unpack_from('<I',b,1)[0],b.hex())
 return ('OTHER',None,(b or b'').hex())
with COV.open('r',encoding='utf-8',newline='') as f: cov=list(csv.DictReader(f,delimiter='\t'))
atl={r['entry'].strip().lower() for r in csv.DictReader(ATL.open('r',encoding='utf-8',newline=''),delimiter='\t')}
s10=[r for r in cov if r['subsystem'].strip().upper()=='S10']
inter=[r for r in s10 if r['entry'].strip().lower() in atl]
non=[r for r in s10 if r['grade'].strip()!='[已证]']
non_in=[r for r in non if r['entry'].strip().lower() in atl]
b8=[r for r in inter if shape(int(r['entry'].strip(),16))[0]=='B8_IMM32_C3']
rj=json.loads((WORK/'all_rtti.json').read_text(encoding='utf-8'))
anchors=set()
for v in rj['vtables']:
    for s in v['slots']:
        if s: anchors.add(s.strip().lower())
non_anchor=sum(1 for r in non_in if r['entry'].strip().lower() in anchors)
ph=[r['entry'].strip().upper() for r in non_in if (not r['name'].strip()) or r['name'].strip().startswith('sub_') or '::sub_' in r['name'].strip() or re.search(r'::(?:v?slot)\d+$',r['name'].strip())]
string_entries=[]
for line in (EVID/'scan_nonproved_strings.txt').read_text(encoding='utf-8').splitlines():
    if line.startswith('ENTRY '): string_entries.append(line.split()[1])
cat={
 '004D27C0':'FoggedObjectClass slot12 already [已证] (slot12 imm=0x78 AbstractType FoggedObject precedent); unchanged',
 '005B2E10':'baseline already [已证] (S10-K1); not in this delta',
 '005B2E20':'one of 19 corrected rows (this card)',
 '005B2E30':'one of 19 corrected rows (this card)',
 '005B2E40':'one of 19 corrected rows (this card)',
 '005B2E50':'one of 19 corrected rows (this card)',
 '005B2E70':'one of 19 corrected rows (this card)',
 '005B2E80':'one of 19 corrected rows (this card)',
 '005B2E90':'one of 19 corrected rows (this card)',
 '005B2ED0':'one of 19 corrected rows (this card)',
 '005B2EE0':'one of 19 corrected rows (this card)',
 '005B2EF0':'one of 19 corrected rows (this card)',
 '005B2F10':'one of 19 corrected rows (this card)',
 '005B2F20':'one of 19 corrected rows (this card)',
 '005B2F30':'one of 19 corrected rows (this card)',
 '005B2F40':'one of 19 corrected rows (this card)',
 '005B2F50':'one of 19 corrected rows (this card)',
 '005B2F80':'one of 19 corrected rows (this card)',
 '005B2F90':'one of 19 corrected rows (this card)',
 '005B2FA0':'one of 19 corrected rows (this card)',
 '005B2FB0':'one of 19 corrected rows (this card)',
 '006B1370':'GetSize double-point closure (S10-K3, unchanged)',
 '006B1380':'WhatAmI enum/RTTI closure (S10-K3, unchanged)',
 '006B8120':'GetSize double-point closure (S10-K3, unchanged)',
 '006B8130':'WhatAmI enum/RTTI closure (S10-K3, unchanged)',
 '0070DD90':'negative control: imm=1 enum Unit vs RTTI AircraftClass; no WhatAmI/GetSize closure',
}
b8_rows=[r['entry'].strip().upper() for r in b8]
missing=[e for e in b8_rows if e not in cat]
if missing: raise SystemExit('unclassified B8 '+repr(missing))
lines=['S10-K4 TASK 3: EXHAUSTIVE PROVED CANDIDATE CENSUS',
 'SHA256='+hashlib.sha256(data).hexdigest().upper(),
 'BASELINE: S10_COVERAGE=%d ATLAS_INTER=%d PROVED=%d NONPROVED_ALL=%d NONPROVED_ATLAS=%d NONPROVED_RTTI_ANCHORED=%d'%(len(s10),len(inter),sum(r['grade'].strip()=='[已证]' for r in inter),len(non),len(non_in),non_anchor),
 'B8_IMM32_C3_ATLAS_ROWS=%d UNCLASSIFIED=%d'%(len(b8),len(missing)),
 'NO_REMAINING_B8_ROWS: every atlas B8 row has an explicit disposition below',
]
for e in sorted(b8_rows): lines.append('B8 %s %s'%(e,cat[e]))
lines += [
 'STRING_XREF_SCAN: non-proved S10 functions whose first 2 KiB contain readable string pointers = %d'%len(string_entries),
 'STRING_XREF_ENTRIES='+','.join(string_entries),
 'STRING_XREF_DISPOSITION: all are shared tail references (EVA_UnitLost/UnitSold, EVA_StructureGarrisoned, BTN-PLUS/MINS, rule keys, source-file assert strings, Tip:* tooltip strings). They identify a nearby common callee, not a unique virtual-method name for the entry; no mission-id/name-table closure and no independent second naming channel. Not upgraded.',
 'PLACEHOLDER_NONPROVED_ENTRIES=%d %s'%(len(ph),','.join(ph)),
 'PLACEHOLDER_DISPOSITION: sub_/slotN/vslotN names are excluded from named(S) and have no RTTI/vtable anchor in independently parsed RTTI; no semantic upgrade.',
]
notes={
 '005B3970':'Behavior visible: call 0x5F6250 then repeated call 0x4A1D50 on fields +AC,+B0,+B4,+BC,+timer remaining,+C0, ret 4; direct caller 0065AB10 also writes stream helpers. Name "Save"/"Serialize" is not bound by any in-binary mission-name table, string, or independent caller-side symbol; vtable-slot inference alone is forbidden. Not upgraded.',
 '005B3A60':'Behavior visible: writes 4 vptrs (007EDCC0/7EDCA4/7EDC9C/7EDC94), call 0x5F3B80, conditional call 0x7C8B3D, ret 4 = destructor-shaped. Name "destructor" not bound by an allowed independent naming channel; not upgraded.',
 '005B3A10':'Behavior visible only: mov edx,[ecx+0xB0]; xor eax,eax; cmp edx,-1; setne al; ret. No unique behavior-level semantics or independent name channel for a predicate; not upgraded.',
 '005F5E80':'Inherited ObjectClass field-load/clear routine; no Mission_* dispatch/name evidence; not upgraded.',
 '0070DD90':'B8 imm=1 but RTTI is AircraftClass; imm=1 would mean Unit in the AbstractType enum and this is neither off0 slot11 nor GetSize-closed slot12. Semantic mismatch; negative control, not upgraded.',
}
for e,note in notes.items():
    lines.append('FAIL_CLOSED %s %s'%(e,note))
    for i in dis(int(e,16),64,24): lines.append('  %08X %s %s'%(i.address,i.bytes.hex(),i.op_str))
lines += [
 'THIS CARD PROVED ADVANCE: 19 mission stubs are still [静态推断] on disk; corrected delta promotes them by behavior-level Timer semantics (return value -> UpdateTimer.TimeLeft), not by B8 shape alone.',
 'EXCLUSION: 005B3060 (UpdateTimer body) is already [已证] on disk; its semantics were corrected in EVIDENCE/probe_timer_dispatch.txt but it is intentionally not a new delta row (no grade/name increment, avoids re-merging an already-proved entry).',
 'CHANNELS: raw PE+capstone entry-to-ret, RTTI COL+0xC->TD+8, ctor vptr write, mission dispatch table 0x5B34E8, in-binary mission name table 0x816CAC; no atlas entry+size used as sole channel; no Ghidra.',
]
(EVID/'task3_exhaustive.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('\n'.join(lines[:12]))
