import json,pathlib,re
root=pathlib.Path('D:/Project/ra2-campaign-forge/lead/gate_template_20261108')
doc=root/'GATE_FALSE_POSITIVES.md';tpl=root/'GATE_TEMPLATE_FIXED.py.txt';P=[];B=[];NB=0
if not doc.is_file(): P.append('交付件缺失')
else:
 t=doc.read_text(encoding='utf-8');NB=doc.stat().st_size
 for s in ['## 1','## 2','## 3','## 4','## 5','## 6']:
  if s not in t: P.append('缺小节 '+s)
 for k in ['误报模式','禁词子串','措辞不匹配','版本锚','修正模板','不可引用','未验']:
  if k not in t: P.append('缺要素 '+k)
 B=re.findall(r'被核对象 SHA256\s*=\s*`?([0-9a-fA-F]{64})`?',t)
 if not B: P.append('缺 SHA256 绑定行')
if not tpl.is_file(): P.append('修正模板缺失')
print(json.dumps({'ok':not P,'problems':P,'bindings':len(B),'docBytes':NB},ensure_ascii=False))