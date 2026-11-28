# -*- coding: utf-8 -*-
"""R216 m2：①修正 m1 的边界规则（首 ret 截断）→ 实测 0x410260/0x4103e0 的完整函数体；
②0x4105a0 写入的 4 张 vftable 0x7e1f50/0x7e1f34/0x7e1f2c/0x7e1f24 的 COLA 归属与槽内容。"""
import sys,struct,json,collections
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
from capstone import *
mdl=Cs(CS_ARCH_X86,CS_MODE_32)          # detail=False，仅反汇编
def o(va): return P.r2o(va)
def dump(va,end,label):
    print('=== %s 0x%08x..0x%08x ==='%(label,va,end))
    for i in mdl.disasm(P.RAW[o(va):o(va)+(end-va)],va):
        print('  %08x  %-8s %s'%(i.address,i.mnemonic,i.op_str))
    print('  raw=%s'%P.RAW[o(va):o(va)+(end-va)].hex())
dump(0x410260,0x410300,'slot0 QueryInterface 完整段')
dump(0x4103e0,0x410410,'slot7 完整段')
# 0xCC 填充统计：判断函数边界规则可用性
t=P.B['.text']; tb=P.RAW[t['rawptr']:t['rawptr']+t['rawsize']]
runs=[];i=0;n=len(tb)
while i<n:
    if tb[i]==0xcc:
        j=i
        while j<n and tb[j]==0xcc: j+=1
        if j-i>=2: runs.append((i,j-i))
        i=j
    else: i+=1
print('=== .text 0xCC 连续填充段(>=2B) 数=%d 总字节=%d ==='%(len(runs),sum(r[1] for r in runs)))
print('  长度分布 top:',collections.Counter(r[1] for r in runs).most_common(10))
for va in (0x410260,0x410300,0x410310,0x4103e0,0x410410,0x4105a0):
    fo=o(va)-t['rawptr']
    around=[r for r in runs if r[0]-8<=fo<=r[0]+r[1]]
    print('  槽 0x%08x 文件内 .text 偏移=%d 邻近0xCC段=%s'%(va,fo,around[:2]))
# ---- 4 张 vftable 归属 ----
def s32(v): return struct.unpack('<i',struct.pack('<I',v&0xffffffff))[0]
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
    VIEWS.append(dict(col=S2C[st],base=st,slots=sl,mdisp=md_,ptd=ptd,pchd=pchd,nm=nm[1:] if nm.startswith('.') else nm))
BM={v['base']:v for v in VIEWS}
QB=set(v['base'] for v in VIEWS)
print('=== 4 张 vftable 归属（0x7e1f50 是已知主视图）===')
for b in (0x7e1f50,0x7e1f34,0x7e1f2c,0x7e1f24):
    v=BM.get(b)
    if not v: print('  0x%08x 不在视图表（非 COLA 视图起点）'%b); continue
    print('  0x%08x nm=%-28s mdisp=%-6d ptd=0x%08x pchd=0x%08x slots=%d'%(b,v['nm'],v['mdisp'],v['ptd'],v['pchd'],len(v['slots'])))
    print('     slots=%s'%' '.join('0x%08x'%x for x in v['slots']))
    print('     bytes=%s'%P.RAW[o(b)-4:o(b)-4+4*(len(v['slots'])+2)].hex())
# 4 张视图是否被任何视图槽值引用
TGT=collections.Counter(x for v in VIEWS for x in v['slots'])
for b in (0x7e1f50,0x7e1f34,0x7e1f2c,0x7e1f24):
    print('  0x%08x 作为槽值出现=%d 次'%(b,TGT.get(b,0)))
# 0x7e1f24/2c/34/50 附近所有 COLA 记录
print('=== 0x7e1e00..0x7e2020 区间内所有视图起点 ===')
for v in sorted([v for v in VIEWS if 0x7e1e00<=v['base']<=0x7e2020],key=lambda v:v['base']):
    print('  0x%08x %-30s mdisp=%-6d slots=%d'%(v['base'],v['nm'],v['mdisp'],len(v['slots'])))
json.dump({'views4':[{'base':'0x%08x'%b,'in_table':bool(BM.get(b)),
   'nm':BM[b]['nm'] if b in BM else None,'mdisp':BM[b]['mdisp'] if b in BM else None,
   'slots':['0x%08x'%x for x in BM[b]['slots']] if b in BM else []} for b in (0x7e1f50,0x7e1f34,0x7e1f2c,0x7e1f24)],
  'cc_runs':len(runs),'cc_bytes':sum(r[1] for r in runs)},
  open('/home/t628/projects/ra2-campaign-forge/_r216/m2.json','w'),indent=1)
