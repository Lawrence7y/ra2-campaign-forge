# M29 PROGRESS — 并入 a-S08-K1 认证的 2 行（只升 grade，名字一律不动）

## 结论
- 并入行数（applied）：**2**（004309D0、0047F250；仅第 5 列 grade 提级，其余 7 列逐字节不动）
- `[已证]` 前后值：**1,456 → 1,458**（+2）
- S08：proved **1 → 3**（3/22=13.64%，门槛 11，差 8）；**named 未变（19）**（named(S-R14) 19/22=86.36%、strict 0/22=0.00%）
- coverage.tsv 行数：**18,431 → 18,431**（数据行不变，无新增/删除 entry）
- `conflict=1`：**254 → 254**（本卡不新增 coverage conflict 标记）
- coverage 前后 SHA-256：
  - 前：`b1089f63e3fc180e35c5a4b7f5036d8ece63af1f5a1ef54856c4f15572f40a59`
  - 后：`d8d9c08c96711b0f259bdae75e6279ef3553ebe077f72bb835e19c97dd16fa00`
  - 备份：`D:/Project/ra2-campaign-forge/lead/next_re_20261117_r14/_hygiene/coverage.M29.bak`（改前字节一致，3,671,333 B）

## grade 直方图（全表 coverage.tsv）
| grade | 前 | 后 | 变化 |
|---|---:|---:|---:|
| `[已证]` | 1,456 | 1,458 | +2 |
| `[静态推断]` | 5,948 | 5,947 | −1 |
| `[未证]` | 11,027 | 11,026 | −1 |
| 合计 | 18,431 | 18,431 | 0 |

- atlas 内 `[已证]`：1,451 → 1,453（两行均在 atlas 内，已实测 function_atlas.tsv 命中）

## 2 行改动（仅第 5 列）
| entry | 盘上 name（保持不动）| 盘上 semantics（保持原样）| grade 前 → 后 |
|---|---|---|---|
| `004309D0` | `sub_004309D0` | `[静态推断] Shroud/Radar member (string/import)` | `[静态推断]` → `[已证]` |
| `0047F250` | `sub_0047F250` | 引用 'FOG.SHP' → 迷雾/可见性/雷达（字符串线索） | `[未证]` → `[已证]` |

> `0047F250` 保持 `sub_0047F250`：a-S08-K1 审计裁定 `Draw_Fog` 不算两通道（YRpp 0 命中、srcs 均 docs/re），**不采纳**；语义栏保持原样。
> **named 未变（19）**：名字一个都没加，S08 named(S-R14) 仍 19/22。

## 校验
- coverage.tsv：18,431 数据行；表头逗号、数据行 TAB（8 列）保持；仅第 966、1806 行的第 5 列变化，其余逐列零差异（name / semantics / evidence_path / n_sources / conflict 全部 UNCHANGED）。
- 两行在 atlas 内（function_atlas.tsv 命中）；备份完成且字节一致；未建 venv、未 pip install。
- PANEL.md 已更新 S08 段（proved 1→3、named 保持 19）及全表 `[已证]` 计数（1,456→1,458 / atlas 1,451→1,453）。

## 来源
- `M29/CARD.md`（a-S08-K1 = CONDITIONAL PASS；只升 grade，名字一律不动）
