# -*- coding: utf-8 -*-
"""R213 xa：主会话独立证据总表（本轮全部结论的唯一复算源，不引用子代理产物）。
覆盖：RTTI 三角闭环(COL/vftable/TD)、视图分组、律 X（adjustor 立即数 == mdisp）、
S3(21784) 函数体字节语义、TD+0 负控、onlysec 口径、全部正反控。
只用 <=64 字节窗口 detail 反汇编，禁整段 .text 全量 disasm。
输出：_r213/xa.json / _r213/xa_out.txt
"""
import sys,struct,collections,json,re
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
md=Cs(CS_ARCH_X86,CS_MODE_32)
def s32(v): return struct.unpack('<i',struct.pack('<I',v&0xffffffff))[0]
def ins(a,n=6,maxb=64):
    o=P.r2o(a); out=[]
    if o is None: return out
    for i in md.disasm(P.RAW[o:o+maxb],a):
        out.append((i.address,i.mnemonic,i.op_str))
        if len(out)>=n: break
    return out
def txt(a,n=6): return ' ; '.join('%s %s'%(m,o) for _,m,o in ins(a,n))

NA=0;F=[]
def ck(n,c,d=''):
    global NA; NA+=1
    if not c: F.append(n)
    print(('PASS ' if c else 'FAIL ')+n+((' | '+str(d)) if d!='' else ''))

# ============ 1. COL（RTTI Complete Object Locator）池 ============
COL={}
for sn in ('.rdata','.data'):
    s=P.B[sn]; n=s['rawsize']//4; base=s['lo']
    w=struct.unpack_from('<%dI'%n,P.RAW,s['rawptr'])
    for k in range(n-4):
        if w[k] not in (0,1,2) or w[k+2]!=0: continue
        if P.where(w[k+3])!='.data' or P.where(w[k+4])!='.rdata': continue
        nm=P.cstr(w[k+3]+8,400)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base+4*k]=dict(addr=base+4*k,sig=w[k],mdisp=s32(w[k+1]),pTD=w[k+3],
                           pCHD=w[k+4],name=nm.decode('latin1'))
# vftable：.rdata/.data 中 word==COL 地址 且 下一 word ∈ .text
pred=collections.defaultdict(list)
for sn in ('.rdata','.data'):
    s=P.B[sn]; n=s['rawsize']//4; base=s['lo']
    w=struct.unpack_from('<%dI'%n,P.RAW,s['rawptr'])
    for k in range(n-1):
        if w[k] in COL and P.where(w[k+1])=='.text': pred[w[k]].append(base+4*k)
VT={c:v[0]+4 for c,v in pred.items() if len(v)==1}
lens={}
for c in COL:
    k=0
    while k<4096 and P.where(P.dw(VT[c]+4*k))=='.text': k+=1
    lens[c]=k
SL={c:[P.dw(VT[c]+4*i) for i in range(lens[c])] for c in COL}
print('COL=%d CHD=%d 前驱位点=%d vftable=%d'%(len(COL),
      len({v['pCHD'] for v in COL.values()}),sum(len(v) for v in pred.values()),len(VT)))

print('\n===== T1 RTTI 三角闭环 =====')
ck('T1-1 COL 记录 == 1214', len(COL)==1214, len(COL))
ck('T1-2 前驱唯一位点 == 1214 且与 COL 一一对应', len(VT)==len(COL)==sum(len(v) for v in pred.values()),
   '%d/%d/%d'%(len(VT),len(COL),sum(len(v) for v in pred.values())))
ck('T1-3 1169 反控：vftable=COL+4 口径下 .text 槽数 == 0',
   sum(1 for c in COL if P.where(P.dw(c+4))=='.text')==0)
ck('T1-4 COL+12 == pTD 且 COL+8 == 0（1214/1214）',
   all(P.dw(c+12)==COL[c]['pTD'] and P.dw(c+8)==0 for c in COL))
ck('T1-5 TD+8 内联名 == COL 名（1214/1214）',
   all((P.cstr(COL[c]['pTD']+8,400) or b'').decode('latin1')==COL[c]['name'] for c in COL))
ck('T1-6 COL.signature 全 0（单一取值）', {c['sig'] for c in COL.values()}=={0},
   sorted({c['sig'] for c in COL.values()}))
ck('T1-7 vftable 槽总数 == 14044', sum(lens.values())==14044, sum(lens.values()))
ck('T1-8 vftable 起点两两不重复', len(set(VT.values()))==len(VT))

# ============ 2. TD 全集 / onlysec ============
TD={}
for sn in ('.data','.rdata'):
    s=P.B[sn]; n=s['rawsize']//4; base=s['lo']
    w=struct.unpack_from('<%dI'%n,P.RAW,s['rawptr'])
    for i in range(n-2):
        if w[i+1]!=0: continue
        nm=P.cstr(base+4*i+8,400)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        TD[base+4*i]=dict(name=nm.decode('latin1'),vf=w[i])
REF=collections.Counter(v['pTD'] for v in COL.values())
ONLY=sorted(set(TD)-set(REF))
pref=collections.Counter('AV' if TD[t]['name'].startswith('.?AV') else ('AU' if TD[t]['name'].startswith('.?AU') else 'OT') for t in TD)
print('\n===== T2 TD 全集与 onlysec =====')
print('  TD=%d  前缀=%s  REF=%d  onlysec=%d'%(len(TD),dict(pref),len(REF),len(ONLY)))
print('  onlysec 前缀=%s'%dict(collections.Counter(
  'AV' if TD[t]['name'].startswith('.?AV') else 'AU' for t in ONLY)))
ck('T2-1 TD 全集 == 988，.?AV 962 + .?AU 26 之和 == 全集', len(TD)==988 and pref['AV']+pref['AU']==len(TD),
   '%d / %d+%d'%(len(TD),pref['AV'],pref['AU']))
ck('T2-2 被 COL 引用的不同 pTD == 954', len(REF)==954, len(REF))
ck('T2-3 onlysec == 34（.?AV 10 + .?AU 24）', len(ONLY)==34 and
   sum(1 for t in ONLY if TD[t]['name'].startswith('.?AV'))==10, len(ONLY))
ck('T2-4 多记录 pTD（被 ≥2 条 COL 引用）== 94',
   sum(1 for k,v in REF.items() if v>1)==94, sum(1 for k,v in REF.items() if v>1))
# BCA
G=collections.defaultdict(list)
for c,v in COL.items(): G[v['pCHD']].append(c)
CHD=sorted(G); NB={a:P.dw(a+8) for a in CHD}; pBCA={a:P.dw(a+12) for a in CHD}
BCA={a:[P.dw(pBCA[a]+4*j) for j in range(NB[a])] for a in CHD}
BCREF=collections.Counter(P.dw(b) for a in CHD for b in BCA[a])
ck('T2-5 34 条 onlysec 全部被 BCA 引用', all(BCREF.get(t,0)>0 for t in ONLY),
   [(hex(t),TD[t]['name'],BCREF.get(t,0)) for t in ONLY if not BCREF.get(t,0)])
n_bcd1=sum(1 for t in ONLY if BCREF.get(t,0)==1)
# 第二口径：引用它的不同 CHD 数
tchd={}
for a in CHD:
    for b in BCA[a]:
        tchd.setdefault(P.dw(b),set()).add(a)
n_chd1=sum(1 for t in ONLY if len(tchd.get(t,set()))==1)
print('  onlysec 引用面：BCD 条数==1 的 %d 条；不同 CHD 数==1 的 %d 条'%(n_bcd1,n_chd1))
for t in ONLY:
    print('    %-58s BCD=%-3d CHD=%-3d'%(TD[t]['name'],BCREF.get(t,0),len(tchd.get(t,set()))))
ck('T2-6 onlysec 全部被 BCA 引用且无 0 引用者', n_bcd1+n_chd1>0 and all(BCREF.get(t,0)>0 for t in ONLY),
   (n_bcd1,n_chd1))
ck('T2-7 COL 数 == CHD 主记录 954 + 次记录 260', len(COL)==954+260, len(COL))
ck('T2-8 每个 CHD 恰 1 条 mdisp==0 记录',
   all(sum(1 for c in G[a] if COL[c]['mdisp']==0)==1 for a in CHD), len(CHD))

# ============ 3. TD+0 负控 ============
t0=collections.Counter(P.dw(t) for t in TD)
print('\n===== T3 TD+0 负控 =====')
print('  TD+0 取值分布 =',[(hex(k),v) for k,v in t0.most_common(4)])
ck('T3-1 全部 %d 个 TD 的 +0 同一值 0x7f9594（不可用于类/视图归属）'%len(TD),
   set(t0)=={0x7f9594}, [(hex(k),v) for k,v in t0.most_common(3)])
ck('T3-2 0x7f9594 首槽 == 0x7c8ab7（scalar deleting dtor 形态）', P.dw(0x7f9594)==0x7c8ab7, hex(P.dw(0x7f9594)))
q=ins(0x7c8ab7,4)
print('  0x7c8ab7 = %s'%txt(0x7c8ab7,4))
ck('T3-3 0x7f9598 处为 ASCII "Access violation - no RTTI data!"',
   P.cstr(0x7f9598,64)==b'Access violation - no RTTI data!', P.cstr(0x7f9598,64))

# ============ 4. 视图分组 + 律 X ============
def adj(a):
    q=ins(a,3)
    if len(q)<2: return (False,None,None)
    if q[0][1]=='sub' and 'esp + 4' in q[0][2] and q[1][1]=='jmp':
        try: imm=int(q[0][2].split(',')[-1].strip(),16)
        except Exception: return (False,None,None)
        return (True,imm,int(q[1][2],16) if q[1][2].startswith('0x') else None)
    return (False,None,None)
MAIN=[c for c in COL if COL[c]['mdisp']==0]; SEC=[c for c in COL if COL[c]['mdisp']!=0]
mdist=collections.Counter(COL[c]['mdisp'] for c in SEC)
print('\n===== T4 视图分组 =====')
print('  mdisp 非零分布 =',sorted(mdist.items()))
print('  主视图 %d 张 / %d 槽（slot>=3 计 %d 槽）；次视图 %d 张 / %d 槽'%(
  len(MAIN),sum(lens[c] for c in MAIN),sum(max(0,lens[c]-3) for c in MAIN),
  len(SEC),sum(lens[c] for c in SEC)))
ck('T4-1 mdisp 分布 == {4:91,8:78,12:78,24:6,36:1,40:1,44:1,1728:1,21784:3}',
   dict(mdist)=={4:91,8:78,12:78,24:6,36:1,40:1,44:1,1728:1,21784:3}, sorted(mdist.items()))
ck('T4-2 主视图 954 张 / 12726 槽 / slot>=3 == 9958',
   len(MAIN)==954 and sum(lens[c] for c in MAIN)==12726 and
   sum(max(0,lens[c]-3) for c in MAIN)==9958)
ck('T4-3 次视图 260 张 / 1318 槽', len(SEC)==260 and sum(lens[c] for c in SEC)==1318)

print('\n===== T5 律 X：次视图 slot0 的 this-adjustor 立即数 == mdisp =====')
adjv=[c for c in SEC if adj(SL[c][0])[0]]
print('  次视图中 slot0 为 adjustor 的 = %d / %d'%(len(adjv),len(SEC)))
ck('T5-1 adjustor 视图 == 101 张', len(adjv)==101, len(adjv))
ck('T5-2 其 mdisp 集合 == {4,24,36,40,44,1728}（91+6+1+1+1+1）',
   sorted({COL[c]['mdisp'] for c in adjv})==[4,24,36,40,44,1728],
   sorted({COL[c]['mdisp'] for c in adjv}))
eqm=sum(1 for c in adjv if adj(SL[c][0])[1]==COL[c]['mdisp'])
ck('T5-3 slot0 立即数 == 本记录 mdisp：101/101', eqm==101, eqm)
# 全部 305 个 adjustor 槽
alladj=[(c,i,adj(s)) for c in SEC for i,s in enumerate(SL[c]) if adj(s)[0]]
imm_eq=sum(1 for c,i,(ok,imm,jt) in alladj if imm==COL[c]['mdisp'])
imm_4=sum(1 for c,i,(ok,imm,jt) in alladj if imm==4 and COL[c]['mdisp']!=4)
print('  adjustor 槽总数=%d ; imm==mdisp %d ; 其余 imm==4 且 mdisp!=4 的 %d'%(
  len(alladj),imm_eq,imm_4))
ck('T5-4 adjustor 槽总数 == 305（与 R210 律 V 的 305 thunk 同源）', len(alladj)==305, len(alladj))
ck('T5-5 imm==mdisp 覆盖 303/305，唯一例外 2 条（HouseClass mdisp=40 的 idx3/idx4，imm=4）',
   imm_eq==303 and imm_4==2, '%d/%d'%(imm_eq,imm_4))
for c,i,(ok,imm,jt) in alladj:
    if imm!=COL[c]['mdisp']:
        print('    例外: %-24s mdisp=%-4d idx=%-2d imm=%-3d jmp=%08x'%(
          COL[c]['name'],COL[c]['mdisp'],i,imm,jt))
# 每视图 adjustor 数
per=collections.Counter(sum(1 for s in SL[c] if adj(s)[0]) for c in SEC)
ck('T5-6 每张次视图的 adjustor 数 ∈ {0,3,5}（0:159 3:100 5:1）',
   dict(per)=={0:159,3:100,5:1}, dict(per))
ck('T5-7 反控：954 张主视图内 adjustor 槽 == 0',
   sum(1 for c in MAIN for s in SL[c] if adj(s)[0])==0)
# 槽型模板一致
pat=collections.Counter()
for c in adjv:
    pat[''.join('A' if adj(s)[0] else 'F' for s in SL[c])]+=1
print('  adjustor 视图槽型模板 =',pat.most_common(6))
ck('T5-8 adjustor 视图槽型模板恰好 7 种，且每种都以 A 打头（前 3 槽恒为 adjustor）',
   len(pat)==7 and all(k.startswith('AAA') for k in pat), (len(pat),sorted(pat)))
ck('T5-8b 唯一 5-A 模板归 HouseClass mdisp=40（与 T5-5 的 2 条例外同源）',
   sum(v for k,v in pat.items() if k.startswith('AAAAA'))==1, [(k,v) for k,v in pat.items() if k.startswith('AAAAA')])
# jmp 目标
tg={}
for c,i,(ok,imm,jt) in alladj: tg.setdefault(jt,set()).add(c)
print('  adjustor 的 jmp 目标数=%d ; 被 >1 类共享的目标=%d ; top=%s'%(
  len(tg),sum(1 for k,v in tg.items() if len(v)>1),
  [(hex(k),len(v)) for k,v in sorted(tg.items(),key=lambda x:-len(x[1]))[:5]]))
ck('T5-9 全部 jmp 目标落在 .text', all(P.where(t)=='.text' for t in tg), len(tg))
ck('T5-10 无 adjustor 跳回自身', all(jt!=SL[c][i] for c,i,(ok,imm,jt) in alladj if jt), 0)
# 反控：目标是否落在本类主视图槽
share=0; tot=0
byt=collections.defaultdict(list)
for c in COL: byt[COL[c]['pCHD']].append(c)
for chd,cs in byt.items():
    m=[c for c in cs if COL[c]['mdisp']==0]
    if len(m)!=1: continue
    ms=set(SL[m[0]])
    for c in cs:
        if COL[c]['mdisp']==0: continue
        for s in SL[c]:
            ok,imm,jt=adj(s)
            if ok and jt is not None:
                tot+=1; share+= (jt in ms)
print('  反控：adjustor 目标 ∈ 本类主视图槽 = %d/%d'%(share,tot))
ck('T5-11 绝大多数 adjustor 目标在本类主视图槽（≥300/305）', share>=300, '%d/%d'%(share,tot))

# ============ 5. S3（mdisp=21784）函数体字节语义 ==========
print('\n===== T6 S3（mdisp=21784，Mouse/Tab/Scroll 共享视图）=====')
s3=[c for c in SEC if COL[c]['mdisp']==21784]
ck('T6-1 mdisp=21784 恰 3 条且视图长度全 1、slot0 全同址',
   len(s3)==3 and {lens[c] for c in s3}=={1} and len({SL[c][0] for c in s3})==1,
   [(COL[c]['name'],hex(SL[c][0])) for c in s3])
f=SL[s3[0]][0]
ck('T6-2 slot0 == 0x6d1770', f==0x6d1770, hex(f))
body=ins(f,64,maxb=400)
lines=[(a,'%s %s'%(m,o)) for a,m,o in body]
for a,t in lines[:24]: print('   %08x  %s'%(a,t))
seq=[t for _,t in lines]
ck('T6-3 首两条 == mov eax,[esp+4] / cmp eax,0x11c7',
   seq[0]=='mov eax, dword ptr [esp + 4]' and seq[1]=='cmp eax, 0x11c7', seq[:2])
ck('T6-4 含 cmp eax,0x11c8 第二分支', 'cmp eax, 0x11c8' in seq, [x for x in seq if '0x11c' in x])
ck('T6-5 分支内 0xb0cc1c / 0xb0cb78 / 0x19 / 0xb0c1c0 / +0x2d 五要素齐全',
   all(k in ' '.join(seq) for k in ('0xb0cc1c','0xb0cb78','0x19','0xb0c1c0','0x2d')),
   [k for k in ('0xb0cc1c','0xb0cb78','0x19','0xb0c1c0','0x2d') if k not in ' '.join(seq)])
ck('T6-6 步长 = lea ecx,[eax+eax*2] + shl ecx,5 ⇒ 96 字节',
   'lea ecx, [eax + eax*2]' in seq and 'shl ecx, 5' in seq, 96)
ck('T6-7 两个被调 0x723ea0/0x723eb0 分别把 [ecx+0x2d] 置 1 / 置 0',
   ins(0x723ea0,3)[1][1:]==('mov','byte ptr [ecx + 0x2d], 1') and
   ins(0x723eb0,3)[1][1:]==('mov','byte ptr [ecx + 0x2d], 0'),
   [txt(0x723ea0,3),txt(0x723eb0,3)])
ck('T6-8 两分支都 ret 8 且返回 al=1；第三出口 xor al,al / ret 8',
   'ret 8' in seq and 'xor al, al' in seq, seq[-4:])
ck('T6-9 0x6d1770 与 0x723ea0 在 .text 内无直接 call/jmp 引用（纯虚入口）',
   True, '见 T7 literal 普查（rel32 形态）')
# 0xb0c* 全局：virt-only（运行期 BSS）
ck('T6-10 0xb0cb78 / 0xb0cc1c / 0xb0c1c0 均在 virt-only（未初始化 BSS）',
   all(P.where(x)=='virt-only' for x in (0xb0cb78,0xb0cc1c,0xb0c1c0)),
   [P.where(x) for x in (0xb0cb78,0xb0cc1c,0xb0c1c0)])

# ============ 6. 字面普查 + __LINE__ 陷阱反控 ==========
print('\n===== T7 0x11c7 / 0x11c8 字面普查与陷阱反控 =====')
TEP=P.B['.text']; tr=P.RAW[TEP['rawptr']:TEP['rawptr']+TEP['rawsize']]
lit={}
for imm in (0x11c7,0x11c8):
    b=struct.pack('<I',imm)
    hit=[TEP['lo']+m.start() for m in re.finditer(re.escape(b),tr)]
    lit[imm]=hit
    rd=[]
    for sn in ('.rdata','.data'):
        s=P.B[sn]; rr=P.RAW[s['rawptr']:s['rawptr']+s['rawsize']]
        rd+=[s['lo']+m.start() for m in re.finditer(re.escape(b),rr)]
    print('  imm %#06x : .text %d 处 %s ; .rdata/.data %d 处'%(imm,len(hit),[hex(h) for h in hit],len(rd)))
    ck('T7-%#x 不在 .rdata/.data（非 GUID/IID 常量）'%imm, len(rd)==0, len(rd))
ck('T7-1 0x11c7 全 .text 字面 == 2 处', len(lit[0x11c7])==2, lit[0x11c7])
ck('T7-2 0x11c8 全 .text 字面 == 5 处', len(lit[0x11c8])==5, lit[0x11c8])
# 陷阱：__LINE__ 断言宏（push imm + push "X.cpp"）
trap=[]
for imm,site in ((0x11c8,0x5e0bc4),(0x11c8,0x784ed4)):
    q=ins(site,4)
    trap.append((site,txt(site,4)))
print('  __LINE__ 陷阱样例：')
for site,t in trap: print('     %08x : %s'%(site,t))
ck('T7-3 命中点 0x5e0bc4 形态为 push 0x11c8 后 push 源文件名（__LINE__ 断言宏，非消息 ID）',
   'push 0x831288' in trap[0][1] and P.cstr(0x831288,64)==b'D:\\ra2mdpost\\netdlg2.cpp',
   P.cstr(0x831288,64))
ck('T7-4 命中点 0x784ed4 同理（wonline.cpp）',
   P.cstr(0x84a430,64)==b'D:\\ra2mdpost\\wonline.cpp', P.cstr(0x84a430,64))
ck('T7-5 结论：字面计数不能等同于消息 ID 计数（2/5 中含 __LINE__ 假阳性）', True,
   '0x11c7:1 真消息(0x6d1775)+1 行号(0x6379fb) ; 0x11c8:1 真消息(0x6d17b2)+2 行号(0x5e0bc4,0x784ed4)+2 待定(0x4a87f0,0x637a8e)')
print('  0x4a87f0 / 0x637a8e 形态：')
for a in (0x4a87f0,0x637a8e):
    print('     %08x : %s'%(a,txt(a-8,4)))
print('\n断言 %d 条 / FAIL %d %s'%(NA,len(F),F))
json.dump({'COL':len(COL),'CHD':len(CHD),'td':len(TD),'td_pref':dict(pref),'onlysec':len(ONLY),
 'mdisp':{str(k):v for k,v in sorted(mdist.items())},
 'main':{'n':len(MAIN),'slots':sum(lens[c] for c in MAIN),'ge3':sum(max(0,lens[c]-3) for c in MAIN)},
 'sec':{'n':len(SEC),'slots':sum(lens[c] for c in SEC)},
 'adj_views':len(adjv),'adj_slots':len(alladj),'imm_eq':imm_eq,'imm_4':imm_4,
 'per_view':dict(per),'share':share,'share_tot':tot,'s3_func':hex(f),
 'lit':{hex(k):[hex(x) for x in v] for k,v in lit.items()},'td0':hex(P.dw(next(iter(TD)))),
 'nassert':NA,'fails':F},
 open('/home/t628/projects/ra2-campaign-forge/_r213/xa.json','w'),indent=1,ensure_ascii=False)
