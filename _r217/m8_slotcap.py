# -*- coding: utf-8 -*-
"""R217 m8：槽数上限截断复核（card B 报 6 张表在 cap=256 处被截断，真值 309..344）。
逐个 cap 重算：终止条件 = 该 dword 不落在 .text；不设上限，但记录首次越界地址，并做反控
（若把 .text 判定换成 .rdata+ .text 会让槽数暴涨 => 证明 .text 判据是必要的）。
正控：AbstractClass 主视图 24 槽、0x7e1f34 6 槽。
"""
import sys,struct,collections,json
sys.path.insert(0,'_r185'); import pe185 as P
def words(sn):
    s=P.B[sn]; return struct.unpack_from('<%dI'%(s['rawsize']//4),P.RAW,s['rawptr']),s['lo']
def s32(v): return struct.unpack('<i',struct.pack('<I',v))[0]
COL={}
for sn in ('.rdata','.data'):
    w,base=words(sn)
    for k in range(len(w)-5):
        if w[k]>2 or w[k+2]!=0: continue
        if P.where(w[k+3])!='.data' or P.where(w[k+4])!='.rdata': continue
        nm=P.cstr(w[k+3]+8,512)
        if not nm or nm[:3]!=b'.?A' or nm[-2:]!=b'@@': continue
        COL[base+4*k]=dict(md_=s32(w[k+1]),pCHD=w[k+4],name=nm.decode('latin1'))
CS=set(COL); VT={}
for sn in ('.rdata','.data'):
    w,base=words(sn)
    for k,v in enumerate(w):
        if v in CS: VT[base+4*k+4]=v
VTS=sorted(VT)
def nslots(vt,cap=4096):
    n=0
    while n<cap and P.where(P.dw(vt+4*n))=='.text': n+=1
    return n
ALL={v:nslots(v) for v in VTS}
print('[正控] 0x7e1f50=%d (期望24)  0x7e1f34=%d (期望6)  0x7e1f2c=%d  0x7e1f24=%d'%(ALL[0x7e1f50],ALL[0x7e1f34],ALL[0x7e1f2c],ALL[0x7e1f24]))
print('[总量] 表数=%d 总槽数=%d  cap256 后总槽数=%d  差额=%d'%(len(VTS),sum(ALL.values()),sum(min(n,256) for n in ALL.values()),sum(ALL.values())-sum(min(n,256) for n in ALL.values())))
over=[(v,ALL[v]) for v in VTS if ALL[v]>256]
print('[超 256 的表] %d 张:'%len(over))
for v,n in sorted(over,key=lambda x:-x[1]): print('   %08x slots=%3d  %s'%(v,n,COL[VT[v]]['name']))
print('[槽数分布>200]',dict(sorted(collections.Counter(n for n in ALL.values() if n>200).items())))
print('[零槽表]',[hex(v) for v in VTS if ALL[v]==0])
# 反控：把判据放宽为 .text 或 .rdata
def nslots2(vt,cap=4096):
    n=0
    while n<cap and P.where(P.dw(vt+4*n)) in ('.text','.rdata'): n+=1
    return n
B={v:nslots2(v) for v in VTS}
print('[反控] 判据含 .rdata 后总槽数=%d（暴涨 %d）=> .text 判据必要'%(sum(B.values()),sum(B.values())-sum(ALL.values())))
json.dump(dict(tables=len(VTS),total=sum(ALL.values()),total_cap256=sum(min(n,256) for n in ALL.values()),
  over256=[(hex(v),n,COL[VT[v]]['name']) for v,n in sorted(over,key=lambda x:-x[1])],
  dist={str(k):v for k,v in sorted(collections.Counter(ALL.values()).items())},
  zero=[hex(v) for v in VTS if ALL[v]==0], alt_total=sum(B.values())),open('_r217/m8.json','w'),indent=1)
