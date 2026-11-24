import json,pathlib,re,hashlib
root=pathlib.Path('D:/Project/ra2-campaign-forge')
wd=pathlib.Path('D:/Project/ra2-campaign-forge/lead/gate_doc_name_fix_20261109/_dnv_sandbox36/c07_protocol_attacks_20261109')
P=[];NB=0;DOC=None;B=0
DOC=wd/'PROTOCOL_ATTACK_TEST.md';SHA='MISSING'
if not DOC.is_file(): P.append('主件缺失 PROTOCOL_ATTACK_TEST.md（写域='+wd.name+'）')
else:
 raw=DOC.read_bytes();NB=len(raw);SHA=hashlib.sha256(raw).hexdigest()
 t=raw.decode('utf-8',errors='replace')
 for s in ['## 1','## 2','## 3','## 4','## 5']:
  if s not in t: P.append('缺小节 '+s)
 miss=[str(i) for i in range(1,11) if ('A'+str(i)) not in t]
 if miss: P.append('缺手法：'+','.join(miss))
 for k in ['构造','应挡条款','实际结果','实跑','推理','严重性','铁则','可执行','效力上限','未改任何文件','未验']:
  if k not in t: P.append('缺要素 '+k)
 if ('根本性' not in t) and ('无法加固' not in t): P.append('缺根本性漏洞评估')
 FAKE=len(re.findall(r'sess_[A-Za-z0-9]{24,}',t))
 if FAKE>0: P.append('写域内出现疑似真实ID形态 '+str(FAKE)+' 处（应仅在子目录样本内）')
 B=len(re.findall(r'被核对象 SHA256 = [0-9a-fA-F]{64}',t))
 if B<1: P.append('缺规范格式绑定行')
PRE_P='68395681bbfd6b348a91664ec8c0dfafe1b9aa22a939691d0683414071f96547'
PRE_C='fe0d6909c49aa6ee30775d77304da88eac924acaab2d13ccbb858c99bf6136b7'
PRE_G='3ddddc60fca034fe2b6434e0d8baf38c7bc79966342cf287e8521070b2553600'
PRE_H='3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7'
PRE_GO='2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede'
for lbl,rel,pre in [('主协议','lead/c07_truth_protocol_20261109/_tp_C07_TRUTH_PROTOCOL.md',PRE_P),('核验清单','lead/c07_truth_protocol_20261109/_tp_TP_VERIFIER_CHECKLIST.md',PRE_C),('增强门禁','lead/c07_gate_fix_20261109/_f3_c7check.py',PRE_G),('台账','lead/PENDING_DECISIONS.md',PRE_H),('目标台账','lead/GOAL_THREE_TARGETS_20261018.md',PRE_GO)]:
 p=root/rel
 cur=hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else 'MISSING'
 if cur!=pre: P.append(lbl+' 被改动 pre='+pre[:12]+' cur='+cur[:12])
print(json.dumps({'ok':not P,'problems':P,'docSha256':SHA,'bindings':B,'docBytes':NB,'doc':(DOC.name if DOC else '')},ensure_ascii=False))