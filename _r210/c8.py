# -*- coding: utf-8 -*-
"""R210 c8: 律 W —— 额外视图偏移决定形态（mdisp -> form 交叉表）；76 个 (0,4,8,12) 家族的类名链；
S/I 三个静态表的完整函数体与直接 call/jmp 引用数。
防 OOM：只对 3 个地址单独反汇编。
"""
import sys,struct,json,collections
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
md=Cs(CS_ARCH_X86,CS_MODE_32)
fails=[];NA=0
def ck(n,c,d=''):
    global NA;NA+=1
    if not c: fails.append(n)
    print(('PASS ' if c else 'FAIL ')+n+((' | '+str(d)) if d!='' else ''))
d7=json.load(open('/home/t628/projects/ra2-campaign-forge/_r210/c7.json'))
FORM={int(k,16):v for k,v in d7['form'].items()}
d3=json.load(open('/home/t628/projects/ra2-campaign-forge/_r209/q3.json'))
VT={int(k,16):[int(x,16) for x in v] for k,v in d3['vt'].items()}
MD={int(k,16):v for k,v in d3['mdisp'].items()}
NM={int(k,16):v for k,v in d3['names'].items()}
tab=collections.defaultdict(collections.Counter)
for c,f in FORM.items(): tab[MD[c]][f]+=1
print('# mdisp -> form 交叉表：')
for m in sorted(tab):
    print('   mdisp=%-6d n=%-4d %s'%(m,sum(tab[m].values()),dict(tab[m])))
ck('Z1 mdisp=4 全部为 T（91 张）', sum(tab[4].values())==91 and set(tab[4])=={'T'}, dict(tab[4]))
ck('Z2 mdisp=12 全部为 S1（78）', sum(tab[12].values())==78 and set(tab[12])=={'S1'}, dict(tab[12]))
ck('Z3 mdisp=8 只有 S2/I 两种（合计 78 = S2 75 + I 3）', sum(tab[8].values())==78 and set(tab[8])<={'S2','I'}, dict(tab[8]))
ck('Z4 mdisp=24 全部为 T（6）', sum(tab[24].values())==6 and set(tab[24])=={'T'}, dict(tab[24]))
ck('Z5 mdisp=21784 全部为 S3（3）', sum(tab[21784].values())==3 and set(tab[21784])=={'S3'}, dict(tab[21784]))
ck('Z6 36/40/44/1728 全为 T', all(set(tab[m])=={'T'} for m in (36,40,44,1728)), {m:dict(tab[m]) for m in (36,40,44,1728)})
# 76 家族
cls=collections.defaultdict(dict)
for c in MD: cls[P.dw(c+16)][MD[c]]=c
fam76=[p for p,v in cls.items() if set(v)=={0,4,8,12}]
ck('Z7 (0,4,8,12) 四视图类数', len(fam76)>=70, len(fam76))
nm=[NM[cls[p][0]] for p in fam76]
suf=collections.Counter(n.split('@@')[0][-6:] for n in nm)
print('# 76 家族类名后缀 top12：',suf.most_common(12))
print('# 76 家族样例：',sorted(nm)[:12])
# S/I 表体与直接引用
TE=P.B['.text']; TB=P.RAW[TE['rawptr']:TE['rawptr']+TE['rawsize']]; BASE=TE['lo']
def body(a,cap=400):
    o=P.r2o(a); out=[]
    for i in md.disasm(P.RAW[o:o+cap],a):
        out.append((i.address,i.mnemonic,i.op_str))
        if i.mnemonic=='ret': break
    return out
def direct_refs(target):
    cs=ej=0
    for m,pat,ln in (('call',b'\xe8',5),('jmp',b'\xe9',5)):
        i=0
        while True:
            i=TB.find(pat,i)
            if i<0: break
            rel=struct.unpack_from('<i',TB,i+1)[0]
            if (BASE+i+5+rel)&0xffffffff==target:
                if m=='call': cs+=1
                else: ej+=1
            i+=1
    return cs,ej
for a,label in ((0x410580,'S2'),(0x410590,'S1'),(0x6d1770,'S3')):
    b=body(a)
    print('==== %08x %s ninsn=%d'%(a,label,len(b)))
    for x in b: print('   %08x %-10s %s'%x)
    c_,j_=direct_refs(a)
    print('   直接 call=%d  jmp=%d'%(c_,j_))
    # 反控
    c2,j2=direct_refs(0x4c9150)
    print('   反控 0x4c9150 call=%d jmp=%d'%(c2,j2))
json.dump(dict(tab={str(m):dict(v) for m,v in tab.items()},
               fam76=sorted(nm), n_fam=len(fam76)),
          open('/home/t628/projects/ra2-campaign-forge/_r210/c8.json','w'),indent=0,ensure_ascii=False)
print('FAILS',fails)
