import os, hashlib, json
ROOT=r'D:\Project\ra2-campaign-forge'
def L(rel): return open(os.path.join(ROOT,rel.replace('/',os.sep)),'rb').read().decode('utf-8').split('\n')

print('=== 1. 三组硬项：文件去重并集 ===')
GROUPS={
 '① 处8≡处9': [('lead/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md',123),('lead/ledger_appendix_20261108/_la_draft3_s604_gapdiff.md',25)],
 '② #C1≡#C2': [('lead/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md',215),('lead/ledger_appendix_20261108/_lad_tpl.md',151)],
 '③ #A3':     [('lead/s604_attribution_20261108/S604_ATTRIBUTION.md',171)],
}
uniq=[]
for g,items in GROUPS.items():
    print(g)
    for rel,n in items:
        line=L(rel)[n-1]
        print(f'  {rel}:{n}: {line[:200]}')
        if rel not in uniq: uniq.append(rel)
print('UNION_FILES=',len(uniq))
for u in uniq: print('  ',u)

print()
print('=== 2. 逐字同文对验证 ===')
def is_id(a,na,b,nb): return L(a)[na-1]==L(b)[nb-1]
print('处8≡处9 :',is_id('lead/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md',123,'lead/ledger_appendix_20261108/_la_draft3_s604_gapdiff.md',25))
print('#C1≡#C2 :',is_id('lead/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md',215,'lead/ledger_appendix_20261108/_lad_tpl.md',151))
print('处5 连带 ATTRIBUTION:136 ≡ _sa:90 :',is_id('lead/s604_attribution_20261108/S604_ATTRIBUTION.md',136,'lead/s604_attribution_20261108/_sa_ATTRIBUTION_S604.md',90))

print()
print('=== 3. 漏项：与 :123 逐字同文、且位于「整段复制/逐字照抄」块内的下游载体 ===')
target=L('lead/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md')[122]
carriers=[]
for rel in ['lead/ledger_bound_20261109/LEDGER_BOUND_VOLUME.md','lead/ledger_bound_20261109/_lb_BOUND_VOLUME.md','lead/ledger_bound_20261109/_lb2_TEMPLATE.md']:
    ls=L(rel)
    for i,l in enumerate(ls,1):
        if l==target:
            # find nearest preceding copy-start marker
            mk=None
            for j in range(i-1,0,-1):
                if any(k in ls[j-1] for k in ['逐字照抄，从下一行起','逐字转录开始','从这里开始整段复制']):
                    mk=j; break
            print(f'  {rel}:{i} IDENTICAL; nearest copy-start marker = :{mk}')
            carriers.append(rel)
print('CARRIER_FILES=',len(set(carriers)),sorted(set(carriers)))
print('UNION_WITH_CARRIERS=',len(set(uniq)|set(carriers)))
for u in sorted(set(uniq)|set(carriers)): print('  ',u)
print('UNION_WITH_CARRIERS_AND_处5连带=',len(set(uniq)|set(carriers)|{'lead/s604_attribution_20261108/_sa_ATTRIBUTION_S604.md'}))

print()
print('=== 4. 加注 22 点的文件分布：哪些落在「原13 处已触达的 6 件」之外 ===')
covered_orig13=['lead/slowframe_r3_20261108/S604_GAP_RECHECK.md',
 'lead/s604_attribution_20261108/S604_ATTRIBUTION.md',
 'lead/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md',
 'lead/ledger_appendix_20261108/_la_draft3_s604_gapdiff.md',
 'lead/s604_script_gap_20261109/S604_SCRIPT_GAP.md',
 'lead/s604_exclusive_20261109/S604_EXCLUSIVITY.md']
# 22 加注点: #A1,#A2,#A4 (3), #B1-#B5 (5), #D1,#D5 (2), #E1-#E3 (3), #F1,#F2 (2),
# #G1,#G2 (2), #H1 (1), #I1 (1), #J1-#J3 (3) = 22
ann={
 'lead/s604_attribution_20261108/S604_ATTRIBUTION.md':3,
 'lead/s604_attribution_20261108/_sa_ATTRIBUTION_S604.md':5,
 'lead/s604_script_gap_20261109/S604_SCRIPT_GAP.md':2,
 'lead/s604_script_gap_20261109/_sg_FINDINGS.md':3,
 'lead/s604_exclusive_20261109/S604_EXCLUSIVITY.md':2,
 'lead/s604_exclusive_20261109/_ex_EXCLUSIVITY.md':2,
 'lead/slowwindow_n8_20261108/SLOW_WINDOW_LIMITS.md':1,
 'lead/direction_ruling_20261108/RULING_DIRECTION.md':1,
 'lead/direction_ruling_20261108/_dr_RULING.md':3,
}
tot=0; absorbed=0; newfiles=[]
for rel,c in ann.items():
    tot+=c
    if rel in covered_orig13:
        absorbed+=c; print(f'  已触达(零边际) {rel}: {c} 点')
    else:
        newfiles.append(rel); print(f'  ★新开遍 {rel}: {c} 点')
print('本批加注总点=',tot,'落在已触达件=',absorbed,'落在新件=',tot-absorbed,'新件数=',len(newfiles))
print('相对「原13 处 6 件」新增指纹变更 = 新件数 + _lad_tpl(#C2 新件) =',len(newfiles)+1)
print('相对「最小硬项 4 件」新增指纹变更 = 13 - 4 =',13-4)

print()
print('=== 5. 严格交集（13 件内）：IN_BLOCK 且过时 ===')
F13=[k for k in []]
blocks3={'lead/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md':[(46,61),(80,92),(110,125),(149,179)],
         'lead/ledger_appendix_20261108/_la_draft3_s604_gapdiff.md':[(11,28)],
         'lead/ledger_appendix_20261108/_lad_tpl.md':[(46,48),(67,69),(87,89),(113,115)]}
for rel,bs in blocks3.items():
    ls=L(rel)
    for i,l in enumerate(ls,1):
        if '不能定位当年错误步骤' in l or '确切错误机理无法归属' in l or '不可定谳' in l:
            inb=any(a<i<b for a,b in bs)
            print(f'  {rel}:{i} IN_BLOCK={inb} :: {l[:150]}')
print('  → :215/:151 在 §6.3（:211/:147 起），四段逐字转录区块止于 :179/:115 ⇒ OUTSIDE')
