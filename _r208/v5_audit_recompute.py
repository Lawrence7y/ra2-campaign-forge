# -*- coding: utf-8 -*-
"""R208 v5：执行员 #531 与审计员 #532 全部主张的 §2.12 规则 D 复算（不读 x1/x2 json）。
额外核验审计员的「thunk 级常量」提醒：按 thunk 地址分组，组内 imm 与本组 COL 的 mdisp 是否各自唯一。
反控：若按「锚点计数」口径，83 应为 67 / 81 应为 3，与 slot0 口径的 100/1 不可比 —— 直接实测两口径。
"""
import sys,struct,collections,json
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
def s32(v): return struct.unpack('<i',struct.pack('<I',v))[0]
fails=[];NA=0;OUT={}
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
loc=collections.defaultdict(list)
for sn in ('.rdata','.data'):
    s=P.B[sn]; n=s['rawsize']//4; base=s['lo']
    w=struct.unpack_from('<%dI'%n,P.RAW,s['rawptr'])
    for i,x in enumerate(w):
        if x in COL: loc[x].append(base+4*i)
vt={}
multi=0
for c in COL:
    q=[p for p in loc.get(c,[]) if P.where(P.dw(p+4))=='.text']
    if len(q)==1: vt[c]=q[0]+4
    elif len(q)>1: multi+=1
OUT['col']=len(COL); OUT['vt']=len(vt); OUT['multi_locator']=multi
ck('#531-1 STRICT: vftable locator 对 1214 条 COL 各恰好命中 1 个、无多重命中',
   len(COL)==1214 and len(vt)==1214 and multi==0,(len(COL),len(vt),multi))
CHD=sorted({v['pCHD'] for v in COL.values()})
extras=[c for c in vt if c not in {a+16 for a in CHD}]
prim=[c for c in vt if c in {a+16 for a in CHD}]
OUT['extras']=len(extras); OUT['prim']=len(prim)
ck('#532-1 主视图 954 / 额外视图 260 / 合计 1214',len(prim)==954 and len(extras)==260,(len(prim),len(extras)))
def form(slot0):
    o=P.r2o(slot0); b=P.RAW[o:o+16]
    if b[:4]==b'\x83\x6c\x24\x04': return 'A83'
    if b[:4]==b'\x81\x6c\x24\x04': return 'B81'
    if b[:3]==b'\xc2\x04\x00': return 'C20400'
    if b[:5]==b'\x32\xc0\xc2\x08\x00': return '32C0C20800'
    if b[:4]==b'\x8b\x44\x24\x04': return '8B442404'
    return 'REALFN'
D=collections.Counter(form(P.dw(vt[c])) for c in extras)
ck('#532-3 形态分布 = A83 100 / B81 1 / C20400 78 / 32C0C20800 75 / 8B442404 3 / REALFN 3，合计 260',
   D=={'A83':100,'B81':1,'C20400':78,'32C0C20800':75,'8B442404':3,'REALFN':3} and sum(D.values())==260,dict(D))
OUT['dist']=dict(D)
T=[c for c in extras if form(P.dw(vt[c])) in ('A83','B81')]
Dp=collections.Counter(form(P.dw(vt[c])) for c in prim)
OUT['prim_dist']=dict(Dp)
ck('#532-4 T 共 101 且全在额外视图；主视图 954 条 0 条 thunk（无 A83/B81）',
   len(T)==101 and not (set(Dp)&{'A83','B81'}),dict(Dp))
ck('#532-4b 主视图 954 条里有 2 条 slot0 以 8B 44 24 04 开头（CD 0x4790e0 / ProgressScreen 0x643e80），'
   '但体首是 mov eax,[esp+4]; cmp eax,0xfffffffe 或 mov [ecx+4],eax，属真函数体不是 thunk',
   Dp.get('8B442404')==2,[(hex(vt[c]),COL[c]['name'],hex(P.dw(vt[c]))) for c in prim if form(P.dw(vt[c]))=='8B442404'])
def imm(c):
    a=P.dw(vt[c]); o=P.r2o(a); b=P.RAW[o:o+12]
    if b[:4]==b'\x83\x6c\x24\x04': return struct.unpack('<i',b[4:5]+b'\x00\x00\x00')[0]
    if b[:4]==b'\x81\x6c\x24\x04': return struct.unpack('<i',b[4:8])[0]
    return None
ck('#532-5/#532-6 imm == mdisp 101/101（83 组 100/100 + 81 组 1/1）',
   all(imm(c)==COL[c]['mdisp'] for c in T) and sum(1 for c in T if form(P.dw(vt[c]))=='A83')==100,
   [(hex(c),COL[c]['name'],COL[c]['mdisp'],imm(c)) for c in T if imm(c)!=COL[c]['mdisp']][:3])
def jtgt(c):
    a=P.dw(vt[c]); o=P.r2o(a); b=P.RAW[o:o+16]
    if b[:4]==b'\x83\x6c\x24\x04': return a+10+struct.unpack('<i',b[6:10])[0]
    if b[:4]==b'\x81\x6c\x24\x04': return a+13+struct.unpack('<i',b[9:13])[0]
    return None
ck('#532-7 101/101 的 E9 目标全落 .text 且全 == 本类主视图 slot0',
   all(P.where(jtgt(c))=='.text' for c in T) and all(jtgt(c)==P.dw(vt[COL[c]['pCHD']+16]) for c in T),
   [(hex(c),COL[c]['name'],hex(jtgt(c))) for c in T if jtgt(c)!=P.dw(vt[COL[c]['pCHD']+16])][:3])
# thunk 级常量（审计 #532 提醒）
G=collections.defaultdict(list)
for c in T: G[P.dw(vt[c])].append(c)
OUT['thunk_addrs']=len(G)
gimm={a:{imm(c) for c in cs} for a,cs in G.items()}
gm={a:{COL[c]['mdisp'] for c in cs} for a,cs in G.items()}
ck('#532 提醒成立：100 条 A83 只映射到 21 个不同 thunk 地址',len([a for a in G if form(a)=='A83'])==21,
   len([a for a in G if form(a)=='A83']))
ck('#532 提醒成立：每个 thunk 地址的 imm 唯一（21/21），且该组内 COL 的 mdisp 也唯一（组内无冲突）',
   all(len(v)==1 for v in gimm.values()) and all(len(gm[a])==1 for a in G),
   {hex(a):(sorted(gimm[a]),sorted(gm[a])) for a in G if len(gm[a])>1 or len(gimm[a])>1})
OUT['thunk_imm']={hex(a):(sorted(gimm[a])[0],len(G[a])) for a in sorted(G)}
# 锚点口径 vs slot0 口径（审计 #532 的易误算点）
ts=P.B['.text']; raw=P.RAW[ts['rawptr']:ts['rawptr']+ts['rawsize']]; base=ts['lo']
def count_anchor(p):
    c=0; j=0
    while True:
        j=raw.find(p,j)
        if j<0: return c
        c+=1; j+=1
n83=count_anchor(b'\x83\x6c\x24\x04'); n81=count_anchor(b'\x81\x6c\x24\x04')
OUT['anchor']={'83':n83,'81':n81}
ck('#532-9 .text 锚点口径 83=67 / 81=3，与 slot0 口径 100/1 不可混用（分母不同）',
   n83==67 and n81==3 and n83!=100 and n81!=1,(n83,n81))
# 81 三站点的 vftable 槽归属
vt_of=collections.defaultdict(set)
for c in vt: vt_of[P.dw(vt[c])].add(c)
slots81=[0x41c670,0x41c680,0x41c690]
OUT['slot81_owner']={hex(a):sorted(COL[c]['name'] for c in vt_of.get(a,())) for a in slots81}
ck('#532 提醒成立：81 的另两处（0x41c680/0x41c690）不是任何 COL 的 slot0，而是同一 vftable 0x7e2250 的 slot1/slot2',
   OUT['slot81_owner']=={'0x41c670':['.?AVAircraftClass@@'],'0x41c680':[],'0x41c690':[]},
   OUT['slot81_owner'])
# vftable 0x7e2250 的槽序列
v=[P.dw(0x7e2250+4*k) for k in range(4)]
OUT['vt_7e2250']=[hex(x) for x in v]
ck('vftable 0x7e2250 = [0x41c670, 0x41c680, 0x41c690, ...] 三连 81 thunk',
   v[:3]==slots81,OUT['vt_7e2250'])
print('\n== 断言 %d / FAIL %d == %s'%(NA,len(fails),fails))
json.dump({'asserts':NA,'fails':fails,'out':OUT},open('/home/t628/projects/ra2-campaign-forge/_r208/v5_audit_recompute.json','w'),indent=1,ensure_ascii=False)
