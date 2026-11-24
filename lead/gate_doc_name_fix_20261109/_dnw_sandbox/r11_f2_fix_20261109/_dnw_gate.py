import json,pathlib,re,hashlib
root=pathlib.Path('D:/Project/ra2-campaign-forge')
wd=pathlib.Path('D:/Project/ra2-campaign-forge/lead/gate_doc_name_fix_20261109/_dnw_sandbox/r11_f2_fix_20261109')
P=[];NB=0;DOC=None;B=0
mods=[]
DOC=wd/'R11_F2_COVERAGE_FIX.md';SHA='MISSING'
if not DOC.is_file(): P.append('主件缺失 R11_F2_COVERAGE_FIX.md（写域='+wd.name+'）')
else:
 raw=DOC.read_bytes();NB=len(raw);SHA=hashlib.sha256(raw).hexdigest()
 t=raw.decode('utf-8',errors='replace')
 for s in ['## 1','## 2','## 3','## 4','## 5']:
  if s not in t: P.append('缺小节 '+s)
 for k in ['F2','path=null','形态','行号后缀','引文语境','覆盖率','1/18','新误报','盘符','未验']:
  if k not in t: P.append('缺要素 '+k)
 if not re.search(r'1/18',t): P.append('缺覆盖率基数 1/18')
 for bad in ['已改 _g7','已改 g7','已改原文件','已修正 _g7']:
  if bad in t: P.append('含越界断言 '+bad)
 B=len(re.findall(r'被核对象 SHA256 = [0-9a-fA-F]{64}',t))
 if B<1: P.append('缺规范格式绑定行')
 mods=list(wd.glob('_f2_*.py')) if wd.is_dir() else []
 if not mods: P.append('写域内无 _f2_ 补丁模块')
PRE_P='02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120'
PRE_G='a83081eeffc56e830c84ebcfe945114b5e2ac1082467ed04d97634912dacd2a6'
PRE_H='3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7'
PRE_GO='2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede'
for lbl,rel,pre in [('g7谓词','lead/gate_fp7_20261108/_g7_predicates.py',PRE_P),('g9门禁','lead/gate_r9r12_20261109/_g9_gate.py',PRE_G),('台账','lead/PENDING_DECISIONS.md',PRE_H),('目标台账','lead/GOAL_THREE_TARGETS_20261018.md',PRE_GO)]:
 p=root/rel
 cur=hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else 'MISSING'
 if cur!=pre: P.append(lbl+' 被改动 pre='+pre[:12]+' cur='+cur[:12])
print(json.dumps({'ok':not P,'problems':P,'docSha256':SHA,'bindings':B,'docBytes':NB,'doc':(DOC.name if DOC else ''),'modules':len(mods)},ensure_ascii=False))