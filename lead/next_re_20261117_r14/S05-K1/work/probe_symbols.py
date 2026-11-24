import json, os
P = os.path.join('D:', os.sep, 'Project', 'ra2-campaign-forge', 're_atlas', 'evidence', 'rtti', 'symbols.json')
d = json.load(open(P, encoding='utf-8', errors='replace'))
print('keys', list(d.keys()))
cls = d.get('classes')
print('classes type', type(cls), 'len', len(cls) if hasattr(cls,'__len__') else '')
if isinstance(cls, dict):
    items = list(cls.items())[:5]
    for k,v in items:
        print(' ', k, '->', json.dumps(v)[:300] if not isinstance(v,str) else v[:200])
elif isinstance(cls, list):
    for v in cls[:5]:
        print(' ', json.dumps(v)[:300])
# search target class ctor names
import re
def walk(o, depth=0):
    pass
s = json.dumps(d, ensure_ascii=False)
for nm in ['BuildingClass::BuildingClass','UnitClass::UnitClass','InfantryClass::InfantryClass','AircraftClass::AircraftClass','ObjectClass::ObjectClass','TechnoClass::TechnoClass']:
    idx = s.find(nm)
    print(nm, 'found' if idx>=0 else 'MISS', (s[idx:idx+80] if idx>=0 else ''))
