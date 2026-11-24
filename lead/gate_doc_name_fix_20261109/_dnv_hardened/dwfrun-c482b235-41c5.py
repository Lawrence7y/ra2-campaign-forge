import json,pathlib,re,hashlib
root=pathlib.Path('D:/Project/ra2-campaign-forge')
wd=pathlib.Path('D:/Project/ra2-campaign-forge/lead/gate_doc_name_fix_20261109/_dnv_sandbox36/matrix_reach_20261109')
P=[];NB=0;DOC=None;B=0
DOC=wd/'MATRIX_DEFECT_REACHABILITY.md';SHA='MISSING'
if not DOC.is_file(): P.append('主件缺失 MATRIX_DEFECT_REACHABILITY.md（写域='+wd.name+'）')
else:
 raw=DOC.read_bytes();NB=len(raw);SHA=hashlib.sha256(raw).hexdigest()
 t=raw.decode('utf-8',errors='replace')
 for s in ['## 1','## 2','## 3','## 4','## 5']:
  if s not in t: P.append('缺小节 '+s)
 for k in ['W1','W2','O1','O2','W3','可达','不可达','实跑输出','触发条件','已实证','未验','未改任何文件']:
  if k not in t: P.append('缺要素 '+k)
 for bad in ['已改矩阵','已收紧','应改为','建议修改矩阵']:
  if bad in t: P.append('含越界断言 '+bad)
 B=len(re.findall(r'被核对象 SHA256 = [0-9a-fA-F]{64}',t))
 if B<1: P.append('缺规范格式绑定行')
PRE_C='ca23c116064b25a61d6072f93458673990b0bf766b2430524f1980addd3c76d2'
PRE_MAT='1d4ccc937cfa78f1ac5144c15fd3e87152e45d41565bf5031bde53202667e016'
PRE_M='517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636'
PRE_H='3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7'
PRE_G='2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede'
for lbl,rel,pre in [('候选','lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py',PRE_C),('乙矩阵','lead/b2b_design_20261106/STATE_MATRIX.json',PRE_MAT),('母本','out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py',PRE_M),('台账','lead/PENDING_DECISIONS.md',PRE_H),('目标台账','lead/GOAL_THREE_TARGETS_20261018.md',PRE_G)]:
 p=root/rel
 cur=hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else 'MISSING'
 if cur!=pre: P.append(lbl+' 被改动 pre='+pre[:12]+' cur='+cur[:12])
print(json.dumps({'ok':not P,'problems':P,'docSha256':SHA,'bindings':B,'docBytes':NB,'doc':(DOC.name if DOC else '')},ensure_ascii=False))
