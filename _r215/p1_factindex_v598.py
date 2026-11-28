# -*- coding: utf-8 -*-
"""R215 p1：FACT_INDEX V597 -> V598。把本轮 slot18 归因链 8 组实测追加到 F29；其余 57 行逐字节不变。"""
import os,hashlib
ROOT='/home/t628/projects/ra2-campaign-forge'
TIER=ROOT+'/lead/next_re_20261117_r14'
OLDV=TIER+'/R17_R131_FACTINDEX_V597/FACT_INDEX.tsv'
NEWDIR=TIER+'/R17_R131_FACTINDEX_V598'
raw=open(OLDV,'rb').read()
OLD_SHA=hashlib.sha256(raw).hexdigest(); OLD_B=len(raw)
print('V597 sha %s bytes %d'%(OLD_SHA,OLD_B))
assert OLD_SHA.startswith('42762bfb'),OLD_SHA[:8]
lines=raw.decode('utf-8').split('\n'); ORIG=list(lines)

ADD=('【虚槽 +0x48 落点归因 · R215】R214 只给 slot18 的 27 落点分布与复用度，本轮做归因：'
 '137 张有 slot18 的视图严格闭合为 **9 个多类组（覆盖 119 视图）+ 18 个单类组** = 137；'
 '9 组落点与视图数 = **0x4104c0×56 / 0x5f65a0×19 / 0x4e1960×17 / 0x4c9150×9 / 0x5d6450×8 / '
 '0x7ba8c0×3 / 0x557fd0×3 / 0x7aa6a0×2 / 0x7b1740×2**。'
 '【0x4104c0 = 基类 12 字节描述符取值器】该地址在 14044 槽里**只出现在 slot18（56/56）**，'
 '函数体 9 条指令：`8b 44 24 04`（取 [esp+4] 出参指针）+ 三次「从全局 0x887680/0x887684/0x887688 各读 1 dword '
 '写入 [eax+0]/[eax+4]/[eax+8]」+ `c2 04 00`；**三个全局均落 .data virt-only（r2o=None，BSS，运行期值须 win-main）**。'
 '其宿主基类为 `?AVAbstractClass@@` 主视图 0x7e1f50（24 槽）slot18。'
 '【配套消费者表】对全部 **931** 处 `call/jmp [reg+0x48]`（skipdata 覆盖率 100%）按「所属函数 = ≤ 该位点的最大 vftable 槽目标」'
 '归并：**677 位点归入 273 个函数**，254 位点距最近槽函数 >4096 B 判为未归并（口径声明）；'
 'slot19 默认桩 0x4104f0（73 视图）与 slot22 默认桩 0x410540（77 视图）**体内各含 1 处 `ff 50 48`**，'
 '形态 = `mov eax,[ecx]` / `sub esp,0xc` / `lea edx,[esp]` / `push` / `call [eax+0x48]` / 把返回的 3 dword 拷给出参 ⇒ '
 '**+0x48 是「返回 3 dword 描述符」的虚槽**，与 0x4104c0 的写 0/4/8 三 dword 同型（27 落点中符合该形态者 5 个）。'
 '【口径订正 · 审计 #557 指出并经主会话复算】① **「305」是双口径同值巧合**：adjustor **出现次数** 305 与 '
 '`call [eax+0x48]` **字节口径站点数** 305 数值相同但**集合交集 = 0**，两者不可互相充当论据；'
 'adjustor 的 distinct 桩地址只有 **70**（imm8 形式 `83 6c 24 04` **67** 个、IMM 分布 {4:40, 0x18:18, 0x24:3, 0x28:3, 0x2c:3}；'
 'imm32 形式 `81 6c 24 04 ...` **3** 个、IMM 全 0x6c0）。② Locomotion 组 = **11 派生 + 基类 ?AVLocomotionClass@@**，'
 '12 张 mdisp=4 的 50 槽视图逐槽同为 **[21,22]**（值 0x55ab90 / 0x55a8f0），其余 48 槽各异；'
 '主视图槽数 **11 个是 10 槽、?AVTeleportLocomotionClass@@ 是 12 槽**（故 12 组的主视图无一有 slot18）。'
 '③ 0x4104f0 函数体内 `ff 50 48` 只有 1 处（0x4104fb），用宽窗口扫会把相邻 0x410540 的 0x41054b 计入。'
 '【+0x48 特异性反控】disp8 邻值对照：0x44→133、0x47→**0**、0x48→**930**（FF /2|/4 非 SIB）、0x49→1、0x4c→124 ⇒ '
 '**0x48 的 930 是同量级邻值（133/124）的约 7–8 倍且相邻 0x47/0x49 近乎空**，非通用 disp8 噪声。'
 '【显式失效判据】slot17/18/19 的「目标只出现在本槽号」比例 96.4% / 96.3% / 96.3%，'
 '而同法在 slot0..slot6 上为 99.7–99.9% ⇒ **「只出现在本槽号」不是 slot18 特有信息**，该判据不得作为 slot18 语义证据；'
 '同理「组内 slot18 distinct == 1」在各组内均与 2–12 个其它槽号并列（0x4e1960 组并列 12 个、0x557fd0 组并列 20 个），'
 '**slot18 不是组内唯一未覆写槽**。'
 '【INoticeSink / Aircraft 收口 · 审计 #557 复算成立】`?AVINoticeSink@@` 只有 1 张视图（0x7e1fbc，mdisp=0，1 槽 0x4c9150）；'
 'mdisp==8 视图 **78** 张、mdisp==21784 视图 **3** 张（Mouse 0x7e195c / Tab 0x7edfac / Scroll 0x7f108c），'
 '**全体 70 个 adjustor 桩的 IMM 不含 8 也不含 21784**（原 R215 卡面以「305 条 adjustor」框定该结论属口径错误，已订正）。'
 '`?AVAircraftClass@@` 五视图 = 0x7e2250(1728,9) / 0x7e2278(12,1) / 0x7e2280(8,1) / 0x7e2288(4,6) / 0x7e22a4(0,**341**)；'
 'mdisp=1728 视图 slot0/1/2 值 0x41c670/0x41c680/0x41c690 为三条 **8 字节** `81 6c 24 04 c0 06 00 00 e9 ..` 桩（IMM=0x6c0），'
 'jmp 落 mdisp=0 主视图 0x7e22a4 的 slot0/1/2（0x414290/0x4142f0/0x414300），律 X `imm == mdisp_self − mdisp_target` '
 '= 1728 − 0 **3/3 成立**；0x7e2250/54/58 **不作为任何视图槽值**。'
 '【跨家族 §2.12 规则 D · R215 全复算】exec #555（hy4，24 回合 / 1.92 分 vs 10，无 OVERTIME）、'
 'exec #556（hy4，7 回合 / 2.62 分 vs 10，无 OVERTIME）、audit #557（deepseek 只读，13 回合 / 3.95 分 vs 8，无 OVERTIME）。'
 '审计 4 条订正全部经主会话复算成立（m15 8 断言 0 FAIL）：305 双口径、Locomotion 11+1、0x4104f0 单处、三全局 virt-only。'
 '主会话独立复算源：_r215/m1_recheck.py 3 断言、m9_recheck_exec2.py **11 断言 0 FAIL**、m12_claims.py **17 断言 0 FAIL**、'
 'm15_audit_fix.py **8 断言 0 FAIL**；exec 侧 ex1.json / ex2.json 均已主会话重算一致。')

idx29=[i for i,l in enumerate(lines) if l.startswith('F29\t')]
assert len(idx29)==1,idx29
i29=idx29[0]
cols=lines[i29].split('\t'); assert len(cols)==5,len(cols)
cols[4]=cols[4]+ADD
lines[i29]='\t'.join(cols)
nb='\n'.join(lines).encode('utf-8')
nlines=nb.decode('utf-8').split('\n')
assert len(nlines)==len(ORIG)
diff=[j for j in range(len(ORIG)) if ORIG[j]!=nlines[j]]
assert diff==[i29],diff
print('仅第 %d 行(F29) 变化；其余 %d 行逐字节不变'%(i29,len(ORIG)-1))
os.makedirs(NEWDIR,exist_ok=True)
out=NEWDIR+'/FACT_INDEX.tsv'
assert not os.path.exists(out),'V598 已存在'
open(out,'wb').write(nb)
assert open(out,'rb').read()==nb
NSHA=hashlib.sha256(nb).hexdigest(); NB=len(nb)
print('V598 sha %s bytes %d (+%d)'%(NSHA,NB,NB-OLD_B))
print('CR=%d lines=%d cols=%d'%(nb.count(b'\r'),len(nlines),len(nlines[0].split('\t'))))
open(ROOT+'/_r215/p1_out.txt','w').write('%s %d %s %d\n'%(OLD_SHA,OLD_B,NSHA,NB))
