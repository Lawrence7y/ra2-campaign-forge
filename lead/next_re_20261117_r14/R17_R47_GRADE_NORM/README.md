# R17_R47_GRADE_NORM 用法说明（FACT_INDEX v5.1）

## 规范化口径
- 以 v5.0（`R17_R46_FACTINDEX_V5/FACT_INDEX.tsv`）为基底；F01–F49 不增删、不重排。
- `grade` 列只允许 4 个取值：`[已证]` / `[静态推断]` / `[流程]` / `未取得`。
- 原 grade 中的括注、斜杠后缀等限定一律移入该行 `limitations` 开头；已有 `limitations` 用「；」连接。只搬运原措辞并作必要连接，不改写、不删除。
- `[流程]（裁定）` 归 `[流程]`；「裁定」已在 `statement`，不再搬入 `limitations`。
- 混合态 `[已证]（结构）＋未取得（表内容）` 归 `[已证]`，并在 `limitations` 明写「表内容未取得」。
- `statement`、`evidence_paths`、`fact_id` 一律不动。

## 文件
- `FACT_INDEX.tsv`：v5.1 主表，5 列不变，49 条不变。
- `REPORT.md`：改前→改后→搬入文本、grade 统计、路径解析、SHA-256 与 CR 自证。

## 编码
本目录全部产物 LF、无 CR。
