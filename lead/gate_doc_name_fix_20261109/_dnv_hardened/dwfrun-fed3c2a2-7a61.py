import json,pathlib,re,hashlib
root=pathlib.Path('D:/Project/ra2-campaign-forge')
wd=pathlib.Path('D:/Project/ra2-campaign-forge/lead/gate_doc_name_fix_20261109/_dnv_sandbox36/gate_fp7_20261108')
P=[];NB=0;DOC=None;B=0
DOC=wd/'GATE_FALSE_POSITIVE_5_6_7.md';SHA='MISSING'
if not DOC.is_file(): P.append('主件缺失 GATE_FALSE_POSITIVE_5_6_7.md（写域='+wd.name+'）')
else:
 raw=DOC.read_bytes();NB=len(raw);SHA=hashlib.sha256(raw).hexdigest()
 t=raw.decode('utf-8',errors='replace')
 for s in ['## 1','## 2','## 3','## 4','## 5','## 6']:
  if s not in t: P.append('缺小节 '+s)
 for k in ['第 5 类','第 6 类','第 7 类','第 8 类','反引号','否定语境','双重否定','绑定行','反向验证','未验']:
  if k not in t: P.append('缺要素 '+k)
 for pn in ['R9','R10','R11','R12']:
  if pn not in t: P.append('缺谓词 '+pn)
 B=len(re.findall(r'SHA256\s*=\s*`?[0-9a-fA-F]{64}',t))
 if B<1: P.append('缺 SHA256 绑定（SHA256 后直接跟 = 与 hex）')
PRE_T='543e79184258f9f96517fdc8d61d42e46a7cd544f11ce0ab3b78d9fd505e9abe'
PRE_H='3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7'
PRE_G='2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede'
for lbl,rel,pre in [('门禁模板','lead/gate_template_20261108/GATE_TEMPLATE_FIXED.py.txt',PRE_T),('台账','lead/PENDING_DECISIONS.md',PRE_H),('目标台账','lead/GOAL_THREE_TARGETS_20261018.md',PRE_G),('重签件','lead/n4_yi_final_20261108/CANDIDATE_RESIGN_YES_V2.md',None),('台账草案','lead/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md',None)]:
 p=root/rel
 if pre is None:
  continue
 cur=hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else 'MISSING'
 if cur!=pre: P.append(lbl+' 被改动 pre='+pre[:12]+' cur='+cur[:12])
print(json.dumps({'ok':not P,'problems':P,'docSha256':SHA,'bindings':B,'docBytes':NB,'doc':(DOC.name if DOC else '')},ensure_ascii=False))
