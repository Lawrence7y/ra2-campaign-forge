# -*- coding: utf-8 -*-
"""R208 m12：①mdisp=4/8/12 三组共享视图对应的基类 pTD 名（定性接口）；②全部 attrs!=0 的 BCD 记录逐条；
③HEAD attributes 分布与相关性；④21784 记录在 BCD 与 COL 的双向一致性。
正控：1002 条 BCD 全分类
反控：把 attrs 换成 mdisp 做同样的相关性检验
"""
import sys,struct,collections,json
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
def s32(v): return struct.unpack('<i',struct.pack('<I',v))[0]
COL={}
for sn in ('.rdata','.data'):
    s=P.B[sn]; n=s['rawsize']//4; base=s['lo']
    w=struct.unpack_from('<%dI'%n,P.RAW,s['rawptr'])
    for i in range(n-4):
        if w[i] not in (0,1,2) or w[i+2]!=0: continue
        if P.where(w[i+3])!='.data' or P.where(w[i+4])!='.rdata': continue
        nm=P.cstr(w[i+3]+8,400)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base+4*i]=dict(sig=w[i],mdisp=s32(w[i+1]),pTD=w[i+3],pCHD=w[i+4],name=nm.decode('latin1'))
G=collections.defaultdict(list)
for c,v in COL.items(): G[v['pCHD']].append(c)
CHD=sorted(G)
NB={a:P.dw(a+8) for a in CHD}; pBCA={a:P.dw(a+12) for a in CHD}
ATTR={a:P.dw(a+4) for a in CHD}
BCA={a:[P.dw(pBCA[a]+4*j) for j in range(NB[a])] for a in CHD}
phys=sorted({x for a in CHD for x in BCA[a]})
def tn(t):
    n=P.cstr(t+8,300); return n.decode('latin1') if n else '?'
R={b:dict(pTD=P.dw(b),nc=P.dw(b+4),m=s32(P.dw(b+8)),p=s32(P.dw(b+12)),v=s32(P.dw(b+16)),attr=P.dw(b+20)) for b in phys}
own={a:COL[a+16]['pTD'] for a in CHD}
print('== A mdisp 4/8/12 组对应的基类 pTD ==')
for m in (4,8,12,21784):
    recs=[(b,R[b]) for b in phys if R[b]['m']==m]
    names=collections.Counter(tn(R[b]['pTD']) for b,_ in recs)
    print('  mdisp=%-6d 记录 %d 条，基类 pTD 名 %s' % (m,len(recs),names.most_common(4)))
    print('     记录 nc/attr 分布 %s ; 引用类数 %d' %
          (collections.Counter((R[b]['nc'],R[b]['attr']) for b,_ in recs).most_common(3),
           len({a for a in CHD for x in BCA[a] if x in {bb for bb,_ in recs}})))
print('== B attrs != 0 的 BCD 记录（全部）==')
nz=[b for b in phys if R[b]['attr']!=0]
print('  共 %d 条 / 1002；attrs 分布 %s' % (len(nz),collections.Counter(R[b]['attr'] for b in phys).most_common()))
for b in nz:
    r=R[b]
    cls=[tn(own[a]) for a in CHD if b in BCA[a]]
    print('  0x%-7x pTD=0x%-7x %-46s nc=%-3d m=%-6d p=%-4d v=%-3d attr=%-2d 引用类 %d: %s' %
          (b,r['pTD'],tn(r['pTD']),r['nc'],r['m'],r['p'],r['v'],r['attr'],len(cls),sorted(cls)[:3]))
print('== C HEAD attributes 分布 ==')
print('  %s' % collections.Counter(ATTR.values()).most_common())
print('  attrs==5 的类: %s' % [tn(own[a]) for a in CHD if ATTR[a]==5])
print('  attrs==2 的类: %s' % [tn(own[a]) for a in CHD if ATTR[a]==2][:12])
print('  attrs==0 的类数 %d' % sum(1 for a in CHD if ATTR[a]==0))
print('== D HEAD attrs 与 BCD attrs 的关系 ==')
hasv={a for a in CHD if any(R[x]['attr']!=0 for x in BCA[a])}
print('  BCA 含 attrs!=0 记录的类 %d 个；其 HEAD attrs 分布 %s' %
      (len(hasv),collections.Counter(ATTR[a] for a in hasv).most_common()))
print('  HEAD attrs!=0 但 BCA 全 attrs==0 的类 %d 个，HEAD attrs 分布 %s' %
      (sum(1 for a in CHD if ATTR[a]!=0 and a not in hasv),
       collections.Counter(ATTR[a] for a in CHD if ATTR[a]!=0 and a not in hasv).most_common()))
print('== E 反控：HEAD attrs 与「有额外视图」/「mdisp!=0」的相关性 ==')
print('  HEAD attrs vs 有额外视图: %s' % collections.Counter((ATTR[a],bool([c for c in G[a] if c!=a+16])) for a in CHD).most_common())
print('== F 21784 COL/BCD 一致性 ==')
anom=[c for c in COL if COL[c]['mdisp']==21784]
for c in anom:
    H=COL[c]['pCHD']
    b=[x for x in BCA[H] if R[x]['m']==21784]
    print('  COL 0x%x 类 %-32s ↔ BCD %s（pTD 名 %s）' %
          (c,COL[c]['name'],[hex(x) for x in b],[tn(R[x]['pTD']) for x in b]))
json.dump(dict(attrDist=[[k,v] for k,v in collections.Counter(R[b]['attr'] for b in phys).most_common()],
               headAttr=[[k,v] for k,v in collections.Counter(ATTR.values()).most_common()],
               nz=[[hex(b),R[b]['pTD'],tn(R[b]['pTD']),R[b]['nc'],R[b]['m'],R[b]['p'],R[b]['v'],R[b]['attr'],
                    [tn(own[a]) for a in CHD if b in BCA[a]]] for b in nz]),
          open('_r208/m12_attrs.json','w'),ensure_ascii=False,indent=1)
