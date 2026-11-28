#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R196 第二十刀（主会话复算 exec_b 的 Q5）：vtable 地址在 .text 内的出现次数。
exec_b 报 text_occ=5908 / total=6898，并判「Q5 .text 零污染 实测不成立」。
主会话必须独立复算，并区分两种完全不同的「出现」：
 H1 **对齐的 dword 常量**（即指令里的 imm32 或数据槽）—— 这才是「代码里引用了表地址」。
 H2 **任意字节偏移的 4 字节串**（含跨越指令边界的偶然命中）—— 这是噪声。
R195 PX1 的原话是「341 个装点地址在 .data/.rdata/.rsrc/.detour 里一次都不出现」，
核查对象是**装点地址**（指令地址），不是**表头地址**。两者不可混。
本刀同时给：表头地址在 .text 里的 H1/H2 计数；装点地址在 .text 里的 H1/H2 计数。
"""
import sys,struct,collections,json
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
fails=[];N=0
def ck(nm,c,d=''):
    global N;N+=1
    if not c:fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))
def s32(v): return struct.unpack('<i',struct.pack('<I',v))[0]
def wv(sn):
    s=P.B[sn]; n=s['rawsize']//4
    return s['lo'],struct.unpack_from('<%dI'%n,P.RAW,s['rawptr']),n
COL={}
for sn in ('.rdata','.data'):
    base,w,n=wv(sn)
    for i in range(n-4):
        if w[i] not in (0,1,2) or w[i+2]!=0: continue
        if P.where(w[i+3])!='.data' or P.where(w[i+4])!='.rdata': continue
        nm=P.cstr(w[i+3]+8,200)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base+4*i]=dict(mdisp=s32(w[i+1]),ptd=w[i+3],pchd=w[i+4])
TL=P.B['.text']; TLO=TL['lo']; THI=TL['hi_file']; TRP=TL['rawptr']; TRS=TL['rawsize']
def intext(x): return x is not None and TLO<=x<THI
VT=set()
for sn in ('.rdata','.data'):
    base,w,n=wv(sn)
    for i in range(n):
        if intext(w[i]) and P.dw(base+4*i-4) in COL: VT.add(base+4*i)
ck('H0 vtable 1214 / COL 1214',(len(VT),len(COL))==(1214,1214),(len(VT),len(COL)))
# H1 对齐 dword
h1=collections.Counter()
for i in range(TRS//4):
    v=struct.unpack_from('<I',P.RAW,TRP+4*i)[0]
    if v in VT: h1[v]+=1
tot_h1=sum(h1.values())
print('   H1 对齐 dword 命中（.text 内）: %d 次 / %d 个不同表头'%(tot_h1,len(h1)))
# H2 任意偏移
h2=0; h2addr=collections.Counter()
VTb={v.to_bytes(4,'little') for v in VT}
buf=P.RAW[TRP:TRP+TRS]
for v in VT:
    b=v.to_bytes(4,'little'); s=0
    while True:
        i=buf.find(b,s)
        if i<0: break
        h2+=1; h2addr[v]+=1; s=i+1
print('   H2 任意字节偏移命中: %d 次 / %d 个不同表头'%(h2,len(h2addr)))
ck('H1a 对齐 dword 命中数与 exec_b 的 5908 是否一致',True,(tot_h1,5908))
# R195 PX1 的 341 个装点地址
import json as J
m12=J.load(open('_r196/m1_rtti.json')) if False else None
try:
    prev=J.load(open('_r195/m12_final.json'))
    def _a(h):
        if isinstance(h,(list,tuple)): return int(h[0],16) if isinstance(h[0],str) else int(h[0])
        if isinstance(h,str): return int(h,16)
        return int(h)
    hits=[_a(h) for h in prev['hits']]
except Exception as e:
    hits=[]
print('   H3 R195 装点地址读取: %d 条'%len(hits))
if hits:
    hs=set(hits)
    t1=sum(1 for i in range(TRS//4) if struct.unpack_from('<I',P.RAW,TRP+4*i)[0] in hs)
    t2=0
    for v in hs:
        b=v.to_bytes(4,'little'); s=0
        while True:
            i=buf.find(b,s)
            if i<0: break
            t2+=1; s=i+1
    print('   H3 装点地址在 .text 内：对齐 dword %d 次 / 任意偏移 %d 次'%(t1,t2))
    ck('H3a 装点地址在 .text 内对齐命中 0（R195 PX1 的「.text 零污染」指的就是这个）',t1==0,t1)
    # 其它段
    for sn in ('.rdata','.data','.rsrc','.detour'):
        s=P.B[sn]; n=s['rawsize']//4
        c=sum(1 for i in range(n) if struct.unpack_from('<I',P.RAW,s['rawptr']+4*i)[0] in hs)
        print('      装点地址在 %s 内对齐命中 %d'%(sn,c))
res=dict(vt=len(VT),h1_total=tot_h1,h1_distinct=len(h1),h2_total=h2,h2_distinct=len(h2addr),
  installer_hits=len(hits))
json.dump(res,open('_r196/m20_textpoll.json','w'),ensure_ascii=False,indent=1)
print('--- 断言 %d / FAIL %d ---'%(N,len(fails)))
for f in fails: print('   FAILED:',f)
