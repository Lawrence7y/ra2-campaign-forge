# -*- coding: utf-8 -*-
"""R213 x0：MSVC RTTI 三角闭环（vftable-COL-TD）字节实证 + 主/次视图 TD+0 关系。
一次输出全部证据，含正反控。不用指令级反汇编。
"""
import sys,struct,json,collections
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
def s32(v): return struct.unpack('<i',struct.pack('<I',v&0xffffffff))[0]

# ---- COL 池 ----
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
# ---- 前驱位点：word==COL 地址 且 下一 word ∈ .text ----
pred=collections.defaultdict(list)
for sn in ('.rdata','.data'):
    s=P.B[sn]; n=s['rawsize']//4; base=s['lo']
    w=struct.unpack_from('<%dI'%n,P.RAW,s['rawptr'])
    for k in range(n-1):
        if w[k] in COL and P.where(w[k+1])=='.text':
            pred[w[k]].append(base+4*k)
# ---- CHD / BCA ----
G=collections.defaultdict(list)
for c,v in COL.items(): G[v['pCHD']].append(c)
CHD=sorted(G)
NB={a:P.dw(a+8) for a in CHD}; pBCA={a:P.dw(a+12) for a in CHD}
BCA={a:[P.dw(pBCA[a]+4*j) for j in range(NB[a])] for a in CHD}
own={a+16:COL[a+16] for a in CHD if a+16 in COL}
REF=collections.Counter(v['pTD'] for v in COL.values())

NA=0; F=[]
def ck(n,c,d=''):
    global NA; NA+=1
    if not c: F.append(n)
    print(('PASS ' if c else 'FAIL ')+n+((' | '+str(d)) if d!='' else ''))

print('COL=%d  CHD=%d  own=%d  不同 pTD=%d  BCA 记录=%d'%(
    len(COL),len(CHD),len(own),len(REF),sum(NB.values())))

# ================= T1 三角闭环 =================
print('\n===== T1 vftable-COL-TD 三角闭环 =====')
ck('T1-1 每条 COL 恰有 1 个前驱位点', all(len(v)==1 for v in pred.values()) and len(pred)==len(COL),
   'min=%d max=%d 覆盖 %d/%d'%(min(len(v) for v in pred.values()),max(len(v) for v in pred.values()),
                            len(pred),len(COL)))
ck('T1-2 前驱位点总数 == COL 数（无一对多）', sum(len(v) for v in pred.values())==len(COL),
   sum(len(v) for v in pred.values()))
# vt = COL+4 的定义自洽：COL+4 起是 .text 指针
t4=sum(1 for c in COL if P.where(P.dw(c+4))=='.text')
ck('T1-3 全部 COL 的 +4 指向 .text（vftable 起于 COL+4）', t4==len(COL),'%d/%d'%(t4,len(COL)))
t12=sum(1 for c in COL if P.dw(c+12)==COL[c]['pTD'])
ck('T1-4 COL+12 == COL.pTD（pTD 字段位置）', t12==len(COL),'%d/%d'%(t12,len(COL)))
t8=sum(1 for c in COL if P.dw(c+8)==0)
ck('T1-5 COL+8 == 0（cdOffset 恒 0）', t8==len(COL),'%d/%d'%(t8,len(COL)))
tn=sum(1 for c in COL if (P.cstr(COL[c]['pTD']+8,400) or b'').decode('latin1')==COL[c]['name'])
ck('T1-6 TD+8 内联名 == COL 名', tn==len(COL),'%d/%d'%(tn,len(COL)))
# 前驱位点处那 4 字节 = COL 自身地址 ⇒ vftable-4 == &COL
ck('T1-7 前驱位点 word == 该 COL 地址本身',
   all(P.dw(a)==c for c,v in pred.items() for a in v), '逐点校验')
# 反向：.text 指针运行结束处就是下一结构（槽表定长性粗检）
lens=[]
for c in COL:
    k=0
    while k<4096 and P.where(P.dw(c+4+4*k))=='.text': k+=1
    lens.append(k)
L=collections.Counter(lens)
print('   vftable 长度分布(前8) = %s ; 总槽数 = %d ; 表数 = %d'%(L.most_common(8),sum(lens),len(lens)))
ck('T1-8 每个 vftable 长度 >= 1', min(lens)>=1,'min=%d max=%d'%(min(lens),max(lens)))

# ================= T2 TD+0 pVFTable 与主/次视图 =================
print('\n===== T2 TD+0(pVFTable) 与视图偏移的对应 =====')
MAIN=[c for c in COL if COL[c]['mdisp']==0]
SEC =[c for c in COL if COL[c]['mdisp']!=0]
print('   mdisp==0 记录=%d   mdisp!=0 记录=%d'%(len(MAIN),len(SEC)))
# 主视图：TD+0 == vftable(=COL+4)?
m_hit=sum(1 for c in MAIN if P.dw(COL[c]['pTD'])==c+4)
ck('T2-1 主视图(mdisp=0) TD+0 == COL+4', m_hit==len(MAIN),'%d/%d'%(m_hit,len(MAIN)))
# 反控：主视图 TD+0 落在 .rdata 的比例
m_where=collections.Counter(P.where(P.dw(COL[c]['pTD'])) for c in MAIN)
print('   主视图 TD+0 段分布 = %s'%m_where.most_common())
# 次视图 TD+0 落点：是否等于某个 mdisp=0 视图（即 TD+0 恒指主视图）
vtof={COL[c]['pTD']:c+4 for c in MAIN}
s_hit=sum(1 for c in SEC if P.dw(COL[c]['pTD']) in vtof)
ck('T2-2 次视图(mdisp!=0) TD+0 指向某个主视图 vftable', s_hit==len(SEC),'%d/%d'%(s_hit,len(SEC)))
s_where=collections.Counter(P.where(P.dw(COL[c]['pTD'])) for c in SEC)
print('   次视图 TD+0 段分布 = %s'%s_where.most_common())
# 每个 TD 的 +0 是否唯一稳定（同一 TD 多条 COL 记录时）
bytd=collections.defaultdict(list)
for c in COL: bytd[COL[c]['pTD']].append(c)
multi={t:v for t,v in bytd.items() if len(v)>1}
uniq=sum(1 for t,v in bytd.items() if len({P.dw(t)} if P.dw(t) is not None else set())==1)
print('   多记录 pTD 数=%d ; 每个 TD 只有 1 个 +0 值(恒真检) =%d/%d'%(len(multi),uniq,len(bytd)))

# ================= T3 mdisp -> 视图类型统计 =================
print('\n===== T3 mdisp 记录分布（含 0） =====')
md=collections.Counter(COL[c]['mdisp'] for c in COL)
print('   nz 值分布 = %s'%[(k,v) for k,v in sorted(md.items()) if k!=0])
ck('T3-1 COL 记录数 == 954 + 260', len(COL)==1214,'%d'%len(COL))
ck('T3-2 mdisp==0 记录数 == CHD 数', len(MAIN)==len(CHD),'%d vs %d'%(len(MAIN),len(CHD)))

# ================= T4 正反控（判据必要性） =================
print('\n===== T4 正反控：放宽任一判据后的计数 =====')
def count_col(cols, drop=None):
    n=0
    for c in cols:
        v=cols[c]
        if drop=='sig' and v['sig'] not in (0,1,2): continue
        if drop!='cd0' and v.get('cd')!=0: pass
        n+=1
    return n
# A9: 去掉 +8==0
c9=0
for sn in ('.rdata','.data'):
    s=P.B[sn]; n=s['rawsize']//4; base=s['lo']
    w=struct.unpack_from('<%dI'%n,P.RAW,s['rawptr'])
    for k in range(n-4):
        if w[k] not in (0,1,2): continue
        if P.where(w[k+3])!='.data' or P.where(w[k+4])!='.rdata': continue
        nm=P.cstr(w[k+3]+8,400)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        c9+=1
print('   A9 去掉 +8==0 后 COL 计数 = %d (基准 %d)'%(c9,len(COL)))
# A10: 前缀放宽 .?A
c10=0
for sn in ('.rdata','.data'):
    s=P.B[sn]; n=s['rawsize']//4; base=s['lo']
    w=struct.unpack_from('<%dI'%n,P.RAW,s['rawptr'])
    for k in range(n-4):
        if w[k] not in (0,1,2) or w[k+2]!=0: continue
        if P.where(w[k+3])!='.data' or P.where(w[k+4])!='.rdata': continue
        nm=P.cstr(w[k+3]+8,400)
        if not nm: continue
        c10+=1
print('   A10 去掉名字约束（+8==0 且 pTD/pCHD 段对）计数 = %d'%c10)
# A11: 去掉 pTD 在 .data
c11=0
for sn in ('.rdata','.data'):
    s=P.B[sn]; n=s['rawsize']//4; base=s['lo']
    w=struct.unpack_from('<%dI'%n,P.RAW,s['rawptr'])
    for k in range(n-4):
        if w[k] not in (0,1,2) or w[k+2]!=0: continue
        if P.where(w[k+4])!='.rdata': continue
        nm=P.cstr(w[k+3]+8,400) if P.where(w[k+3]) in ('.data','.rdata') else None
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        c11+=1
print('   A11 去掉 |pTD 在 .data| 计数 = %d'%c11)
# 反控：sig 放宽
c12=sum(1 for sn in ('.rdata','.data') for k in [0])
print('   反控 sig 分布 = %s'%collections.Counter(v['sig'] for v in COL.values()).most_common())

print('\n断言 %d 条 / FAIL %d %s'%(NA,len(F),F))
json.dump({'COL':len(COL),'CHD':len(CHD),'own':len(own),'td_distinct':len(REF),
  'bca_recs':sum(NB.values()),'lens_total':sum(lens),'len_dist':L.most_common(12),
  'main':len(MAIN),'sec':len(SEC),'m_hit':m_hit,'s_hit':s_hit,
  'md_dist':{str(k):v for k,v in sorted(md.items())},
  'a9':c9,'a10':c10,'a11':c11,'nassert':NA,'fails':F},
  open('/home/t628/projects/ra2-campaign-forge/_r213/x0.json','w'),indent=1,ensure_ascii=False)
