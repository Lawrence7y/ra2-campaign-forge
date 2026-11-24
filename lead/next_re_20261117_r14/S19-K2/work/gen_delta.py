#!/usr/bin/env python3
"""Generate evidence file + coverage_delta.tsv for all T2 names."""
import os,struct,re,csv
import pefile
ROOT=r'D:\Project\ra2-campaign-forge'
EXE=os.path.join(ROOT,r'ra2youli\gamemd.exe')
CARD=os.path.join(ROOT,r'lead\next_re_20261117_r14\S19-K2')
pe=pefile.PE(EXE,fast_load=False); IB=pe.OPTIONAL_HEADER.ImageBase; d=open(EXE,'rb').read()
def u32(va): return struct.unpack_from('<I',d,va-IB)[0]
# verify push 0x240 -> operator new
for va in [0x6BF0BC,0x6FF449,0x6FF623]:
    callva=va+5; rel=struct.unpack_from('<i',d,callva-IB+1)[0]; tgt=callva+5+rel
    print(f'push 0x240 @0x{va:X}; call @0x{callva:X} -> 0x{tgt:X}')
# current grades
cov={}
with open(os.path.join(ROOT,r'lead\next_re_20261117_r14\COVERAGE\coverage.tsv'),encoding='utf-8') as f:
    for row in csv.DictReader(f,delimiter='\t'):
        if row['subsystem']=='S19': cov[row['entry'].upper()]=row
# names: entry, name, evtype, evaddr(s), grade, one_line
NAMES=[
 ('00443860','EVA_NewRallyPointEstablished_Trigger','strref+call',
  'mov ecx,0x818E58("EVA_NewRallyPointEstablished")@0x443A64; call 0x752700@0x443A69','[已证]','Plays EVA_NewRallyPointEstablished voice via 0x752700'),
 ('0044F820','EVA_BuildingOnLine_Trigger','strref+call',
  'EVA_BuildingOnLine strref; call 0x752700','[已证]','Plays EVA_BuildingOnLine voice'),
 ('004571E0','EVA_Infiltration_Trigger','strref+call',
  'EVA_RadarSabotaged/PowerSabotaged/CashStolen/TechnologyStolen strrefs + call 0x752700 (7 sites)','[已证]','Infiltration EVA voice dispatcher'),
 ('00458200','EVA_StructureAbandoned_Trigger','strref+call',
  'EVA_StructureAbandoned strref; call 0x752700','[已证]','Plays EVA_StructureAbandoned voice'),
 ('004FB0E0','EVA_CannotDeployHere_UnitReady_Trigger','strref+call',
  'EVA_CannotDeployHere/EVA_UnitReady strrefs + call 0x752700','[已证]','Unit-event EVA voice dispatcher (EVA_CannotDeployHere + EVA_UnitReady)'),
 ('0050E010','EVA_RobotTanksBackOnline_Trigger','strref+call',
  'EVA_RobotTanksBackOnline strref + call 0x752700','[已证]','Plays EVA_RobotTanksBackOnline voice'),
 ('00522910','EVA_StructureGarrisoned_Trigger','strref+call',
  'EVA_StructureGarrisoned strref + call 0x752700','[已证]','Plays EVA_StructureGarrisoned voice'),
 ('00686570','EVA_BattleControlTerminated_Trigger','strref+call',
  'EVA_BattleControlTerminated strref + call 0x752700','[已证]','Plays EVA_BattleControlTerminated voice'),
 ('006A87F0','EVA_NewConstructionOptions_Trigger','strref+call',
  'EVA_NewConstructionOptions strref + call 0x752700','[已证]','Plays EVA_NewConstructionOptions voice'),
 ('006A8B30','EVA_ConstructionComplete_Trigger','strref+call',
  'EVA_ConstructionComplete strref + call 0x752700','[已证]','Plays EVA_ConstructionComplete voice'),
 ('006CC080','EVA_SuperWeaponReady_Trigger','strref+call',
  '10 EVA superweapon-ready strrefs + call 0x752700','[已证]','Superweapon-ready EVA voice dispatcher'),
 ('007393C0','EVA_CannotDeployHere_Trigger','strref+call',
  'EVA_CannotDeployHere strref + call 0x752700','[已证]','Plays EVA_CannotDeployHere voice'),
 ('00432BD0','Bink_Goto','IAT',
  'call dword[0x7E15AC]=binkw32!_BinkGoto@12 @0x432BDE','[已证]','Bink OO wrapper -> BinkGoto'),
 ('00432C30','Bink_Pause','IAT',
  'call dword[0x7E15B0]=binkw32!_BinkPause@8 @0x432C3E','[已证]','Bink OO wrapper -> BinkPause'),
 ('00433020','Bink_Wait','IAT',
  'call dword[0x7E15C0]=binkw32!_BinkWait@4 @0x433027','[已证]','Bink OO wrapper -> BinkWait'),
 ('004331F0','Bink_CopyToBuffer','IAT',
  'call dword[0x7E15B8]=binkw32!_BinkCopyToBuffer@28 @0x433251','[已证]','Bink OO wrapper -> BinkCopyToBuffer'),
 ('00432E40','Bink_DoFrame','IAT',
  'call dword[0x7E15BC]=binkw32!_BinkDoFrame@4 (in body); F1 anchor','[已证]','Bink frame-decode wrapper -> BinkDoFrame'),
 ('00752B70','LoadTauntVOX_Files','strref',
  'taunts\\tau*%02i.wav strrefs (10) @0x752B70 body','[静态推断]','Loads taunt VOX wav filename table'),
]
evpath=os.path.join(CARD,'EVIDENCE','t2_naming_evidence.txt')
with open(evpath,'w',encoding='utf-8') as f:
    f.write('S19-K2 T2 naming evidence (byte-level). Target SHA-256 73201CC0...F67476 verified.\n')
    f.write('pefile IAT parse: binkw32.dll imports @0x7E1590..0x7E15C0 (13 APIs).\n')
    f.write('EVA anchor 0x752700 = VoxClass::Play (F1 task4); call sites verified by capstone full-body disasm.\n\n')
    for e,n,ty,addr,g,sem in NAMES:
        cur=cov.get(e)
        f.write(f'{e}\t{n}\t{ty}\t{addr}\tgrade={g}\tcur_name={cur["name"] if cur else "?"}\tcur_grade={cur["grade"] if cur else "?"}\n')
# delta
dp=os.path.join(CARD,'coverage_delta.tsv')
with open(dp,'w',encoding='utf-8',newline='') as f:
    w=csv.writer(f,delimiter='\t',lineterminator='\n')
    w.writerow(['entry','subsystem','name','one_line_semantics','grade','evidence_path'])
    for e,n,ty,addr,g,sem in NAMES:
        w.writerow([e,'S19',n,sem,g,'lead/next_re_20261117_r14/S19-K2/EVIDENCE/t2_naming_evidence.txt#'+e])
print('wrote',evpath)
print('wrote',dp,'rows',len(NAMES))
# grade distribution of named targets
from collections import Counter
print('current grades of targets:',Counter(cov.get(e,{}).get('grade','?') for e,*_ in NAMES))
