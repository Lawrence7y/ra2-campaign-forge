import json,pathlib,re,hashlib
root=pathlib.Path('D:/Project/ra2-campaign-forge/lead/dtrigger_round2_20261107')
doc=root/'CRITERIA_ROUND2.md'
problems=[]; binds=[]; docBytes=0
if not doc.is_file():
 problems.append('交付件缺失: CRITERIA_ROUND2.md')
else:
 text=doc.read_text(encoding='utf-8'); docBytes=doc.stat().st_size
 for s in ['## 1','## 2','## 3','## 4','## 5','## 6','## 7','## 8']:
  if s not in text: problems.append('缺必填小节 '+s)
 banned=['OpenProcess','ReadProcessMemory','WriteProcessMemory','SuspendThread','StackWalk64','MiniDumpWriteDump','CreateRemoteThread','SetWindowsHookEx','VirtualAllocEx','TerminateProcess','gamemd.exe','ra2loader','taskkill']
 for b in banned:
  if b in text: problems.append('交付件含禁用词 '+b)
 binds=re.findall(r'被核对象 SHA256\s*=\s*`?([0-9a-fA-F]{64})`?',text)
 if len(binds)<4: problems.append('SHA256 绑定行不足4: '+str(len(binds)))
 if len(re.findall(r'字节数\s*=\s*\d+',text))<4: problems.append('字节数绑定行不足4')
for py in root.glob('*.py'):
 s=py.read_text(encoding='utf-8')
 for b in ['OpenProcess','ReadProcessMemory','SuspendThread','StackWalk','MiniDump','CreateRemoteThread','ctypes.windll','VirtualAllocEx']:
  if b in s: problems.append(py.name+' 含禁用词 '+b)
print(json.dumps({'ok':len(problems)==0,'problems':problems,'sha256Bindings':len(binds),'docBytes':docBytes,'root':str(root)},ensure_ascii=False))