# -*- coding: utf-8 -*-
"""R208 m16：订正 m15 的三条误判（口径差，非对方错），并把结论钉死。
订正 1：审计 #529 的「1275 出现点」在**全段口径**（.text+.rdata+.data+.rsrc+.detour）成立；m15 只扫 .rdata/.data 得 1218 ⇒ 我错。
订正 2：审计 #529 的 3 处 imm32==0x7f9598 在全段**非对齐**扫描成立（0x7ca957/0x7caab1/0x7cabe1）；m15 用 4 对齐 dword 扫描得 0 ⇒ 我错。
订正 3：执行员 #528 的「物理 BCD 1007」在**宽松判据**（pTD∈TD ∧ +4≤200）下成立，但那 5 条不是 BCD：+12≠−1、+16≠0，是 MSVC 异常类 RTTI 记录（exception/bad_typeid/__non_rtti_object/bad_cast/_com_error），且无任何类头引用。
"""
import sys,struct,collections,json
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
def s32(v): return struct.unpack('<i',struct.pack('<I',v))[0]
fails=[];NA=0
def ck(n,c,d=''):
    global NA;NA+=1
    if not c: fails.append(n)
    print(('PASS ' if c else 'FAIL ')+n+((' | '+str(d)) if d!='' else ''))
COL={}
for sn in ('.rdata','.data'):
    s=P.B[sn]; n=s['rawsize']//4; base=s['lo']
    w=struct.unpack_from('<%dI'%n,P.RAW,s['rawptr'])
    for i in range(n-4):
        if w[i] not in (0,1,2) or w[i+2]!=0: continue
        if P.where(w[i+3])!='.data' or P.where(w[i+4])!='.rdata': continue
        nm=P.cstr(w[i+3]+8,400)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base+4*i]=dict(pTD=w[i+3],pCHD=w[i+4],name=nm.decode('latin1'))
CHD=sorted({v['pCHD'] for v in COL.values()})
NB={a:P.dw(a+8) for a in CHD}; pBCA={a:P.dw(a+12) for a in CHD}
BCA={a:[P.dw(pBCA[a]+4*j) for j in range(NB[a])] for a in CHD}
refd=set(x for a in CHD for x in BCA[a])
print('== F1 全段口径的 COL 地址引用点 ==')
tot=0; per={}
for sn in ('.text','.rdata','.data','.rsrc','.detour'):
    s=P.B[sn]; n=s['rawsize']//4; base=s['lo']
    w=struct.unpack_from('<%dI'%n,P.RAW,s['rawptr'])
    c=sum(1 for x in w if x in COL); per[sn]=c; tot+=c
print('  分段: %s ; 合计 %d' % (per,tot))
ck('F1.1 全段口径 = 1275（审计 #529 的数正确，m15 的 1218 是 .rdata/.data 子口径）', tot==1275, tot)
print('== F2 非对齐 imm32 扫描 ==')
st=P.B['.text']; raw=P.RAW[st['rawptr']:st['rawptr']+st['rawsize']]; lo=st['lo']
def scan(va):
    pat=struct.pack('<I',va); out=[]; i=raw.find(pat)
    while i>=0:
        out.append(lo+i); i=raw.find(pat,i+1)
    return out
h98=scan(0x7f9598); h94=scan(0x7f9594)
print('  imm 0x7f9598 命中 %d 处: %s' % (len(h98),[hex(x) for x in h98]))
print('  imm 0x7f9594 命中 %d 处: %s' % (len(h94),[hex(x) for x in h94]))
ck('F2.1 0x7f9598 恰 3 处（审计正确，m15 的 4 对齐扫描漏检）', len(h98)==3, len(h98))
ck('F2.2 3 处落在 0x7ca95x/0x7caabx/0x7cabex 邻域（type_info 实现簇）',
   all(0x7ca800<=x<0x7cb000 for x in h98), [hex(x) for x in h98])
print('== F3 1007 的 5 条到底是什么 ==')
TDs=set(v['pTD'] for v in COL.values())|{P.dw(b) for b in refd}
s=P.B['.rdata']; n=s['rawsize']//4; w=struct.unpack_from('<%dI'%n,P.RAW,s['rawptr']); rlo=s['lo']
loose=[rlo+4*i for i in range(n-6) if w[i] in TDs and w[i+1]<=200 and P.where(w[i])=='.data']
strict=[b for b in loose if P.dw(b+12)==0xffffffff and P.dw(b+16)==0]
five=sorted(set(loose)-set(strict))
print('  宽松 %d / 严格 %d / 差 %d' % (len(loose),len(strict),len(five)))
rows=[]
for b in five:
    nm=P.cstr(P.dw(b)+8,120).decode('latin1')
    rows.append(dict(addr=hex(b),td=hex(P.dw(b)),name=nm,nc=P.dw(b+4),
                     f8=s32(P.dw(b+8)),f12=s32(P.dw(b+12)),f16=s32(P.dw(b+16)),f20=P.dw(b+20),
                     referenced=(b in refd)))
    print('   0x%x %-30s nc=%d +8=%d +12=%d +16=%d +20=%d 被类头引用=%s' %
          (b,nm,P.dw(b+4),s32(P.dw(b+8)),s32(P.dw(b+12)),s32(P.dw(b+16)),P.dw(b+20),b in refd))
c1=all(r['f12']!=-1 and r['f16']!=0 for r in rows)
c2=all(not r['referenced'] for r in rows)
c3=all(r['name'] in ('.?AVexception@@','.?AVbad_typeid@@','.?AV__non_rtti_object@@','.?AVbad_cast@@','.?AV_com_error@@') for r in rows)
ck('F3.1 5 条 +12!=-1 且 +16!=0（非 BCD 形态）', c1, [(r['f12'],r['f16']) for r in rows])
ck('F3.2 5 条无一被类头引用', c2, sum(r['referenced'] for r in rows))
ck('F3.3 5 条恰是 MSVC 异常类：exception/bad_typeid/__non_rtti_object/bad_cast/_com_error', c3, [r['name'] for r in rows])
print('  ⇒ 结论：「物理 BCD 1002」是严格判据口径（+12==-1 ∧ +16==0），1007 是宽松判据把 5 条异常类 RTTI 记录算进来的结果；两者都对，但只有 1002 是 BCD。')
json.dump(dict(allRefs=tot,per=per,imm98=[hex(x) for x in h98],imm94=[hex(x) for x in h94],
               loose=len(loose),strict=len(strict),five=rows,asserts=NA,fails=fails),
          open('_r208/m16_recompute_fix.json','w'),ensure_ascii=False,indent=1)
print('== 断言 %d / FAIL %d =='%(NA,len(fails)),fails)
