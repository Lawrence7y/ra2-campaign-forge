# R17-R44-FACTINDEX-V32 · REPORT

## 范围与方法
- 基底：v3.1 = `lead\next_re_20261117_r14\R17_R42_F23_FIX\FACT_INDEX.tsv`（F01–F26，26 条）。
- 修正对象：仅 `evidence_paths`（含必要的稳定锚点替换）；`statement` / `grade` / `limitations` 逐字节未改，`fact_id` 仍 F01–F26 不增不删不改号。
- 解析基准：仓库根 `D:\Project\ra2-campaign-forge`；括号内段标题/§号/M 编号/事项号只作回查提示，不参与路径拼接。
- 未修改 `R17_R42_F23_FIX` / `R17_R40_FACTINDEX_V3` / `R17_R38_FACTINDEX_FIX` / `R17_R34_FACT_INDEX` 下任何文件（目录哈希前后一致）。未执行逆向、未启动 gamemd。

## 改动统计
- **改了多少条路径**：46 条路径项被改写或新增（其中 F01–F16 的 15 条看板锚所在路径项改锚，F17–F26 的 31 条路径项统一为仓库根相对；F24 把「MED675 相关产物」拆成 `R16_MEASURE_EVID675` + `R16_AUDIT_EVID675` 两条真实目录，净增 1 条路径项）。
- **去掉了多少处裸行号**：18 处（看板 15 处：F01/F02/F03/F04/F05/F06/F07/F09/F10/F11/F12/F13/F14/F15/F16；R14_COMMON 1 处：F17 的 `§2.6四·L215`；PANEL 2 处：F22 的 `L146–337`、F25 的 `L139–140`）。F25 的 `strict_panel.py(L78)` 按例外保留，并在其后加「行号仅供定位，文件变更后可能位移」。
- F25 的 `PANEL` 引用改为 `PANEL.md(M58 界向更正)`，不再含被更正旧句 `L139`；statement 未改。
- 统一基准：`LEAD_LOCK` → `lead\LEAD_LOCK`；`PENDING_DECISIONS.md` → `lead\PENDING_DECISIONS.md`；`R16 续线台账 §1054` → `lead\GOAL_THREE_TARGETS_20261018.md(§1054)`；其余 run 内路径前缀 `lead\next_re_20261117_r14\`。

## 重跑路径解析（自实现，借鉴 R43 work.py 的 split_top/base_path 思路）
- 实现：`verify.js`；逐条拆 `evidence_paths`、取 `(` 前基准、从仓库根 `path.resolve` 查存在性；结果落 `paths.tsv`（表头 + 72 行 = R43 的 71 + F24 净增 1）。
- 三桶（按 fact_id 计，规则同 R43：全部路径存在 = RESOLVED；部分存在 = PARTIAL；全不存在 = BROKEN）：
  - **RESOLVED 26**（F01–F26 全部）
  - **PARTIAL 0**
  - **BROKEN 0**
- 附加校验：`evidence_paths` 中已无 STATUS_BOARD / PANEL / LEAD_LOCK / R14_COMMON / SECTION.md 的裸行号锚；F25 含 `PANEL.md(M58 界向更正)` 且不含 `L139`；F25 `strict_panel.py(L78)` 带位移警示。
- statement / grade / limitations 与 v3.1 逐字节一致；fact_id 连续 F01–F26。

## CR 与产物自检
- 产物 `FACT_INDEX.tsv` / `README.md` / `REPORT.md` / `paths.tsv` / `verify.js` 逐字节检查 0x0D，均为 0。
- 四个受保护 FACT_INDEX 目录哈希前后一致，未改动。
