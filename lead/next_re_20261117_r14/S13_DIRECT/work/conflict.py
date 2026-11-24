import sys,io,os,json,re
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8',errors='replace')
d=json.load(open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13_DIRECT\EVIDENCE\direct_analysis.json',encoding='utf-8'))
entries=[x['entry'] for x in d['results']]
eset=set(entries)
# source files
sources=[]
def walk(root,exts):
    out=[]
    for dp,dn,fn in os.walk(root):
        for f in fn:
            if any(f.lower().endswith(e) for e in exts): out.append(os.path.join(dp,f))
    return out
roots=[r'D:\Project\ra2-campaign-forge\docs\re',r'D:\Project\ra2-campaign-forge\re_atlas\kb',r'D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md',r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE']
for root in roots:
    if os.path.isfile(root): sources.append(root)
    elif os.path.isdir(root): sources+=walk(root,['.md','.tsv','.txt','.json'])
print('source files',len(sources))
# find lines containing any entry (word boundary, case-insensitive)
pat=re.compile(r'(?<!\w)('+'|'.join(eset)+r')(?!\w)',re.I)
hits={e:[] for e in entries}
for fp in sources:
    try:
        txt=open(fp,'r',encoding='utf-8',errors='replace').read()
    except: continue
    for ln in txt.split('\n'):
        m=pat.search(ln)
        if m:
            e=m.group(1).upper()
            if e in hits and len(hits[e])<10:
                hits[e].append({'file':fp.replace(r'D:\Project\ra2-campaign-forge\\',''),'line':ln.strip()[:180]})
n_hit=sum(1 for e in entries if hits[e])
print('entries with external textual hits:',n_hit,'/',len(entries))
# save
with open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13_DIRECT\EVIDENCE\conflict_scan.json','w',encoding='utf-8') as f:
    json.dump(hits,f,ensure_ascii=False,indent=1)
# print a few
for e in entries:
    if hits[e]:
        print('==',e)
        for h in hits[e][:3]: print('  ',h['file'],'::',h['line'])
