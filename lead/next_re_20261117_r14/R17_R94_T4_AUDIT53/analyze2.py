# -*- coding: utf-8 -*-
import csv, io, json
BASE = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
OUT  = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R17_R94_T4_AUDIT53\analysis2.json'
with io.open(BASE + r'\R17_R92_T1_REJUDGE\rejudge1242.tsv', encoding='utf-8', newline='') as f:
    rj = list(csv.DictReader(f, delimiter='\t'))
def B(r): return int(r['bytes'])

# find the two named large files
named = [r for r in rj if 'mesh_imm32' in r['rel'] or 'entry_to_vt' in r['rel']]
named_info = [{'rel':r['rel'],'bytes':B(r),'old':r['old_verdict'],'new':r['new_verdict'],
               'changed':r['changed'],'old_basis':r['old_basis']} for r in named]

# top files by bytes among ALL rejudge, among P2O, among 无法判定->对象
all_sorted = sorted(rj, key=B, reverse=True)
p2o = [r for r in rj if r['old_verdict'].strip()==u'过程输出' and r['new_verdict'].strip()==u'对象抄本']
u2o = [r for r in rj if r['old_verdict'].strip()==u'无法判定' and r['new_verdict'].strip()==u'对象抄本']
o2p = [r for r in rj if r['old_verdict'].strip()==u'对象抄本' and r['new_verdict'].strip()==u'过程输出']
new_obj = [r for r in rj if r['new_verdict'].strip()==u'对象抄本']
old_obj = [r for r in rj if r['old_verdict'].strip()==u'对象抄本']

def top(rs,n=8): return [{'rel':r['rel'],'bytes':B(r),'old':r['old_verdict'],'new':r['new_verdict']} for r in sorted(rs,key=B,reverse=True)[:n]]

res = {
 'named_files': named_info,
 'top_all_rejudge': top(all_sorted,10),
 'p2o_count':len(p2o),'p2o_bytes':sum(map(B,p2o)),'p2o_top':top(p2o,8),
 'u2o_count':len(u2o),'u2o_bytes':sum(map(B,u2o)),'u2o_top':top(u2o,8),
 'o2p_count':len(o2p),'o2p_bytes':sum(map(B,o2p)),
 'new_obj_count':len(new_obj),'new_obj_bytes':sum(map(B,new_obj)),'new_obj_top':top(new_obj,8),
 'old_obj_count':len(old_obj),'old_obj_bytes':sum(map(B,old_obj)),'old_obj_top':top(old_obj,8),
}
# byte delta decomposition
res['delta'] = {
  'new_minus_old_obj_bytes': sum(map(B,new_obj))-sum(map(B,old_obj)),
  'p2o_bytes': sum(map(B,p2o)),
  'u2o_bytes': sum(map(B,u2o)),
  'o2p_bytes': sum(map(B,o2p)),
  'note': 'new-old = p2o + u2o - o2p (files leaving object set via o2p subtract)',
  'check': sum(map(B,p2o))+sum(map(B,u2o))-sum(map(B,o2p)),
}
# o2p top5 pct of each denominator
o2p5 = sum(B(r) for r in sorted(o2p,key=B,reverse=True)[:5])
res['o2p_top5'] = {
  'sum':o2p5,
  'pct_of_o2p': round(100.0*o2p5/sum(map(B,o2p)),2),
  'pct_of_misjudged_21609436': round(100.0*o2p5/21609436,2),
  'pct_of_new_minus_old_delta': round(100.0*o2p5/(sum(map(B,new_obj))-sum(map(B,old_obj))),2),
}
with io.open(OUT,'w',encoding='utf-8') as f: json.dump(res,f,ensure_ascii=False,indent=2)
print('OK',OUT)
