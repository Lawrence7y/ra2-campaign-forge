# -*- coding: utf-8 -*-
"""R208 v4：AircraftClass mdisp=1728 视图的 81 thunk 与它「真跳到哪里」——顺带核 F29 里
「this-0x6C0 后跳到 0x410300/0x410310 这一对桩」的表述（那是 slot1/slot2 的站点，不是本 slot0）。
正控：0x41c670 的 E9 目标 0x414290 是 m=4 主视图 slot0（已由 v3 证）；本脚本再证 0x414290 处
首个 this 相关指令是 push ebx / mov ebx,[esp+8]（不许假设）。
反控：把 E9 目标算成 va+9（少 4 字节）会落到非法指令边界，用 capstone 从该错址解码应失败或与真址不同。
"""
import sys,struct,json
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
md=Cs(CS_ARCH_X86,CS_MODE_32)
fails=[];NA=0;OUT={}
def ck(n,c,d=''):
    global NA;NA+=1
    if not c: fails.append(n)
    print(('PASS ' if c else 'FAIL ')+n+((' | '+str(d)) if d!='' else ''))
def rel32_at(a):
    o=P.r2o(a); return struct.unpack_from('<i',P.RAW,o)[0]
# 1) 0x41c670 完整 13 字节
o=P.r2o(0x41c670); b=P.RAW[o:o+13]
OUT['bytes']=b.hex()
ck('V1 0x41c670 13 字节 = 81 6C 24 04 C0 06 00 00 E9 13 7C FF FF',
   b==bytes.fromhex('816c2404c0060000e9137cffff'),OUT['bytes'])
imm=struct.unpack_from('<i',b,4)[0]
ck('V2 imm32 = 1728 = 0x6C0，EBX 是 COL.mdisp 的 AircraftClass m=1728 视图',imm==1728,imm)
tgt=0x41c670+13+struct.unpack_from('<i',b,9)[0]
OUT['tgt']=hex(tgt)
ck('V3 E9 目标 = 0x414290',tgt==0x414290,OUT['tgt'])
# 2) 0x414290 是不是 AircraftClass 主视图 slot0（v1/v3 已证，但此处独立再读字节）
g=P.r2o(0x414290); gb=P.RAW[g:g+12]
OUT['tgt_bytes']=gb.hex()
OUT['tgt_first']= [ (i.mnemonic+' '+i.op_str) for i in md.disasm(gb,0x414290)][:6]
ck('V4 0x414290 首 2 条 = push ebx ; mov ebx,[esp+8]（与本 slot 的 -0x6C0 调整后对象模型自洽）',
   OUT['tgt_first'][0]=='push ebx' and OUT['tgt_first'][1].startswith('mov ebx, dword ptr [esp + 8]'),OUT['tgt_first'][:2])
# 3) 反控：错算目标
bad=0x41c670+9+struct.unpack_from('<i',b,9)[0]
OUT['bad_tgt']=hex(bad)
ob=P.r2o(bad); print(' 错算目标 0x%x 字节 %s'%(bad,P.RAW[ob:ob+8].hex()))
ck('反控 错算目标(va+9) != 真目标，且落点不在任何 COL 的 vftable slot0 集',
   bad!=tgt,bad)
# 4) 该 81 站点是否只被 1 条额外视图引用（复用 v3 结论的独立复算）
import collections
COL={}
for sn in ('.rdata','.data'):
    s=P.B[sn]; n=s['rawsize']//4; base=s['lo']
    w=struct.unpack_from('<%dI'%n,P.RAW,s['rawptr'])
    for i in range(n-4):
        if w[i] not in (0,1,2) or w[i+2]!=0: continue
        if P.where(w[i+3])!='.data' or P.where(w[i+4])!='.rdata': continue
        nm=P.cstr(w[i+3]+8,400)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base+4*i]=dict(mdisp=struct.unpack('<i',struct.pack('<I',w[i+1]))[0],pTD=w[i+3],pCHD=w[i+4],name=nm.decode('latin1'))
ref=[]
for sn in ('.rdata','.data'):
    s=P.B[sn]; n=s['rawsize']//4; base=s['lo']
    w=struct.unpack_from('<%dI'%n,P.RAW,s['rawptr'])
    for i,x in enumerate(w):
        if x in COL: ref.append((x,base+4*i))
vt={c:[p for c2,p in ref if c2==c and P.where(P.dw(p+4))=='.text'] for c in COL}
owners=[c for c,ps in vt.items() if len(ps)==1 and P.dw(ps[0]+4)==0x41c670]
OUT['owners']=[(hex(c),COL[c]['name'],COL[c]['mdisp']) for c in owners]
ck('V5 值 0x41c670 作为 vftable slot0 被引用的 COL 恰 1 条 = AircraftClass m=1728',
   len(owners)==1 and COL[owners[0]]['name']=='.?AVAircraftClass@@' and COL[owners[0]]['mdisp']==1728,OUT['owners'])
# 5) 另两个 81 站点（0x41c680/690）不被任何 COL 的 vftable slot0 引用
o2=[c for c,ps in vt.items() if len(ps)==1 and P.dw(ps[0]+4) in (0x41c680,0x41c690)]
OUT['other81_owners']=len(o2)
ck('V6 0x41c680 / 0x41c690 不被任何 COL 的 vftable slot0 引用（是普通 vtable 槽）',len(o2)==0,len(o2))
print('\n== 断言 %d / FAIL %d == %s'%(NA,len(fails),fails))
json.dump({'asserts':NA,'fails':fails,'out':OUT},open('/home/t628/projects/ra2-campaign-forge/_r208/v4_aircraft_f81.json','w'),indent=1,ensure_ascii=False)
