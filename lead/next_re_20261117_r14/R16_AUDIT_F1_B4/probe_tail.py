# -*- coding: utf-8 -*-
"""记录：派生 76 行的第 73-76 行（本批之外的尾巴）、以及 raw hit 与 vt+slot*4 的一致性。"""
import io, os, sys, json
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import verify as V

base76, stages, raw = V.derive_76()
print('S3=%d' % len(base76))
print('derived row 55..76 (entry, name):')
for i, r in enumerate(base76, 1):
    if i >= 55:
        print('  %2d  %s  %s' % (i, r['entry'], r['name']))

d = json.load(io.open(os.path.join(V.HERE, 'verify_out.json'), encoding='utf-8'))
print()
print('raw-hit == vt+slot*4 ?')
allok = True
for r in d['rows']:
    vt = int(r['decl']['vt'], 16)
    slot = r['decl']['slot']
    site_slot_va = vt + slot * 4
    raw_hit = None
    # verify_out 未存 hits；重算
    img = None
    print('  %s vt+%d*4=%08X  C1_raw_hits=%d'
          % (r['entry'], slot, site_slot_va, r['C1']['n_raw_hits']))
