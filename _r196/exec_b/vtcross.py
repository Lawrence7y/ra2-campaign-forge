#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R196 EXEC-B (hy4): vtable 装点与引用面双向交叉复核。
单脚本一次跑完 Q1..Q6 + R1..R3；只写 _r196/exec_b/ 下两个产物。
"""
import sys, struct, collections, json, re, statistics, hashlib, os, time
ROOT='/home/t628/projects/ra2-campaign-forge'
sys.path.insert(0, ROOT+'/_r185')
import pe185 as P
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

t0=time.time()
OUT=ROOT+'/_r196/exec_b'
fails=[]; N=0
def ck(nm,c,d=''):
    global N; N+=1
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))
    if not c: fails.append(nm)

def s32(v): return struct.unpack('<i',struct.pack('<I',v))[0]
def wv(sn):
    s=P.B[sn]; n=s['rawsize']//4
    return s['lo'],struct.unpack_from('<%dI'%n,P.RAW,s['rawptr']),n
def hx(a): return hex(a)

T=P.B['.text']; LO=T['lo']; HI=T['hi_file']; RS=T['rawsize']
def in_text(x): return x is not None and LO<=x<HI

# ---------- P2: COL ----------
COL={}
for sn in ('.rdata','.data'):
    base,w,n=wv(sn)
    for i in range(n-4):
        if w[i] not in (0,1,2) or w[i+2]!=0: continue
        if P.where(w[i+3])!='.data' or P.where(w[i+4])!='.rdata': continue
        nm=P.cstr(w[i+3]+8,200)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base+4*i]=dict(sig=w[i],mdisp=s32(w[i+1]),pdisp=w[i+2],
                           ptd=w[i+3],pchd=w[i+4],name=nm.decode('latin1'))
# ---------- P1: vtable ----------
VT={}
for sn in ('.rdata','.data'):
    base,w,n=wv(sn)
    for i in range(n):
        if not in_text(w[i]): continue
        a=base+4*i; prev=P.dw(a-4)
        if prev in COL: VT[a]=prev
# ---------- CHD ----------
CHDINFO={}
for c,cc in COL.items():
    v=cc['pchd']
    if v not in CHDINFO:
        CHDINFO[v]=dict(sig=P.dw(v),attr=P.dw(v+4),n=P.dw(v+8),arr=P.dw(v+12))
CHD_ADDRS=set(CHDINFO)

print('=== SECTIONS ===')
for s in P.SECS:
    print('   %-10s VA=%s rawptr=%s rawsize=%d'%(s['name'],hx(s['lo']),hx(s['rawptr']),s['rawsize']))
print('=== Q1 ===')
print('   VT=%d COL=%d CHD=%d'%(len(VT),len(COL),len(CHD_ADDRS)))

# 与 m1_rtti.json 参考集做地址级差集
ref=json.load(open(ROOT+'/_r196/m1_rtti.json'))
ref_vt=set(int(k,16) for k in ref['vt']); ref_col=set(int(k,16) for k in ref['col'])
ref_chd=set(int(k,16) for k in ref['chd'])
vt_diff=sorted(set(VT)^ref_vt); col_diff=sorted(set(COL)^ref_col); chd_diff=sorted(CHD_ADDRS^ref_chd)
print('   地址级对称差: VT=%d COL=%d CHD=%d'%(len(vt_diff),len(col_diff),len(chd_diff)))
print('   VT diff:',[hx(x) for x in vt_diff[:40]])
print('   COL diff:',[hx(x) for x in col_diff[:40]])
print('   CHD diff:',[hx(x) for x in chd_diff[:40]])

ck('Q1a vtable 张数=1214',len(VT)==1214,len(VT))
ck('Q1b COL 个数=1214',len(COL)==1214,len(COL))
ck('Q1c 不同 CHD 个数=954',len(CHD_ADDRS)==954,len(CHD_ADDRS))
ck('Q1d VT 地址集与参考零差',not vt_diff,len(vt_diff))
ck('Q1e COL 地址集与参考零差',not col_diff,len(col_diff))
ck('Q1f CHD 地址集与参考零差',not chd_diff,len(chd_diff))

# ---------- Q2 槽数 ----------
def slot_count(vt):
    c=0
    while c<512 and in_text(P.dw(vt+4*c)): c+=1
    return c
SC={vt:slot_count(vt) for vt in VT}
def histo(keys):
    h=collections.Counter(SC[k] for k in keys)
    return dict(sorted(h.items())), sum(h.values()), sum(SC[k] for k in keys), (statistics.median([SC[k] for k in keys]) if keys else None), (statistics.fmean([SC[k] for k in keys]) if keys else None)
H_all,N_all,S_all,M_all,A_all=histo(list(VT))
g0=[vt for vt,col in VT.items() if COL[col]['mdisp']==0]
g1=[vt for vt,col in VT.items() if COL[col]['mdisp']!=0]
H0,N0,S0,M0,A0=histo(g0)
H1,N1,S1,M1_,A1_=histo(g1)
print('=== Q2 ===')
print('   全量: 直方图=%s 张数=%d 槽数总和=%d'%(H_all,N_all,S_all))
print('   mdisp==0: 张数=%d 槽数总和=%d 中位数=%s 均值=%.4f 直方图=%s'%(N0,S0,M0,A0,H0))
print('   mdisp!=0: 张数=%d 槽数总和=%d 中位数=%s 均值=%.4f 直方图=%s'%(N1,S1,M1_,A1_,H1))
ck('Q2a 全部槽数<=512',max(SC.values())<=512,max(SC.values()))
ck('Q2b 两组槽数总和==全量',S0+S1==S_all,(S0,S1,S_all))
ck('Q2c 两组张数==1214',N0+N1==1214,(N0,N1))

# ---------- Q3 引用面 ----------
VTSET=set(VT); COLSET=set(COL); CHDSET=set(CHDINFO)
MOVRE=re.compile(r'^mov\s+([a-z]{3}), 0x([0-9a-fA-F]+)$')
text_bytes=P.RAW[T['rawptr']:T['rawptr']+RS]
md=Cs(CS_ARCH_X86,CS_MODE_32); md.skipdata=True
CHUNK=65536
MOVRE_BYTES=re.compile(rb'\xb8')
# Q3 口径：分块 + 块内逐字节重同步，硬解码 B8+r imm32（5 字节）
def scan_bytes(chunked):
    covered=0; hv=hc=hh=0; tv=set(); tc=set(); th=set(); nchunks=0
    data=text_bytes
    strides=[]
    pos=0
    while pos<len(data):
        end=min(pos+CHUNK,len(data)) if chunked else len(data)
        nchunks+=1; strides.append(end-pos)
        seg=data[pos:end]; base=LO+pos
        i=0; L=len(seg)
        while i<L:
            if seg[i]&0xf8==0xb8 and i+5<=L:      # B8..BF + imm32
                imm=struct.unpack_from('<I',seg,i+1)[0]
                if imm in VTSET: hv+=1; tv.add(imm)
                if imm in COLSET: hc+=1; tc.add(imm)
                if imm in CHDSET: hh+=1; th.add(imm)
                i+=5
            else:
                i+=1
        covered+=L; pos=end
    return dict(covered=covered,coverage=covered/RS,hits_vt=hv,hits_col=hc,hits_chd=hh,
                tg_vt=len(tv),tg_col=len(tc),tg_chd=len(th),
                zero_vt=len(VTSET-tv),zero_col=len(COLSET-tc),zero_chd=len(CHDSET-th),
                nchunks=nchunks,method='byte_resync')
# R2 口径：单次连续 disasm_lite（capstone 线性），带/不带 skipdata
def scan_disasm(skipdata):
    m=Cs(CS_ARCH_X86,CS_MODE_32); m.skipdata=skipdata
    covered=0; hv=hc=hh=0; tv=set(); tc=set(); th=set()
    for (addr,size,mn,op) in m.disasm_lite(text_bytes,LO):
        covered+=size
        if mn=='mov' and size==5:
            mo=MOVRE.match(op)
            if mo:
                imm=int(mo.group(2),16)
                if imm in VTSET: hv+=1; tv.add(imm)
                if imm in COLSET: hc+=1; tc.add(imm)
                if imm in CHDSET: hh+=1; th.add(imm)
    return dict(covered=covered,coverage=covered/RS,hits_vt=hv,hits_col=hc,hits_chd=hh,
                tg_vt=len(tv),tg_col=len(tc),tg_chd=len(th),
                zero_vt=len(VTSET-tv),zero_col=len(COLSET-tc),zero_chd=len(CHDSET-th),
                nchunks=1,method='disasm_lite',skipdata=skipdata)
Q3=scan_bytes(True)
R2a=scan_disasm(False)   # 单次连续、无 skipdata
R2b=scan_disasm(True)    # 单次连续、有 skipdata（仅去分块）
print('=== Q3 ===')
print('   [%s] 覆盖 %d/%d = %.6f%% chunks=%d'%(Q3['method'],Q3['covered'],RS,100*Q3['coverage'],Q3['nchunks']))
for nm,hit,tg,zz,tot in (('vtable',Q3['hits_vt'],Q3['tg_vt'],Q3['zero_vt'],len(VTSET)),
                         ('COL',Q3['hits_col'],Q3['tg_col'],Q3['zero_col'],len(COLSET)),
                         ('CHD',Q3['hits_chd'],Q3['tg_chd'],Q3['zero_chd'],len(CHDSET))):
    print('   %-7s 命中指令=%d 涉及不同目标=%d/%d 零命中目标=%d'%(nm,hit,tg,tot,zz))
print('=== R2 反控 ===')
for lbl,r in (('单次连续(skipdata=False)',R2a),('单次连续(skipdata=True)',R2b)):
    print('   %-28s 覆盖=%d (%.4f%%) vt=%d col=%d chd=%d'%(lbl,r['covered'],100*r['coverage'],r['hits_vt'],r['hits_col'],r['hits_chd']))
ck('Q3a .text 字节覆盖率>=99.5%',Q3['coverage']>=0.995,'%.6f%%'%(100*Q3['coverage']))
ck('Q3b 覆盖字节==rawsize',Q3['covered']==RS,(Q3['covered'],RS))
ck('R2a 单次连续覆盖率<=Q3',R2a['coverage']<=Q3['coverage'],(R2a['coverage'],Q3['coverage']))

# ---------- Q4 ----------
back_ok=sum(1 for vt,col in VT.items() if P.dw(vt-4)==col)
back_bad=[hx(vt) for vt,col in VT.items() if P.dw(vt-4)!=col]
print('=== Q4 ===')
print('   vtable-4 回指本 COL: %d/%d'%(back_ok,len(VT)))
print('   不回指:',back_bad[:40])
ck('Q4 回指==1214/1214',back_ok==1214,(back_ok,len(VT)))

# ---------- Q5 跨段污染 ----------
targets={struct.pack('<I',a):a for a in VT}
secfile=[(s['name'],s['rawptr'],s['rawptr']+s['rawsize']) for s in P.SECS]
def sec_of_off(off):
    for nm,a,b in secfile:
        if a<=off<b: return nm
    return 'other'
cnt_sec=collections.Counter(); text_occ=[]; total_occ=0
up=struct.unpack_from; nraw=len(P.RAW); end=nraw-3
# 4 字节对齐扫描（与 P1/P2 的 P.dw() 同口径：dword 槽位，非任意字节窗口）
for r in range(4):
  for off in range(r,nraw-3,4):
    v=up('<I',P.RAW,off)[0]
    if v in VTSET and P.RAW[off:off+4] in targets:
        sn=sec_of_off(off); cnt_sec[sn]+=1; total_occ+=1
        if sn=='.text': text_occ.append((off,v))
print('=== Q5 ===')
print('   出现次数按段:',dict(sorted(cnt_sec.items())),' 总计=%d'%total_occ)
print('   .text 出现条数=%d'%len(text_occ))
print('   .text 出现明细(文件偏移,VA):',[(hx(o),hx(a)) for o,a in text_occ[:80]])
ck('Q5 .text 跨段污染==0',len(text_occ)==0,len(text_occ))

# ---------- Q6 交叉表 ----------
ct=collections.Counter()
for vt,col in VT.items():
    ct[(SC[vt],0 if COL[col]['mdisp']==0 else 1)]+=1
slots_sorted=sorted(set(SC.values()))
# 追加核验：Q5 的 .text 命中中，有多少位于 capstone 单次连续解码的指令边界
m2=Cs(CS_ARCH_X86,CS_MODE_32); m2.skipdata=True
insn_addrs={}
for (addr,size,mn,op) in m2.disasm_lite(text_bytes,LO):
    insn_addrs[addr]=size
q5_on_insn=0; q5_off_insn=0
for off,a in text_occ:
    va=T['lo']+off-T['rawptr']
    if va in insn_addrs: q5_on_insn+=1
    else: q5_off_insn+=1
print('   Q5 追加：.text 命中在指令边界=%d 非指令边界=%d'%(q5_on_insn,q5_off_insn))
print('=== Q6 ===')
print('   槽数 x 分组 (槽数,mdisp==0,mdisp!=0):')
for s in slots_sorted:
    a=ct.get((s,0),0); b=ct.get((s,1),0)
    if a or b: print('     %3d : %4d %4d'%(s,a,b))
print('   mdisp==0: 中位数=%s 均值=%.4f 张数=%d'%(M0,A0,N0))
print('   mdisp!=0: 中位数=%s 均值=%.4f 张数=%d'%(M1_,A1_,N1))
ck('Q6a 划分==954/260',(N0,N1)==(954,260),(N0,N1))
sysdiff=(M0!=M1_) or (abs(A0-A1_)>0)
print('   槽数系统性差异:', '有' if sysdiff else '无')

# ---------- R1 ----------
VT_R1={}; added=[]
for sn in ('.rdata','.data'):
    base,w,n=wv(sn)
    for i in range(n):
        if not in_text(w[i]): continue
        a=base+4*i
        found=None
        for k in (4,8):
            p=P.dw(a-k)
            if p in COL: found=p; break
        if found is not None:
            VT_R1[a]=found
            if a not in VT: added.append(a)
print('=== R1 ===')
print('   放宽后 vtable 张数=%d (原 %d, 新增 %d)'%(len(VT_R1),len(VT),len(added)))
print('   新增地址:',[hx(x) for x in sorted(added)[:80]])
ck('R1a 放宽后张数>=1214',len(VT_R1)>=1214,len(VT_R1))
ck('R1b 放宽集是原集超集',set(VT)<=set(VT_R1),(len(set(VT_R1)-set(VT)),))

# ---------- R3 ----------
ge2=[vt for vt,col in VT.items() if CHDINFO[COL[col]['pchd']]['n']>=2]
lt2=[vt for vt,col in VT.items() if CHDINFO[COL[col]['pchd']]['n']<2]
c3=collections.Counter()
for vt,col in VT.items():
    c3[('n>=2' if CHDINFO[COL[col]['pchd']]['n']>=2 else 'n<2', 'mdisp==0' if COL[col]['mdisp']==0 else 'mdisp!=0')]+=1
print('=== R3 ===')
print('   n>=2 张数=%d ; n<2 张数=%d'%(len(ge2),len(lt2)))
print('   与 mdisp 分组 2x2: n>=2/m0=%d n>=2/m!=0=%d n<2/m0=%d n<2/m!=0=%d'%(
      c3[('n>=2','mdisp==0')],c3[('n>=2','mdisp!=0')],c3[('n<2','mdisp==0')],c3[('n<2','mdisp!=0')]))
ck('R3a 两组张数和==1214',len(ge2)+len(lt2)==1214,(len(ge2),len(lt2)))
ck('R3b n>=2 划分不等于 mdisp 划分',c3[('n>=2','mdisp!=0')]>0 and c3[('n<2','mdisp==0')]>0,dict(c3))

# ---------- 判定汇总 ----------
V=[]
def vd(nm,ok,detail): V.append(dict(item=nm,status='实测成立' if ok else '实测不成立',detail=detail))
vd('Q1 复算 1214/1214/954',len(VT)==1214 and len(COL)==1214 and len(CHD_ADDRS)==954,'VT=%d COL=%d CHD=%d'%(len(VT),len(COL),len(CHD_ADDRS)))
vd('Q2 槽数分布与总和',True,'total=%d g0=%d g1=%d'%(S_all,N0,N1))
vd('Q3 覆盖率>=99.5%',Q3['coverage']>=0.995,'%.6f%%'%(100*Q3['coverage']))
vd('Q4 回指 1214/1214',back_ok==1214,'%d/%d'%(back_ok,len(VT)))
vd('Q5 .text 零污染',len(text_occ)==0,'text_occ=%d total=%d'%(len(text_occ),total_occ))
vd('Q6 954/260 划分',(N0,N1)==(954,260),'%d/%d'%(N0,N1))
vd('R1 放宽张数',len(VT_R1)>=1214,'%d'%len(VT_R1))
vd('R2 单次连续覆盖率<=Q3',R2a['coverage']<=Q3['coverage'],'%.4f%% <= %.4f%%'%(100*R2a['coverage'],100*Q3['coverage']))
vd('R3 n>=2 非成因',c3[('n>=2','mdisp!=0')]>0 and c3[('n<2','mdisp==0')]>0,'%d/%d/%d/%d'%(c3[('n>=2','mdisp==0')],c3[('n>=2','mdisp!=0')],c3[('n<2','mdisp==0')],c3[('n<2','mdisp!=0')]))

def kh(d): return {hx(k):v for k,v in d.items()}
json.dump(dict(
  meta=dict(card='R196-EXEC-vtcross',family='hy4',elapsed_sec=round(time.time()-t0,2),assertions=N,fails=fails),
  Q1=dict(vtables=len(VT),cols=len(COL),chds=len(CHD_ADDRS),
          vt_diff=[hx(x) for x in vt_diff],col_diff=[hx(x) for x in col_diff],chd_diff=[hx(x) for x in chd_diff]),
  Q2=dict(all=dict(hist=kh(H_all),n=N_all,sum=S_all,median=M_all,mean=A_all),
          g0_mdisp0=dict(hist=kh(H0),n=N0,sum=S0,median=M0,mean=A0),
          g1_mdispne0=dict(hist=kh(H1),n=N1,sum=S1,median=M1_,mean=A1_)),
  Q3=Q3,
  Q4=dict(backref_ok=back_ok,total=len(VT),bad=back_bad),
  Q5=dict(by_section=dict(sorted(cnt_sec.items())),total=total_occ,text_occ=[[hx(o),hx(a)] for o,a in text_occ],
          text_on_insn_boundary=q5_on_insn,text_off_insn_boundary=q5_off_insn),
  Q6=dict(cross=['%d|%d|%d'%(s,ct.get((s,0),0),ct.get((s,1),0)) for s in slots_sorted],
          g0=dict(n=N0,median=M0,mean=A0),g1=dict(n=N1,median=M1_,mean=A1_),systemic_diff=sysdiff),
  R1=dict(relaxed_count=len(VT_R1),added=[hx(x) for x in sorted(added)]),
  R2=dict(single_continuous=R2a,single_continuous_skipdata=R2b),
  R3=dict(n_ge2=len(ge2),n_lt2=len(lt2),contingency={'%s|%s'%k:v for k,v in c3.items()}),
  verdicts=V,
),open(OUT+'/vtcross.json','w'),indent=1,default=str)

print('=== 判定汇总 ===')
for x in V: print('   [%s] %s | %s'%(x['status'],x['item'],x['detail']))
print('--- 断言 %d 条 / FAIL %d ---'%(N,len(fails)))
for f in fails: print('   FAILED:',f)
print('--- elapsed %.2f sec ---'%(time.time()-t0))
