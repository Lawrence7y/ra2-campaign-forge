import json,pathlib,re,hashlib
root=pathlib.Path('D:/Project/ra2-campaign-forge')
wd=pathlib.Path('D:/Project/ra2-campaign-forge/lead/gate_doc_name_fix_20261109/_dnv_sandbox36/s604_script_gap_20261109')
P=[];NB=0;DOC=None;B=0
DOC=wd/'S604_SCRIPT_GAP.md';SHA='MISSING'
if not DOC.is_file(): P.append('主件缺失 S604_SCRIPT_GAP.md（写域='+wd.name+'）')
else:
 raw=DOC.read_bytes();NB=len(raw);SHA=hashlib.sha256(raw).hexdigest()
 t=raw.decode('utf-8',errors='replace')
 for s in ['## 1','## 2','## 3','## 4','## 5']:
  if s not in t: P.append('缺小节 '+s)
 for k in ['脚本存在性','可重建','自由度','单向压缩','候选','可证伪','假设非定谳','最小补充证据','未验']:
  if k not in t: P.append('缺要素 '+k)
 for bad in ['已定位错误环节','确定错误在','已重建台账','已改台账']:
  if bad in t: P.append('含越权断言 '+bad)
 B=len(re.findall(r'被核对象 SHA256 = [0-9a-fA-F]{64}',t))
 if B<1: P.append('缺规范格式绑定行（要求：被核对象 SHA256 = 后紧跟64位hex，中间无插入）')
PRE_L='2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede'
PRE_H='3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7'
for lbl,rel,pre in [('台账','lead/GOAL_THREE_TARGETS_20261018.md',PRE_L),('PENDING','lead/PENDING_DECISIONS.md',PRE_H)]:
 p=root/rel
 cur=hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else 'MISSING'
 if cur!=pre: P.append(lbl+' 被改动 pre='+pre[:12]+' cur='+cur[:12])
print(json.dumps({'ok':not P,'problems':P,'docSha256':SHA,'bindings':B,'docBytes':NB,'doc':(DOC.name if DOC else '')},ensure_ascii=False))