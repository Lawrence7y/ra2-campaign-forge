# W175 · DISAGREE（与台账/卡片前提的分歧）

所有引用节号来自 `lead\GOAL_THREE_TARGETS_20261018.md`；纪律来自 R13_COMMON §6 / §1。

## D1 · 卡片前提「构造器 → vftable → RTTI 类名（给 RTTI 字符串地址）」被否证

- **卡片任务 1** 假设 `[0x8871E0]` 指向的对象有 vftable 且可回溯 RTTI 类名。
- **本卡结论 [已证]**：该对象 = RulesClass，**非多态**，`[obj+0] = 0x0F` 是数据字段而非 vptr；
  - 静态：构造器 `0x665650` 对 `[esi+0]` 唯一写入 `C7 06 0F 00 00 00`（`mov [esi],0xF`），无 `.rdata` 指针写入；析构 `0x667A30` 不写 `[esi+0]`（`t1_esi0_rtti_link.txt`）。
  - 全节扫描 `.?AV*` 无任何含 `Rule` 的 RTTI 名，`.\?AVRulesClass@@` 0 命中（`t1_rtti_allsecs.txt`）。
  - 动态：台账 §909-1 真机 `[P]=0x0F`，§909-2 自己也写「不是 vptr」。
- ⇒ **RTTI 字符串地址不存在**；类名只能靠构造/析构/字段结构证明（RulesClass），不能靠 vftable。
- 依据纪律：§6-4（寄存器/字段语义回溯全部写入点）、§6-13（不凭印象）、卡正文纪律 11（候选假设需自己证伪）。

## D2 · §908-2 的 `0x6667B3` 是笔误，正确地址 `0x6677B3`

- §908-2 表格写 `mov [esi+0x1808], ebx @ 0x6667B3`。
- 本卡双通道：`t2_step1.py`（skipdata 全文本，1,394,120 指令）与 `t2_doublechannel.py`（字节模式 `89 9E 08 18 00 00`）均得 **`0x6677B3`**；`0x6667B3` 处字节为 `00 E8 87 D1 EA FF…`，不是该指令。
- 差一位十六进制数字（少一个 `7`）。

## D3 · §908-2「0x66CF70 是 RadSiteClass 的 INI 读取器 / `+0x1808` 是不同对象」错误

- §908-2 陷阱段称 `fn 0x66CF70` 因含 `RadSiteWarhead` 等串而是 `RadSiteClass` 的 INI 读取器，`+0x1808` 与 RulesClass 的是「不同类里的同偏移」。
- **本卡 [已证] 否证**：
  - `0x66CF70` 首部 `mov esi, ecx`（thiscall this），`esi` 全程为同一对象；读写字段 `+0x1804/+0x1808/+0x180C/+0x1810…` 与构造器 `0x665650` 写的是**同一连续字段块**。
  - 键 `RadApplicationDelay`（`0x83B31C`）经 `0x5276d0`（INIClass::Get_Integer）直接写入 `[esi+0x1808]`（`0x66CFDC`）；段 `[Radiation]`。
  - `Rad*` 键是**全局辐射规则**（RadLevelMax/RadLevelFactor/RadSiteWarhead…），不是 RadSiteClass 实例字段；`RadSiteClass` RTTI（`.?AVRadSiteClass@@` @ `0x839608`）属另一套对象。
- ⇒ §908-2「RulesClass+0x1808 具体键名 [未证]」**已闭合**：`RadApplicationDelay`。
- 若保留 §908-2「唯一读取方」表述，需注意 `+0x1808` 另有 2 处写、1 处 INI 读（0x66CFBC）。

## D4 · §926-5「距离阈值」措辞需限定

- §926-5 称 `[0x8871E0+0x172C]` 是「与到某中心的距离比较」的距离阈值。
- 本卡 [已证] 该字段的 INI 来源键是 **`CrateRadius`**（`[CrateRules]`）。「距离阈值」是**用途描述**，不是字段本名；同一字段可能被复用做列表过滤。引用时应写「`+0x172C`（INI: `CrateRadius`）在 0x482943 被当距离阈值比较」，避免误以为有独立的 DistanceThreshold 键。

## D5 · 关于「vftable 表地址反查类名」通用手法

- R13_COMMON §6-8 禁止用「最近 E8/E9 目标」猜构造器；本卡遵循：构造器由 `new(0x18c0)` → 唯一调用者 `0x52BAD1` → 直接 `call` 确定，非入口启发式。
- `0x7E4DD8` 等 `.rdata` 值是 RulesClass **成员子对象**（Vector/DynamicVector）的 vftable，不是 RulesClass 本体 vftable；不得据此反推 RulesClass 类名或 RTTI（本卡 `t1_vft_rtti_raw.txt` 已逐项验证 COL 链不成立）。
