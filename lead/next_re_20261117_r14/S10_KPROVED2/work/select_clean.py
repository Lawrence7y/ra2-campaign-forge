"""Find A-set rows where name-class == 16 base-class attribution, with 3b evidence."""
from re_core import PE, census_vtables
from func_analyze import load_a_rows
from baseline import detect_3b
import re

pe=PE()
vts,emap=census_vtables(pe)
rows=load_a_rows()

def nameclass(name):
    m=re.match(r'^(\w+?)::',name)
    return m.group(1) if m else None

HIER=['TechnoClass','BuildingClass','FootClass','InfantryClass','UnitClass','AircraftClass',
      'MissionClass','ObjectClass','AbstractClass','VeinholeMonsterClass']
DESC={'TechnoClass':'BuildingClass FootClass InfantryClass UnitClass AircraftClass',
      'FootClass':'InfantryClass UnitClass AircraftClass',
      'ObjectClass':'TechnoClass BuildingClass FootClass InfantryClass UnitClass AircraftClass',
      'MissionClass':'', 'AbstractClass':'ObjectClass TechnoClass BuildingClass FootClass InfantryClass UnitClass AircraftClass'}

def base_class(names):
    cls=[n.replace('.?AV','').replace('@@','') for n in names]
    cls=[c for c in cls if c in HIER]
    if not cls: return None
    for c in HIER:
        if c in cls:
            others=[x for x in cls if x!=c]
            if all(x in DESC.get(c,'').split() for x in others):
                return c
    return cls[0]

print('entry\tname\tnholds\theldclasses\tbase\tname_cls\tmatch\t3b_ev')
for r in sorted(rows,key=lambda x:int(x['entry'],16)):
    e=int(r['entry'],16); hi=int(r['ext_hi'],16)
    if hi-e>20000: hi=e+4000
    holds=emap.get(e,[])
    names=sorted(set(h['name'] for h in holds))
    base=base_class(names)
    nc=nameclass(r['name'])
    s,l,ev=detect_3b(e,hi)
    if s and nc and base:
        print(f'{r["entry"]}\t{r["name"]}\t{len(holds)}\t{";".join(names)}\t{base}\t{nc}\t{nc==base}\t{ev[:2]}')
