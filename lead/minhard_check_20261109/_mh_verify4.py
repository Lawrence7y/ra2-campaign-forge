import os
ROOT=r'D:\Project\ra2-campaign-forge'
def L(rel): return open(os.path.join(ROOT,rel.replace('/',os.sep)),'rb').read().decode('utf-8').split('\n')

print('=== _lb2_TEMPLATE.md :113-195 (all 5 body slots) ===')
for i,l in enumerate(L('lead/ledger_bound_20261109/_lb2_TEMPLATE.md'),1):
    if 113<=i<=195: print(f'  :{i}: '+l[:240])
print()
print('=== _lb_BOUND_VOLUME.md §607 chapter wrapper :110-135 ===')
for i,l in enumerate(L('lead/ledger_bound_20261109/_lb_BOUND_VOLUME.md'),1):
    if 108<=i<=135: print(f'  :{i}: '+l[:240])
print()
print('=== _sa_ATTRIBUTION_S604.md :84-96 (处5 连带 :90) ===')
for i,l in enumerate(L('lead/s604_attribution_20261108/_sa_ATTRIBUTION_S604.md'),1):
    if 84<=i<=96: print(f'  :{i}: '+l[:300])
print()
print('=== ATTRIBUTION:136 == _sa:90 ? ===')
a=L('lead/s604_attribution_20261108/S604_ATTRIBUTION.md')[135]
b=L('lead/s604_attribution_20261108/_sa_ATTRIBUTION_S604.md')[89]
print('A:',a); print('B:',b); print('IDENTICAL=',a==b)
print()
print('=== 处5 exact text in S604_REFSYNC_DRAFT.md :88-96 ===')
for i,l in enumerate(L('lead/s604_refsync_20261109/S604_REFSYNC_DRAFT.md'),1):
    if 88<=i<=96: print(f'  :{i}: '+l[:400])
