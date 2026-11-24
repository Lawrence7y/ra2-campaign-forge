# -*- coding: utf-8 -*-
"""逐行细节打印（只读 verify_out.json）。"""
import io, json, sys
sys.dont_write_bytecode = True
d = json.load(io.open(r"D:/Project/ra2-campaign-forge/lead/next_re_20261117_r14/R16_AUDIT_F1_B4/verify_out.json",
                      encoding='utf-8'))
mode = sys.argv[1] if len(sys.argv) > 1 else 'ring'
for r in d['rows']:
    if mode == 'ring':
        print("%s slot=%-3s vt=%s site=%s func=%s ring4=%s eq=%s"
              % (r['entry'], r['decl']['slot'], r['decl']['vt'], r['decl']['site'],
                 r['site_func'], r['ring4']['token'], r['ring4']['equals_declared']))
        print("      ring4_raw: %s" % r['ring4']['raw'])
    elif mode == 'c2':
        print("== %s %s vt=%s  writes=%d usable=%d in_entry=%d"
              % (r['entry'], r['name'], r['decl']['vt'], r['C2']['n_writes'],
                 r['C2']['n_usable'], r['C2b']['n_in_entry_body']))
        for w in r['C2']['writes']:
            print("     %s %-18s func=%s in_entry=%s delfree=%s atexit=%s decl=%s  %s"
                  % (w['site'], w['verdict'], w['func'], w['in_entry_body'],
                     w.get('delfree_sig'), w.get('atexit_reg'), w['is_declared'],
                     w['asm']))
    elif mode == 'c1':
        print("== %s %s slot=%s vt=%s tables=%d same_slot=%d same_slot_cls=%d uniq=%s"
              % (r['entry'], r['row_class'], r['decl']['slot'], r['decl']['vt'],
                 r['C1']['n_candidate_tables'], r['C1']['n_same_slot'],
                 r['C1']['n_same_slot_classmatch'], r['C1']['chosen_is_unique_classmatch']))
        for t in r['C1']['same_slot']:
            print("     vt=%s col=%s head=%-22s cls=%s slots=%s"
                  % (t['vt'], t['col'], t['head'], t['cls_match'], t['slots']))
        others = [t for t in r['C1']['tables'] if t['vt'] not in {x['vt'] for x in r['C1']['same_slot']}]
        for t in others:
            print("     [other-slot] vt=%s head=%-22s cls=%s slots=%s"
                  % (t['vt'], t['head'], t['cls_match'], t['slots']))
    elif mode == 'skel':
        print("== %s" % r['entry'])
        print("   %s" % r['skeleton'])
