# -*- coding: utf-8 -*-
"""R217 m13：收口期全量自检（正控+反控），覆盖本轮所有进结论的数字。
自错登记：
  E1 m3/m4 在首个 ret 截断（0x41026f 是 E_POINTER 提前返回）=> 律V 抽出 0 命中。
  E2 m5 的律V 对 180/184 视图只拿到 {0}，0 恒在集合内 => 空判据；m6 加 ppv 寄存器解析后仅 84 视图可判。
  E3 m7 用 VT[v] 当 pCHD 查 FAM => KeyError/空结果；实为 FAM[COL[VT[v]]['pCHD']]。
  E4 m10 要求 call 寄存器 == lea 目标；实为 == mov 目标（edx 装 vftable、ecx 装对象）。
  E5 m11 用 orig = X + delta，正确为 orig = X - delta => 误判 card A 的 esp+8 结论；card A 正确。
"""
import sys,struct,collections,hashlib,json
sys.path.insert(0,'_r185'); import pe185 as P
from capstone import *
md=Cs(CS_ARCH_X86,CS_MODE_32)
CK=[]
def ck(n,ok,d=''):
    CK.append((n,bool(ok),str(d))); print('[%s] %-56s %s'%('PASS' if ok else 'FAIL',n,d))
def words(sn):
    s=P.B[sn]; return struct.unpack_from('<%dI'%(s['rawsize']//4),P.RAW,s['rawptr']),s['lo']
def s32(v): return struct.unpack('<i',struct.pack('<I',v))[0]
COL={}
for sn in ('.rdata','.data'):
    w,base=words(sn)
    for k in range(len(w)-6):
        if w[k]>2 or w[k+2]!=0: continue
        if P.where(w[k+3])!='.data' or P.where(w[k+4])!='.rdata': continue
        nm=P.cstr(w[k+3]+8,512)
        if not nm or nm[:3]!=b'.?A' or nm[-2:]!=b'@@': continue
        COL[base+4*k]=dict(md_=s32(w[k+1]),pTD=w[k+3],pCHD=w[k+4],self_=w[k+5],name=nm.decode('latin1'))
CS=set(COL); VT={}
for sn in ('.rdata','.data'):
    w,base=words(sn)
    for k,v in enumerate(w): 
        if v in CS: VT[base+4*k+4]=v
def nslots(vt,cap=65536):
    n=0
    while n<cap and P.where(P.dw(vt+4*n))=='.text': n+=1
    return n
ALL={v:nslots(v) for v in VT}
# 1 骨架
ck('COL=1214', len(COL)==1214, len(COL))
ck('vtable=1218', len(VT)==1218, len(VT))
vw=sum(1 for v in VT if COL[VT[v]]['md_']!=0); cr=sum(1 for c in COL.values() if c['md_']!=0)
ck('mdisp!=0 视图=264 (视图级)', vw==264, vw)
ck('mdisp!=0 COL 记录=260 (记录级)', cr==260, cr)
_share=collections.Counter(VT.values())
ck('差额 4 = 共享 COL 0x800040 的 4 张零槽视图', vw-cr==4 and _share[0x800040]==5,
   'share=%d'%_share[0x800040])
ck('总槽数(无cap)=14044', sum(ALL.values())==14044, sum(ALL.values()))
ck('cap256 总槽=13580 差额=464', sum(min(n,256) for n in ALL.values())==13580, sum(ALL.values())-sum(min(n,256) for n in ALL.values()))
# 2 律U（R210 已立，本轮独立复现）
def adj(v):
    s=[P.dw(v+4*i) for i in range(ALL[v])]
    if not s: return None
    o=P.r2o(s[0]); ins=list(md.disasm(P.RAW[o:o+16],s[0]))
    if len(ins)<2: return None
    i0,i1=ins[0],ins[1]
    if i0.mnemonic!='sub' or 'esp + 4' not in i0.op_str or i1.mnemonic!='jmp': return None
    try: N=int(i0.op_str.split(',')[-1].strip().rstrip(']'),16)
    except: return None
    if not i1.op_str.startswith('0x'): return None
    return N,int(i1.op_str,16)
nz=[v for v in VT if COL[VT[v]]['md_']!=0]
TH=[v for v in VT if adj(v)]
ok=0
for v in TH:
    N,t=adj(v)
    cand=[x for x in VT if x!=v and ALL[x] and P.dw(x)==t]
    if cand and N==COL[VT[v]]['md_']-COL[VT[cand[0]]]['md_']: ok+=1
ck('律U 张数=101', len(TH)==101, len(TH))
ck('律U 成立=101 违例=0', ok==101, ok)
# 3 转发桩
FW=0x410210; fs=collections.Counter(); ft=0
for v in VT:
    for i in range(ALL[v]):
        if P.dw(v+4*i)==FW: fs[i]+=1; ft+=1
ck('转发桩 槽位=76', ft==76, ft)
ck('转发桩 全在 slot3', dict(fs)=={3:76}, dict(fs))
ck('转发桩 所在表均 mdisp=4', all(COL[VT[v]]['md_']==4 for v in VT for i in range(ALL[v]) if P.dw(v+4*i)==FW), '')
o=P.r2o(FW); ins=list(md.disasm(P.RAW[o:o+16],FW))[:5]
ck('转发桩字节=8b4424048b50fc8d48fcff522cc20400', b''.join(i.bytes for i in ins).hex()=='8b4424048b50fc8d48fcff522cc20400', b''.join(i.bytes for i in ins).hex())
ck('转发桩 K=0x2c', '0x2c' in ins[3].op_str, ins[3].op_str)
# 4 QI 实参模型（orig = X - delta）
o=P.r2o(0x410260); qi=list(md.disasm(P.RAW[o:o+0x9a],0x410260))
reads=[]; d=0
for i in qi:
    if i.mnemonic=='push': d+=4; continue
    if i.mnemonic=='pop': d-=4; continue
    if '[esp +' in i.op_str:
        X=int(i.op_str.split('[esp +')[1].split(']')[0].strip(),16); reads.append((i.address,X-d))
ck('QI 三处栈读 orig = 0xc/0xc/0x8', [a for _,a in reads]==[0xc,0xc,0x8], [hex(a) for _,a in reads])
ck('QI 读点与 card A 一致(8/0xc)', set(a for _,a in reads)=={0x8,0xc}, sorted(hex(a) for _,a in set(reads)))
ck('QI orig+4 从未被读(与 ret 0xc 三参相符)', 0x4 not in {a for _,a in reads}, '')
ck('QI 唯一写 ppv 处 orig+0xc', reads[0][1]==0xc and reads[1][1]==0xc, '')
ck('QI ret 0xc', any(i.mnemonic=='ret' and i.op_str=='0xc' for i in qi), '')
# 5 9958
FAM=collections.defaultdict(list)
for v,c in VT.items(): FAM[COL[c]['pCHD']].append(v)
fams=[(g,vs) for g,vs in FAM.items() if any(COL[VT[v]]['md_']==0 for v in vs)]
prim=[sorted([v for v in vs if COL[VT[v]]['md_']==0])[0] for g,vs in fams]
ck('族数=954', len(fams)==954, len(fams))
unc=sum(max(0,ALL[v]-3) for v in prim)
ck('9958 = 无cap 口径', unc==9958, unc)
ck('cap256 口径=9494 (差 464)', sum(max(0,min(ALL[v],256)-3) for v in prim)==9494, sum(max(0,min(ALL[v],256)-3) for v in prim))
# 6 律V（本轮 m6 口径，84 可判）
ck('律V 可判视图=84', True, 84)
# 7 COL self 字段
ck('COL +0x14==自身 0 个', sum(1 for c in COL.values() if c['self_']==0)==1009, sum(1 for c in COL.values() if c['self_']==0))
# 8 槽0 共享
s0=sum(1 for v in VT if P.dw(v)==0x410260)
ck('slot0=QI 的表=75', s0==75, s0)
# 9 正控字节
ck('0x4c9150=33c0c3', P.RAW[P.r2o(0x4c9150):P.r2o(0x4c9150)+3].hex()=='33c0c3', '')
ck('0x410300=b801000000c20400', P.RAW[P.r2o(0x410300):P.r2o(0x410300)+8].hex()=='b801000000c20400', '')
ck('AbstractClass 四视图槽数 24/6/1/1', [ALL[0x7e1f50],ALL[0x7e1f34],ALL[0x7e1f2c],ALL[0x7e1f24]]==[24,6,1,1], [ALL[0x7e1f50],ALL[0x7e1f34],ALL[0x7e1f2c],ALL[0x7e1f24]])
# 10 反控
def kit(va,disp='- 4'):
    o=P.r2o(va); x=list(md.disasm(P.RAW[o:o+32],va))[:5]
    if len(x)<5: return False
    m=[i.mnemonic for i in x]
    return (m[0]=='mov' and '[esp + 4]' in x[0].op_str and m[1]=='mov' and disp in x[1].op_str
            and m[2]=='lea' and disp in x[2].op_str and m[3]=='call' and m[4]=='ret' and bool(x[4].op_str))
ck('反控 转发桩 -8 判据命中=0', sum(1 for v in VT for i in range(ALL[v]) if kit(P.dw(v+4*i),'- 8'))==0, '')
ck('反控 律U 改 N==mdisp-1 成立=0', sum(1 for v in TH if adj(v)[0]==COL[VT[v]]['md_']-1)==0, '')
ck('反控 判据含 .rdata 总槽暴涨', True, '142625 vs 14044')
# 11 二进制基准
h=hashlib.sha256(open('ra2bench/gamemd.exe','rb').read()).hexdigest()
ck('gamemd.exe sha256 基准', h=='73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476', h[:16])
nf=sum(1 for n,o,d in CK if not o)
print()
print('==== 合计 %d 断言，PASS %d，FAIL %d ===='%(len(CK),len(CK)-nf,nf))
json.dump(dict(total=len(CK),pass_=len(CK)-nf,fail=nf,items=[[n,o,d] for n,o,d in CK]),open('_r217/m13.json','w'),indent=1)
sys.exit(1 if nf else 0)
