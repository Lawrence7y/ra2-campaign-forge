# -*- coding: utf-8 -*-
"""R218 m13：6 张超 256 表的高槽块是否两两相同（若相同则证明存在一个更大的公共祖先 vftable 分量，
而非各表独立新增）。决定性证据：逐槽比较 6 张表的 [256..min_n) 段。
正控：0x7e1f50 与自身比较全等率 100%。
反控：把比较起点改成 0，全等率应大幅下降（各表低槽各自覆盖）。
"""
import sys,struct,collections,itertools
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
VT={v:c for v,c in VT.items() if P.where(P.dw(v))=='.text'}
def slots(vt,cap=65536):
    out=[]
    while len(out)<cap and P.where(P.dw(vt+4*len(out)))=='.text': out.append(P.dw(vt+4*len(out)))
    return out
TGT=[0x7f4960,0x7e3ebc,0x7e8c94,0x7e22a4,0x7eb058,0x7f5c70]  # 按槽数升序
S={v:slots(v) for v in TGT}
print('[槽数]',[(hex(v),len(S[v])) for v in TGT])
print('\n[两两同槽比对 起点256]')
print('%-10s %-10s %5s %5s %5s %5s'%('A','B','range','same','diff','pct'))
for a,b in itertools.combinations(TGT,2):
    lo=256; hi=min(len(S[a]),len(S[b]))
    same=sum(1 for k in range(lo,hi) if S[a][k]==S[b][k])
    print('%08x %08x %5d %5d %5d %5.1f%%'%(a,b,hi-lo,same,hi-lo-same,100.0*same/(hi-lo)))
print('\n[两两同槽比对 起点0（反控）]')
tot_s=tot_n=0
for a,b in itertools.combinations(TGT,2):
    hi=min(len(S[a]),len(S[b]))
    same=sum(1 for k in range(0,hi) if S[a][k]==S[b][k])
    tot_s+=same; tot_n+=hi-lo
    print('%08x %08x range0 %5d same=%4d %5.1f%%'%(a,b,hi,same,100.0*same/hi))
print('\n[逐槽全 6 表一致性]')
hi=min(len(S[v]) for v in TGT)
allid=[k for k in range(256,hi) if len(set(S[v][k] for v in TGT))==1]
print('  区间 256..%d 共 %d 槽，6 表全同 = %d，不全同 = %d'%(hi-1,hi-256,len(allid),hi-256-len(allid)))
nonid=[k for k in range(256,hi) if k not in set(allid)]
print('  不全同的槽号:',nonid)
print('  全同块 256..%d 的目标（前 20）:'%(allid[-1] if allid else 255))
for k in allid[:20]:
    t=S[TGT[0]][k]; print('    slot%3d = %08x [%s]'%(k,t,P.RAW[P.r2o(t):P.r2o(t)+8].hex()))
print('\n[公共块长度] 全同且连续的最大前缀长度 = %d'%len(allid))
# 该公共块是否与某张已有表的 [0..] 段相同？（即是否是被复制的另一张表）
print('\n[反查] 公共块 256..%d 的目标序列是否等于某张表的低槽段？'%(hi-1))
seq=[S[TGT[0]][k] for k in allid]
found=[]
for v in VT:
    sv=slots(v)
    if len(sv)<len(seq): continue
    for off in range(0,len(sv)-len(seq)+1):
        if sv[off:off+len(seq)]==seq: found.append((hex(v),off,COL[VT[v]]['name']))
print('  命中:',found[:10])
print('\n[正控] 0x7e1f50 自身比对全等率:',100.0*sum(1 for k in range(24) if slots(0x7e1f50)[k]==slots(0x7e1f50)[k])/24)
