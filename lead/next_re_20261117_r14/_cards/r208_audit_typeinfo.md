# R208 审计卡（只读复核，不得执行类操作）：type_info 共享 vftable 律的自洽性与反例审计

## 角色
你是只读审计员。**不要**写任何文件，**不要**跑长时间扫描，只读 + 小规模核验。
目标文件：/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe（只读）。

## 被审计的主张（主会话 R208 提出，7 条）
1. 0x7f9594 是 MSVC type_info 类的**共享 vftable 起点**，全部 988 个类型描述符（TD）的 +0 都指向它。
2. TD 布局 = {+0 vfptr, +4 _M_data(spare, 恒 0), +8 内联 mangled 名}，不是 {+0 类 ID}。
3. 0x7f9590（即 0x7f9594-4）是 .?AVtype_info@@ 的 COL 地址，符合 R207 的「vftable[-1] == COL」律。
4. 0x7f9594+4 起的字符串是 Access violation - no RTTI data!（MSVC type_info::_name 对 __non_rtti_object 路径使用的固定串）。
5. 该 vftable 只有 1 个槽（0x7c8ab7），槽目标首条指令是 push esi，形态与 MSVC type_info 虚析构（scalar deleting destructor）一致。
6. 业务 1214 条 COL 的 vftable 槽数总和 14044（R203/R207 既有结论），本轮新增：这 14044 个槽只落在 **6692** 个不同 .text 地址上，最高频目标 0x4c9150 被引用 **205** 次。
7. 因此「TD+0 语义未取得」这一条历史遗留项（连续多轮记在未取得清单）应**结案**，改记为「= type_info 共享 vftable 指针」。

## 你要做的（用 python3 + struct，单条命令自包含；禁用 capstone 以外的重工具）
A. 复算 0x7f9590 / 0x7f9594 / 0x7f9598 三处 dword 的值，以及 0x7f9594 之后字符串的原始字节。
B. 复算「.data 中值 == 0x7f9594 的 dword 个数」，并核对这些位置的地址是否都落在「某条 COL 的 pTD」或「某条 BCD 的 pTD」上（给出命中数与反例数）。
C. **反例搜索（重点）**：是否存在 TD 的 +0 不等于 0x7f9594？若有，逐条列出地址、+0 的值、该 TD 名，并说明它们是否根本不是 TD（而是同形状的巧合数据）。
D. 独立性检查：主张 3 说 0x7f9590 是 COL 地址。请独立验证 0x7f9590 处的 20 字节是否满足 COL 判据（+0∈{0,1,2} / +8==0 / +12 指向 .data 且该处 +0 是 .rdata 地址 / +16 指向 .rdata 类头），并报是否满足。
E. 主张 5 的「1 个槽」如何界定：若把 0x7f9598 之后也当作槽继续读，第 2 个「槽」的值是多少、落在哪个段？这能否被解释为「字符串字节被误读为指针」？（这是对「槽数=1」的关键反控）

## 输出格式
每条一行：「A/B/C/D/E · 断言 | 你的实测值 | PASS / CONFLICT / 需补证 | 一句话理由」。
最后给：总断言数 / FAIL 数 / 你认为哪条主张应降级或撤回（若有）。
