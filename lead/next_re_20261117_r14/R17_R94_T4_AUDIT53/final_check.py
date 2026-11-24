# -*- coding: utf-8 -*-
import csv, io
B=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
def rows(p):
    with io.open(B+'\\'+p,encoding='utf-8',newline='') as f: return list(csv.DictReader(f,delimiter='\t'))
tf=rows(r'R17_R88_T1_SEMDEF\tier_final.tsv'); rj=rows(r'R17_R92_T1_REJUDGE\rejudge1242.tsv')
def isp(r): return 'P1a' in (r['why_content'] or '')
manual=set(r['rel'] for r in tf if not isp(r))
oldobj=set(r['rel'] for r in rj if (r['old_verdict'] or '').strip()==u'对象抄本')
p1a=set(r['rel'] for r in tf if isp(r))
allrj=set(r['rel'] for r in rj)
print('manual=',len(manual),'oldobj=',len(oldobj))
print('manual_in_rejudge=',len(manual & allrj))
print('manual_minus_oldobj=',len(manual-oldobj),'oldobj_minus_manual=',len(oldobj-manual))
print('p1a_in_oldobj=',len(p1a & oldobj))
# None why_content rows
nn=[r for r in tf if r['why_content'] is None]
print('why_content_None_rows=',len(nn))
