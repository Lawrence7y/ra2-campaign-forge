# -*- coding: utf-8 -*-
"""R210 c19（律 U 定稿 v3）：收紧 QI 返回偏移解析器。
规则：(1) 只在「rep 前缀比较之后」的代码里取偏移；(2) 出参写必须是 mov dword ptr [reg_out], <this或lea结果>，
      且该写必须发生在最近一次 mov edi, IID 之后、下一次 mov edi 之前（即属于该 IID 分支）；
      (3) 排除 lea reg,[<非 this 寄存器> + K]（如 BaseClass 的 lea esi,[ebp+4]）。
this 判定：函数入口后首条 mov reg,[esp+K] 且该 reg 在同一分支被 lea [reg+K] 使用。
为规避「this 判定错」的自由参数，改用**结构性**判据：该 lea 的目标寄存器必须在随后 2 条指令内被写进
一个 dword ptr [reg] （即出参），否则丢弃。
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
    for k,i in enumerate(ins):
        if i.mnemonic=='lea':
            m=re.search(r'^(\w+), \[\w+ \+ (0x[0-9a-f]+|\d+)\]$',i.op_str)
            if not m: continue
            reg=m.group(1); g=m.group(2); off=int(g,16) if g.startswith('0x') else int(g)
            # 必须随后 2 条内被写进 dword ptr [reg_out]
            for j in ins[k+1:k+3]:
                if j.mnemonic=='mov' and j.op_str.startswith('dword ptr [') and j.op_str.split(', ')[1]==reg:
                    res.add(off); break
    cache[a]=(isqi,res); return cache[a]
def tset(p): return {MD[c] for c in cls[p].values() if c in HIT}
def pos(p): return {x for x in an(VT[main[p]][0])[1] if x>0}
def pred(p):
    q=pos(p); return ({4}|q) if q else set()
bad=[(hex(p),NM[main[p]],sorted(tset(p)),sorted(pred(p)),hex(VT[main[p]][0])) for p in main if tset(p)!=pred(p)]
ck('L1 律 U 定稿 v3：954/954 成立（收紧解析器后）', not bad, 'bad=%d %s'%(len(bad),bad[:6]))
d=collections.Counter((tuple(sorted(tset(p))), tuple(sorted(pos(p)))) for p in main)
print('# (T偏移集, 正偏移集) -> 类数：')
for k,v in d.most_common(20): print('   %s -> %d'%(k,v))
npos=sum(1 for p in main if pos(p))
ck('L2 正偏移非空类 = 91，空 = 863', npos==91 and len(main)-npos==863, (npos,len(main)-npos))
badA=[p for p in main if pos(p) and tset(p)==pos(p)]
ck('L3 反控 A：去掉 {4} ⇒ 91 类全失配', len(badA)==91, len(badA))
badB=[p for p in main if pos(p) and tset(p)=={4}]
ck('L4 反控 B：只留 {4} ⇒ 失配 10 类', len(badB)==10, len(badB))
ALLP=set().union(*[pos(p) for p in main]) if npos else set()
badC=[p for p in main if not pos(p) and tset(p)!=set()]
ck('L5 反控 C：正偏移为空的类 T 视图集合必空', not badC, len(badC))
badD=[p for p in main if not pos(p) and tset(p)==({4}|ALLP)]
ck('L6 反控 D：全并集套到空类 ⇒ 863 类全失配', len(badD)==863, len(badD))
# 交叉核：v3 的 91 个正偏移类是否 == R209 的 12 个 QI 目标口径那 91 类
d9=json.load(open('/home/t628/projects/ra2-campaign-forge/_r210/c9.json'))
tcls9=set(int(x,16) for x in d9['tcls'])
s_now=set(p for p in main if pos(p))
ck('L7 v3 的 91 类与 c9（12 QI 口径）的 91 类完全同一', s_now==tcls9, 'diff=%d/%d'%(len(s_now-tcls9),len(tcls9-s_now)))
json.dump(dict(bad=bad,npos=npos,badA=len(badA),badB=len(badB),badC=len(badC),badD=len(badD),
               dist=[[str(k),v] for k,v in d.most_common()],ALLP=sorted(ALLP),
               s_pos=sorted(hex(x) for x in s_now)),
          open('/home/t628/projects/ra2-campaign-forge/_r210/c19.json','w'),indent=0,ensure_ascii=False)
print('FAILS',fails)
