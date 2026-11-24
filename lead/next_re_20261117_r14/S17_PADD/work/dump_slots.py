"""Dump [static-inferred] slotN bodies for 3b contract evaluation + caller counts."""
import re_lib as R

SLOTS = {
    "0048BB00": ("CommBufferClass::slot0", 0x0048BB00),
    "004A2930": ("CStreamClass::slot1", 0x004A2930),
    "004A2950": ("CStreamClass::slot2", 0x004A2950),
    "004A2990": ("CStreamClass::slot0", 0x004A2990),
    "004A2A20": ("CStreamClass::slot3", 0x004A2A20),
    "004A2CD0": ("CStreamClass::slot4", 0x004A2CD0),
    "004A2E00": ("CStreamClass::slot5", 0x004A2E00),
    "006CF430": ("SwizzleManagerClass::slot0", 0x006CF430),
    "006CF490": ("SwizzleManagerClass::slot5", 0x006CF490),
    "006CF4B0": ("SwizzleManagerClass::slot1", 0x006CF4B0),
    "006CF4C0": ("SwizzleManagerClass::slot2", 0x006CF4C0),
    "006CF4D0": ("SwizzleManagerClass::slot7", 0x006CF4D0),
    "006CF4E0": ("SwizzleManagerClass::slot8", 0x006CF4E0),
    "006CF320": ("SwizzleManager_Compare [out of atlas]", 0x006CF320),
}

for key, (label, va) in SLOTS.items():
    print("=" * 90)
    print("[%s] %s @ 0x%08X" % (key, label, va))
    n = 0x60
    b = R.read_bytes(va, n)
    print("bytes:", b.hex()[:120] if b else None)
    for a, mn, op, sz, bh in R.disasm(va, n):
        print("  %08X  %-18s %-8s %s" % (a, bh, mn, op))
        if mn.startswith("ret"):
            break

print("\n\n############ CALLER COUNTS ############")
for label, va in [("00539AE0 Load_StreamFields", 0x00539AE0),
                  ("0055AAC0 Load_SwizzledObject", 0x0055AAC0),
                  ("004B6BB0 Swizzle_RegisterPointerArray", 0x004B6BB0)]:
    tv, ts, _ = R.TEXT
    bnd = sorted(set(s for s, t in R.sweep_e8_boundary(tv, tv+ts) if t == va))
    print("%s: %d boundary-valid direct call sites: %s" % (
        label, len(bnd), [hex(x) for x in bnd[:12]]))
