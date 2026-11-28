# -*- coding: utf-8 -*-
"""R209 v6：§2.12 规则 D —— 复算审计 #536 的 5 项结论 + 它自报的 3 个主会话未见过的数字。
待复算：#536 主张 ①判据漏斗 23707/10932/1229/1214；②213 张表不足 3 槽；③70 thunk 的 imm 分布
4×40/24×18/36×3/40×3/44×3/1728×3；④"0xc 对应前 12 字节 this 调整的成员指针双参调用惯例"（措辞，需订正）；
⑤未出现在前三槽的 2 个 thunk = 0x510ab0/0x510ac0。
"""
import sys, struct, collections, json
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
def s32(v): return struct.unpack('<i',struct.pack('<I',v&0xffffffff))[0]
fails=[];NA=0
def ck(n,c,d=''):
    global NA;NA+=1
    if not c: fails.append(n)
    print(('PASS ' if c else 'FAIL ')+n+((' | '+str(d)) if d!='' else ''))
# ① 判据漏斗（独立重算，不读 q3.json）
f=[0]*5
for sn in ('.rdata','.data'):
    s=P.B[sn]; n=s['rawsize']//4; base=s['lo']
    w=struct.unpack_from('<%dI'%n,P.RAW,s['rawptr'])
    for k in range(n-4):
        if w[k] in (0,1,2): f[0]+=1
        else: continue
        if w[k+2]!=0: continue
        f[1]+=1
        if P.where(w[k+3])!='.data': continue
        f[2]+=1
        if P.where(w[k+4])!='.rdata': continue
        f[3]+=1
        nm=P.cstr(w[k+3]+8,400)
        if nm and nm.startswith(b'.?A') and nm.endswith(b'@@'): f[4]+=1
print('# 漏斗实测: sig=%d w2==0=%d pTD@.data=%d pCHD@.rdata=%d 名称合格=%d'%tuple(f))
ck('V1 审计漏斗 23707/10932/1229/1214/1214 四段全部复现',
   f[0]==23707 and f[1]==10932 and f[2]==1229 and f[3]==1214 and f[4]==1214, f)
# 重建模型
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
ck('V2 模型 1214/1214/14044', len(COL)==1214 and len(VT)==1214 and sum(len(v) for v in VT.values())==14044,
   '%d/%d/%d'%(len(COL),len(VT),sum(len(v) for v in VT.values())))
# ② 不足 3 槽的表数
lens=collections.Counter(len(v) for v in VT.values())
short=sum(n for L,n in lens.items() if L<3)
ck('V3 不足 3 槽的表 = 213（审计 #536 自报数复现）', short==213, short)
ck('V4 槽数分布与审计给出的桶一致（1:199, 2:14, 3:82, 7:412, 122:10, 344:1）',
   lens[1]==199 and lens[2]==14 and lens[3]==82 and lens[7]==412 and lens[122]==10 and lens[344]==1,
   dict(lens))
# ③ thunk imm 分布
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
dist=collections.Counter(t['imm'] for t in TH.values())
ck('V5 70 thunk 的 imm 分布 40/18/3/3/3/3 = 4 24 36 40 44 1728（审计数复现）',
   dist==collections.Counter({4:40,24:18,36:3,40:3,44:3,1728:3}), dict(dist))
# ④ ret 0xc 的正确解释（订正审计措辞）
intab=set()
for c,v in VT.items():
    for x in v[:3]:
        if x in TH: intab.add(x)
outside=[t for t in TH if t not in intab]
ck('V6 未进前三槽的 thunk = 2 个（0x510ab0/0x510ac0），审计数复现',
   len(outside)==2 and {hex(t) for t in outside}=={'0x510ab0','0x510ac0'},
   [hex(t) for t in outside])
# ⑤ 主视图 slot0 ret 分布 vs QI
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
md=Cs(CS_ARCH_X86,CS_MODE_32)
def retimm(a,cap=900):
    o=P.r2o(a)
    for i in md.disasm(P.RAW[o:o+cap],a):
        if i.mnemonic=='ret': return int(i.op_str,16) if i.op_str else 0
    return None
rd=collections.Counter()
for c,v in VT.items():
    if COL[c]['mdisp']==0: rd[retimm(v[0])]+=1
print('# 954 主视图 slot0 首 ret 分布 = %s'%rd.most_common())
# 反控：ret 0xc 的 3 个 dword 参数 —— 用 0x410260 体首读参数确认
o=P.r2o(0x410260); ins=list(md.disasm(P.RAW[o:o+40],0x410260))
args=[i.op_str for i in ins[:8]]
ck('V7 订正审计措辞：ret 0xc 是 stdcall 被调方清 12 字节栈 = 3 个 dword 参数（this,riid,ppv），'
   '不是「前 12 字节 this 调整的成员指针双参」——0x410260 体首读 [esp+0xc] 作 ppv、[esp+0x10] 作 pv',
   ins[0].op_str=='dword ptr [esp + 0xc]' and any('esp + 0x10' in i.op_str for i in ins[:12]),
   [i.mnemonic+' '+i.op_str for i in ins[:4]])
json.dump(dict(funnel=f,short=short,lens=dict(lens),imm=dict(dist),outside=[hex(t) for t in outside],
               prim_slot0_ret={str(k):v for k,v in rd.items()}),
          open('/home/t628/projects/ra2-campaign-forge/_r209/v6.json','w'),indent=1)
print('\n== FAILS: %s (%d 断言) =='%(fails,NA))
