import json,pathlib,re,hashlib
root=pathlib.Path('D:/Project/ra2-campaign-forge')
wd=pathlib.Path('D:/Project/ra2-campaign-forge/lead/gate_doc_name_fix_20261109/_dnv_sandbox36/c07_truth_protocol_20261109')
P=[];NB=0;DOC=None;B=0;FAKE=0
DOC=wd/'C07_TRUTH_SELF_PROOF.md';SHA='MISSING'
if not DOC.is_file(): P.append('主件缺失 C07_TRUTH_SELF_PROOF.md（写域='+wd.name+'）')
else:
 raw=DOC.read_bytes();NB=len(raw);SHA=hashlib.sha256(raw).hexdigest()
 t=raw.decode('utf-8',errors='replace')
 for s in ['## 1','## 2','## 3','## 4','## 5','## 6']:
  if s not in t: P.append('缺小节 '+s)
 for k in ['reviewerSessionId','sourceTaskId','reviewerRole','L1','L2','L3','可核','不可核','伪造检出','检查清单','未验']:
  if k not in t: P.append('缺要素 '+k)
 if ('通过' not in t) or ('存疑' not in t) or ('拒绝' not in t): P.append('缺三档判定')
 FAKE=len(re.findall(r'sess_[A-Za-z0-9]{20,}',t))+len(re.findall(r'\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}',t))
 if FAKE>0: P.append('疑似真实身份ID，命中 '+str(FAKE)+' 处')
 for bad in ['已填','已代填','已提交']:
  if bad in t: P.append('含既成事实断言 '+bad)
 B=len(re.findall(r'被核对象 SHA256 = [0-9a-fA-F]{64}',t))
 if B<1: P.append('缺规范格式绑定行')
PRE_G='3ddddc60fca034fe2b6434e0d8baf38c7bc79966342cf287e8521070b2553600'
PRE_R='d847de88bb0c0c04290c877180a9c45c502df773ba297a36406bffecbe66796b'
PRE_H='3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7'
PRE_GO='2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede'
for lbl,rel,pre in [('增强器','lead/c07_gate_fix_20261109/_f3_c7check.py',PRE_G),('N-1记录','lead/a_residual_n1_20261108/ACCEPTANCE_RECORDS.json',PRE_R),('台账','lead/PENDING_DECISIONS.md',PRE_H),('目标台账','lead/GOAL_THREE_TARGETS_20261018.md',PRE_GO)]:
 p=root/rel
 cur=hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else 'MISSING'
 if cur!=pre: P.append(lbl+' 被改动 pre='+pre[:12]+' cur='+cur[:12])
print(json.dumps({'ok':not P,'problems':P,'docSha256':SHA,'bindings':B,'docBytes':NB,'doc':(DOC.name if DOC else ''),'fakeIds':FAKE},ensure_ascii=False))