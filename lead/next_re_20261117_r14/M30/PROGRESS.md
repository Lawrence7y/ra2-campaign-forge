# M30 PROGRESS — 并入 a-S08-N2 + a-S21-N2 各 1 行真名（只改 name/semantics，grade 不动）

## 结论
- **修改行数：2**（coverage.tsv 第 966、4962 行；仅第 3 列 name、第 4 列 one_line_semantics 变化，其余 6 列逐字节不动）
- **grade 直方图前后（必须相等）**：
  | grade | 前 | 后 | 变化 |
  |---|---:|---:|---:|
  | `[已证]` | 1,458 | 1,458 | 0 |
  | `[静态推断]` | 5,947 | 5,947 | 0 |
  | `[未证]` | 11,026 | 11,026 | 0 |
  | 合计 | 18,431 | 18,431 | 0 |
  ⇒ 完全相等 ✓
- **S08 named 前后（L 口径，atlas 内 W130 ∩ coverage）：19 → 20**（20/22=90.91%，门槛 20 ⇒ 达标）；proved 3 不变、strict 0→1
- **S21 named 前后（L 口径，atlas 内）：90 → 91**（91/129=70.54%，门槛 117，仍差 26）；proved 26 不变、strict 26→27
- **coverage 前后 SHA-256**：
  - 前：`d8d9c08c96711b0f259bdae75e6279ef3553ebe077f72bb835e19c97dd16fa00`
  - 后：`11de45642659ba159feb7bf03d8717feebfa9008a5acd4b796cc5cb197858158`
  - 备份：`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\_hygiene\coverage.M30.bak`（改前字节一致，3,671,327 B）

## 2 行新旧对照
| entry | 子系统 | name 旧 → 新 | semantics 旧 → 新 | grade（不动） | name_kind |
|---|---|---|---|---|---|
| `004309D0` | S08 | `sub_004309D0` → `Init_BeaconArt` | `[静态推断] Shroud/Radar member (string/import)` → `Init_BeaconArt: 加载 PBEACON.SHP/RDRBEACN.SHP 到 [0x89C474]/[0x89C478] 的 Beacon 美术初始化；Scenario Full_Init 0x687BB2 调用（跨项目独立源 VERA20K 具名）` | `[已证]` → `[已证]` | `cross_project_reconstructed` |
| `0053AF40` | S21 | `sub_0053AF40` → `PsyDom::Update` | `调用图邻居 1 票指向 战役/关卡/得分/剧情（弱信号）` → `PsyDom 状态机 Update: 按 [0xA9FAC0] 状态分支, 读写 [0xA9FAC4]/[0xA9FA48] 推进心灵支配仪阶段, 含 call Fire(0x53B080); 唯一直接调用点 0x53A742` | `[未证]` → `[未证]` | `YRpp_CALL_binding+binary_corrob` |

## 证据勘误处理（不得带进 coverage）
- **004309D0**：`name_kind` 写 `cross_project_reconstructed`（非 delta 的 `true_name_cross_project`）；语义保留「跨项目独立源 VERA20K」；未写入 `0x430A2D` 实推 `0x818A40`（"Failed to load BeaconArt"）勘误；未写「caller 位于 Scenario/Full_Init 0x686B20 内」（`0x687923` 有 ret）；call site `0x687BB2` 保留（正确）。
- **0053AF40**：依审计 E2 去掉 delta 括注 ` (PsyDom::Strike 区)`（YRpp 无 `PsyDom::Strike`）；未写 `0xA9FAC8`（本函数不碰，属 Start/Fire）；未写「PsyDom 四条全局逐一对上」（函数边界跑过头）；名字 `Update` 来自 YRpp `SuperClass.h` L191 `CALL(0x53AF40)` 原文行。

## 校验
- coverage.tsv 数据行 **18,431**；表头逗号、数据行 TAB（8 列）保持；仅 2 行第 3、4 列变化，grade / subsystem / evidence_path / n_sources / conflict 全部 UNCHANGED。
- grade 直方图前后完全相等；`conflict=1` 计数 254 → 254；行数 18,431 → 18,431。
- 两行均在 atlas 内（function_atlas.tsv 命中）；备份完成且字节一致；未建 venv、未 pip install。
- PANEL.md 已更新 S08（named 19→20）、S21（named 90→91）段及 TOTAL 一致性；MERGE_LOG.tsv 已记录 2 行旧名→新名、旧语义→新语义、name_kind、来源。

## 来源
- `M30/CARD.md`（a-S08-N2 PASS、a-S21-N2 PASS；只改 name/semantics，grade 一律不动）
- `S08_N2/_audit/VERDICT.md`、`S21_N2/_audit/VERDICT.md`（独立审计 PASS + 证据勘误）
- `S08_N2/coverage_delta.tsv`、`S21_N2/coverage_delta.tsv`（输入 delta 行）
