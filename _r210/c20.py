# -*- coding: utf-8 -*-
"""R210 c20（律 U 定稿 v4）：两条收紧同时生效。
R1 非 QI 形态（函数体内无 rep 前缀指令）⇒ 正偏移集合强制为空，不参与 {4} 附加。
R2 lea reg,[x+K] 的 K 计入返回偏移，需在该 lea 之后 8 条指令内出现 mov dword ptr [out], reg（把 reg 写进出参），
   且中间不得出现对 reg 的重写。此判据排除 0x42ee30（BaseClass，普通工厂，lea esi,[ebp+4] 后写的是 ecx）。
"""
import sys,struct,json,collections,re
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
md=Cs(CS_ARCH_X86,CS_MODE_32)
fails=[];NA=0
def ck(n,c,d=''):
    global NA;NA+=1
    if not c: fails.append(n)
    print(('PASS ' if c else 'FAIL ')+n+((' | '+str(d)) if d!='' else ''))
d3=json.load(open('/home/t628/projects/ra2-campaign-forge/_r209/q3.json'))
TH={int(k,16):v for k,v in d3['thunk'].items()}
VT={int(k,16):[int(x,16) for x in v] for k,v in d3['vt'].items()}
MD={int(k,16):v for k,v in d3['mdisp'].items()}
NM={int(k,16):v for k,v in d3['names'].items()}
HIT={int(k,16):[(i,int(x,16)) for i,x in v] for k,v in d3['hit'].items()}
cls=collections.defaultdict(dict)
for c in MD: cls[P.dw(c+16)][MD[c]]=c
main={p:v[0] for p,v in cls.items() if 0 in v}
cache={}
def an(a):
    if a in cache: return cache[a]
    o=P.r2o(a); ins=[]; n=0
    for i in md.disasm(P.RAW[o:o+900],a):
        ins.append(i); n+=1
        if i.mnemonic=='ret' and i.address>a+0x20: break
        if n>240: break
    isqi=any(i.mnemonic.startswith('rep') for i in ins)
    res=set()
    if isqi:
        for k,i in enumerate(ins):
            if i.mnemonic!='lea': continue
            m=re.search(r'^(\w+), \[\w+ \+ (0x[0-9a-f]+|\d+)\]$',i.op_str)
            if not m: continue
            reg=m.group(1); g=m.group(2); off=int(g,16) if g.startswith('0x') else int(g)
            for j in ins[k+1:k+9]:
                if j.mnemonic.startswith('rep') and reg=='esi': break
                if j.mnemonic=='mov' and j.op_str.startswith(reg+','): break   # reg 被重写
                if j.mnemonic=='mov' and j.op_str.startswith('dword ptr [') and j.op_str.split(', ')[-1]==reg:
                    res.add(off); break
    cache[a]=(isqi,res); return cache[a]
def tset(p): return {MD[c] for c in cls[p].values() if c in HIT}
def pos(p): return {x for x in an(VT[main[p]][0])[1] if x>0}
def pred(p):
    q=pos(p); return ({4}|q) if q else set()
bad=[(hex(p),NM[main[p]],sorted(tset(p)),sorted(pred(p)),hex(VT[main[p]][0])) for p in main if tset(p)!=pred(p)]
ck('M1 律 U 定稿 v4：954/954 成立', not bad, 'bad=%d %s'%(len(bad),bad[:6]))
dd=collections.Counter((tuple(sorted(tset(p))), tuple(sorted(pos(p)))) for p in main)
print('# (T偏移集, 正偏移集) -> 类数：')
for k,v in dd.most_common(20): print('   %s -> %d'%(k,v))
npos=sum(1 for p in main if pos(p))
ck('M2 正偏移非空类 = 91，空 = 863', npos==91 and len(main)-npos==863, (npos,len(main)-npos))
n_pure=len([p for p in main if pos(p) and tset(p)==pos(p)])
ck('M3 反控 A：去掉 {4} 项后仍成立的类数（应为 83：这 83 类的 QI 自己就返回 +4，{4} 对它们冗余）',
   n_pure==83, n_pure)
n_only4=len([p for p in main if pos(p) and tset(p)=={4}])
ck('M4 反控 B：只留 {4} 时仍成立 83 类、需正偏移的 8 类会失配', n_only4==83, n_only4)
ALLP=set().union(*[pos(p) for p in main]) if npos else set()
n_union_empty=len([p for p in main if not pos(p) and tset(p)==({4}|ALLP)])
ck('M5 反控 C：把全并集套到 863 个空类上 ⇒ 成立数必须为 0（逐类取值不可省）', n_union_empty==0, n_union_empty)
n_need4=len([p for p in main if pos(p) and tset(p)!=pos(p)])
ck('M6b {4} 作为独立附加项真正必需的类数 = 8（6 个 +24 / 1 个 +1728 / 1 个 HouseClass）', n_need4==8, n_need4)
d9=json.load(open('/home/t628/projects/ra2-campaign-forge/_r210/c9.json'))
t9=set(int(x,16) for x in d9['tcls']); sn=set(p for p in main if pos(p))
ck('M6 v4 的 91 类与 c9（12 QI 目标口径）的 91 类完全同一', sn==t9, 'diff=%d/%d'%(len(sn-t9),len(t9-sn)))
# BaseClass 明确记
bp=[p for p in main if NM[main[p]]=='.?AVBaseClass@@'][0]
ck('M7 BaseClass 被判为非 QI 形态且正偏移为空（v3 的假阳性已消除）',
   not an(VT[main[bp]][0])[0] and not pos(bp), (an(VT[main[bp]][0])[0], sorted(pos(bp))))
json.dump(dict(bad=bad,npos=npos,
               badA=len([p for p in main if pos(p) and tset(p)==pos(p)]),
               badB=len([p for p in main if pos(p) and tset(p)=={4}]),
               badC=len([p for p in main if not pos(p) and tset(p)==({4}|ALLP)]),
               dist=[[str(k),v] for k,v in dd.most_common()],ALLP=sorted(ALLP),
               s_pos=sorted(hex(x) for x in sn)),
          open('/home/t628/projects/ra2-campaign-forge/_r210/c20.json','w'),indent=0,ensure_ascii=False)
print('FAILS',fails)
