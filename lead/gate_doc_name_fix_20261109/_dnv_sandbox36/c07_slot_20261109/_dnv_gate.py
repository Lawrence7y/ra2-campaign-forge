import json,pathlib,re,hashlib
root=pathlib.Path('D:/Project/ra2-campaign-forge')
wd=pathlib.Path('D:/Project/ra2-campaign-forge/lead/gate_doc_name_fix_20261109/_dnv_sandbox36/c07_slot_20261109')
P=[];NB=0;DOC=None;B=0;FAKE=0
DOC=wd/'C07_IDENTITY_SLOT.md';SHA='MISSING'
if not DOC.is_file(): P.append('主件缺失 C07_IDENTITY_SLOT.md（写域='+wd.name+'）')
else:
 raw=DOC.read_bytes();NB=len(raw);SHA=hashlib.sha256(raw).hexdigest()
 t=raw.decode('utf-8',errors='replace')
 for s in ['## 1','## 2','## 3','## 4','## 5','## 6']:
  if s not in t: P.append('缺小节 '+s)
 for k in ['三字段','N-1 八字段','落点','占位符','校验规则','多处同步','不许代填','需谁补登','未验']:
  if k not in t: P.append('缺要素 '+k)
 for bad in ['已补登','已填入','已填','已代填']:
  if bad in t: P.append('含既成事实断言 '+bad)
 FAKE=len(re.findall(r'sess_[A-Za-z0-9]{6,}',t))+len(re.findall(r'\b[0-9a-f]{32,}\b',t))+len(re.findall(r'\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}',t))
 if FAKE>0: P.append('疑似伪造身份ID，命中 '+str(FAKE)+' 处')
 B=len(re.findall(r'SHA256\s*=\s*`[0-9a-fA-F]{64}`',t))
 if B<1: P.append('缺规范格式绑定行（要求 SHA256 = 反引号包64hex）')
PRE_H='3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7'
PRE_G='2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede'
PRE_D='0a709f2da12e0234cd94ff0baf521652e7d1aed6cfd04929b9728adbfd85bf5f'
for lbl,rel,pre in [('台账','lead/PENDING_DECISIONS.md',PRE_H),('目标台账','lead/GOAL_THREE_TARGETS_20261018.md',PRE_G),('DQ卡','lead/d13d14_cards_20261108/DECISION_QUESTIONS.md',PRE_D)]:
 p=root/rel
 cur=hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else 'MISSING'
 if cur!=pre: P.append(lbl+' 被改动 pre='+pre[:12]+' cur='+cur[:12])
print(json.dumps({'ok':not P,'problems':P,'docSha256':SHA,'bindings':B,'docBytes':NB,'doc':(DOC.name if DOC else ''),'fakeIds':FAKE},ensure_ascii=False))