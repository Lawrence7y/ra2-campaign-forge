import os,re,json
root=r'D:\Project\ra2-campaign-forge'
OUT=os.path.join(root,'lead','next_re_20261117_r14','S21_KPROVED2')
c=json.load(open(os.path.join(OUT,'work','candidates.json'),encoding='utf-8'))
st=[r for r in c['rows'] if r['grade']=='[静态推断]']
hits={r['entry']:[] for r in st}
pat=re.compile(r'(?:CALL|JMP_THIS|VEE)\s*\(\s*0x([0-9A-Fa-f]{8})\s*\)')
# also plain 8-hex addresses in YRpp source text
for d in ['YRpp','ref\\yrpp']:
 p=os.path.join(root,d)
 for dp,dn,fn in os.walk(p):
  for f in fn:
   if not f.lower().endswith(('.h','.cpp','.hpp','.c','.txt','.md')): continue
   try: t=open(os.path.join(dp,f),encoding='utf-8',errors='ignore').read()
   except: continue
   for m in pat.finditer(t):
    k=m.group(1).upper()
    if k in hits: hits[k].append(os.path.relpath(os.path.join(dp,f),root)+':'+t[:m.start()].count('\n')+1)
json.dump(hits,open(os.path.join(OUT,'EVIDENCE','yrpp_bindings.json'),'w',encoding='utf-8'),indent=2,ensure_ascii=False)
for k,v in hits.items():
 if v: print(k,v[:3])
print('rows with YRpp binding',sum(1 for v in hits.values() if v))
