# a-S17-ENGFAM — 审计 S17 英文措辞族 34 行的四环实质

## 背景（已核实，可直接用）

`coverage.tsv` 中语义串匹配 `(?i)unproven|unverified|not proven` 的行共 **34 行**，全部属 **S17**、全部 grade `[已证]`、全部在 `function_atlas.tsv` 内。它们全部是 `Save_VectorBlock_NN` 一族（01–35 缺 #17），语义尾缀为 `class name unproven (arg .bss obj)`，`evidence_path` 全指 `S17-F1/EVIDENCE/analysis_deep2.txt`。

这 34 行此前从未进入任何审计论域：S17 的 `proved_strict = 55`，其中含这 34 行；剔除后为 21，门槛 51。

## 你要回答的唯一问题

**这 34 行，逐行看，四环到底齐不齐？**

不是问措辞该不该算问题（那是裁决项，已另报），而是问**实质**：把措辞当作已声明的待复核标记，逐行按 D-40 四环 + D-42 ③ 分级复核一遍，得出每行真实的成立与否。这样无论裁决走哪个读法，S17 的真实存活数都是已知的。

## 材料

- 目标二进制：`D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe`，期望 SHA-256 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`（先自校验）
- ImageBase `0x400000`，`.text = [0x401000, 0x7E038D)`
- capstone 5.0.7（**必须 `skipdata=True`**）+ pefile 2024.8.26，Python 3.12.10，无 venv、不许 pip install
- 34 行清单：自己从 `coverage.tsv` 过滤得到（不要凭空列），把过滤命令写进报告
- 原始普查：`S17-F1\EVIDENCE\analysis_deep2.txt`（**只能当线索，不能当证据**）

## 逐行要核的五点

1. **① 入口**：地址在 `.text` 内、函数边界自洽。
2. **② 类身份**：所属类可证（RTTI 名 / 虚表归属 / 构造链）。**注意**：这 34 行的语义自己说 `class name unproven` —— 你要判断这是"当时没查"还是"查不到"。若你能用 RTTI / 虚表把它定死，就写清定死的依据。
3. **③ 整体合同**：**只有 ③b 计入**。③b 四形态之一：①跳转表且每路可验证；②可伪证错误码/返回约定；③内存形状断言；④完整循环 I/O 带边界检查。
   - ③b④ 的"写"必须是**栈外写**或**可伪证返回码**；写栈、写累加槽、纯寄存器推进**不算**。
   - ③a（单调用+单写、纯转发、零+默认、无分支直线）**不算**。
4. **④ 使用见证**：真实调用者或活虚表派发；**direct-only 不足**。
5. **`Save_VectorBlock_NN` 这一族的共性**：这 34 个是不是同一模板的 N 个实例？如果是，说明模板形态（有界循环？逐字段保存？），并给出"模板成立"能否替代逐行成立的理由。**不许**用"同族所以都成立"一句带过——必须给出至少 3 个不同实例的独立字节核验结果，再给整族结论。

## 已知陷阱（主动排查）

- `0045A640` 类：循环内只有 `push` 写栈、非栈写 0、计数器游标皆寄存器推进 ⇒ ③b 不成立。
- 多路进同一 call、仅参数不同 ⇒ 不计 细则#1。
- 名字若为 `slotN` 形式：不满足 `named_pct_S(strict)`，但满足 `named_pct_S(R14)`，不构成判行不成立的理由。

## 输出（只写自己目录）

- `S17_ENGFAM\VERDICT.md`：逐行一节，写出 entry、五点结论 + 地址与字节、最终 `PASS` / `FAIL` / `词措辞掩盖了实质` 三选一，并给整族结论（模板是否成立、成立范围）
- `S17_ENGFAM\verdict.tsv`：表头 `entry	verdict	has_ring2	has_ring3b	has_ring4	reason`，34 行数据；`has_*` 填 `yes`/`no`；`verdict` 只能是 `PASS`/`FAIL`
- `S17_ENGFAM\SUMMARY.md`：一段话给出「34 行中实质 PASS n 行 / FAIL m 行」，以及「若按读法 Y 全剔，S17 为 21；若按实质复核结果，S17 为 21 + n」

## 纪律

- **不许**修改 `coverage.tsv`、`PANEL.md`、`R14_COMMON.md` 或任何既有台账；只写 `S17_ENGFAM\`。
- 不许把 `analysis_deep2.txt` 的结论当证据；每个 PASS 必须有你自己反汇编出的地址与字节。
- 证据不足判 `FAIL`，不许写"基本成立"。
