import os, hashlib
ROOT=r'D:\Project\ra2-campaign-forge'
rels=['lead/ledger_bound_20261109/LEDGER_BOUND_VOLUME.md',
      'lead/ledger_bound_20261109/_lb_BOUND_VOLUME.md',
      'lead/ledger_bound_20261109/_lb2_TEMPLATE.md',
      'lead/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md',
      'lead/ledger_appendix_20261108/_lad_tpl.md',
      'lead/ledger_appendix_20261108/_la_draft3_s604_gapdiff.md',
      'lead/s604_verdict_entry_20261109/S604_VERDICT_ENTRY_DRAFT.md',
      'lead/s604_verdict_entry_20261109/_ve_DRAFT_S609.md']
KEYS=['## §607','## §609','逐字转录开始','逐字转录结束','整段复制','整段追加','不是台账','不入台账',
      '边界（如实）','不能定位当年错误步骤','只能判「不可复现』','三选一','确切错误机理无法归属','__DRAFT3__','__DRAFT5__']
for rel in rels:
    p=os.path.join(ROOT,rel.replace('/',os.sep))
    b=open(p,'rb').read()
    lines=b.decode('utf-8').split('\n')
    print('####',rel,'bytes=',len(b),'lines=',len(lines))
    for i,l in enumerate(lines,1):
        if any(k in l for k in KEYS):
            print(f'  :{i}: '+l[:400])
    print()

# Exact byte-identical check of the three "boundary sentence" lines
print('=== verbatim identical check for the 3 known lines ===')
def line(rel,n):
    p=os.path.join(ROOT,rel.replace('/',os.sep))
    return open(p,'rb').read().decode('utf-8').split('\n')[n-1]
pairs=[('lead/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md',123,'lead/ledger_appendix_20261108/_la_draft3_s604_gapdiff.md',25),
       ('lead/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md',215,'lead/ledger_appendix_20261108/_lad_tpl.md',151)]
for a,na,bp,nb in pairs:
    x,y=line(a,na),line(bp,nb)
    print(f'{a}:{na} == {bp}:{nb} ? {x==y}')
    print('  A:',x)
    print('  B:',y)
