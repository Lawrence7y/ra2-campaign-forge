# -*- coding: utf-8 -*-
"""R218 m1 探针：R217 的 nslots 是否越界读进下一张 vftable（.rdata 相邻表连读）。
判据：遇到 vt+4*n 本身是另一张已登记 vftable 起点 (§VT) 即终止。
对照 R217 口径（仅 .text 判据，cap 65536）。
只作探测，不下结论。
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
def n_old(vt):
    n=0
    while n<65536 and P.where(P.dw(vt+4*n))=='.text': n+=1
    return n
def n_new(vt):
    n=0
    while n<65536:
        if n>=1 and (vt+4*n) in VT: break
        if P.where(P.dw(vt+4*n))!='.text': break
        n+=1
    return n
OLD={v:n_old(v) for v in VTS}; NEW={v:n_new(v) for v in VTS}
print('[表数] %d'%len(VTS))
print('[总槽] old=%d new=%d 差=%d'%(sum(OLD.values()),sum(NEW.values()),sum(OLD.values())-sum(NEW.values())))
print('[正控] 0x7e1f50 old=%d new=%d | 0x7e1f34 old=%d new=%d'%(OLD[0x7e1f50],NEW[0x7e1f50],OLD[0x7e1f34],NEW[0x7e1f34]))
diff=[(v,OLD[v],NEW[v]) for v in VTS if OLD[v]!=NEW[v]]
print('[口径不同的表] %d 张'%len(diff))
for v,o,n in sorted(diff,key=lambda x:-x[1])[:20]:
    print('   %08x old=%3d new=%3d 首越界 at k=%3d  名称=%s'%(v,o,n,(v+4*n in VT and n or n),COL[VT[v]]['name'][:60]))
over=[(v,OLD[v],NEW[v]) for v in VTS if OLD[v]>256]
print('[>256 的表 old] %d 张'%len(over))
for v,o,n in sorted(over,key=lambda x:-x[1]):
    print('   %08x old=%3d new=%3d  vt+4*new=%08x 是否VT=%s  %s'%(v,o,n,v+4*n,(v+4*n) in VT,COL[VT[v]]['name'][:64]))
json.dump(dict(n=len(VTS),old=sum(OLD.values()),new=sum(NEW.values()),
  diff=[[hex(v),o,n] for v,o,n in diff],
  over=[[hex(v),o,n,hex(v+4*n),COL[VT[v]]['name']] for v,o,n in sorted(over,key=lambda x:-x[1])]),open('_r218/m1.json','w'),indent=1)
