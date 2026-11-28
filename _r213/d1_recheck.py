# -*- coding: utf-8 -*-
"""R213 d1：跨家族审计复核（§2.12 规则 D）。独立复算 xa.py 全部关键数 + 处理审计员
提出的 BCA 共享口径差（我方 xa T2-6 的 BCD 次数按「CHD×元素」计，未对共享 BCA 去重）。
"""
import sys,struct,collections,json
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
def s32(v): return struct.unpack('<i',struct.pack('<I',v&0xffffffff))[0]
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
md=Cs(CS_ARCH_X86,CS_MODE_32)
def ins(a,n=4,maxb=64):
    o=P.r2o(a); out=[]
    if o is None: return out
    for i in md.disasm(P.RAW[o:o+maxb],a):
        out.append((i.address,i.mnemonic,i.op_str))
        if len(out)>=n: break
    return out
NA=0;F=[]
def ck(n,c,d=''):
    global NA; NA+=1
    if not c: F.append(n)
    print(('PASS ' if c else 'FAIL ')+n+((' | '+str(d)) if d!='' else ''))
COL={}
for sn in ('.rdata','.data'):
    s=P.B[sn]; n=s['rawsize']//4; base=s['lo']
    w=struct.unpack_from('<%dI'%n,P.RAW,s['rawptr'])
    for k in range(n-4):
        if w[k] not in (0,1,2) or w[k+2]!=0: continue
        if P.where(w[k+3])!='.data' or P.where(w[k+4])!='.rdata': continue
        nm=P.cstr(w[k+3]+8,400)
        if nm and nm.startswith(b'.?A') and nm.endswith(b'@@'):
            COL[base+4*k]=dict(mdisp=s32(w[k+1]),pTD=w[k+3],pCHD=w[k+4],name=nm.decode('latin1'))
G=collections.defaultdict(list)
for c,v in COL.items(): G[v['pCHD']].append(c)
CHD=sorted(G); NB={a:P.dw(a+8) for a in CHD}; pBCA={a:P.dw(a+12) for a in CHD}
BCA={a:[P.dw(pBCA[a]+4*j) for j in range(NB[a])] for a in CHD}
print('COL=%d CHD=%d'%(len(COL),len(CHD)))
# === 口径 A（xa.py 原用）：CHD×元素 展开计数 ===
cA=collections.Counter(P.dw(e) for a in CHD for e in BCA[a])
# === 口径 B（审计员）：对共享 BCA 数组去重后按元素计数 ===
seen=set(); cB=collections.Counter()
for a in CHD:
    p=pBCA[a]
    if p in seen: continue
    seen.add(p)
    for e in BCA[a]: cB[P.dw(e)]+=1
# === 口径 C：distinct BCD 记录（元素地址去重）被引用一次 ===
seenE=set(); cC=set()
for a in CHD:
    for e in BCA[a]: seenE.add(e); cC.add(P.dw(e))
print('不同 pBCA 数组=%d ; 不同 BCA 元素地址=%d ; 被引用 TD 数=%d'%(len(seen),len(seenE),len(cC)))
print('口径A 总引用=%d  口径B 总引用=%d'%(sum(cA.values()),sum(cB.values())))
TD={}
for sn in ('.data','.rdata'):
    s=P.B[sn]; n=s['rawsize']//4; base=s['lo']
    w=struct.unpack_from('<%dI'%n,P.RAW,s['rawptr'])
    for i in range(n-2):
        if w[i+1]!=0: continue
        nm=P.cstr(base+4*i+8,400)
        if nm and nm.startswith(b'.?A') and nm.endswith(b'@@'):
            TD[base+4*i]=dict(name=nm.decode('latin1'),vf=w[i])
REF=collections.Counter(v['pTD'] for v in COL.values())
ONLY=sorted(set(TD)-set(REF))
print('\n=== onlysec 34 条的两种引用口径 ===')
for t in ONLY:
    print('  %-58s A=%-4d B=%-3d C=%s'%(TD[t]['name'],cA.get(t,0),cB.get(t,0),cC.__contains__(t)))
nA=sum(1 for t in ONLY if cA.get(t,0)==1); nB=sum(1 for t in ONLY if cB.get(t,0)==1)
nC=sum(1 for t in ONLY if t in cC)
print('  次数==1：口径A %d 条 / 口径B %d 条 ; 被引用总数 口径C %d 条'%(nA,nB,nC))
ck('D1 onlysec 34 条全部被 BCA 引用（三条口径同真）', nC==34, nC)
ck('D2 口径B 下「恰被 1 条 BCD 引用」== 20 条（审计员报 32 ⇒ 其 G12 附注错，漏 14 条多引用）',
   nB==20 and nB!=32, nB)
ck('D3 我方 xa.py 的 20 条是口径A（CHD×元素展开）下的数，非同一把尺', nA==20, nA)
ck('D4 BCA 数组无共享（不同 pBCA 954 == CHD 954）⇒ 审计员「共享 BCA 致口径差」假设被证伪',
   len(seen)==len(CHD)==954, '%d vs %d'%(len(seen),len(CHD)))
ck('D4b 口径A 与口径B 总引用数相同（2615==2615）⇒ 两口径无差',
   sum(cA.values())==sum(cB.values())==2615, (sum(cA.values()),sum(cB.values())))
# === 审计员 G9 附注：0x11c8 另有 .rsrc 1 处 0xb7a8bc ===
s=P.B.get('.rsrc')
if s:
    raw=P.RAW[s['rawptr']:s['rawptr']+s['rawsize']]
    import re
    hits=[s['lo']+m.start() for m in re.finditer(re.escape(struct.pack('<I',0x11c8)),raw)]
    print('\n.rsrc 内 0x11c8 字面命中 = %d 处 %s'%(len(hits),[hex(h) for h in hits[:5]]))
    ck('D5 .rsrc 内 0x11c8 命中且非立即数（资源载荷）', len(hits)==1 and hits[0]==0xb7a8bc, [hex(h) for h in hits])
else:
    print('  no .rsrc'); ck('D5 无 .rsrc', False)
# === 审计员 G11：0x7f9594 与 0x7f9598 引用面 ===
n_data=0
for sn in ('.data','.rdata'):
    s=P.B[sn]; raw=P.RAW[s['rawptr']:s['rawptr']+s['rawsize']]
    import re
    for m in re.finditer(re.escape(struct.pack('<I',0x7f9594)),raw):
        va=s['lo']+m.start()
        if any(v['pTD']==va-0 and False for v in COL.values()): pass
        n_data+=1
print('\n0x7f9594 在 .data/.rdata 的字面出现 = %d 次（TD+0 槽位 988 + 其他）'%n_data)
td0=sum(1 for t in TD if P.dw(t)==0x7f9594)
ck('D6 0x7f9594 出现次数 == TD 数 988 + 非 TD 引用（.rdata 内可能另有）', n_data>=td0, '%d vs TD=%d'%(n_data,td0))
tr=P.B['.text']; traw=P.RAW[tr['rawptr']:tr['rawptr']+tr['rawsize']]
import re
n_9594txt=len([m for m in re.finditer(re.escape(struct.pack('<I',0x7f9594)),traw)])
n_str=len([m for m in re.finditer(re.escape(struct.pack('<I',0x7f9598)),traw)])
print('  .text 内 0x7f9594 字面=%d ; 0x7f9598 字面=%d'%(n_9594txt,n_str))
ck('D7 .text 内 0x7f9594 字面 == 2 处（审计员数）', n_9594txt==2, n_9594txt)
ck('D8 .text 内 0x7f9598 字面 == 3 处（审计员数）', n_str==3, n_str)
# === 抽 2 处反汇编确认 ===
for imm in (0x7f9594,0x7f9598):
    b=struct.pack('<I',imm)
    for m in list(re.finditer(re.escape(b),traw))[:3]:
        a=tr['lo']+m.start()
        print('   %#010x 前一条起始附近: %s'%(a,' ; '.join('%s %s'%(x[1],x[2]) for x in ins(a-6,3))))
# === 审计员 G2 附注：vftable 位点全在 .rdata，.data 内 0 ===
cnt=collections.Counter()
for sn in ('.rdata','.data'):
    s=P.B[sn]; n=s['rawsize']//4; base=s['lo']
    w=struct.unpack_from('<%dI'%n,P.RAW,s['rawptr'])
    for k in range(n-1):
        if w[k] in COL and P.where(w[k+1])=='.text': cnt[sn]+=1
print('\nvftable 位点段分布 =',dict(cnt))
ck('D9 vftable 位点全在 .rdata（1214），.data 内 0', cnt['.rdata']==1214 and cnt['.data']==0, dict(cnt))
# === 关键数字再核 ===
ck('D10 COL==1214 且 CHD==954', len(COL)==1214 and len(CHD)==954, (len(COL),len(CHD)))
ck('D11 TD==988 且 onlysec==34', len(TD)==988 and len(ONLY)==34, (len(TD),len(ONLY)))
md=collections.Counter(v['mdisp'] for v in COL.values())
ck('D12 mdisp 分布 == {0:954,4:91,8:78,12:78,24:6,36:1,40:1,44:1,1728:1,21784:3}',
   dict(md)=={0:954,4:91,8:78,12:78,24:6,36:1,40:1,44:1,1728:1,21784:3}, sorted(md.items()))
print('\n断言 %d / FAIL %d %s'%(NA,len(F),F))
json.dump({'nA':nA,'nB':nB,'nC':nC,'bca_arrays':len(seen),'bca_elems':len(seenE),
 'rsrc':True,'t9594':n_9594txt,'t9598':n_str,'nassert':NA,'fails':F},
 open('_r213/d1_recheck.json','w'),indent=1,ensure_ascii=False)
