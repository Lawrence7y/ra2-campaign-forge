# -*- coding: utf-8 -*-
"""AUDIT-MARGIN: independent recompute of n / named_L / named_S / proved for S15/S16/S17.
Self-written. Reads only: COVERAGE\coverage.tsv (r14 plate) + W130 function_atlas.tsv.
Caliber (per M4_merge/_audit/a1_core.py + _hygiene/recompute_COMMON_R5F.py):
  named_L  = name non-empty and not startswith 'sub_'
  named_S  = named_L and '::sub_' not in name       (D-38 undecided -> does NOT drop slotN)
  proved   = grade == '[已证]'
  denominator = |coverage ∩ atlas| (uppercase entry match)
Thresholds: ceil(0.90*n) for named_S, ceil(0.50*n) for proved.
"""
import sys, os, math, collections, json

sys.stdout.reconfigure(encoding='utf-8')

R14 = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
COV = os.path.join(R14, "COVERAGE", "coverage.tsv")
ATLAS = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv"
TARGETS = ("S15", "S16", "S17")
OUT = os.path.join(R14, "AUDIT_MARGIN", "work")


def tsv(path):
    with open(path, 'r', encoding='utf-8', newline='') as f:
        txt = f.read()
    lines = txt.split('\n')
    if lines and lines[-1] == '':
        lines = lines[:-1]
    h0 = lines[0].rstrip('\r')
    # QUIRK: coverage.tsv header line is COMMA-separated while data rows are TAB-separated.
    hdr = h0.split(',') if ',' in h0 and '\t' not in h0 else h0.split('\t')
    hdr = [h.strip() for h in hdr]
    rows = [ln.rstrip('\r').split('\t') for ln in lines[1:]]
    return hdr, rows


def main():
    ahdr, arows = tsv(ATLAS)
    atlas = {r[0].strip().upper(): int(r[1]) for r in arows if r}
    chdr, crows = tsv(COV)
    print("atlas rows=%d distinct=%d" % (len(arows), len(atlas)))
    print("coverage rows=%d hdr=%s" % (len(crows), chdr))
    idx = {h: i for i, h in enumerate(chdr)}

    rows = []
    for r in crows:
        if len(r) < 8:
            continue
        e = r[idx['entry']].strip().upper()
        if e not in atlas:
            continue
        s = r[idx['subsystem']].strip()
        if s not in TARGETS:
            continue
        rows.append({
            'entry': e,
            'subsystem': s,
            'name': r[idx['name']],
            'sem': r[idx['one_line_semantics']],
            'grade': r[idx['grade']].strip(),
            'ev': r[idx['evidence_path']],
            'nsrc': r[idx['n_sources']],
            'conflict': r[idx['conflict']],
            'atlas_size': atlas[e],
        })

    def named_L(n):
        return bool(n) and not n.startswith('sub_')

    def named_S(n):
        return named_L(n) and '::sub_' not in n

    res = {}
    for s in TARGETS:
        sub = [x for x in rows if x['subsystem'] == s]
        n = len(sub)
        nl = sum(1 for x in sub if named_L(x['name']))
        ns = sum(1 for x in sub if named_S(x['name']))
        pv = sum(1 for x in sub if x['grade'] == '[已证]')
        th_ns = math.ceil(0.90 * n - 1e-9)
        th_pv = math.ceil(0.50 * n - 1e-9)
        res[s] = dict(n=n, named_L=nl, named_S=ns, proved=pv,
                      th_named=th_ns, th_proved=th_pv,
                      margin_named=ns - th_ns, margin_proved=pv - th_pv,
                      pct_named=round(100.0 * ns / n, 4), pct_proved=round(100.0 * pv / n, 4))
        # grade distribution for the record
        gd = collections.Counter(x['grade'] for x in sub)
        print("\n=== %s ===" % s)
        print("  n=%d  named_L=%d  named_S=%d (%.4f%%)  proved=%d (%.4f%%)"
              % (n, nl, ns, 100.0 * ns / n, pv, 100.0 * pv / n))
        print("  threshold named_S>=%d (90%%), proved>=%d (50%%)" % (th_ns, th_pv))
        print("  margin named_S=%+d proved=%+d" % (ns - th_ns, pv - th_pv))
        print("  grade dist: %s" % dict(gd))

    tot = sum(res[s]['n'] for s in TARGETS)
    print("\nTOTAL domain rows (S15+S16+S17 ∩ atlas) = %d" % tot)

    # duplicate-entry check inside domain
    dup = [e for e, c in collections.Counter(x['entry'] for x in rows).items() if c > 1]
    print("duplicate entries inside domain: %s" % (dup or 'none'))

    with open(os.path.join(OUT, 'recompute.json'), 'w', encoding='utf-8') as f:
        json.dump(res, f, ensure_ascii=False, indent=2)

    # dump domain rows for the fragility pass
    with open(os.path.join(OUT, 'domain_rows.tsv'), 'w', encoding='utf-8', newline='') as f:
        f.write("entry\tsubsystem\tname\tgrade\tevidence_path\tn_sources\tconflict\tone_line_semantics\n")
        for x in sorted(rows, key=lambda y: (y['subsystem'], y['entry'])):
            f.write("%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (
                x['entry'], x['subsystem'], x['name'], x['grade'], x['ev'],
                x['nsrc'], x['conflict'], x['sem']))

    # positive controls (outside domain, known-fragile rows named in the card)
    print("\n=== POSITIVE CONTROLS (outside S15-S17 domain) ===")
    cmap = {r[0].strip().upper(): r for r in crows}
    for e in ('004E2690', '0045A640'):
        r = cmap.get(e)
        if r:
            print("%s  sub=%s grade=%s name=%s\n   sem=%s\n   ev=%s"
                  % (e, r[idx['subsystem']], r[idx['grade']], r[idx['name']],
                     r[idx['one_line_semantics']], r[idx['evidence_path']]))


if __name__ == '__main__':
    main()
