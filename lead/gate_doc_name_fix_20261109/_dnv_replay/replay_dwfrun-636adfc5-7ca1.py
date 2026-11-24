import json,pathlib,re,hashlib
root=pathlib.Path('D:/Project/ra2-campaign-forge')
wd=root/'lead/counterpart_fix_20261109'
P=[];NB=0;DOC=None;B=0
cands=sorted(wd.glob('*.md')) if wd.is_dir() else []
if not cands: P.append('写域内无 md 交付件')
else:
 DOC=max(cands,key=lambda p:p.stat().st_size)
 t=DOC.read_text(encoding='utf-8');NB=DOC.stat().st_size
 for s in ['## 1','## 2','## 3','## 4','## 5','## 6']:
  if s not in t: P.append('缺小节 '+s)
 for k in ['MISLABEL','ORPHAN','收紧','补对照','分流表述','逐格','绑定击穿','最小必要改动','兼容','未改任何文件','未验']:
  if k not in t: P.append('缺要素 '+k)
 if ('变 ORPHAN' not in t) and ('变成 ORPHAN' not in t): P.append('缺「变ORPHAN不等于解决」声明')
 for bad in ['已改','已补','已收紧','已增行']:
  if bad in t: P.append('含既成事实断言 '+bad)
 B=len(re.findall(r'被核对象 SHA256 = [0-9a-fA-F]{64}',t))
 if B<1: P.append('缺规范格式绑定行')
PRE_MAT='00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000'
PRE_D='00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000'
PRE_C='00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000'
PRE_V='00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000'
PRE_M='00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000'
PRE_H='00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000'
PRE_GO='00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000'
for lbl,rel,pre in [('乙矩阵','lead/b2b_design_20261106/STATE_MATRIX.json',PRE_MAT),('乙设计','lead/b2b_design_20261106/B2B_DESIGN.md',PRE_D),('候选','lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py',PRE_C),('V2','lead/n4_yi_final_20261108/_n4v2_B_EXECUTION_SPEC_V2.md',PRE_V),('母本','out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py',PRE_M),('台账','lead/PENDING_DECISIONS.md',PRE_H),('目标台账','lead/GOAL_THREE_TARGETS_20261018.md',PRE_GO)]:
 p=root/rel
 cur=hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else 'MISSING'
 if cur!=pre: P.append(lbl+' 被改动 pre='+pre[:12]+' cur='+cur[:12])
print(json.dumps({'ok':not P,'problems':P,'bindings':B,'docBytes':NB,'doc':(DOC.name if DOC else '')},ensure_ascii=False))