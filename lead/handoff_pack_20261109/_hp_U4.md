# U4 —— STATE_MATRIX.json:4 condition 加句（随批关闭 W2；可推迟须登记，每条一页）

## 目标
- 文件：`lead/b2b_design_20261106/STATE_MATRIX.json`（同 U2 件）
- 行：**第 4 行**（数据行 3）

## 原文逐字（本轮 Read 实读 :4）
```
  {"state":"error","preState":"error","condition":"跑前采集抛异常（snap.error 非空）⇒ 独立 error 出口，不降级、不静默、不给 high","verdict":"error_pre_snapshot","confidence":"none","usableAsCrashEvidence":false},
```

## 加句逐字（源件处方原文：row5 §4.3-B:135「JSON:4 condition 加」；**拼接点源件未逐字指明**——仅言「加」，如实标注）
```
（post.read_error 非空时仍先落 post_read_error，见 :5 行）
```
`_m5_cells.json` json4_new_recommended（推荐拼接点 = 「独立 error 出口」之后，见下 P6）：
```
跑前采集抛异常（snap.error 非空）⇒ 独立 error 出口（post.read_error 非空时仍先落 post_read_error，见 :5 行），不降级、不静默、不给 high
```

## 拼接点（P6）
源件未逐字指明拼接点（`_uf_UNIFIED_FIX_LIST_20261109.md:82` 自记）；`_m5_cells.json` 按「推荐拼接点（独立 error 出口 之后）」拼入、`U5U6_MIRROR_TEXTS.md` §3.3/§5.3-2 同推荐——**最终由批准人定**。

## 出处
- 源②：`lead/matrix_row5_20261109/MATRIX_ROW5_COUPLING.md` §4.3-B:135 随批（「不加则须在登记中如实保留 W2」）。
- W2 本体：源③ `lead/w2_samecause_20261109/W2_SAME_CAUSE.md` §4.2:100（:4 无跑后限定 ⇒ error×read_error 格被 :4 声称 error_pre_snapshot、实码 post_read_error；RULING_MATRIX_AB.md:50/:60 已判活性误配、取值层无损——源③转引）。

## 需谁批准
**乙设计责任人**；row5 明示**可推迟**，推迟须在登记中如实保留 W2（row5 §4.3-B:135）。级联同 U2。

## 依赖关系
- 与 U7（其设计镜像 :150）成对；**六处同批**（P3）；受范围准冲突①（P1）辖。
