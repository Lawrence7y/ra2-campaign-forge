# -*- coding: utf-8 -*-
"""R213 p1：FACT_INDEX V595 -> V596。把本轮 3 条新事实补入 F29（律 X / 视图槽表 / S3 函数体），
并把 RTTI 三角闭环订正补入 F01（旧数 1201/1211 与 COL+4 口径）。其余行逐字节不变。
"""
import os,hashlib
ROOT='/home/t628/projects/ra2-campaign-forge'
TIER=ROOT+'/lead/next_re_20261117_r14'
BASE=ROOT+'/lead/R17_LEAD_BASELINE'
OLDV=TIER+'/R17_R131_FACTINDEX_V595/FACT_INDEX.tsv'
NEWDIR=TIER+'/R17_R131_FACTINDEX_V596'
raw=open(OLDV,'rb').read()
OLD_SHA=hashlib.sha256(raw).hexdigest(); OLD_B=len(raw)
print('V595 sha %s bytes %d'%(OLD_SHA,OLD_B))
assert OLD_SHA=='9ffc56c90e3537e5d238759866b2a41d7eb4b2efa2c3100d8bcde3a166b40f18',OLD_SHA
assert OLD_B==257435,OLD_B
lines=raw.decode('utf-8').split('\n'); ORIG=list(lines)

ADD29=('【律 X · R213 实测·101/101】次视图的 slot0 形态把 260 张次视图**二分**：'
 '①**101 张**的 slot0 是 **this-adjustor thunk**（形态 `sub dword ptr [esp+4], imm` ; `jmp rel32`），'
 '其 **imm 恒等于该 COL 记录的 mdisp**（101/101，无反例；mdisp→imm 观测集为 {4:[4],24:[24],36:[36],40:[40],44:[44],1728:[1728]}）；'
 '②其余 **159 张**为 8(78)/12(78)/21784(3) 三类，均非 adjustor。'
 '全体 adjustor **槽**（不只 slot0）合计 **305** 个，其中 **303** 个 imm==mdisp、**2** 个例外'
 '（?AVHouseClass@@ mdisp=40 的 idx=3 与 idx=4，imm=4，jmp 0x4f6e60 / 0x4f6950，两目标均在主视图槽内）。'
 '每张次视图的 adjustor 数 ∈ {0:159, 3:100, 5:1}；槽型模板共 **7** 种且**全部以 AAA 打头**'
 '（AAAFFF:78 / AAA+47F:12 / AAAFFFFF:6 / AAAFF:2 / AAAFFFFFF:1 / AAAA AFFFF:1 / AAA+13F:1）。'
 '反控：**954 张主视图内 adjustor 槽 = 0**（0 例外）。adjustor 的 jmp 目标共 **40** 个、全部落 .text、'
 '其中 **303/305** 落在**本类主视图槽**内（多继承 forwarding），最高频三个目标 0x410260(75 类)/0x410300(74)/0x410310(74)。'
 '【视图槽表定长复算 · R213】vftable 定位口径 = **「.rdata 中某 word == COL 地址、且下一 word ∈ .text」的位点 + 4**，'
 '**不是 COL+4**：COL+4 起连续 .text 指针在 1214 条上全部为 0（反控）。该位点恰 **1214** 个、每 COL 恰 1 个、'
 '1214 条 COL ↔ 1214 个 vftable 双射、起点两两不重复；槽总数 **14044**（主视图 954 张 **12726** 槽、其中 slot≥3 计 **9958**；'
 '次视图 260 张 **1318** 槽）；按 mdisp 的长度分布 = 0:{7:412,5:158,3:82,9:60,1:40,24:26,…} / 4:{6:78,50:12,5:1} / '
 '8:{1:78} / 12:{1:78} / 24:{8:6} / 36:{15:1} / 40:{9:1} / 44:{5:1} / 1728:{9:1} / 21784:{1:3}。'
 '【TD+0 负控 · R213】**988/988 个 TypeDescriptor 的 +0 是同一个值 0x7f9594**（distinct=1），'
 '该址首槽 0x7c8ab7 = `push esi ; mov esi,ecx ; call 0x7c8a8e ; test byte [esp+8],1`（scalar deleting dtor 形态），'
 '+4 处即 ASCII "Access violation - no RTTI data!"；.text 内被引用仅 2 处（0x7c8a93 / 0x7c8b2f 的 `mov [..],0x7f9594`）、'
 '该字符串被 3 处 push（0x7ca956 / 0x7caab0 / 0x7cabe0），即 TD+0 是**共享 type_info 占位 vfptr**，'
 '**禁止**用 TD+0 判类归属或视图归属（此前若以 TD+0==vftable 作判据全表 0/1214 命中）。'
 '【S3 函数体字节语义定案 · R213】mdisp=21784 的 3 条（MouseClass 0x7fab28 / TabClass 0x805e90 / ScrollClass 0x809050）'
 '共享**同一视图**（各 1 槽，slot0 同为 **0x6d1770**），函数体 0x6d1770..0x6d17f3 全解：'
 '`mov eax,[esp+4]` ; `cmp eax,0x11c7` jne→第二分支 ; 取全局 **0xb0cc1c** 作序号 → 读 int 数组 **[0xb0cb78 + eax*4]** '
 '→ `jl 0` / `cmp eax,0x19` `jge`（**上界 25**）→ `lea ecx,[eax+eax*2] ; shl ecx,5`（**元素步长 96**）`; add ecx,0xb0c1c0` '
 '→ `test ecx,ecx` je → 读 **byte [ecx+0x2d]** → `test al,al` `jne` 跳过 → `call 0x723ea0` ; 出口 `mov al,1 ; ret 8`；'
 '第二分支 `cmp eax,0x11c8` 结构同构但判据反相（`je` 跳过）并 `call 0x723eb0`，同样 `mov al,1 ; ret 8`；'
 '第三出口 `xor al,al ; ret 8`（消息 ID 既非 0x11c7 也非 0x11c8）。两个被调 **0x723ea0 / 0x723eb0** = '
 '`mov eax,[ecx]` + `mov byte [ecx+0x2d],1`（或 `,0`）+ `jmp dword [eax+0x48]` ⇒ 语义为「对第 k 个结构置/清 [k+0x2d] 标志位并转发虚槽 +0x48」。'
 '三个全局 0xb0cb78 / 0xb0cc1c / 0xb0c1c0 全部落在 **virt-only（BSS，未初始化）**，初值须运行期取（属动态项）。'
 '【0x11c7/0x11c8 字面普查 · 陷阱反控】二字面在 **.text 分别 2 处 / 5 处**、在 **.rdata/.data 均 0 处**（故不是 IID/GUID）；'
 '但字面命中 **不等于** 消息 ID 使用点：0x11c7 的 2 处中仅 **0x6d1775** 是真 `cmp`，另 1 处 0x6379fb 是 `push 0x11c7`（0x6379fa 起）的字面错位；'
 '0x11c8 的 5 处中仅 **0x6d17b2** 是真 `cmp`，**2 处是 __LINE__ 断言宏**（0x5e0bc4 `push 0x11c8` + `push 0x831288`="D:\\\\ra2mdpost\\\\netdlg2.cpp"；'
 '0x784ed4 同形 + `push 0x84a430`="D:\\\\ra2mdpost\\\\wonline.cpp"），另 2 处是**结构体位移**假阳性（0x4a87f0 `mov [esi+0x11c8],eax`、0x637a8e `push 0x11c8` 传参）。'
 '另有 .rsrc 1 处 0xb7a8bc（资源载荷，非立即数）。⇒ **任何「立即数出现 N 次」结论必须先按指令边界与上下文分类**，'
 '本轮 N=2/5 的真消息点为 1/1。'
 '【onlysec 引用面口径 · R213 复算】34 个 onlysec TD 的 BCA 引用次数（按 BCD 记录计，与按不同 CHD 计**完全相同**，'
 '因 954 个 CHD 的 pBCA **两两不同、无共享**，954/954）明细：IUnknown 290(189 CHD) / IPersist 90 / IPersistStream 90 / '
 'IClassFactory 78 / IRTTITypeInfo 78 / ILocomotion 12 / IGameMap 9 / StageClass 9 / FlasherClass 6 / IPiggyback 6 / '
 'CComObjectRootEx 5 / CComObjectRootBase 5 / IWOLBrowserEvent 1 / IDiskSwap... 等 20 条恰为 1 次，'
 '**「恰被 1 条 BCD 引用」= 20 条**（不是 32 条；R213 曾据子代理报数误写 32，主会话复算推翻）。'
 '【自错 4 组 · R213，0 条进结论】①调度卡与 x0.py 把 vftable 起点写成 **COL+4**（实测应为「前驱位点+4」，COL+4 起 .text 槽数 0/1214），'
 'EX1 子代理当场指出；②xa.py T2-6 断言「恰 1 次引用 = 32 条」直接采信子代理报数而未先复算，实测 20 条；'
 '③xa.py T5-8 断言「槽型模板 6 种」，实测 7 种；④xa.py T6 反汇编窗口仅取 40 条导致第二分支被截断，误报 T6-4/T6-8 两 FAIL，'
 '扩窗到 64 条后 PASS；⑤d1_recheck.py 首版把审计员的 32 与「BCA 共享」当断言写死（D2/D4），复算后改为反证其两条附注错。')

ADD01=('【R213 RTTI 三角闭环重钉】以字节直接重算 MSVC RTTI 三结构：**COL 1214 条**（+0 sig 恒 0 / +4 mdisp / +8==0 / '
 '+12 pTD 全落 .data / +16 pCHD 全落 .rdata，1214/1214 全合式）、**CHD 954 个**（每类恰 1 条 mdisp==0 主记录，'
 '另有 260 条次记录 ⇒ 954+260=1214）、**TypeDescriptor 988 个**（.?AV 962 + .?AU 26）、'
 '**vftable 1214 张**（定位 = .rdata 中 word==COL 地址且下一 word ∈ .text 的位点 **+4**）。'
 '**双射闭环**：1214 条 COL ↔ 1214 个前驱位点 ↔ 1214 张 vftable，一一对应无一对多、起点两两不重复；'
 'TD+8 内联名 == COL 名 1214/1214。此三条取代 F01 正文的旧数「1201 条 COL 全被指回 / 总 COL 1211 / 954 主 COL」'
 '（旧数在现盘不可复现；本轮实测为 **1214 / 1214 / 954**，且 pTD 命中率 1214/1214 而非 1201）。'
 '同时订正口径：**vftable ≠ COL+4**（COL 是 .rdata 里 20 字节记录，其 +4 是 mdisp，不是 vtable 入口）。')

idx29=[i for i,l in enumerate(lines) if l.startswith('F29\t')]
idx01=[i for i,l in enumerate(lines) if l.startswith('F01\t')]
assert len(idx29)==1 and len(idx01)==1,(idx29,idx01)
i29=idx29[0]; i01=idx01[0]
for i,add in ((i29,ADD29),(i01,ADD01)):
    cols=lines[i].split('\t'); assert len(cols)==5,(i,len(cols))
    cols[4]=cols[4]+add
    lines[i]='\t'.join(cols)
nb='\n'.join(lines).encode('utf-8')
nlines=nb.decode('utf-8').split('\n')
assert len(nlines)==len(ORIG)
diff=[j for j in range(len(ORIG)) if ORIG[j]!=nlines[j]]
assert sorted(diff)==sorted([i01,i29]),diff
print('仅第 %d(F01) 与 %d(F29) 行变化；其余 %d 行逐字节不变'%(i01,i29,len(ORIG)-2))
os.makedirs(NEWDIR,exist_ok=True)
out=NEWDIR+'/FACT_INDEX.tsv'
assert not os.path.exists(out),'V596 已存在'
open(out,'wb').write(nb)
assert open(out,'rb').read()==nb
NSHA=hashlib.sha256(nb).hexdigest(); NB=len(nb)
print('V596 sha %s bytes %d (+%d)'%(NSHA,NB,NB-OLD_B))
open(ROOT+'/_r213/p1_out.txt','w').write('%s %d %s %d\n'%(OLD_SHA,OLD_B,NSHA,NB))
