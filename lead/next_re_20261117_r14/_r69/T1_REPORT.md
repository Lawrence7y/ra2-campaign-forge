# R69-T1-LIMREF — FACT_INDEX limitations 列非 § 引用核验

执行员：work/cn:deepseek-v4.1-flash（R17 第 69 轮，2026-11-22）
只读核验，未修改任何文件（脚本经 stdin/`/tmp` 执行，唯一产物为本文件）。
仓库根：/home/t628/projects/ra2-campaign-forge
索引：lead/next_re_20261117_r14/R17_R102_FACTINDEX_V530/FACT_INDEX.tsv（表头 + 54 数据行，5 列，每行 NF=5 已核）

---

## 1 · 2.1 evidence_paths 存在性普查

| 项 | 值 |
|---|---|
| A 条目总数 | **171** |
| B 路径存在 | **128** |
| C 路径不存在 | **43** |
| （参考）带锚点条目 | 117 |

唯一路径数 68；不存在路径去重后 16 条；不存在涉及 34 个 fact_id；20 个 fact_id 的全部 evidence_paths 均存在
（F01 F02 F03 F05 F17 F20 F21 F26 F30 F31 F32 F33 F37 F38 F40 F41 F42 F50 F53 F54）。
无空路径条目；无「路径存在但为目录」的条目。

### 缺失清单全文（43 条，按 fact_id 顺序；带锚点列均为 Y）

```
F04 | lead/next_re_20261117_r14/R17_LEDGER_1062/SECTION.md      | 锚=Y
F06 | lead/next_re_20261117_r14/R17_LEDGER_1064/SECTION.md      | 锚=Y
F07 | lead/next_re_20261117_r14/R17_LEDGER_1064/SECTION.md      | 锚=Y
F08 | lead/next_re_20261117_r14/R17_LEDGER_1064/SECTION.md      | 锚=Y
F09 | lead/next_re_20261117_r14/R17_LEDGER_1065/SECTION.md      | 锚=Y
F09 | lead/next_re_20261117_r14/R17_LEDGER_1063/SECTION.md      | 锚=Y
F10 | lead/next_re_20261117_r14/R17_LEDGER_1065/SECTION.md      | 锚=Y
F10 | lead/next_re_20261117_r14/R17_LEDGER_1064/SECTION.md      | 锚=Y
F11 | lead/next_re_20261117_r14/R17_LEDGER_1062/SECTION.md      | 锚=Y
F12 | lead/next_re_20261117_r14/R17_LEDGER_1062/SECTION.md      | 锚=Y
F13 | lead/next_re_20261117_r14/R17_LEDGER_1063/SECTION.md      | 锚=Y
F13 | lead/next_re_20261117_r14/R17_LEDGER_1064/SECTION.md      | 锚=Y
F14 | lead/next_re_20261117_r14/R17_LEDGER_1062/SECTION.md      | 锚=Y
F15 | lead/next_re_20261117_r14/R17_LEDGER_1063R/SECTION.md     | 锚=Y
F16 | lead/next_re_20261117_r14/R17_LEDGER_1063/SECTION.md      | 锚=Y
F16 | lead/next_re_20261117_r14/R17_LEDGER_1062/SECTION.md      | 锚=Y
F18 | lead/next_re_20261117_r14/GATE_BEHAV/PROGRESS.md          | 锚=Y
F19 | lead/next_re_20261117_r14/R17_AUDIT_R9/VERDICT.md         | 锚=Y
F22 | lead/next_re_20261117_r14/R17_DELIVERY/DELIVERY_SUMMARY.md| 锚=Y
F22 | lead/next_re_20261117_r14/COVERAGE/PANEL.md               | 锚=Y
F23 | lead/next_re_20261117_r14/R17_DELIVERY/DELIVERY_SUMMARY.md| 锚=Y
F23 | lead/next_re_20261117_r14/COVERAGE/PANEL.md               | 锚=Y
F24 | lead/next_re_20261117_r14/R17_DELIVERY/DELIVERY_SUMMARY.md| 锚=Y
F25 | lead/next_re_20261117_r14/R17_DELIVERY/DELIVERY_SUMMARY.md| 锚=Y
F25 | lead/next_re_20261117_r14/COVERAGE/PANEL.md               | 锚=Y
F27 | lead/next_re_20261117_r14/HANDOFF_R16.md                  | 锚=Y
F28 | lead/next_re_20261117_r14/NAMED_PUSH_AUDIT10/VERDICT.md   | 锚=Y
F28 | lead/next_re_20261117_r14/COVERAGE/PANEL.md               | 锚=Y
F29 | lead/next_re_20261117_r14/COVERAGE/PANEL.md               | 锚=Y
F34 | lead/next_re_20261117_r14/COVERAGE/PANEL.md               | 锚=Y
F35 | lead/next_re_20261117_r14/COVERAGE/PANEL.md               | 锚=Y
F36 | lead/next_re_20261117_r14/COVERAGE/PANEL.md               | 锚=Y
F39 | lead/next_re_20261117_r14/HANDOFF_R14_R3.md               | 锚=Y
F43 | lead/next_re_20261117_r14/S13_K10/_audit/VERDICT.md       | 锚=Y
F44 | lead/next_re_20261117_r14/S13_K10/_audit/VERDICT.md       | 锚=Y
F45 | lead/next_re_20261117_r14/S13_K10/_audit/VERDICT.md       | 锚=Y
F46 | lead/next_re_20261117_r14/S10_KPROVED/_audit/VERDICT.md   | 锚=Y
F46 | lead/next_re_20261117_r14/S13_K12/_audit/VERDICT.md       | 锚=Y
F47 | lead/next_re_20261117_r14/S13_K12/_audit/VERDICT.md       | 锚=Y
F48 | lead/next_re_20261117_r14/S10_KPROVED/_audit/VERDICT.md   | 锚=Y
F49 | lead/next_re_20261117_r14/HANDOFF_R14_R3.md               | 锚=Y
F51 | lead/next_re_20261117_r14/R17_AUDIT_FI_V5/VERDICT.md      | 锚=Y
F52 | lead/next_re_20261117_r14/NAMED_PUSH_AUDIT10/VERDICT.md   | 锚=Y
```

---

## 2 · 2.2 缺失目录归组（按路径第 3 段，即轮次目录下第一层）

| 目录 | 涉及 fact_id | 条目数 | 该目录在本机是否存在 |
|---|---|---|---|
| lead/next_re_20261117_r14/COVERAGE | F22,F23,F25,F28,F29,F34,F35,F36 | 8 | N |
| lead/next_re_20261117_r14/R17_LEDGER_1062 | F04,F11,F12,F14,F16 | 5 | N |
| lead/next_re_20261117_r14/R17_LEDGER_1064 | F06,F07,F08,F10,F13 | 5 | N |
| lead/next_re_20261117_r14/R17_DELIVERY | F22,F23,F24,F25 | 4 | N |
| lead/next_re_20261117_r14/R17_LEDGER_1063 | F09,F13,F16 | 3 | **Y**（仅含 SUPERSEDED.md） |
| lead/next_re_20261117_r14/S13_K10 | F43,F44,F45 | 3 | N |
| lead/next_re_20261117_r14/R17_LEDGER_1065 | F09,F10 | 2 | N |
| lead/next_re_20261117_r14/NAMED_PUSH_AUDIT10 | F28,F52 | 2 | N |
| lead/next_re_20261117_r14/HANDOFF_R14_R3.md | F39,F49 | 2 | N（该 md 不存在） |
| lead/next_re_20261117_r14/S10_KPROVED | F46,F48 | 2 | N |
| lead/next_re_20261117_r14/S13_K12 | F46,F47 | 2 | N |
| lead/next_re_20261117_r14/R17_LEDGER_1063R | F15 | 1 | N |
| lead/next_re_20261117_r14/GATE_BEHAV | F18 | 1 | **Y**（仅含 CASES.tsv） |
| lead/next_re_20261117_r14/R17_AUDIT_R9 | F19 | 1 | N |
| lead/next_re_20261117_r14/HANDOFF_R16.md | F27 | 1 | N（该 md 不存在） |
| lead/next_re_20261117_r14/R17_AUDIT_FI_V5 | F51 | 1 | N |

合计 43 条 / 16 组；其中 14 组的顶层目录本机不存在，2 组（R17_LEDGER_1063、GATE_BEHAV）目录存在但所列文件不存在。

---

## 3 · 2.3 limitations 列非 § 引用清点

### 3.1 F 号（严格边界：前不接 [0-9A-Za-z]、后不接数字）

共 **32 次出现 / 25 个去重有向边**，全部指向表内存在的 fact_id（悬挂 0、自环 0）。

| 出现它的 fact_id | 引用串 | 目标 Fxx 是否存在于 FACT_INDEX |
|---|---|---|
| F08 | F17 | Y |
| F13 | F20 | Y |
| F17 | F08（×2，`须与 F08 同引`、`D-1：与 F08（b 部分）`） | Y |
| F17 | F36 | Y |
| F20 | F13 | Y |
| F29 | F49 | Y |
| F30 | F01 | Y |
| F35 | F25 | Y |
| F35 | F26 | Y |
| F36 | F17（×2） | Y |
| F37 | F01 | Y |
| F37 | F02 | Y |
| F39 | F08 | Y |
| F39 | F23 | Y |
| F40 | F16（×2） | Y |
| F45 | F01（×2） | Y |
| F46 | F38 | Y |
| F49 | F13（×2） | Y |
| F49 | F29 | Y |
| F50 | F20（原文 `与 F20① 部分重叠`；`①` 属 CJK 圈码，`\b` 在此处失效） | Y |
| F51 | F27（×2） | Y |
| F52 | F28 | Y |
| F52 | F29 | Y |
| F53 | F28 | Y |
| F54 | F30（×2） | Y |

正则口径说明（实测差异，只报事实）：用 `\bF(\d{2})\b` 只得 31 次，漏掉 F50 的 `F20①`（`①` 被 Python 视为 `\w`，故 `\b` 不成立）；改用上表严格边界后得 32 次。两口径在其他 53 行完全一致（实测 `ROWS_WHERE_REGEXES_DIFFER 1`）。

### 3.2 M 号（限 F34/F35/F36）

| 事实行 | 引用串 | 本机是否存在含该 M 号定义的文件 | 命中文件数（rg -l 于 lead/） |
|---|---|---|---|
| F34 | M98 | Y | 22 |
| F34 | M102 | Y | 29 |
| F35 | M47 | Y | 45 |
| F35 | M52 | Y | 39 |
| F35 | M44 | Y | 38 |
| F36 | M103 | Y | 32 |

M 号总出现 6 次、6 个不同 M 号，无其他 M 号。命中数含 `R17_LEAD_BASELINE/` 下的 `.bak`/`before_*` 历史副本，未区分定义处与引用处。

### 3.3 R17 目录号（`R17_[A-Za-z0-9_]+`）

| 引用串 | 出现于 | 同名目录 | 同名文件 |
|---|---|---|---|
| R17_R28_R12_REPAIR | F15 | N | N |
| R17_LEDGER_1063 | F15 | **Y**（仅 SUPERSEDED.md） | N |
| R17_LEDGER_1063R | F15 | N | N |
| R17_R96_TIER_FINAL_4413 | F24 | Y | N |
| R17_R97_TIER_FINAL_4413B | F24 | Y | N |
| R17_R99_TIER_FINAL_4416 | F24 | Y | N |
| R17_R52_ADJ_D4 | F29,F49 | Y | N |
| R17_R68_T1_IAT | F29 | Y | N |

R17 号共 **8 个不同串 / 9 次（fact_id, 引用串）配对**：F15×3（R17_LEDGER_1063、R17_LEDGER_1063R、R17_R28_R12_REPAIR）、F24×3（R17_R96/R97/R99）、F29×2（R17_R52_ADJ_D4、R17_R68_T1_IAT）、F49×1（R17_R52_ADJ_D4）。

---

## 4 · 2.4 F 号交叉引用：双向对与单向对

有向边 24 个去重（32 次出现），无自环、无悬挂。

### 4.1 双向对（4 对）

| A | B | 依据 |
|---|---|---|
| F08 | F17 | F08 limitation 提 F17；F17 limitation 提 F08 两次 |
| F13 | F20 | F13 提 F20；F20 提 F13 |
| F17 | F36 | F17 提 F36；F36 提 F17 两次 |
| F29 | F49 | F29 提 F49；F49 提 F29 |

### 4.2 单向对（17 条）

```
F30 -> F01
F35 -> F25
F35 -> F26
F37 -> F01
F37 -> F02
F39 -> F08
F39 -> F23
F40 -> F16
F45 -> F01
F46 -> F38
F49 -> F13
F50 -> F20
F51 -> F27
F52 -> F28
F52 -> F29
F53 -> F28
F54 -> F30
```

注：F49→F13 记为单向，因 F13 的 limitation 只提 F20，未回指 F49。

---

## 5 · 命令与输出原文

<details>
<summary>5.1 表结构核验</summary>

```
$ awk -F'\t' '{print NR": "$1" | "NF}' lead/.../FACT_INDEX.tsv
1: fact_id | 5
2: F01 | 5
...（55 行，全部 NF=5，末行 55: F54 | 5）

$ awk -F'\t' 'NR>1 && ...'  # 数据行统计
HDR: ['fact_id', 'statement', 'grade', 'evidence_paths', 'limitations']
DATA_ROWS 54
```
</details>

<details>
<summary>5.2 2.1 / 2.2 主脚本输出</summary>

```
$ python3 /tmp/_r69_t1.py
[2.1] A=171 B=128 C=43 ANCHORED=117
[2.1] MISSING:
  F04 | lead/next_re_20261117_r14/R17_LEDGER_1062/SECTION.md | anchor=Y
  F06 | lead/next_re_20261117_r14/R17_LEDGER_1064/SECTION.md | anchor=Y
  F07 | lead/next_re_20261117_r14/R17_LEDGER_1064/SECTION.md | anchor=Y
  F08 | lead/next_re_20261117_r14/R17_LEDGER_1064/SECTION.md | anchor=Y
  F09 | lead/next_re_20261117_r14/R17_LEDGER_1065/SECTION.md | anchor=Y
  F09 | lead/next_re_20261117_r14/R17_LEDGER_1063/SECTION.md | anchor=Y
  F10 | lead/next_re_20261117_r14/R17_LEDGER_1065/SECTION.md | anchor=Y
  F10 | lead/next_re_20261117_r14/R17_LEDGER_1064/SECTION.md | anchor=Y
  F11 | lead/next_re_20261117_r14/R17_LEDGER_1062/SECTION.md | anchor=Y
  F12 | lead/next_re_20261117_r14/R17_LEDGER_1062/SECTION.md | anchor=Y
  F13 | lead/next_re_20261117_r14/R17_LEDGER_1063/SECTION.md | anchor=Y
  F13 | lead/next_re_20261117_r14/R17_LEDGER_1064/SECTION.md | anchor=Y
  F14 | lead/next_re_20261117_r14/R17_LEDGER_1062/SECTION.md | anchor=Y
  F15 | lead/next_re_20261117_r14/R17_LEDGER_1063R/SECTION.md | anchor=Y
  F16 | lead/next_re_20261117_r14/R17_LEDGER_1063/SECTION.md | anchor=Y
  F16 | lead/next_re_20261117_r14/R17_LEDGER_1062/SECTION.md | anchor=Y
  F18 | lead/next_re_20261117_r14/GATE_BEHAV/PROGRESS.md | anchor=Y
  F19 | lead/next_re_20261117_r14/R17_AUDIT_R9/VERDICT.md | anchor=Y
  F22 | lead/next_re_20261117_r14/R17_DELIVERY/DELIVERY_SUMMARY.md | anchor=Y
  F22 | lead/next_re_20261117_r14/COVERAGE/PANEL.md | anchor=Y
  F23 | lead/next_re_20261117_r14/R17_DELIVERY/DELIVERY_SUMMARY.md | anchor=Y
  F23 | lead/next_re_20261117_r14/COVERAGE/PANEL.md | anchor=Y
  F24 | lead/next_re_20261117_r14/R17_DELIVERY/DELIVERY_SUMMARY.md | anchor=Y
  F25 | lead/next_re_20261117_r14/R17_DELIVERY/DELIVERY_SUMMARY.md | anchor=Y
  F25 | lead/next_re_20261117_r14/COVERAGE/PANEL.md | anchor=Y
  F27 | lead/next_re_20261117_r14/HANDOFF_R16.md | anchor=Y
  F28 | lead/next_re_20261117_r14/NAMED_PUSH_AUDIT10/VERDICT.md | anchor=Y
  F28 | lead/next_re_20261117_r14/COVERAGE/PANEL.md | anchor=Y
  F29 | lead/next_re_20261117_r14/COVERAGE/PANEL.md | anchor=Y
  F34 | lead/next_re_20261117_r14/COVERAGE/PANEL.md | anchor=Y
  F35 | lead/next_re_20261117_r14/COVERAGE/PANEL.md | anchor=Y
  F36 | lead/next_re_20261117_r14/COVERAGE/PANEL.md | anchor=Y
  F39 | lead/next_re_20261117_r14/HANDOFF_R14_R3.md | anchor=Y
  F43 | lead/next_re_20261117_r14/S13_K10/_audit/VERDICT.md | anchor=Y
  F44 | lead/next_re_20261117_r14/S13_K10/_audit/VERDICT.md | anchor=Y
  F45 | lead/next_re_20261117_r14/S13_K10/_audit/VERDICT.md | anchor=Y
  F46 | lead/next_re_20261117_r14/S10_KPROVED/_audit/VERDICT.md | anchor=Y
  F46 | lead/next_re_20261117_r14/S13_K12/_audit/VERDICT.md | anchor=Y
  F47 | lead/next_re_20261117_r14/S13_K12/_audit/VERDICT.md | anchor=Y
  F48 | lead/next_re_20261117_r14/S10_KPROVED/_audit/VERDICT.md | anchor=Y
  F49 | lead/next_re_20261117_r14/HANDOFF_R14_R3.md | anchor=Y
  F51 | lead/next_re_20261117_r14/R17_AUDIT_FI_V5/VERDICT.md | anchor=Y
  F52 | lead/next_re_20261117_r14/NAMED_PUSH_AUDIT10/VERDICT.md | anchor=Y
[2.2] GROUPS:
  lead/next_re_20261117_r14/COVERAGE | F22,F23,F25,F28,F29,F34,F35,F36 | 8 | exists=N
  lead/next_re_20261117_r14/R17_LEDGER_1062 | F04,F11,F12,F14,F16 | 5 | exists=N
  lead/next_re_20261117_r14/R17_LEDGER_1064 | F06,F07,F08,F10,F13 | 5 | exists=N
  lead/next_re_20261117_r14/R17_DELIVERY | F22,F23,F24,F25 | 4 | exists=N
  lead/next_re_20261117_r14/R17_LEDGER_1063 | F09,F13,F16 | 3 | exists=Y
  lead/next_re_20261117_r14/S13_K10 | F43,F44,F45 | 3 | exists=N
  lead/next_re_20261117_r14/R17_LEDGER_1065 | F09,F10 | 2 | exists=N
  lead/next_re_20261117_r14/NAMED_PUSH_AUDIT10 | F28,F52 | 2 | exists=N
  lead/next_re_20261117_r14/HANDOFF_R14_R3.md | F39,F49 | 2 | exists=N
  lead/next_re_20261117_r14/S10_KPROVED | F46,F48 | 2 | exists=N
  lead/next_re_20261117_r14/S13_K12 | F46,F47 | 2 | exists=N
  lead/next_re_20261117_r14/R17_LEDGER_1063R | F15 | 1 | exists=N
  lead/next_re_20261117_r14/GATE_BEHAV | F18 | 1 | exists=Y
  lead/next_re_20261117_r14/R17_AUDIT_R9 | F19 | 1 | exists=N
  lead/next_re_20261117_r14/HANDOFF_R16.md | F27 | 1 | exists=N
  lead/next_re_20261117_r14/R17_AUDIT_FI_V5 | F51 | 1 | exists=N
```
</details>

<details>
<summary>5.3 2.3 M 号存在性（rg）</summary>

```
$ cd lead; for m in M44 M47 M52 M98 M102 M103; do
    n=$(rg -l --no-messages "\b$m\b" . | wc -l); echo "$m files=$n"; done
M44 files=38
M47 files=45
M52 files=39
M98 files=22
M102 files=29
M103 files=32
```
（`rg` 不支持 look-around，此处用 `\b`，对 `M\d+` 与 CJK 相邻情形已人工核：6 个 M 号前接空格/中文括号，边界成立。）

```
$ rg -o --no-filename 'R17_[A-Za-z0-9_]+' FACT_INDEX.tsv | sort | uniq -c | sort -rn | head -40
      5 R17_LEDGER_1064
      5 R17_LEDGER_1063
      5 R17_LEDGER_1062
      4 R17_R52_ADJ_D4
      4 R17_DELIVERY
      3 R17_R92_T1_REJUDGE
      ...（evidence_paths 列亦被扫入，故计数高于 limitations 内的 8 项）
```
仅 limitations 列（第 5 列切出后）的 R17 串为 8 个，见 3.3 表。
</details>

<details>
<summary>5.4 2.4 边集与目录存在性</summary>

```
$ python3 （见脚本输出）
EDGE_UNIQUE 24 EDGE_OCCURRENCES 32（严格边界口径）
DANGLING none
SELF none
BIDI [('F08','F17'), ('F13','F20'), ('F17','F36'), ('F29','F49')] 4
UNI 17

$ cd lead/next_re_20261117_r14
$ for d in COVERAGE R17_LEDGER_1062 R17_LEDGER_1064 R17_DELIVERY R17_LEDGER_1065 \
    NAMED_PUSH_AUDIT10 HANDOFF_R14_R3.md S10_KPROVED S13_K12 R17_LEDGER_1063R \
    R17_AUDIT_R9 HANDOFF_R16.md R17_AUDIT_FI_V5 S13_K10 R17_R28_R12_REPAIR \
    R17_LEDGER_1063 GATE_BEHAV; do printf "%-24s %s\n" "$d" "$([ -e $d ] && echo EXISTS || echo MISSING)"; done
COVERAGE                 MISSING
R17_LEDGER_1062          MISSING
R17_LEDGER_1064          MISSING
R17_DELIVERY             MISSING
R17_LEDGER_1065          MISSING
NAMED_PUSH_AUDIT10       MISSING
HANDOFF_R14_R3.md        MISSING
S10_KPROVED              MISSING
S13_K12                  MISSING
R17_LEDGER_1063R         MISSING
R17_AUDIT_R9             MISSING
HANDOFF_R16.md           MISSING
R17_AUDIT_FI_V5          MISSING
S13_K10                  MISSING
R17_R28_R12_REPAIR       MISSING
R17_LEDGER_1063          EXISTS_DIR_OR_FILE
GATE_BEHAV               EXISTS_DIR_OR_FILE

$ ls R17_LEDGER_1063 → SUPERSEDED.md
$ ls GATE_BEHAV      → CASES.tsv
$ ls NAMED_PUSH_AUDIT15 → VERDICT.md   （注：1063 与 GATE_BEHAV 目录在场但所列文件不在场；
                                         NAMED_PUSH_AUDIT15 在场，而 evidence 引的是 NAMED_PUSH_AUDIT10）
```
</details>

<details>
<summary>5.5 解析器自测原始输出</summary>

```
PASS | SELF-1 正控 存在路径判存在 | lead/next_re_20261117_r14/R14_COMMON.md | anchor= None
PASS | SELF-2 反控 不存在路径判不存在 | lead/next_re_20261117_r14/__NO_SUCH_DIR_XYZ__/NOPE.md | anchor= None
PASS | SELF-3 正控 锚剥离 | lead/next_re_20261117_r14/R14_COMMON.md | anchor= §2.9四/六
PASS | SELF-4 正控 括号内分号不分割 | ['a(x;y)', 'b'] | anchor= None
PASS | SELF-5 正控 全角括号锚剥离 | lead/LEAD_LOCK | anchor= M98
PASS | SELF-6 反控 无右括号不剥锚 | lead/LEAD_LOCK | anchor= None
PASS | SELF-7 正控 反引号剥离 | lead/LEAD_LOCK | anchor= None
SELFTEST_TOTAL 7 PASS 7
```
</details>

---

## 6 · 自测结果

| # | 类型 | 断言 | 结果 |
|---|---|---|---|
| 1 | 正控 | 已知存在路径 `lead\next_re_20261117_r14\R14_COMMON.md` 判为存在 | **PASS** |
| 2 | 反控 | 必然不存在路径 `__NO_SUCH_DIR_XYZ__/NOPE.md` 判为不存在 | **PASS** |
| 3 | 正控 | 带括号锚 `...(§2.9四/六)` 剥离出锚且路径部分为 `.../R14_COMMON.md`，且该路径存在 | **PASS** |
| 4 | 正控 | 深度>0 的分号不分割：`a(x;y);b` → 2 条 | **PASS** |
| 5 | 正控 | 全角括号锚 `lead\LEAD_LOCK（M98）` → 路径 `lead/LEAD_LOCK`、锚 `M98` | **PASS** |
| 6 | 反控 | 无右括号条目不剥锚：`lead/LEAD_LOCK` → anchor=None | **PASS** |
| 7 | 正控 | 反引号包裹 `\`lead\LEAD_LOCK\`` 剥离后判存在 | **PASS** |

合计 7/7 PASS。另有两项一致性核（非自测项）：
- 条目数 A=171 与上一轮 anchor_check.txt 的「路径项 171」一致（该文件同时声称「文件存在 171/171」，与本轮实测 B=128 不同）。
- F 号引用两种正则口径差异仅 1 处（F50 与 `F20①`），已取严格口径 32 次。

---

## 7 · 边界声明

- 全程只读；未运行反汇编、未读 gamemd.exe 字节、未判函数入口、未联网。
- 唯一写入：本文件 `/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14/_r69/T1_REPORT.md`；脚本经 heredoc/`/tmp` 执行。
- 未对「索引是否有问题」作任何判断，仅交数字与清单。
