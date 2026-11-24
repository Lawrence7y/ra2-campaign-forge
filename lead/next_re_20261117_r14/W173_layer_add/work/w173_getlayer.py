# -*- coding: utf-8 -*-
"""针对 slot+0x78 = GetLayer 的逐字符核对"""
from __future__ import annotations
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import w173_common as C
import w173_layer_class as LC

E = C.EVID
b = C.B()


def dis(va, n=64):
    m = C.md(True)
    try:
        data = b.read(va, n)
    except Exception:
        return "  (unreadable)"
    out = []
    for ins in m.disasm(data, va):
        out.append("  %08X  %-7s %s" % (ins.address, ins.mnemonic, ins.op_str))
        if ins.mnemonic == "ret" or len(out) >= 16:
            break
    return "\n".join(out)


def main():
    L = ["=" * 95, "slot+0x78 返回值逐字符核对（GetLayer 候选）"]
    for fn, tag in [(0x5F4260, "ObjectClass::GetLayer? 共用 L2"),
                    (0x428970, "Animate L0"), (0x43AC90, "NeuronClass L0"),
                    (0x40FE1C, "? L1"), (0x5D6340, "MovieHandle L1"),
                    (0x65C320, "RadSiteClass L1"),
                    (0x4369F0, "BuildingLightClass L3"),
                    (0x62D770, "ParticleClass L3"),
                    (0x74A960, "VoxelAnimClass L3"),
                    (0x75F890, "WaveClass L3")]:
        L.append("-" * 90)
        L.append("%s fn=%08X" % (tag, fn))
        L.append(dis(fn))

    L.append("")
    L.append("=" * 95)
    L.append("关键 ObjectClass 派生类虚表 slot+0x78")
    vfts = LC.find_vftables(b)
    key_classes = ["UnitClass", "InfantryClass", "AircraftClass", "BuildingClass",
                   "TechnoClass", "ObjectClass", "AnimClass", "OverlayClass",
                   "TerrainClass", "SmudgeClass", "BulletClass", "ParticleClass",
                   "VoxelAnimClass", "WaveClass", "BuildingLightClass", "AirstrikeClass"]
    for vft in vfts:
        nm = LC.rtti_name(b, vft)
        if nm not in key_classes:
            continue
        try:
            fn = b.u32(vft + 0x78)
        except Exception:
            continue
        val, _ = LC.imm_return(fn)
        L.append("  %-20s vft=%08X slot78=%08X ret=%s" % (nm, vft, fn, val))
        L.append(dis(fn))

    C.write_text(os.path.join(E, "w173_getlayer_detail.txt"), L)
    print("getlayer detail written")


if __name__ == "__main__":
    main()
