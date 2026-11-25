import json, re, bisect, os, collections
OBJ='/tmp/hy4_objd.txt'
A2='lead/next_re_20261117_r14/D41_SUBST/_audit/EVIDENCE/a2_sites.json'
pat=re.compile(r'^\s*([0-9a-fA-F]{6,8}):\s')
starts=set(); nlines=0
with open(OBJ,encoding='utf-8',errors='replace') as f:
    for line in f:
        nlines+=1
        m=pat.match(line)
        if m: starts.add(int(m.group(1),16))
sl=sorted(starts)
d=json.load(open(A2,encoding='utf-8'))
bounds=[int(x,16) for x in d['bounds']]
boundset=set(bounds)
hit=boundset & starts
miss=[a for a in bounds if a not in starts]
print('B1 objdump_lines=',nlines,'starts_total=',len(starts),'min=',hex(sl[0]),'max=',hex(sl[-1]))
print('B2 bounds_n=',len(bounds),'bounds_unique=',len(boundset),'hit=',len(hit),'miss=',len(miss),
      'hit_pct=%.6f'%(100*len(hit)/len(bounds)),'miss_pct=%.6f'%(100*len(miss)/len(bounds)))
# B3 misses with previous instruction start and delta
rows=[]
for a in sorted(set(miss)):
    i=bisect.bisect_left(sl,a)
    prev=sl[i-1] if i>0 else None
    nxt=sl[i] if i<len(sl) else None
    rows.append({'addr':a,'prev':prev,'prev_delta':(a-prev) if prev else None,
                 'next':nxt,'next_delta':(nxt-a) if nxt else None})
print('B3 miss_unique=',len(rows))
for r in rows[:100]: print('  ',hex(r['addr']),'prev=',hex(r['prev']) if r['prev'] else None,'delta=',r['prev_delta'],'next=',hex(r['next']),'nextdelta=',r['next_delta'])
# distribution of delta
print('B3 delta histogram=',dict(collections.Counter(r['prev_delta'] for r in rows)))
# B5 controls
cut=[a for a in bounds if a<0x600000]
cuthit=sum(1 for a in cut if a in starts)
plus=[a+4 for a in bounds]
plushit=sum(1 for a in plus if a in starts)
print('B5a cut<0x600000 n=',len(cut),'hit=',cuthit,'pct=%.6f'%(100*cuthit/len(cut)))
print('B5b +4 n=',len(plus),'hit=',plushit,'pct=%.6f'%(100*plushit/len(plus)))
# extra: check whether bounds max/min within .text and data coverage
print('B_extra bounds_min=',hex(min(bounds)),'bounds_max=',hex(max(bounds)))
# raw start address count from objdump line regex independent check
json.dump({'starts_n':len(starts),'hit':len(hit),'miss':len(miss),
           'miss_rows':[{'addr':hex(x['addr']),'prev':hex(x['prev']) if x['prev'] else None,'prev_delta':x['prev_delta']} for x in rows],
           'delta_hist':{str(k):v for k,v in collections.Counter(r['prev_delta'] for r in rows).items()},
           'b5a':{'n':len(cut),'hit':cuthit},'b5b':{'n':len(plus),'hit':plushit}},
          open('_r136/sub_hy4/hy4_b.json','w'),ensure_ascii=False,indent=1)
