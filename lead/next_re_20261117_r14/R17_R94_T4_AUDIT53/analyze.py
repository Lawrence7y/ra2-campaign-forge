# -*- coding: utf-8 -*-
import csv, collections, json, io
BASE = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
OUT  = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R17_R94_T4_AUDIT53\analysis.json'

def rows(rel):
    with io.open(BASE + '\\' + rel, encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f, delimiter='\t'))

tf   = rows(r'R17_R88_T1_SEMDEF\tier_final.tsv')       # 4518 old tier_final
cp   = rows(r'R17_R78_T1_RECLASS\files_tier_Cprime.tsv')# 18712 C-prime
rj   = rows(r'R17_R92_T1_REJUDGE\rejudge1242.tsv')     # 1242 rejudge

P1a_marker = u'P1a'
def is_p1a(r):
    return P1a_marker in r['why_content']

# --- sets of rel keys ---
rel_tf = set(r['rel'] for r in tf)
rel_cp = set(r['rel'] for r in cp)
rel_rj = set(r['rel'] for r in rj)
cp_bytes = dict((r['rel'], int(r['bytes'])) for r in cp)

p1a = [r for r in tf if is_p1a(r)]
manual = [r for r in tf if not is_p1a(r)]   # "逐件判为对象者" 732
rel_p1a = set(r['rel'] for r in p1a)
rel_manual = set(r['rel'] for r in manual)

res = {}
res['counts'] = {
    'tf_rows': len(tf), 'tf_sum_bytes': sum(int(r['bytes']) for r in tf),
    'cp_rows': len(cp), 'rj_rows': len(rj),
    'p1a_rows': len(p1a), 'p1a_bytes': sum(int(r['bytes']) for r in p1a),
    'manual_rows': len(manual), 'manual_bytes': sum(int(r['bytes']) for r in manual),
    'p1a_plus_manual_rows': len(p1a)+len(manual),
    'p1a_plus_manual_bytes': sum(int(r['bytes']) for r in p1a)+sum(int(r['bytes']) for r in manual),
}
# duplicates within tf?
res['dup_in_tf'] = len(tf) - len(rel_tf)
res['dup_in_cp'] = len(cp) - len(rel_cp)
res['dup_in_rj'] = len(rj) - len(rel_rj)

# Q1: are 732 manual in C-prime? are 3786 p1a in C-prime?
manual_in_cp = rel_manual & rel_cp
p1a_in_cp = rel_p1a & rel_cp
res['Q1'] = {
    'manual_in_Cprime_count': len(manual_in_cp),
    'manual_not_in_Cprime_count': len(rel_manual - rel_cp),
    'p1a_in_Cprime_count': len(p1a_in_cp),
    'p1a_not_in_Cprime_count': len(rel_p1a - rel_cp),
    'tf_in_Cprime_count': len(rel_tf & rel_cp),
    'tf_not_in_Cprime_count': len(rel_tf - rel_cp),
    'oldC_Y_in_manual': sum(1 for r in manual if r['oldC']=='Y'),
    'oldC_N_in_manual': sum(1 for r in manual if r['oldC']=='N'),
    'oldC_Y_in_p1a': sum(1 for r in p1a if r['oldC']=='Y'),
    'oldC_N_in_p1a': sum(1 for r in p1a if r['oldC']=='N'),
}
# new-value cross check: 3786 + 627 = 4413 ; bytes
# derive new object set from rejudge: new_verdict==对象抄本
new_obj = [r for r in rj if r['new_verdict'].strip()==u'对象抄本']
res['Q1']['rejudge_new_obj_count'] = len(new_obj)
res['Q1']['rejudge_new_obj_bytes'] = sum(int(r['bytes']) for r in new_obj)
# old object in rejudge
old_obj = [r for r in rj if r['old_verdict'].strip()==u'对象抄本']
res['Q1']['rejudge_old_obj_count'] = len(old_obj)
res['Q1']['rejudge_old_obj_bytes'] = sum(int(r['bytes']) for r in old_obj)

res['Q1']['new_tf_count_formula'] = 3786 + 627
res['Q1']['new_tf_bytes_formula'] = 714228639 + 29944200
res['Q1']['new_tf_count_sub'] = 4518 - 732 + 627
res['Q1']['new_tf_bytes_sub'] = 724479859 - 10251220 + 29944200

# Q2: among 227 "对象->过程" (old=对象抄本 new=过程输出 changed), top5 bytes
o2p = [r for r in rj if r['old_verdict'].strip()==u'对象抄本' and r['new_verdict'].strip()==u'过程输出']
o2p.sort(key=lambda r:int(r['bytes']), reverse=True)
o2p_total = sum(int(r['bytes']) for r in o2p)
res['Q2'] = {
    'o2p_count': len(o2p),
    'o2p_total_bytes': o2p_total,
    'top5': [{'rel':r['rel'],'bytes':int(r['bytes'])} for r in o2p[:5]],
    'top5_sum': sum(int(r['bytes']) for r in o2p[:5]),
    'top5_pct_of_o2p': round(100.0*sum(int(r['bytes']) for r in o2p[:5])/o2p_total,2) if o2p_total else None,
    'top10_pct_of_o2p': round(100.0*sum(int(r['bytes']) for r in o2p[:10])/o2p_total,2) if o2p_total else None,
    'o2p_all': [{'rel':r['rel'],'bytes':int(r['bytes'])} for r in o2p],
}
# misjudged bytes claimed = 21,609,436 for 260 misjudged (o2p + p2o)
p2o = [r for r in rj if r['old_verdict'].strip()==u'过程输出' and r['new_verdict'].strip()==u'对象抄本']
misjudged = o2p + p2o
res['Q2']['p2o_count']=len(p2o)
res['Q2']['p2o_bytes']=sum(int(r['bytes']) for r in p2o)
res['Q2']['misjudged_total_bytes']=sum(int(r['bytes']) for r in misjudged)
res['Q2']['top5_pct_of_misjudged']=round(100.0*sum(int(r['bytes']) for r in o2p[:5])/sum(int(r['bytes']) for r in misjudged),2)

# Q3: intersection between 627 new objects and 3786 P1a / and 732 manual
# "627 全在 C′ 外、P1a 全在 C′ 内 => 无交集" -- test 627 new obj rels vs p1a rels
rel_new_obj = set(r['rel'] for r in new_obj)
res['Q3'] = {
    'new_obj_3786_p1a_intersection': len(rel_new_obj & rel_p1a),
    'new_obj_in_Cprime_count': len(rel_new_obj & rel_cp),
    'new_obj_not_in_Cprime_count': len(rel_new_obj - rel_cp),
    'intersection_rels': sorted(list(rel_new_obj & rel_p1a))[:20],
    'new_obj_vs_manual732_intersection': len(rel_new_obj & rel_manual),
}
# also: 627 = 505 + 89 + 33 ; where do the 89 and 33 come from - all outside tier_final?
# new_obj rels that were in old tier_final
res['Q3']['new_obj_already_in_old_tf'] = len(rel_new_obj & rel_tf)
# the 505 staying objects came from the 732 manual set (old=对象抄本 among rejudge old obj)
stay = [r for r in rj if r['old_verdict'].strip()==u'对象抄本' and r['new_verdict'].strip()==u'对象抄本']
res['Q3']['stay_obj_count']=len(stay)
res['Q3']['stay_bytes']=sum(int(r['bytes']) for r in stay)

with io.open(OUT,'w',encoding='utf-8') as f:
    json.dump(res,f,ensure_ascii=False,indent=2)
print('OK wrote',OUT)
