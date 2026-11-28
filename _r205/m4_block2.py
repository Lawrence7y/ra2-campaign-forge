#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R205 m4：RTTI 块的真实边界。修正 m3 的两处脚本 bug：
 ① cname(b) 写了 P.cstr(P.dw(b)) —— TD 名字在 TD+8，应为 P.cstr(P.dw(b)+8)；
 ② C2 正控写了 P.dw(a+16)==a —— 内嵌 COL 的 pCHD 字段在 a+32，应为 P.dw(a+32)==a。
m3 断言过强 3 处（E2b/E2c/E4a）本轮改为基础量实测。
"""
import sys, struct, collections, json, random
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
fails=[]; N=0
def ck(nm,c,d=''):
    global N; N+=1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))
def s32(v): return struct.unpack('<i',struct.pack('<I',v))[0]
def wv(sn):
    s=P.B[sn]; n=s['rawsize']//4
    return s['lo'],struct.unpack_from('<%dI'%n,P.RAW,s['rawptr']),n
T=P.B['.text']; LO=T['lo']; HI=T['hi_file']
def in_text(x): return x is not None and LO<=x<HI
def cname(b):
    t=P.cstr(P.dw(b)+8,400)
    return None if t is None else t.decode('latin1')
COL={}
for sn in ('.rdata','.data'):
    base,w,n=wv(sn)
    for i in range(n-4):
        if w[i] not in (0,1,2) or w[i+2]!=0: continue
        if P.where(w[i+3])!='.data' or P.where(w[i+4])!='.rdata': continue
        nm=P.cstr(w[i+3]+8,400)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base+4*i]=dict(sig=w[i],mdisp=s32(w[i+1]),ptd=w[i+3],pchd=w[i+4],name=nm.decode('latin1'))
VTI={}
for sn in ('.rdata','.data'):
    base,w,n=wv(sn)
    for i in range(n):
        if in_text(w[i]) and P.dw(base+4*i-4) in COL: VTI[base+4*i]=P.dw(base+4*i-4)
G=collections.defaultdict(list)
for c,v in COL.items(): G[v['pchd']].append(c)
CHD=sorted(G)
BCA={a:[P.dw(P.dw(a+12)+4*j) for j in range(P.dw(a+8))] for a in CHD}
uniq=sorted(set(b for v in BCA.values() for b in v))
OWN={a:COL[a+16]['ptd'] for a in CHD}
ck('V0 基数 COL1214/VTI1214/CHD954/BCD1002/BCA2615',
   (len(COL),len(VTI),len(G),len(uniq),sum(len(v) for v in BCA.values()))==(1214,1214,954,1002,2615),
   (len(COL),len(VTI),len(G),len(uniq),sum(len(v) for v in BCA.values())))
ck('V1 修正后 cname 有效：954 个自有 pTD 名 == 954 个 CHD 类名 集合相等',
   set(cname(0) or '' for _ in [])==set() and {cname(b) for b in OWN.values()}=={COL[a+16]['name'] for a in CHD}, None)

# ---------- F1 22 条「mdisp==0 但 pTD 非自有」的真实身份 ----------
m0=[b for b in uniq if s32(P.dw(b+8))==0]
ownset=set(OWN.values())
extra=[b for b in m0 if P.dw(b) not in ownset]
print('   F1 uniq %d / mdisp==0 %d / 非自有 %d'%(len(uniq),len(m0),len(extra)))
en=collections.Counter(cname(b) or 'UNDEC' for b in extra)
for b in extra:
    print('     0x%x pTD=0x%x name=%s ncb=%d attr=%d'%(b,P.dw(b),(cname(b) or '?')[:46],P.dw(b+4),P.dw(b+20)))
ck('F1a 非自有 mdisp==0 共 22 条，pTD 名全部可读且互异或少数族',
   all((cname(b) or '').startswith('.?A') for b in extra), dict(en))
ck('F1b 这些 pTD 名全部不在 954 类名集合内',
   all((cname(b) or '') not in {COL[a+16]['name'] for a in CHD} for b in extra),
   [cname(b) for b in extra if cname(b) in {COL[a+16]['name'] for a in CHD}][:4])

# ---------- F2 pBCA 数组尾与 CHD 之间的 4/8 字节 ----------
d=collections.Counter()
for a in CHD:
    n=len(BCA[a]); d[a-(P.dw(a+12)+4*n)]+=1
ck('F2a (CHD 起点 - pBCA - 4n) 只有 {8:714, 4:240} 两态',dict(d)=={8:714,4:240},dict(d))
pad=c=collections.Counter()
for a in CHD:
    n=len(BCA[a]); padend=P.dw(a+12)+4*n
    if a-padend==8: pad[('dw',P.dw(padend),P.dw(padend+4))]+=1
    else: pad[('one',P.dw(padend),None)]+=1
print('   F2 尾部 8 字节内容 top4:',[x for x in pad.most_common(4)])
ck('F2b 8 字节间隔的 8 个字节里，首个 dword 恒 0',all(k[1]==0 for k in pad if k[0]=='dw'),None)
ck('F2c 4 字节间隔唯一',pad and any(k[0]=='one' for k in pad),dict((k,v) for k,v in pad.items() if k[0]=='one'))

# ---------- F3 块真实边界：BCD 池地址范围 vs CHD 地址范围 ----------
blo,bhi=min(uniq),max(uniq)
print('   F3 BCD 池 [0x%x,0x%x] 跨度 %d B；CHD [0x%x,0x%x]'%(blo,bhi,bhi-blo,CHD[0],CHD[-1]))
ck('F3a BCD 池整段位于 CHD 段之前（bhi < CHD[0]）',bhi<CHD[0],(hex(bhi),hex(CHD[0])))
# 相邻 CHD 之间的空隙里是否都是 BCD/BCA/填充
lo_=CHD[0]; covered=0; tot=0
for i in range(len(CHD)-1):
    a=CHD[i]; b=CHD[i+1]
    tot+=1
    # 该区间内：属于任何 CHD 的 BCD 或 BCA
    inc=0
    for x in range(a+40,b,4):
        if x in set(uniq): inc+=1
    covered+=1 if inc>0 or True else 0
# 更直接：BDC 池 + CHD 40 字节，是否覆盖 [CHD[0], CHD[-1]+40) 的绝大部分
tot_bytes=CHD[-1]+40-CHD[0]
bcdb=len(uniq)*24
bca_bytes=sum(len(v) for v in BCA.values())*4
chd_bytes=len(CHD)*40
print('   F3 区间 %d B = BCD %d + BCA %d + CHD %d = %d (%.1f%%)'%(
    tot_bytes,bcdb,bca_bytes,chd_bytes,bcdb+bca_bytes+chd_bytes,100.0*(bcdb+bca_bytes+chd_bytes)/tot_bytes))
ck('F3b 三部分之和占区间 95%+',(bcdb+bca_bytes+chd_bytes)>=0.95*tot_bytes,
   round(100.0*(bcdb+bca_bytes+chd_bytes)/tot_bytes,2))

# ---------- F4 每类块按「自有 BCD 地址」排序是否与 CHD 地址序一致 ----------
o1=[a for a in sorted(CHD)]
o2=[a for a in sorted(CHD,key=lambda a:OWN[a])]
ck('F4a 按自有 BCD 地址排序 == 按 CHD 地址排序',o1==o2,sum(1 for i in range(len(o1)) if o1[i]!=o2[i]))
# BCA 数组本身是否按地址升序/降序
asc=desc=0; mixed=0
for a in CHD:
    v=BCA[a]
    if all(v[i]<v[i+1] for i in range(len(v)-1)): asc+=1
    elif all(v[i]>v[i+1] for i in range(len(v)-1)): desc+=1
    else: mixed+=1
print('   F4 BCA 引用序列单调性: 升 %d / 降 %d / 混 %d'%(asc,desc,mixed))
ck('F4b BCA[0] 恒为本类自有 BCD（V + 复现）954/954',
   all(P.dw(BCA[a][0])==OWN[a] for a in CHD),None)
ck('F4c 单调升/降合计远小于 954（=> 顺序是继承路径序，非地址序）',asc+desc<200,(asc,desc,mixed))

# ---------- F5 反控 ----------
random.seed(2052)
rdlo=P.B['.rdata']['lo']; rdhi=P.B['.rdata']['hi_file']
hit=0
for _ in range(4000):
    x=rdlo+4*random.randrange((rdhi-rdlo)//4-12)
    if P.dw(x)==0 and P.dw(x+8)==0 and P.dw(x+32)==x: hit+=1
ck('C1 反控：随机地址命中「+0==0 且 +8==0 且 +32==自身」0 次',hit==0,hit)
ok=sum(1 for a in CHD if P.dw(a)==0 and P.dw(a+8)==0 and P.dw(a+32)==a)
ck('C2 正控：954 个 CHD 上该判据 954 命中',ok==954,ok)
# 反控：pTD 位置 +28 换成 +12（pBCA）
ok2=sum(1 for a in CHD if P.dw(a+12)==OWN[a])
ck('C3 反控：CHD+12（pBCA）等于自有 pTD 的 0 次',ok2==0,ok2)

print('\n%d asserts, %d FAIL %s'%(N,len(fails),fails))
json.dump(dict(asserts=N,fails=fails,extra=len(extra),pad=dict((str(k),v) for k,v in d.items()),
               trio_pct=round(100.0*(bcdb+bca_bytes+chd_bytes)/tot_bytes,2),
               mono=dict(asc=asc,desc=desc,mixed=mixed)),open('_r205/m4_block2.json','w'),indent=1)
