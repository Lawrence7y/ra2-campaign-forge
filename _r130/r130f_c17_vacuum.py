#!/usr/bin/env python3
# R130 r130f: is C17 currently vacuuming? (attacking the gate, not the binary)
#
# R129 reported "C17 self-produced-line anachrony: checked=0 impossible=0".
# R129's ruling emptied C17_PIN, so impossible=0 was expected. But checked=0 is a
# DIFFERENT fact and was not explained: C17 only examines rows whose column 7 claims
# "yes" AND whose product file exists AND which carry a parseable DISC_RECHECK line.
# If the real products carry no such line at all, C17 scans nothing, and its two
# assertion sets (C17a, C17b) are compared against fixtures rather than against reality.
#
# This script measures, for every column-7 "yes" row of the CURRENT table:
#   - does the product file exist?
#   - how many DISC_RECHECK lines does it carry, for this discipline id?
# and separately reports where DISC_RECHECK machinery actually lives on disk.
#
# Controls:
#   PC1: the R94 fixtures DO contain DISC_RECHECK lines -> the scanner is not broken.
#   NC1: a synthetic line with the right shape but a wrong round is counted as a line
#        (proves the counter counts lines, not just files).
#   NC2: asking for a discipline id that exists nowhere yields 0 (proves per-id filter).
# Memory: pure text scan, bounded.
import io
import json
import os
import re
import sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead/next_re_20261117_r14')
TSV = os.path.join(R14, 'DISC_RECHECK.tsv')
OUT = os.path.join(ROOT, '_r130/r130f_c17_vacuum.json')

LINE = re.compile(r'^DISC_RECHECK discipline=(\d+) round=(R\d+) at=(\S+) '
                  r'anchors=(sha256:[0-9a-f]{64}) conclusion=(\S+?)\r?$')


def count_lines(path, did):
    n = 0
    if not os.path.isfile(path):
        return 0
    for ln in io.open(path, encoding='utf-8', errors='replace'):
        m = LINE.match(ln.rstrip('\n'))
        if m and int(m.group(1)) == did:
            n += 1
    return n


def main():
    rows = [l.rstrip('\n').split('\t') for l in io.open(TSV, encoding='utf-8')]
    body = [r for r in rows[1:] if r and r[0].strip().isdigit()]
    yes = [r for r in body if r[6].strip().startswith('有')]

    per = []
    for r in yes:
        did = int(r[0])
        rel = r[4].strip().replace('\\', '/')
        ap = os.path.join(ROOT, rel)
        per.append({
            'id': did, 'path': rel, 'exists': os.path.isfile(ap),
            'lines_for_id': count_lines(ap, did) if os.path.isfile(ap) else 0,
        })

    total_lines = sum(x['lines_for_id'] for x in per)

    # where the DISC_RECHECK machinery actually lives. NOTE: these fixtures sit under
    # the R14 directory, not the project root (self-error S-202: I resolved them from
    # ROOT and got a false "fixtures carry zero lines").
    fixture_dir = os.path.join(R14, '_r94/_audit/tmp_products')
    fx = []
    if os.path.isdir(fixture_dir):
        for fn in sorted(os.listdir(fixture_dir)):
            p = os.path.join(fixture_dir, fn)
            if not os.path.isfile(p):
                continue
            for ln in io.open(p, encoding='utf-8', errors='replace'):
                if LINE.match(ln.rstrip('\n')):
                    fx.append(fn)
                    break

    # controls
    pc1 = len(fx) > 0
    probe = os.path.join(ROOT, '_r130/_probe_line.txt')
    with io.open(probe, 'w', encoding='utf-8', newline='\n') as f:
        f.write('DISC_RECHECK discipline=99 round=R99 at=2026-11-25T00:00:00 '
                'anchors=sha256:' + 'a' * 64 + ' conclusion=PASS\n')
    nc1 = count_lines(probe, 99) == 1
    nc2 = count_lines(probe, 98) == 0
    os.unlink(probe)

    rec = {
        'rows_claiming_yes': len(yes),
        'product_files_missing': sum(1 for x in per if not x['exists']),
        'total_disc_recheck_lines_in_real_products': total_lines,
        'rows_with_zero_lines': sum(1 for x in per if x['lines_for_id'] == 0),
        'fixture_files_carrying_lines': len(fx),
        'ctl_PC1_fixtures_scanned': pc1,
        'ctl_NC1_line_counted': nc1,
        'ctl_NC2_wrong_id_zero': nc2,
        'c17_is_vacuuming': (len(yes) > 0 and total_lines == 0),
        'per_row': per,
    }
    with io.open(OUT, 'w', encoding='utf-8') as f:
        json.dump(rec, f, ensure_ascii=False, indent=1)

    for k in ('rows_claiming_yes', 'product_files_missing',
              'total_disc_recheck_lines_in_real_products', 'rows_with_zero_lines',
              'fixture_files_carrying_lines', 'ctl_PC1_fixtures_scanned',
              'ctl_NC1_line_counted', 'ctl_NC2_wrong_id_zero',
              'c17_is_vacuuming'):
        print(k, '=', rec[k])
    print('--- per row ---')
    for x in per:
        print(' id', x['id'], 'exists', x['exists'], 'lines', x['lines_for_id'],
              '|', x['path'][:62])
    ok = pc1 and nc1 and nc2
    print('CONTROLS', ok)
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
