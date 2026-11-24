"""Build coverage_delta.tsv for S05-K1 (does NOT touch coverage.tsv)."""
import os, csv
ROOT=os.path.join('D:',os.sep,'Project','ra2-campaign-forge')
OUT=os.path.join(ROOT,'lead','next_re_20261117_r14','S05-K1','coverage_delta.tsv')
EV='EVIDENCE/class_chain_core.json'

# entry, subsystem, name, one_line_semantics, grade, evidence_path
rows=[]
def add(e,nm,sem,grade,path):
    rows.append((e.upper(),'S05',nm,sem,grade,path))

# Constructors proved via vtable-write + push<size>/operator-new bidirectional
ctors=[
 ('0043B740','BuildingClass::BuildingClass','ctor: writes vptr 0x7E3EBC @43B9FA; v[12]=0x720; alloc 44FAF8 push0x720->7C8E17->ecx=eax->call','[已证]',EV),
 ('007353C0','UnitClass::UnitClass','ctor: writes vptr 0x7F5C70 @73543A; v[12]=0x8E8; alloc 449E16 push0x8E8->7C8E17->ecx=eax->call','[已证]',EV),
 ('00517A50','InfantryClass::InfantryClass','ctor: writes vptr 0x7EB058 @517ACC; v[12]=0x6F0; alloc 4430C2 push0x6F0->7C8E17->ecx=eax->call','[已证]',EV),
 ('00413D20','AircraftClass::AircraftClass','ctor: writes vptr 0x7E22A4 @413D87; v[12]=0x6D8; alloc 41B1B4 push0x6D8->7C8E17->ecx=eax->call','[已证]',EV),
 ('006F2B40','TechnoClass::TechnoClass','ctor: writes vptr 0x7F4960 @6F3130; 112 this-writes all in [0xF0,0x2F4]','[已证]',EV),
 ('004D31E0','FootClass::FootClass','ctor: writes vptr 0x7E8C94 @4D345D; name dispels noinit_t trap (DISAGREE D5)','[已证]',EV),
 ('005F3900','ObjectClass::ObjectClass','ctor: writes vptr 0x7EF060 @5F39BA; also +0x94=ecx @5F3987 / +0x80=bl / +0x81=al / +0x74=bl','[已证]',EV),
 ('00410170','AbstractClass::AbstractClass','ctor: writes vptr 0x7E1F50 @410198, +0x10=0xFFFFFFFF @410191, +0x20=cl @410188','[已证]',EV),
]
for r in ctors: add(*r)

# Ctor variants (same class vptr write, byte-evidenced) - conservative grade
variants=[
 ('0043B680','BuildingClass::BuildingClass','ctor variant: writes vptr 0x7E3EBC @43B71F','[已证]'),
 ('0043BCF0','BuildingClass::~BuildingClass','scalar dtor: writes vptr 0x7E3EBC @43BCFD','[已证]'),
 ('00735780','UnitClass::UnitClass','ctor variant: writes vptr 0x7F5C70 @735794','[已证]'),
 ('00744470','UnitClass::UnitClass','ctor variant: writes vptr 0x7F5C70 @744521','[已证]'),
 ('00517D90','InfantryClass::InfantryClass','ctor variant: writes vptr 0x7EB058 @517D9D','[已证]'),
 ('00521960','InfantryClass::InfantryClass','ctor variant: writes vptr 0x7EB058 @521A11','[已证]'),
 ('00414080','AircraftClass::AircraftClass','ctor variant: writes vptr 0x7E22A4 @41408A ([edi])','[已证]'),
 ('0041B430','AircraftClass::AircraftClass','ctor variant: writes vptr 0x7E22A4 @41B4E1','[已证]'),
 ('006F4300','TechnoClass::TechnoClass','ctor variant: writes vptr 0x7F4960 @6F4413','[已证]'),
 ('006F4500','TechnoClass::TechnoClass','ctor variant: writes vptr 0x7F4960 @6F450D','[已证]'),
 ('004D3540','FootClass::FootClass','ctor variant: writes vptr 0x7E8C94 @4D3568','[已证]'),
 ('004D3590','FootClass::FootClass','ctor variant: writes vptr 0x7E8C94 @4D359D','[已证]'),
 ('005F3B50','ObjectClass::ObjectClass','ctor variant: writes vptr 0x7EF060 @5F3B5D','[已证]'),
 ('005F3B80','ObjectClass::ObjectClass','ctor variant: writes vptr 0x7EF060 @5F3B87','[已证]'),
 ('004101C0','AbstractClass::AbstractClass','ctor variant: writes vptr 0x7E1F50 @4101D0','[已证]'),
 ('004101F0','AbstractClass::AbstractClass','ctor variant: writes vptr 0x7E1F50 @4101F0','[已证]'),
 ('004105A0','AbstractClass::~AbstractClass','scalar deleting dtor: writes 4 vptrs (kb/11 §0.2)','[已证]'),
]
for e,nm,sem,g in variants: add(e,nm,sem,g,EV)

# GetSize / WhatAmI slot functions (RTTI v[11]/v[12] direct, already known but now byte-proved)
slots=[
 ('00459E70','BuildingClass::GetSize','v[12] B8 20 07 00 00 C3 -> 0x720','[已证]'),
 ('00459EC0','BuildingClass::WhatAmI','v[11] B8 06 00 00 00 C3 -> 0x6 (Building)','[已证]'),
 ('00746DD0','UnitClass::GetSize','v[12] B8 E8 08 00 00 C3 -> 0x8E8','[已证]'),
 ('00746E20','UnitClass::WhatAmI','v[11] B8 01 00 00 00 C3 -> 0x1 (Unit)','[已证]'),
 ('005232F0','InfantryClass::GetSize','v[12] B8 F0 06 00 00 C3 -> 0x6F0','[已证]'),
 ('00523340','InfantryClass::WhatAmI','v[11] B8 0F 00 00 00 C3 -> 0xF (Infantry)','[已证]'),
 ('0041C170','AircraftClass::GetSize','v[12] B8 D8 06 00 00 C3 -> 0x6D8','[已证]'),
 ('0041C180','AircraftClass::WhatAmI','v[11] B8 02 00 00 00 C3 -> 0x2 (Aircraft)','[已证]'),
]
for e,nm,sem,g in slots: add(e,nm,sem,g,EV)

# field semantics upgrades (existing S05 entries now fully supported)
fields=[
 ('005F3900','ObjectClass::ObjectClass','+0x94 layer=ecx, +0x80=bl, +0x81=al, +0x74=bl writes; double-supported LAYOUT.md','[已证]'),
 ('007014A0','TechnoClass::SetOwner','writes [esi+0x21C] owner; double-supported 4w/196r; LAYOUT.md','[已证]'),
 ('005F4D30','ObjectClass::Limbo','sets +0x81=1 / +0x80=0; LAYOUT.md','[已证]'),
 ('005F4EC0','ObjectClass::Unlimbo','+0x81=0 / rollback=1; +0x74 read; LAYOUT.md','[已证]'),
]
for e,nm,sem,g in fields: add(e,nm,sem,g,'EVIDENCE/field_access_scan.json')

# dedupe by (entry,name), keep first
seen=set(); final=[]
for r in rows:
    k=(r[0],r[2])
    if k in seen: continue
    seen.add(k); final.append(r)
with open(OUT,'w',encoding='utf-8',newline='') as f:
    f.write('entry\tsubsystem\tname\tone_line_semantics\tgrade\tevidence_path\n')
    for r in final:
        f.write('\t'.join(r)+'\n')
print('wrote',OUT,'rows',len(final))
