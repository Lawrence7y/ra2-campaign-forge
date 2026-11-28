# -*- coding: utf-8 -*-
"""R218 m10：核验 .data 那 4 张「零槽表」是否真虚表（card B 报它们与 0x7e8278 共用 COL 0x800040）。
判据三条：
 (1) 从严口径「dw(V-4)==COL 且 dw(V) 落 .text」的表数应 = 1214 = COL 数；
 (2) 0x7e8278 槽数；
 (3) 在 .text 内按小端 dword 字节搜 V 值（虚表地址在代码里以 imm 形式被 mov [reg],V 写入）：
     真虚表应被引用，4 张 .data 假表应 0 引用；正控 0x7e1f50 / 0x7f5c70 应被引用。
 反控：搜一个必定不存在的地址 0x8f3a1c0 命中应为 0。
"""
import sys,struct
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
def slots(vt,cap=65536):
    out=[]
    while len(out)<cap and P.where(P.dw(vt+4*len(out)))=='.text': out.append(P.dw(vt+4*len(out)))
    return out
strict={v:c for v,c in VT.items() if P.where(P.dw(v))=='.text'}
print('[口径] COL=%d  dw(V-4)==COL 的表=%d  其中 dw(V)落.text 的=%d  零槽=%d'%(
    len(COL),len(VT),len(strict),len(VT)-len(strict)))
print('[零槽表]',[hex(v) for v in sorted(VT) if v not in strict])
print('[0x7e8278] slots=%d name=%s mdisp=%d'%(len(slots(0x7e8278)),COL[VT[0x7e8278]]['name'],COL[VT[0x7e8278]]['md_']))
# .text 内小端 dword 搜值
tlo=P.B['.text']['lo']; thi=P.B['.text']['hi_file']
traw=P.RAW[P.B['.text']['rawptr']:P.B['.text']['rawptr']+P.B['.text']['rawsize']]
def hits(va):
    pat=struct.pack('<I',va); out=[]; s=0
    while True:
        i=traw.find(pat,s)
        if i<0: break
        out.append(tlo+i); s=i+1
    return out
TGT=[0x7e8278,0x877000,0x877010,0x87b17c,0x87b18c,0x7e1f50,0x7f5c70,0x7e8c94,0x8f3a1c0]
for v in TGT:
    h=hits(v)
    print('  引用 %08x : %3d 处 %s'%(v,len(h),[hex(x) for x in h[:6]]))
print('[反控] 0x8f3a1c0 命中应为 0 ->',len(hits(0x8f3a1c0)))
# 4 张 .data 表的字节内容
import binascii
for v in (0x877000,0x877010,0x87b17c,0x87b18c,0x7e8278):
    o=P.r2o(v); print('  内容 %08x [%s..]: %s'%(v,P.where(v),P.RAW[o:o+32].hex()))
