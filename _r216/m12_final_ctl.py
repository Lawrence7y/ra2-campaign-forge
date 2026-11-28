# -*- coding: utf-8 -*-
"""R216 m12：收口期全量自检（正控+反控），覆盖本轮全部进结论的数字。"""
import sys,struct,json,hashlib,collections,os
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
from capstone import *
mdl=Cs(CS_ARCH_X86,CS_MODE_32); mdl.skipdata=True
CK=[]
def ck(n,ok,d=''):
    CK.append((n,bool(ok),str(d))); print('[%s] %-58s %s'%('PASS' if ok else 'FAIL',n,d))
def o(va): return P.r2o(va)
def s32(v): return struct.unpack('<i',v)[0] if isinstance(v,(bytes,bytearray)) else struct.unpack('<i',struct.pack('<I',v&0xffffffff))[0]
def words(sn):
    s=P.B[sn];nn=s['rawsize']//4
    return struct.unpack_from('<%dI'%nn,P.RAW,s['rawptr']),s['lo']
COLA={}
for sn in ('.rdata','.data'):
    w,base=words(sn)
    for k in range(len(w)-4):
        if w[k]>2 or w[k+2]!=0: continue
        if P.where(w[k+3])!='.data' or P.where(w[k+4])!='.rdata': continue
        nm=P.cstr(w[k+3]+8,512)
        if not nm or nm[:3]!=b'.?A' or nm[-2:]!=b'@@': continue
        COLA[base+4*k]=(s32(w[k+1]),w[k+3],w[k+4],nm.decode('latin1'))
PRE=collections.defaultdict(list)
for sn in ('.rdata','.data'):
    w,base=words(sn)
    for k in range(len(w)-1):
        if w[k] in COLA and P.where(w[k+1])=='.text': PRE[w[k]].append(base+4*k)
starts=sorted(min(v)+4 for v in PRE.values() if len(v)==1)
S2C={min(v)+4:c for c,v in PRE.items() if len(v)==1}
VIEWS=[]
for i,st in enumerate(starts):
    end=starts[i+1] if i+1<len(starts) else P.B['.rdata']['hi_file']
    sl=[];a=st
    while a<end and P.where(P.dw(a))=='.text': sl.append(P.dw(a));a+=4
    md_,ptd,pchd,nm=COLA[S2C[st]]
    VIEWS.append(dict(base=st,slots=sl,mdisp=md_,ptd=ptd,pchd=pchd,nm=nm[1:] if nm.startswith('.') else nm))
VB={v['base']:v for v in VIEWS}
# A. 视图表基线
ck('views==1214',len(VIEWS)==1214,len(VIEWS))
ck('slots==14044',sum(len(v['slots']) for v in VIEWS)==14044)
ck('distinct==6692',len({x for v in VIEWS for x in v['slots']})==6692)
# B. AbstractClass 四视图
AC={v['mdisp']:(v['base'],len(v['slots'])) for v in VIEWS if v['nm']=='?AVAbstractClass@@'}
ck('AbstractClass mdisp 集合 == {0,4,8,12}',set(AC)=={0,4,8,12},AC)
ck('四视图 (base,slots) 对',AC=={0:(0x7e1f50,24),4:(0x7e1f34,6),8:(0x7e1f2c,1),12:(0x7e1f24,1)},AC)
ck('四视图 pTD/pCHD 全同',len({VB[b]['ptd'] for b,_ in AC.values()})==1 and len({VB[b]['pchd'] for b,_ in AC.values()})==1)
# C. slot8 四写
bx=P.RAW[o(0x4105a0):o(0x4105a0)+53]
want=bytes.fromhex('8a442404568bf1a801c706501f7e00c74604341f7e00c746082c1f7e00c7460c241f7e00740956e871853b0083c4048bc65ec20400')
ck('slot8 53 字节逐字节等于期望',bx==want,bx.hex()[:32])
hx8=bx.hex()
EXP4=['c706501f7e00','c74604341f7e00','c746082c1f7e00','c7460c241f7e00']
_pos=[hx8.find(e) for e in EXP4]
ck('slot8 内 4 条 mov vfptr 指令字节逐条存在且顺序递增',all(p>=0 for p in _pos) and _pos==sorted(_pos),_pos)
# D. QI 四 IID
ck('0x7f7c90 IID_IUnknown',P.RAW[o(0x7f7c90):o(0x7f7c90)+16]==bytes.fromhex('0000000000000000c000000000000046'))
ck('0x7f7c80 00000109',P.RAW[o(0x7f7c80):o(0x7f7c80)+16]==bytes.fromhex('0901000000000000c000000000000046'))
ck('0x7f7c70 0000010c',P.RAW[o(0x7f7c70):o(0x7f7c70)+16]==bytes.fromhex('0c01000000000000c000000000000046'))
ck('0x7e9ae0 170DAC82',P.RAW[o(0x7e9ae0):o(0x7e9ae0)+16]==bytes.fromhex('82ac0d17e412d2118175006008055bb5'))
ck('主视图 slot0 24 槽首值',VB[0x7e1f50]['slots'][0]==0x410260)
# E. 主视图 24 槽清单
EXP=[0x410260,0x410300,0x410310,0x4c9150,0x410450,0x4c9150,0x4c9150,0x4103e0,0x4105a0,0x410470,
     0x410480,0x4c9150,0x4c9150,0x410410,0x410490,0x4104a0,0x4104b0,0x410440,0x4104c0,0x4104f0,
     0x410520,0x410530,0x410540,0x410570]
ck('24 槽清单逐项相等',VB[0x7e1f50]['slots']==EXP)
for va,hx in ((0x410300,'b801000000c20400'),(0x4c9150,'33c0c3'),(0x410440,'b001c3'),(0x410490,'83c8ffc3'),
              (0x410520,'32c0c3'),(0x410530,'32c0c3'),(0x410470,'c3'),(0x410570,'c3'),(0x410480,'c20800')):
    ck('字节 %s == %s'%(hex(va),hx[:12]),P.RAW[o(va):o(va)+len(bytes.fromhex(hx))]==bytes.fromhex(hx))
# F. 律 U
SEC=[v for v in VIEWS if v['mdisp']!=0]
def head(va,n=16): return list(mdl.disasm_lite(P.RAW[o(va):o(va)+n],va))
okU=0;badU=0;form=collections.Counter()
for v in SEC:
    if not v['slots']: form['empty']+=1; continue
    h=head(v['slots'][0])
    if not h: form['undec']+=1; continue
    if h[0][2] not in ('sub','add') or not h[0][3].startswith('dword ptr [esp + 4], '):
        form[h[0][2]]+=1; continue
    imm=int(h[0][3].split(', ')[1],0); sgn=1 if h[0][2]=='sub' else -1
    j=[x for x in h if x[2]=='jmp']
    if not j: form['nojmp']+=1; continue
    jt=int(j[0][3],16)
    tv=next((vv for vv in VIEWS if vv['slots'] and vv['slots'][0]==jt),None)
    if tv is None: form['jt-not-view']+=1; continue
    if sgn*imm==v['mdisp']-tv['mdisp']: okU+=1
    else: badU+=1
ck('律 U 成立==101 且反例==0',okU==101 and badU==0,(okU,badU))
ck('次级视图总数==260',len(SEC)==260,len(SEC))
# G. 律 T 复算（文本解析口径，与 m5 一致）
t=P.B['.text'];tb=P.RAW[t['rawptr']:t['rawptr']+t['rawsize']];lo=t['lo'];n=len(tb)
hitsT=0;okT=0
for k in range(n-6):
    if tb[k]!=0xc7: continue
    m=tb[k+1];mod=m>>6;reg=(m>>3)&7;rm=m&7
    if reg!=0 or rm==4 or (mod==0 and rm==5): continue
    if mod==0: off=0;io=k+2
    elif mod==1: off=s32(struct.pack('<i',tb[k+2] if tb[k+2]<0x80 else tb[k+2]-256));io=k+3
    elif mod==2: off=s32(tb[k+2:k+6]);io=k+6
    else: continue
    if io+4>n: continue
    imm=struct.unpack_from('<I',tb,io)[0]
    if imm in VB:
        hitsT+=1
        if off==VB[imm]['mdisp']: okT+=1
ck('律 T 命中==4202',hitsT==4202,hitsT)
ck('律 T 符==3876',okT==3876,okT)
ck('律 T 违例==326',hitsT-okT==326,hitsT-okT)
# H. 反控：把 mdisp 全置 0，律 T 符数必须等于「off==0」的命中数（判据非常量）
ok0=0
for k in range(n-6):
    if tb[k]!=0xc7: continue
    m=tb[k+1];mod=m>>6;reg=(m>>3)&7;rm=m&7
    if reg!=0 or rm==4 or (mod==0 and rm==5): continue
    if mod==0: off=0;io=k+2
    elif mod==1: off=s32(struct.pack('<i',tb[k+2] if tb[k+2]<0x80 else tb[k+2]-256));io=k+3
    elif mod==2: off=s32(tb[k+2:k+6]);io=k+6
    else: continue
    if io+4>n: continue
    imm=struct.unpack_from('<I',tb,io)[0]
    if imm in VB and off==0: ok0+=1
ck('[反控] mdisp 全置 0 时符数=%d != 3876（判据非恒真）'%ok0, ok0!=okT and ok0>0, ok0)
# I. 落盘一致性
R={}
for nm,path,exp_cr in (('R14_COMMON','lead/next_re_20261117_r14/R14_COMMON.md',1081),
                       ('GOAL','lead/GOAL_THREE_TARGETS_20261018.md',337),
                       ('LOCK','lead/LEAD_LOCK',137),
                       ('BOARD','lead/next_re_20261117_r14/STATUS_BOARD.md',0)):
    b=open(path,'rb').read(); R[nm]=dict(cr=b.count(b'\r'),bytes=len(b),sha=hashlib.sha256(b).hexdigest()[:16])
    ck('%s CR==%d'%(nm,exp_cr),b.count(b'\r')==exp_cr,b.count(b'\r'))
ck('BOARD 行数<=300',R['BOARD']['bytes']>0 and open('lead/next_re_20261117_r14/STATUS_BOARD.md','rb').read().count(b'\n')<=300)
V599=open('lead/next_re_20261117_r14/R17_R131_FACTINDEX_V599/FACT_INDEX.tsv','rb').read()
ck('V599 sha==616a86e2…',hashlib.sha256(V599).hexdigest()=='616a86e251fd88e5d4fa7a3c488c15d65ce2c6e1bceb62de6d639ee1dca374e9')
ck('V599 bytes==277566',len(V599)==277566,len(V599))
V598=open('lead/next_re_20261117_r14/R17_R131_FACTINDEX_V598/FACT_INDEX.tsv','rb').read()
l598=V598.decode('utf-8').split('\n'); l599=V599.decode('utf-8').split('\n')
ck('V598/V599 仅 1 行不同',sum(1 for a,b in zip(l598,l599) if a!=b)==1 and len(l598)==len(l599))
ck('F29 正文字节==12751',len([x for x in l599 if x.startswith('F29\t')][0].split('\t')[1].encode())==12751)
print('\n=== 汇总 PASS=%d FAIL=%d ==='%(sum(1 for _,ok,_ in CK if ok),sum(1 for _,ok,_ in CK if not ok)))
json.dump({'ck':[[a,b,c] for a,b,c in CK],'lawU':[okU,badU],'lawT':[hitsT,okT],'neg_zero':ok0,'files':R},
  open('/home/t628/projects/ra2-campaign-forge/_r216/m12.json','w'),indent=1)
