"""
S11-K2 T5: build TARGETS.tsv (all S11 rows from coverage.tsv grouped by grade)
and coverage_delta.tsv (upgrades backed by byte evidence).
"""
import csv, collections

COV=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv'
OUTDIR=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S11-K2'
rows=[]
with open(COV,encoding='utf-8') as f:
    for r in csv.DictReader(f,delimiter='\t'):
        rows.append(r)
s11=[r for r in rows if r['subsystem']=='S11']
print('S11 rows =',len(s11))
grp=collections.Counter(r['grade'] for r in s11)
print('grade groups =',dict(grp))

# TARGETS.tsv: entry | 现name | 现grade | 缺什么 | 取证计划
with open(OUTDIR+r'\TARGETS.tsv','w',encoding='utf-8',newline='') as f:
    w=csv.writer(f,delimiter='\t',lineterminator='\n')
    w.writerow(['entry','现name','现grade','缺什么','取证计划'])
    for r in sorted(s11,key=lambda z:z['entry']):
        g=r['grade']
        if g=='[已证]':
            miss='已证（本卡核对是否可加固）'; plan='RTTI/GetSize/vtable 再核'
        elif g=='[静态推断]':
            miss='缺字节级硬证（入口/语义仅静态推断）'; plan='查 off4/off0 vtable 槽位+B8/C3 或构造器分配点'
        else:
            miss='缺入口字节证据+语义'; plan='查是否 vtable 槽直指/构造器调用点/字段双支撑'
        w.writerow([r['entry'],r['name'],g,miss,plan])
print('wrote TARGETS.tsv (%d rows)'%len(s11))

# coverage_delta.tsv: entry | subsystem | name | one_line_semantics | grade | evidence_path
# Only upgrades with byte-level evidence. evidence_path points to EVIDENCE files (relative to card).
DELTA=[]
# (entry, name, semantics, grade, evidence)
# 11 GetSize (static->proved)
gets={
'004B4CF0':('DriveLocomotionClass::GetSize','GetSize: off0 slot9, B8 70 00 00 00 C3 -> 0x70; factory new push 0x70 (6A70) closes','[已证]'),
'004B66E0':('DropPodLocomotionClass::GetSize','off0 slot9 B8 30...C3=0x30; factory push 0x30 (6A30)','[已证]'),
'004D0390':('FlyLocomotionClass::GetSize','off0 slot9 B8 60...C3=0x60; factory push 0x60 (6A60)','[已证]'),
'005172B0':('HoverLocomotionClass::GetSize','off0 slot9 B8 78...C3=0x78; factory push 0x78 (6A78)','[已证]'),
'0054DF90':('JumpjetLocomotionClass::GetSize','off0 slot9 B8 98...C3=0x98; factory push 0x98 (68 imm32)','[已证]'),
'005B1B40':('MechLocomotionClass::GetSize','off0 slot9 B8 34...C3=0x34; factory push 0x34 (6A34)','[已证]'),
'006635B0':('RocketLocomotionClass::GetSize','off0 slot9 B8 60...C3=0x60; factory push 0x60 (6A60)','[已证]'),
'006A42A0':('ShipLocomotionClass::GetSize','off0 slot9 B8 70...C3=0x70; factory push 0x70 (6A70)','[已证]'),
'0071A120':('TeleportLocomotionClass::GetSize','off0 slot9 B8 4C...C3=0x4C; factory push 0x4C (6A4C)','[已证]'),
'0072A200':('TunnelLocomotionClass::GetSize','off0 slot9 B8 3C...C3=0x3C; factory push 0x3C (6A3C)','[已证]'),
'0075CBD0':('WalkLocomotionClass::GetSize','off0 slot9 B8 3C...C3=0x3C; factory push 0x3C (6A3C)','[已证]'),
}
for e,(nm,sem,g) in gets.items():
    DELTA.append((e,'S11',nm,sem,g,'EVIDENCE/t2_getsize_closure.txt'))

# ctors [未证]->[已证]: install canonical vtable + called from factory after new
ctors={
'004AF540':('DriveLocomotionClass::DriveLocomotionClass','ctor: installs off0=7E7F7C/off4=7E7EB0 (004AF5C2/5C8), called by factory 6C4010 after new(0x70)'),
'00513C20':('HoverLocomotionClass::HoverLocomotionClass','ctor: installs off0=7EADC8/off4=7EACFC, called by factory 6C4310 after new(0x78)'),
'00728A00':('TunnelLocomotionClass::TunnelLocomotionClass','ctor: installs off0=7F5AF0/off4=7F5A24, called by factory 6C4610 after new(0x3C)'),
'0075AA90':('WalkLocomotionClass::WalkLocomotionClass','ctor: installs off0=7F6AC4/off4=7F69F8, called by factory 6C4790 after new(0x3C)'),
'004B5AB0':('DropPodLocomotionClass::DropPodLocomotionClass','ctor: installs off0=7E8344/off4=7E8278, called by factory 6C4910 after new(0x30)'),
'00718000':('TeleportLocomotionClass::TeleportLocomotionClass','ctor: installs off0=7F50CC/off4=7F5000, called by factory 6C4C10 after new(0x4C)'),
'005AFEF0':('MechLocomotionClass::MechLocomotionClass','ctor: installs off0=7EDC38/off4=7EDB6C, called by factory 6C4D90 after new(0x34)'),
'0069EC50':('ShipLocomotionClass::ShipLocomotionClass','ctor: installs off0=7F2E58/off4=7F2D8C, called by factory 6C4F10 after new(0x70)'),
}
for e,(nm,sem) in ctors.items():
    DELTA.append((e,'S11',nm,sem,'[已证]','EVIDENCE/t2_ctor_map.log'))

# Jumpjet CreateInstance at CORRECT addr 006C4190 [未证]->[已证]
DELTA.append(('006C4190','S11','T_TClassFactory_VJumpjetLocomotionClass__::slot3',
              'Jumpjet factory CreateInstance (ctor 6C40C0+0xD0): new(0x98), ctor 54AC40 installs 7ECE34/7ECD68','[已证]',
              'EVIDENCE/t2_ctor_map.log'))

with open(OUTDIR+r'\coverage_delta.tsv','w',encoding='utf-8',newline='') as f:
    w=csv.writer(f,delimiter='\t',lineterminator='\n')
    w.writerow(['entry','subsystem','name','one_line_semantics','grade','evidence_path'])
    for row in DELTA: w.writerow(row)
print('wrote coverage_delta.tsv (%d upgrades)'%len(DELTA))
for row in DELTA: print(row[0],row[2])
