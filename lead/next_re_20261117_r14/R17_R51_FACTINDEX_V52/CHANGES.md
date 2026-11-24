# CHANGES.md — FACT_INDEX v5.1 → v5.2

基底：`lead\next_re_20261117_r14\R17_R47_GRADE_NORM\FACT_INDEX.tsv`（v5.1，49 条）。本目录为新增产物，未修改任何既有 FACT_INDEX 目录。

## 1. 字节裁决 C-1

| fact_id | 改了什么 | 依据产物 |
|---|---|---|
| F01 | 删除「954 个主 COL 的 pSelf=COL−0x10」；改写为「954 为主 COL 数、总 COL 1211/TD 988、34 个 TD 无 vtable-COL 指向、本镜像 COL 内无 pSelf 字段（COL 恰 5 dword）」；保留 1201/988/100%/.?AV 962 + .?AU 26/非 988 项总表；limitations 注明 0/1211；evidence_paths 增列裁决 VERDICT | `lead\next_re_20261117_r14\R17_R50_ADJ_PSELF\VERDICT.md`；`_cards\R17-R51-FACTINDEX-V52.md` |
| F31 | 结论「不可判起点」保留；理由改为「COL 结构内无 pSelf 字段（5 dword），不存在可用来判表起点的 self 指针」；合规 COL 联合判据保留；limitations 注明旧「恒为 0」描述的是 COL−0x4 处另一结构（257/1211），不是 COL 内字段；evidence_paths 增列裁决 VERDICT | `lead\next_re_20261117_r14\R17_R50_ADJ_PSELF\VERDICT.md`；`_cards\R17-R51-FACTINDEX-V52.md` |

## 2. grade 与 limitations 补正

| fact_id | 改了什么 | 依据产物 |
|---|---|---|
| F25 | grade `[已证]` → `[流程]`；evidence_paths 去掉裸行号锚点 | `lead\next_re_20261117_r14\R17_AUDIT_FI_V5\VERDICT.md` §2.1；V52 卡要点 2/5 |
| F24 | grade 保持 `[已证]`；limitations 开头加「『改指针无解、不再投卡』属单源归因 + 行动裁决，不随数字一并作已证」 | `R17_AUDIT_FI_V5\VERDICT.md` §2.1；V52 卡要点 2 |
| F17 | limitations 末尾补「引 ②-b 须同引 §2.9 定谳句 + 书面限制 a–e + §2.10 的 (a′)，四者不可拆」；加 D-1/D-2 交叉引用；evidence_paths 括号内分号改斜杠 | `R17_AUDIT_FI_V5\VERDICT.md` §3；`R17_AUDIT_FI_V5\dup_conflict.md` D-1/D-2 |
| F18 | limitations 末尾补同一四件套不可拆句 | `R17_AUDIT_FI_V5\VERDICT.md` §3 |
| F19 | limitations 末尾补同一四件套不可拆句 | `R17_AUDIT_FI_V5\VERDICT.md` §3 |
| F21 | limitations 末尾补同一四件套不可拆句 | `R17_AUDIT_FI_V5\VERDICT.md` §3 |
| F36 | limitations 末尾补同一四件套不可拆句；加 D-2 交叉引用；evidence_paths 括号内分号改斜杠 | `R17_AUDIT_FI_V5\VERDICT.md` §3；`R17_AUDIT_FI_V5\dup_conflict.md` D-2 |

## 3. 重复/矛盾处置（保留条目，不删）

| fact_id | 改了什么 | 依据产物 |
|---|---|---|
| F08 | 加 D-1 交叉引用：与 F17 部分重叠，引用时二者同看 | `R17_AUDIT_FI_V5\dup_conflict.md` D-1 |
| F13 | 加 D-3 交叉引用：与 F20 部分重叠，引用时二者同看 | `R17_AUDIT_FI_V5\dup_conflict.md` D-3 |
| F20 | 加 D-3 交叉引用：与 F13 部分重叠，引用时二者同看 | `R17_AUDIT_FI_V5\dup_conflict.md` D-3 |
| F29 | 加 D-4 交叉引用；并列两种读法并注明口径待裁、不得单引其一 | `R17_AUDIT_FI_V5\dup_conflict.md` D-4 |
| F49 | 加 D-4 交叉引用；并列两种读法并注明口径待裁、不得单引其一 | `R17_AUDIT_FI_V5\dup_conflict.md` D-4 |

## 4. evidence_paths 格式卫生

| fact_id | 改了什么 | 依据产物 |
|---|---|---|
| F22 | `(§1 L1–L3)` → `(§1 表)`，去掉裸行号锚点 | V52 卡硬约束 2 |
| F28 | 括号内分号 `；` 改为 ` / ` | V52 卡硬约束 2 |
| F33 | 括号内分号改为 ` / ` | V52 卡硬约束 2 |
| F34 | 括号内分号改为 ` / `（保留嵌套括注） | V52 卡硬约束 2 |
| F35 | 括号内分号改为 ` / ` | V52 卡硬约束 2 |

以上仅改 evidence_paths 锚点写法；statement、grade、limitations 未动。

## 5. 新增五条

| fact_id | 改了什么 | 依据产物 |
|---|---|---|
| F50 | 新增：VA→文件偏移必须走 PE 节表，含 0x87F7E8→0x47F7E8 错节反例；grade `[流程]` | `R17_AUDIT_FI_V5\VERDICT.md` §5 N1；`R17_R36_VERIFY_TABLEBASE` Q1 |
| F51 | 新增：E8 原始命中数 ≠ 严格形态数（336/68/1439）；grade `[已证]` | `R17_AUDIT_FI_V5\VERDICT.md` §5 N2；`GOAL_THREE_TARGETS_20261018.md` N9 |
| F52 | 新增：删除析构器三件齐判据（调用侧 + call 0x7C8B3D + ret 4）；grade `[流程]` | `R17_AUDIT_FI_V5\VERDICT.md` §5 N3；`R14_COMMON.md` §13.3/§13.5；`NAMED_PUSH_AUDIT10\VERDICT.md` §2 |
| F53 | 新增：活表判据顺序与 0x007E88D0 固定反例；grade `[流程]` | `R17_AUDIT_FI_V5\VERDICT.md` §5 N4；`R14_COMMON.md` §13.5 |
| F54 | 新增：PEFormatError 是读法错症状而非不可解证据；grade `[流程]` | `R17_AUDIT_FI_V5\VERDICT.md` §5 N5；`R14_COMMON.md` §13.1 |
