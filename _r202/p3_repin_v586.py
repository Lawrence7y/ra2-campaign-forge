#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R202 台账升版 V585 -> V586：只改 F55 一行（追加第 ⑫ 条实测），其余 55 行逐字节不变。
fail-closed：旧常量复算旧 MASTER 命中旧 pin 作硬闸；新版本目录先写，后改指针（顺序不可反）。
"""
import ast, hashlib, io, os, re, sys, time
from collections import Counter
ROOT='/home/t628/projects/ra2-campaign-forge'
TIER=os.path.join(ROOT,'lead','next_re_20261117_r14')
OLD_DIR='R17_R131_FACTINDEX_V585'; NEW_DIR='R17_R131_FACTINDEX_V586'
SRC=os.path.join(TIER,OLD_DIR,'FACT_INDEX.tsv')
DSTDIR=os.path.join(TIER,NEW_DIR); DST=os.path.join(DSTDIR,'FACT_INDEX.tsv')
fails=[];n=0
def ck(nm,c,d=''):
    global n;n+=1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))
old=io.open(SRC,encoding='utf-8',newline='').read()
sha_old=hashlib.sha256(old.encode()).hexdigest()
ck('G1a 源 V585 未变（219024 B / 2d3d065a… / CR 0）',
   len(old.encode())==219024 and sha_old.startswith('2d3d065a') and old.count('\r')==0,
   (len(old.encode()),sha_old[:16],old.count('\r')))
L=old.split('\n')
ck('G1b 58 段（1 表头 + 56 行 + 尾空）且 5 列',len(L)==58 and all(len(x.split('\t'))==5 for x in L[:57]),
   (len(L),[i for i,x in enumerate(L[:57]) if len(x.split('\t'))!=5]))
R=[x.split('\t') for x in L[:57]]
f55=[r for r in R if r[0]=='F55'][0]

ADD1=('⑫**R202 交付（主会话 _r202/m14_authority.py 33 断言、m9_final.py 20 断言 0 FAIL、m8_verify.py 20 断言、m13_layout.py 复算）**：'
 '①**口径订正（影响百分比）**：R201 的 98.85% 用混合分母 697；实测 697 = **686 条严格次表 store**（disp8 恰等于该虚表 COL 记录的 mdisp，'
 '**686/686 全等**，mdisp 分布 **4:345 / 8:341**）+ **11 条 mdisp==0**。两组归属规则不同（686 条自身计入 brs、11 条不计）⇒ '
 '同质分母下「次表装填与主表装填同区间」= **686/686 = 100%**，在 ret/int3、E1（CALLAT 目标）、E3（CALLAT ∪ 严格序言位）三种网格下**全部成立**。'
 '②**判据订正**：R201「only_sub 的 0 首次成为结构性事实」不成立（该分支对 686 条因自身计数而恒真）；真事实是 **KM ⊇ KR**：'
 '含严格次表 store 的区间 **388 个，388/388（100%）也含至少一处主表 store**，「有次表无主表」区间数 **0**；'
 '含主表 store 的区间 **1,893** 个。主会话内部一度写作「死分支」，被可达性反控推翻（主表集置空 ⇒ only_sub 立刻 686）。'
 '③**区间不等于函数（本轮核心）**：31,968 个 ret/int3 区间中起点为 `nop` **17,726（55.45%）**；'
 '全 .text 去重 CALLAT 目标 **6,719** 个，落**指令起点** 6,692（99.6%）、落**区间起点**仅 **755（11.2%）**、'
 '其余 **5,964** 落区间内部；**25,357（79.3%）** 个区间内零 CALLAT 目标 ⇒ 「store 所属区间」≠「同一函数」，在 79% 区间上无约束。'
 '④**收紧网格结论不变**：E1 = CALLAT 目标（6,692）；E3 = E1 ∪ 严格序言位，区间起点上的序言分布 '
 '**P1（push ebp; mov ebp,esp）249 / P4（sub esp,imm 起首）158 / P3b（mov edi,edi 后 3 条内含两级序言）60**，合计 **467**，'
 '**(i)∪(ii) = 864** 个区间，|E3| = **10,674**。697 条在 E3 下 **both 691 / only_sub 0 / none 6**'
 '（none：0x5d5b80 / 0x635f34 / 0x637114 / 0x638aa4 / 0x7b1b2b / 0x7b27fb）；686 条在三种网格下均 **686/0/0**。'
 '反控：E3 每入口 +1 字节 ⇒ **683/3/0**（非恒等变换）。'
 '⑤**8 条 none 的宿主类名（5 取得 / 3 UNDETERMINED）**：0x5d5b80 → `MultiplayerGameMode`（区间内另有 '
 '`DynamicVectorClass<MultiplayerTeam>` 与 `CCINIClass` 主表）；0x6cf196 与 0x6cf209 → `SwizzleManagerClass`'
 '（区间内另有 `DynamicVectorClass/VectorClass<SwizzlePointerClass>` 主表与 `SuperWeaponTypeClass` 的 +4/+8/+12 次表）；'
 '0x7b1b2b 与 0x7b27fb → `WinsockInterfaceClass`（区间内另有 3..5 处 `VectorClass<PAUWinsockBufferType@WinsockInterfaceClass>` 主表）。'
 '**UNDETERMINED**：0x635f34 / 0x637114 / 0x638aa4 —— 其区间内只有模板成员类（`DynamicVectorClass<PlanningNodeClass>` / '
 '`VectorClass<PlanningNodeClass>`）的**主表**，无任何非模板外层类主表；调用点前 24 字节只有 `mov ecx,...` 透传，拿不到外层 RTTI 写入证据。'
 '⑥**11 条 mdisp==0 装表是两种机制**：机制 A（**3 条，全是 `. ?AVINoticeSink@@`：0x410174 / 0x4101c2 / 0x6e8008**）'
 '的 +8 槽位**被后续基类次表同槽位覆盖** —— 0x410174 / 0x4101c2 为 [INoticeSink mdisp=0] → [AbstractClass mdisp=8]，'
 '0x6e8008 为 [INoticeSink] → [AbstractClass mdisp=8] → [TaskForceClass mdisp=8]；'
 '机制 B（**8 条模板容器成员**）槽位序列长度恒 **1**、无任何后续覆盖，是纯粹的内嵌成员子对象 vftable 初始化。'
 '**判别力**：686 条中「后继同槽位被 mdisp==disp 的 store 覆盖」只有 **12 条（1.7%）**，11 条中 **3 条（27.3%）**，富集 **16.1 倍**。'
 'INoticeSink 全段主表装填仅 **5 处**（0x410174 / 0x4101c2 / 0x6e8008 disp=8、0x5be9bd disp=21784、0x6cfe3c disp=0），'
 'disp=8 的 3 处全部命中覆盖 ⇒ **R201「11 条全是内嵌成员子对象主表初始化」的定性只对 8 条成立**。'
 '⑦**交叉点（审计 #510 独立发现，主会话逐数复算后采纳）**：VT 项的 COL 指针**恒在 vt-4**（**1214/1214** 成立），'
 '而 COL 结构体自身地址**不是常数**（相对虚表地址有 **916 个不同取值**）⇒ 只能查表、不能线性推算；'
 '主会话独立得同一结论，并订正 m7 的「死分支」表述。'
 '⑧**自错 13 组（0 条进结论）**：分母不同源 3 处（m1 断言 689/697 却用 686 集、m3-F4a 得 697/0/0、m8-P4c 按 #510 的 564 设区间）；'
 'm2 三条断言预期「识别 0x66 前缀后掉到 686」实测**两提取器均 697**（697/686 之差是 mdisp==0 的 11 条，**不是前缀**）；'
 'm3 拿 118,491 全指令起点与 1,150 区间起点子集比较；m4 扰动反控把区间键换成新元组致反控自身失效；'
 'm7 断言「brs>=1 恰 686」实测 **689**，其「死分支」表述因此不成立；m10 假设「每 disp 只对应一类」，'
 '实测 `AbstractClass` 次表在 +4/+8/+12 三处都有；m12-V1a 预期「11 条全覆盖」实测 3 条 —— **该 FAIL 开出第六交付**，'
 'V3a 判别力门限写反；m13-W4a 断言槽位序列恒 1 实测 **{1:662, 2:16, 3:8}**，W5b 的 `0x5be9bd`（disp=21784）也有覆盖；'
 'm15-Y1a 把 P1=249 当全指令起点计数（真值 **458**，249 是区间起点子集），Y3a 的 P3 严格 span=3 时 0 条。'
 '⑨**跨家族**：执行员 **#509**（hy4，31 回合 / 7.65 分 / 预算 8 分，**无 OVERTIME**，18 断言 0 FAIL）的 5 条类名与 3 条 UNDETERMINED '
 '逐条复算一致；审计员 **#510**（deepseek，20 回合 / 7.68 分，**无 OVERTIME**，33 断言全 PASS）采纳 **3 条**'
 '（区间≠函数三证据 55.45%/5,964/79.3%、函数范围口径 **691/0/6** 与 6 条 none 地址逐条、COL 指针恒 vt-4 且地址 916 取值）、'
 '**不采纳 2 条**（「11 条应称 disp 与 mdisp 不一致」—— mdisp==0 即该 COL 记录的主对象标记，命名无误；'
 '「重装 564/697 = 80.9%」—— 那是全 4,198 条 vts 的函数范围口径，与 686 条小位移口径的 **285/114** 不可比，两者并存标注）。')

ADD_EV='_r202/m8_verify.py;_r202/m8_verify.json;_r202/m9_final.py;_r202/m9_final.json;_r202/m13_layout.py;_r202/m13_layout.json;_r202/m14_authority.py;_r202/m14_authority.json;_r202/m15_prolog.py;_r202/m15_prolog.json;_r202/m12_overwrite.py;_r202/m10_inotice.py;_r202/m11_inotice2.py;_r202/m7_deadbranch.py;_r202/m1_realfunc.py;_r202/m3_caliber.py;_r202/m4_both689.py;_r202/m5_funcgrid.py;_r202/m6_selfpollute.py;_r202/b_nonehost.py;_r202/b_nonehost.log;_r202/audit_c.py;_r202/audit_c.log'

f55[1]=f55[1]+ADD1
f55[3]=f55[3]+';'+ADD_EV
f55[4]=f55[4]+'；R202 边界：E3 只是**候选入口网格**、不是真函数边界（间接调用目标不可恢复）；686 条同区间率 100% 受「区间 = 直到下一条 ret/int3」这一近似约束，E5 网格（31,968 个区间起点）下 697 条得 689/0/8 而 686 条仍 686/0/0，故 100% 在该近似下稳健但函数真边界未取得；8 条 none 中 3 条外层类名仍 UNDETERMINED。'
new='\n'.join('\t'.join(r) for r in R)+'\n'+(L[-1] if L[-1]=='' else '')
newraw=new.encode()
ck('G2a 新体 CR 仍 0 / 换行数仍 57',newraw.count(b'\r')==0 and new.count('\n')==len(L)-1,
   (newraw.count(b'\r'),new.count('\n'),len(L)-1))
ck('G2b 除 F55 外 55 行逐字节未变',
   all(R[i]==L[i].split('\t') for i in range(57) if R[i][0]!='F55'),True)
FF=os.path.join(ROOT,'_r160/facts_floors.py')
src=io.open(FF,encoding='utf-8',newline='').read()
need=('CUR_SHA256','TOTAL_BYTES','MASTER_SHA256','GRADES','FLOORS','EVID','EVIDB','LOST','ITEMS','UNIQ','LOST_ITEMS','LOST_UNIQ')
C={}
for node in ast.parse(src).body:
    if isinstance(node,ast.Assign) and isinstance(node.targets[0],ast.Name):
        nm=node.targets[0].id
        if nm in need: C[nm]=ast.literal_eval(node.value)
ck('G3a 12 常量可 ast 取出',all(k in C for k in need),len(C))
def canon_g(d): return '\n'.join("    '%s': '%s',"%(k,d[k]) for k in sorted(d))
def canon_f(d): return '\n'.join("    '%s': (%d, %d),"%(k,d[k][0],d[k][1]) for k in sorted(d))
def canon_e(d): return '\n'.join("    '%s': [%s],"%(k,', '.join("'%s'"%x for x in d[k])) for k in sorted(d))
def canon_eb(d): return '\n'.join("    '%s': %d,"%(k,d[k]) for k in sorted(d))
def master(sha,tot,floors,grades,evid,evidb,lost,items,uniq,li,lu):
    return hashlib.sha256(('\n'.join([sha,str(tot),canon_g(grades),canon_f(floors),canon_e(evid),
        canon_eb(evidb),canon_eb(lost),str(items),str(uniq),str(li),str(lu)])).encode()).hexdigest()
old_m=master(C['CUR_SHA256'],C['TOTAL_BYTES'],C['FLOORS'],C['GRADES'],C['EVID'],C['EVIDB'],
             C['LOST'],C['ITEMS'],C['UNIQ'],C['LOST_ITEMS'],C['LOST_UNIQ'])
ck('G3b 旧常量复算旧 MASTER 命中旧 pin（硬闸）',old_m==C['MASTER_SHA256'],(old_m[:16],C['MASTER_SHA256'][:16]))
new_sha=hashlib.sha256(newraw).hexdigest(); new_tot=len(newraw)
def strip_note(s):
    s=s.strip()
    if s.endswith(')'):
        d=0
        for i in range(len(s)-1,-1,-1):
            if s[i]==')': d+=1
            elif s[i]=='(':
                d-=1
                if d==0: return s[:i].strip()
    return s
def norm(p): return p.replace('\\','/').strip()
def resolvable(p):
    for c in (p,'lead/'+p,TIER+'/'+p):
        if os.path.exists(os.path.join(ROOT,c)): return True
    return False
items=[]
for r in R[1:]:
    for x in r[3].split(';'):
        if x.strip(): items.append((r[0],norm(strip_note(x))))
uniq=set(p for _,p in items)
lost=[p for _,p in items if not resolvable(p)]
lostc=Counter(lost)
newitems=[norm(strip_note(x)) for x in ADD_EV.split(';') if x.strip()]
ck('G3c 新增 %d 条证据路径全部可解析'%len(newitems),all(resolvable(x) for x in newitems),
   [x for x in newitems if not resolvable(x)])
ck('G3d LOST 多重集逐键未变',dict(lostc)==C['LOST'],(len(lost),len(lostc),C['LOST_ITEMS']))
GRADES2=dict(C['GRADES']);FLOORS2=dict(C['FLOORS'])
FLOORS2['F55']=(len(f55[1].encode()),len(f55[4].encode()))
EVID2=dict(C['EVID']);EVIDB2=dict(C['EVIDB'])
EVID2['F55']=[norm(strip_note(x)) for x in f55[3].split(';') if x.strip()]
EVIDB2['F55']=len(f55[3].encode())
ck('G3e FLOORS F55 现盘 %s -> %s（stmt 增、lim 不缩）'%(C['FLOORS']['F55'],FLOORS2['F55']),
   C['FLOORS']['F55']==(39304,24540) and FLOORS2['F55'][0]>39304 and FLOORS2['F55'][1]>=24540,
   (C['FLOORS']['F55'],FLOORS2['F55']))
ck('G3f EVID F55 %d -> %d 条且前 %d 条逐项未动'%(len(C['EVID']['F55']),len(EVID2['F55']),len(C['EVID']['F55'])),
   len(EVID2['F55'])==len(C['EVID']['F55'])+len(newitems) and EVID2['F55'][:len(C['EVID']['F55'])]==C['EVID']['F55'],
   (len(EVID2['F55']),len(newitems)))
ck('G3g EVIDB F55 %d -> %d'%(C['EVIDB']['F55'],EVIDB2['F55']),C['EVIDB']['F55']==1879 and EVIDB2['F55']!=1879,EVIDB2['F55'])
_low=[]
for fid in C['FLOORS']:
    if fid=='F55': continue
    r=[x for x in R if x[0]==fid][0]
    cur=(len(r[1].encode()),len(r[4].encode())); fl=C['FLOORS'][fid]
    if not (cur[0]>=fl[0] and cur[1]>=fl[1]): _low.append((fid,fl,cur))
ck('G3h 既有 55 条 FLOORS 仍 <= 现盘',not _low,_low[:3])
ck('G3i 既有 55 条 grade 逐条未变',
   all(C['GRADES'][k]==[x for x in R if x[0]==k][0][2] for k in C['GRADES'] if k!='F55'),True)
new_m=master(new_sha,new_tot,FLOORS2,GRADES2,EVID2,EVIDB2,dict(lostc),len(items),len(uniq),len(lost),len(lostc))
ck('G3j 新 MASTER != 旧 MASTER',new_m!=old_m,(new_m[:16],old_m[:16]))
ck('G3k 反控 A：F55 lim floor +1 ⇒ MASTER 变',
   master(new_sha,new_tot,{**FLOORS2,'F55':(FLOORS2['F55'][0],FLOORS2['F55'][1]+1)},GRADES2,EVID2,EVIDB2,
          dict(lostc),len(items),len(uniq),len(lost),len(lostc))!=new_m,True)
ck('G3l 反控 B：EVIDB F55 +1 ⇒ MASTER 变',
   master(new_sha,new_tot,FLOORS2,GRADES2,EVID2,{**EVIDB2,'F55':EVIDB2['F55']+1},dict(lostc),
          len(items),len(uniq),len(lost),len(lostc))!=new_m,True)
ck('G3m 反控 C：TOTAL_BYTES +1 ⇒ MASTER 变',
   master(new_sha,new_tot+1,FLOORS2,GRADES2,EVID2,EVIDB2,dict(lostc),
          len(items),len(uniq),len(lost),len(lostc))!=new_m,True)
print('   ITEMS %d -> %d / UNIQ %d -> %d / LOST %d -> %d / LOST_UNIQ %d -> %d'%(
   C['ITEMS'],len(items),C['UNIQ'],len(uniq),C['LOST_ITEMS'],len(lost),C['LOST_UNIQ'],len(lostc)))
ck('G3n ITEMS/UNIQ 增量 == %d'%len(set(newitems)),(len(items)-C['ITEMS'],len(uniq)-C['UNIQ'])==(len(newitems),len(set(newitems))),
   (len(items)-C['ITEMS'],len(uniq)-C['UNIQ'],len(newitems),len(set(newitems))))
if fails:
    print('★ fail-closed：%d 条未过，不写盘'%len(fails)); sys.exit(1)
print('== 写盘阶段 1：先建新版本目录 ==')
os.makedirs(DSTDIR,exist_ok=True)
with io.open(DST,'wb') as f: f.write(newraw)
ck('W1a 目标目录新建完成',os.path.exists(DST),os.path.basename(DSTDIR))
ck('W1b 回读一致（sha / 字节 / CR）',
   hashlib.sha256(io.open(DST,'rb').read()).hexdigest()==new_sha and
   len(io.open(DST,'rb').read())==new_tot and io.open(DST,'rb').read().count(b'\r')==0,
   (new_sha[:16],new_tot))
ns=src
ns=ns.replace("'%s'"%OLD_DIR,"'%s'"%NEW_DIR,1)
ck('G4a EXPECT_CUR 目录号已换且只 1 处',OLD_DIR not in ns and ns.count(NEW_DIR)==1,(ns.count(OLD_DIR),ns.count(NEW_DIR)))
ns=ns.replace("CUR_SHA256 = '%s'"%C['CUR_SHA256'],"CUR_SHA256 = '%s'"%new_sha,1)
ns=ns.replace("TOTAL_BYTES = %d"%C['TOTAL_BYTES'],"TOTAL_BYTES = %d"%new_tot,1)
def block(olddict,newdict,name):
    global ns
    pat=re.compile(r'^%s = \{\n(.*?)\n\}$'%name,re.M|re.S)
    m=pat.search(ns); assert m,name
    body_old=m.group(1)
    def fmt(v):
        if isinstance(v,str): return "'%s'"%v
        if isinstance(v,tuple): return '(%d, %d)'%v
        if isinstance(v,int): return '%d'%v
        return '[%s]'%', '.join("'%s'"%x for x in v)
    body_new='\n'.join("    '%s': %s,"%(k,fmt(newdict[k])) for k in sorted(newdict))
    ns=ns[:m.start(1)]+body_new+ns[m.end(1):]
    return body_old!=body_new
ch_g=block(C['GRADES'],GRADES2,'GRADES')
ch_f=block(C['FLOORS'],FLOORS2,'FLOORS')
ch_e=block(C['EVID'],EVID2,'EVID')
ch_b=block(C['EVIDB'],EVIDB2,'EVIDB')
ck('G4b 只有 FLOORS / EVID / EVIDB 三表变化',ch_f and ch_e and ch_b and not ch_g,(ch_g,ch_f,ch_e,ch_b))
for name,val in (('ITEMS',len(items)),('UNIQ',len(uniq)),('LOST_ITEMS',len(lost)),('LOST_UNIQ',len(lostc))):
    ns=re.sub(r'^%s = \d+$'%name,'%s = %d'%(name,val),ns,count=1,flags=re.M)
pat=re.compile(r'^LOST = \{\n(.*?)\n\}$',re.M|re.S)
m=pat.search(ns); ck('G4c LOST 表可定位',m is not None,True)
ns=ns[:m.start(1)]+'\n'.join("    '%s': %d,"%(k,lostc[k]) for k in sorted(lostc))+ns[m.end(1):]
ns=ns.replace("MASTER_SHA256 = '%s'"%C['MASTER_SHA256'],"MASTER_SHA256 = '%s'"%new_m,1)
C2={}
for node in ast.parse(ns).body:
    if isinstance(node,ast.Assign) and isinstance(node.targets[0],ast.Name):
        nm=node.targets[0].id
        if nm in need: C2[nm]=ast.literal_eval(node.value)
ck('G4d 新源码 12 常量可 ast 取出',all(k in C2 for k in need),len(C2))
ck('G4e 新源码用新常量复算 MASTER 命中新 pin',
   master(C2['CUR_SHA256'],C2['TOTAL_BYTES'],C2['FLOORS'],C2['GRADES'],C2['EVID'],C2['EVIDB'],
          C2['LOST'],C2['ITEMS'],C2['UNIQ'],C2['LOST_ITEMS'],C2['LOST_UNIQ'])==C2['MASTER_SHA256'],True)
ck('G4f 新源码 F55 floor 与 EVIDB 已换',
   C2['FLOORS']['F55']==FLOORS2['F55'] and C2['EVIDB']['F55']==EVIDB2['F55'],
   (C2['FLOORS']['F55'],C2['EVIDB']['F55']))
GR=os.path.join(ROOT,'_r161/gate_runner.py')
gr=io.open(GR,encoding='utf-8',newline='').read()
ck('G5a gate_runner 含旧目录 1 次',gr.count(OLD_DIR)==1,gr.count(OLD_DIR))
gr2=gr.replace(OLD_DIR,NEW_DIR,1)
ck('G5b gate_runner 换后含新目录 1 次 / 旧目录 0 次',gr2.count(NEW_DIR)==1 and gr2.count(OLD_DIR)==0,(gr2.count(NEW_DIR),gr2.count(OLD_DIR)))
PTR=os.path.join(TIER,'FACT_INDEX_CURRENT.md')
ptr=io.open(PTR,encoding='utf-8',newline='').read()
ck('G6a 旧版本目录串在指针里出现 2 次',ptr.count(OLD_DIR)==2,ptr.count(OLD_DIR))
for o,tag in ((C['CUR_SHA256'],'P2 sha256'),(str(C['TOTAL_BYTES']),'P3 字节数'),
              ('530..585 连续 56 份','P4 自述份数'),('| 声明轮次 | R200 |','P5 声明轮次')):
    ck('G6b %s 在指针里恰 1 次'%tag,ptr.count(o)==1,ptr.count(o))
ptr2=ptr.replace(OLD_DIR,NEW_DIR).replace(C['CUR_SHA256'],new_sha,1) \
    .replace(str(C['TOTAL_BYTES']),str(new_tot),1) \
    .replace('530..585 连续 56 份','530..586 连续 57 份',1) \
    .replace('| 声明轮次 | R200 |','| 声明轮次 | R201 |',1)
ck('G6c 指针新体含 V586 与 R201',NEW_DIR in ptr2 and '| 声明轮次 | R201 |' in ptr2,True)
if fails:
    print('★ fail-closed（写盘阶段 2）：%d 条未过'%len(fails)); sys.exit(1)
print('== 写盘阶段 2：改 facts_floors / gate_runner / 指针 ==')
BL=os.path.join(TIER,'R17_LEAD_BASELINE'); stamp=time.strftime('%Y%m%d_%H%M%S')
for path,oldraw,newtxt,tag in ((FF,src.encode(),ns,'facts_floors'),
                               (GR,gr.encode(),gr2,'gate_runner'),
                               (PTR,ptr.encode(),ptr2,'ptr')):
    bak=os.path.join(BL,'%s.before_r202_repin_%s.bak'%(tag,stamp))
    fd=os.open(bak,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o644)
    with os.fdopen(fd,'wb') as f: f.write(oldraw)
    ck('W2 %s 备份 sha 一致'%tag,
       hashlib.sha256(open(bak,'rb').read()).hexdigest()==hashlib.sha256(oldraw).hexdigest(),True)
    assert io.open(path,'rb').read()==oldraw,'%s 被外部改动'%tag
    io.open(path,'w',encoding='utf-8',newline='').write(newtxt)
    ck('W3 %s 回读一致'%tag,
       hashlib.sha256(open(path,'rb').read()).hexdigest()==hashlib.sha256(newtxt.encode()).hexdigest(),True)
print('   NEW_SHA=%s NEW_BYTES=%d NEW_MASTER=%s'%(new_sha,new_tot,new_m))
print('   FLOORS F55=%s EVIDB F55=%d EVID F55=%d 条'%(FLOORS2['F55'],EVIDB2['F55'],len(EVID2['F55'])))
print('   ITEMS=%d UNIQ=%d LOST=%d/%d'%(len(items),len(uniq),len(lost),len(lostc)))
print('\nSUMMARY asserts=%d fails=%d %s'%(n,len(fails),fails))
