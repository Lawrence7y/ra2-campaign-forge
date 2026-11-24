import os,re,bisect
EV=r"D:\Project\ra2-campaign-forge\lead\next_re_20261116_r12\W160_aidispatch\EVIDENCE"
lines=open(os.path.join(EV,'W160_whole_text_disasm.tsv'),encoding='utf-8').read().splitlines()
D={int(l.split('\t')[0],16):l for l in lines}; S=sorted(D)
atlas=[]
with open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv",encoding='utf-8') as f:
    next(f)
    for ln in f:
        p=ln.split()
        if len(p)>=2: atlas.append((int(p[0],16),int(p[1])))
atlas.sort(); amap=dict(atlas)
arrs=['8B4118','8B410C','A83DF8','A83DEC','A8EB50','A8EB44','A8E3A0','A8E394','A8ED50','A8ED44']
targets=set()
for a in S:
    if 0x55D360<=a<0x55D360+2940:
        m=re.search(r'\tcall\t0x([0-9a-f]+)\t',D[a])
        if m: targets.add(int(m.group(1),16))
for t in sorted(targets):
    sz=amap.get(t,0x3000)
    seq=[a for a in S if t<=a<t+sz]
    hits=[D[a] for a in seq if any(x in D[a] for x in arrs)]
    sl=[D[a] for a in seq if D[a].split('\t')[1]=='call' and '+ 0x5c]' in D[a]]
    if hits or sl: print(f'{t:08X} size={sz} arrays={len(hits)} 5c={len(sl)}')
