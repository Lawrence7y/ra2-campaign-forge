import json,pathlib,re,hashlib
root=pathlib.Path('D:/Project/ra2-campaign-forge')
wd=pathlib.Path('D:/Project/ra2-campaign-forge/lead/gate_doc_name_fix_20261109/_dnv_sandbox36/gate_r9r12_20261109')
P=[];NB=0;DOC=None;B=0
DOC=wd/'GATE_R9R12_REGRESSION.md';SHA='MISSING'
if not DOC.is_file(): P.append('主件缺失 GATE_R9R12_REGRESSION.md（写域='+wd.name+'）')
else:
 raw=DOC.read_bytes();NB=len(raw);SHA=hashlib.sha256(raw).hexdigest()
 t=raw.decode('utf-8',errors='replace')
 for s in ['## 1','## 2','## 3','## 4','## 5','## 6']:
  if s not in t: P.append('缺小节 '+s)
 for k in ['R9','R10','R11','R12','检查计数','全历史回归','残余','真问题','误报','未改任何文件','未验']:
  if k not in t: P.append('缺要素 '+k)
 for bad in ['已改模板','已改交付件','已修改模板']:
  if bad in t: P.append('含既成事实断言 '+bad)
 B=len(re.findall(r'被核对象 SHA256 = [0-9a-fA-F]{64}',t))
 if B<1: P.append('缺规范格式绑定行')
 mods=list(wd.glob('_g9_*.py')) if wd.is_dir() else []
 if not mods: P.append('写域内无 _g9_ 门禁模块')
PRE_P='02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120'
PRE_H='3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7'
PRE_G='2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede'
for lbl,rel,pre in [('谓词件','lead/gate_fp7_20261108/_g7_predicates.py',PRE_P),('台账','lead/PENDING_DECISIONS.md',PRE_H),('目标台账','lead/GOAL_THREE_TARGETS_20261018.md',PRE_G)]:
 p=root/rel
 cur=hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else 'MISSING'
 if cur!=pre: P.append(lbl+' 被改动 pre='+pre[:12]+' cur='+cur[:12])
print(json.dumps({'ok':not P,'problems':P,'docSha256':SHA,'bindings':B,'docBytes':NB,'doc':(DOC.name if DOC else ''),'modules':len(mods)},ensure_ascii=False))