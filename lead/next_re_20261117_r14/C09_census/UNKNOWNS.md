# C09 · UNKNOWNS（未证项与待 P1 细化）

## 1. 440 个零证据函数（source=none → S22 兜底）
- 判据：`EVIDENCE/classification_trace.tsv` 中 `source==none`，无任何 self_known / vtable / module / string / 已知名邻居 / 导入 API 信号。
- 分布：集中于 0x75–0x77 段尾（VoxClass/Wave/Weapon 之后至 0x7734F9）的未具名 wrapper 与小型 helper；另有 0x71–0x72 段若干 WDT 相关未映射小函数。
- 现状：一律 S22 / low / `[未证]`；**不是断言它们无用**，只是本卡自动证据无法归类。建议 P1 用 YRpp/kb 二次细化或函数体语义人工判读。
- 分级诚实：未把这些函数虚高到具体 Sxx high；与 C05/C06/C08 同口径。

## 2. 79 个 jmp8 空洞目标（疑函数内短跳 / 未建模代码块）
- `atlas_gaps.tsv` 中 chan=jmp8 共 79 行；多数「引用站点在洞内」（sites_in_fn=0），首指令为 mov/cmp/add/test 等。
- 判据（R14-R1 严格）：无一满足 16 对齐 + prev∈{nop,ret,jmp} + 非分支标签，故**全部不计入疑似真入口**。
- 2 例特殊：`0x71F2C5`（boundary unknown，no-prior-entry，保留 None 不当 False）；`0x71F613`（落 `jno 0x71F614` 指令内部，bd=False，双通道自证非边界）。二者均 jmp8，不影响真入口计数。
- 待 P1：若这些洞是真实未建模代码块（非分支标签），需逐个人工确认序言与调用链，届时可能上调；本卡据实不计。

## 3. 8 个 jmp32 空洞目标（全部不计入疑似真入口）
- 全部 align16=0、prev=other（前驱为非 nop/ret/jmp 的普通指令），按 R14-R1 严格判据一概不计。
- 其中 3 个首指令为 `test`/`cmp` + jcc，是典型函数内循环/条件分支标签：`0x748F97`（cmp+jne）、`0x74DD43`（test+jle）、`0x74DD4B`（test+je）。
- 另 5 个首指令为 mov（`0x733129`/`0x733FAE`/`0x748705`/`0x748AAA`/`0x748F87`），虽非分支标签，但不对齐且前驱非 nop-ret-jmp，判为洞内非入口代码块，不计。
- 4 个地址（0x748705/0x748AAA/0x748F97/0x74DD4B）同时被 jmp32+jmp8 命中（104 行 = 100 独立地址的原因）。
- 与 Lead 数据点一致（C04 19 个 jmp32 仅 2 真、C03 0 真、C06 72/78 被质疑过宽）：本卡对 jmp32 采取最保守口径，**0 计入**，不放宽判据凑数。

## 4. 17 个 call32 疑似真入口（已计入，建议 P1 补 atlas）
- 全部 16 字节对齐 + 前驱 nop 填充 + 首指令为函数序言（push/sub esp/mov），是 R14-R1 最硬入口证据。
- 集中分布在 0x72–0x76 的 atlas 函数尺寸低估空洞：多为前一函数 entry+size 之后 2–15 字节（如 0x769C20 前驱 0x769C00+0x1E、0x769D70 前驱 0x769D60+0xE），少数为更大间隙（0x733E10 间隙 333、0x751EA0 间隙 631）。
- 完整清单见 `EVIDENCE/gap_channels.tsv`（entry_like=1 的 call32 行）与 `work/gap_stats.json` suspect_list。
- 待 P1：为这些地址补 atlas 函数条目并重算 owner()；本卡仅报「疑似真入口」，不改 atlas。

## 5. WorldDominationTour(WDT) 类族归属存在歧义
- 本片 0x71–0x72 段有 113 个函数带 `WorldDominationTour`/`WDT` 虚表类，是自定义「世界征服巡回赛」模式（GameOption/Selection/Territory/Conflict/History/Campaign/State/Map + WDTSel/WDTGameOptions/WDTProps/WDTTerr.cpp）。
- 本卡拆分：`*GameOption*` + ToolTip/TextButton/TextLabel + `Anim_Voices` → S09（UI/游戏选项，high）；`Campaign/History/State/Territory/Conflict/Map/Selection/Centroid/WDTState/WDTTerritory` → S21（战役/得分/剧情，high）。
- `[未证]`：该模式是独立战役流程（S21）还是多人游戏选项（S18/S09）的边界尚需人工确认；本卡按 .cpp 名字面与类语义给候选，未写新 [已证] 结论。见 DISAGREE。

## 6. 多类并列虚表「most_common 取首个」局限
- 与 C05/C06 同类：若一个函数同时是多个类的虚表槽，分类取 `Counter(subs).most_common(1)` 首个，可能把 S14/S06 等少数类归到多数类。
- 本片受影响子系统：S14 仅 14 且 high=0（Radio/House 类槽多与其它类并列被分流）、S04 18 全 low（INI 线索经 relay_vote）。这是归因分散，不是全局不存在。
- 未在本卡修正（沿用前片统一口径），建议 P1 在类布局卡中按单类精确重判。

## 7. 通用容器实例类型不做 core 判断（避免虚高）
- 222 个 S22 函数是 `T_VectorClass`/`T_DynamicVectorClass`/`T_VectorCursor`/`T_rc_ptr` 等泛型容器（含 `T_VectorClass_PAVUnitClass__` 等实例）。
- 类名嵌入的 T（如 UnitClass/TemporalClass）只是模板参数，容器方法本身不属于 T 的子系统；本卡按 C08 纪律先于 core 规则识别为 S22 core=False，不计 high。见 DISAGREE。
