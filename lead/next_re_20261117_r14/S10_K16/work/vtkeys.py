import sys,os,json,collections
sys.path.insert(0,os.path.dirname(__file__)); import common
v=common.vtable_info(); print('n',len(v)); c=collections.Counter(x.get('class','?') for x in v)
for k,n in c.most_common(60): print(n,repr(k))
