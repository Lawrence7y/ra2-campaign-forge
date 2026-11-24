# -*- coding: utf-8 -*-
"""Independent verification pass for NAMED_PUSH_S17_B1.
Dump exactly the anchors I need to judge the 4 rings, with fresh eyes.
"""
import sys, os, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import np_core as C

def dump(ea, maxbytes=0x200, maxi=80, title=""):
    print("="*70)
    print("FUNC %s  %s  atlas=%s" % (C.hx(ea), title, C.ATLAS.get(C.hx(ea))))
    n=0
    for ins in C.disasm_body(ea, maxbytes):
        if n>=maxi: 
            print("  ... truncated at %d insns" % maxi); break
        print("  %s: %-9s %-40s ; %s" % (C.hx(ins.address), ins.mnemonic, ins.op_str, ins.bytes.hex().upper()))
        n+=1
    print()

def vtable(vt, n=7, title=""):
    print("--- VT %s %s ---" % (C.hx(vt), title))
    for i in range(n):
        print("  [%+02X] slot#%-2d @%s = %s" % (4*i, i, C.hx(vt+4*i), C.hx(C.u32(vt+4*i))))
    c=C.u32(vt-4)
    ci=C.parse_col(c) if c else None
    if ci:
        tdi=C.parse_td(ci['td'])
        print("  COL=%s sig=%d pTD=%s pCHD=%s name=%r" % (C.hx(c), ci['sig'], C.hx(ci['td']) if ci['td'] else '-', C.hx(ci['chd']) if ci['chd'] else '-', tdi['name'] if tdi else None))
    print()

print("SHA match:", C.sha256_exe()==C.EXPECT_SHA, "TEXT=[%s,%s)"%(C.hx(C.TEXT_VA),C.hx(C.TEXT_VA+C.TEXT_SIZE)))
print()

# ---- ③ callee bodies ----
dump(0x4A3020, 0x140, 90, "callee checked by 004A2CD0 slot4 (direct 2x)")
dump(0x4A2990, 0xA0, 70, "slot0 of vt 007E5DAC -> callee of call [eax] in 006BEF10")
dump(0x6caec0, 0x100, 90, "ctor called by 006BF690 CreateInstance")
dump(0x6BF5D0, 0xA0, 70, "slot0 of vt 007F37E0")

# ---- vtables ----
vtable(0x007E5DAC, 7, "CStreamClass primary")
vtable(0x007E5D94, 5, "CStreamClass secondary([esi+4])")
vtable(0x007F3768, 6, "TClassFactory<CStreamClass>")
vtable(0x007F37E0, 6, "TClassFactory<SuperClass>")

# ---- dword refs for free functions ----
for e in (0x00539AE0, 0x0055AAC0):
    refs=C.find_dword_refs(e)
    print("dword refs for %s : %d  %s" % (C.hx(e), len(refs), [ (C.hx(a),s) for a,s in refs ]))

# ---- RTTI chains ----
for e, slot in [(0x004A2B60,0x007E5DB8),(0x004A2CD0,0x007E5DBC),(0x006BEF10,0x007F3774),(0x006BF690,0x007F37EC)]:
    si=C.resolve_slot(slot, kmax=64)
    print("RTTI %s slot@%s val@slot=%s -> %s" % (C.hx(e), C.hx(slot), C.hx(C.u32(slot)), si and {
        'vt':C.hx(si['vtable_base']),'off':si['slot_off'],'idx':si['slot_idx'],
        'col':C.hx(si['col']),'td':C.hx(si['td']),'name':si['rtti_name']}))

# ---- all vtable write sites + atexit classification ----
for vt in (0x007E5DAC, 0x007F3768, 0x007F37E0):
    w=C.find_vtable_writes(vt)
    print("WRITE SITES vt %s: global=%s regdisp=%s imm_load=%s" % (C.hx(vt), w['global'], w['regdisp'], w['imm_load']))
    for d in w['regdisp']:
        a=int(d,16); af=C.containing_atlas_func(a)
        print("   regdisp@%s in_func=%s atexit=%s" % (d, af, C.is_atexit_registered(af[0]) if af else None))
    print()
