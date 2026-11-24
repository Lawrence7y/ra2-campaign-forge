# S15-K4 · PROGRESS（S15 触发器逼近 DoD 第 1 条 · 静态）

## 结论表（分母 = coverage.tsv subsystem=S15 ∩ function_atlas.tsv，entry 先统一小写 = 158）

| 结论 | 状态 | 证据路径 |
|---|---|---|
| 现场重算：S15=159 行，表外 006E6080 后分母 158；named(S)=137/158=86.71%；proved=95/158=60.13%；need=143、差 6 | [已证] | `EVIDENCE/t0_baseline.txt`; `work/t0_recompute.py` |
| 与 S15-K3 报的 158/137/95/143/6 逐值一致 ⇒ 不停机、不凑数 | [已证] | `S15-K3/PROGRESS.md`; `EVIDENCE/t0_baseline.txt` |
| 新命名 1：`00726910` = `TriggerClass::GetHouse`，[已证] | [已证] | `EVIDENCE/naming_evidence_k4.md`; `EVIDENCE/verify_named_k4.txt` |
| 新命名 2：`0071FA30` = `TEventClass::GetHouse`，[静态推断]（YRpp 无显式方法地址，字段名+getter+ecx 来源双支撑） | [静态推断] | `EVIDENCE/naming_evidence_k4.md`; `EVIDENCE/verify_named_k4.txt` |
| K3 的 `006E2A10`/`006E2AA0` 本卡不重签：未找到第二条独立“命名”通道，不为凑数复用 K3 结论 | [未证] | `EVIDENCE/source_grep_bare_hex.txt`; `UNKNOWNS.md` U-K3 |
| 其余 19 行保持 `sub_`；逐条不可定原因见 UNKNOWNS | [未证] | `UNKNOWNS.md`; `EVIDENCE/targets_disasm.txt`; `EVIDENCE/vtable_rtti_fixed.txt` |
| 修正版 RTTI 链（COL+0xC→TD，TD+8 为内联名）实测 2,919 个有效 vptr 写点 / 302 类；21 条目标直接虚表槽命中仍为 0 | [已证] | `EVIDENCE/vtable_rtti_fixed.txt`; `work/rtti_chain_fixed.py` |
| 写台账前 grep：主台账无 `TriggerClass::GetHouse` / `TEventClass::GetHouse` | [已证] | `EVIDENCE/verify_named_k4.txt` §3 |

## 核心数字（卡前/卡后）

| 口径 | named(S) | proved [已证] | 门槛/差额 |
|---|---:|---:|---|
| 盘上卡前（coverage 未合任何 delta） | 137/158 = 86.71% | 95/158 = 60.13% | need 143，差 6 |
| 仅合入本卡 2 行 | 139/158 = 87.97% | 96/158 = 60.76% | 仍差 4 |
| 合入 K3 2 行 + 本卡 2 行（跨卡预计） | 141/158 = 89.24% | 98/158 = 62.03% | 仍差 2 |

## 给审计员的复算入口（3 个核心数字）

1. **基线 158/137/95 + need 143**：`python work/t0_recompute.py` → `EVIDENCE/t0_baseline.txt`。
2. **两条新名的双通道**：`python work/verify_named.py` → `EVIDENCE/verify_named_k4.txt`；补充链 `python work/rtti_chain_fixed.py` → `EVIDENCE/vtable_rtti_fixed.txt`。
3. **卡前/卡后/跨卡计数**：`python work/final_recompute.py` → `EVIDENCE/final_recompute_k4.txt`。

写域仅 `S15_K4\`；未改 coverage/台账/游戏文件，未 git commit。
