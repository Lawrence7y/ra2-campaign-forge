import sys, os, json, hashlib, collections
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from pathlib import Path
OUT=Path(r'D:/Project/ra2-campaign-forge/lead/next_re_20261117_r14/S22_CENSUS')
files=['CENSUS.tsv','SUMMARY.md','PROGRESS.md','EVIDENCE/counts.json','EVIDENCE/scan_manifest.txt','EVIDENCE/rtti_tds.tsv','EVIDENCE/rtti_cols.tsv','EVIDENCE/vtable_slots.tsv','EVIDENCE/channel_hits.tsv','EVIDENCE/class_agg_full.tsv','EVIDENCE/A4_samples.tsv','EVIDENCE/coverage_class_hints.tsv','EVIDENCE/suggested_subsystem_distribution.tsv','work/census.py','work/finalize.py','work/compact_summary.py']
for f in files:
 p=OUT/f
 if not p.exists(): print('MISSING',f); continue
 nlines=sum(1 for _ in open(p,encoding='utf-8',errors='replace'))
 print('%6d  %s'%(nlines,f))
rows=[]
with open(OUT/'CENSUS.tsv',encoding='utf-8') as f:
 hdr=f.readline().rstrip('\n').split('\t')
 for ln in f:
  r=ln.rstrip('\n').split('\t')
  if len(r)==7: rows.append(r)
print('CENSUS_HEADER',hdr)
print('CENSUS_ROWS',len(rows))
print('KINDS',collections.Counter(r[1] for r in rows))
print('SUMMARY_LINES',sum(1 for _ in open(OUT/'SUMMARY.md',encoding='utf-8')))
print('PROGRESS_LINES',sum(1 for _ in open(OUT/'PROGRESS.md',encoding='utf-8')))
print('A4_SAMPLES',sum(1 for _ in open(OUT/'EVIDENCE/A4_samples.tsv',encoding='utf-8'))-1)
cnt=json.load(open(OUT/'EVIDENCE/counts.json',encoding='utf-8'))
print('COUNTS',json.dumps({k:cnt[k] for k in ['S22_TOTAL','ANCHORED','UNANCHORED','A1','A2','A3','A4','TD','COL','vtable_tables','vtable_slots','migration_suggested']},ensure_ascii=False))
exe=Path(r'D:/Project/ra2-campaign-forge/ra2youli/gamemd.exe')
print('EXE_SHA',hashlib.sha256(exe.read_bytes()).hexdigest().upper())
print('DIRS',[p.name for p in OUT.iterdir()])
