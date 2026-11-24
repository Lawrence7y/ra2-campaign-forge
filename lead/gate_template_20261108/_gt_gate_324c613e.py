import json,pathlib,re
root=pathlib.Path('D:/Project/ra2-campaign-forge/lead/a_residual_n1_20261108')
doc=root/'A_RESIDUAL_REFERENCES.md';js=root/'ACCEPTANCE_RECORDS.json';problems=[];binds=[];docBytes=0
if not doc.is_file(): problems.append('交付件缺失')
else:
 t=doc.read_text(encoding='utf-8');docBytes=doc.stat().st_size
 for s in ['## 1','## 2','## 3','## 4','## 5','## 6']:
  if s not in t: problems.append('缺小节 '+s)
 for k in ['W9-2','W9-9','W9-19','W8-6','W8-11','W8-8','W8-7','未验','替代关系']:
  if k not in t: problems.append('缺标签 '+k)
 binds=re.findall(r'被核对象 SHA256\s*=\s*`?([0-9a-fA-F]{64})`?',t)
 if len(binds)<1: problems.append('缺 SHA256 绑定行')
if not js.is_file(): problems.append('验收 JSON 缺失')
else:
 try:
  d=json.loads(js.read_text(encoding='utf-8'))
  req=['itemId','reviewerRole','reviewerSessionId','sourceTaskId','inputHashes','artifactHashes','decision','unresolved','timestamp']
  rows=d if isinstance(d,list) else (d.get('records') if isinstance(d,dict) else [])
  if not isinstance(rows,list) or len(rows)==0: problems.append('验收记录为空')
  for i,r in enumerate(rows if isinstance(rows,list) else []):
   missing=[k for k in req if k not in r]
   if missing: problems.append('记录%d缺字段 %s'%(i,','.join(missing)))
 except Exception as e: problems.append('验收 JSON 不可解析: '+str(e)[:80])
for py in root.glob('*.py'):
 s=py.read_text(encoding='utf-8')
 if re.search(r'subprocess\.(Popen|run|call)\s*\([^)]*(gamemd|ra2loader|YURI)',s): problems.append(py.name+' 启动游戏进程')
print(json.dumps({'ok':len(problems)==0,'problems':problems,'bindings':len(binds),'docBytes':docBytes},ensure_ascii=False))