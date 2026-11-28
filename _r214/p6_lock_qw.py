# -*- coding: utf-8 -*-
"""R214 p6：LEAD_LOCK 追加 QW 段（CR 保持 137）。"""
import os,hashlib
ROOT='/home/t628/projects/ra2-campaign-forge'
F=ROOT+'/lead/LEAD_LOCK'; BASE=ROOT+'/lead/R17_LEAD_BASELINE'
raw=open(F,'rb').read()
print('before: bytes=%d CR=%d LF=%d'%(len(raw),raw.count(b'\r'),raw.count(b'\n')))
assert raw.count(b'\r')==137,raw.count(b'\r')
assert b'## QW \xc2\xb7 R214' not in raw
bak=BASE+'/R214_LOCK_QW_20261128.bak'
fd=os.open(bak,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o644); os.write(fd,raw); os.close(fd)
assert open(bak,'rb').read()==raw
S = """
## QW · R214（2026-11-28）· 虚槽 +0x48 转发面全表（137 视图 / 27 落点 / 两桩 19 处直接调用、0/14044 虚槽值）；律 X 升一般式 imm == mdisp_self − mdisp_target（305/305）；订正 R213「两目标在主视图」；V597

**QW1. 🔴 虚槽 +0x48（slot18）全表面（R213 QV7 遗留）.** 槽数 > 18 的视图 **137** 张（主 **125** / 次 **12**）；slot18 落点 **distinct 27**、**全落 .text**（virt-only 0 / other 0）；top3 **`0x4104c0` ×56** / **`0x5f65a0` ×19** / **`0x4e1960` ×17**。三类对照：MouseClass 主视图 `0x7e1964`（55 槽，slot0 `0x4f4240`）slot18 = **`0x5bda80`**；TabClass `0x7edfb4`（55 槽）与 ScrollClass `0x7f1094`（55 槽）slot18 **均 `0x4c9150`**（纯桩）⇒ 三类共享 21784 视图（slot0 同 `0x6d1770`）**不蕴含** +0x48 同落点。

**QW2. 🔴 转发桩引用面.** `0x723ea0` / `0x723eb0` 在 .text 内 **e8 直接调用 19 处**（**10 / 9**，capstone 逐条确认**全为 call、无 jmp**、decode 失败 0）；**两地址不作任何 vftable 槽值（0/14044）** ⇒ 只能被直接调用，非虚槽实现、非虚表条目。

**QW3. 🔴 律 X 一般式定稿.** `imm == mdisp_self − mdisp_target`（target 所属视图 mdisp）在 **305/305** 全成立、**反例 0**。R213 简化式「imm == 本视图 mdisp」的 **303/305** 保留为**特例口径**。两「例外」= HouseClass mdisp=**40** 次视图（`0x7ea80c`，9 槽）idx3/idx4，字节 `83 6c 24 04 04 e9 ..`，jmp `0x4f6e60` / `0x4f6950`，owner 唯一 = 同类 **mdisp=36 次视图（`0x7ea834`）idx3/idx4**，`imm = 40 − 36 = 4`。

**QW4. 🟡 订正 QV4③ 表述错误.** R213 QV4③ 写「**303/305** 目标落在本类**主视图**槽内」，实测为「落本类**任一视图**槽内（多继承 forwarding），其中 HouseClass 那 2 条例外落 **mdisp=36 次视图**」。主会话 a5 断言 N12 复算：两目标 owner 唯一、非主视图。HouseClass 七视图（起点/COL/mdisp/槽数）：`0x7ea7f4`(`0x8028a0`,44,5) / `0x7ea80c`(`0x8028b8`,40,9) / `0x7ea834`(`0x8028d0`,36,15) / `0x7ea874`(`0x8028e8`,12,1) / `0x7ea87c`(`0x802900`,8,1) / `0x7ea884`(`0x802918`,4,6) / `0x7ea8a0`(`0x802a28`,0,24)。

**QW5. 🟡 adjustor 指令级模板 = 2 种.** `sub [esp+4],imm`(5B)+`jmp rel32`(5B) **×302**；`sub [esp+4],imm`(8B)+`jmp rel32`(5B) **×3**，3 条**全属** `?AVAircraftClass@@` mdisp=**1728**（`imm=0x6c0`），槽位 `0x7e2250/54/58`。纯助记符 distinct = **1**。R213 的「7 种」是 A/F 布尔串口径，**不可互换**。

**QW6. 🟡 槽面普查.** 1214 视图 / 14044 槽 / distinct 目标 **6692**；主 distinct **6345** / 次 **348** / **交集 1** = `0x4c9150`。**口径恒真声明（审计 #553，经复算成立）**：「槽值全落 .text」与「COL+4 取 .text = 0/1214」皆为**定义恒真**，不构成独立证据；去过滤后按截断口径分别为 **29580**（上限 4096）与 **49766**（无上限，差全在末视图 `0x7fa498`→`0x812000` 的 24282 dword）。

**QW7. 🟡 单值索引分母塌缩.** **91 / 344** 个槽号单值，但分母 1 者 **1** / 2–4 者 **8** / 5–9 者 **69** / 10–99 者 **13** / **≥100 者 0**；唯一分母 954 的 idx0 distinct **863** 非单值 ⇒ 不可作虚槽语义稳定证据。

**QW8. 🟡 mdisp 元组 6 种.** `(4,8,12)×76` / `(4,)×7` / `(4,24)×6` / `(21784,)×3` / `(4,8,12,36,40,44)×1`（House）/ `(4,8,12,1728)×1`（Aircraft），合计 **94** 自洽。

**QW9. 🟡 跨家族（§2.12 规则 D 全复算）.** #551（hy4 exec）**21** 回合 / **2.90'** vs 10，无 OVERTIME，25 断言 0 FAIL；#552（hy4 exec）**15** 回合 / **2.85'**，无 OVERTIME，30 断言 0 FAIL；#553（deepseek audit 只读）**16** 回合 / **3.70'** vs 7，无 OVERTIME，5 条订正**全成立**。主会话复算源：`_r214/a1_recheck.py` **31/0**、`a3_audit_claims.py` **13/0**、`a5_final_nums.py` **14/0**（重写表重建，不复用子代理代码）。

**QW10. 📌 自错 6 组（0 条进结论）.** ①「vftable 前缀 ⇒ 单继承父」方法无效（93 歧义 / 根 861 / 深度 75 / 长度层 55 / 最长 344 槽），产出全废；②末视图上界误用 `.text` hi_file ⇒ 14043（少 1），a2_diag 定位后改回 14044；③类名未去首点 ⇒ 三类查询全空、误报 6 FAIL；④slot17/18/19「三者不等」判据失效（d18==d19=27）；⑤臆造阈值「长度≥100 的类≥400」实测 21；⑥与审计「29580」冲突未先定位口径（我方 49766），确认为**视图上限差异**，两者皆真。

**QW11. 🟡 落盘与门禁.** R14_COMMON **§2.222** CR 保持 **1081**（1894861→**1904851** B）；GOAL **§1272** CR 保持 **337**（5447692→**5456181** B）；本段 **QW** CR 保持 **137**（1483886→本段后）；STATUS_BOARD 第 214 轮 CR 保持 **0**（开局 **266 行 ≥ 260** ⇒ **归档最早 2 段 83 行**，ARCH CR 保持 **2952**，保留 **184** 行）。**FACT_INDEX V596→V597**（仅 F29，其余 **57 行逐字节不变**），sha `fd18fe6a`→**`42762bfb`**、264072→**270750** B；指针 + `facts_floors`（MASTER `ea10885c`→**`09558a11`**）+ `gate_runner.LEDGER` 重钉；`C16_FLOORS` 纳入 **222**（**214** pins，sha `f3b881dd`→**`0d51c0d9`**）。三门实测 exit 0（check_disc / facts_floors / gate_runner）。

**QW12. ⚪ 未取得.** ①+0x48 的 **27 个落点**的函数族归属（只给分布与复用度）；②三全局运行期初值 + 0x19 元素结构（BSS，须 win-main）；③`[ecx+0x2d]` 位义；④`?AVINoticeSink@@` 8/21784 双偏移选择规则；⑤主视图 **9958** 个 slot≥3 槽语义；⑥69 个分母 5–9 的单值槽号是否真对应稳定虚函数；⑦F23/F35 grade；⑧C7 三死分支、C11 十二 ID。
"""
nb=(raw.decode('utf-8')+S).encode('utf-8')
open(F,'wb').write(nb); assert open(F,'rb').read()==nb
r=open(F,'rb').read()
print('after : bytes=%d CR=%d LF=%d'%(len(r),r.count(b'\r'),r.count(b'\n')))
assert r.count(b'\r')==137,'CR 漂移 %d'%r.count(b'\r')
open(ROOT+'/_r214/p6_out.txt','w').write('%d %d\n'%(len(raw),len(r)))
print('OK QW written, CR 保持 137')
