# COMMON-R10 · 把 `docs/re` 不能作名字异源通道写成硬判据（Lead 卡面授权错误的封堵）

## 铁规
**改 `D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R14_COMMON.md` 前必须先备份**到 `D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\_hygiene\R14_COMMON.COMMON-R10.bak`。
写域（绝对路径，唯一）：`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R14_COMMON.md`、`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\_hygiene\`、`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COMMON_R10\`。**其他位置一律只读**。
**严禁建 venv / pip install。**

## 背景：Lead 的判据口径错，被审计拦下
`S08-K1` 的卡面把「`docs\re\` + 台账」列为**可接受的名字异源通道** —— 这与项目已有的 R14-R17（双通道不得同源）**直接冲突**。
`a-S08-K1` 审计裁定（原话）：「**卡面文字确实允许 docs+台账，故非执行员过错，但采纳须先改 R14_COMMON，不得默许。**」

### 审计的完整依据（逐条照录，勿改写）
1. docs 原文**确真**：`ARCHITECTURE_ATLAS.md:4336` = `| 0x0047EFE0 / 0x0047F250 / 0x004801F0 | Draw_Shroud / Draw_Fog / CellClass::Draw | [实证] |`；
   `fog_firststage_site_locate.md:52-53` = `Draw_Shroud 0x47EFE0（1 caller: 0x480230）` / `Draw_Fog 0x47F250（2 callers: 0x480278 / 0x480290）`。
2. 但 **`docs\re\` 只能是线索**（`KICKOFF_R14.md:78`、`R14_CARDS.md:27`）。
3. **R14-R17「双通道不得同源」**：docs/台账是**同项目读同一 exe 的自记**，名称是人工推断，**给不出二进制的独立信息**。
4. **YRpp 对 `0x47F250`/`Draw_Fog` 0 命中**；`re_atlas\evidence\symbol_map.json` **自证该地址所有 names 的 srcs 均为 `docs/re`**。
5. 先例：前卡 docs 名 `MapClass::DrawShroudFogLayer` 至今未并入（`COVERAGE\CONFLICTS.tsv:392` OPEN，盘上仍 `sub_0047EFE0`）。

## 任务：并入 3 条（第 1 条是主条）

### 主条（新小节 §8.5 或接在 §8 错源序列后，按文件现有结构决定，**先读文件确认**）
**「`docs\re\` 与台账不得作为「名字」的异源通道」**
- **规则**：给函数命名时，「第二条通道」只能是 ①`YRpp\` 的 `CALL(0x…)`/`JMP_THIS(0x…)` 地址绑定原文行，或 ②跨项目独立源。
  **`docs\re\*.md`、`re_atlas\kb\*`、台账 §x 都不能充当第二条通道**——它们是同项目读同一 exe 的自记，不满足 R14-R17。
- **后果**：只靠 docs/台账得到的名字 ⇒ **只能算一条通道** ⇒ 该名字**不得升 `[已证]`**，且**是否计入 `named` 须另行裁定**（见下条）。
- **实证**：`S08-K1` 的 `0047F250` 因此**名字回退 `sub_0047F250`**（`M29` 已按此并入：只升 grade，名字未采纳）。
- 来源：`S08_K1\_audit\VERDICT.md`；`M29\MERGE_LOG.tsv`。

### 第 2 条：`named` 百分比**必须标注口径**
- 规则：报任何 `named%` 必须写明 **L 口径**（`name` 非空且不以 `sub_` 开头）还是 **S 口径**（再排除 `Class::slotN`/占位名）。
- 实证（本段新增）：**S08 的 19 个名字全是槽/占位式** ⇒ **L 口径 19/22 达标，S 口径只有 12/22**；「恰好达标」**只在 L 口径成立**。
- 来源：`S08_K1\_audit\VERDICT.md`；R14-R14（named 双口径）。

### 第 3 条：族级判据的「结构性反例」要求
- 规则：凡「按 slot/合同批量给一族函数定名」的卡，除随机基线外**必须给结构性反例检验**（例：跨类误挂计数）。
- 实证：`S13_K10` 的合同判据随机地址上 1.53%~2.02%，但**同族槽上 1,843/1,975 = 93.3% 直接满足**（族内零区分力）；真正有鉴别力的是**跨类误挂 0/1,975**。
- 来源：`S13_K10\_audit\VERDICT.md` §2/§4。

## 另并入（§1 作废索引 +1）
- **`S08-K1` 的 `0047F250 → Draw_Fog` 命名作废**：docs-only 单通道，不满足 R14-R17；盘上保持 `sub_0047F250`（`M29` 已执行）。来源：`S08_K1\_audit\VERDICT.md`、`M29\PROGRESS.md`。

## 同时刷新现态（新 §9.0e 小节）
- `coverage.tsv`：**18,431 行**；`[已证]` **1,458** / `[静态推断]` **5,947** / `[未证]` **11,026**（和自洽）；`conflict=1` **254**；
- `CONFLICTS.tsv` **470 行**（新增 `007C978A` 子系统归属争议，OPEN）；
- **达标子系统 3 个**：S15（144/158 + 101/158）、S16（81/90 + 46/90）、S17（94/102 + 54/102）；
- 只差 proved：S13 **89**/120｜S10 **151**/263｜S20 **72**/205｜S11 29/184；S08 **3**/11（named 19/22 仅 L 口径）；
- 台账 **3,370,848 B / 35,216 行 / 最大 §1006**（本轮正在补 §1007–§1010）。

## 交付
1. `D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R14_COMMON.md`（**先备份再改**；保留原结构与旧行；每条带来源路径）。
2. `D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COMMON_R10\PROGRESS.md`（≤40 行）：逐条列出加了什么、加在哪个 §、来源；给改前/改后字节数与行数。
3. 任一条**与盘上事实不符** ⇒ 不要改，写进 PROGRESS「拒绝并入」段（纪律 ⑨）。
完成后只回复：改前/改后字节数 + 并入条数 + 拒绝并入条数。