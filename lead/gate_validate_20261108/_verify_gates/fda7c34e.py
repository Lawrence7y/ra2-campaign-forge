import json,pathlib,re
root=pathlib.Path('D:/Project/ra2-campaign-forge/lead/criteria_r3_verify_20261108')
doc=root/'R2_BREAKPOINTS_CLOSURE.md';P=[];B=[];NB=0
if not doc.is_file(): P.append('交付件缺失')
else:
 t=doc.read_text(encoding='utf-8');NB=doc.stat().st_size
 for s in ['## 1','## 2','## 3','## 4','## 5','## 6']:
  if s not in t: P.append('缺小节 '+s)
 for k in ['维度 A','维度 B','维度 C','维度 D','闭合','未闭合','升格','未验','不选判据']:
  if k not in t: P.append('缺要素 '+k)
 for bad in ['gamemd.exe','ra2loader','taskkill']:
  if bad in t: P.append('含禁用词 '+bad)
 B=re.findall(r'被核对象 SHA256\s*=\s*`?([0-9a-fA-F]{64})`?',t)
 if not B: P.append('缺 SHA256 绑定行')
print(json.dumps({'ok':not P,'problems':P,'bindings':len(B),'docBytes':NB},ensure_ascii=False))