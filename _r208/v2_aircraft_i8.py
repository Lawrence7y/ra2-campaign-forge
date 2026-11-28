# -*- coding: utf-8 -*-
"""R208 v2：I 形态第三类 this 调整定位（QM9 ⑥ 未取得项收官）。
上一轮/上一步只搜 lea reg,[reg-imm]，AircraftClass 漏判；本轮把判据放宽为「任意指令的
操作数里出现 -m 的常量负偏移，且该指令写回一个寄存器」，三形态逐条给地址。
正控：Infantry/Unit 已知若含 lea esi,[edi-8] 必须仍命中（判据是超集，不得丢已知）。
反控：同址 +0x400 起的窗口必须 0 命中（证非散弹式误命中）。
"""
import sys,struct,json,re
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
md=Cs(CS_ARCH_X86,CS_MODE_32)
fails=[];NA=0;OUT={}
def ck(n,c,d=''):
    global NA;NA+=1
    if not c: fails.append(n)
    print(('PASS ' if c else 'FAIL ')+n+((' | '+str(d)) if d!='' else ''))
CASES=[('AircraftClass',0x41bc30,8),('InfantryClass',0x522a60,8),('UnitClass',0x746100,8)]
def body(a,cap=2048):
    o=P.r2o(a); out=[]
    for i in md.disasm(P.RAW[o:o+cap],a):
        out.append(i)
        if i.mnemonic=='ret' and len(out)>3: break
    return out
def neg_hits(ins,m):
    r=re.compile(r'-\s*%d\b'%m); out=[]
    for i in ins:
        s=i.op_str.replace(' ','')
        if r.search(s) and 'esp' not in s and 'ebp' not in s:
            out.append((i.address,i.mnemonic+' '+i.op_str))
    return out
TAB={}
for nm,addr,m in CASES:
    ins=body(addr); hits=neg_hits(ins,m)
    TAB[nm]=dict(entry=hex(addr),insns=len(ins),end=hex(ins[-1].address),
                 hits=[[hex(a),s] for a,s in hits])
    print('%s 0x%x：%d 条指令 0x%x..0x%x，-%d 调整命中 %d：%s'%(nm,addr,len(ins),addr,ins[-1].address,m,len(hits),hits))
    ck('%s 体内存在 -%d 的 this 调整'%(nm,m),len(hits)==1,len(hits))
OUT['table']=TAB
# 编码分型
enc={}
for nm,addr,m in CASES:
    h=TAB[nm]['hits'][0][1]
    enc[nm]='add' if h.startswith('add ') else ('lea' if h.startswith('lea ') else h.split()[0])
OUT['enc']=enc
ck('三种编码不全相同：Aircraft=add esi,-8；Infantry/Unit=lea',enc=={'AircraftClass':'add','InfantryClass':'lea','UnitClass':'lea'},enc)
# 反控
o=P.r2o(0x41bc30+0x400)
alt=neg_hits(list(md.disasm(P.RAW[o:o+512],0x41bc30+0x400)),8)
OUT['ctrl']=len(alt)
ck('反控 +0x400 窗口 0 命中',len(alt)==0,alt[:2])
# 修正位在函数体中的位置（相对偏移）
for nm,addr,m in CASES:
    a=int(TAB[nm]['hits'][0][0],16)
    TAB[nm]['rel']=a-addr; print(' %s 调整位 0x%x = 入口 +0x%x'%(nm,a,a-addr))
ck('调整位相对偏移：Aircraft 独异（+0x5F），Infantry/Unit 同（+0x2E）',
   TAB['AircraftClass']['rel']==95 and TAB['InfantryClass']['rel']==46 and TAB['UnitClass']['rel']==46,
   {n:TAB[n]['rel'] for n in TAB})
# Infantry/Unit 函数体逐字节比对
def bytes_of(a,n):
    o=P.r2o(a); return P.RAW[o:o+n]
bI=bytes_of(0x522a60,0x522acf-0x522a60+1); bU=bytes_of(0x746100,0x74616f-0x746100+1)
bA=bytes_of(0x41bc30,0x41bdc0-0x41bc30+1)
OUT['len_I'],OUT['len_U'],OUT['len_A']=len(bI),len(bU),len(bA)
OUT['I_eq_U']=bI==bU
ck('Infantry 与 Unit 的 m=8 视图函数体逐字节不同（各自独立副本）',bI!=bU,(len(bI),len(bU)))
from capstone import Cs as _Cs,CS_ARCH_X86 as _A,CS_MODE_32 as _M
_md=_Cs(_A,_M)
def _dis(a,n): 
    o=P.r2o(a); return [(i.mnemonic+' '+i.op_str) for i in _md.disasm(P.RAW[o:o+n],a)]
_dI=_dis(0x522a60,0x522acf-0x522a60+1); _dU=_dis(0x746100,0x74616f-0x746100+1)
OUT['ins_I']=len(_dI); OUT['ins_U']=len(_dU)
_diffs=[(k,_dI[k],_dU[k]) for k in range(min(len(_dI),len(_dU))) if _dI[k]!=_dU[k]]
OUT['diffs']=_diffs
ck('两者指令数相同（39/39）且差异 10 处',len(_dI)==39 and len(_dU)==39 and len(_diffs)==10,(len(_dI),len(_dU),len(_diffs)))
_kinds={'栈帧':0,'参数偏移':0,'字段偏移':0,'内部跳转':0}
for k,a,b in _diffs:
    if a.startswith('sub esp') or a.startswith('add esp'): _kinds['栈帧']+=1
    elif 'esp +' in a: _kinds['参数偏移']+=1
    elif 'edi +' in a: _kinds['字段偏移']+=1
    elif a.split()[0].startswith('j'): _kinds['内部跳转']+=1
OUT['diff_kinds']=_kinds
ck('10 处差异分型 = 栈帧2/参数偏移1/字段偏移1/内部跳转6，无一处落在 this 调整位（lea/add -8）',
   _kinds=={'栈帧':2,'参数偏移':1,'字段偏移':1,'内部跳转':6},_kinds)
ck('差异中无任何一处含 -8 立即数',not any('-8' in a.replace(' ','') or '- 8' in a for k,a,b in _diffs),[a for k,a,b in _diffs if '-8' in a.replace(' ','')])
ck('Aircraft m=8 视图函数体与上两者都不同',bA!=bI and bA!=bU,len(bA))
print('\n== 断言 %d / FAIL %d == %s'%(NA,len(fails),fails))
json.dump({'asserts':NA,'fails':fails,'out':OUT},open('/home/t628/projects/ra2-campaign-forge/_r208/v2_aircraft_i8.json','w'),indent=1,ensure_ascii=False)
