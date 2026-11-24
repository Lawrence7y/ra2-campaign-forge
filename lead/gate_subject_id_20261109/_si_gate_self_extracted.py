import json,pathlib,re,hashlib
root=pathlib.Path('D:/Project/ra2-campaign-forge')
wd=root/'lead/gate_subject_id_20261109'
P=[]
expected=wd/'GATE_SUBJECT_ID_FIX.md'
if not expected.is_file(): P.append('主交付件未按约定命名 GATE_SUBJECT_ID_FIX.md')
else:
 t=expected.read_text(encoding='utf-8');NB=expected.stat().st_size
 for s in ['## 1','## 2','## 3','## 4','## 5']:
  if s not in t: P.append('缺小节 '+s)
 for k in ['max(st_size)','中间稿','下划线','受害面','根因','可操纵性','绕过','显式命名','三方案','全量清单','未改任何历史件','未验']:
  if k not in t: P.append('缺要素 '+k)
 for bad in ['已改门禁','已改历史件','已修复']:
  if bad in t: P.append('含既成事实断言 '+bad)
 B=len(re.findall(r'被核对象 SHA256 = [0-9a-fA-F]{64}',t))
 if B<1: P.append('缺规范格式绑定行')
PRE_H='3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7'
PRE_GO='2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede'
for lbl,rel,pre in [('台账','lead/PENDING_DECISIONS.md',PRE_H),('目标台账','lead/GOAL_THREE_TARGETS_20261018.md',PRE_GO)]:
 p=root/rel
 cur=hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else 'MISSING'
 if cur!=pre: P.append(lbl+' 被改动 pre='+pre[:12]+' cur='+cur[:12])
print(json.dumps({'ok':not P,'problems':P,'bindings':(B if expected.is_file() else 0)},ensure_ascii=False))