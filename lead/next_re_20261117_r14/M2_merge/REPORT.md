# M2 合并报告（Coverage 单写者）

## 结论
- **合入 delta 卡数：33**（W176_place81 / W178_guards=PASS，其余 31=PARTIAL；0 张 FAIL/无 VERDICT）。
- **冲突数：76 条新增**（CONFLICTS data 156→232；同 grade 的 name/subsystem 不一致，保留旧值+conflict=1，未裁决）。
- **PANEL.md**：`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\PANEL.md`
- **coverage 行数：14,493 → 14,495**（+2 真新增；109 行 grade 提级不改行数）。

## 合入清单（卡号:裁决/提级/新冲突/+cov/+probe/跳过同值）
 census 卡（均 PARTIAL，提级0/+cov0/+probe0）：
- C01:1275跳 · C02:1277跳/1冲突 · C03:1275跳/1冲突 · C04:1284跳 · C05:1276跳/9冲突 · C06:1270跳
- C07:1220跳/5冲突 · C08:1238跳/6冲突 · C09:1275跳/8冲突 · C10:1286跳
 P1/F1/K1 卡（除注外均 PARTIAL）：
- S01-V1:7跳 · S03-K1:提14/冲3 · S06-K1:提12/冲8 · S08-K1:提11/冲9 · S09-F1:2跳
- S10-K1:提32/冲2/+cov1/+probe1 · S11-K1:提32/冲14/+cov1 · S12-Q2:提4/冲8
- S13-F1:13跳 · S13-K1:0 · S14-F1:提4/2跳 · S16-K1:24跳/+probe2 · S17-F1:48跳
- S18-F1:6跳/+probe39 · S19-F1:0（35行`high`未采纳，见下）
 W 卡：
- W173_layer_add:39跳/+probe2 · W174_dirty80:40跳 · W175_global8871:+probe15
- W176_place81(PASS):4跳/+probe8 · W177-B:冲2/+probe3 · W177-C:+probe8 · W177_live_place:+probe15 · W178_guards(PASS):+probe31
- **合计**：提级109 / 新冲突76 / +cov2 / +probe处理124（其中**12行本次新落盘**，其余112行 M1 已预路由按重复跳过）。

## 未合入 / 拦截（均记录，未盲目降级）
- **FAIL/无 VERDICT 卡：0**。
- **§966 保护**：65 次提级请求被拦（UNSOURCED_PROVED 41 + PENDING 降级项，含 `004C9150`/`0071F8C0`/`0046B540`），保留原低 grade；**需 Lead 裁决**。
- **S19-F1 35 行 grade=`high`**：`high` 是分类置信度（§9 与 `[已证]` 正交），非合法 grade，不采纳提级；**需 Lead 裁决**。
- **点名降级 3 条**（均 `[已证]→[未证]` 写 PENDING）：`00414B9E`(S10-K1，RTTI 链失效误标、call site→probe)、`0000021C`(W177-B，证据仅散文)、`0000030C`(W177-B，evidence 文件不存在)。

## 行数 / grade 分布变化
| 指标 | 前 | 后 | Δ |
|---|---:|---:|---:|
| coverage 数据行 | 14,493 | 14,495 | +2 |
| `[已证]`/`[静态推断]`/`[未证]` | 1022/6238/7233 | 1125/6186/7184 | +103/−52/−49 |
| conflict=1 / S22 行 | 90/6240 | 146/6240 | +56/0 |
| CONFLICTS / PENDING / probe data | 156/79/112 | 232/82/124 | +76/+3/+12 |

> grade 校验：+103−52−49=+2（=新增2行），无凭空增行。提级 60×`[静态推断]→[已证]`、43×`[未证]→[已证]`、6×`[未证]→[静态推断]`，evidence_path 均实存。

## PANEL 改动摘要
- 标题/量纲段改 M2 后，`[已证]`1,022→1,125，增「S19-F1 `high` 未采纳」警示。
- 三分母：coverage 14,493→14,495；缺口 约222(222–820)→约220(220–820)，保留「估计值非枚举」。
- 覆盖面板仅更 proved_n/pct 与 TOTAL(1,020→1,121, 7.90%→8.68%)；named_n/doctype_n 不变；S22 补注「proved 上升系既有行提级、非新语义证据，仍不得排名」。C08 注记与全部警示段保留。

## 合规
仅写 `COVERAGE\` 与卡目录 `M2_merge\`；未改台账、未改 `ra2youli\`、未 git commit/push。开工前基线实测与派卡值一致（14,493/1022·6238·7233/conflict90/S22 6240）才覆盖。
