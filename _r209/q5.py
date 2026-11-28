# -*- coding: utf-8 -*-
"""R209 q5（定稿）：101 张 T 表的 slot0/1/2 = IUnknown 三方法的 this 调整 thunk 三元组。
断言全部按实测口径重写（q4 的 6/7 是我预设数字错，本轮纠正在此）。
"""
import sys, struct, collections, json
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
md=Cs(CS_ARCH_X86,CS_MODE_32)
def s32(v): return struct.unpack('<i',struct.pack('<I',v&0xffffffff))[0]
fails=[];NA=0
def ck(n,c,d=''):
    global NA;NA+=1
    if not c: fails.append(n)
    print(('PASS ' if c else 'FAIL ')+n+((' | '+str(d)) if d!='' else ''))
d3=json.load(open('/home/t628/projects/ra2-campaign-forge/_r209/q3.json'))
TH={int(k,16):v for k,v in d3['thunk'].items()}
VT={int(k,16):[int(x,16) for x in v] for k,v in d3['vt'].items()}
VO={int(k,16):int(v,16) for k,v in d3['vt_of'].items()}
HIT={int(k,16):[(i,int(x,16)) for i,x in v] for k,v in d3['hit'].items()}
MD={int(k,16):v for k,v in d3['mdisp'].items()}
NM={int(k,16):v for k,v in d3['names'].items()}

def retof(a,cap=400):
    o=P.r2o(a)
    for i in md.disasm(P.RAW[o:o+cap],a):
        if i.mnemonic=='ret': return i.bytes.hex()
    return None
def E_POINTER_first(a):
    o=P.r2o(a); code=P.RAW[o:o+32]
    return b'\x03\x40\x00\x80' in code   # 0x80004003 little-endian

tri=collections.defaultdict(list)
for c in HIT: tri[(VT[c][0],VT[c][1],VT[c][2])].append(c)
ck('T1 101 张 T 表 / 23 个不同 (s0,s1,s2) 三元组', len(HIT)==101 and len(tri)==23, '%d/%d'%(len(HIT),len(tri)))
ck('T2 每个三元组内 mdisp 唯一', all(len({MD[c] for c in v})==1 for v in tri.values()))
ck('T3 每张表 slot0/1/2 三槽全为 this 调整 thunk', all(all(x in TH for x in VT[c][:3]) for c in HIT))
ck('T4 slot0/1/2 的 thunk imm 全等该表 mdisp（303/303）',
   all(TH[VT[c][i]]['imm']==MD[c] for c in HIT for i in (0,1,2)),
   sum(1 for c in HIT for i in (0,1,2) if TH[VT[c][i]]['imm']==MD[c]))
ck('T5 全槽 thunk 命中 305 = 101*3 + 2', sum(len(HIT[c]) for c in HIT)==305,
   sum(len(HIT[c]) for c in HIT))
ck('T6 非 0/1/2 槽命中仅 2 处，同属 COL 0x8028b8 HouseClass mdisp=40 idx3/4',
   len([1 for c in HIT for (i,v) in HIT[c] if i>=3])==2 and
   {c for c in HIT for (i,v) in HIT[c] if i>=3}=={0x8028b8})

# IUnknown 语义证据：slot0 目标 ret 0xc + E_POINTER；slot1/2 目标 ret 4
s0t={TH[VT[c][0]]['jmp'] for c in HIT}; s1t={TH[VT[c][1]]['jmp'] for c in HIT}; s2t={TH[VT[c][2]]['jmp'] for c in HIT}
r0={a:retof(a) for a in s0t}; r1={a:retof(a) for a in s1t}; r2={a:retof(a) for a in s2t}
ck('T7 slot0 目标全部 ret 0xc（3 参数 = QI(this,riid,ppv)）', len(s0t)==13 and all(v=='c20c00' for v in r0.values()),
   {hex(k):v for k,v in r0.items()})
ck('T8 slot1 目标全部 ret 4（2 参数 = AddRef(this)）', len(s1t)==13 and all(v=='c20400' for v in r1.values()),
   len(s1t))
ck('T9 slot2 目标全部 ret 4（2 参数 = Release(this)）', len(s2t)==13 and all(v=='c20400' for v in r2.values()),
   len(s2t))
ck('T10 23 三元组只落 13 个 jmp 三元组 ⇒ jmp 目标 trio 不随 mdisp 变',
   len({tuple(TH[x]['jmp'] for x in k) for k in tri})==13,
   len({tuple(TH[x]['jmp'] for x in k) for k in tri}))
# E_POINTER 检查：13 个 QI 目标里有多少含 0x80004003
ep={a:E_POINTER_first(a) for a in s0t}
ck('T11 13 个 QI 目标准一返回 E_POINTER 0x80004003 的存在性', sum(ep.values())>=1,
   '%d/13'%sum(ep.values()))
ck('T12 A83 thunk 地址 21 个（slot0 口径）',
   len({t for c in HIT for t in (VT[c][0],)})==21,
   len({VT[c][0] for c in HIT}))
ck('T13 70 个 thunk 全部被使用，无未使用者（推翻 q2 的 48 未用）',
   {v for c in HIT for (i,v) in HIT[c]}==set(TH), '%d'%len({v for c in HIT for (i,v) in HIT[c]}))
# 21 个 slot0 thunk 的 jmp 目标 -> 表数
print('\n## slot0 thunk -> QI 目标 -> 承载表数 -> mdisp')
rows=[]
for tv,n in collections.Counter(VT[c][0] for c in HIT).most_common():
    j=TH[tv]['jmp']; mds=sorted({MD[c] for c in HIT if VT[c][0]==tv})
    rows.append(dict(thunk=hex(tv),imm=TH[tv]['imm'],qi=hex(j),tables=n,mdisp=mds))
    print('   %s imm=%-4d QI=%s 表=%-3d mdisp=%s ret=%s'%(hex(tv),TH[tv]['imm'],hex(j),n,mds,r0[j]))
json.dump(dict(rows=rows), open('/home/t628/projects/ra2-campaign-forge/_r209/q5.json','w'),indent=1)
print('\n== FAILS: %s (%d 断言) =='%(fails,NA))
