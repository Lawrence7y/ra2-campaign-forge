# S13-K1: generate coverage_delta.tsv from established functions
import csv
BASE=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13-K1"
EV="lead/next_re_20261117_r14/S13-K1/EVIDENCE/"
rows=[
 # entry, name, semantics, grade, evidence
 ("7730E0","WeaponTypeClass::WhatAmI","returns AbstractType id 0x31 (49)","[已证]",EV+"verify_slots.txt"),
 ("7730D0","WeaponTypeClass::GetSize","returns 0x160 (352) instance size","[已证]",EV+"verify_slots.txt"),
 ("772080","WeaponTypeClass::LoadFromINI","INI loader: 56 keys -> +0x98..+0x15C; Warhead/Projectile ptr at +0xAC/+0xA0","[已证]",EV+"ini_fields.tsv"),
 ("771C70","WeaponTypeClass::Constructor","ctor: base 0x410800; field defaults +0x98..+0x15C; registers in global array","[已证]",EV+"ctor_candidates_detail.txt"),
 ("75E3B0","WarheadTypeClass::FindOrMake","name->WarheadTypeClass*; scans [0x8874c4], new(0x1d0)+ctor if absent","[已证]",EV+"resolvers.txt"),
 ("75E500","WarheadTypeClass::WhatAmI","returns id 0x32 (50)","[已证]",EV+"verify_slots.txt"),
 ("75E4F0","WarheadTypeClass::GetSize","returns 0x1D0 (464)","[已证]",EV+"verify_slots.txt"),
 ("75D3A0","WarheadTypeClass::LoadFromINI","INI loader: 53 keys; Verses double[11]@+0xA0 via strtok loop","[已证]",EV+"ini_fields.tsv"),
 ("75CEC0","WarheadTypeClass::Constructor","ctor: Verses 11x double init at +0xA0 (rep movsd), defaults to +0x1C8","[已证]",EV+"ctor_candidates_detail.txt"),
 ("46C850","BulletTypeClass::WhatAmI","returns id 0x09 (9)","[已证]",EV+"verify_slots.txt"),
 ("46C860","BulletTypeClass::GetSize","returns 0x2F8 (760)","[已证]",EV+"verify_slots.txt"),
 ("46BEE0","BulletTypeClass::LoadFromINI","INI loader: 41 keys (rules+art) -> +0x22F..+0x2F7","[已证]",EV+"ini_fields.tsv"),
 ("46BBC0","BulletTypeClass::Constructor","ctor: base 0x5F7090; default flags +0x294..+0x2A9, fields to +0x2F7","[已证]",EV+"ctor_candidates_detail.txt"),
 ("46C790","BulletTypeClass::FindOrMake","name->BulletTypeClass*; scans [0xa83c84], new(0x2f8)+ctor if absent","[已证]",EV+"resolvers.txt"),
 ("46B550","BulletClass::WhatAmI","returns id 0x08 (8)","[已证]",EV+"rtti_extract.txt"),
 ("46B540","BulletClass::GetSize","returns 0x160 (352)","[已证]",EV+"rtti_extract.txt"),
 ("466380","BulletClass::Constructor","ctor: base 0x5F3900; Type*+0xAC, defaults +0x100..+0x158","[已证]",EV+"ctor_candidates_detail.txt"),
 ("468090","BulletClass::Draw","draws projectile; reads Type*+0xAC, doubles +0xE8/+0xF0, +0x158","[静态推断]",EV+"bullet_methods2.txt"),
 ("468670","BulletClass::Move/Update","reads/writes position doubles +0xE8/+0xF0/+0xF8, Type*+0xAC","[静态推断]",EV+"bullet_methods2.txt"),
 ("46B5A0","BulletClass::SetAltitude","mov [ecx+0x10C], arg (setter for +0x10C)","[静态推断]",EV+"bullet_methods2.txt"),
]
with open(BASE+r"\coverage_delta.tsv","w",encoding="utf-8",newline="\n") as f:
    for e,n,s,g,ev in rows:
        f.write(f"{e}\tS13\t{n}\t{s}\t{g}\t{ev}\n")
print("wrote",len(rows),"rows")
