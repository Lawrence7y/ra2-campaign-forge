# U3 —— STATE_MATRIX.json:5 condition 追加码序注记（每条一页）

## 目标
- 文件：`lead/b2b_design_20261106/STATE_MATRIX.json`（同 U2 件）
- 行：**第 5 行**（数据行 4）

## 原文逐字（本轮 Read 实读 :5）
```
  {"state":"post_read_error","preState":"present","condition":"跑后 read_bytes/stat/write_bytes 抛异常（post.read_error 非空）⇒ 独立 error 出口","verdict":"post_read_error","confidence":"none","usableAsCrashEvidence":false},
```

## 追加文本逐字（源件处方原文：row5 §4.3-B:132；源件外侧「」为引注记号——该判读经复核 F1 更正后依据成立、**待批准人确认**，U5U6_MIRROR_TEXTS §4.3(f)/§5.1）
```
（★ N1 码序 read_error 出口先于一切 pre 分支：候选 :4643-4646 先于 :4648 unknown / :4652 error / :4657 无件 / :4666 absent_confirmed / :4672 起 present 支；pre 任意态——unknown/absent_confirmed/present/error——+ read_error 均落本行，preState 列的 present 为最常见登记态，匹配以本 condition 为准）
```
row5:132 所给追加后完整 condition（原样转录，去外侧「」；与 `_m5_cells.json` json5_new 同文）：
```
跑后 read_bytes/stat/write_bytes 抛异常（post.read_error 非空）⇒ 独立 error 出口（★ N1 码序 read_error 出口先于一切 pre 分支：候选 :4643-4646 先于 :4648 unknown / :4652 error / :4657 无件 / :4666 absent_confirmed / :4672 起 present 支；pre 任意态——unknown/absent_confirmed/present/error——+ read_error 均落本行，preState 列的 present 为最常见登记态，匹配以本 condition 为准）
```

## 拼接点（P5，供批准人确认）
row5:132 给出了追加后完整 condition，可读出拼接点 = 原 condition 串末尾「独立 error 出口」之后（UNIFIED_TEXT_FIX.md 补此判读；汇总件 `_uf_UNIFIED_FIX_LIST_20261109.md:70` 原记「未逐字指明」——如实并录两口径）。

## preState 字段不动（N-3）
row5 §4.3-B:132 理由：「写 "any" 违值域契约（B2B_DESIGN.md:142 preState ∈ 四态）；域覆盖由 condition 文本承载」。

## 出处
- 源②：`lead/matrix_row5_20261109/MATRIX_ROW5_COUPLING.md` §0/§3.1（:5 欠宽判定）、§4.3-B:132（选项 B，**推荐**）。
- 源① §4.7-1:204 只把 :5 欠宽列为「连带供裁量（非本登记项）」且仅描述「放宽 preState」分支——把订正落成「condition 加注、preState 不动」的成文建议出自源②。两源不矛盾（UNIFIED_TEXT_FIX §5.1 组(a)）。
- 事实底座（row5 §4.3-B:76 实读，转引）：候选 :4643/:4648/:4652/:4657/:4666/:4672 分支行号逐一相符。

## 需谁批准
**乙设计责任人**（row5 §5.4-1:184「:2/:4/:5 三行的 condition 措辞变更同属此主体」）。级联同 U2（同文件同批 → 指纹一次性变化）。

## 依赖关系
- 与 U2 一交一接、语义闭合（:2 分流「见 :5 行」→ :5 注记承接「pre 任意态……均落本行」）；**六处同批**（P3）；受范围准冲突①（P1）辖——row5 选项 A 之下本条为省略项，代价 = 严格键层 O3 孤儿 + W2 残留（row5 §4.3-A:129）。
