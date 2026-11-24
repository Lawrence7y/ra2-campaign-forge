import json,pathlib,re,hashlib
root=pathlib.Path('D:/Project/ra2-campaign-forge')
wd=pathlib.Path('D:/Project/ra2-campaign-forge/lead/gate_doc_name_fix_20261109/_dnv_sandbox36/n11_wording_fix_20261108')
P=[];NB=0;DOC=None;B=0
DOC=wd/'N11_WORDING_FIX.md';SHA='MISSING'
if not DOC.is_file(): P.append('主件缺失 N11_WORDING_FIX.md（写域='+wd.name+'）')
else:
 raw=DOC.read_bytes();NB=len(raw);SHA=hashlib.sha256(raw).hexdigest()
 t=raw.decode('utf-8',errors='replace')
 for s in ['## 1','## 2','## 3','## 4','## 5']:
  if s not in t: P.append('缺小节 '+s)
 for k in ['一一对应','11 裁决项','13 维','拆分','最小改动','改前改后','承接件','需谁批准','未改任何文件','未验']:
  if k not in t: P.append('缺要素 '+k)
 for bad in ['已修改','已订正','已改首件']:
  if bad in t: P.append('含既成事实断言 '+bad)
 B=len(re.findall(r'SHA256\s*=\s*`?[0-9a-fA-F]{64}',t))
 if B<1: P.append('缺 SHA256 绑定')
PRE_P='3d463483ad0d53d048a9cad9990b6c0e8b72485ef20eeaa8c519074ebdf94bda'
PRE_O='c0dfb0d17edab4d0d89c43dc48bce4b84354fd13bd89cae7277aa15e82cf65f2'
PRE_H='3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7'
PRE_G='2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede'
for lbl,rel,pre in [('首件','lead/n11_protocol_spec_20261108/_ps_N11_MIN_OBS_PROTOCOL_SPEC.md',PRE_P),('承接件','lead/n11_protocol_spec_20261108/OBSERVATION_PROTOCOL_SPEC.md',PRE_O),('台账','lead/PENDING_DECISIONS.md',PRE_H),('目标台账','lead/GOAL_THREE_TARGETS_20261018.md',PRE_G)]:
 p=root/rel
 cur=hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else 'MISSING'
 if cur!=pre: P.append(lbl+' 被改动 pre='+pre[:12]+' cur='+cur[:12])
print(json.dumps({'ok':not P,'problems':P,'docSha256':SHA,'bindings':B,'docBytes':NB,'doc':(DOC.name if DOC else '')},ensure_ascii=False))
