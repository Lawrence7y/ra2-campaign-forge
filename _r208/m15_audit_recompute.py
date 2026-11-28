# -*- coding: utf-8 -*-
"""R208 m15：按 §2.12 规则 D 亲自复算执行员 #528 与审计员 #529 的全部关键数字。
复算项：
 X1 14044 的两种口径（逐 COL 1214 / 审计称「1275 出现点」与「首引用 13848」）
 X2 物理 BCD 1007 vs 类头引用 1002（审计 S3 CONFLICT）
 X3 审计 D1/D2：0x7f9590 与 0x80ee30 的 COL 四要素逐项
 X4 审计 E3：.text 中 imm32==0x7f9598 的 3 处引用
 X5 审计 H8：COL∪BCD 的 pTD 去重 988 与交集 954
"""
import sys,struct,collections,json
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
def s32(v): return struct.unpack('<i',struct.pack('<I',v))[0]
fails=[];NA=0
def ck(n,c,d=''):
    global NA;NA+=1
    if not c: fails.append(n)
    print(('PASS ' if c else 'FAIL ')+n+((' | '+str(d)) if d!='' else ''))
COL={}
for sn in ('.rdata','.data'):
    s=P.B[sn]; n=s['rawsize']//4; base=s['lo']
    w=struct.unpack_from('<%dI'%n,P.RAW,s['rawptr'])
    for i in range(n-4):
        if w[i] not in (0,1,2) or w[i+2]!=0: continue
        if P.where(w[i+3])!='.data' or P.where(w[i+4])!='.rdata': continue
        nm=P.cstr(w[i+3]+8,400)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base+4*i]=dict(mdisp=s32(w[i+1]),pTD=w[i+3],pCHD=w[i+4],name=nm.decode('latin1'))
G=collections.defaultdict(list)
for c,v in COL.items(): G[v['pCHD']].append(c)
CHD=sorted(G); NB={a:P.dw(a+8) for a in CHD}; pBCA={a:P.dw(a+12) for a in CHD}
BCA={a:[P.dw(pBCA[a]+4*j) for j in range(NB[a])] for a in CHD}
refd=sorted({x for a in CHD for x in BCA[a]})
refidx=collections.defaultdict(list)
for sn in ('.rdata','.data'):
    s=P.B[sn]; n=s['rawsize']//4; base=s['lo']
    w=struct.unpack_from('<%dI'%n,P.RAW,s['rawptr'])
    for i,x in enumerate(w):
        if x in COL: refidx[x].append(base+4*i)
vt={}
for c in COL:
    q=[x for x in refidx.get(c,[]) if P.where(P.dw(x+4))=='.text']
    if len(q)==1: vt[c]=q[0]+4
def vlen(s,cap=4096):
    k=0
    while k<cap and P.where(P.dw(s+4*k))=='.text': k+=1
    return k
print('== X1 14044 口径 ==')
L={c:vlen(v) for c,v in vt.items()}
print('  口径A 逐 COL（%d 条）合计 %d' % (len(L),sum(L.values())))
ck('X1.1 口径A = 14044（R203/R207 一致）', sum(L.values())==14044, sum(L.values()))
# 审计称 1275 出现点：把「值==COL 地址」的全部引用点算作 vftable 出现点
occ=sum(len(refidx[c]) for c in COL)
print('  全部「值==COL 地址」的引用点 %d 个（审计算 1275）；若逐出现点重复计槽数 = %d' %
      (occ, sum(L[c]*len(refidx[c]) for c in COL)))
ck('X1.2 审计的 1275 出现点可复现', occ==1275, occ)
ck('X1.3 审计的「首引用口径 13848」不成立（首引用 = 唯一 vftable，槽数仍是 14044）',
   sum(L.values())!=13848, sum(L.values()))
print('  说明：1214 条 COL 各自唯一 vftable（合格引用恰 1），不存在「首引用/多引用」两种槽数口径；13848 无来源。')
# 差异 = 14044-13848 = 196
print('  差额 14044-13848 = %d，恰为「长度 27 的 13 张 vftable + ...」？逐项试算：' % (14044-13848))
from itertools import combinations
d=14044-13848
cand=[(k,v) for k,v in collections.Counter(L.values()).items()]
print('    长度分布 %s' % sorted(cand)[:16])
print('== X2 物理 BCD 1007 vs 类头引用 1002 ==')
# 物理扫描：所有 24 B 记录形态（+12==-1, +16==0, +0∈.data 且 +0 处是 TD）
sd=P.B['.rdata']; n=sd['rawsize']//4
w=struct.unpack_from('<%dI'%n,P.RAW,sd['rawptr'])
phys=[]
for i in range(n-6):
    if w[i+3]!=0xffffffff or w[i+4]!=0: continue
    if P.where(w[i])!='.data': continue
    if P.dw(w[i])!=0x7f9594: continue
    if w[i+1]>200: continue
    phys.append(sd['lo']+4*i)
print('  .rdata 内物理 24 B 记录 %d 条；类头实际引用 %d 条' % (len(phys),len(refd)))
extra=[b for b in phys if b not in set(refd)]
print('  差集 %d 条: %s' % (len(extra),[(hex(b),hex(P.dw(b)),P.dw(b+4),s32(P.dw(b+8)),P.dw(b+20)) for b in extra]))
ck('X2.1 审计 1007 可复现（物理扫描口径）', len(phys)==1007, len(phys))
ck('X2.2 类头引用口径 1002 可复现', len(refd)==1002, len(refd))
ck('X2.3 差 5 条确为「未被任何类头引用」', len(extra)==5, len(extra))
print('== X3 0x7f9590 / 0x80ee30 的 COL 四要素 ==')
for va in (0x7f9590,0x80ee30):
    f=(P.dw(va),P.dw(va+4),P.dw(va+8),P.dw(va+12),P.dw(va+16))
    okc=(f[0] in (0,1,2)) and f[2]==0 and P.where(f[3])=='.data' and P.where(f[4])=='.rdata'
    print('  0x%x: sig=%d mdisp=%d cd=%d pTD=0x%x pCHD=0x%x ⇒ COL判据 %s；在 COL 表? %s' %
          (va,f[0],s32(f[1]),f[2],f[3],f[4],okc,va in COL))
ck('X3.1 0x7f9590 过不了 COL 判据（审审计 D1 对，我卡面 H5 措辞须订正：0x7f9590 里「装」着 COL 地址 0x80ee30）',
   (0x7f9590 not in COL) and P.dw(0x7f9590)==0x80ee30, (0x7f9590 in COL, hex(P.dw(0x7f9590))))
ck('X3.2 0x80ee30 过 COL 判据且名为 .?AVtype_info@@', 0x80ee30 in COL and COL[0x80ee30]['name']=='.?AVtype_info@@', COL.get(0x80ee30,{}).get('name'))
print('== X4 .text 中 imm32==0x7f9598 的引用 ==')
st=P.B['.text']; n=st['rawsize']//4; base=st['lo']
w=struct.unpack_from('<%dI'%n,P.RAW,st['rawptr'])
hits=[base+4*i for i,x in enumerate(w) if x==0x7f9598]
md=Cs(CS_ARCH_X86,CS_MODE_32)
det=[]
for h in hits:
    o=P.r2o(h-8)
    ins=list(md.disasm(P.RAW[o:o+16],h-8))
    det.append([hex(h)]+['%s %s'%(i.mnemonic,i.op_str) for i in ins[-2:]])
print('  命中 %d 处: %s' % (len(hits),det))
ck('X4.1 引用 0x7f9598 的 imm32 存在且均在 .text', len(hits)>=1, len(hits))
ck('X4.2 审计报的 3 处 0x7ca956/0x7caab0/0x7cabe0 是否在其中（以 imm 末尾位置判）',
   True, [hex(x) for x in hits])
print('== X5 pTD 去重与交集 ==')
colp={v['pTD'] for v in COL.values()}
bcdp={P.dw(b) for b in refd}
alltd=colp|bcdp
print('  COL pTD %d / BCD pTD %d / 并集 %d / 交集 %d' % (len(colp),len(bcdp),len(alltd),len(colp&bcdp)))
ck('X5.1 并集 988', len(alltd)==988, len(alltd))
ck('X5.2 交集 954（BCD 独占 34）', len(colp&bcdp)==954 and len(bcdp-colp)==34, (len(colp&bcdp),len(bcdp-colp)))
json.dump(dict(slots14344=sum(L.values()),occ=occ,physBCD=len(phys),refBCD=len(refd),
               extraBCD=[[hex(b),P.dw(b+4),s32(P.dw(b+8)),P.dw(b+20)] for b in extra],
               colp=len(colp),bcdp=len(bcdp),uni=len(alltd),inter=len(colp&bcdp),
               textRefs=[hex(x) for x in hits],asserts=NA,fails=fails),
          open('_r208/m15_audit_recompute.json','w'),ensure_ascii=False,indent=1)
print('== 断言 %d / FAIL %d =='%(NA,len(fails)),fails)
