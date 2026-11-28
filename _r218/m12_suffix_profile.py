# -*- coding: utf-8 -*-
"""R218 m12：464 个 slot>=256 目标的画像（去重/地址区间/前缀/是否与低槽重复/是否属父类继承）。
同时给出 67 个 diff（覆盖）目标的画像，判断是否为真实覆盖。
正控：0x7e1f50 的 24 槽全部前缀应能被归类；反控：把区间过滤设成 .rdata 则计数应为 0。
"""
import sys,struct,collections
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
def body(a,n=10):
    o=P.r2o(a); return P.RAW[o:o+n]
def cls(b):
    if b[:3]==b'\x33\xc0\xc3': return 'xor_eax_ret'
    if b[:1]==b'\xc3': return 'ret'
    if b[:1]==b'\x32\xc0': return 'xor_al_ret'
    if b[:4]==b'\x83\xec': return 'sub_esp_frame'
    if b[:2]==b'\x8b\x01': return 'mov_eax_this_vt'
    if b[:2]==b'\x8b\x44': return 'mov_eax_arg'
    if b[:3]==b'\x8b\xff\x55' or b[:2]==b'\x55\x8b': return 'push_ebp_std'
    if b[:1]==b'\xe9': return 'jmp_rel'
    return 'other'
TGT=[0x7f5c70,0x7eb058,0x7e22a4,0x7e8c94,0x7e3ebc,0x7f4960]
PAR={0x7f5c70:0x7e8c94,0x7eb058:0x7e8c94,0x7e22a4:0x7e8c94,0x7e8c94:0x7f4960,0x7e3ebc:0x7f4960,0x7f4960:0x7f0508}
allsuf=[]; all_diff=[]
for vt in TGT:
    S=slots(vt); P2=slots(PAR[vt])
    suf=[(k,t) for k,t in enumerate(S) if k>=256]
    allsuf+=suf
    for k in range(256,len(S)):
        if k<len(P2) and S[k]!=P2[k]: all_diff.append((vt,k,S[k],P2[k]))
print('[汇总] slot>=256 目标 %d 个，去重 %d；diff 覆盖 %d 个'%(len(allsuf),len(set(t for _,t in allsuf)),len(all_diff)))
tg=[t for _,t in allsuf]
print('[区间] 目标地址 min=%08x max=%08x'%(min(tg),max(tg)))
print('[分段] 全部落 .text: %s'%all(P.where(t)=='.text' for t in tg))
print('[前缀分类]')
c=collections.Counter(cls(body(t)) for t in tg)
for k,v in c.most_common(): print('   %-16s %4d  (%.1f%%)'%(k,v,100.0*v/len(tg)))
print('[频次 top 12]')
for t,n in collections.Counter(tg).most_common(12):
    ks=[k for k,x in allsuf if x==t]
    print('   %08x n=%2d slots=%s [%s]'%(t,n,ks[:8],body(t,8).hex()))
print('[diff 覆盖 67 个的前缀分类]')
cd=collections.Counter(cls(body(e[2])) for e in all_diff)
for k,v in cd.most_common(): print('   %-16s %4d'%(k,v))
print('[diff 明细：是否父类目标是桩而本类是真函数]')
stubcnt=0
for vt,k,a,b in all_diff:
    pa=cls(body(a)); pb=cls(body(b))
    if pb in ('xor_eax_ret','ret','xor_al_ret') and pa not in ('xor_eax_ret','ret','xor_al_ret'): stubcnt+=1
print('   本类真函数覆盖父类桩的条数 = %d / %d'%(stubcnt,len(all_diff)))
print('[低槽内重复] slot>=256 目标在本表低 256 槽出现次数 = %d'%sum(1 for t in tg if t in set(slots(0)) ))
low_dup=0
for vt in TGT:
    S=slots(vt); low=set(S[:256]); low_dup+=sum(1 for t in S[256:] if t in low)
print('   合计（按表内低槽）= %d'%low_dup)
print('[反控] 若把判据改成目标落 .rdata，计数=%d（应 0）'%sum(1 for t in tg if P.where(t)=='.rdata'))
print('[正控] 0x7e1f50 24 槽前缀分类:',collections.Counter(cls(body(t)) for t in slots(0x7e1f50)))
