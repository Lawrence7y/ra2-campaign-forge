# -*- coding: utf-8 -*-
"""R215 m14b：修正 m14 的 owner 判定 bug。
m14 的『向前找填充后的地址』在命中点前无填充时退化为 cand==A 自身，导致 931 个"函数"（恒真）。
改法：把「已知 vftable 槽目标集合」当函数起点字典，对位点 A 取 max{ f in SLOTSET : f <= A } 作为所属函数
      （并记录距离；距离 >4096 的标 unreachable）。
"""
import sys,struct,json,collections,bisect
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P, capstone
def s32(v): return struct.unpack('<i',struct.pack('<I',v&0xffffffff))[0]
def words(sn):
    s=P.B[sn];n=s['rawsize']//4
    return struct.unpack_from('<%dI'%n,P.RAW,s['rawptr']),s['lo']
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
    sl=[];a=st
    while a<end and P.where(P.dw(a))=='.text':
        sl.append(P.dw(a));a+=4
    md_,ptd,pchd,nm=COLA[S2C[st]]
    VIEWS.append(dict(base=st,slots=sl,mdisp=md_,nm=nm[1:] if nm.startswith('.') else nm))
POS=collections.defaultdict(collections.Counter)
for v in VIEWS:
    for i,x in enumerate(v['slots']): POS[x][i]+=1
SLOT=sorted(POS)
raw=P.RAW; t=P.B['.text']; tb=t['lo']; n=t['rawsize']; o0=t['rawptr']
m2=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); m2.skipdata=True
CH=0x10000; hits=[]
for base in range(o0,o0+n,CH):
    chunk=raw[base:min(base+CH,o0+n)]; va=tb+(base-o0)
    for a,sz,mn,op in m2.disasm_lite(chunk,va):
        if mn in ('call','jmp') and op.endswith('+ 0x48]') and ',' not in op.split('[')[0]: hits.append(a)
print('+0x48 位点=%d'%len(hits))
OWN=collections.Counter(); far=0; dist=[]
for a in hits:
    i=bisect.bisect_right(SLOT,a)-1
    if i<0: far+=1; continue
    d=a-SLOT[i]; dist.append(d)
    if d>4096: far+=1; continue
    OWN[SLOT[i]]+=1
print('归并成功位点=%d  未归并(距最近槽函数>4096B 或越界)=%d  distinct 所属函数=%d'%(sum(OWN.values()),far,len(OWN)))
print('距离分布: max=%d 中位=%d  >1024 的位点=%d'%(max(dist) if dist else -1,
      sorted(dist)[len(dist)//2] if dist else -1, sum(1 for d in dist if d>1024)))
by_slot=collections.Counter()
for f,c in OWN.items():
    for i,k in POS[f].items(): by_slot[i]+=c
print('按槽号（所属函数被放的位置）聚合 +0x48 消费位点:',dict(sorted(by_slot.items())))
print('=== top20 消费函数 ===')
for f,c in OWN.most_common(20):
    print('  0x%08x 位点%2d 作为槽值位置=%s'%(f,c,dict(sorted(POS[f].items()))))
# slot18 组默认桩 0x4104f0 的消费者
print('0x4104f0(slot19默认桩) 自身消费 +0x48 =',1 if 0x4104f0 in OWN else 0,'(它体内含 1 处，见 m13)')
# 消费者按 所属函数槽号=19 的（即"转发链"）
print('消费者中身份为 slot19 槽值的位点数=%d ; slot18 槽值=%d'%(by_slot.get(19,0),by_slot.get(18,0)))
json.dump({'hits':len(hits),'owned':sum(OWN.values()),'far':far,'funcs':len(OWN),
 'by_slot':dict(sorted(by_slot.items())),
 'top':[['0x%08x'%f,c] for f,c in OWN.most_common(40)]},
 open('/home/t628/projects/ra2-campaign-forge/_r215/m14b.json','w'),indent=1)
