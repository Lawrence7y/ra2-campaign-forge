#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verify jump-table paths for the two ③b① rows. Reads table entries from exe,
checks every target is in-text and within the row body (each path verifiable)."""
import os, csv
import s09lib8 as L

R14 = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
EV = os.path.join(R14, 'S09_KPROVED8', 'EVIDENCE')

# (entry, table_va, n_entries, index_map_desc, body_lo, body_hi)
TABLES = [
 ('00488980', 0x488EC0, 5, 'direct index eax (cmp eax,4; ja default)', 0x488980, 0x488EB0),
 ('006539D0', 0x653EFC, None, 'indirect: dl=[eax+0x653F04], eax=[esi-1] in 0..0x47', 0x6539D0, 0x653EFA),
]

def main():
    # byte map table for 006539D0: values 0..? at 0x653F04
    out = []
    for e, tva, n, desc, lo, hi in TABLES:
        lines = ['=== %s jump table @%08X ===' % (e, tva), 'index: %s' % desc,
                 'body=[%08X,%08X)' % (lo, hi)]
        if e == '006539D0':
            # determine distinct byte values in map table (index 0..0x47)
            vals = []
            for i in range(0x48):
                v = L.u8(0x653F04 + i)
                vals.append(v)
            distinct = sorted(set(vals))
            lines.append('map table @653F04[0..0x47]: %d distinct dispatch ids %s' % (len(distinct), distinct))
            n_entries = max(distinct) + 1
            lines.append('dispatch table size = max_id+1 = %d' % n_entries)
            for i in range(n_entries):
                t = L.u32(tva + 4*i)
                inb = lo <= t < hi
                lines.append('  [%02d] -> %08X in_body=%s in_text=%s' % (i, t or 0, inb, L.is_text(t)))
        else:
            for i in range(n):
                t = L.u32(tva + 4*i)
                inb = lo <= t < hi
                lines.append('  [%d] -> %08X in_body=%s in_text=%s' % (i, t or 0, inb, L.is_text(t)))
        with open(os.path.join(EV, 'JUMPTABLE_%s.txt' % e), 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines) + '\n')
        print('\n'.join(lines))
        print()

if __name__ == '__main__':
    main()
