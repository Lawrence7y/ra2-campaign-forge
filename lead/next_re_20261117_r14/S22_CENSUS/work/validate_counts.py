import sys, json, collections
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from pathlib import Path
OUT=Path(r'D:/Project/ra2-campaign-forge/lead/next_re_20261117_r14/S22_CENSUS')
cnt=json.load(open(OUT/'EVIDENCE/counts.json',encoding='utf-8'))
print('COUNTS',json.dumps({k:cnt[k] for k in ['S22_TOTAL','ANCHORED','UNANCHORED','A1','A2','A3','A4','TD','COL','vtable_tables','vtable_slots','migration_suggested']},ensure_ascii=False))
for f in ['SUMMARY.md','PROGRESS.md','CENSUS.tsv','EVIDENCE/A4_samples.tsv']:
 print(f,sum(1 for _ in open(OUT/f,encoding='utf-8')))
s=(OUT/'SUMMARY.md').read_text(encoding='utf-8').split('\n')
print('SCAN',s[3][:260])
print('LAST',s[-2][:260])
