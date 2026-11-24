import os, hashlib
ROOT=r'D:\Project\ra2-campaign-forge'
def L(rel): return open(os.path.join(ROOT,rel.replace('/',os.sep)),'rb').read().decode('utf-8').split('\n')

print('=== §609 body in S604_VERDICT_ENTRY_DRAFT.md:66-84 ===')
for i,l in enumerate(L('lead/s604_verdict_entry_20261109/S604_VERDICT_ENTRY_DRAFT.md'),1):
    if 66<=i<=84: print(f'  :{i}: '+l[:330])
print()
print('=== _lb2_TEMPLATE.md placeholders ===')
for i,l in enumerate(L('lead/ledger_bound_20261109/_lb2_TEMPLATE.md'),1):
    if '__DRAFT' in l or '逐字照抄' in l or '## §60' in l:
        print(f'  :{i}: '+l[:250])
print()
print('=== SLOW_WINDOW_LIMITS.md :88-95 and :120-132 ===')
for i,l in enumerate(L('lead/slowwindow_n8_20261108/SLOW_WINDOW_LIMITS.md'),1):
    if 88<=i<=95 or 120<=i<=132: print(f'  :{i}: '+l[:300])
print()
print('=== LEDGER_BOUND_VOLUME.md §607 chapter wrapper :180-215 (copy markers) ===')
for i,l in enumerate(L('lead/ledger_bound_20261109/LEDGER_BOUND_VOLUME.md'),1):
    if 180<=i<=215: print(f'  :{i}: '+l[:250])
