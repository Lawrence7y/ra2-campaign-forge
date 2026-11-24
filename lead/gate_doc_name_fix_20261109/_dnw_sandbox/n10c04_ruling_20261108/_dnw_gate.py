import json,pathlib,re,hashlib
root=pathlib.Path('D:/Project/ra2-campaign-forge')
wd=pathlib.Path('D:/Project/ra2-campaign-forge/lead/gate_doc_name_fix_20261109/_dnw_sandbox/n10c04_ruling_20261108')
P=[];B=[];NB=0;DOC=None
DOC=wd/'RULING_STATIC_ORDER.md';SHA='MISSING'
if not DOC.is_file(): P.append('主件缺失 RULING_STATIC_ORDER.md（写域='+wd.name+'）')
else:
 raw=DOC.read_bytes();NB=len(raw);SHA=hashlib.sha256(raw).hexdigest()
 t=raw.decode('utf-8',errors='replace')
 for s in ['## 1','## 2','## 3','## 4','## 5','## 6']:
  if s not in t: P.append('缺小节 '+s)
 for k in ['Q3','顺序','写域','P11','S4','S1','P6 半闭半开','条件性','不授实施权','未验']:
  if k not in t: P.append('缺要素 '+k)
 for bad in ['授实施权','解除 PAUSE','可应用母本','已应用','已签 APPROVE_SCOPE']:
  if bad in t: P.append('含越权断言 '+bad)
 if re.search(r'并行推进\s*$',t,re.M): P.append('含不可排期结论「并行推进」')
 for item in ['S1','S2','S3','S4','P6','P7','P8','P11']:
  if item not in t: P.append('缺缺口项 '+item)
 B=re.findall(r'被核对象 SHA256\s*=\s*`?([0-9a-fA-F]{64})`?',t)
 if not B: P.append('缺 SHA256 绑定行')
PRE_H='3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7'
PRE_G='2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede'
for lbl,rel,pre in [('台账','lead/PENDING_DECISIONS.md',PRE_H),('目标台账','lead/GOAL_THREE_TARGETS_20261018.md',PRE_G)]:
 p=root/rel
 cur=hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else 'MISSING'
 if cur!=pre: P.append(lbl+' 被改动 pre='+pre[:12]+' cur='+cur[:12])
print(json.dumps({'ok':not P,'problems':P,'docSha256':SHA,'bindings':len(B),'docBytes':NB,'doc':(DOC.name if DOC else '')},ensure_ascii=False))