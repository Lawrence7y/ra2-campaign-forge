# -*- coding: utf-8 -*-
"""定位审计员报的 29580 属哪种停止口径（一次性枚举 4 种变体）。"""
import sys,struct,collections
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
def s32(v): return struct.unpack('<i',struct.pack('<I',v&0xffffffff))[0]
def words(sn):
    s=P.B[sn]; n=s['rawsize']//4
    return struct.unpack_from('<%dI'%n,P.RAW,s['rawptr']), s['lo']
COL={}
for sn in ('.rdata','.data'):
    w,base=words(sn)
    for k in range(len(w)-4):
        if w[k]>2 or w[k+2]!=0: continue
        if P.where(w[k+3])!='.data' or P.where(w[k+4])!='.rdata': continue
        nm=P.cstr(w[k+3]+8,512)
        if not nm or nm[:3]!=b'.?A' or nm[-2:]!=b'@@': continue
        COL[base+4*k]=s32(w[k+1])
PA=collections.defaultdict(list)
for sn in ('.rdata','.data'):
    w,base=words(sn)
    for k in range(len(w)-1):
        if w[k] in COL and P.where(w[k+1])=='.text': PA[w[k]].append(base+4*k)
starts=sorted(min(v)+4 for v in PA.values() if len(v)==1)
def run(mode,cap=None):
    tot=0; hist=collections.Counter()
    for i,st in enumerate(starts):
        end=starts[i+1] if i+1<len(starts) else P.B['.rdata']['hi_file']
        a=st; n=0
        while a<end and (cap is None or n<cap):
            v=P.dw(a)
            if mode=='all': ok=True
            elif mode=='nonzero': ok=bool(v)
            elif mode=='known': ok=P.where(v) not in ('None','other')
            elif mode=='nortdatadiff': ok=P.where(v)=='.text' or v==0
            if not ok: break
            n+=1; a+=4
        tot+=n; hist[n]+=1
    return tot,hist
for m in ('all','nonzero','known'):
    for cap in (None,4096):
        t,h=run(m,cap); print('mode=%-9s cap=%-5s tot=%d'%(m,cap,t))
print('\n=== 单视图超 4096 的诊断（mode=all 无 cap） ===')
for i,st in enumerate(starts):
    end=starts[i+1] if i+1<len(starts) else P.B['.rdata']['hi_file']
    n=(end-st)/4
    if n>4096: print('  start=%s gap=%d dword=%d end=%s'%(hex(st),end-st,int(n),hex(end)))
print('末视图 start=%s .rdata hi=%s gap字节=%d'%(hex(starts[-1]),hex(P.B['.rdata']['hi_file']),P.B['.rdata']['hi_file']-starts[-1]))
print('若末视图强制以 .text hi_file 收口: gap=%d dword=%d'%(P.B['.text']['hi_file']-starts[-1],(P.B['.text']['hi_file']-starts[-1])//4))
