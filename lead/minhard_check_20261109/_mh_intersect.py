import os, hashlib
ROOT=r'D:\Project\ra2-campaign-forge'
# 13 files from §4.2 list
F13=[
 'lead/slowframe_r3_20261108/S604_GAP_RECHECK.md',
 'lead/s604_attribution_20261108/S604_ATTRIBUTION.md',
 'lead/s604_attribution_20261108/_sa_ATTRIBUTION_S604.md',
 'lead/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md',
 'lead/ledger_appendix_20261108/_la_draft3_s604_gapdiff.md',
 'lead/ledger_appendix_20261108/_lad_tpl.md',
 'lead/s604_script_gap_20261109/S604_SCRIPT_GAP.md',
 'lead/s604_script_gap_20261109/_sg_FINDINGS.md',
 'lead/s604_exclusive_20261109/S604_EXCLUSIVITY.md',
 'lead/s604_exclusive_20261109/_ex_EXCLUSIVITY.md',
 'lead/slowwindow_n8_20261108/SLOW_WINDOW_LIMITS.md',
 'lead/direction_ruling_20261108/RULING_DIRECTION.md',
 'lead/direction_ruling_20261108/_dr_RULING.md',
]
# additional "bound volume" / verdict-entry files not in the 13
EXTRA=[
 'lead/ledger_bound_20261109/LEDGER_BOUND_VOLUME.md',
 'lead/ledger_bound_20261109/_lb_BOUND_VOLUME.md',
 'lead/ledger_bound_20261109/_lb2_TEMPLATE.md',
 'lead/s604_verdict_entry_20261109/S604_VERDICT_ENTRY_DRAFT.md',
 'lead/s604_verdict_entry_20261109/_ve_DRAFT_S609.md',
 'lead/s604_refsync_20261109/S604_REFSYNC_DRAFT.md',
 'lead/s604_refsync_20261109/_rs_REFSYNC_DRAFT.md',
 'lead/s604_refsync_full_20261109/S604_REFSYNC_FULL.md',
 'lead/s604_refsync_full_20261109/_rf_FULL_REFSYNC_DRAFT.md',
]
# markers that indicate "this text block is meant to be copied verbatim into the permanent ledger"
LEDMARK=['逐字转录开始','逐字转录结束','从这里开始整段复制','草案正文（整段复制','整段复制追加','## §60','## §607','## §609','待 Leader 追加','供 Leader 整段复制追加']
# markers of "已定谳但表述旧" (outdated statements)
OLD=['不能定位当年错误步骤','不能定位错误','不可定谳','确切错误机理无法归属','只能判「不可复现」','语料不存在','确切错误行不可定位','从未落盘','错误步骤和根因未验','原始错误步骤未验','旧生成代码缺失','代码未落盘','无法定谳','无法归属','不可定位']

def classify(rel):
    p=os.path.join(ROOT,rel.replace('/',os.sep))
    if not os.path.exists(p): return None
    b=open(p,'rb').read()
    lines=b.decode('utf-8',errors='replace').split('\n')
    # identify verbatim-copy block line ranges
    blocks=[]
    start=None
    for i,l in enumerate(lines,1):
        if ('逐字转录开始' in l) or ('从这里开始整段复制' in l) or ('草案正文（整段复制' in l):
            start=i
        elif ('逐字转录结束' in l) or ('草案正文结束' in l):
            if start: blocks.append((start,i)); start=None
    if start: blocks.append((start,len(lines)))
    return lines,blocks

def inblock(n,blocks):
    return any(a<n<b for a,b in blocks)

print('=== 13 files: outdated lines inside verbatim-copy blocks ===')
for rel in F13:
    r=classify(rel)
    if r is None: print('MISSING',rel); continue
    lines,blocks=lines,blocks=r
    print('####',rel,'blocks=',blocks)
    for i,l in enumerate(lines,1):
        if any(k in l for k in OLD):
            tag='IN_BLOCK' if inblock(i,blocks) else 'outside'
            print(f'  :{i} [{tag}] '+l[:240])
print()
print('=== EXTRA files: outdated lines inside verbatim-copy blocks ===')
for rel in EXTRA:
    r=classify(rel)
    if r is None: print('MISSING',rel); continue
    lines,blocks=r
    print('####',rel,'blocks=',blocks)
    for i,l in enumerate(lines,1):
        if any(k in l for k in OLD):
            tag='IN_BLOCK' if inblock(i,blocks) else 'outside'
            print(f'  :{i} [{tag}] '+l[:240])
print()
print('=== exact match: §607 boundary sentence (LEDGER:123) anywhere ===')
target=open(os.path.join(ROOT,'lead','ledger_appendix_20261108','LEDGER_APPENDIX_DRAFT.md'),'rb').read().decode('utf-8').split('\n')[122]
for dp,dn,fns in os.walk(os.path.join(ROOT,'lead')):
    for f in fns:
        if not f.endswith('.md'): continue
        p=os.path.join(dp,f)
        try: lines=open(p,'r',encoding='utf-8',errors='replace').read().split('\n')
        except: continue
        for i,l in enumerate(lines,1):
            if l==target:
                print(os.path.relpath(p,ROOT).replace(os.sep,'/')+':'+str(i)+' IDENTICAL')
