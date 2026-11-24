"""S10-KPROVED3 step 1: enumerate ② holding tables, ③b (with entry-relative offsets),
and ④ verified direct-call sites for all 41 remaining S10 A rows. Writes analysis.json.
"""
import csv, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import core

HERE = os.path.dirname(os.path.abspath(__file__))
CLS = r'lead\next_re_20261117_r14\SURVEY_RING24\EVIDENCE\classification.tsv'
MERGED = set('004D74E0 004D7D50 004D7170 004D85D0 004DB3C0 004D9960 004DF040 004DB690'.split())

def load_a_rows():
    rows = {}
    with open(CLS, encoding='utf-8') as f:
        for c in csv.DictReader(f, delimiter='\t'):
            if c['subsystem'] == 'S10' and c['has4_strict'] == '1' and c['has2_rtti'] == '1':
                rows[c['entry']] = c
    return rows

def main():
    pe = core.PE()
    print('building RTTI census...')
    vts, emap = core.census_vtables(pe)
    print('  vtables:', len(vts), 'total slots:', sum(v['nslots'] for v in vts))
    print('sweeping 100% .text for E8...')
    targets, n_ins, n_e8 = core.full_text_sweep_calls(pe)
    print('  instructions:', n_ins, 'E8@boundary:', n_e8, 'distinct targets:', len(targets))
    print('  self-check known call 0x4D74E0 sites:', [hex(x) for x in targets.get(0x004D74E0, [])])

    arows = load_a_rows()
    out = []
    for entry in sorted(arows):
        if entry in MERGED:
            continue
        e = int(entry, 16)
        c = arows[entry]
        ext_hi = int(c['ext_hi'], 16)
        holds = emap.get(e, [])
        # ② attribution: collect (vt,slot,name)
        hlist = [dict(vt='%08X' % h['vt'], slot=h['slot'], name=h['name'],
                      col='%08X' % h['col'], td='%08X' % h['td'], byte_off=h['byte_off'])
                 for h in holds]
        # ③b
        strict, coreb, loose, hits, detail = core.detect_3b(pe, e, ext_hi)
        # ④ verified direct sites: E8 boundary + rel32==entry (targets map already guarantees), outside body
        sites = []
        for s in targets.get(e, []):
            outside = not (e <= s < ext_hi)
            if outside:
                sites.append('%08X' % s)
        out.append(dict(entry=entry, name=c['name'], rtti_classes=c['rtti_classes'],
                        rtti_slot=c['rtti_slot'], ext_hi=c['ext_hi'], atlas_size=c['atlas_size'],
                        holds=hlist, n_holds=len(hlist),
                        strict=strict, core=coreb, loose=loose, hits=hits,
                        detail=detail, sites=sites, n_sites=len(sites),
                        n_direct_all=c['n_direct_all'], n_direct_out=c['n_direct_out']))
    json.dump(dict(vtables=len(vts), text_insns=n_ins, e8=n_e8, rows=out),
              open(os.path.join(HERE, 'analysis.json'), 'w'), indent=1)
    # concise table
    print('\nentry\tname\tnholds\tattrib(slot/name)\tstrict/core\tloop/sw/err/guard\toffset\tsites')
    for r in out:
        hs = ';'.join('%s/s%d/%s' % (h['vt'][-4:], h['slot'], h['name'].replace('.?AV','').replace('@@','').replace('?$','')) for h in r['holds'])
        offs = []
        for k in ('switch', 'errcode', 'loop', 'guards'):
            if k in r['detail']:
                offs.append(k + ':' + str(r['detail'][k].get('at', r['detail'][k].get('branch', '?'))))
        print('%s\t%s\t%d\t%s\t%s/%s\t%d/%d/%d/%d\t%s\t%s' % (
            r['entry'], r['name'], r['n_holds'], hs,
            'Y' if r['strict'] else 'n', 'Y' if r['core'] else 'n',
            int(r['hits']['s4_loop']), int(r['hits']['s1_switch']), int(r['hits']['s2_errcode']),
            int(r['hits']['s1b_guards']), ','.join(offs), ','.join(r['sites'])))

if __name__ == '__main__':
    main()
