import json,pathlib,re,hashlib
root=pathlib.Path('D:/Project/ra2-campaign-forge')
wd=root/'lead/ledger_bound_20261109'
P=[]
expected=wd/'LEDGER_BOUND_VOLUME.md'
if not expected.is_file(): P.append('主交付件未按约定命名 LEDGER_BOUND_VOLUME.md')
else:
 t=expected.read_text(encoding='utf-8');NB=expected.stat().st_size
 for s in ['## 1','## 2','## 3','## 4','## 5']:
  if s not in t: P.append('缺小节 '+s)
 for k in ['待入账','笔3','第五笔','§609','冲突','依赖','编号','逐字照抄','未改台账','未验']:
  if k not in t: P.append('缺要素 '+k)
 for bad in ['已入账','已追加','已生效']:
  if bad in t: P.append('含越权断言 '+bad)
 B=len(re.findall(r'被核对象 SHA256 = [0-9a-fA-F]{64}',t))
 if B<1: P.append('缺规范格式绑定行')
PRE_L='2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede'
PRE_H='3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7'
PRE_S='058630a1b34a8140ed2b57e796f3d64413e76e0f99a5f7f648fd56347577f9ec'
for lbl,rel,pre in [('目标台账','lead/GOAL_THREE_TARGETS_20261018.md',PRE_L),('PENDING','lead/PENDING_DECISIONS.md',PRE_H),('§609草案','lead/s604_verdict_entry_20261109/_ve_DRAFT_S609.md',PRE_S)]:
 p=root/rel
 cur=hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else 'MISSING'
 if cur!=pre: P.append(lbl+' 被改动 pre='+pre[:12]+' cur='+cur[:12])
print(json.dumps({'ok':not P,'problems':P,'bindings':(B if expected.is_file() else 0)},ensure_ascii=False))