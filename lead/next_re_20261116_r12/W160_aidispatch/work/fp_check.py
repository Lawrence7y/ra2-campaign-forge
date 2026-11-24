import json,os,bisect
EV=r"D:\Project\ra2-campaign-forge\lead\next_re_20261116_r12\W160_aidispatch\EVIDENCE"
r=json.load(open(os.path.join(EV,'W160_Q1_channelA.json'),encoding='utf-8'))
atlas=[]
with open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv",encoding="utf-8") as f:
    next(f)
    for ln in f:
        p=ln.split()
        if len(p)>=2: atlas.append((int(p[0],16),int(p[1])))
atlas.sort(); starts=[a for a,s in atlas]
for target in [0x617641,0x61CC5C,0x785132,0x7852CF]:
    i=bisect.bisect_right(starts,target)-1
    a,s=atlas[i]
    print(f'{target:08X}: nearest atlas entry {a:08X} size={s} delta={target-a} inside={target<a+s}')
    h=[x for x in r['raw_hits'] if int(x['va'],16)==target][0]
    print('  ',h)
