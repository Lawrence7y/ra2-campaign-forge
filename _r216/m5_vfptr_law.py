# -*- coding: utf-8 -*-
"""R216 m5：律 T 全域检验——.text 中『mov dword ptr [reg+off], <视图基址>』的 off 是否恒等于该视图的 mdisp。
字节口径：C7 /0（mov r/m32, imm32）+ 8B8?（mov r32, imm32 不算）; 另扫 0xB8..0xBF 的 imm32 引用（修正 m3 的 IID 扫描漏 mov edi）。
正控：0x4105a0 的 4 条写入必须命中且 off=0/4/8/12 对应 mdisp 0/4/8/12。
反控：把视图基址表整体 +4 再扫，命中数必须为 0（判据非常量）。"""
import sys,struct,json,collections
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
def s32(v): return struct.unpack('<i',v)[0] if isinstance(v,(bytes,bytearray)) else struct.unpack('<i',struct.pack('<I',v&0xffffffff))[0]
def words(sn):
    s=P.B[sn];nn=s['rawsize']//4
    return struct.unpack_from('<%dI'%nn,P.RAW,s['rawptr']),s['lo']
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
    VIEWS.append(dict(col=S2C[st],base=st,slots=sl,mdisp=md_,nm=nm[1:] if nm.startswith('.') else nm))
VB={v['base']:v for v in VIEWS}
t=P.B['.text']; tb=P.RAW[t['rawptr']:t['rawptr']+t['rawsize']]; base=t['lo']
print('view bases=%d'%len(VB))
def scan(vbset):
    hits=[]
    n=len(tb)
    for k in range(n-6):
        if tb[k]!=0xc7: continue
        m=tb[k+1]
        mod=m>>6; reg=(m>>3)&7; rm=m&7
        if reg!=0 or rm==4: continue
        if mod==0:
            off=0; io=k+2
            # mod=00 rm=101 => disp32 (absolute), skip
            if rm==5: continue
        elif mod==1:
            off=s32(struct.pack('<i',tb[k+2] if tb[k+2]<0x80 else tb[k+2]-256)); io=k+3
        elif mod==2:
            off=s32(tb[k+2:k+6]); io=k+6
        else: continue
        if io+4>n: continue
        imm=struct.unpack_from('<I',tb,io)[0]
        if imm in vbset:
            hits.append((base+k,off,imm))
    return hits
hits=scan(VB)
print('=== 律 T 命中=%d ==='%len(hits))
ok=bad=0; badlist=[]; perclass=collections.defaultdict(list)
for a,off,imm in hits:
    v=VB[imm]
    if off==v['mdisp']: ok+=1
    else:
        bad+=1; badlist.append((a,off,imm,v['mdisp'],v['nm']))
    perclass[v['nm']].append((off,v['mdisp']))
print('  off==mdisp : %d ; off!=mdisp : %d'%(ok,bad))
print('  违例 top20:',[('0x%08x'%a,o,'0x%08x'%im,d,nm) for a,o,im,d,nm in badlist[:20]])
print('  命中按类 top15:',sorted(((len(v),k) for k,v in perclass.items()),reverse=True)[:15])
# 正控
pc=[h for h in hits if 0x4105a0<=h[0]<0x4105d3]
print('  [正控] 0x4105a0 体内命中=%d 明细=%s'%(len(pc),[(hex(a),o,hex(i)) for a,o,i in pc]))
assert len(pc)==4 and sorted(o for a,o,i in pc)==[0,4,8,12], 'POSITIVE CONTROL FAIL'
# 反控
sh={(b+4):v for b,v in VB.items()}
neg=scan(sh)
print('  [反控] 视图基址整体+4 后命中=%d'%len(neg))
assert len(neg)==0,'NEGATIVE CONTROL FAIL'
# mdisp 分布
md=collections.Counter(v['mdisp'] for v in VIEWS)
print('=== mdisp 分布 top15 ===',md.most_common(15))
print('  mdisp%4!=0 的视图数=%d'%sum(1 for v in VIEWS if v['mdisp']%4))
# 每个类内 mdisp 是否含 0
byname=collections.defaultdict(set)
for v in VIEWS: byname[v['nm']].add(v['mdisp'])
nozero=[(k,sorted(s)) for k,s in byname.items() if 0 not in s]
print('=== 无 mdisp=0 主视图的类=%d ==='%len(nozero))
for k,s in nozero[:10]: print('   ',k,s)
multi=[(k,sorted(s)) for k,s in byname.items() if len(s)>1]
print('=== 多视图类=%d ; 前12 mdisp 集合 ==='%len(multi))
for k,s in sorted(multi,key=lambda t:-len(t[1]))[:12]: print('   %-34s %s'%(k,s))
json.dump({'law_hits':len(hits),'ok':ok,'bad':bad,'badlist':[['0x%08x'%a,o,'0x%08x'%i,d,nm] for a,o,i,d,nm in badlist[:50]],
 'perclass':{k:len(v) for k,v in perclass.items()},'mdisp_dist':dict(md),
 'nozero':len(nozero),'multi_n':len(multi)},
 open('/home/t628/projects/ra2-campaign-forge/_r216/m5.json','w'),indent=1)
