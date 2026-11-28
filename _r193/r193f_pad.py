#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R193 分歧裁定（§2.12 规则 D）：执行员 #471 报 both_has_ret=78 / HAS_RET|PAD_CC=10，
主会话 r193e 复算得 both_has_ret=88 / PAD_CC=0。10 对的差额必须逐对查清，不得取平均。

分歧根因假设：判定次序不同。
  H471（推测）：先查「原始字节里出现 >=2 连续 90/CC」⇒ 立即判 PAD，不再看 ret。
  MAIN（r193e）：先线性反汇编查 ret，命中即 HAS_RET。
本脚本给「可辩护口径」：填充只在**指令边界**上才算边界（capstone 解出来的那条指令是 nop/int3
且从它起 >=2 连续同类填充字节）。由此得 STRICT_RET / PAD_BEFORE_RET / WINDOW_OUT 三档，
并对 10 对逐对列出两侧入口字节 + 首个 ret 地址 + 首个指令边界填充地址 + 解码指令数。

主张（可被否掉）：
  P1 「103 对里真正两侧都没有 ret 的对数 = 0」在两种口径下都成立（PAD 不算无 ret，只是不可判）。
  P2 10 对的差额全部由「一侧入口落在填充/非法偏移上」解释，不是「该侧有两条 ret」。
  P3 若把 PAD_BEFORE_RET 也算作「无可用 ret」，则 103 对里两侧都无可用 ret 的对数 = 0。
"""
import sys, struct, collections, json, capstone
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
fails=[];N=0
def ck(nm,c,d=''):
    global N;N+=1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))
T=P.B['.text']; LO=T['lo']; HI=T['hi_file']
def in_text(x): return x is not None and LO<=x<HI
def wv(sn):
    s=P.B[sn]; n=s['rawsize']//4
    return s['lo'], struct.unpack_from('<%dI'%n,P.RAW,s['rawptr']), n
COL={}
for sn in ('.rdata','.data'):
    base,w,n=wv(sn)
    for i in range(n-4):
        if w[i] not in (0,1) or w[i+2]!=0: continue
        if P.where(w[i+3])!='.data' or P.where(w[i+4])!='.rdata': continue
        nm=P.cstr(w[i+3]+8,200)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base+4*i]=dict(mdisp=w[i+1],ptd=w[i+3],pchd=w[i+4],name=nm.decode('latin1'))
VT={}
for sn in ('.rdata','.data'):
    base,w,n=wv(sn)
    for i in range(n):
        if in_text(w[i]) and P.dw(base+4*i-4) in COL: VT[base+4*i]=P.dw(base+4*i-4)
def nslot(vt):
    k=0
    while in_text(P.dw(vt+4*k)): k+=1
    return k
NS={vt:nslot(vt) for vt in VT}
grp=collections.defaultdict(list)
for vt in sorted(VT): grp[COL[VT[vt]]['name']].append(vt)
def is_adj(va):
    o=P.r2o(va)
    if o is None: return False
    r=P.RAW[o:o+4]
    return r[0:3] in (b'\x83\x6c\x24',b'\x81\x6c\x24') and r[3]==0x04
direct=[(vt,k,P.dw(vt+4*k)) for vt in sorted(VT) if COL[VT[vt]]['mdisp']!=0
        for k in range(NS[vt]) if not is_adj(P.dw(vt+4*k))]
pairs=[]
for vt,k,v in direct:
    nm=COL[VT[vt]]['name']; sibs=[t for t in grp[nm] if t!=vt and k<NS[t]]
    if not sibs: continue
    t=sorted(sibs)[0]; w=P.dw(t+4*k)
    if w==v: continue                       # 只用 SAME 排除；THUNK_OTHER 也要列入对
    pairs.append((vt,k,v,t,w,is_adj(w)))
ck('P0 基线复现：直接槽 1013 / 可比对对 535', (len(direct),len(pairs))==(1013,535),(len(direct),len(pairs)))
def retn96(va,b=96):
    o=P.r2o(va)
    if o is None: return 'no-ret'
    for ins in md.disasm(P.RAW[o:o+b],va):
        if ins.mnemonic=='ret': return int(ins.op_str,16) if ins.op_str else 0
        if ins.mnemonic in ('jmp','int3','hlt') and ins.address>va: return 'no-ret'
    return 'no-ret'
inc=[(vt,k,v,t,w) for vt,k,v,t,w,adj in pairs if retn96(v)=='no-ret' or retn96(w)=='no-ret']
ck('P0b 96 字节不可解对 103（R192 值）', len(inc)==103, len(inc))

def pad_at_boundary(va,win=512):
    """返回 (类别, 首个 ret 地址, 首个指令边界填充地址, 解码条数, 首 16 字节)"""
    o=P.r2o(va)
    if o is None: return ('NONTEXT',None,None,0,'')
    code=P.RAW[o:o+win]; ret=None; pad=None; n=0
    for i in md.disasm(code,va):
        n+=1
        k=i.address-va
        if i.mnemonic in ('nop','int3'):
            b=code[k]
            if k+1<len(code) and code[k+1]==b:
                pad=i.address
                break
        if i.mnemonic in ('ret','retn'):
            ret=i.address
            break
    cat='WINDOW_OUT'
    if pad is not None: cat='PAD_BEFORE_RET'
    elif ret is not None: cat='STRICT_RET'
    return (cat,ret,pad,n,P.RAW[o:o+16].hex())
cache={}
def C(va):
    if va not in cache: cache[va]=pad_at_boundary(va)
    return cache[va]
ADJ={('%08X'%v,'%08X'%w):adj for vt,k,v,t,w,adj in pairs}
tab=collections.Counter(); strict_both=0; usable_both=0; detail=[]; rawpad=0
def raw_pad(va,win=512):
    o=P.r2o(va)
    if o is None: return False
    c=P.RAW[o:o+win]; run=1
    for k in range(1,len(c)):
        if c[k]==c[k-1] and c[k] in (0x90,0xCC): run+=1
        else: run=1
        if run>=2: return True
    return False
for vt,k,v,t,w in inc:
    a=C(v); b=C(w)
    tab[(a[0],b[0])]+=1
    if raw_pad(v) or raw_pad(w): rawpad+=1
    if a[0]=='STRICT_RET' and b[0]=='STRICT_RET': strict_both+=1
    if a[0]!='WINDOW_OUT' and b[0]!='WINDOW_OUT': usable_both+=1
    if (a[0]=='PAD_BEFORE_RET') ^ (b[0]=='PAD_BEFORE_RET'):
        li = a if a[0]=='PAD_BEFORE_RET' else b
        detail.append(dict(left='%08X'%v,right='%08X'%w,lc=a[0],rc=b[0],
            side=('L' if a[0]=='PAD_BEFORE_RET' else 'R'),
            padva=('%08X'%li[2]) if li[2] else None, retva=('%08X'%li[1]) if li[1] else None,
            nins=li[3], hexb=li[4], host=COL[VT[vt]]['name'], slot=k))
print('   三档交叉表：%s'%dict(tab))
print('   STRICT_RET|STRICT_RET %d / 两侧都不可判(WINDOW_OUT) %d / 两侧都非 WINDOW_OUT %d'
      %(strict_both, tab[('WINDOW_OUT','WINDOW_OUT')], usable_both))
print('\n   PAD_BEFORE_RET 出现在单侧的 %d 对：'%len(detail))
for d in detail:
    print('     %s vs %s  侧=%s pad@%s ret@%s n=%d host=%s slot=%d hex=%s'
          %(d['left'],d['right'],d['side'],d['padva'],d['retva'],d['nins'],d['host'],d['slot'],d['hexb']))
ck('P1 严格口径：两侧都完全无 ret 的对数 = 0（WINDOW_OUT|WINDOW_OUT == 0）',
   tab[('WINDOW_OUT','WINDOW_OUT')]==0, (tab[('WINDOW_OUT','WINDOW_OUT')], len(inc), strict_both))
ck('P1b 严格口径 STRICT_RET|STRICT_RET 的对数（本脚本值，须与 #471 的 78 或主会话的 88 之一相符）',
   strict_both in (78,88), strict_both)
ck('P2 实测：指令边界口径 PAD_BEFORE_RET = 10 对（不是 0）；原始字节 >=2 连续 90/CC 口径命中 %d 对'%rawpad,
   len(detail)==10 and rawpad==103, (len(detail),rawpad))
ck('P2b 原始字节口径命中的 10 对 == THUNK_OTHER 的那 10 对（同胞侧是调整器 thunk）',
   sum(1 for vt,k,v,t,w in inc if ADJ[('%08X'%v,'%08X'%w)])==10,
   sum(1 for vt,k,v,t,w in inc if ADJ[('%08X'%v,'%08X'%w)]))
ck('P3 实测：两侧都可判的 88 对 = STRICT_RET|STRICT_RET 78 + STRICT_RET|PAD 10；'
   '两侧都不可判 0 ⇒ 「两侧都无可用 ret」= 0',
   usable_both==88 and tab[('WINDOW_OUT','WINDOW_OUT')]==0
   and tab[('STRICT_RET','STRICT_RET')]+len(detail)==88,
   (usable_both,len(inc),tab[('WINDOW_OUT','WINDOW_OUT')]))
# 追跳：PAD 侧的调整器 thunk 尾部 E9 落到哪里，落点有没有 ret
follow=[]
for d in detail:
    va=int(d['padva'],16) if d['padva'] else None
    side=d['side']
    ent=int(d['left'] if side=='L' else d['right'],16)
    o=P.r2o(ent); tgt=None; kind=None
    if o is not None:
        r=P.RAW[o:o+16]
        if r[0:3]==b'\x81\x6c\x24' and r[8]==0xE9:      # 81 6C 24 04 imm32 ; E9 rel32
            kind='adjust48'; tgt=ent+13+struct.unpack_from('<i',r,9)[0]
        elif r[0:3]==b'\x83\x6c\x24' and r[5]==0xE9:    # 83 6C 24 04 imm8 ; E9 rel32
            kind='adjust36'; tgt=ent+10+struct.unpack_from('<i',r,6)[0]
        elif r[0]==0xE9:
            kind='plain'; tgt=ent+5+struct.unpack_from('<i',r,1)[0]
    c=C(tgt)[:4] if tgt else None
    follow.append(dict(ent='%08X'%ent,kind=kind,tgt=('%08X'%tgt) if tgt else None,
                       tgt_cls=(c[0] if c else None),tgt_ret=('%08X'%c[1]) if c and c[1] else None))
print('\n   PAD 侧追跳：')
for f in follow: print('     %s %s → %s  %s ret@%s'%(f['ent'],f['kind'],f['tgt'],f['tgt_cls'],f['tgt_ret']))
ck('P4 10 个 PAD 侧全部是调整器 thunk（83/81 6C 24 04 前缀 + E9 jmp），且其 E9 落点在严格口径下有 ret',
   all(f['kind'] in ('adjust36','adjust48') for f in follow)
   and all(f['tgt_cls']=='STRICT_RET' for f in follow),
   [(f['kind'],f['tgt_cls']) for f in follow])
# 反控
ck('N1 反控 0x41045F（ret 4 的立即数中间）在严格口径下判 PAD_BEFORE_RET 而不是 STRICT_RET',
   C(0x41045F)[0]=='PAD_BEFORE_RET', C(0x41045F)[:4])
ck('N2 正控 0x410450 STRICT_RET @0x41045E / 0x4C9150 STRICT_RET @0x4C9152',
   C(0x410450)[:2]==('STRICT_RET',0x41045E) and C(0x4C9150)[:2]==('STRICT_RET',0x4C9152),
   (C(0x410450)[:2],C(0x4C9150)[:2]))
ck('N3 反控 0x410220（#471 口径下槽 4 Top1）在严格口径下的分类',
   C(0x410220)[0] in ('STRICT_RET','PAD_BEFORE_RET'), C(0x410220)[:4])
json.dump(dict(inc=len(inc),tab={('%s|%s'%k):v for k,v in tab.items()},
   strict_both=strict_both,usable_both=usable_both,detail=detail,follow=follow,rawpad=rawpad,
   c410450=C(0x410450),c41045f=C(0x41045F),c410220=C(0x410220),fails=fails),
   open('_r193/r193f.json','w'),ensure_ascii=False,indent=1)
print('\n断言 %d 条，FAIL %d 条 %s'%(N,len(fails),fails))
sys.exit(1 if fails else 0)
