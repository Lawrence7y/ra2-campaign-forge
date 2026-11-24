# fabricated.md · A1「来源里根本没有的论断」清单

判定口径：**statement 或 limitations 的关键论断，在其 evidence_paths 指向的来源里找不到对应原文/字节**，且不能由来源的算术或同义重述直接得出。只要能在来源里逐字或逐项对上（含同一数字不同排版），不计入。

## 结论：凭空论断 **0 条**

33 条（F17–F49）逐条比对了 statement 与 limitations 的每个可核对论断：无一条出现「来源里根本没有」的论断。逐条依据见 `trace33.tsv` 的「A1_依据」列。

## 有据但「出处/归属」有偏差的 3 处（不计凭空，但引用时须改）

| # | fact_id | 论断 | 来源实际状态 | 处置 |
|---|---|---|---|---|
| O-1 | F32 | limitations：「§8.1 错源19 支撑『绝对寻址 + 基址加载两种形式都要看』」 | §8.1 错源⑲ 是 *capstone `op.index` 陷阱*，与访问形式无关；「访问形式三种：绝对 / reg+off / 基址全局→[reg+idx*4]→[reg+off]」出自 `HANDOFF_R14_R3.md` 九 | 把出处由「§8.1 错源19」改为「HANDOFF_R14_R3 九」；「lea 中介 0 处」仍由 LEAD_LOCK / GOAL §1049 N9 支撑，结论不变 |
| O-2 | F35 | limitations：「M44 双列裁决 段」承载 `proved_strict` 定义 | `proved_strict` 定义在 PANEL L27 / L51 / L95（「严格口径双列表」）；M44 段是 M44 并表说明 | 改为「PANEL L27/L51/L95（严格口径双列表）」 |
| O-3 | F23 | limitations 的「宽松子串 direct call 命中 12 行 / 减法读法多计 10 / 集合差 9 / 6 行为否定式 / 真多计 3 行」 | `DELIVERY_SUMMARY.md` 无此明细；limitations 的 evidence 指向 PANEL M94 注记。**本审计未逐行复核这条子串统计**（超预算） | 记为 **未复核项**，不作 DISAGREE；建议在 limitations 注明「12/10/9 出自 PANEL M94 注记，非 §2 正文」 |

## 需一并注意的两处「陈述不完整」（非凭空）

- **F18**：statement 只写「8 用例逐例判定，A/B/C/E 每例均存在 ≥2 种解释」——`CASES.tsv` 实有 D（不可构造）与 F（未做）两例，A 组解释数为 **3**、B/C/E 为 **2**；数字与判据成立，但「每例 ≥2」对 D/F 不成立（该两例本就是判据不可执行）。建议补「D 判据无法执行、F 未做」。
- **F24**：statement「R_MISSING 0」成立，但同一 R_OK 863「自行复算」体量（1,654 行、791/863 分桶）在 `DELIVERY_SUMMARY` 标「自行复算」，可复核性依赖 `EVID_RESOLVE/resolve.py` 定义；**本审计未复算 863/791**（超预算），只核了 863/1,654 = 52.176% → 52.18% 与 §2 表逐字一致。
