# -*- coding: utf-8 -*-
import os, json, sys
WORK = os.path.dirname(os.path.abspath(__file__))
A = json.load(open(os.path.join(WORK,'analysis.json'), encoding='utf-8'))
for rec in A:
    print("="*100)
    print("#%d %s %s  grade=%s" % (rec['idx'], rec['entry'], rec['name'], rec['grade']))
    r1 = rec['ring1']
    print("  ① in_text=%s atlas_size=%s fallback=%s n_disasm=%s skip=%s first=%s last=%s ends=%s" % (
        r1.get('in_text'), r1.get('atlas_size'), r1.get('fallback_size'), r1.get('n_disasm'),
        r1.get('n_skipdata'), r1.get('first'), r1.get('last'), r1.get('ends_with_ret_or_jmp')))
    # ring2 slots
    print("  ② slots:")
    for s in rec.get('ring2_slots', []):
        print("     slot_va=%s sec=%s vt=%s off=%s col=%s td=%s rtti=%s" % (
            s.get('slot_va'), s.get('section'), s.get('vtable_base'), s.get('slot_off'),
            s.get('col'), s.get('td'), s.get('rtti_name')))
    # chA
    ch = rec.get('chA', {})
    print("  ③ chA p1/p2/p3=%s/%s/%s chB=%s" % (ch.get('p1'), ch.get('p2'), ch.get('p3'), rec.get('chB')))
    for st in ch.get('sites', []):
        print("     site call@%s callee=%s test@%s(%s,%s) jcc@%s %s tgt=%s form=%s falsy=%s" % (
            st.get('call_addr'), st.get('callee'), st.get('test_addr'), st.get('test_kind'),
            st.get('test_imm'), st.get('jcc_addr'), st.get('jcc_mnemonic'), st.get('jcc_target'),
            st.get('p3_form'), st.get('call_site_falsy')))
        cp = st.get('callee_profile') or {}
        print("        callee_prof consts=%s n_rets=%s origins=%s key=%s" % (
            cp.get('falsifiable_consts'), cp.get('n_rets'), cp.get('origins'), cp.get('callee_key')))
        print("        sig_t=%s" % st.get('sig_taken'))
        print("        sig_f=%s" % st.get('sig_fallthrough'))
    # ring4 writes
    print("  ④ direct=%s" % rec.get('ring4_direct'))
    for s in rec.get('ring2_slots', []):
        gw = s.get('global_writes', [])
        if gw:
            print("     vt=%s writes:" % s.get('vtable_base'))
            for g in gw:
                print("       write=%s global=%s in_func=%s atexit=%s" % (
                    g.get('write_va'), g.get('global'), g.get('in_func'), g.get('atexit')))
        if s.get('imm_loads'):
            print("     vt=%s imm_loads=%s" % (s.get('vtable_base'), s.get('imm_loads')))
