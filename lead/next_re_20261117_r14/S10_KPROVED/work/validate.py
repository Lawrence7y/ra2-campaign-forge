import csv,json,hashlib,os,collections,sys
OUT='D:/Project/ra2-campaign-forge/lead/next_re_20261117_r14/S10_KPROVED'; root='D:/Project/ra2-campaign-forge'
fails=[]
core=json.load(open(OUT+'/EVIDENCE/core_numbers.json',encoding='utf-8'))
cls=json.load(open(OUT+'/EVIDENCE/classification.json',encoding='utf-8'))
sel=cls['selected']; d=list(csv.DictReader(open(OUT+'/coverage_delta.tsv',encoding='utf-8',newline=''),delimiter='\t')); d39=list(csv.DictReader(open(OUT+'/D39_CANDIDATES.tsv',encoding='utf-8',newline=''),delimiter='\t'))
if len(d)!=40 or len({r['entry'] for r in d})!=40: fails.append('delta count/unique')
if {r['entry'] for r in d}&{r['entry'] for r in d39}: fails.append('delta/D39 overlap')
cols=['entry','subsystem','name','one_line_semantics','grade','evidence_path','n_sources','conflict']
cov=[dict(zip(cols,l.rstrip('\r\n').split('\t'))) for l in open(root+'/lead/next_re_20261117_r14/COVERAGE/coverage.tsv',encoding='utf-8',errors='replace').read().splitlines()[1:] if l.strip()]
cm={r['entry'].upper():r for r in cov}
if any(cm[r['entry']]['grade']!='[静态推断]' or cm[r['entry']]['name']!=r['name'] or cm[r['entry']]['subsystem']!=r['subsystem'] for r in d): fails.append('delta old grade/name/subsystem mismatch')
if any(r['grade']!='[已证]' or r['旧grade→新grade']!='[静态推断]→[已证]' for r in d): fails.append('delta grade columns')
if any(not os.path.exists(OUT+'/'+r['evidence_path']) for r in d): fails.append('missing proof')
sha=hashlib.sha256(open(root+'/ra2youli/gamemd.exe','rb').read()).hexdigest().upper()
if sha!='73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476': fails.append('target hash')
mem={r['entry'].upper():r['grade'] for r in cov}
for r in d: mem[r['entry']]='[已证]'
atlas=set()
with open(root+'/lead/next_re_20261112_r10/W130_atlas/function_atlas.tsv',encoding='utf-8',errors='replace') as f:
 f.readline(); atlas={l.split('\t')[0].upper() for l in f if l.strip()}
S=[e for e in atlas if e in mem and cm[e]['subsystem'].upper()=='S10']
proved=sum(1 for e in S if mem[e]=='[已证]')
if proved!=117+40: fails.append('final proved')
summary=[]
summary.append('VALIDATION '+('PASS' if not fails else 'FAIL')+' '+(';'.join(fails) if fails else ''))
summary.append('target_sha256='+sha)
summary.append('delta=40 unique=40 d39='+str(len(d39))+' overlap=0')
summary.append('selected_direct='+str(sum(1 for x in sel if x['ring']=='DIRECT'))+' selected_exact='+str(sum(1 for x in sel if x['ring']=='EXACT')))
summary.append('old_grades='+str(dict(collections.Counter(cm[r['entry']]['grade'] for r in d))))
summary.append('baseline_seed='+str(core['baseline_seed'])+' sample='+str(core['baseline_sample'])+' mis='+str(core['baseline_mis']))
summary.append('S10_n='+str(len(S))+' proved_after='+str(proved)+' rate='+str(round(100*proved/len(S),2))+'%')
summary.append('proof_files='+str(sum(1 for r in d if os.path.exists(OUT+'/'+r['evidence_path']))))
open(OUT+'/EVIDENCE/validation.txt','w',encoding='utf-8').write('\n'.join(summary)+'\n')
print('\n'.join(summary))
sys.exit(1 if fails else 0)