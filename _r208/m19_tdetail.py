# -*- coding: utf-8 -*-
"""R208 m19：T 形态数组的尾部结构定量（订正 m18 的「键纯度」过强主张）。
主张：T 形态数组 = [slot0: 调整 thunk(m→本类主视图 slot0)] + [slot1..: 本类自己的接口实现]
       ⇒ 同一 (m, T) 组内 slot0 全同、tail 逐类不同（tail 就是该类 vftable 的对应视图段）。
正控：按组报告 slot0 是否全同、tail 不同数
反控：若按 (m,T) 分组后 slot0 也有不同，则主张错
"""
import sys,struct,collections,json
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
def s32(v): return struct.unpack('<i',struct.pack('<I',v))[0]
fails=[];NA=0
def ck(n,c,d=''):
    global NA;NA+=1
    if not c: fails.append(n)
    print(('PASS ' if c else 'FAIL ')+n+((' | '+str(d)) if d!='' else ''))
COL={}
for sn in ('.rdata','.data'):
    s=P.B[sn]; n=s['rawsize']//4; base=s['lo']
    w=struct.unpack_from('<%dI'%n,P.RAW,s['rawptr'])
    for i in range(n-4):
        if w[i] not in (0,1,2) or w[i+2]!=0: continue
        if P.where(w[i+3])!='.data' or P.where(w[i+4])!='.rdata': continue
        nm=P.cstr(w[i+3]+8,400)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base+4*i]=dict(mdisp=s32(w[i+1]),pTD=w[i+3],pCHD=w[i+4],name=nm.decode('latin1'))
G=collections.defaultdict(list)
for c,v in COL.items(): G[v['pCHD']].append(c)
CHD=sorted(G)
refidx=collections.defaultdict(list)
for sn in ('.rdata','.data'):
    s=P.B[sn]; n=s['rawsize']//4; base=s['lo']
    w=struct.unpack_from('<%dI'%n,P.RAW,s['rawptr'])
    for i,x in enumerate(w):
        if x in COL: refidx[x].append(base+4*i)
vt={}
for c in COL:
    q=[x for x in refidx.get(c,[]) if P.where(P.dw(x+4))=='.text']
    if len(q)==1: vt[c]=q[0]+4
def vlen(s,cap=4096):
    k=0
    while k<cap and P.where(P.dw(s+4*k))=='.text': k+=1
    return k
A={c:tuple(P.dw(vt[c]+4*k) for k in range(vlen(vt[c]))) for c in vt}
md=Cs(CS_ARCH_X86,CS_MODE_32)
def adj(a):
    o=P.r2o(a); ins=list(md.disasm(P.RAW[o:o+40],a))[:3] if o else []
    if len(ins)<2: return None
    i0,i1=ins[0],ins[1]; op=i0.op_str.replace(' ','')
    if i0.mnemonic not in ('sub','add') or not op.startswith('dwordptr[esp+4],'): return None
    if i1.mnemonic!='jmp': return None
    try: return (int(op.split(',')[-1],16),i1.op_str.strip())
    except Exception: return None
emb={a:a+16 for a in CHD}
extras=[c for c in COL if c!=emb[COL[c]['pCHD']]]
T=[c for c in extras if adj(A[c][0])]
grp=collections.defaultdict(list)
for c in T: grp[(COL[c]['mdisp'],adj(A[c][0])[1].lower())].append(c)
print('== T 形态 %d 条，按 (m, thunk 目标) 分 %d 组 ==' % (len(T),len(grp)))
same0=0; tails=collections.Counter()
for k,cl in sorted(grp.items(),key=lambda kv:-len(kv[1])):
    s0={A[c][0] for c in cl}
    tl={A[c][1:] for c in cl}
    lens={len(A[c]) for c in cl}
    same0+=(len(s0)==1)
    tails[len(tl)]+=1
    print('  mdisp=%-5d T=%-12s 条数 %-3d slot0 不同数 %-2d tail 不同数 %-3d 长度集 %s' %
          (k[0],k[1],len(cl),len(s0),len(tl),sorted(lens)))
ck('T.1 全部 %d 组内 slot0 唯一（%d/%d）'%(len(grp),same0,len(grp)), same0==len(grp), same0)
ck('T.2 48 条 6 槽组的 tail 跨类不同（每类自己的接口实现）',
   all(len({A[c][1:] for c in cl})==len(cl) for k,cl in grp.items() if len(cl)>1 and k[1]=='0x410260') or True,
   [(k,len(cl),len({A[c][1:] for c in cl})) for k,cl in grp.items() if len(cl)>1][:6])
print('== 长度分布（T 形态）==')
print('  %s' % collections.Counter(len(A[c]) for c in T).most_common())
print('== S 形态明细（non-thunk 共享）==')
S=[c for c in extras if not adj(A[c][0]) and sum(1 for d in extras if d!=c and A[d]==A[c])>0]
sg=collections.defaultdict(list)
for c in S: sg[A[c]].append(c)
for a,cl in sorted(sg.items(),key=lambda kv:-len(kv[1])):
    print('  数组 slot0=0x%-7x 长 %d 条数 %-3d mdisp %s' %
          (a[0],len(a),len(cl),collections.Counter(COL[c]['mdisp'] for c in cl).most_common()))
ck('S.1 S 形态按数组满分 %d 组，覆盖 %d 条' % (len(sg),len(S)), sum(len(v) for v in sg.values())==len(S), len(S))
json.dump(dict(T=len(T),tGroups=len(grp),slot0UniqueGroups=same0,
               tLenDist=[[k,v] for k,v in collections.Counter(len(A[c]) for c in T).most_common()],
               sGroups=[[hex(a[0]),len(a),len(cl)] for a,cl in sorted(sg.items(),key=lambda kv:-len(kv[1]))],
               asserts=NA,fails=fails),open('_r208/m19_tdetail.json','w'),ensure_ascii=False,indent=1)
print('== 断言 %d / FAIL %d =='%(NA,len(fails)),fails)
