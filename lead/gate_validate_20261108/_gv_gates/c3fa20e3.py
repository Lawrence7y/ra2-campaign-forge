import json,pathlib,re
root=pathlib.Path('D:/Project/ra2-campaign-forge/lead/slowframe_round2_20261107')
doc=root/'SLOWFRAME_PROXY.md';problems=[];binds=[];docBytes=0
if not doc.is_file(): problems.append('交付件缺失')
else:
 t=doc.read_text(encoding='utf-8');docBytes=doc.stat().st_size
 for s in ['## 1','## 2','## 3','## 4','## 5','## 6']:
  if s not in t: problems.append('缺小节 '+s)
 for b in ['gamemd.exe','ra2loader','taskkill','OpenProcess','ReadProcessMemory','SuspendThread','StackWalk64','MiniDumpWriteDump','CreateRemoteThread','SetWindowsHookEx','ctypes.windll']:
  if b in t: problems.append('禁用词 '+b)
 binds=re.findall(r'被核对象 SHA256\s*=\s*`?([0-9a-fA-F]{64})`?',t)
 if len(binds)<1: problems.append('缺 SHA256 绑定行')
for py in root.glob('*.py'):
 s=py.read_text(encoding='utf-8')
 for b in ['OpenProcess','ReadProcessMemory','SuspendThread','StackWalk','MiniDump','CreateRemoteThread','ctypes.windll']:
  if b in s: problems.append(py.name+' 含禁用词 '+b)
print(json.dumps({'ok':len(problems)==0,'problems':problems,'bindings':len(binds),'docBytes':docBytes},ensure_ascii=False))