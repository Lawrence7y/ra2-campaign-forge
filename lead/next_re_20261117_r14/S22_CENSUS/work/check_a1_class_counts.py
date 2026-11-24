import sys, collections
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
exec(open(r'D:/Project/ra2-campaign-forge/lead/next_re_20261117_r14/S22_CENSUS/work/explore_channels.py',encoding='utf-8').read().split("print('channel hits:'")[0])
cls=collections.Counter()
for r in targets:
 e=int(r[0],16)
 if e in slot_to_members:
  cls[slot_to_members[e][0]['cls']]+=1
print('distinct classes A1',len(cls))
for k,v in cls.most_common(80): print(v,k)
