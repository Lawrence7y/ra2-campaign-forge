import json,pathlib,re
root=pathlib.Path('D:/Project/ra2-campaign-forge/lead/five_read_n7_20261107')
doc=root/'FIVE_READ_COST_RECHECK.md';problems=[];binds=[];docBytes=0
if not doc.is_file(): problems.append('交付件缺失')
else:
 t=doc.read_text(encoding='utf-8');docBytes=doc.stat().st_size
 for s in ['## 1','## 2','## 3','## 4','## 5','## 6']:
  if s not in t: problems.append('缺小节 '+s)
 for k in ['输入清单','分母','纳排','双窗口','未验']:
  if k not in t: problems.append('缺要素 '+k)
 binds=re.findall(r'被核对象 SHA256\s*=\s*`?([0-9a-fA-F]{64})`?',t)
 if len(binds)<1: problems.append('缺 SHA256 绑定行')
for py in root.glob('*.py'):
 s=py.read_text(encoding='utf-8')
 if re.search(r'subprocess\.(Popen|run|call)\s*\([^)]*(gamemd|ra2loader|YURI)',s): problems.append(py.name+' 启动游戏进程')
print(json.dumps({'ok':len(problems)==0,'problems':problems,'bindings':len(binds),'docBytes':docBytes},ensure_ascii=False))