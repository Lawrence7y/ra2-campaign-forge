# -*- coding: utf-8 -*-
"""R210 c7: 260 张额外视图（mdisp!=0）全量形态分类 T / S / I / 其它，并给每类的 mdisp 集合。
订正记要：R209 的「101 张额外视图」实为「101 张 T 形态表」；额外视图总数 260。
"""
import sys,struct,json,collections
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
fails=[];NA=0
def ck(n,c,d=''):
    global NA;NA+=1
    if not c: fails.append(n)
    print(('PASS ' if c else 'FAIL ')+n+((' | '+str(d)) if d!='' else ''))
d3=json.load(open('/home/t628/projects/ra2-campaign-forge/_r209/q3.json'))
TH={int(k,16):v for k,v in d3['thunk'].items()}
VT={int(k,16):[int(x,16) for x in v] for k,v in d3['vt'].items()}
MD={int(k,16):v for k,v in d3['mdisp'].items()}
NM={int(k,16):v for k,v in d3['names'].items()}
VO={int(k,16):int(v,16) for k,v in d3['vt_of'].items()}
S={0x410590:'S1',0x410580:'S2',0x6d1770:'S3'}
I={0x41bc30,0x522a60,0x746100}
extra=[c for c in MD if MD[c]!=0]
ck('Y0 额外视图总数 = 260', len(extra)==260, len(extra))
def form(c):
    t=VT[c]
    if any(v in TH for v in t[:3]): return 'T'
    if len(t)==1 and t[0] in S: return 'S'+S[t[0]][1]
    if t and t[0] in I: return 'I'
    return 'X'
FOR={c:form(c) for c in extra}
cnt=collections.Counter(FOR.values())
print('# 形态分布：',cnt.most_common())
ck('Y1 T=101', cnt['T']==101, cnt['T'])
ck('Y2 S 合计=156', cnt['S1']+cnt['S2']+cnt['S3']==156, (cnt['S1'],cnt['S2'],cnt['S3']))
ck('Y3 I=3', cnt['I']==3, cnt['I'])
ck('Y4 其它(X)=0', cnt['X']==0, cnt['X'])
cls=collections.defaultdict(lambda: collections.defaultdict(set))
for c in MD: cls[P.dw(c+16)][MD[c]].add(FOR.get(c,'main'))
for p,v in cls.items():
    if len(v)>1: cls[p]=v
withmulti={p:v for p,v in cls.items() if len(v)>1}
ck('Y5 有额外视图的类数', len(withmulti)>=91, len(withmulti))
# 每类 mdisp -> 形态
pat=collections.Counter()
for p,v in withmulti.items():
    sig=tuple(sorted((m,tuple(sorted(fs))) for m,fs in v.items() if m!=0))
    pat[sig]+=1
print('# 类的视图形态签名 top10：')
for sig,n in pat.most_common(10): print('   n=%-3d %s'%(n,sig))
# T 形态的类
tcls={p for p,v in withmulti.items() if any('T' in fs for m,fs in v.items() if m!=0)}
ck('Y6 有 T 形态视图的类 = 91', len(tcls)==91, len(tcls))
json.dump(dict(form={hex(c):FOR[c] for c in extra},
               cls={hex(p):{str(m):sorted(fs) for m,fs in v.items()} for p,v in withmulti.items()},
               cnt=dict(cnt), pat=[[str(s),n] for s,n in pat.most_common()]),
          open('/home/t628/projects/ra2-campaign-forge/_r210/c7.json','w'),indent=0)
print('FAILS',fails)
