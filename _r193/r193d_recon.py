#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R193 第四刀：与审计员 #472 的基线分歧定位 + 槽 13 序列化辅助函数定性。

审计员报「COL 条数 1214 / 主表(d0=0) 1214 / 接口子表 0」，而四轮已证的基线是
主表 954 + 接口子表 260。本脚本判定谁的口径对：
  D1 COL 五个 dword 的实际取值分布 —— 若 d0 恒为 0（signature），d1 才有 0/非 0 两类，
     则「以 d0 判主表」必然把 1214 全判成主表，审计员的基线是错的。
  D2 按 d1（= MSVC COL 的 offset 字段）分裂：0 与 非 0 两张数。
  D3 逐槽 Top 在两种分母下各是多少（审计员报槽 4 Top1 = 0x410220 78 次；
     我在 954 主表上测得 0x410450 77 次 —— 差异必须由分母解释，否则是本轮结论有错）。
  D4 0x410450 / 0x410220 / 0x410580 / 0x410590 四个地址的全槽号分布与表类型分布。
  D5 槽 13 的 0x410410 调用的两个辅助 0x4A1D50 / 0x4A1CA0 是什么（体首 + 是否含 call [reg+off]）。
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
RAWCOL={}
for sn in ('.rdata','.data'):
    base,w,n=wv(sn)
    for i in range(n-4):
        if w[i] not in (0,1) or w[i+2]!=0: continue
        if P.where(w[i+3])!='.data' or P.where(w[i+4])!='.rdata': continue
        nm=P.cstr(w[i+3]+8,200)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        RAWCOL[base+4*i]=(w[i],w[i+1],w[i+2],w[i+3],w[i+4],nm.decode('latin1'))
d0c=collections.Counter(v[0] for v in RAWCOL.values())
d1c=collections.Counter(v[1] for v in RAWCOL.values())
d2c=collections.Counter(v[2] for v in RAWCOL.values())
print('   COL 五字段分布：d0 %s | d1(0/非0) 0:%.0f 非0:%.0f | d2 %s'
      %(dict(d0c), d1c.get(0,0), sum(v for k,v in d1c.items() if k!=0), dict(d2c)))
ck('D1 COL 共 1214 条，d0 恒为 0（signature），d2 恒为 0（cdOffset）',
   len(RAWCOL)==1214 and set(d0c)=={0} and set(d2c)=={0}, (len(RAWCOL),dict(d0c),dict(d2c)))
ck('D2 以 d1（COL offset = mdisp）分裂 = 主表 954 / 接口子表 260',
   d1c.get(0,0)==954 and sum(v for k,v in d1c.items() if k!=0)==260,
   (d1c.get(0,0), sum(v for k,v in d1c.items() if k!=0)))
ck('D2b 反控：以 d0 判主表会得 1214/0 —— 这正是审计员 #472 报的基线，属口径错',
   d0c.get(0,0)==1214 and d1c.get(0,0)==954, (d0c.get(0,0), d1c.get(0,0)))
COL={va:dict(mdisp=v[1],ptd=v[3],pchd=v[4],name=v[5]) for va,v in RAWCOL.items()}
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
MAIN=[vt for vt in sorted(VT) if COL[VT[vt]]['mdisp']==0]
SUB=[vt for vt in sorted(VT) if COL[VT[vt]]['mdisp']!=0]
ck('D2c VT 1214 张；主表 954 / 子表 260；槽合计 14044',
   (len(VT),len(MAIN),len(SUB),sum(NS.values()))==(1214,954,260,14044),
   (len(VT),len(MAIN),len(SUB),sum(NS.values())))
def topset(vts,slot,k=4):
    d=collections.Counter()
    for vt in vts:
        if NS[vt]>slot: d[P.dw(vt+4*slot)]+=1
    return d
rows={}
for name,vts in (('ALL1214',sorted(VT)),('MAIN954',MAIN)):
    for slot in range(0,8):
        d=topset(vts,slot); top=d.most_common(3)
        rows['%s_s%d'%(name,slot)]=[('%08X'%a,c) for a,c in top]
print('\n   两种分母下的槽 0..7 Top3：')
for slot in range(0,8):
    print('    槽%d  MAIN954 %-34s | ALL1214 %s'%(slot,rows['MAIN954_s%d'%slot],rows['ALL1214_s%d'%slot]))
d4m=topset(MAIN,4); d4a=topset(VT,4)
ck('D3 954 主表：槽 4 Top1 = 0x410450 77 次（本轮主口径）',
   d4m.most_common(1)[0]==(0x410450,77), d4m.most_common(2))
ck('D3b 1214 全表：槽 4 Top1 = 0x410220 78 次（审计员口径可复现），且 0x410450 退居第二 77 次',
   d4a.most_common(2)[0]==(0x410220,78) and d4a[0x410450]==77, d4a.most_common(2))
ck('D3c 差异由分母解释（实测订正）：0x410220 在 954 主表槽 4 上出现 0 次，78 次全在接口子表',
   topset(MAIN,4)[0x410220]==0, topset(MAIN,4)[0x410220])
sub4=topset(SUB,4)
ck('D3d 接口子表槽 4 上 0x410220 出现 78 次（两口径的 Top1 来自两个互不相交的表集合）',
   sub4[0x410220]==78, [('%08X'%a,c) for a,c in sub4.most_common(3)])
print('   接口子表槽 4 上 0x410220 落在：%s'
      %[('%08X'%vt,'%08X'%COL[VT[vt]]['mdisp'],COL[VT[vt]]['name']) for vt in SUB
        if NS[vt]>4 and P.dw(vt+16)==0x410220])

print('\n   四地址的全槽号分布（ALL1214 / MAIN954）：')
dist={}
for tgt in (0x410450,0x410220,0x410580,0x410590):
    ca=collections.Counter(); cm=collections.Counter(); cs=collections.Counter()
    for vt in VT:
        for s in range(NS[vt]):
            if P.dw(vt+4*s)==tgt:
                ca[s]+=1
                (cm if COL[VT[vt]]['mdisp']==0 else cs)[s]+=1
    dist['%08X'%tgt]=dict(all={str(k):v for k,v in ca.items()},
                          main={str(k):v for k,v in cm.items()},
                          sub={str(k):v for k,v in cs.items()})
    print('     %08X ALL %s | MAIN %s | SUB %s'%(tgt,dict(ca),dict(cm),dict(cs)))
ck('D4 0x410450 只在槽 4（77 次，全部在主表）',
   dist['00410450']['all']=={'4':77} and dist['00410450']['sub']=={}, dist['00410450'])
ck('D4b 0x410580/0x410590 的槽号与表类型',
   all(dist[x]['all'] for x in ('00410580','00410590')),
   (dist['00410580']['all'],dist['00410590']['all']))

def dis(va,n=96):
    o=P.r2o(va)
    out=[]
    for i in md.disasm(P.RAW[o:o+n],va):
        out.append('%08X %-16s %s %s'%(i.address,i.bytes.hex(),i.mnemonic,i.op_str))
        if i.mnemonic in ('ret','retn'): break
    return out
h1=dis(0x4A1D50); h2=dis(0x4A1CA0)
print('\n   0x4A1D50（槽13 第一个辅助，参数 = [this+0x10]）：')
for x in h1[:14]: print('     '+x)
print('   0x4A1CA0（槽13 第二个辅助，参数 = [this+0x20]）：')
for x in h2[:14]: print('     '+x)
ck('D5 0x4A1D50 与 0x4A1CA0 都是非平凡函数（>4 条）且不同地址',
   len(h1)>4 and len(h2)>4 and 0x4A1D50!=0x4A1CA0,(len(h1),len(h2)))
ck('D5b 两辅助体首不同字节（不是同一实现的别名）',
   P.RAW[P.r2o(0x4A1D50):P.r2o(0x4A1D50)+8]!=P.RAW[P.r2o(0x4A1CA0):P.r2o(0x4A1CA0)+8])
json.dump(dict(d0=dict(d0c),d1=dict(d1c),d2=dict(d2c),main=len(MAIN),sub=len(SUB),
   rows=rows,dist=dist,h1=h1,h2=h2,fails=fails),
   open('_r193/r193d.json','w'),ensure_ascii=False,indent=1)
print('\n断言 %d 条，FAIL %d 条 %s'%(N,len(fails),fails))
sys.exit(1 if fails else 0)
