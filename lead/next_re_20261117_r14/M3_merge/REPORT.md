# M3 合并报告（合卡 M3 / m3b）· 2026-11-17

## 1. 实测基线（脚本测得，与 M2 声称逐项一致，未停机）
| 指标 | 实测值 | M2 声称 | 一致 |
|---|---:|---:|:---:|
| coverage.tsv 数据行（去表头） | 14,495 | 14,495 | ✓ |
| 列数 | 8 | 8 | ✓ |
| `[已证]` / `[静态推断]` / `[未证]` | 1,125 / 6,186 / 7,184 | 同 | ✓ |
| `conflict=1` 行 | 146 | 146 | ✓ |
| CONFLICTS.tsv 数据行 | 232 | 232 | ✓ |
| probe_and_data_entries.tsv 行 | 124 | 124 | ✓ |
| S22 行 | 6,240 | 6,240 | ✓ |

**基线 mtime**：coverage.tsv / CONFLICTS.tsv = 17:47:09；PENDING / probe = 17:48:59；PANEL.md = 17:49:31；UNSOURCED_PROVED = 16:32:58。基线全部吻合，故未触发"停机报告"。

## 2. INVENTORY 汇总（`M3_merge\INVENTORY.tsv`，55 卡全扫描）
- **合入卡数 = 22**（PASS 3：S10-K2 / S11-K2 / S15-K2；其余 19 = PARTIAL）；**跳过卡数 = 33**（FAIL 0、无 VERDICT 0）。
- 合入：P0_INITTERM(3922) P0_RESIDUAL_2(20) S05-K1(36) S06-K2(13) S09-K1(5) S10-K2(37) S11-K2(13) S12-K2(23) S15-K2(42) S16-K2(14) S16-K3(14) S17-K2(7) S20-K1(25) S21-F1(12) W177-C(24) W177-D(17) W177-E(4) W177-F(8) W177-G(4) W177-H(5) W177-I(7) W178_PATCH(0 行)。
- **未能合入/跳过**：33 张为 M2 已并表旧卡（C01–C10、S01-V1、S03-K1、S06-K1、S08-K1、S09-F1、S10-K1、S11-K1、S12-Q2、S13-F1/K1、S14-F1、S16-K1、S17-F1、S18-F1、S19-F1、KB-INDEX、W173/174/175/176、W177_live_place、W177-B、W178_guards）——delta entry 已在 coverage，去重跳过；无 FAIL、无缺失 VERDICT 卡。PARTIAL 新卡的 VERDICT 必改项多为卡文档/语义措辞、未写明 delta 行降级，故按原样合入并标「需 Lead 裁决」（见 INVENTORY 理由列）。
- 去重：同 entry 同值跳过 15；delta 内重复 0；同 entry 低 grade 跳过 22；非函数条目入 probe 新 6（另有 38 条与既有 probe 去重）。

## 3. 合并结果
- **冲突数**：CONFLICTS.tsv 232 → **325**（+93 行，69 个 entry；带卡号+两方值，coverage 保留旧值 + conflict=1，未自行裁决）；coverage `conflict=1` 146 → 181。
- **coverage 行数 前→后：14,495 → 18,436**（+3,941，无重复行）。
- **grade 分布 前→后**：`[已证]` 1,125 → **1,281**；`[静态推断]` 6,186 → **6,093**；`[未证]` 7,184 → **11,062**。就地 grade 提级 161 行（grade 高者优先）。
- S22 行 6,240 → 10,170（增量几乎全为 initterm thunk，仍 `[未证]`）。

## 4. P0-INITTERM 单独影响（单列）
- delta 3,922 行：全 S22 / 全 `[未证]` / name=`initterm_thunk_NNNN` / 0 重复 / 审计确认与旧 coverage 交集 0 ⇒ **整类合入**。
- 占本次 +3,941 的 **99.5%**：仅此卡即令 coverage 由 14,495 → 18,417，S22 由 6,240 → 10,162；行数大幅跳增**是正确的**。
- PENDING_CORRECTIONS 86 行、probe 130 行、CONFLICTS 325 行中**无一条来自 P0-INITTERM**（全 `[未证]`、无 grade 越级、无证据缺失）。VERDICT 的三项必改均针对卡文档（159 项写 vptr、结构定理表述、分桶窗口），不涉 delta 行；delta 本身审计判「交付质量合格」。

## 5. PANEL.md 改动摘要
- 路径：`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\PANEL.md`。
- 保留全部警示段（量纲不可混用 / S22 不得参与排名 / C08 注记 / 已知不完整处），仅更新数字。
- **新增双口径 named 列**：`named_pct_L`（name 非空且非 `sub_` 开头）与 `named_pct_S`（再排除 `Class::sub_`），两列均出；TOTAL L=7,150(55.36%)、S=7,142(55.30%)。
- 分母按 R14-R15 终稿并列 **A 12,916 / B 14,487 / C 18,431**；运营文件实际 18,436（比 C 多 5 = S12-K2 3 + W177-D 2）。旧估计值已全部撤除，PANEL 内不再出现。
- atlas 内 `[已证]` 1,121 → 1,274；面板 22 行 proved_n 已按新表重算。

## 6. M2 审计四项必改落实
1. **提级分解 109(60/43/6) → 107(58 静态→已证 / 43 未证→已证 / 6 未证→静态)**：已按复算值写入本报告与 PANEL 文字说明，**未改 coverage.tsv**。
2. **`004F8440`（S16-K1）**：由 `[已证]` 降 `[静态推断]`，语义加注"每 Super 恰一次已证/每帧未证"；已写 PENDING_CORRECTIONS.tsv（source=M2-audit）。
3. **UNSOURCED_PROVED 理由句**：「任何 delta 均未断言 `[已证]`」**撤回**，改写为——被拦 42 项中 **24 项证据文件确含该地址（S09-F1 21 / S18-F1 3）**，交 Lead 重裁。该文件在写域外，未在盘面修改，仅于本报告与 PANEL 声明撤回。
4. **`0000021C`**：probe 表内仍 `[已证]` 但 PENDING 记 applied 的矛盾已订正——probe 降 `[未证]`，PENDING 注明 M3 订正；另补记 S19-F1 3 行 `medium` 入 PENDING；`00414B9E` 语义改用 §965 更正文本（`AircraftClass::Mission_Hunt → Attack`，非 Guard→Attack）。

## 7. 证据校验 / 边界
- `[已证]` 行 evidence_path 三基点（card 目录 / r14 根 / 项目根）解析：本轮无"[已证] 但文件不存在"行（0 降级）；带限定 token（`[已证·复用]` 等）归一并登记 PENDING 待裁。
- 未 git commit；写域外文件（台账、`ra2youli\`、UNSOURCED_PROVED.tsv）一律只读未改。
