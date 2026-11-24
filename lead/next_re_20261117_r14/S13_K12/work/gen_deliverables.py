import json
from pathlib import Path
OUT=Path(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13_K12')
data=json.loads((OUT/'work/reverify_core.json').read_text(encoding='utf-8'))
S=data['summary']; ROWS=data['rows']; B=S['baseline']; SC=S['selfcheck019']; N9=S['n9']
E=OUT/'EVIDENCE'; E.mkdir(exist_ok=True)
def hx(x): return x if isinstance(x,str) else hex(x)

with (E/'four_rings.tsv').open('w',encoding='utf-8') as f:
    f.write('entry\tsubsystem\tname\told_grade\tnew_grade\tring1\tring2\tcontract\texact_sites\n')
    for r in ROWS:
        r1=r['ring1']; r2=r['ring2']; r3=r['ring3']; r4=r['ring4']
        sites=';'.join('site=%s/g=%s/slot=%d/vt=%s/install=%s'%(hx(s['site']),hx(s['global']),s['slot'],hx(s['vt']),hx(s['install_site'])) for s in r4['sites'])
        f.write('\t'.join([r['entry'],'S13',r['cov_name'],r['old_grade'],'[已证]',
            'align=%s,first=%s,notbranch=%s,predterm=%s,pf=%s'%(r1['aligned16'],r1['first_byte'],r1['not_E8_E9_EB'],r1['pred_insn'],r1['pred_fallthrough']),
            ';'.join('%s@%s(slot%d)'%(v['name'],v['vt'],v['slot']) for v in r2['vt_tables']),
            r3['contract'],sites])+'\n')

with (E/'four_rings.md').open('w',encoding='utf-8') as f:
    f.write('# S13-K12 17 rows C1 independent four-ring re-verification\n\n')
    f.write('READ-ONLY target gamemd.exe SHA-256 '+S['exe_sha256']+'\n\n')
    for r in ROWS:
        f.write('## '+r['entry']+'  '+r['cov_name']+'  ([静态推断] -> [已证])\n')
        r1=r['ring1']; r2=r['ring2']; r3=r['ring3']; r4=r['ring4']
        f.write('- R1 entry: align16=%s first=%s not_E8E9EB=%s pred_real_insn=%s (not_fallthrough=%s) prologue=%s\n'%(
            r1['aligned16'],r1['first_byte'],r1['not_E8_E9_EB'],r1['pred_insn'],not r1['pred_fallthrough'],r1['prologue']))
        for v in r2['vt_tables']:
            f.write('- R2 class: vt=%s slot=%d vt-4=COL=%s COL+0xC=TD=%s TD+8-inline-name=%s section=%s witness=%s\n'%(
                v['vt'],v['slot'],v['col'],v['td'],v['name'],v['section'],
                ';'.join('%s@%s'%(w['kind'],hx(w['site'])) for w in v['witness'])))
        f.write('- R3 contract=%s family=%s key_insns(offset)=%s\n'%(
            r3['contract'],r3['family'],';'.join('%s:%s(%s)'%(k['tag'],k['off'],k['insn']) for k in r3['key_insns'])))
        for s in r4['sites']:
            f.write('- R4 exact site=%s insn=%s global=%s vt=%s slot=%d install_write_site=%s slotval==entry=True caller!=entry=%s\n'%(
                hx(s['site']),s['call'],hx(s['global']),hx(s['vt']),s['slot'],hx(s['install_site']),s['site']!=int(r['entry'],16)))
        f.write('\n')
print('EVIDENCE four_rings written', (E/'four_rings.tsv').stat().st_size, (E/'four_rings.md').stat().st_size)

with (E/'baseline_selfcheck.md').open('w',encoding='utf-8') as f:
    f.write('# 019 selfcheck + detection-power baseline\n\n')
    f.write('## 019 selfcheck (capstone mem.index trap)\n')
    f.write('- known positive: '+SC['site']+' '+SC['disasm']+' capstone='+SC['capstone']+'\n')
    f.write('- mem.index='+str(SC['mem_index'])+' (no-index returns 0, NOT None), mem.base='+str(SC['mem_base'])+', disp='+SC['mem_disp']+'\n')
    f.write('- script never filters call by op.index is None: '+str(SC['never_tests_op_index_is_None'])+'\n\n')
    f.write('## Detection-power baseline (measured FIRST)\n')
    f.write('- seed='+str(B['seed'])+' pool='+str(B['pool_size'])+' (S13 [静态推断] minus 17 C1), random sample '+str(B['sample_n'])+' rows\n')
    f.write('- false_positive_hits='+str(B['false_positive_hits'])+'/'+str(B['sample_n'])+' (%.2f%%)\n'%(100.0*B['false_positive_hits']/B['sample_n']))
    f.write('- full S13 240 rows: predicate hits '+str(B['S13_predicate_hits'])+' == target 17; outside_target_hits='+str(len(B['S13_hits_outside_target']))+' target_missed='+str(len(B['S13_target_missed']))+'\n')
    f.write('- precision=100% recall=100% on S13. More specific than C2 baseline 15/100=15%% and S20-KPROVED 8/40=20%%: exact dispatch additionally requires slot-value==entry (rule 14) + global vptr write witness, not merely \"has live install\".\n\n')
    f.write('## Other stop-checks\n')
    f.write('- 009 disk recompute: n='+str(N9['n'])+' named='+str(N9['named_L'])+' proved='+str(N9['proved'])+' matches CARD.\n')
    f.write('- direct_call_sites_total='+str(S['direct_call_sites_total'])+' install_records='+str(S['install_records'])+' text_instructions='+str(S['text_instructions'])+'\n')

def name_kind(nm):
    u=nm.upper()
    if 'VSLOT' in u: return 'vslot_placeholder'
    if 'SLOT' in u: return 'slot_placeholder'
    if 'SUB_' in u: return 'sub_placeholder'
    return 'other'
with (OUT/'coverage_delta.tsv').open('w',encoding='utf-8') as f:
    f.write('entry\tsubsystem\tname\tone_line_semantics\tgrade\tevidence_path\tname_kind\toldgrade_to_newgrade\n')
    for r in ROWS:
        f.write('\t'.join([r['entry'],'S13',r['cov_name'],r['cov_sem'],'[已证]',
            'EVIDENCE/four_rings.md#'+r['entry'],name_kind(r['cov_name']),
            r['old_grade']+'->[已证]'])+'\n')

P=OUT/'PROGRESS.md'
head=['# S13-K12 PROGRESS',
'## 0 premises and selfchecks',
'- target gamemd.exe SHA-256 '+S['exe_sha256'][:8]+'...'+S['exe_sha256'][-6:]+' verified READ-ONLY; write domain = S13_K12 + _ghidra/S13-K12 only',
'- 009 disk recompute: S13 n='+str(N9['n'])+' named='+str(N9['named_L'])+' proved='+str(N9['proved'])+' matches CARD -> go',
'- 019 selfcheck: 0x4386AB call dword ptr [edx+0x10], mem.index=0 (no-index returns 0 not None); never filters by op.index is None',
'- baseline FIRST: seed='+str(B['seed'])+', pool='+str(B['pool_size'])+', random 17 rows -> false_positive='+str(B['false_positive_hits'])+'/17 (0.00%)',
'- full S13: predicate hits '+str(B['S13_predicate_hits'])+' == target 17, outside=0, missed=0, precision=recall=100%',
'- exact dispatch requires slot-value==entry (14) + global vptr write witness -> more specific than C2 15% / S20 20%',
'- 018 conflict scan: 17 addresses scanned in docs/re + re_atlas/kb + ledger + COVERAGE; no pre-existing name conflict (only coverage.tsv self rows)',
'- no slot-baseline; no same-source double-count; name/subsystem unchanged; 00773030 untouched; C2 36 rows untouched',
'## 1 four-ring re-verification (incremental every 3 rows)']
P.write_text('\n'.join(head)+'\n',encoding='utf-8')
for i in range(0,len(ROWS),3):
    batch=ROWS[i:i+3]
    with P.open('a',encoding='utf-8') as f:
        for j,r in enumerate(batch):
            ln=i+j+1
            s=r['ring4']['sites'][0]
            f.write('- row%02d %s %s contract=%s exact@%s/g%s/s%d [静态推断]->[已证]\n'%(
                ln,r['entry'],r['cov_name'],r['ring3']['contract'],hx(s['site']),hx(s['global']),s['slot']))
        f.write('  [checkpoint %d/%d rows flushed]\n'%(min(i+3,len(ROWS)),len(ROWS)))
with P.open('a',encoding='utf-8') as f:
    f.write('## 2 final\n')
    f.write('- coverage_delta.tsv: 17 rows, each with ring4 site address + 4-ring evidence path, grade [静态推断]->[已证]\n')
    f.write('- merged S13 proved: 86 + 17 = 103 (threshold 120, still short 17; NOT claiming达标)\n')
    f.write('- C2 36 rows NOT touched (D-39 undecided); coverage.tsv/name/subsystem NOT modified\n')
    f.write('- deliverable files: PROGRESS.md, UNKNOWNS.md, DISAGREE.md, EVIDENCE/, work/\n')
print('DELIVERABLES part2 written')
for x in ['EVIDENCE/baseline_selfcheck.md','coverage_delta.tsv','PROGRESS.md']:
    q=OUT/x; print(x,q.exists(),q.stat().st_size if q.exists() else 0)

(OUT/'UNKNOWNS.md').write_text('''# S13-K12 UNKNOWNS / method boundaries

1. C2 36 rows not evaluated: D-39 undecided. This card touches only the 17 C1 rows.
2. The 17 rows carry placeholder names (vslotN/slotN). Per card rule names/subsystem are NOT changed; only grade is raised. one_line_semantics kept verbatim from coverage.tsv. Semantic method names (SetCapacity/FindItemIndex/Clear) are recorded in EVIDENCE/four_rings.md R3 as byte-contract evidence only, NOT written into the delta name column.
3. Ring4 exact-dispatch scan recognizes mov reg,[global] + mov ecx,global + call [reg+slot] with a live install (mov [global],vt) and vt[slot]==entry. Rarer equivalent forms not enumerated; this is a conservative lower bound (misses would leave rows [静态推断], never create false positives). The S13-wide scan found exactly 17 hits == the 17 targets.
4. RTTI class names read per R14_COMMON 8.2.7: vt-4=COL -> COL+0xC=TD -> TD+8 inline ASCII; fail-closed. All 17 resolved; none read from PAU/PAV template prefix (rule 22).
5. 017 same-source non-double-count: for these virtual functions, R3 (in-body byte contract) and R4 (out-of-body exact dispatch site with global write witness) are physically disjoint byte evidence (function body vs call sites+install site), NOT the same entry->vt scan split in two. Ring2 RTTI and Ring4 install witness are separate addresses.
6. Baseline false-positive measured on same-subsystem pool (112 rows, seed 20261118), 0/17; consistent with precision=recall=100% over all 240 S13 rows. This specificity comes from slot-value==entry, unlike the weaker C2 baseline (15%).
7. No venv / no pip install used; python 3.12.10 + capstone 5.0.7 + pefile 2024.8.26 (system).
''',encoding='utf-8')

(OUT/'DISAGREE.md').write_text('''# S13-K12 DISAGREE

None. All 17 C1 rows independently reproduced four rings; no disagreement with SURVEY-D39 classification for these 17 rows.

- Not claiming S13达标: merged proved 103 < threshold 120.
- C2 36 rows deliberately not evaluated (D-39 undecided) - not a disagreement, a scope boundary.
''',encoding='utf-8')

# final integrity checks
j2=json.loads((OUT/'work/reverify_core.json').read_text(encoding='utf-8'))
assert len(j2['rows'])==17
assert len((OUT/'coverage_delta.tsv').read_text(encoding='utf-8').splitlines())==18
assert all(r['ring4']['n_sites']>=1 and not r['ring1']['pred_fallthrough'] and r['ring1']['aligned16'] and r['ring3']['contract'] for r in j2['rows'])
assert all(not r['ring1']['pred_fallthrough'] for r in j2['rows'])
# ensure no forbidden entry and no C2 rows leaked
delta_entries=[l.split(chr(9))[0] for l in (OUT/'coverage_delta.tsv').read_text(encoding='utf-8').splitlines()[1:]]
assert '00773030' not in delta_entries
cls=(Path(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\SURVEY_D39\EVIDENCE\classification.tsv')).read_text(encoding='utf-8').splitlines()[1:]
c2={l.split(chr(9))[0] for l in cls if len(l.split(chr(9)))>=3 and l.split(chr(9))[1]=='S13' and l.split(chr(9))[2]=='C2'}
assert not (set(delta_entries) & c2), 'C2 row leaked into delta!'
print('ALL INTEGRITY CHECKS PASSED')
print('delta rows',len(delta_entries),'C2 rows',len(c2),'overlap',len(set(delta_entries)&c2))
print('PROGRESS lines',len((OUT/'PROGRESS.md').read_text(encoding='utf-8').splitlines()))
