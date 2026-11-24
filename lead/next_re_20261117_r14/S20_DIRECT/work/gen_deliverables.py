#!/usr/bin/env python3
import os,sys,io,json
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8',errors='replace')
ROOT=r"D:\Project\ra2-campaign-forge";OUT=os.path.join(ROOT,"lead","next_re_20261117_r14","S20_DIRECT")
WK=os.path.join(OUT,"work");EV=os.path.join(OUT,"EVIDENCE")
V=json.load(open(os.path.join(EV,'verify_direct.json'),encoding='utf-8'))
virt=json.load(open(os.path.join(EV,'virtual_reachable_rows.json'),encoding='utf-8'))
ver=V['verified']
# site detail (call instr = 5 bytes E8 rel32)
with open(os.path.join(EV,'direct_call_sites_clean.tsv'),'w',encoding='utf-8',newline='\n') as f:
    f.write('entry\tgrade_old\tname\tsite\tbytes\traw_rel32\tcomputed_target\texpected_target\tis_call\tcaller_owner\tcaller_owner_grade\tself_loop\tOK\n')
    for rec in ver:
        for s in rec['sites']:
            f.write('\t'.join([rec['entry'],rec['grade_old'],rec['name'],s['site'],s['bytes'],
                str(s['rel']),s['target'],rec['entry'],str(s['callok']).lower(),str(s.get('owner') or ''),
                s.get('owner_grade',''),str(s['selfloop']).lower(),str(s['ok']).lower()])+'\n')
print('direct_call_sites_clean.tsv written')
with open(os.path.join(OUT,'VIRTUAL_SKIPPED.tsv'),'w',encoding='utf-8',newline='\n') as f:
    f.write('entry\tname\tone_line_semantics\tgrade\tevidence_path\trdata_dword_refs\t环123(盘上既有)\t环4状态\t本卡处置\n')
    for v in virt:
        ring123=(f"盘上{v['grade']}: entry在atlas(环1); name来自vt/rdata(环2); "
                 f"semantics={v['sem']}(环3)")
        f.write('\t'.join([v['entry'],v['name'],v['sem'],v['grade'],
            'EVIDENCE/analysis_full.json;EVIDENCE/virtual_reachable_rows.json',
            f"{v['nvrefs']}@{','.join(v['vrefs'][:4])}",ring123,
            '无direct call(全.text E8边界扫0命中),仅虚表可达','保留原grade,不升格'])+'\n')
print('VIRTUAL_SKIPPED.tsv:',len(virt),'rows')
summary=dict(direct_rows=11,virtual_skipped=len(virt),
             sites_total=sum(len(r['sites']) for r in ver),
             sites_ok=sum(1 for r in ver for s in r['sites'] if s['ok']),
             entries=[d.split('\t')[0] for d in open(os.path.join(OUT,'coverage_delta.tsv'),encoding='utf-8').read().splitlines()[1:]])
json.dump(summary,open(os.path.join(EV,'summary.json'),'w',encoding='utf-8'),indent=2)
print('summary:',json.dumps(summary,ensure_ascii=False))
