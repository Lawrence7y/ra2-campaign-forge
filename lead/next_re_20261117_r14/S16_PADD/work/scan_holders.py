import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S16_PADD\work")
import re_lib as R

CANDS = {
    "0053DBC0": "T_VectorClass_PAVIonBlastClass__::slot4 (FindItemIndex)",
    "0053DCD0": "T_DynamicVectorClass_PAVIonBlastClass__::slot4 (FindItemIndex)",
    "0053DAA0": "T_DynamicVectorClass_PAVIonBlastClass__::slot1 (operator==)",
    "0053DA40": "T_DynamicVectorClass_PAVIonBlastClass__::slot3 (Clear)",
    "006CDEB0": "SuperClass::slot3",
    "006CDFF0": "SuperClass::slot10",
    "006CE1F0": "SuperClass::slot3b",
    "006CE7C0": "SuperWeaponTypeClass::slot3",
    "006CE800": "SuperWeaponTypeClass::slot5",
    "006CEA10": "SuperWeaponTypeClass::slot16",
    "006CEF80": "SuperWeaponTypeClass::slot27",
    "0071A650": "TemporalClass::slot13",
    "0071A660": "TemporalClass::slot5",
    "0071A700": "TemporalClass::slot6",
    "0071A720": "TemporalClass::slot3",
    "0071A760": "TemporalClass::slot23",
    "0071B190": "TemporalClass::slot12",
    "0071B1A0": "TemporalClass::slot11",
    "0071B1B0": "TemporalClass::slot8",
}

for hx, label in CANDS.items():
    va = int(hx, 16)
    holders = R.vtable_holders(va)
    print(f"=== {hx} {label} : {len(holders)} raw 4B hits ===")
    for slot_va, sec, off in holders:
        # try vtable base = slot_va - 4*k for k 0..40
        base = None
        slot = None
        for k in range(0, 41):
            b = slot_va - 4*k
            if b % 4: continue
            rtti = R.rtti_of_vtable(b)
            if rtti and rtti["name"].startswith(".?AV"):
                base, slot, info = b, k, rtti
                break
        if base:
            print(f"   slot_va={slot_va:08X} sec={sec}  vtable_base~{base:08X} slot{k}={slot} RTTI={info['name']}")
        else:
            print(f"   slot_va={slot_va:08X} sec={sec}  (no RTTI found in -0..-160)")
    print()
