# -*- coding: utf-8 -*-
"""R208 v1：主会话独立复算（不读 _r208 既有 json，仅从 gamemd.exe 重算）。
正控：结论必须成立；反控：把 0x7f9594 换成邻居地址/换成 0x800080 必须显著劣化。
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
# ---- 1. COL 全池（同 m17 判据）----
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
refidx=collections.defaultdict(list)
for sn in ('.rdata','.data'):
    s=P.B[sn]; n=s['rawsize']//4; base=s['lo']
    w=struct.unpack_from('<%dI'%n,P.RAW,s['rawptr'])
    for i,x in enumerate(w):
        if x in COL: refidx[x].append(base+4*i)
# ---- 2. TD 记录（+0 全等候选）----
td_by_plus0=collections.Counter()
tdnames=[]
for sn in ('.rdata','.data'):
    s=P.B[sn]; n=s['rawsize']//4; base=s['lo']
    w=struct.unpack_from('<%dI'%n,P.RAW,s['rawptr'])
    for i in range(n):
        nm=None
        try: nm=P.cstr(base+4*i+8,400)
        except Exception: nm=None
        if nm and nm.startswith(b'.?A') and nm.endswith(b'@@'):
            tdnames.append((base+4*i,w[i],nm.decode('latin1')))
scan_plus0=collections.Counter(v for _,v,_ in tdnames)
OUT['td_records']=len(tdnames)
OUT['plus0_top']=scan_plus0.most_common(3)
ck('V1 最大 +0 值是 0x7f9594 且计数 988',scan_plus0.most_common(1)[0][0]==0x7f9594 and scan_plus0.most_common(1)[0][1]==988,scan_plus0.most_common(1)[0])
OUT['td_unique_plus0']=len(scan_plus0)
ck('V1b 988 个 TD 记录的 +0 取值唯一（分布仅 1 项）',len(tdnames)==988 and len(scan_plus0)==1,(len(tdnames),len(scan_plus0)))
# ---- 3. 0x7f9594 的 .text 槽数 ----
k=0
while P.where(P.dw(0x7f9594+4*k))=='.text': k+=1
OUT['slots_at_7f9594']=k
ck('V2 0x7f9594 起 .text 槽恰 1 个',k==1,k)
OUT['slot0']=hex(P.dw(0x7f9594))
ck('V2b 唯一槽 = 0x7c8ab7',P.dw(0x7f9594)==0x7c8ab7,OUT['slot0'])
# ---- 4. vftable[-1] -> COL -> pTD 名 ----
v=P.dw(0x7f9590); OUT['vftable_minus1']=hex(v)
ck('V3 vftable[-1] = 0x80ee30 且是 COL',v==0x80ee30 and v in COL,v)
ck('V3b 该 COL 的 pTD 名 = .?AVtype_info@@',v in COL and COL[v]['name']=='.?AVtype_info@@',COL.get(v,{}).get('name'))
# ---- 5. cstr ----
s=P.cstr(0x7f9598,64); OUT['cstr']=s.decode('latin1') if s else None
ck('V4 +4 起是 Access violation - no RTTI data!',s is not None and s.startswith(b'Access violation - no RTTI data!'),OUT['cstr'])
# ---- 6. .data 内 imm 引用榜 ----
cnt=collections.Counter()
sd=P.B['.data']; nd=sd['rawsize']//4
wd=struct.unpack_from('<%dI'%nd,P.RAW,sd['rawptr'])
for x in wd: cnt[x]+=1
OUT['ref_7f9594']=cnt[0x7f9594]; OUT['ref_800080']=cnt[0x800080]
ck('V5 .data 内 0x7f9594 引用 988 / 0x800080 = 8',cnt[0x7f9594]==988 and cnt[0x800080]==8,(OUT['ref_7f9594'],OUT['ref_800080']))
# ---- 7. 律 M 三形态总数复算 ----
G=collections.defaultdict(list)
for c,v2 in COL.items(): G[v2['pCHD']].append(c)
CHD=sorted(G); NB={a:P.dw(a+8) for a in CHD}; pBCA={a:P.dw(a+12) for a in CHD}
BCA={a:[P.dw(pBCA[a]+4*j) for j in range(NB[a])] for a in CHD}
phys=sorted({x for a in CHD for x in BCA[a]})
vt={}
for c in COL:
    q=[x for x in refidx.get(c,[]) if P.where(P.dw(x+4))=='.text']
    if len(q)==1: vt[c]=q[0]+4
def vlen(s):
    kk=0
    while kk<4096 and P.where(P.dw(s+4*kk))=='.text': kk+=1
    return kk
Ext=[c for c in vt]  # 所有有 vftable 的 COL
# 额外视图 = 非 pCHD 内嵌主 COL 的视图
main={v3['pCHD'] for v3 in COL.values()}
# 主视图：每组 mdisp==0 的 COL 地址（内嵌于 CHD+16）
extras=[c for c in vt if c not in {CHD2+16 for CHD2 in CHD}]
OUT['vt_total']=len(vt); OUT['extras']=len(extras)
def enc(slot0):
    o=P.r2o(slot0)
    b=P.RAW[o:o+14] if o else b''
    if len(b)>=7 and b[0:4]==b'\x83\x6c\x24\x04' and b[5]==0xE9:
        return ('imm8',struct.unpack('<i',b[4:5]+(b'\x00'*3))[0],b)
    if len(b)>=10 and b[0:4]==b'\x81\x6c\x24\x04' and b[8]==0xE9:
        return ('imm32',struct.unpack('<i',b[4:8])[0],b)
    return (None,None,b)
T=[c for c in extras if enc(P.dw(vt[c]))[0]]
ENC=collections.Counter(enc(P.dw(vt[c]))[0] for c in T)
OUT['T_enc']=dict(ENC)
OUT['T_imm32']=[(COL[c]['name'],COL[c]['mdisp'],hex(P.dw(vt[c])),enc(P.dw(vt[c]))[2].hex()) for c in T if enc(P.dw(vt[c]))[0]=='imm32']
ck('V6b T 形态两种编码：imm8 100 / imm32 1，且两种的立即数都等于 mdisp',
   ENC=={'imm8':100,'imm32':1} and all(enc(P.dw(vt[c]))[1]==COL[c]['mdisp'] for c in T), (dict(ENC),OUT['T_imm32']))
ck('V6 额外视图 260 / thunk(T) 101',len(extras)==260 and len(T)==101,(len(extras),len(T)))
arr=collections.defaultdict(list)
for c in extras:
    arr[tuple(P.dw(vt[c]+4*j) for j in range(vlen(vt[c])))].append(c)
S=[c for c in extras if c not in T and len(arr[tuple(P.dw(vt[c]+4*j) for j in range(vlen(vt[c])))])>1]
I=[c for c in extras if c not in T and c not in S]
OUT['S']=len(S); OUT['I']=len(I); OUT['I_names']=[COL[c]['name'] for c in I]
ck('V7 S 156 / I 3 且 I 名集',len(S)==156 and len(I)==3 and sorted(COL[c]['name'] for c in I)==['.?AVAircraftClass@@','.?AVInfantryClass@@','.?AVUnitClass@@'],OUT['I_names'])
ck('V8 101+156+3=260 零残留',len(T)+len(S)+len(I)==260,len(T)+len(S)+len(I))
# ---- 9. 反控：换地址 ----
cnt2=collections.Counter({k:v for k,v in cnt.items() if k!=0 and P.where(k)=='.rdata'})
rank=cnt2.most_common(3); OUT['data_ref_top3']=rank
ck('C1 反控 .data 引用榜第二名 0x800080 仅 8 次（0x7f9594 的 1/123.5）',rank[0][0]==0x7f9594 and rank[1][0]==0x800080 and rank[1][1]==8,rank[:2])
print('\n== 断言 %d / FAIL %d == %s'%(NA,len(fails),fails))
json.dump({'asserts':NA,'fails':fails,'out':OUT},open('/home/t628/projects/ra2-campaign-forge/_r208/v1_lead_indep.json','w'),indent=1,ensure_ascii=False)
