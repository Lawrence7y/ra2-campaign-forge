#!/usr/bin/env python3
"""S16-K3 T1: AbstractClass / SuperClass / SuperWeaponTypeClass slot contracts.
Vtable boundaries from .rdata only: stop at COL pointer (.rdata value) or non-code.
RTTI via COL+0xC -> TD+8 inline name, fail-closed.
"""
import sys, struct
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S16-K3\work")
import k3_lib as K
b=K.Bin()

def first_insn(va):
    try:
        ins=list(K.md(skipdata=True).disasm(b.read(va,16),va))[0]
        if ins.id==0: return ".byte"
        return f"{ins.mnemonic} {ins.op_str}"
    except Exception:
        return "?"

def dump_vtable(label, vft, expect_col=None, maxslot=40):
    print(f"\n===== {label}  vftable={vft:08X} =====")
    # verify COL at vft-4
    col=b.u32(vft-4)
    r=K.rtti_from_col(b,col)
    if r:
        print(f"COL[vft-4]={col:08X} -> TD={r['ptd']:08X} name='{r['name']}' off={r['off']}")
        if expect_col and col!=expect_col:
            print(f"  !! WARN: expected COL {expect_col:08X}, got {col:08X}")
    else:
        print(f"COL[vft-4]={col:08X} -> RTTI UNREADABLE (fail-closed)")
    slots=[]
    for k in range(maxslot):
        va=vft+4*k
        val=b.u32(va)
        tag=""
        if b.in_rdata(val):
            rr=K.rtti_from_col(b,val)
            nm=rr['name'] if rr else "?"
            print(f"  slot[{k:2d}] @{va:08X} = {val:08X}  <COL/data ptr -> '{nm}'  [STOP]")
            break
        if not b.in_text(val):
            print(f"  slot[{k:2d}] @{va:08X} = {val:08X}  <non-code  [STOP]")
            break
        slots.append((k,val))
        print(f"  slot[{k:2d}] @{va:08X} = {val:08X}  {first_insn(val)}")
    print(f"  -> {len(slots)} code slots")
    return slots, col, r

# 1) AbstractClass main table from KB22 (0x7E1F50)
abstract_slots, abstract_col, abstract_r = dump_vtable("AbstractClass main", 0x7E1F50)

# 2) find SuperClass / SuperWeaponTypeClass vtables via TD
for cls_td, label, expect in [
    (0x8423E0,"SuperClass",0x80B610),
    (0x842600,"SuperWeaponTypeClass",0x80B6C8),
]:
    r=K.rtti_from_col(b,expect)
    nm = r['name'] if r else '?'
    ptd = r['ptd'] if r else 0
    print(f"\n--- {label} expect COL {expect:08X}: name='{nm}' TD={ptd:08X} ---")
    vfts=K.vftables_for_td(b, cls_td)
    print(f"  vftables found: {[(f'{v[chr(118)+chr(102)+chr(116)]:08X}', f'{v[chr(99)+chr(111)+chr(108)]:08X}', v['off'], len(v['slots'])) for v in vfts]}")
    # pick offset-0 table (primary) = min off==0
    main=[v for v in vfts if v['off']==0]
    for v in main:
        dump_vtable(f"{label} primary (off=0)", v['vft'], expect)
