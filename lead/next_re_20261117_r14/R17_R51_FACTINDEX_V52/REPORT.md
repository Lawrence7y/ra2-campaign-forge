# REPORT.md — R17_R51_FACTINDEX_V52（FACT_INDEX v5.2）

## 1. 基底与产物
- 基底：`lead\next_re_20261117_r14\R17_R47_GRADE_NORM\FACT_INDEX.tsv`（v5.1，49 条）。
- 产物：本目录 `FACT_INDEX.tsv` / `CHANGES.md` / `README.md` / `REPORT.md`。
- 未修改任何既有 FACT_INDEX 目录。
- 总条数：**54**（F01–F49 + F50–F54）。

## 2. grade 四档统计
| grade | 条数 |
|---|---:|
| [已证] | 27 |
| [静态推断] | 1 |
| [流程] | 24 |
| 未取得 | 2 |
| 合计 | 54 |

四档之外取值：0。

## 3. evidence_paths 路径解析（括号深度切分）
- 解析器对 ASCII 括号 `()` 与全角括号 `（）` 同计深度；只在深度为 0 的分号处切分；随后剥离首处顶层锚点括号，按仓库根目录检查存在性。
- 路径项：**133**；RESOLVED：**133**；**BROKEN 0**。
- 绝对路径：0；裸行号路径：0；括号内分号：0。
- BROKEN 明细：无。

## 4. 改动闭环
- C-1：F01 删除 `pSelf=COL−0x10`，改为「COL 内无 pSelf 字段（5 dword）」并保留成立数字；F31 保留「不可判起点」结论，理由换成「COL 无 self 字段」，limitations 注明旧说法指 COL−0x4 处另一结构（257/1211）。
- grade：F25 改 `[流程]`；F24 保持 `[已证]` 并加单源归因限制。
- 四件套：F17/F18/F19/F21/F36 limitations 末尾均含「引 ②-b 须同引 §2.9 定谳句 + 书面限制 a–e + §2.10 的 (a′)，四者不可拆」。
- 重复/矛盾：D-1/D-2/D-3 两条均保留并互引；D-4 两条 limitations 均并列两种读法并注明「口径待裁，不得单引其一」。
- 新增：F50–F54 共 5 条，编号顺延；无 F55。

## 5. 格式自证
- `FACT_INDEX.tsv`：CR 字节 0；列数 5；数据行 54。
- `CHANGES.md`：CR 字节 0。
- `README.md`：CR 字节 0。
- `REPORT.md`：CR 字节 0。
