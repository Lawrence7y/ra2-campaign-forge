# -*- coding: utf-8 -*-
"""R215 m8：修正 m7 的恒真断言，改测『组内逐槽 distinct』——slot18 是否是该组唯一未被覆写的槽。
同时：对每组找"最可能的基类"（槽数最少且在前 18 槽里未出现于派生差异的类），逐槽比对其自身视图。
"""
import sys,struct,json,collections
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
def s32(v): return struct.unpack('<i',struct.pack('<I',v&0xffffffff))[0]
def words(sn):
    s=P.B[sn]; n=s['rawsize']//4
    return struct.unpack_from('<%dI'%n,P.RAW,s['rawptr']), s['lo']
COLA={}
for sn in ('.rdata','.data'):
    w,base=words(sn)
    for k in range(len(w)-4):
        if w[k]>2 or w[k+2]!=0: continue
        if P.where(w[k+3])!='.data' or P.where(w[k+4])!='.rdata': continue
        nm=P.cstr(w[k+3]+8,512)
        if not nm or nm[:3]!=b'.?A' or nm[-2:]!=b'@@': continue
        COLA[base+4*k]=(s32(w[k+1]),w[k+3],w[k+4],nm.decode('latin1'))
PRE=collections.defaultdict(list)
for sn in ('.rdata','.data'):
    w,base=words(sn)
    for k in range(len(w)-1):
        if w[k] in COLA and P.where(w[k+1])=='.text': PRE[w[k]].append(base+4*k)
starts=sorted(min(v)+4 for v in PRE.values() if len(v)==1)
S2C={min(v)+4:c for c,v in PRE.items() if len(v)==1}
VIEWS=[]
for i,st in enumerate(starts):
    end=starts[i+1] if i+1<len(starts) else P.B['.rdata']['hi_file']
    sl=[]; a=st
    while a<end and P.where(P.dw(a))=='.text':
        sl.append(P.dw(a)); a+=4
    md_,ptd,pchd,nm=COLA[S2C[st]]
    VIEWS.append(dict(col=S2C[st],base=st,slots=sl,mdisp=md_,nm=nm[1:] if nm.startswith('.') else nm))
h18=[v for v in VIEWS if len(v['slots'])>18]
c18=collections.Counter(v['slots'][18] for v in h18)
OUT={}
print('=== 组内逐槽 distinct（槽 0..20）：slot18 是否唯一未被覆写 ===')
for T,n in c18.most_common(9):
    grp=[v for v in h18 if v['slots'][18]==T]
    m=min(len(v['slots']) for v in grp)
    per={}
    for i in range(min(m,21)):
        per[i]=len(set(v['slots'][i] for v in grp))
    others=[per[i] for i in per if i!=18]
    ismin = per.get(18,99)==min(list(per.values()))
    nmin = sum(1 for i in per if per[i]==per.get(18,99))
    print('0x%08x 视图%2d 共同槽数=%3d | slot18 distinct=1 | 其他20槽 distinct 范围=%d..%d 均值%.1f | 18 是否为最少=%s (%d 个槽并列)'%(
        T,len(grp),m,min(others),max(others),sum(others)/len(others),ismin,nmin))
    print('   per-slot:',{i:per[i] for i in sorted(per)})
    OUT['0x%08x'%T]=dict(n=len(grp),per=per,ismin=ismin,nmin=nmin)
    # 若 m<=21 之外，补充 21..min(m,60)
    if m>21:
        per2={i:len(set(v['slots'][i] for v in grp)) for i in range(21,min(m,121))}
        one=[i for i,vv in per2.items() if vv==1]
        print('   槽21..%d 中 distinct==1 的槽号: %s'%(min(m,121)-1,one[:20]))
        OUT['0x%08x'%T]['tail_single']=one
print()
print('=== 参照：同样算法跑在 slot17 / slot19 组上（反控） ===')
for idx in (17,19):
    c=collections.Counter(v['slots'][idx] for v in VIEWS if len(v['slots'])>idx)
    T,n=c.most_common(1)[0]
    grp=[v for v in VIEWS if len(v['slots'])>idx and v['slots'][idx]==T]
    m=min(len(v['slots']) for v in grp)
    per={i:len(set(v['slots'][i] for v in grp)) for i in range(min(m,21))}
    print('slot%d top 0x%08x 视图%d per-slot=%s'%(idx,T,len(grp),{i:per[i] for i in sorted(per)}))
json.dump(OUT,open('/home/t628/projects/ra2-campaign-forge/_r215/m8.json','w'),indent=1)
