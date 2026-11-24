import json,pathlib,re
root=pathlib.Path('D:/Project/ra2-campaign-forge/lead/slowwindow_n8_20261108')
doc=root/'SLOW_WINDOW_LIMITS.md';problems=[];binds=[];docBytes=0
if not doc.is_file(): problems.append('交付件缺失')
else:
 t=doc.read_text(encoding='utf-8');docBytes=doc.stat().st_size
 for s in ['## 1','## 2','## 3','## 4','## 5','## 6']:
  if s not in t: problems.append('缺小节 '+s)
 for k in ['帧级单位数','节点数','路径调用次数','引擎阶段时间','可识别','未验','N-11']:
  if k not in t: problems.append('缺要素 '+k)
 binds=re.findall(r'被核对象 SHA256\s*=\s*`?([0-9a-fA-F]{64})`?',t)
 if len(binds)<1: problems.append('缺 SHA256 绑定行')
for py in root.glob('*.py'):
 s=py.read_text(encoding='utf-8')
 if re.search(r'subprocess\.(Popen|run|call)\s*\([^)]*(gamemd|ra2loader|YURI)',s): problems.append(py.name+' 启动游戏进程')
print(json.dumps({'ok':len(problems)==0,'problems':problems,'bindings':len(binds),'docBytes':docBytes},ensure_ascii=False))