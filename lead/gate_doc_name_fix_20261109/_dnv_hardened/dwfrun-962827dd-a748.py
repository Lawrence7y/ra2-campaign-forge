import json,pathlib,re,hashlib
root=pathlib.Path('D:/Project/ra2-campaign-forge')
wd=pathlib.Path('D:/Project/ra2-campaign-forge/lead/gate_doc_name_fix_20261109/_dnv_sandbox36/c07_gate_audit_20261109')
P=[];NB=0;DOC=None;B=0
DOC=wd/'C07_SELFCHECK_AUDIT.md';SHA='MISSING'
if not DOC.is_file(): P.append('主件缺失 C07_SELFCHECK_AUDIT.md（写域='+wd.name+'）')
else:
 raw=DOC.read_bytes();NB=len(raw);SHA=hashlib.sha256(raw).hexdigest()
 t=raw.decode('utf-8',errors='replace')
 for s in ['## 1','## 2','## 3','## 4','## 5']:
  if s not in t: P.append('缺小节 '+s)
 for k in ['15 项校验','攻样本','T4','T6','拦住','漏过','冒签','严重性','保证边界','未改 _c7_selfcheck.py','未验']:
  if k not in t: P.append('缺要素 '+k)
 for bad in ['已改门禁','已修补','已加固']:
  if bad in t: P.append('含既成事实断言 '+bad)
 B=len(re.findall(r'被核对象 SHA256 = [0-9a-fA-F]{64}',t))
 if B<1: P.append('缺规范格式绑定行')
PRE_G='74bec4d48498903df08dbf3a56ba942e74b58f5b4a7940c094eafdeb03adbf2e'
PRE_T='3d763a8b679370ade8999a23a18679c7296909bf8a020b71694c0ccca7e8b062'
PRE_R2='d847de88bb0c0c04290c877180a9c45c502df773ba297a36406bffecbe66796b'
PRE_R1='d421f8bc5cc02eee2a0ea908a60477cdb313541cbff3cfd96a65728528d0efda'
PRE_H='3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7'
PRE_GO='2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede'
for lbl,rel,pre in [('C07门禁','lead/c07_slot_20261109/_c7_selfcheck.py',PRE_G),('模板','lead/c07_slot_20261109/_c7_record_template.json',PRE_T),('r2先例','lead/a_residual_n1_20261108/ACCEPTANCE_RECORDS.json',PRE_R2),('r1先例','lead/a_residual_20261106/ACCEPTANCE_RECORDS.json',PRE_R1),('台账','lead/PENDING_DECISIONS.md',PRE_H),('目标台账','lead/GOAL_THREE_TARGETS_20261018.md',PRE_GO)]:
 p=root/rel
 cur=hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else 'MISSING'
 if cur!=pre: P.append(lbl+' 被改动 pre='+pre[:12]+' cur='+cur[:12])
print(json.dumps({'ok':not P,'problems':P,'docSha256':SHA,'bindings':B,'docBytes':NB,'doc':(DOC.name if DOC else '')},ensure_ascii=False))
