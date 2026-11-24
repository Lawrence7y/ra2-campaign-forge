# -*- coding: utf-8 -*-
"""扩展回扫（k=0..140）复核高槽号行的 ②；并逐行验证槽值==entry。"""
import os, sys, json, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
import core2 as C2

WORK = os.path.dirname(os.path.abspath(__file__))
A = json.load(open(os.path.join(WORK,'analysis.json'), encoding='utf-8'))

def resolve_slot_ext(refva, kmax=140):
    best = None
    for k in range(0, kmax+1):
        vb = refva - 4*k
        c = C2.u32(vb - 4)
        if not c:
            continue
        ci = C2.parse_col(c)
        if not ci or ci['sig'] != 0:
            continue
        tdi = C2.parse_td(ci['td'])
        if tdi and tdi['name'] and '.?AV' in tdi['name']:
            best = {'vtable_base': vb, 'slot_off': 4*k, 'slot_num': k,
                    'col': ci['col'], 'td': tdi['td'], 'name_va': tdi['name_va'],
                    'rtti_name': tdi['name']}
            break
    return best

for rec in A:
    ea = int(rec['entry'], 16)
    print("="*90)
    print("#%d %s %s" % (rec['idx'], rec['entry'], rec['name']))
    for s in rec.get('ring2_slots', []):
        refva = int(s['slot_va'], 16)
        slotval = C2.u32(refva)
        print("  ref@%s slotval=%08X (entry=%08X %s)" % (
            s['slot_va'], slotval if slotval is not None else 0, ea,
            "MATCH" if slotval==ea else "MISMATCH"))
        if s.get('rtti_name'):
            print("    existing: vt=%s off=%s rtti=%s" % (s['vtable_base'], s['slot_off'], s['rtti_name']))
        else:
            ext = resolve_slot_ext(refva, 140)
            if ext:
                print("    EXT FOUND: vt=%08X slot_off=%d slot#=%d col=%08X td=%08X rtti=%s" % (
                    ext['vtable_base'], ext['slot_off'], ext['slot_num'],
                    ext['col'], ext['td'], ext['rtti_name']))
                # writes for extended vt
                w = C2.find_vtable_writes(ext['vtable_base'])
                for g in w['global']:
                    f = C2.find_containing_atlas_func(g['write_va'])
                    g['in_func'] = f
                    g['atexit'] = bool(C2.is_atexit_registered(f[0])) if f else False
                for rw in w['regdisp']:
                    f = C2.find_containing_atlas_func(rw)
                    if f:
                        w['global'].append({'write_va':'%08X'%rw,'global':None,'in_func':f,
                                            'atexit':bool(C2.is_atexit_registered(f[0]))})
                print("    writes:", json.dumps(w['global'], ensure_ascii=False))
            else:
                print("    EXT NOT FOUND (k<=140)")
