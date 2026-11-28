# -*- coding: utf-8 -*-
"""R208 m10：残留 3 条非 thunk 且非共享的额外视图定性 + 三张共享小表的桩函数字节核验 + 组成员全名单。
正控：三组（78/75/3）的类名单与 mdisp、桩地址反汇编
反控：把三组桩地址换成组外随机 .text 地址，形态判据应不再成立
"""
import sys,struct,collections,json
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
def s32(v): return struct.unpack('<i',struct.pack('<I',v))[0]
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
    try: return (i0.mnemonic,int(op.split(',')[-1],16),i1.op_str.strip())
    except Exception: return None
emb={a:a+16 for a in CHD}
extras=[c for c in COL if c!=emb[COL[c]['pCHD']]]
groups=collections.defaultdict(list)
for c,a in A.items(): groups[a].append(c)
dup={c for a,cl in groups.items() if len(cl)>1 for c in cl}
resid=[c for c in extras if not adj(A[c][0]) and c not in dup]
print('== A 残留（非 thunk 且不共享）%d 条 ==' % len(resid))
for c in resid:
    print('   0x%x %-40s mdisp=%-6d 数组长度=%d slot0=0x%x' % (c,COL[c]['name'],COL[c]['mdisp'],len(A[c]),A[c][0]))
    o=P.r2o(A[c][0]); ins=list(md.disasm(P.RAW[o:o+32],A[c][0]))[:6]
    print('      slot0 反汇编: %s' % '; '.join('%s %s'%(i.mnemonic,i.op_str) for i in ins))
    print('      slot0 原始字节: %s' % P.RAW[o:o+16].hex())
print('== B 三张共享小表 ==')
for a,cl in sorted(((a,cl) for a,cl in groups.items() if len(cl)>2),key=lambda x:-len(x[1])):
    print('  组 %d 条 长度 %d slot0=0x%x mdisp %s' % (len(cl),len(a),a[0],collections.Counter(COL[c]['mdisp'] for c in cl).most_common()))
    o=P.r2o(a[0]); ins=list(md.disasm(P.RAW[o:o+24],a[0]))[:4]
    print('     slot0 字节 %s → %s' % (P.RAW[o:o+10].hex(),'; '.join('%s %s'%(i.mnemonic,i.op_str) for i in ins)))
    if len(a)>1:
        o2=P.r2o(a[1]); ins2=list(md.disasm(P.RAW[o2:o2+24],a[1]))[:4]
        print('     slot1 字节 %s → %s' % (P.RAW[o2:o2+10].hex(),'; '.join('%s %s'%(i.mnemonic,i.op_str) for i in ins2)))
    print('     成员（%d）: %s' % (len(cl),sorted(COL[c]['name'] for c in cl)))
print('== C 反控 ==')
import random; random.seed(208)
okn=0
for _ in range(200):
    a=0x401000+random.randrange((0x7e1000-0x401000)//4)*4
    r=adj(a)
    if r: okn+=1
print('  随机 .text 地址中 adj 形态命中 %d/200（三组桩地址应 3/3 命中）' % okn)
okt=sum(1 for a,cl in groups.items() if len(cl)>2 and (a[0]==0x410590 or a[0]==0x410580 or a[0]==0x6d1770))
print('  三组桩地址命中 %d/3' % okt)
json.dump(dict(resid=[[hex(c),COL[c]['name'],COL[c]['mdisp'],len(A[c]),hex(A[c][0]),
                       P.RAW[P.r2o(A[c][0]):P.r2o(A[c][0])+16].hex()] for c in resid],
               shared=[[len(cl),[hex(c) for c in sorted(cl)],[str(k)+':'+str(v) for k,v in collections.Counter(COL[c]['mdisp'] for c in cl).most_common()],
                        [COL[c]['name'] for c in sorted(cl)]] for a,cl in sorted(((a,cl) for a,cl in groups.items() if len(cl)>2),key=lambda x:-len(x[1]))],
               ctrl=[okn,200]),
          open('_r208/m10_resid.json','w'),ensure_ascii=False,indent=1)
