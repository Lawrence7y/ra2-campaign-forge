# -*- coding: utf-8 -*-
"""R211 c1：8 个{4}独立附加项类的成因取证。
一次输出：(A) 每类 mdisp==4 的 BCD 记录（pTD 真名 / pdisp / vdisp / attributes）；
(B) 主视图 slot0（QI）完整体反汇编中"所有对出参的写入形态"，分五类：
    S1 lea reg,[x+K] + mov [out],reg   (R210 判据已覆盖)
    S2 mov dword ptr [out], imm        (常量直写)
    S3 add/sub reg,imm + mov [out],reg
    S4 mov reg,[x+K] + mov [out],reg   (load 后写)
    S5 其他含 [out] 的写
(C) QI 体内 GUID 比较链（repe cmpsd 前的 push/mov 立即数）。
"""
import sys,json,collections,re
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
md=Cs(CS_ARCH_X86,CS_MODE_32)
d3=json.load(open('/home/t628/projects/ra2-campaign-forge/_r209/q3.json'))
VT={int(k,16):[int(x,16) for x in v] for k,v in d3['vt'].items()}
MD={int(k,16):v for k,v in d3['mdisp'].items()}
NM={int(k,16):v for k,v in d3['names'].items()}
cls=collections.defaultdict(dict)
for v in MD: cls[P.dw(v+16)][MD[v]]=v
TARGET=[0x802a18,0x7fb4b0,0x7ffea0,0x800098,0x804ce0,0x8093f8,0x80c1d0,0x80d298]
def body(a,lim=1400,maxn=400):
    o=P.r2o(a); ins=[]
    for i in md.disasm(P.RAW[o:o+lim],a):
        ins.append(i)
        if i.mnemonic=='ret' and i.address>a+0x20: break
        if len(ins)>maxn: break
    return ins
def bcd_list(col):
    """COL +16 = pCHD ; CHD +0 = pBCA? 用 R207 已知：COL+0 pTD, +4 pdisp, +8 cdOffset, +12 vdisp,
    +16 mdisp, +20 attributes  (BCD 24B 六字段)；COL+16 是内嵌主对象 COL。
    这里改用 R206/R207 实证的物理 BCD 反查：直接在 .data 搜 pTD==本类 pTD 的记录。"""
    return None
out={}
for c in TARGET:
    vs=cls[c]; offs=sorted(vs)
    name=NM[vs[0]]
    qa=VT[vs[0]][0]
    ins=body(qa)
    # collect out-pointer writes: any 'mov dword ptr [reg...], src'
    writes=[]; guidcmp=[]
    lastlea=None; lastadd=None; gap=0
    for i in ins:
        op=i.op_str
        if i.mnemonic=='lea':
            m=re.search(r'^(\w+), \[\w+ \+ (0x[0-9a-f]+|\d+)\]',op)
            if m: lastlea=(m.group(1),int(m.group(2),16) if m.group(2).startswith('0x') else int(m.group(2)),i.address)
            else: lastlea=None
            gap=0
        elif i.mnemonic in ('add','sub'):
            m=re.search(r'^(\w+), (0x[0-9a-f]+|\d+)$',op)
            if m: lastadd=(m.group(1),i.mnemonic,int(m.group(2),16) if m.group(2).startswith('0x') else int(m.group(2)),i.address)
            else: lastadd=None
            gap=0
        else:
            gap+=1
            if gap>8: lastlea=None; lastadd=None
        if i.mnemonic=='mov' and 'dword ptr [' in op and ',' in op:
            dst,src=op.split(', ')[0],op.split(', ')[-1]
            if 'esp' in dst: continue
            kind=None
            if src.startswith('0x') or re.fullmatch(r'\d+',src):
                kind='S2_imm'
            elif lastlea and src==lastlea[0]:
                kind='S1_lea+%d@%x'%(lastlea[1],lastlea[2])
            elif lastadd and src==lastadd[0]:
                kind='S3_%s%d@%x'%(lastadd[1],lastadd[2],lastadd[3])
            else:
                kind='S4/S5_'+src
            writes.append((i.address,dst,kind))
        if i.mnemonic.startswith('rep') or (i.mnemonic=='cmp'):
            guidcmp.append((i.address,op))
    out[name]={'col':hex(c),'views':[[o,hex(vs[o])] for o in offs],'qi':hex(qa),'n_ins':len(ins),
               'writes':[[hex(a),d,k] for a,d,k in writes],
               'guidcmp':[[hex(a),o] for a,o in guidcmp]}
    print('='*100)
    print('%s  COL=%s  QI(slot0)=%s  指令数=%d'%(name,hex(c),hex(qa),len(ins)))
    print('  视图 %s'%([[o,hex(vs[o])] for o in offs]))
    print('  出参写入 %d 条：'%len(writes))
    for a,d,k in writes: print('    %s  %-22s %s'%(hex(a),d,k))
json.dump(out,open('/home/t628/projects/ra2-campaign-forge/_r211/c1.json','w'),indent=1)
print('\nWROTE c1.json')
