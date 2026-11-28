# -*- coding: utf-8 -*-
"""R212 c5：S 域 8/12 的 vftable 字节侧独立复算（不经 q3.json 的 mdisp 推导，直读槽表）。
对 78 类中抽 5 类：给出其主视图 vftable 起始 VA、槽数、slot0..slotN 落点，确认 8/12 槽的真实位置。
另核：mdisp=8 视图函数落点是否与 mdisp=12 视图同址族。
"""
import sys,struct,collections,json
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
md=Cs(CS_ARCH_X86,CS_MODE_32)
d3=json.load(open('_r209/q3.json'))
VT={int(k,16):[int(x,16) for x in v] for k,v in d3['vt'].items()}
MD={int(k,16):v for k,v in d3['mdisp'].items()}
NM={int(k,16):v for k,v in d3['names'].items()}
cls=collections.defaultdict(dict)
for v in MD: cls[P.dw(v+16)][MD[v]]=v
SAMPLE=[0x802a18,0x7fb4b0,0x800098,0x804ce0,0x8093f8]
NA=0;FAILS=[]
def ck(n,c,d=''):
    global NA;NA+=1
    if not c: FAILs_append(n)
    print(('PASS ' if c else 'FAIL ')+n+((' | '+str(d)) if d!='' else ''))
FAILs_append=lambda n: FAILS.append(n)
def peek(a,n=6):
    """只取前 n 条指令，详细模式仅用于这少数地址（合规）"""
    o=P.r2o(a)
    if o is None: return []
    out=[]
    for i in md.disasm(P.RAW[o:o+64],a):
        out.append('%s %s'%(i.mnemonic,i.op_str))
        if len(out)>=n: break
    return out
print('抽样 5 类的 vftable 槽表（主视图 + 8/12 视图）')
for c in SAMPLE:
    name=NM[cls[c][0]]
    print('='*100); print('%s  COL=%s  视图偏移 %s'%(name,hex(c),sorted(cls[c])))
    for off in sorted(cls[c]):
        v=cls[c][off]; slots=VT[v]
        print('   mdisp=%-5d vftable=%s 槽数=%d 落点=%s'%(
            off,hex(v),len(slots),[hex(s) for s in slots[:6]]))
        if off in (8,12):
            print('        slot0 前 3 条：%s'%peek(P.dw(v) if not slots else slots[0] if False else slots[0],3))
# 8 与 12 视图的 slot0 落点是否同址
same=0; diff=0; pair=[]
for c in cls:
    if 8 in cls[c] and 12 in cls[c]:
        s8=VT[cls[c][8]][0]; s12=VT[cls[c][12]][0]
        pair.append((s8,s12))
        if s8==s12: same+=1
        else: diff+=1
print('\n78 类中 8 与 12 视图 slot0 落点：同址 %d / 异址 %d'%(same,diff))
ck('C1 8 与 12 视图 slot0 落点全部异址（两个不同接口表）', diff==78 and same==0, '同%d 异%d'%(same,diff))
# 落点频次
f8=collections.Counter(VT[cls[c][8]][0] for c in cls if 8 in cls[c])
f12=collections.Counter(VT[cls[c][12]][0] for c in cls if 12 in cls[c])
print('8 视图 slot0 落点 top：%s'%[(hex(k),v) for k,v in f8.most_common(6)])
print('12 视图 slot0 落点 top：%s'%[(hex(k),v) for k,v in f12.most_common(6)])
ck('C2 8/12 视图 slot0 落点种类数 > 1（非共享单一 thunk）', len(f8)>1 and len(f12)>1, '%d/%d'%(len(f8),len(f12)))
# 视图槽数
n8=collections.Counter(len(VT[cls[c][8]]) for c in cls if 8 in cls[c])
n12=collections.Counter(len(VT[cls[c][12]]) for c in cls if 12 in cls[c])
print('8 视图槽数分布：%s'%dict(n8))
print('12 视图槽数分布：%s'%dict(n12))
ck('C3 8 与 12 视图槽数均为 1（单槽接口表）', set(n8)=={1} and set(n12)=={1}, '%s / %s'%(dict(n8),dict(n12)))
json.dump(dict(same=same,diff=diff,f8=[[hex(k),v] for k,v in f8.most_common()],
  f12=[[hex(k),v] for k,v in f12.most_common()],n8=dict(n8),n12=dict(n12),
  nassert=NA,fails=FAILS),open('_r212/c5.json','w'),indent=1)
print('\n断言 %d 条 / FAIL %d %s'%(NA,len(FAILS),FAILS))
