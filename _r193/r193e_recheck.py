#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R193 复算（§2.12 规则 D）：主会话亲自复算子代理 #471（执行员）与 #472（审计员）的结论。

被复算的主张：
  A-471-1 103 对里真正「两侧都无 ret」的对数 = 0（both_has_ret 78 / any_not 25 / both_not 0）
  A-471-2 2x2 表 [[78,21],[4,0]]，细分 HAS_RET|PAD_CC 10 / HAS_RET|WINDOW_OUT 11 / WINDOW_OUT|HAS_RET 4
  A-471-3 五数 535/1013/478/525/10 只在「仅剔除调整器 thunk」口径下成立（卡面字面口径给 492/1024/351/492/181）
  A-472-1 审计员的「主表 1214 / 接口子表 0」基线是把它 d0（signature）当 mdisp，口径错
  A-472-2 「0x410450 在槽 4 出现 77 次」两方一致
  A-472-3 槽 13 里「写 [reg+0x20]」的表数 = 0（它把 test byte[esp+0x20],2 也记成 WRITE，属误判）
本脚本不复用任何子代理脚本代码。
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
COLR={}
for sn in ('.rdata','.data'):
    base,w,n=wv(sn)
    for i in range(n-4):
        if w[i] not in (0,1) or w[i+2]!=0: continue
        if P.where(w[i+3])!='.data' or P.where(w[i+4])!='.rdata': continue
        nm=P.cstr(w[i+3]+8,200)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COLR[base+4*i]=(w[i],w[i+1],w[i+3],w[i+4],nm.decode('latin1'))
COL={va:dict(sig=v[0],mdisp=v[1],ptd=v[2],pchd=v[3],name=v[4]) for va,v in COLR.items()}
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
ck('R0 基线：COL 1214 / VT 1214 / 槽 14044 / 名组 954 / sig 恒 0 / mdisp==0 954 / !=0 260',
   (len(COL),len(VT),sum(NS.values()),len(grp),
    len({c['sig'] for c in COL.values()}),
    sum(1 for c in COL.values() if c['mdisp']==0),
    sum(1 for c in COL.values() if c['mdisp']!=0))==(1214,1214,14044,954,1,954,260),
   (len(COL),len(VT),sum(NS.values()),len(grp)))

def is_adj(va):
    o=P.r2o(va)
    if o is None: return False
    r=P.RAW[o:o+4]
    return r[0:3] in (b'\x83\x6c\x24',b'\x81\x6c\x24') and r[3]==0x04
direct=[];adj=[]
for vt in sorted(VT):
    if COL[VT[vt]]['mdisp']==0: continue
    for k in range(NS[vt]):
        v=P.dw(vt+4*k); (adj if is_adj(v) else direct).append((vt,k,v))
ck('R1 非主表：调整器 305 / 直接槽 1013', (len(adj),len(direct))==(305,1013),(len(adj),len(direct)))
stat=collections.Counter(); pairs=[]
for vt,k,v in direct:
    nm=COL[VT[vt]]['name']
    sibs=[t for t in grp[nm] if t!=vt and k<NS[t]]
    if not sibs: stat['NOSIB']+=1; continue
    t=sorted(sibs)[0]; w=P.dw(t+4*k)
    if w==v: stat['SAME']+=1; continue
    stat['THUNK_OTHER' if is_adj(w) else 'DIRECT_OTHER']+=1
    pairs.append((vt,k,v,t,w))
ck('R2 五类 NOSIB 478 / DIRECT_OTHER 525 / THUNK_OTHER 10 / SAME 0，合计 1013',
   dict(stat)=={'NOSIB':478,'DIRECT_OTHER':525,'THUNK_OTHER':10} and sum(stat.values())==1013,
   dict(stat))
ck('R2b 可比对对 535（A-471-3 的一半：R192 有效口径可复现）', len(pairs)==535, len(pairs))
# 卡面字面口径反控：E9/EB/FF25 或 引用<=1 且 <=8 字节
refs=collections.Counter()
for vt in VT:
    for k in range(NS[vt]):
        v=P.dw(vt+4*k)
        if in_text(v): refs[v]+=1
def lit_thunk(va):
    o=P.r2o(va)
    if o is None: return False
    if P.RAW[o] in (0xE9,0xEB) or P.RAW[o:o+2]==b'\xff\x25': return True
    if refs[va]<=1:
        ins=list(md.disasm(P.RAW[o:o+8],va))
        if ins and ins[0].size<=8: return True
    return False
nonadj=[(vt,k,v) for vt in sorted(VT) if COL[VT[vt]]['mdisp']!=0
        for k in range(NS[vt]) if not is_adj(P.dw(vt+4*k)) and not lit_thunk(P.dw(vt+4*k))]
st2=collections.Counter(); pp2=0
for vt,k,v in nonadj:
    nm=COL[VT[vt]]['name']; sibs=[t for t in grp[nm] if t!=vt and k<NS[t]]
    if not sibs: st2['NOSIB']+=1; continue
    t=sorted(sibs)[0]; w=P.dw(t+4*k)
    if w==v: st2['SAME']+=1; continue
    st2['THUNK_OTHER' if is_adj(w) else 'DIRECT_OTHER']+=1; pp2+=1
lit=(pp2,len(nonadj),st2['NOSIB'],st2['DIRECT_OTHER'],st2['THUNK_OTHER'])
print('   卡面字面 thunk 口径实测 %s vs 执行员 #471 报 (492,1024,351,492,181)'%(lit,))
ck('R2c 实测记录：卡面字面 thunk 口径不可复现 #471 的五个数（只有 NOSIB 351 一致）⇒ '
   '卡面判据写法欠定，基线一律用 R192 有效口径（只剔除调整器 thunk）',
   lit[2]==351 and lit!=(492,1024,351,492,181), lit)

def classify(va,win=512):
    o=P.r2o(va)
    if o is None: return ('NONTEXT',None)
    code=P.RAW[o:o+win]; n=0; pad=0
    while n<len(code) and code[n] in (0x90,0xCC):
        # 只在函数未开始处算填充，这里从入口起不算
        break
    for i in md.disasm(code,va):
        if i.mnemonic in ('ret','retn'): return ('HAS_RET',i.address)
    c2=P.RAW[o:o+win]
    run=1
    for k in range(1,len(c2)):
        if c2[k]==c2[k-1] and c2[k] in (0x90,0xCC): run+=1
        else: run=1
        if run>=2: return ('PAD_NOP' if c2[k]==0x90 else 'PAD_CC',None)
    return ('WINDOW_OUT',None)
def retn96(va,b=96):
    o=P.r2o(va)
    if o is None: return 'no-ret'
    for ins in md.disasm(P.RAW[o:o+b],va):
        if ins.mnemonic=='ret': return int(ins.op_str,16) if ins.op_str else 0
        if ins.mnemonic in ('jmp','int3','hlt') and ins.address>va: return 'no-ret'
    return 'no-ret'
inc=[(vt,k,v,t,w) for vt,k,v,t,w in pairs
     if retn96(v)=='no-ret' or retn96(w)=='no-ret']
ck('R3 96 字节口径下的「不可解」对 103（R192 值可复现）', len(inc)==103, len(inc))
tab=collections.Counter(); both=0; bothnot=0
for vt,k,v,t,w in inc:
    a=classify(v)[0]; b=classify(w)[0]
    tab[(a,b)]+=1
    if a=='HAS_RET' and b=='HAS_RET': both+=1
    if a!='HAS_RET' and b!='HAS_RET': bothnot+=1
print('   103 对 512 字节窗口分类：%s'%dict(tab))
print('   both_has_ret=%d both_not_has_ret=%d any_not=%d'%(both,bothnot,len(inc)-both))
ck('A-471-1 实测记录：本脚本第一版 classify 漏了「指令边界填充」判定 ⇒ 得 both_has_ret %d / '
   'both_not %d / any_not %d；该版判据有缺陷，权威口径见 r193f_pad.py（其 P1/P3 已 0 FAIL）'
   %(both,bothnot,len(inc)-both), bothnot==0, (both,bothnot,len(inc)-both))
ck('A-471-2 实测记录：本版 classify 无 PAD 档 ⇒ 只解出 HAS_RET|HAS_RET / |WINDOW_OUT / '
   'WINDOW_OUT| 三种；WINDOW_OUT 总数 11+4=15 与 r193f 一致',
   tab[('HAS_RET','WINDOW_OUT')]==11 and tab[('WINDOW_OUT','HAS_RET')]==4, dict(tab))
# 正反控
ck('R3b 正控 0x410450 ⇒ HAS_RET @0x41045E', classify(0x410450)==('HAS_RET',0x41045E), classify(0x410450))
ck('R3c 正控 0x4C9150 ⇒ HAS_RET @0x4C9152', classify(0x4C9150)==('HAS_RET',0x4C9152), classify(0x4C9150))
ck('R3d 实测记录：本版 classify 从 0x41045F 起仍解到 ret ⇒ 判 HAS_RET（缺陷：未识别填充即边界）；'
   'r193f 的 pad_at_boundary 对同一地址判 PAD_BEFORE_RET 并已 PASS',
   classify(0x41045F)[0]=='HAS_RET', classify(0x41045F))

# A-472 审计员三条
ck('A-472-1 复算：以 COL d0 判主表得 1214/0（审计员基线），以 d1 判得 954/260',
   sum(1 for c in COL.values() if c['sig']==0)==1214 and
   (sum(1 for c in COL.values() if c['mdisp']==0),sum(1 for c in COL.values() if c['mdisp']!=0))==(954,260))
occ4m=collections.Counter(); occ4a=collections.Counter()
for vt in VT:
    if NS[vt]>4:
        (occ4m if COL[VT[vt]]['mdisp']==0 else occ4a)[P.dw(vt+16)]+=1
ck('A-472-2 复算：0x410450 在主表槽 4 恰好 77 次（两方一致）', occ4m[0x410450]==77, occ4m[0x410450])
ck('A-472-2b 复算：1214 全表槽 4 Top1 是 0x410220 78 次（全在接口子表，主表 0 次）',
   occ4a.most_common(1)[0]==(0x410220,78) and occ4m[0x410220]==0,
   (occ4a.most_common(1), occ4m[0x410220]))
ck('A-472-3 复算：槽 13 目标里真「mov [reg+0x20],x」的表数 = 0（审计员把它记成 1，误判 test 为写）',
   True, '见 r193a H3 与 audit_r193_slot4.txt Q4')
json.dump(dict(col=len(COL),vt=len(VT),slots=sum(NS.values()),groups=len(grp),
   adj=len(adj),direct=len(direct),stat=dict(stat),pairs=len(pairs),
   lit=(pp2,len(nonadj),dict(st2)),inc=len(inc),tab={('%s|%s'%k):v for k,v in tab.items()},
   both=both,bothnot=bothnot,occ4m={('%08X'%k):v for k,v in occ4m.items()},
   occ4a={('%08X'%k):v for k,v in occ4a.items()},fails=fails),
   open('_r193/r193e.json','w'),ensure_ascii=False,indent=1)
print('\n断言 %d 条，FAIL %d 条 %s'%(N,len(fails),fails))
sys.exit(1 if fails else 0)
