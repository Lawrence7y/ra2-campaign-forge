# -*- coding: utf-8 -*-
"""R209 q3: thunk 在 vftable 各槽的分布 + vlen 合并风险 + 含 thunk 表的长度/形态。
"""
import sys, struct, collections, json
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
def s32(v): return struct.unpack('<i',struct.pack('<I',v&0xffffffff))[0]
TE=P.B['.text']; TB=P.RAW[TE['rawptr']:TE['rawptr']+TE['rawsize']]; BASE=TE['lo']
def scan(buf,base):
    out=[]
    for pat,kind,ecut in ((b'\x83\x6c\x24\x04','A83',5),(b'\x81\x6c\x24\x04','B81',8)):
        i=0
        while True:
            i=buf.find(pat,i)
            if i<0: break
            if i+ecut+5<=len(buf) and buf[i+ecut]==0xe9:
                imm=s32(buf[i+4]) if kind=='A83' else s32(struct.unpack_from('<I',buf,i+4)[0])
                rel=s32(struct.unpack_from('<I',buf,i+ecut+1)[0])
                out.append(dict(va=base+i,kind=kind,imm=imm,jmp=(base+i+ecut+5+rel)&0xffffffff))
            i+=1
    return out
TH={t['va']:t for t in scan(TB,BASE)}
COL={}
for sn in ('.rdata','.data'):
    s=P.B[sn]; n=s['rawsize']//4; base=s['lo']
    w=struct.unpack_from('<%dI'%n,P.RAW,s['rawptr'])
    for k in range(n-4):
        if w[k] not in (0,1,2) or w[k+2]!=0: continue
        if P.where(w[k+3])!='.data' or P.where(w[k+4])!='.rdata': continue
        nm=P.cstr(w[k+3]+8,400)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base+4*k]=dict(mdisp=s32(w[k+1]),pTD=w[k+3],pCHD=w[k+4],name=nm.decode('latin1'))
refidx=collections.defaultdict(list)
for sn in ('.rdata','.data'):
    s=P.B[sn]; n=s['rawsize']//4; base=s['lo']
    w=struct.unpack_from('<%dI'%n,P.RAW,s['rawptr'])
    for k,x in enumerate(w):
        if x in COL: refidx[x].append(base+4*k)
vt_of={}
for c in COL:
    q=[x for x in refidx.get(c,[]) if P.where(P.dw(x+4))=='.text']
    if len(q)==1: vt_of[c]=q[0]+4
def vlen(s,cap=4096):
    k=0
    while k<cap and P.where(P.dw(s+4*k))=='.text': k+=1
    return k
VT={c:tuple(P.dw(vt_of[c]+4*k) for k in range(vlen(vt_of[c]))) for c in vt_of}
print('# 表数=%d，长度分布=%s'%(len(VT), collections.Counter(len(t) for t in VT.values()).most_common()))
# 表起点是否重叠（合并风险）
starts=sorted({vt_of[c] for c in vt_of})
ov=0
for c in vt_of:
    s=vt_of[c]; e=s+4*len(VT[c])
    for s2 in starts:
        if s2>s and s2<e: ov+=1; break
print('# 表区间被更晚起点侵入的表数 = %d / %d'%(ov,len(VT)))
# 含 thunk 的表
hit=collections.defaultdict(list)   # col -> [(idx,thunkva)]
for c,t in VT.items():
    for i,v in enumerate(t):
        if v in TH: hit[c].append((i,v))
print('# 含 thunk 的表 = %d'%len(hit))
print('# 这些表的 mdisp 分布 = %s'%collections.Counter(COL[c]['mdisp'] for c in hit).most_common(10))
print('# idx 分布 = %s'%collections.Counter(i for c in hit for (i,v) in hit[c]).most_common(10))
print('# 表长度分布 = %s'%collections.Counter(len(VT[c]) for c in hit).most_common(10))
# 抽 3 个样例
for c in list(hit)[:4]:
    print('---- COL %08x %s mdisp=%d vt=%08x len=%d'%(c,COL[c]['name'],COL[c]['mdisp'],vt_of[c],len(VT[c])))
    print('     slots=%s'%[hex(v) for v in VT[c]][:12])
    print('     thunk idx=%s'%[(i,hex(v),TH[v]['imm'],hex(TH[v]['jmp'])) for i,v in hit[c]][:12])
# 全槽 thunk 命中总数与 idx 计数
allidx=collections.Counter(i for c in hit for (i,v) in hit[c])
print('\n# 全槽 thunk 出现总数 = %d，idx 明细 = %s'%(sum(allidx.values()), sorted(allidx.items())[:20]))
# 关键：mdisp=4 表 vs 其它
for md_ in sorted({COL[c]['mdisp'] for c in hit}):
    sub=[c for c in hit if COL[c]['mdisp']==md_]
    print('#   mdisp=%-6d 表数=%-4d 槽位分布=%s'%(md_,len(sub),collections.Counter(i for c in sub for (i,v) in hit[c]).most_common(6)))
# 0x4105f0 / 0x410600 承载
for tv in (0x4105e0,0x4105f0,0x410600):
    cols=[(c,i) for c in hit for (i,v) in hit[c] if v==tv]
    print('# thunk %08x imm=%d jmp=%08x 承载 %d 个位置，idx 分布=%s'%(
        tv,TH[tv]['imm'],TH[tv]['jmp'],len(cols),collections.Counter(i for c,i in cols).most_common(6)))
json.dump(dict(vt={hex(c):[hex(v) for v in VT[c]] for c in VT},
               vt_of={hex(c):hex(vt_of[c]) for c in vt_of},
               thunk={hex(k):v for k,v in TH.items()},
               hit={hex(c):[[i,hex(v)] for i,v in hit[c]] for c in hit},
               mdisp={hex(c):COL[c]['mdisp'] for c in COL},
               names={hex(c):COL[c]['name'] for c in COL}),
          open('/home/t628/projects/ra2-campaign-forge/_r209/q3.json','w'),indent=0)
