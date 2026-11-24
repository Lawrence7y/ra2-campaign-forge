# -*- coding: utf-8 -*-
"""R16-D1-WIDE-B2 class-consistency scan (read-only gamemd.exe / writes only this dir).

Reuses R16_PROBE_4FINAL.final's authoritative table enumerator (import, not reimplement)
to find, for each B2 entry, EVERY live table holding it, then applies card §3.4
"类一致优先": when final.tsv's decisive table class != row-name class, pick the
row-name class's own live table (with an install site outside the entry body).

final.py has an if-__name__ guard, so importing it runs no writes.
"""
import io, os, sys, json, bisect, re

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
PROBE = os.path.join(R14, "R16_PROBE_4FINAL")
ROOT = os.path.dirname(os.path.dirname(R14))
EXE = os.path.join(ROOT, "ra2youli", "gamemd.exe")
sys.path.insert(0, PROBE)
import final as F   # noqa: E402  (authoritative, read-only at import)

IB = F.IMAGE_BASE
B2 = ['0046C890','00473B10','004A2990','004A8960','004A9840','004AAD30',
      '004AAE90','004AB9B0','004D7330','004D94B0','004DFB70','004F4320',
      '004F4480','0051D6F0','00523340','0054E890','0054EA70','005B3970']
# row-name class from coverage name (col3) = text before ::; template pseudo-names handled by token match
NAMES = {
 '0046C890':'BulletTypeClass','00473B10':'CCFileClass','004A2990':'CStreamClass',
 '004A8960':'TabClass','004A9840':'TabClass','004AAD30':'TabClass',
 '004AAE90':'TabClass','004AB9B0':'DisplayClass','004D7330':'FootClass',
 '004D94B0':'FootClass','004DFB70':'AircraftClass','004F4320':'MouseClass',
 '004F4480':'MouseClass','0051D6F0':'InfantryClass','00523340':'InfantryClass',
 '0054E890':'T_DynamicVectorClass_PAUKamikazeControl__',
 '0054EA70':'T_DynamicVectorClass_PAUKamikazeControl__','005B3970':'MissionClass'}

img = F.Image(EXE)
text = F.Text(img)
atlas = F.load_atlas()
starts = sorted(atlas)
sizes = [atlas[s] for s in starts]
tabs = F.enumerate_tables(img)
stop = set(tabs)
for vt in tabs:
    tabs[vt]['n_slots'] = F.table_len(img, vt, stop)
# install sites per table
installs = {}
for vt in tabs:
    if text.stores.get(vt):
        installs[vt] = list(text.stores[vt])
# entry -> [(vt,slot)]
import collections
holdings = collections.defaultdict(list)
for vt, t in tabs.items():
    for k in range(t['n_slots']):
        v = img.u32(vt + k * 4)
        if v is None or not (F.TEXT_LO <= v < F.TEXT_HI):
            continue
        holdings[v].append((vt, k))

def host_of(site):
    i = bisect.bisect_right(starts, site) - 1
    if i >= 0 and starts[i] <= site < starts[i] + sizes[i]:
        return starts[i]
    return None

def ext_sites(e_int, vt):
    sz = atlas.get(e_int)
    body = (e_int, e_int + sz) if sz else None
    out = []
    for s, _d in installs.get(vt, []):
        if body and body[0] <= s < body[1]:
            continue
        out.append(s)
    return out

def inst_text(site):
    return text.installs_insn.get(site, '?')

recs = []
for e in B2:
    ei = int(e, 16)
    nc = NAMES[e]
    holds = holdings.get(ei, [])
    cand = []
    for vt, k in holds:
        t = tabs[vt]
        mg = t['cls']
        exact = (mg == '.?AV%s@@' % nc)
        match = exact or F.col_match_of(nc, mg)
        col = t['col']
        coff = img.u32(col + 4)
        td = img.u32(col + 12)
        extern = ext_sites(ei, vt)
        cand.append(dict(vt='%08X' % vt, slot=k, cls=mg, exact=exact, match=bool(match),
                         col='%08X' % col, coff=coff, td=('%08X' % td) if td else None,
                         live=bool(installs.get(vt)), ext=len(extern),
                         ext_site=('%08X' % extern[0]) if extern else None,
                         ext_insn=inst_text(extern[0]) if extern else None,
                         ext_host=('%08X' % host_of(extern[0])) if extern and host_of(extern[0]) else None,
                         insts=[('%08X' % s) for s, _ in installs.get(vt, [])]))
    # authoritative final.tsv decisive table
    fin = None
    with io.open(os.path.join(PROBE, 'final.tsv'), encoding='utf-8-sig') as f:
        for ln in f:
            c = ln.rstrip('\r\n').split('\t')
            if c and c[0] == e:
                fin = dict(vt=c[5], slot=c[6], site=c[7], note=c[9]); break
    recs.append(dict(entry=e, name_cls=nc, final=fin, holds=cand))

io.open(os.path.join(HERE, 'classfix_scan.json'), 'w', encoding='utf-8').write(
    json.dumps(dict(exe_sha=F.sha256(EXE), tables=len(tabs),
                    slots=sum(t['n_slots'] for t in tabs.values()), recs=recs),
               ensure_ascii=False, indent=1))
print("wrote classfix_scan.json  tables=%d slots=%d" % (len(tabs), sum(t['n_slots'] for t in tabs.values())))
for r in recs:
    print("\n%s  name_cls=%s  final: vt=%s slot=%s site=%s [%s]" % (
        r['entry'], r['name_cls'], r['final']['vt'], r['final']['slot'],
        r['final']['site'], r['final']['note']))
    for c in sorted(r['holds'], key=lambda x: (x['vt'])):
        print("   vt=%s s=%-4s cl=%-58s exact=%s match=%s coff=%s live=%s ext=%d site=%s ins=%s host=%s" % (
            c['vt'], c['slot'], c['cls'], c['exact'], c['match'], c['coff'],
            c['live'], c['ext'], c['ext_site'], c['ext_insn'], c['ext_host']))
