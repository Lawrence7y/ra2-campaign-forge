# M30 · 并入 `a-S08-N2` + `a-S21-N2` 各 **1 个真名**（**只改 name/semantics，grade 一律不动**）

写域（绝对路径，唯一）：`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\` + `D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\M30\`。**其他位置一律只读**。
⚠️ **严禁建 venv / pip install**。**coverage.tsv 表头逗号、数据行 TAB**（8 列）。**改前备份**到 `D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\_hygiene\coverage.M30.bak`。

## 两份审计均 **PASS**（各 1 行可并入）

### ① `004309D0` → **`Init_BeaconArt`**（`a-S08-N2` PASS）
- 盘上现：`S08 / sub_004309D0 / [已证]` ⇒ **grade 保持 `[已证]` 不动**，只改 name 与 semantics。
- 通道①（二进制，审计逐项核过）：`0x4309D6 push "PBEACON.SHP"`、`0x430A3A push "RDRBEACN.SHP"`、写 `[0x89C474]`@`0x4309EF`、写 `[0x89C478]`@`0x430A53`、唯一 E8 caller `0x687BB2`。
- 通道②（跨项目独立源，审计**联网拉原文逐字核实**）：`github.com/YuriPlanet/vera20k` 的 `src/render/beacon_art.rs` L1-3 明文 `Init_BeaconArt 0x004309D0`；`src/app/loading/transitions.rs` L452 `Full_Init 687BB2 -> Init_BeaconArt 4309D0`；`src/app/presentation/state.rs` L195-196。
- ⚠️ **审计要求**：`name_kind` 请写 **`cross_project_reconstructed`**（不是 `true_name_cross_project`），并在语义栏保留「跨项目独立源 VERA20K」字样。
- ⚠️ **两处证据勘误不得带进 coverage**：`0x430A2D` 实推 `0x818A40`（"Failed to load BeaconArt"）；**不要写**「caller 位于 `Scenario/Full_Init 0x686B20` 内」（未证，`0x687923` 处有 ret）。call site 地址 `0x687BB2` 本身正确，可保留。

### ② `0053AF40` → **`PsyDom::Update`**（`a-S21-N2` PASS）
- 盘上现：`S21 / sub_0053AF40 / [未证]` ⇒ **grade 保持 `[未证]` 不动**，只改 name 与 semantics。
- 通道①（YRpp 原文，审计到盘上抄行核过）：`YRpp\SuperClass.h` **L178 `class PsyDom`** → **L190 `static void Update()`** → **L191 `{ CALL(0x53AF40); }`** ⇒ **名字 `Update` 是 YRpp 原文所给，非卡方自起**。
- 二进制复核（审计逐项）：读写 `0xA9FAC0`（6 路跳表 switch，table@`0x53B064`）、写 `0xA9FA48`@`0x53B027`、读写 `0xA9FAC4`、`call 0x53B080`(Fire)@`0x53AFBA`、唯一 E8 caller `0x53A742`。
- ⚠️ **`0xA9FAC8` 不得写进语义**（审计实测本函数不碰它，那是 `Start`/`Fire` 的）。delta 行本身没错，**照 delta 的全局列表即可**。
- ⚠️ **两处勘误不得带进 coverage**：不要写「PsyDom 四条全局逐一对上」（函数边界跑过头）；不要写括注「`0x53A742` (PsyDom::Strike 区)」（YRpp 无 `PsyDom::Strike`）。

## 硬要求
1. **只改这 2 行的 `name`（第 3 列）与 `one_line_semantics`（第 4 列）**；**grade（第 5 列）一律不动**；subsystem 不动。
2. 合并后数据行仍 **18,431**；**grade 直方图必须前后完全相等**：`[已证]` **1,458** / `[静态推断]` 5,947 / `[未证]` **11,026**。
3. 记 `D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\M30\MERGE_LOG.tsv`：2 行旧名→新名、旧语义→新语义、`name_kind` 取值、来源。
4. 更新 `COVERAGE\PANEL.md`（S08、S21 段）。

## 预期（自行核对，不符先停）
- **named（L 口径）：S08 19 → 20**（达标）、**S21 90 → 91**（门槛 117，仍差 26）
- **proved 完全不变**；`conflict=1` 保持 254；行数 18,431

## 交付
`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\M30\PROGRESS.md`：2 行新旧对照 / grade 直方图前后（应相等）/ S08 与 S21 的 named 前后 / coverage 前后 SHA。
完成后只回复：修改行数 / grade 直方图前后（应相等）/ S08 named 前后 / S21 named 前后 / coverage 前后 SHA。