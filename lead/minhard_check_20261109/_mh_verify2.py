import os, hashlib
ROOT=r'D:\Project\ra2-campaign-forge'
def L(rel): return open(os.path.join(ROOT,rel.replace('/',os.sep)),'rb').read().decode('utf-8').split('\n')
def sh(s): return hashlib.sha256(s.encode('utf-8')).hexdigest()

# §607 body candidates from source drafts
s_la = '\n'.join(L('lead/ledger_appendix_20261108/_la_draft3_s604_gapdiff.md')[12:26])  # :13-26
s_led= '\n'.join(L('lead/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md')[110:124])  # :111-124
print('source §607 body sha', sh(s_la), 'chars', len(s_la), 'LEDGER==_la?', s_led==s_la)

# bound volume §607 body: heading line to line before next '## §'
for rel in ['lead/ledger_bound_20261109/LEDGER_BOUND_VOLUME.md','lead/ledger_bound_20261109/_lb_BOUND_VOLUME.md']:
    ls=L(rel)
    st=None
    for i,l in enumerate(ls,1):
        if l.startswith('## §607'): st=i; break
    en=None
    for i in range(st+1,len(ls)+1):
        if ls[i-1].startswith('## §'):
            en=i-1; break
    body='\n'.join(ls[st-1:en])
    # strip trailing blank lines for structure comparison
    print('####',rel,'§607 heading@',st,'next heading after@',en,'body chars',len(body),'sha',sh(body))
    print('  contains source body verbatim?', s_la in body)
    # compare line-by-line ignoring trailing blank lines
    a=s_la.split('\n'); b=body.split('\n')
    print('  src lines',len(a),'bound lines',len(b))
    for i,(x,y) in enumerate(zip(a,b),1):
        if x!=y: print('  DIFF at body line',i,'src:',x[:150],'| bound:',y[:150])
    if len(a)!=len(b):
        print('  length mismatch; extra bound lines:',[x[:100] for x in b[len(a):]][:6])

print()
print('=== _la_draft3 copy markers ===')
for i,l in enumerate(L('lead/ledger_appendix_20261108/_la_draft3_s604_gapdiff.md'),1):
    if i<=32: print(f'  :{i}: '+l[:250])
print()
print('=== _lad_tpl.md §6.3 area :140-158 ===')
for i,l in enumerate(L('lead/ledger_appendix_20261108/_lad_tpl.md'),1):
    if 140<=i<=160: print(f'  :{i}: '+l[:250])
print()
print('=== refsync draft 处8/处9 table ===')
for i,l in enumerate(L('lead/s604_refsync_20261109/S604_REFSYNC_DRAFT.md'),1):
    if 54<=i<=74: print(f'  :{i}: '+l[:300])
