# -*- coding: utf-8 -*-
"""R212 d2：核准 D4 的语义标签 / D10 的失败原因。"""
import sys,struct,collections,json
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
def S(v): return struct.unpack('<i',struct.pack('<I',v))[0]
COL={}
for sn in ('.rdata','.data'):
    s=P.B[sn]; n=s['rawsize']//4; base=s['lo']
    w=struct.unpack_from('<%dI'%n,P.RAW,s['rawptr'])
    for i in range(n-4):
        if w[i] in (0,1,2) and w[i+2]==0 and P.where(w[i+3])=='.data' and P.where(w[i+4])=='.rdata':
            m=P.cstr(w[i+3]+8,400)
            if m and m.startswith(b'.?A') and m.endswith(b'@@'):
                COL[base+4*i]=dict(mdisp=S(w[i+1]),pTD=w[i+3],pCHD=w[i+4],name=m.decode('latin1'))
G=collections.defaultdict(list)
for c,v in COL.items(): G[v['pCHD']].append(c)
CHD=sorted(G); NB={a:P.dw(a+8) for a in CHD}; pBCA={a:P.dw(a+12) for a in CHD}
BCA={a:[P.dw(pBCA[a]+4*j) for j in range(NB[a])] for a in CHD}
def N(t):
    c=P.cstr(t+8,400) if t else None
    return c.decode('latin1') if c else ''
per=collections.defaultdict(list)
for a in CHD:
    for j,e in enumerate(BCA[a]):
        per[a].append(dict(idx=j,mdisp=S(P.dw(e+8)),pTD=P.dw(e)))
d3=json.load(open('/home/t628/projects/ra2-campaign-forge/_r209/q3.json'))
MD={int(k,16):v for k,v in d3['mdisp'].items()}
VS=collections.defaultdict(dict)
for v in MD: VS[P.dw(v+16)][MD[v]]=v
V={a:set(VS[a])-{0} for a in VS}
emp={a for a in CHD if not V.get(a)}
nz={a for a in CHD if any(r['mdisp']!=0 for r in per[a])}
print('== D4 语义核准 ==')
print('  |全部|=%d  |V空|=%d  |含非零记录|=%d'%(len(CHD),len(emp),len(nz)))
print('  V空 ∧ 非零      = %d   (V 空但仍载非零记录 → 律 W 必须把它们滤掉)'%len(emp&nz))
print('  V非空 ∧ 非零    = %d   (律 W 真正「吃力」的类：既有视图又载非零记录)'%len(nz-emp))
print('  V空 ∧ 无非零    = %d   (平凡满足：两侧都空，自动一致)'%len(emp-nz))
print('  V非空 ∧ 无非零  = %d   (应为 0，否则律 W 会失配)'%len((set(CHD)-emp)-nz))
print('  并集覆盖 = %d / 954'%len(emp|nz))
print('  审计员三数 860/99/94 → 94 的实证位置：V非空∧非零 = %d'%len(nz-emp))
print('  审计员「平凡 855」= V空∧无非零 = %d ⇒ 数值对，标签「交集」错位'%len(emp-nz))
print('\n== D10 诊断：5 个 sink ==')
for a in (0x80e680,0x80e740,0x80e780,0x80e7c0,0x80e998):
    print('  CHD=%s  in COL? %s   CHD+16=%s in COL? %s  VS.get(CHD)=%s  VS.get(CHD+16)=%s'%(
      hex(a),a in COL,hex(a+16),a+16 in COL,
      sorted(VS.get(a,{})),sorted(VS.get(a+16,{}))))
    if a in COL:
        print('        CHD 本身作为 COL 记录：名=%s mdisp=%d'%(COL[a]['name'],COL[a]['mdisp']))
    if a+16 in COL:
        print('        own COL：名=%s mdisp=%d'%(COL[a+16]['name'],COL[a+16]['mdisp']))
    print('        该 CHD 的 BCA 非零记录 %s'%[r['mdisp'] for r in per[a] if r['mdisp']!=0])
