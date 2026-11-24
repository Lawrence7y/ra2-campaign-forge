import json,pathlib,re,hashlib
root=pathlib.Path('D:/Project/ra2-campaign-forge')
wd=pathlib.Path('D:/Project/ra2-campaign-forge/lead/gate_doc_name_fix_20261109/_dnv_sandbox36/samedoc_link_20261109')
P=[];NB=0;DOC=None;B=0
mods=[]
DOC=wd/'SAMEDOC_LINK.md';SHA='MISSING'
if not DOC.is_file(): P.append('主件缺失 SAMEDOC_LINK.md（写域='+wd.name+'）')
else:
 raw=DOC.read_bytes();NB=len(raw);SHA=hashlib.sha256(raw).hexdigest()
 t=raw.decode('utf-8',errors='replace')
 for s in ['## 1','## 2','## 3','## 4','## 5']:
  if s not in t: P.append('缺小节 '+s)
 for k in ['唯一命中','多命中','零命中','放弃采集','去重','相对路径','warning','全仓反查','9/10','防伪造','残余风险','未改任何文件','未验']:
  if k not in t: P.append('缺要素 '+k)
 for bad in ['已改','已合入','已升级为 problem']:
  if bad in t: P.append('含越界断言 '+bad)
 B=len(re.findall(r'被核对象 SHA256 = [0-9a-fA-F]{64}',t))
 if B<1: P.append('缺规范格式绑定行')
 mods=list(wd.glob('_sl_*.py')) if wd.is_dir() else []
 if not mods: P.append('写域内无 _sl_ 联查实现')
PRE_G='02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120'
PRE_P='83f8217fb9a194befdd389f0fd9e699660d3240f0cf1eec365cc3d612fdf8f75'
PRE_H='3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7'
PRE_GO='2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede'
for lbl,rel,pre in [('g7谓词','lead/gate_fp7_20261108/_g7_predicates.py',PRE_G),('补丁模块','lead/r11_f2_fix_20261109/_f2_r11plus.py',PRE_P),('台账','lead/PENDING_DECISIONS.md',PRE_H),('目标台账','lead/GOAL_THREE_TARGETS_20261018.md',PRE_GO)]:
 p=root/rel
 cur=hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else 'MISSING'
 if cur!=pre: P.append(lbl+' 被改动 pre='+pre[:12]+' cur='+cur[:12])
print(json.dumps({'ok':not P,'problems':P,'docSha256':SHA,'bindings':B,'docBytes':NB,'doc':(DOC.name if DOC else ''),'mods':len(mods)},ensure_ascii=False))
