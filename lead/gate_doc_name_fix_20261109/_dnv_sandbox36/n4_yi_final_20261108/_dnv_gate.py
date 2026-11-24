import json,pathlib,re,hashlib
root=pathlib.Path('D:/Project/ra2-campaign-forge')
wd=pathlib.Path('D:/Project/ra2-campaign-forge/lead/gate_doc_name_fix_20261109/_dnv_sandbox36/n4_yi_final_20261108')
P=[];B=[];NB=0;DOC=None
DOC=wd/'CANDIDATE_RESIGN_YES_V2.md';SHA='MISSING'
if not DOC.is_file(): P.append('主件缺失 CANDIDATE_RESIGN_YES_V2.md（写域='+wd.name+'）')
else:
 raw=DOC.read_bytes();NB=len(raw);SHA=hashlib.sha256(raw).hexdigest()
 t=raw.decode('utf-8',errors='replace')
 for s in ['## 1','## 2','## 3','## 4','## 5','## 6']:
  if s not in t: P.append('缺小节 '+s)
 for k in ['逐行','十四行','九 hunk','语义层 YES','甲不再绑定','不签 APPROVE_SCOPE','未验']:
  if k not in t: P.append('缺要素 '+k)
 for bad in ['可应用母本','放行 N-5','已应用','已签 APPROVE_SCOPE']:
  if bad in t: P.append('含越权断言 '+bad)
 rows=len(re.findall(r'^\|\s*(R\d+|\d+)\s*\|',t,re.M))
 if rows<14: P.append('逐行表不足 14 行，实得 '+str(rows))
 hk=len(re.findall(r'H0[1-9]',t))
 if hk<9: P.append('九 hunk 覆盖不足，实得 '+str(hk))
 B=re.findall(r'被核对象 SHA256\s*=\s*`?([0-9a-fA-F]{64})`?',t)
 if not B: P.append('缺 SHA256 绑定行')
PRE_M='517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636'
PRE_C='ca23c116064b25a61d6072f93458673990b0bf766b2430524f1980addd3c76d2'
PRE_V='c7bcf035920234bdc66ec410564b296d4c18b62008dd5653ba76a26a38f10801'
PRE_MAT='1d4ccc937cfa78f1ac5144c15fd3e87152e45d41565bf5031bde53202667e016'
PRE_H='3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7'
PRE_G='2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede'
for lbl,rel,pre in [('母本','out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py',PRE_M),('候选','lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py',PRE_C),('V2正文','lead/n4_yi_final_20261108/_n4v2_B_EXECUTION_SPEC_V2.md',PRE_V),('乙矩阵','lead/b2b_design_20261106/STATE_MATRIX.json',PRE_MAT),('台账','lead/PENDING_DECISIONS.md',PRE_H),('目标台账','lead/GOAL_THREE_TARGETS_20261018.md',PRE_G)]:
 p=root/rel
 cur=hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else 'MISSING'
 if cur!=pre: P.append(lbl+' 被改动 pre='+pre[:12]+' cur='+cur[:12])
print(json.dumps({'ok':not P,'problems':P,'docSha256':SHA,'bindings':len(B),'docBytes':NB,'doc':(DOC.name if DOC else ''),'rows':rows,'hunks':hk},ensure_ascii=False))