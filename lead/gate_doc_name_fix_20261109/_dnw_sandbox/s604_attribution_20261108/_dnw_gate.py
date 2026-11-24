import json,pathlib,re,hashlib
root=pathlib.Path('D:/Project/ra2-campaign-forge')
wd=pathlib.Path('D:/Project/ra2-campaign-forge/lead/gate_doc_name_fix_20261109/_dnw_sandbox/s604_attribution_20261108')
P=[];B=[];NB=0;DOC=None
DOC=wd/'S604_ATTRIBUTION.md';SHA='MISSING'
if not DOC.is_file(): P.append('主件缺失 S604_ATTRIBUTION.md（写域='+wd.name+'）')
else:
 raw=DOC.read_bytes();NB=len(raw);SHA=hashlib.sha256(raw).hexdigest()
 t=raw.decode('utf-8',errors='replace')
 for s in ['## 1','## 2','## 3','## 4','## 5','## 6']:
  if s not in t: P.append('缺小节 '+s)
 for k in ['逐窗','对照表','口径差异','语料差异','台账记错','双锚点','无法归属','不改台账','未验']:
  if k not in t: P.append('缺要素 '+k)
 for bad in ['台账应改为','建议修正台账','应修改台账','已修改台账','可应用母本']:
  if bad in t: P.append('含越界断言 '+bad)
 B=re.findall(r'被核对象 SHA256\s*=\s*`?([0-9a-fA-F]{64})`?',t)
 if not B: P.append('缺 SHA256 绑定行')
PRE_L='2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede'
PRE_H='3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7'
for lbl,rel,pre in [('台账','lead/GOAL_THREE_TARGETS_20261018.md',PRE_L),('PENDING','lead/PENDING_DECISIONS.md',PRE_H)]:
 p=root/rel
 cur=hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else 'MISSING'
 if cur!=pre: P.append(lbl+' 被改动 pre='+pre[:12]+' cur='+cur[:12])
print(json.dumps({'ok':not P,'problems':P,'docSha256':SHA,'bindings':len(B),'docBytes':NB,'doc':(DOC.name if DOC else '')},ensure_ascii=False))