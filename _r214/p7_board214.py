# -*- coding: utf-8 -*-
"""R214 p7：STATUS_BOARD 追加第 214 轮（全 LF，CR=0，总行数 <= 300）。"""
import os
ROOT='/home/t628/projects/ra2-campaign-forge'
F=ROOT+'/lead/next_re_20261117_r14/STATUS_BOARD.md'; BASE='/home/t628/projects/ra2-campaign-forge/lead/R17_LEAD_BASELINE'
raw=open(F,'rb').read()
print('before: lines=%d bytes=%d CR=%d'%(raw.count(b'\n'),len(raw),raw.count(b'\r')))
assert raw.count(b'\r')==0
assert raw.count(b'\n')<260,raw.count(b'\n')
assert b'R17 \xe7\xac\xac 214 \xe8\xbd\xae' not in raw
bak=BASE+'/R214_BOARD214_20261128.bak'
fd=os.open(bak,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o644); os.write(fd,raw); os.close(fd)
assert open(bak,'rb').read()==raw
REC = """## 🟢 R17 第 214 轮（2026-11-28）· 虚槽 +0x48 转发面全表（137 视图 / 27 落点 / 两桩 19 处直接调用、0/14044 虚槽值）；律 X 升一般式 imm == mdisp_self − mdisp_target（305/305 无反例）；订正 R213「两目标在主视图」为 mdisp=36 次视图 idx3/idx4；槽面 6692 目标 + 单值索引分母塌缩；V597

**取得（1 新面 + 1 律升级 + 1 订正 + 3 组普查）.** ①🔴 **虚槽 +0x48（slot18）转发面全表**：R213 QV7 只解到 `jmp dword [eax+0x48]` 一句，本轮落到全表 —— 槽数 > 18 的视图 **137** 张（主 **125** / 次 **12**），slot18 落点 **distinct 27**、**全落 .text**（virt-only 0 / other 0），top3 **`0x4104c0` ×56** / **`0x5f65a0` ×19** / **`0x4e1960` ×17**。三类对照：MouseClass 主视图（`0x7e1964`，55 槽，slot0 `0x4f4240`）slot18 = **`0x5bda80`**；TabClass（`0x7edfb4`，55 槽）与 ScrollClass（`0x7f1094`，55 槽）slot18 **均 `0x4c9150`**（`xor eax,eax ; ret` 纯桩）⇒ **三类共享同一张 21784 视图（slot0 同 `0x6d1770`）并不蕴含 +0x48 同落点**，Mouse 与 Tab/Scroll 分叉、Tab 与 Scroll 相同。两转发桩 **`0x723ea0` / `0x723eb0`** 在 .text 内 **e8 直接调用 19 处**（**10 / 9**，capstone 逐条确认**全为 call、无 jmp**、decode 失败 0），且**两地址不作为任何 vftable 槽值（0/14044）** ⇒ 只能被直接调用，非虚槽实现、非虚表条目。②🔴 **律 X 升为一般式**：`imm == mdisp_self − mdisp_target`（target 所属视图的 mdisp）在全体 **305/305** 个 adjustor 上**全部成立、反例 0**；R213 的简化式「imm == 本视图 mdisp」的 **303/305** 保留为特例口径。两条原「例外」= `?AVHouseClass@@` mdisp=**40** 次视图（`0x7ea80c`，9 槽）idx3/idx4，字节 `83 6c 24 04 04 e9 ..`（`sub dword ptr [esp+4], 4` + `jmp 0x4f6e60` / `jmp 0x4f6950`），jmp 目标 **owner 唯一** = 同类 **mdisp=36 次视图（`0x7ea834`）idx3 / idx4**，**不在 mdisp=0 主视图（`0x7ea8a0`，24 槽）内**，`imm = 40 − 36 = 4` 严格成立。③🔴 **订正 R213**：QV4③ 与看板第 213 轮「**303/305** 目标落在本类**主视图**槽内」表述错误 —— 实为「落本类**任一视图**槽内（多继承 forwarding）」，其中那 2 条落 **mdisp=36 次视图**。HouseClass 共 **7** 张视图（起点/COL/mdisp/槽数）：`0x7ea7f4`(`0x8028a0`,44,5) / `0x7ea80c`(`0x8028b8`,40,9) / `0x7ea834`(`0x8028d0`,36,15) / `0x7ea874`(`0x8028e8`,12,1) / `0x7ea87c`(`0x802900`,8,1) / `0x7ea884`(`0x802918`,4,6) / `0x7ea8a0`(`0x802a28`,0,24)。④🟡 **adjustor 指令级模板 = 2 种**（按首指令字节长度）：`sub [esp+4],imm`(5B)+`jmp rel32`(5B) **×302**、`sub [esp+4],imm`(8B)+`jmp rel32`(5B) **×3**；后者 3 条**全属** `?AVAircraftClass@@` mdisp=**1728**（`imm=0x6c0` 需 4 字节立即数），槽位 `0x7e2250/54/58`。纯助记符 distinct = **1**。R213 的「槽型模板 7 种」是**逐视图 A/F 布尔串**口径，与指令级模板**不可互换**。⑤🟡 **槽面普查**：1214 视图 / **14044** 槽（主 12726 / 次 1318）/ distinct 槽目标 **6692**；主视图 distinct **6345** / 次视图 **348** / **交集仅 1** = **`0x4c9150`** ⇒ 仅主独有 6344、仅次独有 347。⑥🟡 **单值索引分母塌缩**：主视图按槽号聚合，**91 / 344** 个槽号单值，但分母 1 者 **1**、2–4 者 **8**、5–9 者 **69**、10–99 者 **13**、**≥100 者 0**；唯一分母 954 的槽号是 **idx0**，而 idx0 distinct **863**（非单值）⇒ 「单值索引 91」**不可**当作虚槽语义稳定的证据。⑦🟡 **mdisp 元组仅 6 种**：`(4,8,12)×76` / `(4,)×7` / `(4,24)×6` / `(21784,)×3` / `(4,8,12,36,40,44)×1`（House）/ `(4,8,12,1728)×1`（Aircraft），合计 **94** 自洽。

**口径恒真声明（审计 #553 指出，经主会话复算成立）.** 「槽值 100% 落 .text（14044/14044）」与「按 COL+4 取 .text 指针 = 0/1214」二者皆为**定义恒真**（视图槽的定义就是连续落 .text 的 dword；COL+4 就是 mdisp 字段），**不构成独立证据**。去掉 .text 过滤、仅用「下一视图起点」截断时同一批视图切出 **29580** 槽（视图上限 **4096** 口径）或 **49766** 槽（**无上限**口径，差额全在末视图 `0x7fa498` → `.rdata` 上界 `0x812000` 的 97128 B = 24282 dword）⇒ 该数**必须与停止口径同时引用**；`_r214/a4_variants.py` 枚举 6 变体定位（49766 / 29580 / 15314 / 15043）。

**跨家族（§2.12 规则 D 全复算）.** #551（hy4 `exec`）**21** 回合 / **2.90'** vs 10、无 OVERTIME、25 断言 0 FAIL；#552（hy4 `exec`）**15** 回合 / **2.85'** vs 10、无 OVERTIME、30 断言 0 FAIL；#553（deepseek `audit` 只读）**16** 回合 / **3.70'** vs 7、无 OVERTIME。审计 5 条订正**全部经主会话复算成立**：①B5 判据失效（`d18 == d19 = 27`）；②律 X 一般式 **305/305**；③A1/A5 为定义恒真；④8B `sub` 3 条全属 AircraftClass 1728；⑤单值索引分母 ≥100 者 0。另审计指出我方 B5 卡面「slot17/18/19 三者不等」表述与实测不符（实为 `d17/d18/d19 = 28/27/27`），已改为交集判据（slot18 ∩ slot19 = 1）。主会话独立复算源（重写表重建，不复用子代理代码）：`_r214/a1_recheck.py` **31 断言 0 FAIL**、`a3_audit_claims.py` **13 断言 0 FAIL**、`a5_final_nums.py` **14 断言 0 FAIL**。

**自错 6 组（0 条进结论）.** ①「vftable 前缀一致 ⇒ 单继承父类」推导**方法无效**（实测 93 类歧义、根 861、深度 75 且 1..75 每层恰 1 个退化长链、长度层 55、最长视图 344 槽），`_r214/m1.json` 产出**全部作废**仅作反证留存；②末张视图截断上界误写为 `.text` hi_file（应为 `.rdata` 上界）⇒ 总槽 **14043**（少 1），由 `a2_diag.py` 定位后改回 **14044**；③律 X 复算首版用带首点的 `.?AV..@@` 匹配类名 ⇒ 三类查询全空、误报 **6 FAIL**，去首点后 PASS；④「slot17/18/19 distinct 三者不等」判据失效；⑤臆造阈值「主视图长度 ≥100 的类 ≥400」，实测 **21**，已改为事实性断言；⑥与审计「29580」冲突未先定位口径（我方首版 49766），经 a4 变体枚举确认为**视图上限差异**，两者皆真 —— 与 R213 自错②同型：**不同口径的数不可直接判对错**。

**落盘与门禁.** R14_COMMON **§2.222** CR 保持 **1081**（1894861→**1904851** B）；GOAL **§1272** CR 保持 **337**（5447692→**5456181** B）；LEAD_LOCK **QW** CR 保持 **137**（1483886→**1489643** B）；本段第 214 轮 CR 保持 **0**（开局 **266 行 ≥ 260** ⇒ **已归档最早 2 段共 83 行**到 BOARD_ARCHIVE，ARCH CR 保持 **2952**，保留 **184** 行后写入）。**FACT_INDEX V596→V597**：仅 F29 追加，其余 **57 行逐字节不变**（58 行 / 5 列），sha `fd18fe6a`→**`42762bfb`**、264072→**270750** B（+6678）；指针 + `facts_floors`（EXPECT_CUR / CUR_SHA256 / TOTAL_BYTES / MASTER `ea10885c`→**`09558a11`**）+ `gate_runner.LEDGER` 重钉 V597；`check_disc.py` `C16_FLOORS` 纳入 **222**（**214** pins，sha `f3b881dd`→**`0d51c0d9`**）。**三门实测全绿**：`check_disc.py` exit 0（live checks 31）、`facts_floors.py` exit 0（D0–D10 全 PASS）、`gate_runner.py` exit 0（G1/G2/G3a–G3f 全 PASS）。

**⚪ 未取得.** ①虚槽 **+0x48** 的 **27 个落点**分别属于哪些类的哪一族虚函数（本轮只给落点分布与复用度，未做函数族归属）；②`0xb0cb78`/`0xb0cc1c`/`0xb0c1c0` 三全局运行期初值与 **0x19 元素结构**全字段（**virt-only BSS ⇒ 须 win-main 动态**）；③`[ecx+0x2d]` 标志位语义归属；④`?AVINoticeSink@@` 被以 **8 / 21784** 两偏移引用的**选择规则**；⑤主视图 **9958** 个 slot≥3 槽语义归属；⑥单值索引里 69 个分母 5–9 的槽号是否真对应语义稳定虚函数（须更高分母样本）；⑦F23/F35 grade（两 tsv 不可读，**禁预估回填**）；⑧C7 三死分支、C11 十二 ID。
"""
nb=(raw.decode('utf-8')+REC).encode('utf-8')
open(F,'wb').write(nb); assert open(F,'rb').read()==nb
r=open(F,'rb').read()
print('after : lines=%d bytes=%d CR=%d'%(r.count(b'\n'),len(r),r.count(b'\r')))
assert r.count(b'\r')==0
assert r.count(b'\n')<=300,r.count(b'\n')
print('OK board %d lines <=300'%r.count(b'\n'))
