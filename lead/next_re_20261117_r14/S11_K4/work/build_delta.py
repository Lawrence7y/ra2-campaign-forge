#!/usr/bin/env python3
"""Generate S11_K4/coverage_delta.tsv from fresh evidence files only.

Upgrade rule: an S11 row is raised to [已证] iff its entry is a direct vtable slot
in the freshly rebuilt .rdata/RTTI layout, or it is a proven constructor from
the independent two-point factory closure. No high-level semantic is inferred.
"""
from pathlib import Path
import json,csv,re,collections
ROOT=Path(r'D:\Project\ra2-campaign-forge'); R=ROOT/'lead/next_re_20261117_r14'; CARD=R/'S11_K4'
lay=json.loads((CARD/'work/layout.json').read_text(encoding='utf-8'))
clo=json.loads((CARD/'work/closure.json').read_text(encoding='utf-8'))
ent=json.loads((CARD/'work/entry_evidence.json').read_text(encoding='utf-8'))
with (R/'COVERAGE/coverage.tsv').open(encoding='utf-8',newline='') as f:
 cov=[r for r in csv.DictReader(f,delimiter='\t') if r['subsystem']=='S11']
with (ROOT/'lead/next_re_20261112_r10/W130_atlas/function_atlas.tsv').open(encoding='utf-8',newline='') as f:
 atl={r['entry'].lower() for r in csv.DictReader(f,delimiter='\t')}
closure_by={r['entry']:r for r in []}
gets={r['off0_slot9']:r for r in clo}
ctors={r['ctor']:r for r in clo}
SHARED='004C9150'

def iface_name(off,slot):
    if off==0 and slot<=7: return 'IPersistStream'
    if off==0 and slot in (8,9): return 'Primary'
    if off==4: return 'ILocomotion'
    if off==24: return 'IPiggyback'
    return f'off{off}'

def structural_name(old,occs):
    if old.startswith('sub_') or not old:
        # Prefer the most specific class/interface/slot occurrence.
        cand=[o for o in occs if 'TClassFactory' not in o['mangled']] or occs
        o=cand[0]
        cls=o['class']
        return f'{cls}::{iface_name(o["interface_offset"],o["slot"])}_vslot{o["slot"]:02d}'
    return old

rows=[]; stats=collections.Counter()
for r in cov:
    e=r['entry'].upper(); grade=r['grade'].strip()
    if grade=='[已证]':
        continue
    occs=ent.get(e,[])
    if not occs and e not in ctors:
        continue
    if e==SHARED:
        continue
    oldname=r['name'].strip()
    name=oldname; sem=''; ev='EVIDENCE/entry_evidence.txt'
    if e in gets:
        g=gets[e]
        if g['closed']:
            name=f'{g["class"]}::GetSize'
            sem=f'YRpp Size(); off0 main vtable slot9 bytes {g["slot9_bytes"]} imm=0x{g["slot9_imm"]:X}; factory {g["factory_ci"]} push {g["size_from_push"]} ({g["push_encoding"]}) -> 7C8E17; ctor {g["ctor"]} installs {g["off0_vt"]}'
            ev='EVIDENCE/closure.txt;EVIDENCE/entry_evidence.txt'
            stats['getsize']+=1
    elif e in ctors:
        g=ctors[e]
        name=f'{g["class"]}::{g["class"]}'
        sem=f'ctor called by factory {g["factory_ci"]} after push 0x{g["size_from_push"]:X} ({g["push_encoding"]}) -> 7C8E17; writes canonical vtables incl {g["off0_vt"]}'
        ev='EVIDENCE/closure.txt'
        stats['ctor']+=1
    else:
        name=structural_name(oldname,occs)
        # RTTI class names, interface offsets and slots from all occurrences.
        sig=[]
        for o in occs[:4]:
            sig.append(f'{o["class"]}/off{o["interface_offset"]}/slot{o["slot"]}@{o["vtable"]}:{o["slot_bytes"]}')
        if len(occs)>4: sig.append(f'+{len(occs)-4} more vtables')
        sem='RTTI-bound vtable implementation: '+', '.join(sig)+'; first bytes '+occs[0]['entry_bytes'][:32]
        stats['vtable']+=1
    rows.append((e,'S11',name,sem,'[已证]',ev))
    stats['total']+=1
    if e.lower() in atl: stats['atlas']+=1
    else: stats['outside']+=1
# stable sort by entry
rows.sort(key=lambda x:int(x[0],16))
outp=CARD/'coverage_delta.tsv'
outp.write_text('\n'.join('\t'.join(r) for r in rows)+'\n',encoding='utf-8')
# validation report
report=[]
report.append('DELTA_ROWS=%d'%len(rows))
report.append('UPGRADE_BY_KIND='+repr(dict(stats)))
report.append('ATLAS_ROWS=%d OUTSIDE_ATLAS=%d'%(stats['atlas'],stats['outside']))
base_proved_atlas=29; base_named_atlas=358; den=368
new_atlas_proved=stats['atlas']
report.append('BASE_ATLAS_PROVED=%d FINAL_ATLAS_PROVED=%d FINAL_PCT=%.4f'%(base_proved_atlas,base_proved_atlas+new_atlas_proved,100*(base_proved_atlas+new_atlas_proved)/den))
report.append('DOD_THRESHOLD=%d STILL_NEED=%d'%((den+1)//2,max(0,(den+1)//2-(base_proved_atlas+new_atlas_proved))))
# ensure no header and exact columns
bad=0
for line in outp.read_text(encoding='utf-8').splitlines():
    if len(line.split('\t'))!=6 or not re.fullmatch(r'[0-9A-F]{8}',line.split('\t')[0]): bad+=1
report.append('BAD_ROWS=%d'%bad)
(CARD/'work/build_delta.log').write_text('\n'.join(report)+'\n',encoding='utf-8')
print('\n'.join(report))
