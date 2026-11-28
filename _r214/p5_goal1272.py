# -*- coding: utf-8 -*-
"""R214 p5：GOAL 追加 §1272（CR 保持 337）。"""
import os,hashlib
ROOT='/home/t628/projects/ra2-campaign-forge'
GF=ROOT+'/lead/GOAL_THREE_TARGETS_20261018.md'; BASE=ROOT+'/lead/R17_LEAD_BASELINE'
g=open(GF,'rb').read()
print('before: bytes=%d CR=%d LF=%d'%(len(g),g.count(b'\r'),g.count(b'\n')))
assert g.count(b'\r')==337,g.count(b'\r')
assert b'## \xc2\xa71272' not in g
bak=BASE+'/R214_GOAL1272_20261128.bak'
fd=os.open(bak,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o644); os.write(fd,g); os.close(fd)
assert open(bak,'rb').read()==g
S = """
## §1272 · R214（2026-11-28）· 虚槽 +0x48 转发面全表（137 视图 / 27 落点 / 两桩 19 处直接调用且非任何虚槽值）；律 X 升为一般式 imm == mdisp_self − mdisp_target（305/305 无反例），订正 R213「两目标在主视图」为 mdisp=36 次视图 idx3/idx4；槽面 6692 目标 + 单值索引分母塌缩；V597

**一、🔴 虚槽 +0x48（slot index 18）转发面（本轮主成果，R213 QV7 遗留项结案前半）.** R213 已解 S3(21784) 函数体尾为 `jmp dword [eax+0x48]`，本轮把这把尺落到全表 14044 槽：
槽数 > 18 的视图 **137** 张（主 **125** / 次 **12**）；其 slot18 落点 **distinct 27** 个、**全部落 .text**（virt-only **0** / other **0**）；落点 top3 = **`0x4104c0` ×56** / **`0x5f65a0` ×19** / **`0x4e1960` ×17**。
三类对照：MouseClass 主视图（起点 `0x7e1964`，55 槽，slot0 `0x4f4240`）**slot18 = `0x5bda80`**；TabClass（`0x7edfb4`，55 槽）与 ScrollClass（`0x7f1094`，55 槽）**slot18 均 = `0x4c9150`**（纯桩 `xor eax,eax ; ret`）⇒ **三类共享同一张 21784 视图（slot0 同 `0x6d1770`）并不蕴含 +0x48 同落点**；Mouse 与 Tab/Scroll 分叉、Tab 与 Scroll 相同。
两个转发桩 **`0x723ea0` / `0x723eb0`**：.text 内 **e8 直接调用位点 19 处**（`0x723ea0` **10** / `0x723eb0` **9**，capstone 逐条确认**全为 `call`、无 jmp**、decode 失败 **0**）；且**两地址不作为任何 vftable 槽值出现（0/14044）** ⇒ 只能被直接调用，不是任何类的虚槽实现，也不是虚表条目。
**判据失效更正（本轮自错）**：首版用「slot17/18/19 distinct 三者不等」判 slot18 非平凡，实测 **d17/d18/d19 = 28/27/27**（**d18 == d19**），判据**不成立**；替用判据 = slot18 ∩ slot19 = **1**（唯一 `0x4c9150`）、仅 18 独有 **26**、仅 19 独有 **26**。

**二、🔴 律 X 升为一般式（订正 R213 简化式）.** R213 律 X 原口径「adjustor 的 `imm` 恒 == **本视图 mdisp**」成立 **303/305**，2 例外 = HouseClass mdisp=40 的 idx3/idx4。本轮升为一般式：
> **律 X（一般式）**：`imm == mdisp_self − mdisp_target`（`mdisp_target` = adjustor 的 jmp 目标**所属视图**的 mdisp）。
一般式在全体 **305/305** 上**全部成立、反例 0**。两条「例外」是**简化式口径的产物**：`?AVHouseClass@@` mdisp=**40** 次视图（起点 `0x7ea80c`，9 槽）idx3/idx4 字节 `83 6c 24 04 04 e9 ..`（`sub dword ptr [esp+4], 4` + `jmp 0x4f6e60` / `jmp 0x4f6950`），两 jmp 目标 **owner 唯一** = 同一 HouseClass 的 **mdisp=36 次视图（`0x7ea834`）idx3 / idx4**，**不在 mdisp=0 主视图（`0x7ea8a0`，24 槽）内**，`imm = 40 − 36 = 4` 严格成立。
⇒ **订正 R213 §1271 第二节与看板第 213 轮「两目标均在本类主视图槽内」的表述**，实为落 mdisp=36 次视图 idx3/idx4。HouseClass 共 **7** 张视图（vftable 起点 / COL / mdisp / 槽数）：`0x7ea7f4`(`0x8028a0`, 44, 5) / `0x7ea80c`(`0x8028b8`, 40, 9) / `0x7ea834`(`0x8028d0`, 36, 15) / `0x7ea874`(`0x8028e8`, 12, 1) / `0x7ea87c`(`0x802900`, 8, 1) / `0x7ea884`(`0x802918`, 4, 6) / `0x7ea8a0`(`0x802a28`, 0, 24)。

**三、🟡 adjustor 指令级模板（新口径）.** 按「首指令字节长度」只有 **2** 种：`sub [esp+4],imm`(5B)+`jmp rel32`(5B) **×302**；`sub [esp+4],imm`(8B)+`jmp rel32`(5B) **×3** —— 后者 3 条**全部**属 `?AVAircraftClass@@` mdisp=**1728**（`imm=0x6c0` 需 4 字节立即数），槽位 `0x7e2250 / 0x7e2254 / 0x7e2258`。纯助记符序列 distinct = **1**（`sub;jmp`）。R213 的「槽型模板 7 种」是**另一把尺**（逐视图的 A/F 布尔串），两口径**不可互换**。

**四、🟡 槽面普查.** 视图 **1214**（主 954 / 次 260）、槽 **14044**（主 12726 / 次 1318）、distinct 槽目标 **6692**；主视图 distinct **6345** / 次视图 **348** / **交集仅 1** = **`0x4c9150`**（`xor eax,eax ; ret`）⇒ 仅主视图独有 6344、仅次视图独有 347。**口径声明（审计 #553 指出，成立）**：「槽值 100% 落 .text」是**定义恒真**，「COL+4 取 .text 指针 = 0/1214」亦然（COL+4 即 mdisp 字段）⇒ 二者**不构成独立证据**。去掉 .text 过滤仅用「下一视图起点」截断时，同一批视图切出 **29580** 槽（上限 4096 口径）或 **49766** 槽（无上限口径，差额全在末视图 `0x7fa498`→`.rdata` 上界 `0x812000` 的 97128 B=24282 dword）⇒ 该数**必须与停止口径同时引用**；`_r214/a4_variants.py` 已枚举 6 变体（49766 / 29580 / 15314 / 15043）。

**五、🟡 单值索引分母塌缩.** 主视图按槽号聚合，**91 / 344** 个槽号满足「该槽号所有类共用一个目标」，但分母塌缩：分母 1 者 **1**、2–4 者 **8**、5–9 者 **69**、10–99 者 **13**、**≥100 者 0**；唯一分母 954 的槽号是 **idx0**，而 idx0 distinct **863**（非单值）⇒ 「单值索引 91」**不可**当作虚槽语义稳定的证据。

**六、🟡 mdisp 元组分布.** 有非零 mdisp 记录的类 **94** 个，去重只有 **6** 种：`(4,8,12) ×76` / `(4,) ×7` / `(4,24) ×6` / `(21784,) ×3` / `(4,8,12,36,40,44) ×1`（HouseClass）/ `(4,8,12,1728) ×1`（AircraftClass），合计 94 自洽。

**七、📌 自错 6 组（0 条进结论）.** ①「vftable 前缀一致 ⇒ 单继承父类」**方法无效**：实测 93 类歧义、根 861、深度 75（1..75 每层恰 1）退化长链、长度层 55、最长视图 344 槽，产出**全部作废**（`_r214/m1.json` 仅作反证留存）；②末张视图截断上界误写为 `.text` hi_file（应为 `.rdata` 上界）⇒ 总槽 **14043**（少 1），由 `a2_diag.py` 定位后改回 **14044**；③律 X 复算首版用带首点的 `.?AV..@@` 匹配类名 ⇒ 三类查询全空、误报 **6 FAIL**，去首点后 PASS；④slot17/18/19 判据失效（见第一节）；⑤臆造阈值「主视图长度 ≥100 的类 ≥400」，实测 **21**，改为事实性断言；⑥与审计员的「29580」冲突未先定位口径（我方首版 49766），经 a4 变体枚举确认为**视图上限差异**，两者皆真 —— 与 R213 自错②同型：**不同口径的数不可直接判对错**。

**八、🟡 跨家族（§2.12 规则 D 全复算）.** #551（hy4 `exec`）**21** 回合 / **2.90'** vs 10，无 OVERTIME，25 断言 0 FAIL；#552（hy4 `exec`）**15** 回合 / **2.85'**，无 OVERTIME，30 断言 0 FAIL；#553（deepseek `audit` 只读）**16** 回合 / **3.70'** vs 7，无 OVERTIME。审计 5 条订正**全部经主会话复算成立**：①B5 判据失效（d18==d19）；②一般式 305/305；③A1/A5 定义恒真；④8B sub 全属 AircraftClass 1728；⑤单值索引分母 ≥100 者 0。主会话独立复算源（重写表重建，不复用子代理代码）：`_r214/a1_recheck.py` **31 断言 0 FAIL**、`a3_audit_claims.py` **13 断言 0 FAIL**、`a5_final_nums.py` **14 断言 0 FAIL**。

**九、🟡 落盘与门禁.** R14_COMMON **§2.222** CR 保持 **1081**（1894861→**1904851** B）；本段 **§1272** CR 保持 **337**；LEAD_LOCK **QW** CR 保持 **137**；STATUS_BOARD 第 214 轮 CR 保持 **0**（开局 **266 行 ≥ 260** ⇒ **已归档最早 2 段共 83 行**到 BOARD_ARCHIVE，CR 保持 **2952**，保留 **184** 行后写入）。**FACT_INDEX V596→V597**（仅 F29 追加，其余 **57 行逐字节不变**），sha `fd18fe6a`→**`42762bfb`**、264072→**270750** B（+6678）；指针 + `facts_floors`（MASTER `ea10885c`→**`09558a11`**）+ `gate_runner.LEDGER` 重钉 V597；`check_disc.py` `C16_FLOORS` 纳入 **222**（**214** pins，sha `f3b881dd`→**`0d51c0d9`**）。三门实测全绿：check_disc exit 0 / facts_floors exit 0 / gate_runner exit 0。

**十、⚪ 未取得.** ①虚槽 **+0x48** 的 **27 个落点**分别属于哪些类的哪一族虚函数（本轮只给落点分布与复用度，未做函数族归属）；②`0xb0cb78`/`0xb0cc1c`/`0xb0c1c0` 三全局运行期初值与 **0x19 元素结构**全字段（**virt-only BSS ⇒ 须 win-main 动态**）；③`[ecx+0x2d]` 标志位语义归属；④`?AVINoticeSink@@` 被以 **8 / 21784** 两偏移引用的**选择规则**；⑤主视图 **9958** 个 slot≥3 槽语义归属；⑥单值索引里 69 个分母 5–9 的槽号是否真对应语义稳定虚函数（须更高分母样本）；⑦F23/F35 grade（两 tsv 不可读，**禁预估回填**）；⑧C7 三死分支、C11 十二 ID。
"""
nb=(g.decode('utf-8')+S).encode('utf-8')
open(GF,'wb').write(nb); assert open(GF,'rb').read()==nb
r=open(GF,'rb').read()
print('after : bytes=%d CR=%d LF=%d'%(len(r),r.count(b'\r'),r.count(b'\n')))
assert r.count(b'\r')==337,'CR 漂移 %d'%r.count(b'\r')
open(ROOT+'/_r214/p5_out.txt','w').write('%d %d\n'%(len(g),len(r)))
print('OK §1272 written, CR 保持 337')
