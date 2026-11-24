# S13-K5 DISAGREE

## D1 — 分母口径：只并列，不裁决
逐行复核认定 92 行容器模板实例化（清单 EVIDENCE/container_template_92.tsv）。规则原文（COVERAGE/coverage_README.md）：「容器模板（`T_VectorClass_*`/`T_DynamicVectorClass_*`/`T_TClassFactory_*`/`T_VectorCursor_*` 等）按审计 `class_to_sub` 建议显式归 S22，sem 标 `container_template`（210 条）；」。命中 92/240，当前这 92 行在 coverage.tsv 仍为 S13 且 proved=0。
并列结果（并入 K2+K4+本卡 6 行后）：
- 240 口径：74/240 = 30.83%，50% 门槛 = 120 行，差 46。
- 148 口径（剔除 92 行）：74/148 = 50.00%，50% 门槛 = 74 行，差 0。
本卡不宣布达标或未达标。裁决人：Lead（并由用户确认项目口径）。需要输入：①确认 coverage.tsv 是否按 class_to_sub 把 92 行迁 S22；②确认 DoD 的 50% 分母绑定 240 还是 148；③若采纳 148，是否要求合并员同步改 subsystem/sem，而非只在百分比中扣减。

## D2 — 审计「同型」与逐字节同一性
审计称 0040F510 与 0x75E3B0 同型；本卡证实创建核心同型但逐字节不同（参数压栈顺序、跳转编码、返回路径均不同），返回约定从对象指针变为索引。若审计期望「同型=字节一致」，该措辞应改为「同一 find-or-make 算法族，返回约定不同」。

## D3 — 两个 thunk 是否计入 proved
本卡 census 判定 0046B990/0046B9A0 行为级可证，但因占位名且非派工 6 行，未写 coverage_delta.tsv。若 Lead 采用「行为可证即 proved」，需另裁 2 行并更新统计为 76/240=31.67%、76/148=51.35%。

## D4 — 未改台账
coverage.tsv 现场仍为 47/160/33；K2 8 行、K4 13 行、本卡 6 行均未写入 coverage.tsv。四阶段数只是模拟合并，不代表台账已更新。
