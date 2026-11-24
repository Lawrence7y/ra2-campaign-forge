# M5 合并卡 REPORT（合并员 M5 · 2026-11-17）

依据：`M4_merge/_audit/VERDICT.md`（34 行，裁决 PARTIAL）点名的必改项。写域仅 `COVERAGE\` + 自建 `M5_merge\`；改前 4 文件已备份至 `M5_merge\_backup\`；未 git commit。

## ⑴ UNSOURCED_PROVED.tsv 理由句（改 3 行）
- 全表 41 行逐行对 coverage.tsv 实际 grade：38 行实为 `[未证]`、理由"已降 `[未证]`"一致；仅 3 行实为 `[静态推断]`、理由失真。
- 改 `004AB9B0`/`006AAD00`/`006ABD30`：理由"已降 `[未证]`"→"已降 `[静态推断]`（当前档位见 coverage.tsv；有 E03_vtable_slot_semantics.txt 可核）"。entry/grade/action 列未动；CRLF 42/42 保持。
- 理由句 `[静态推断]` 档 0→3、`[未证]` 档 41→38。

## ⑵ W177-C 11 条不足证据 `[已证]`（降 10 + 登记 11）
- 自核：6 条仅探针脚本（work/*.py）、2 条恒 0 读数（B02 cam_x/y=0）、1 条自相矛盾（`000001AC` 卡面 u32=0 vs 证据 512）——均不满足硬规矩①字节级②独立复算；另 2 条（`0087F7E8`/`00000520`）仅 m13_ingame.json 运行时观测，非字节级/独立复算，a-M4 亦判"该批不得用作 `[已证]` 依据"。⇒ 11 条全降，**无反驳**。
- probe 实际改 10 条：8 条→`[静态推断]`（0087F7E8/000001AC/000009C/000000A0/00000520/A8EB50/B0F724/B0F730）；2 条→`[未证]`（00886FA0/00886FA4，恒 0 且疑非本 build 有效地址）。
- `00000030` 盘上确为 `[未证]`（probe W177_live_place 行），未改盘、仅登记更正。
- M4 "14/14" 偏宽：00000030 未落地 ⇒ 按"登记落地"为 **13/14**；按 a-M4 ★E"盘上 grade 与映射一致"仅 **10/14**（另 3 行 coverage 属"保留高者"非 M4 升格）。
- PENDING 新增 11 行（原 `[已证]`→新 grade + 降级理由 + 引 a-M4 VERDICT L25/29）。

## ⑶ probe 非标 token 归一（15 行）
- 定位 15 行裸 `已证`（全 W175_global8871，probe 第 11–25 行）。
- 逐行核 evidence：均为反汇编/原始字节级读写入指令（t1_callsite、t1_cleanup、t2_disp、t2_doublechannel、t3_final_verify、t3_bytechannel_full、t3_global_writes、t2_ini_readers），imm32/指令边界可独立复算 ⇒ 归一为 `[已证]`，保留。
- PENDING 新增 15 行（含 evidence_path）。probe 裸 token 15→0。

## ⑷ "69 个 entry" → 46
- PANEL.md:74 直接改 69→46（写域内，已改）。
- M3_merge/REPORT.md:23 同为 69，但在写域外，**未改**；已在 PENDING 新增 1 行登记"该处应更正为 46，待后续卡更正"。

## 数值汇总（前→后）
| 项 | 前 | 后 |
|---|---|---|
| coverage.tsv 行数 | 18,431 | 18,431（不变） |
| coverage.tsv `[已证]`/`[静态推断]`/`[未证]` | 1,278/6,091/11,062 | 1,278/6,091/11,062（不变） |
| probe 行数 | 132 | 132（不变） |
| probe `[已证]` | 45 | 50（+15 归一 −10 降级） |
| probe 裸 `已证` | 15 | 0 |
| probe `[静态推断]` | 61 | 69 |
| probe `[未证]` | 11 | 13 |
| PENDING_CORRECTIONS 行数 | 105 | 132（+27） |

注：任务书预期"`[已证]` 1,278→约 1,267"基于"11 条在 coverage.tsv"的前提；实测该 11 条全在 `probe_and_data_entries.tsv`，coverage.tsv 的 `[已证]` 不受影响，故维持 1,278。未擅自改 coverage.tsv 的 grade 凑数。
