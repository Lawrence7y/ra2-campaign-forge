# U6 —— B2B_DESIGN.md:151 镜像同步（JSON:5 的设计镜像，每条一页）

## 目标
- 文件：`lead/b2b_design_20261106/B2B_DESIGN.md`（同 U5 件）
- 行：**第 151 行**（§2 状态矩阵表数据行 4，第 3 列 condition；镜像 `STATE_MATRIX.json:5`）

## 原文整行逐字（本轮 Read 实读 :151）
```
| `post_read_error` | `present` | 跑后 `read_bytes/stat/write_bytes` 抛异常（`post.read_error` 非空）⇒ 独立 error 出口 | `post_read_error` | `none` | `None` | `false` |
```

## 改后整行逐字（改文正本：`_m5_cells.json` U6.new_condition_cell、`U5U6_MIRROR_TEXTS.md` §3.2 成文交付）
```
| `post_read_error` | `present` | 跑后 `read_bytes/stat/write_bytes` 抛异常（`post.read_error` 非空）⇒ 独立 error 出口（★ N1 码序 `read_error` 出口先于一切 pre 分支；pre 任意态——`unknown`/`absent_confirmed`/`present`/`error`——+ `read_error` 均落本行，`preState` 列的 `present` 为最常见登记态，匹配以本 condition 为准） | `post_read_error` | `none` | `None` | `false` |
```

## JSON 侧 ↔ B2B 侧对照（U5U6_MIRROR_TEXTS §3.2 表转录）
| 段 | JSON 侧（row5:132 逐字） | B2B 侧改文（去反引号） | 差异性质 |
|:--|:--|:--|:--|
| 谓词① | ★ N1 码序 read_error 出口先于一切 pre 分支 | 同文 | 仅反引号 |
| 谓词① 续 | ：候选 :4643-4646 先于 :4648 unknown / :4652 error / :4657 无件 / :4666 absent_confirmed / :4672 起 present 支 | （无） | 白名单差＝候选行号指针串（指针级，既有省略惯例） |
| 谓词② | pre 任意态——unknown/absent_confirmed/present/error——+ read_error 均落本行 | 同文（含同款 `/` 分隔） | 仅反引号 |
| 谓词③ | preState 列的 present 为最常见登记态，匹配以本 condition 为准 | 同文 | 仅反引号 |

- 不动项：`preState` 列保持 `present` 不动（B2B_DESIGN.md:142 四态值域契约）；其余 6 列、14 行结构、行序全不动。

## 出处
- 镜像义务：B2B_DESIGN.md:144（本轮实读 ✓）；row5 §4.3-B:133「镜像必改」。
- 触发理由说明（两源不同、结论一致，非冲突）：pf2 §4.7-1:204 提 :151 是在「放宽 :5 preState」分支下（该分支两源均不采）；row5 要改 :151 的原因是 condition 注记的镜像（UNIFIED_TEXT_FIX U6 条转录）。

## 需谁批准
**乙设计责任人**（同 U5）。级联同 U5。

## 依赖关系
- **与 U3 成对、六处同批**（P3）。
- 时间线同 U5（两汇总件如实标「未提供」，正本为 `lead/u5u6_mirror_20261109/` 后补起草，待批准）。
