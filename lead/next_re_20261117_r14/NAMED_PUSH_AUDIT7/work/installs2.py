"""AUDIT7: locate vtable install sites + classify host function (ctor vs dtor vs atexit)."""
import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT7\work")
from core import *
import fast

ROWS = [
    (0x0062D9A0, 'S20', 'ParticleClass::slot8',           0x007EF974, 0x007EF954),
    (0x0062FE90, 'S20', 'ParticleSystemClass::slot10',    0x007EFBC4, 0x007EFB9C),
    (0x00630090, 'S20', 'ParticleSystemClass::slot6',     0x007EFBB4, 0x007EFB9C),
    (0x00644960, 'S20', 'ParticleSystemTypeClass::slot8', 0x007F00C8, 0x007F00A8),
    (0x006457A0, 'S20', 'ParticleTypeClass::slot6',       0x007F01A0, 0x007F0188),
    (0x00645950, 'S20', 'ParticleTypeClass::slot8',       0x007F01A8, 0x007F0188),
    (0x00749F30, 'S20', 'VoxelAnimClass::slot23',         0x007F6374, 0x007F6318),
    (0x0074BA30, 'S20', 'VoxelAnimTypeClass::slot8',      0x007F6568, 0x007F6548),
    (0x0071E1D0, 'S06', 'TerrainTypeClass::slot5',        0x007F546C, 0x007F5458),
    (0x007220A0, 'S06', 'TiberiumClass::slot7',           0x007F5744, 0x007F5728),
    (0x007220D0, 'S06', 'TiberiumClass::slot6',           0x007F5740, 0x007F5728),
    (0x007281A0, 'S06', 'TubeClass::slot5',               0x007F59C4, 0x007F59B0),
    (0x00763D90, 'S06', 'WaypointPathClass::slot6',       0x007F6E88, 0x007F6E70),
]

FREE = 0x7C8B3D


def report(vt):
    print(f"  install sites for vt {vt:08X}:")
    for s in fast.refs_imm(vt):
        print(f"    {s:08X}  {fast.db()['recs'][s][0]} {fast.db()['recs'][s][1]}")


def hostinfo(site):
    fs = fast.func_start(site)
    b = fast.body(fs)
    end = b[-1][0]
    calls = [r[4][0] for r in b if r[1] == 'call' and r[4]]
    stores = [(r[0], f"{r[1]} {r[2]}") for r in b if r[4] and any(v in [0x7EF954, 0x7EFB9C, 0x7F00A8, 0x7F0188, 0x7F6318, 0x7F6548, 0x7F5458, 0x7F5728, 0x7F59B0, 0x7F6E70] for v in r[4])]
    return {'start': fs, 'end': end, 'n': len(b), 'calls': calls,
            'free': [hex(c) for c in calls if c == FREE],
            'atexit': fast.atexit_sites_for(fs),
            'vtstores': stores}


if __name__ == '__main__':
    for entry, sub, name, slot, vt in ROWS:
        print(f"\n######## {entry:08X} {sub} {name} vt={vt:08X}")
        report(vt)
