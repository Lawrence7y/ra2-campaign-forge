import json,pathlib,re,hashlib
root=pathlib.Path('D:/Project/ra2-campaign-forge')
wd=pathlib.Path('D:/Project/ra2-campaign-forge/lead/gate_doc_name_fix_20261109/_dnv_sandbox36/c07_gate_fix_20261109')
P=[];NB=0;DOC=None;B=0
DOC=wd/'C07_GATE_G1_G5_FIX.md';SHA='MISSING'
if not DOC.is_file(): P.append('主件缺失 C07_GATE_G1_G5_FIX.md（写域='+wd.name+'）')
else:
 raw=DOC.read_bytes();NB=len(raw);SHA=hashlib.sha256(raw).hexdigest()
 t=raw.decode('utf-8',errors='replace')
 for s in ['## 1','## 2','## 3','## 4','## 5','## 6']:
  if s not in t: P.append('缺小节 '+s)
 for k in ['G1','G2','G3','G4','G5','36 样本','拦下','误放','真值','守门人','未改原门禁','未验']:
  if k not in t: P.append('缺要素 '+k)
 if ('sess_dwf' not in t) and ('形制' not in t): P.append('缺 G5 形制校验说明')
 for bad in ['已改原门禁','已改 _c7_selfcheck','已改门禁']:
  if bad in t: P.append('含越界断言 '+bad)
 B=len(re.findall(r'被核对象 SHA256 = [0-9a-fA-F]{64}',t))
 if B<1: P.append('缺规范格式绑定行')
 mods=list(wd.glob('_f3_*.py')) if wd.is_dir() else []
 if not mods: P.append('写域内无 _f3_ 增强版校验器')
PRE_G='74bec4d48498903df08dbf3a56ba942e74b58f5b4a7940c094eafdeb03adbf2e'
PRE_T='3d763a8b679370ade8999a23a18679c7296909bf8a020b71694c0ccca7e8b062'
PRE_I='53082d91ce34f76877b08061503795b8d50b0bcbfac036cc0df6e9b67e7d5610'
PRE_H='3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7'
PRE_GO='2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede'
for lbl,rel,pre in [('原门禁','lead/c07_slot_20261109/_c7_selfcheck.py',PRE_G),('模板','lead/c07_slot_20261109/_c7_record_template.json',PRE_T),('独立器','lead/c07_gate_audit_20261109/_c7a_independent.py',PRE_I),('台账','lead/PENDING_DECISIONS.md',PRE_H),('目标台账','lead/GOAL_THREE_TARGETS_20261018.md',PRE_GO)]:
 p=root/rel
 cur=hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else 'MISSING'
 if cur!=pre: P.append(lbl+' 被改动 pre='+pre[:12]+' cur='+cur[:12])
print(json.dumps({'ok':not P,'problems':P,'docSha256':SHA,'bindings':B,'docBytes':NB,'doc':(DOC.name if DOC else ''),'modules':len(mods)},ensure_ascii=False))