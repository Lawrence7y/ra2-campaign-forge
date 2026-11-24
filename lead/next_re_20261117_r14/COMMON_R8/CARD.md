# COMMON-R8 · `R14_COMMON.md` 事实底座刷新（本段 7 的新增事实 + 新错源）

## 铁规（先做这条）
**改 `D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R14_COMMON.md` 之前必须先备份**到 `D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\_hygiene\R14_COMMON.COMMON-R8.bak`（否则审计无法逐行 diff）。
写域（绝对路径，唯一）：`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R14_COMMON.md`、`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\_hygiene\`、本卡目录 `D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COMMON_R8\`。**其他位置一律只读**。
**严禁建 venv / pip install。**

## 任务：把下列已发生的事实并入底座，**每条必须带来源路径**，不得新增来源之外的结论
（现 `R14_COMMON.md` 92,609 B，结构：§1 作废索引 / §6 纪律 19 条 / §7 环境 / §8 错源 18 类 + 技术 8 项 / §9 三分母与现态 / §10 冲突台账）

### A · 新增错源候选（编号接 §8，从 ⑲ 起）
1. **⑲ capstone `op.index` 陷阱**：capstone 5.0.7 对**无 index 的 mem 操作数返回 `0` 而非 `None``** ⇒ `op.index is None` **恒假** ⇒ 所有 `call [reg+disp]` 被静默跳过。
   实证代价：`S13_K7` 因此得出「11 行 exact 命中 **0**」的**假否定**，整卡报废。
   判据/自检：凡按「操作数是否 None」筛 call 的脚本，必须先打一条已知阳性的 call 做自检。
   来源：`S13_K9\_audit\VERDICT.md` §4。
2. **⑳ 族级判据的判别力必须按「族内随机」算，不能按「随机地址」算**：`S13_K10` 的容器合同判据在随机地址上 **1.53%~2.02%**（看似很强），
   但在**同族槽**上 **1,843/1,975 = 93.3%** 直接满足 ⇒ **族内零区分力**。
   判据：任何「按 slot/合同批量给一族函数定名」的卡，基线必须是「同族随机挑 N 个会不会也过」。
   来源：`S13_K10\_audit\VERDICT.md` §4。
3. **㉑ 「合取判据自洽」可能是循环论证**：若两个判据由同一张序表推出（合同形态由槽定义、槽又由合同判定），则「两者一致」是**恒等式**不是核对。
   必须找**可分离的第三方事实**（本轮有效的是：跨类误挂 **0/1,975**）。
   来源：同上 §4。
4. **㉒ 模板前缀不是类名**：RTTI 里的 `PAU`/`PAV` 是「指向 struct/class」，**不是类名的一部分**。
   `S13_K10` 造出 `UDamageGroup`（正确为 `DamageGroup`），被判全库无据。
   来源：`S13_K10\_audit\VERDICT.md` §3。

### B · 对既有条款的正面精化（写在该条旁边，标注【精化】）
1. **⑰ 正面精化（虚函数）**：虚函数的环③（体内合同）与环④（体外 vt 引用）**物理同源**，有效环数最多 3；
   合法的替代证据链是「**二进制给 (RTTI 类, vtable 槽号)** × **源码给该方法在该类 vtable 的声明序**」——两通道**各给对方给不出的信息**。
   ⚠️ 该链条能否单独支撑 `[已证]` **尚待 D-39 裁决**，标注「待裁」。
   来源：`S13_K8\_audit\VERDICT.md` §五、`S13_K10\_audit\VERDICT.md` §5。
2. **⑯ 实例增补**：同一地址同处 **DV 表与 V 表同一槽**，且 `VectorClass` 内 `GetItem`/`GetItemIndex` 为 `final`（DV 不覆盖）
   ⇒ 应归**基类** `VectorClass<X*>`。来源：`S13_K10\_audit\VERDICT.md` §3。

### C · 容器族 slot→method 映射表（新事实，独立小节）
slot1=`operator==`、slot2=`SetCapacity`(ret 8)、slot3=`Clear`(`call 0x7C8B3D` free + 写 {4,8,0xD}；**DV 版另写 +0x10**)、
slot4=`FindItemIndex`(回跳 + `or eax,-1` + ret 4)、slot5=`GetItemIndex`(`[ecx+0xC]` 守卫 + `(arg-Items)>>2`)、slot6=`GetItem`(`8B 41 04 / 8B 4C 24 04 / 8B 04 88 / C2 04 00`)。
旁证：395 张 7 槽族表 × 槽 1/3/4/5/6 = **1,975 槽，跨类误挂 0 例**；exact 派发锚 `0x4386AB`/`0x43942B`（slot4 返索引、−1=未命中）、`0x43864A`（slot2 返 bool）。
来源：`S13_K10\_audit\VERDICT.md` §2、`S13_K9\_audit\VERDICT.md` §3。

### D · 环境/流程事实更新（§7 与 §9）
1. **`coverage.tsv` 格式陷阱**：**表头行用逗号、数据行用 TAB**（8 列）。按逗号切会毁表。来源：本段 Lead 实测。
2. **派卡纪律增补**：**派卡时引用的盘面数字必须当场重读**，不得沿用上一张卡的世界。
   本段实证 2 次错：Lead 在 M23 卡面写 `[静态推断]` 预期 6,024（**漏减 K9 的 11 行**，真值 6,013）；在 `S16_N2` 卡面写 S16 named 73（**那是 S16_N1 并入前截面**，现为 81）。
   来源：`M23\PROGRESS.md`、`S16_N2\PROGRESS.md`。
3. **现态（2026-11-18 13:5x 实测）**：coverage **18,431 行**；`[已证]` **1,387** / `[静态推断]` **6,013** / `[未证]` **11,031**（和自洽）；`conflict=1` **254**；atlas **12,916**。
   台账 **3,370,848 B / 35,216 行 / 最大 §1006**（`_hygiene\H25_baseline.json` 存有 3,348,343 B 时点的前缀哈希 `77D8DCB1…58EE4D8`，可用于「只增不减」校验）。
   **达标子系统 3 个**：S15（144/158 + 101/158）、**S16（81/90 + 46/90，本轮新增）**、S17（94/102 + 54/102）。
   S13：named 216/240 = 90.00%（**零余量**）、proved 86（门槛 120）。

### E · §1 作废索引增补（逐条带来源）
1. `S13_K7` 的「`exact11_entries_with_hit=0`」**作废**（成因见 ⑲）。来源：`S13_K9\_audit\VERDICT.md` §4。
2. `S13_K8` 将 `00773030` 降为 `[未证]` 的提议**被拒**：它是 ABSTRACTTYPE_ARRAY **类静态成员**，「非虚表槽」是应有形态非反证；降级会丢 1 proved + 1 named 使 S13 named → 215 = 89.58% 跌破门槛。来源：`S13_K8\_audit\VERDICT.md` §二。
3. `S16_N1` 的「8 行 grade 与盘上一致、未动 grade」**失实**（其中 5 行原为 `[未证]`）。来源：`S16_N1\_audit\VERDICT.md` §1。
4. `S16_N1` 的 DISAGREE D3（「SuperClass.h 里 Ion:: 与 LightningStorm:: 混用」）**为假**：该文件全文不含 "Ion"，`class Ion` 是空类。同源。

## 交付
1. `D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R14_COMMON.md`（**先备份再改**；保留原结构，新增内容按上面 A–E 归类；每条带来源路径）。
2. `D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COMMON_R8\PROGRESS.md`（≤40 行）：**逐条列出你加了哪些条目、加在哪个 §、来源路径**；并给「改前/改后字节数 + 行数」。
3. 若发现上述任何一条**与盘上事实不符**，**不要改，写进 PROGRESS 的「拒绝并入」段并说明**（纪律 ⑨）。

完成后只回复：R14_COMMON 改前/改后字节数 + 并入条数 + 拒绝并入条数。