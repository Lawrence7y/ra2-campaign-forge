# M27 · 修 3 行的语义栏（`[已证]` 但语义仍写「缺具名语义」，自相矛盾）

写域（绝对路径，唯一）：`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\` + 本卡目录 `D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\M27\`。**其他位置一律只读**。
⚠️ **严禁建 venv / pip install**。**coverage.tsv 表头逗号、数据行 TAB**（8 列）。**改前备份**到 `D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\_hygiene\coverage.M27.bak`。

## 问题
`M26` 并入了 3 行，但**只改了 grade**，语义栏仍留着旧文「`[静态推断] 占位名(slot/vslot/sub),缺具名语义`」：
| entry | name（保持不动）| grade（保持不动）| 现语义（**要替换**）|
|---|---|---|---|
| `0040F870` | `?$DynamicVectorClass::PAVWar::vslot4` | `[已证]` | `[静态推断] 占位名(slot/vslot/sub),缺具名语义` |
| `0054E890` | `T_DynamicVectorClass_PAUKamikazeControl__::slot3` | `[已证]` | 同上 |
| `0054EA70` | `T_DynamicVectorClass_PAUKamikazeControl__::slot2` | `[已证]` | 同上 |

## 任务：只改这 3 行的 `one_line_semantics`（第 4 列）
**新语义必须逐字取自 `D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13_K12\coverage_delta.tsv` 对应行的第 4 列**（该列已含完整的体内合同描述与指令偏移）。
若 delta 的语义栏与审计 `S13_K12\_audit\VERDICT.md` §2 的 ③ 结论**不一致**，**以 VERDICT 为准**，并在 MERGE_LOG 注明差异。
⚠️ 审计 §2 给的 ③ 证据（供你核对，勿自行改写）：
- `0040F870` = `FindItemIndex`：`+0x00 8B5110` / `+0x13 3931` / `+0x1F 83C8FF` / `+0x23 C20400`
- `0054E890` = `Clear`：`+0x09 895E10` / `+0x16 E8…` / `+0x24 895E08` / `+0x29 C3`
- `0054EA70` = `SetCapacity`：`+0x22 E8…` / `+0x54 8B5482FC` / `+0xA4 C20800`

## 硬要求
1. **只改第 4 列**，只这 3 行；`name` / `grade` / `subsystem` / 其余列一律不动。
2. 新语义**不得**再出现「缺具名语义」「占位名」「[静态推断]」等字样（那正是要消除的矛盾）。
3. 合并后行数仍 **18,431**；grade 直方图**不变**（`[已证]` 1,452 / `[静态推断]` 5,948 / `[未证]` 11,031）。
4. 记 `D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\M27\MERGE_LOG.tsv`：3 行 `entry / old_semantics / new_semantics / source`。

## 交付
`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\M27\PROGRESS.md`：3 行新旧语义对照 + grade 直方图前后（应完全相等）+ coverage 前后 SHA。
完成后只回复：修改行数 + grade 直方图前后（应相等）+ coverage 前后 SHA。