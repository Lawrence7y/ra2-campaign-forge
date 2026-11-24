#!/usr/bin/env python3
"""WaveClass RTTI chain (TD->COL->vtable->GetSize) + name uniqueness check."""
import os,re,struct,csv
import pefile
ROOT=r'D:\Project\ra2-campaign-forge'; EXE=os.path.join(ROOT,r'ra2youli\gamemd.exe')
pe=pefile.PE(EXE,fast_load=False); IB=pe.OPTIONAL_HEADER.ImageBase; data=open(EXE,'rb').read()
def u32(va): return struct.unpack_from('<I',data,va-IB)[0]
def cstr(va):
    b=data[va-IB:va-IB+160]; z=b.find(b'\0'); return b[:z if z>=0 else 160].decode('ascii','replace')
m=re.search(rb'AVWaveClass@@',data)
if not m:
    print('WaveClass TD name not found'); raise SystemExit
td=m.start()+IB-8
print(f'WaveClass TD=0x{td:X}  name@TD+8=0x{IB+m.start():X} = "{cstr(IB+m.start())}"')
col_hits=[]
for s in pe.sections:
    if s.Name.rstrip(b'\0')==b'.rdata':
        base=IB+s.VirtualAddress; sz=s.Misc_VirtualSize
        for off in range(0,sz-4,4):
            va=base+off
            if u32(va)==td: col_hits.append(va-0xC)
print('COL candidates (COL+0xC==TD):',[hex(x) for x in col_hits])
for col in col_hits:
    vt_hits=[]
    for s in pe.sections:
        if s.Name.rstrip(b'\0')==b'.rdata':
            base=IB+s.VirtualAddress; sz=s.Misc_VirtualSize
            for off in range(0,sz-4,4):
                va=base+off
                if u32(va)==col: vt_hits.append(va+4)
    print(f'  COL 0x{col:X} -> vtable starts {[hex(x) for x in vt_hits]}')
    for vt in vt_hits[:4]:
        slots=[u32(vt+4*i) for i in range(20)]
        print(f'    vtable 0x{vt:X} slots20={[hex(x) for x in slots]}')
        for i,fn in enumerate(slots):
            if 0x401000<=fn<0x7E038D:
                b=data[fn-IB:fn-IB+6]
                if len(b)==6 and b[:1]==b'\xB8' and b[5:6]==b'\xC3':
                    print(f'      GETSIZE? slot{i} fn=0x{fn:X} imm=0x{struct.unpack_from("<I",b,1)[0]:X}')
print()
print('=== name uniqueness check ===')
newnames=['EVA_NewRallyPointEstablished_Trigger','EVA_BuildingOnLine_Trigger','EVA_Infiltration_Trigger',
 'EVA_StructureAbandoned_Trigger','EVA_CannotDeployHere_UnitReady_Trigger','EVA_RobotTanksBackOnline_Trigger',
 'EVA_StructureGarrisoned_Trigger','EVA_BattleControlTerminated_Trigger','EVA_NewConstructionOptions_Trigger',
 'EVA_ConstructionComplete_Trigger','EVA_SuperWeaponReady_Trigger','EVA_CannotDeployHere_Trigger',
 'Bink_Goto','Bink_Pause','Bink_Wait','Bink_CopyToBuffer','Bink_DoFrame','LoadTauntVOX_Files']
with open(os.path.join(ROOT,r'lead\next_re_20261117_r14\COVERAGE\coverage.tsv'),encoding='utf-8') as f:
    names=set(row['name'] for row in csv.DictReader(f,delimiter='\t'))
for n in newnames:
    print(f'  {n}: exists={n in names}')
