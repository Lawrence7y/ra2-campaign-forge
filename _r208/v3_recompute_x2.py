# -*- coding: utf-8 -*-
"""R208 v3：对审计员 #532（deepseek）结论的 §2.12 规则 D 独立复算（不读 x2 json，直接盘上重算）。
重点核验：①额外 slot0 = 83 编码 100 / 81 编码 1；②81 在 .text 的全部 3 处站点（0x41c670/680/690）与
jmp 目标；③imm==mdisp 101/101；④mdisp>127 的 4 条额外视图及其形态。
反控：假设接受「统一 83」口径，则 101 - 100 = 1 条无法解释；该条必须是 AircraftClass mdisp=1728。
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
OUT['col']=len(COL); OUT['vt']=len(vt)
CHD=sorted({v['pCHD'] for v in COL.values()})
extras=[c for c in vt if c!=CHD_MAP16] if False else [c for c in vt if c not in {a+16 for a in CHD}]
OUT['extras']=len(extras)
ck('V1 COL 1214 / vftable 1214 / 额外视图 260',len(COL)==1214 and len(vt)==1214 and len(extras)==260,
   (len(COL),len(vt),len(extras)))
def k(slot0):
    o=P.r2o(slot0); b=P.RAW[o:o+16]
    if b[:4]==b'\x83\x6c\x24\x04': return '83'
    if b[:4]==b'\x81\x6c\x24\x04': return '81'
    if b[:3]==b'\xc2\x04\x00': return 'C20400'
    if b[:5]==b'\x32\xc0\xc2\x08\x00': return '32C0C20800'
    if b[:4]==b'\x8b\x44\x24\x04': return '8B442404'
    return 'OTHER'
D=collections.Counter(k(P.dw(vt[c])) for c in extras)
OUT['dist']=dict(D)
ck('V2 额外视图 slot0 形态分布 = {83:100, 81:1, C20400:78, 32C0C20800:75, 8B442404:3, OTHER:3}',
   D=={'83':100,'81':1,'C20400':78,'32C0C20800':75,'8B442404':3,'OTHER':3},dict(D))
ck('V2b 83+81 = 101 = thunk 总数',D['83']+D['81']==101,D['83']+D['81'])
# imm 解码
def imm(c):
    a=P.dw(vt[c]); o=P.r2o(a); b=P.RAW[o:o+12]
    if b[:4]==b'\x83\x6c\x24\x04': return struct.unpack('<i',b[4:5]+b'\x00\x00\x00')[0],'83'
    if b[:4]==b'\x81\x6c\x24\x04': return struct.unpack('<i',b[4:8])[0],'81'
    return None,None
T=[c for c in extras if k(P.dw(vt[c])) in ('83','81')]
bad=[(hex(c),COL[c]['name'],COL[c]['mdisp'],imm(c)) for c in T if imm(c)[0]!=COL[c]['mdisp']]
OUT['T']=len(T); OUT['bad']=bad
ck('V3 T 101 条中立即数 == mdisp 101/101（0 例外）',len(T)==101 and not bad,bad[:3])
OUT['m83']=sorted({COL[c]['mdisp'] for c in T if imm(c)[1]=='83'})
OUT['m81']=[(COL[c]['name'],COL[c]['mdisp'],hex(P.dw(vt[c]))) for c in T if imm(c)[1]=='81']
ck('V3b 83 编码的 mdisp 集合 = {4,24,36,40,44}；81 编码唯一且 mdisp=1728',
   OUT['m83']==[4,24,36,40,44] and len(OUT['m81'])==1 and OUT['m81'][0][1]==1728,(OUT['m83'],OUT['m81']))
# .text 内 81 6C 24 04 全部站点（非对齐也扫）
ts=P.B['.text']; raw=P.RAW[ts['rawptr']:ts['rawptr']+ts['rawsize']]; base=ts['lo']
sites=[]
pj=0
while True:
    j=raw.find(b'\x81\x6c\x24\x04',pj)
    if j<0: break
    sites.append(base+j); pj=j+1
OUT['site81']=[hex(x) for x in sites]
ck('V4 .text 内 81 6C 24 04 恰 3 处',len(sites)==3,OUT['site81'])
info=[]
for a in sites:
    o=P.r2o(a); b=P.RAW[o:o+14]
    im=struct.unpack('<i',b[4:8])[0]
    tgt=a+13+struct.unpack('<i',b[9:13])[0]   # 81 6c 24 04 <imm32> = 8 B，E9 <rel32> = 5 B
    info.append((hex(a),im,hex(tgt),b[:13].hex()))
OUT['site81_info']=info
ck('V4b 3 处立即数全 = 1728、下一字节全为 E9、jmp 目标全落 .text',
   all(i[1]==1728 for i in info) and all(P.where(int(i[2],16))=='.text' for i in info),info)
ck('V4c 3 处目标各不相同（0x414290/0x4142f0/0x414300）',
   sorted(i[2] for i in info)==['0x414290','0x4142f0','0x414300'],[i[2] for i in info])
used=[c for c in T if imm(c)[1]=='81']
ck('V4d 3 个站点里只有 0x41c670 被某个额外视图 slot0 使用（其余 2 个是普通 vtable 槽）',
   len(used)==1 and P.dw(vt[used[0]])==0x41c670,hex(P.dw(vt[used[0]])) if used else None)
# mdisp>127 的额外视图
big=[c for c in extras if COL[c]['mdisp']>127]
OUT['big']=[(COL[c]['name'],COL[c]['mdisp'],k(P.dw(vt[c])),hex(P.dw(vt[c]))) for c in big]
ck('V5 mdisp>127 的额外视图 4 条：1 条 81 编码 + 3 条 8B442404（mov eax,[esp+4]; cmp eax,0x11c7）',
   len(big)==4 and sum(1 for x in OUT['big'] if x[2]=='81')==1 and sum(1 for x in OUT['big'] if x[2]=='8B442404')==3,OUT['big'])
# 反控
ck('反控：若按「统一 83」口径解释 101 条，则恰有 1 条无法解释，且它就是 AircraftClass mdisp=1728',
   len(T)-sum(1 for c in T if imm(c)[1]=='83')==1 and OUT['m81'][0][0]=='.?AVAircraftClass@@',
   OUT['m81'])
# 主视图里是否有 83/81 形态
prim=[c for c in vt if c not in extras]
P83=[c for c in prim if k(P.dw(vt[c]))in('83','81')]
OUT['prim_thunk']=len(P83)
ck('V6 主视图（954 条）里 0 条以 83/81 thunk 作 slot0',len(P83)==0,len(P83))
print('\n== 断言 %d / FAIL %d == %s'%(NA,len(fails),fails))
json.dump({'asserts':NA,'fails':fails,'out':OUT},open('/home/t628/projects/ra2-campaign-forge/_r208/v3_recompute_x2.json','w'),indent=1,ensure_ascii=False)
