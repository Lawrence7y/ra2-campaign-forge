# -*- coding: utf-8 -*-
"""R210 p6：STATUS_BOARD 第 210 轮（CR 保持 0，行数 <= 300）。开局 253 行 < 260 ⇒ 不归档。"""
import os
ROOT='/home/t628/projects/ra2-campaign-forge'
TIER=ROOT+'/lead/next_re_20261117_r14'; BASE=ROOT+'/lead/R17_LEAD_BASELINE'
BOARD=TIER+'/STATUS_BOARD.md'
b=open(BOARD,'rb').read()
n0=b.count(b'\n')
assert b.count(b'\r\n')==0
assert n0<=300 and n0<260, n0
bak=BASE+'/STATUS_BOARD.md.before_r210_board_20261128.bak'
fd=os.open(bak,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o644); os.write(fd,b); os.close(fd)
assert open(bak,'rb').read()==b
SEC='''## 🟢 R17 第 210 轮（2026-11-28）· 律 U 定稿：视图偏移集合 = ({4} ∪ 本类 QI 正偏移)，954/954 零失配；律 V thunk 通用式 305/305 取代「越界槽例外」；mdisp→形态交叉表；V592

**取得（2 律 + 2 表）.** ①🔴 **律 U（954/954 零失配）**：对 954 个类的主视图 slot0 函数解析「返回 this 偏移」集合 R，判据三重收紧（体内须有 `rep` 前缀比较指令 / `lea reg,[x+K]` 的 K 仅在随后 8 条内写进 `mov dword ptr [out],reg` 时计入 / 非 QI 形态类 R 强制为空）。分布：R 空 **863** ⇒ T 视图空；R={4} **83** ⇒ {4}；R={24} **6** ⇒ {4,24}；R={1728} **1** ⇒ {4,1728}；R={36,40,44} **1** ⇒ {4,36,40,44}。公式 **(R 非空) ? ({4} ∪ R) : 空集**。②🔴 **{4} 的性质**：对 83 类与 QI 自返 +4 重合（冗余），对另外 **8** 类（6 Locomotion + `AircraftClass` + `HouseClass`）是**独立附加项**。反控：全并集套 863 空类 ⇒ 成立 **0**；不先分离 QI 形态 ⇒ 1 个假阳性（`BaseClass` slot0 `0x42ee30` 的 `lea esi,[ebp+4]` 与出参无关）。③🔴 **{4} 两侧分解 90/91**：BCD 真接口名 `.?AUIRTTITypeInfo@@` 78 / `.?AUILocomotion@@` 12 / `.?AUILinkStream@@` 1；QI 返 +4 的 IID `0x7e9ae0` 77 / `0x7ed358` 12 / `0x7e9530` 1。**唯一不匹配 = HouseClass**（BCD 声明 IRTTITypeInfo@+4，QI `0x4f6830` 偏移集 `{0,36,40,44}` 无 4，而该类 +4 视图 slot0 thunk `0x510a20` 落点就是它）⇒ 成因**未取得、不外推**。④🔴 **律 V（305/305）**：`imm == mT − mV` 且 `E9 落点 == 同类 mV 视图第 k 槽`，mV 必在本类视图偏移集合内；mV `{0:303,36:2}`、槽号 `{0:101,1:101,2:101,3:1,4:1}`、(mT,mV) 七种 `(4,0)273/(24,0)18/(36,0)3/(40,0)3/(44,0)3/(1728,0)3/(40,36)2`；反控 `imm+4`=0。⇒ **HouseClass slot3/4 不是越界例外，是 (40,36) 的普通实例**，R209 §2.217 五的措辞已订正。⑤🟡 **mdisp→形态交叉表（260 全量零残留）**：`4→T91` / `8→{S2 75,I 3}` / `12→S1 78` / `24→T6` / `36,40,44,1728→T 各1` / `21784→S3 3` ⇒ **偏移决定形态**。⑥🟡 **主视图普查**：全槽 **12726**、slot≥3 **9958**、slot3 独占 **686** / 复用 **132** / 短表 **136**，slot3 ret top `ret 510, 0x10 81, 0x1c 60`。

**跨家族（§2.12 规则 D 全复算）.** #538（hy4，10 回合 / **2.25'** vs 预算 8.0，无 OVERTIME）5/5 PASS，主会话 c2 复算一致。#539（hy4，7 回合 / **0.98'**，无 OVERTIME）6/6 PASS，另给 4/24 成对 **6** 组（J05/J06/J10/J11/J12/J13）。#540（deepseek，36 回合 / **8.72' vs 8.0 ⇒ [OVERTIME] 如实记**）报 `error_max_turns`、**result 空、0 条结论采信**；其崩溃前落盘 `_r210/audit_deepseek.json` 的 G2（律 V）**305/305、imm+4=0、by_k 101/101/101/1/1、distinct_thunks 70** 与我方逐数一致，G3（普查）**12726/9958/136/818/686/132** 一致、slot3 ret top **511 vs 510** 为「无 ret」口径差（c2 复算 510）；**G1 FAIL 947 是口径错**（把 `{4}` 套全部 954 类），c20 M1 正确判据 954/954，故不采信 G1，但记其在 `0x4f4240`（9 类 slot0）上的发现——该函数经 c16 判为**非 QI 形态**（无 rep 前缀），9 类视图集 {0} 或 {0,21784}，与律 U 无冲突。

**自错 6 组（0 条进结论）.** ①`c4` 取 `disasm_lite` 元组 `ins[1]` 当 mnemonic（应 `ins[2]`）；②`lea` 偏移正则只收十六进制，capstone 对 <0x10 位移输出十进制 `4` ⇒ 漏 `0x410260` 的 `lea ecx,[ebx+4]`，先误报「HouseClass 唯一例外」并写进 V592 第一版（**已删除重建**）；③`c16` 用 `mnemonic=='repe'` 判前缀，实际是 `'repe cmpsd'` ⇒ 185 个 QI 类全判 0；④`c15` 预设「跟进委托边会失配」实测 **0**（6 条边指向的 QI 自身不返正偏移，闭包对 T 是 no-op）⇒ 该说法已从 V592 删除；⑤`c20` 反控 A/B 预期 91/10 实测 **83/83**，含义改写为「{4} 对 83 冗余、对 8 必需」；⑥`p1` 两次重建 V592（旧 `735a7b5b/249150` 已删，最终 `b3327fd4/249545`）。

**落盘与门禁.** R14_COMMON **§2.218** CR 保持 **1081**；GOAL **§1268** CR 保持 **337**；LEAD_LOCK **QS** CR 保持 **137**；本段 CR 保持 **0**（开局 **253 行 < 260**，**不归档**）。**FACT_INDEX V591→V592**：F29 stmt 7377→10553 B、lim 21688→22603 B（其余 55 行逐字节不变；57 行 / 5 列 / grade 与第 4 列全同），sha `c529a08c`→**`b3327fd4`**、245454→**249545** B；指针 + facts_floors（EXPECT_CUR/CUR_SHA256/TOTAL_BYTES/MASTER `ba31ddc1`→`519ee33a`）+ gate_runner LEDGER 同步重钉。三门 exit 0：`check_disc`（C15 末节 218、C16 210 节全钉、C19 ok(b3327fd4/249545/V592)、C20 ok）、`facts_floors`（D8 249545、D9/D10 一致、MASTER 519ee33a）、`gate_runner`（G1=G2=G3=ok）。五项 CR 不变量全绿，无孤儿进程（`pgrep -f wait_subagents` 0）。

**⚪ 未取得.** ①{4} 独立附加项对 8 类成立的成因（HouseClass 唯一反例）；②12 个 QI 目标具名 IID（仅 3 个 OLE 标准前缀形态 `0x7f7c90/0x7f7c80/0x7f7c70` 可判，其余 8 个 Westwood 私有 GUID 无外部头文件）；③主视图 9958 个 slot≥3 槽语义归属；④S3 三表（Mouse/Tab/Scroll，mdisp 21784）的 `0x11c7`/`0x11c8` 语义；⑤`attributes` 位义（须 win-main 动态）；⑥F23/F35 grade（coverage.tsv/function_atlas.tsv 仍不可读，禁预估回填）；⑦C7 三死分支、C11 十二 ID。
'''
nb=b+SEC.encode('utf-8')
assert nb.count(b'\r\n')==0
assert nb.count(b'\n')<=300, nb.count(b'\n')
tmp=BOARD+'.r210tmp'; open(tmp,'wb').write(nb); os.replace(tmp,BOARD)
assert open(BOARD,'rb').read()==nb
print('OK STATUS_BOARD %d -> %d B lines %d -> %d CR %d'%(len(b),len(nb),n0,nb.count(b'\n'),nb.count(b'\r\n')))
