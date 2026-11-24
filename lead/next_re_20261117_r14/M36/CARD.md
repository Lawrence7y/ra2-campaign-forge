# M36 · 并入 `SEMFIX-6` 的 **6 行**语义栏（**grade/name 一律不变**）

写域（绝对路径，唯一）：`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\` + `D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\M36\`。**其他位置一律只读**。
⚠️ **严禁建 venv / pip install**。**coverage.tsv 表头逗号、数据行 TAB**。**改前备份**到 `D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\_hygiene\coverage.M36.bak`。

## 输入：`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\SEMFIX_6\coverage_delta.tsv`（6 行，8 列）
| entry | 新语义长度 |
|---|---|
| `0040F0A0` | 220 |
| `0040F150` | 232 |
| `00417FE0` | 198 |
| `0041A5C0` | 245 |
| `0041FB10` | 298 |
| `0044ACF0` | 236 |

（这 6 行是 `SEMFIX-REST` 漏掉的 —— 它的语义栏原本是 43~48 字符模板语 `[静态推断] … member (rtti-vftable)`。）

## 硬要求
1. **只改第 4 列（one_line_semantics）**。`grade` 必须仍 `[已证]`；`name` 必须与盘上**逐字相同**；其余列不动。
2. 合并后行数 **18,431**；**grade 直方图完全不变**（1,366 / 6,041 / 11,024）。
3. 记 `D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\M36\MERGE_LOG.tsv`：6 行新旧语义对照。

## 预期（自行核对）
- 直方图不变；`conflict=1` 254 不变
- **「`[已证]` 且语义栏含『未定/弱信号/线索/槽语义未证/rtti-vftable』」的行数应保持 10 或更少**（当前 10，全是 S22）
  ⚠️ 注意：我上一条用的正则**含 `rtti-vftable`**，比 M35 卡面用的宽 —— 请**两个口径都测**并报出来：
  - 口径 A（M35 用的）：`未定|弱信号|线索|槽语义未证` ⇒ 应 = **10**
  - 口径 B（更宽，含 `rtti-vftable`）：请实测（这 6 行若改对了，B 口径应从 16 降到 10）

## 交付
`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\M36\PROGRESS.md`：6 行改动 / 直方图前后（应相等）/ **口径 A 与口径 B 的实测值** / coverage 前后 SHA。
完成后只回复：修改行数 / 直方图前后 / 口径A 与 口径B 前后值 / coverage 前后 SHA。