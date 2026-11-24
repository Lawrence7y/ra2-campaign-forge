# S17-K3 · DISAGREE

## D0 · 分母与基线：**无 DISAGREE**
现读盘核实（`work/t1_named_count.py` → `EVIDENCE/t1_named_count.txt`）：
- coverage.tsv 18,431 数据行 / atlas 12,916 数据行，与 HANDOFF/PANEL 权威值一致。
- S17 全表 104 行；S17∩atlas 分母 **102**。
- named_L = **91**（89.22%），named_S = **91**（89.22%）—— 两者相等，因 S17 内 `Class::sub_` 行数 = **0**（我脚本全表扫 `::sub_` 命中 0）。
- proved = **53**（51.96%）。
- ⇒ 与 PANEL.md:49（S17 102/91/89.22/89.22/53/51.96）**逐位一致**，与卡面"91/102、只差 1 个"一致。**无 DISAGREE，不停机。**

## D1 · S16 翻车先例不适用于 S17（口径澄清，非 DISAGREE）
卡面警告「named 的 S 口径排除 `sub_` 与 `Class::sub_`，占位名不算达标」。本卡实测：S17 的 named_L 与 named_S 都是 91，差 1 是**真实少一个具名**（10 个纯 `sub_` + 1 个待定 00431B80），不是 S16 那种 `Class::sub_` 占位造成 L→S 掉 1。补名必须给真实语义（00431B80 已给 RTTI+字节证据），未用占位。

## D2 · 前序卡 K2 的 named=92 预测为何未兑现（解释，非 DISAGREE）
K2 delta 7 行中 6 行名已并入 coverage（0041D6E0/0043A5D0/004B6BB0/0067C690/0055AAC0/00539AE0），唯 00431B80 的名未并：`CONFLICTS.tsv` 有 `00431B80 name S17-K2:BufferIOFileClass::~BufferIOFileClass vs COVERAGE(prior):sub_00431B80`，同 grade [静态推断] → 合并保留 prior。故 K2 预测 92、PANEL 现值 91。本卡以 [已证] 字节级证据重交该名（见 `coverage_delta.tsv`）。

## D3 · T3 证据水分（需 Lead/审计注意，非本卡自改台账）
抽 5 条 [已证]（0041D6E0 / 0043A5D0 / 004B6BB0 / 0067C690 / 006CF240）独立字节复核：
- 前 4 条字节级证据真实（详见 `EVIDENCE/t3_byte_audit.txt`）。
- 第 5 条 `006CF240 Here_I_Am`：grade=[已证] 依据为 YRpp/kb 外部名复用 + 槽位，语义栏自带 [未证]；按硬规矩「复用别人结论不够 [已证]」证据链偏软，建议降级/补字节证据。我独立字节复核其行为真实（非造假）。
- 若该行降级：proved 53→52=50.98%，仍在 50% 线上；不影响 S17 proved 达标结论。
