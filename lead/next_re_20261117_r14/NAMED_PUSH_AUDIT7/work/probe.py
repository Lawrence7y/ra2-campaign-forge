"""AUDIT7 probe: per-row raw facts from my own disassembly."""
import sys, json
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT7\work")
from core import *

ROWS = [
    (0x0062D9A0, 'S20', 'ParticleClass::slot8', 0x007EF974, 0x007EF954),
    (0x0062FE90, 'S20', 'ParticleSystemClass::slot10', 0x007EFBC4, 0x007EFB9C),
    (0x00630090, 'S20', 'ParticleSystemClass::slot6', 0x007EFBB4, 0x007EFB9C),
    (0x00644960, 'S20', 'ParticleSystemTypeClass::slot8', 0x007F00C8, 0x007F00A8),
    (0x006457A0, 'S20', 'ParticleTypeClass::slot6', 0x007F01A0, 0x007F0188),
    (0x00645950, 'S20', 'ParticleTypeClass::slot8', 0x007F01A8, 0x007F0188),
    (0x00749F30, 'S20', 'VoxelAnimClass::slot23', 0x007F6374, 0x007F6318),
    (0x0074BA30, 'S20', 'VoxelAnimTypeClass::slot8', 0x007F6568, 0x007F6548),
    (0x0071E1D0, 'S06', 'TerrainTypeClass::slot5', None, None),
    (0x007220A0, 'S06', 'TiberiumClass::slot7', None, None),
    (0x007220D0, 'S06', 'TiberiumClass::slot6', None, None),
    (0x007281A0, 'S06', 'TubeClass::slot5', None, None),
    (0x00763D90, 'S06', 'WaypointPathClass::slot6', None, None),
]


def body(entry, max_insn=3000):
    o = va2off(entry)
    out = []
    for insn in md.disasm(DATA[o:o + 30000], entry):
        out.append(insn)
        if len(out) >= max_insn:
            break
        if insn.mnemonic.startswith('ret'):
            nx = DATA[va2off(insn.address) + insn.size: va2off(insn.address) + insn.size + 4]
            if all(x in (0xCC, 0x90, 0x00) for x in nx) or len(nx) < 4:
                break
    return out


def summary_of(entry):
    ins = body(entry)
    print(f"=== {entry:08X} insns={len(ins)} skipdata={sum(1 for i in ins if i.id==0)} "
          f"last={ins[-1].address:08X} {ins[-1].mnemonic} {ins[-1].op_str}")
    return ins


if __name__ == '__main__':
    which = sys.argv[1] if len(sys.argv) > 1 else 'ring2'
    if which == 'ring2':
        for entry, sub, name, slot, vtb in ROWS:
            print(f"\n######## {entry:08X} {sub} {name}")
            # find all vtables containing entry
            hits = find_dword(entry)
            print(f"  dword-refs of entry: {[(h[0], hex(h[1])) for h in hits]}")
            for sec, va in hits:
                if sec not in ('.rdata', '.data'):
                    continue
                vt, idx = vtable_containing(va)
                r = rtti_of_vtable(vt)
                print(f"  slot {va:08X} in vtable {vt:08X} index={idx} (off 0x{idx*4:X})")
                print(f"    RTTI col={r['col'] and hex(r['col'])} td={r['td'] and hex(r['td'])} name={r['name']!r} err={r['err']}")
                print(f"    vt first6: {[(hex(a), hex(v)) for a, v in vt_first_slots(vt, 6)]}")
            if slot:
                print(f"  claimed slot {slot:08X} -> dword {u32(slot) and hex(u32(slot))}; "
                      f"claimed vt {vtb:08X} -> dword {u32(vtb) and hex(u32(vtb))}")
