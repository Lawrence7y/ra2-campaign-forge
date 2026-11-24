"""AUDIT7: for each row, locate vtable install sites in .text and classify host function."""
import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT7\work")
from core import *
import idx

ROWS = [
    (0x0062D9A0, 'S20', 'ParticleClass::slot8',          0x007EF974, 0x007EF954),
    (0x0062FE90, 'S20', 'ParticleSystemClass::slot10',   0x007EFBC4, 0x007EFB9C),
    (0x00630090, 'S20', 'ParticleSystemClass::slot6',    0x007EFBB4, 0x007EFB9C),
    (0x00644960, 'S20', 'ParticleSystemTypeClass::slot8', 0x007F00C8, 0x007F00A8),
    (0x006457A0, 'S20', 'ParticleTypeClass::slot6',      0x007F01A0, 0x007F0188),
    (0x00645950, 'S20', 'ParticleTypeClass::slot8',      0x007F01A8, 0x007F0188),
    (0x00749F30, 'S20', 'VoxelAnimClass::slot23',        0x007F6374, 0x007F6318),
    (0x0074BA30, 'S20', 'VoxelAnimTypeClass::slot8',     0x007F6568, 0x007F6548),
    (0x0071E1D0, 'S06', 'TerrainTypeClass::slot5',       0x007F546C, 0x007F5458),
    (0x007220A0, 'S06', 'TiberiumClass::slot7',          0x007F5744, 0x007F5728),
    (0x007220D0, 'S06', 'TiberiumClass::slot6',          0x007F5740, 0x007F5728),
    (0x007281A0, 'S06', 'TubeClass::slot5',              0x007F59C4, 0x007F59B0),
    (0x00763D90, 'S06', 'WaypointPathClass::slot6',       0x007F6E88, 0x007F6E70),
]

ATEXIT = 0x7C978A


def sites(vt):
    db = idx.db()
    return sorted(db['immmap'].get(vt, []))


def host(site):
    return idx.func_start(site)


def classify(fstart, site):
    recs = [r for r in idx.db()['recs'] if fstart <= r[0] <= site + 0x200]
    # trim at first ret-with-padding after site
    body = []
    for r in recs:
        body.append(r)
        if r[2].startswith('ret') and r[0] >= site:
            nxt = DATA[va2off(r[0] + r[1]):va2off(r[0] + r[1]) + 4]
            if all(x in (0xCC, 0x90, 0x00) for x in nxt) or len(nxt) < 4:
                break
    mns = [r[2] for r in body]
    calls = [r for r in body if r[2] == 'call']
    calltgt = [r[5][0] for r in calls if r[5]]
    info = {
        'start': fstart, 'site': site, 'n': len(body),
        'calls': [f"{c[0]:08X}->{c[5][0]:08X}" for c in calls if c[5]],
        'has_free': any(t == 0x7C8B3D for t in calltgt),
        'has_atexit': any(t == ATEXIT for t in calltgt),
        'stores_imm_after_site': [(r[0], r[2] + ' ' + r[3]) for r in body if r[0] >= site and r[5]],
    }
    return info


def atexit_registered(f):
    """is function f pushed then passed to 0x7C978A ?"""
    db = idx.db()
    hits = []
    for a in db['immmap'].get(f, []):
        recs = {r[0]: r for r in db['recs']}
        # look 1-3 instructions ahead for call 0x7C978A
        for k in range(1, 5):
            nxt = None
            for r in db['recs']:
                if r[0] == a + 0:
                    break
            break
        hits.append(a)
    # simpler: find any 'call 0x7C978A' whose preceding 2 insns contain a push of f
    res = []
    for csite in db['calls'].get(ATEXIT, []):
        recs = db['recs']
        pre = [r for r in recs if csite - 16 <= r[0] < csite]
        if any(f in r[5] for r in pre):
            res.append(csite)
    return res


if __name__ == '__main__':
    for entry, sub, name, slot, vt in ROWS:
        print(f"\n######## {entry:08X} {sub} {name} vt={vt:08X}")
        db = idx.db()
        recs = {r[0]: r for r in db['recs']}
        for s in sites(vt):
            r = recs[s]
            fs = host(s)
            info = classify(fs, s)
            print(f"  site {s:08X}  {r[2]} {r[3]}")
            print(f"    host {fs:08X}.. n={info['n']} has_free={info['has_free']} has_atexit={info['has_atexit']}")
            print(f"    calls: {info['calls'][:12]}")
            print(f"    after-site imm stores: {info['stores_imm_after_site'][:6]}")
            a = atexit_registered(fs)
            print(f"    atexit-registered-as-target? {'YES '+str([hex(x) for x in a]) if a else 'no'}")
