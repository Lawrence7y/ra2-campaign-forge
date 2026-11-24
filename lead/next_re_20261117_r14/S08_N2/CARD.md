# S08-N2 · 给 S08 补 **1 个真名**（差 1 即 named 达标）

## 盘上现态（Lead 实测）
`S08` n=**22**、named=**19**（门槛 **20** ⇒ **差 1**）、proved=**3**（门槛 11）。
剩下 3 个 `sub_` 名字，且它们**已经是 `[已证]`**（`M29` 刚升的）：
| entry | grade | 现名 | 已知线索 |
|---|---|---|---|
| `004309D0` | `[已证]` | `sub_004309D0` | 体内 `PBEACON.SHP`/`RDRBEACN.SHP`、`Failed to load BeaconArt`/`Failed to load RadarBeaconArt`、全局 `0x89C474/0x89C478`；`direct @00687BB2`（caller `Scenario 0x686B20`）|
| `0047EFE0` | `[已证]` | `sub_0047EFE0` | 体内 `FOG.SHP`；`direct @00480230`（caller `CellClass::Draw 0x4801F0`）；**CONFLICTS:392 有 OPEN 命名争议** |
| `0047F250` | `[已证]` | `sub_0047F250` | 体内 `FOG.SHP`@`0x81CE10`、懒加载 `0x89E760`、`ret 0xC`；`direct @00480278/@00480290` |

## 唯一目标：**任意 1 条**拿到真名（named 19→20 即达标）

## 🔴 名字的合格条件（本段刚立的新规矩，必须遵守）
**两条通道，且第二条通道只能是**：
- ① `YRpp\` 里的 `CALL(0x…)` / `JMP_THIS(0x…)` **地址绑定原文行**（给文件:行号）；
- 或 ② **跨项目独立源**（如公开的 RA2/YR 源码、独立反编译项目的符号表 —— 须给可核验出处）。

### ⛔ 明确禁止当第二条通道（`R14_COMMON §8.5` 主条，本段刚立）
- **`docs\re\*.md`**、**`re_atlas\kb\*`**、**台账 §x** —— 它们是**同项目读同一 exe 的自记**，不满足 R14-R17「双通道不得同源」。
- 实证：`0047F250 → Draw_Fog` 因只有 docs 通道，**已被作废**（`M29` 只升 grade 未采纳名字）。**别再走这条路。**

### ⛔ 其他硬禁令
- 禁 `Class::sub_XXXX` 占位名；禁编名（查不到就交 0 条 + 列出已试通道，**照实交差算合格**）。
- 禁把占位名（`slotN`/`vslotN`）当"真名"计入。

## 可用的通道提示（按成功率排序）
1. **镜像内串**：`PBEACON.SHP`/`RDRBEACN.SHP`/`FOG.SHP` 是文件名串，本身不能定名；但要看**它们被传给的 API**（如 `CCFileClass` 构造 / `LoadFromFile`），以及**读写哪些成员**。
2. **`YRpp\` 全库按地址 grep**：`004309D0` `0047EFE0` `0047F250`（试 `0x4309D0`/`0x47EFE0`/`0x47F250`，含大小写变体）。上一张卡说 `004309D0` 无 YRpp 命中 —— **请自己复核一遍**（6/8 位地址、大小写）。
3. **`re_atlas\evidence\symbol_map.json`**：查这 3 个地址的 `names` 与 `srcs`，看有没有**非 docs 来源**；若 srcs 全是 `docs/re` ⇒ 按新规矩**不能用**（但要在报告里写明你查过）。

## 强制自证
- **⑱ 按 entry 地址查全库冲突**（`docs\re\` + `re_atlas\kb\` + 台账 + `COVERAGE\`）—— **只报不改名**。注意 `0047EFE0` 已有 OPEN 争议（前卡 `MapClass::DrawShroudFogLayer` vs docs `Draw_Shroud`），你给的新名若与之冲突，**必须写明**。
- **⑨ 停机核验**：盘上 S08 = 22 行 / named 19 / proved 3，自己重算。
- **⑮ 体内出现**：引用的串/全局地址必须给**指令偏移**。

## 交付（绝对路径，只写这里）
`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S08_N2\`
`PROGRESS.md`（≤40 行，**第一行写「拿到几个真名」**）/ `UNKNOWNS.md` / `EVIDENCE\` / `work\`
`coverage_delta.tsv`：8 列（**若 0 条，只交表头 —— 合格交付**）
**开工 10 分钟内先落 PROGRESS 骨架。严禁建 venv / pip install / import 其他卡 work 代码。**

## 核心数字
① 拿到真名几条（目标 ≥1）② 每条的**第二条通道是什么**（必须非 docs/台账）③ 若 0 条：已试通道清单