import json,random,math,os
OUT=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S08_KPROVED2\EVIDENCE'
static=['0040D250','0045A070','0045A0A0','0045A0C0','0045A640','0045A680','0045A730','0045AB00','0045AB50','0045AC00','0045AC30','0045AC70','0045AC90','004D24A0','004D2510','004D27B0','004D27D0','004D2810','004D2910']
strong=['0045A680','0045A730','0045AB50','0045AC30','004D24A0','004D2510','004D27D0','004D2810']
weak=static[:]
diff=[e for e in static if e not in strong]
N=len(static); K=len(strong); k=8
exact={'N':N,'k':k,'weak_count':len(weak),'strong_count':K,'weak_mean':len(weak)/N*k,'strong_mean':K/N*k,'weak_minus_strong_mean':(len(weak)-K)/N*k,'p_all_strong':math.comb(K,k)/math.comb(N,k) if K>=k else 0,'comb_den':math.comb(N,k)}
sims={}
for seed in [1,7,42,1337]:
 r=random.Random(seed); wm=sm=0; hits=0; trials=20000
 for _ in range(trials):
  sample=r.sample(static,k)
  w=sum(1 for e in sample if e in weak); s=sum(1 for e in sample if e in strong)
  wm+=w; sm+=s; hits += (s==k)
 sims[str(seed)]={'trials':trials,'weak_mean':wm/trials,'strong_mean':sm/trials,'all_strong_hits':hits}
res={'population':'S08 [静态推断] candidate pool','exact':exact,'simulations':sims,'weak_rows':weak,'strong_rows':strong,'weak_vs_strong_diff_rows':diff,'secondary_all_S08':{'n':22,'weak_count':22,'strong_count':11,'k':8,'weak_mean':8.0,'strong_mean':8*11/22}}
json.dump(res,open(os.path.join(OUT,'baseline.json'),'w',encoding='utf-8'),indent=2,ensure_ascii=False)
with open(os.path.join(OUT,'weak_vs_strong.tsv'),'w',encoding='utf-8') as f:
 f.write('entry\tpredicate_weak_④\tpredicate_strong_④+③b\tin_diff\n')
 for e in static:
  w=e in weak; s=e in strong
  f.write(f'{e}\t{int(w)}\t{int(s)}\t{int(w and not s)}\n')
print(json.dumps({'exact':exact,'sims':sims},indent=2,ensure_ascii=False))
