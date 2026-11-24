"""S10-KPROVED3 own toolkit step 0: extract S10 A-set rows from SURVEY classification.tsv.
Read-only on external data; writes only into this card's work dir.
"""
import csv, json, os

CLS = r'lead\next_re_20261117_r14\SURVEY_RING24\EVIDENCE\classification.tsv'

MERGED = set('004D74E0 004D7D50 004D7170 004D85D0 004DB3C0 004D9960 004DF040 004DB690'.split())

def main():
    rows = []
    with open(CLS, encoding='utf-8') as f:
        r = csv.DictReader(f, delimiter='\t')
        for c in r:
            if c['subsystem'] == 'S10' and c['has4_strict'] == '1' and c['has2_rtti'] == '1':
                rows.append(c)
    rows.sort(key=lambda x: int(x['entry'], 16))
    print('S10 A set (has4_strict=1 & has2_rtti=1) =', len(rows))
    print('entry\tname\trtti_classes\trtti_vt\trtti_slot\tn_direct_out\next_lo\next_hi\tatlas_size\tmerged')
    for c in rows:
        print('\t'.join([c['entry'], c['name'], c['rtti_classes'], c['rtti_vt'], c['rtti_slot'],
                         c['n_direct_out'], c['ext_lo'], c['ext_hi'], c['atlas_size'],
                         'Y' if c['entry'] in MERGED else 'N']))
    remain = [c for c in rows if c['entry'] not in MERGED]
    print('remaining =', len(remain))
    with open(os.path.join(os.path.dirname(__file__), 'a_rows_remaining.json'), 'w') as o:
        json.dump(rows, o, indent=1)

if __name__ == '__main__':
    main()
