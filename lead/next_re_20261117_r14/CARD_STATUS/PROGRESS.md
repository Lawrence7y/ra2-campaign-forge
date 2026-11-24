# CARD_STATUS PROGRESS — next_re_20261117_r14

- 扫描卡目录：85（规则：排除 `_` 开头与 `C0*_census`；只读其它目录）
- 裁决分布：PASS 8 / PARTIAL 65 / FAIL 3 / NO_VERDICT 9 / AMBIGUOUS 0
- 裁决方法：仅用行首/加粗标签、表格单元格、文首/文末独立短行；负语境（不判/避免/否则）剔除。全文正则只用于复现旧误判，不作为裁决依据。
- AMBIGUOUS 列表：无（无两条结构判据冲突）
- 并入判定：按 delta entry 在 COVERAGE/coverage.tsv 中查 name+grade；grade 归一化 已证/[已证] 等同；0 数据行视为已并入（无增量）

## 未并入但可并入：50 卡，delta_rows 合计 2290
  C10_census(1288)；P0_RESIDUAL_2(21)；S01-K2(9)；S01-V1(8)；S02-K2(5)；S03-K1(16)；S05-K1(37)；S06-K1(20)
  S06-K2(14)；S06-K3(2)；S08-K1(19)；S09-F1(31)；S10-K1(37)；S10-K2(37)；S10_K4(19)；S11-K1(48)
  S12-K2(24)；S12-Q2(11)；S13-F1(21)；S13-K1(20)；S13-K2(8)；S13_K5(6)；S14-F1(7)；S15-K3(3)
  S16-K1(29)；S16-K2(15)；S16-K3(15)；S17-F1(50)；S17-K2(7)；S17-K3(1)；S18-F1(65)；S18-K2(4)
  S19-F1(39)；S20-K1(26)；S21-F1(12)；W173_layer_add(54)；W174_dirty80(83)；W175_global8871(20)；W176_place81(21)；W177-B(14)
  W177-C(25)；W177-D(18)；W177-E(5)；W177-F(9)；W177-G(5)；W177-H(6)；W177-I(8)；W177_live_place(16)
  W178_PATCH(1)；W178_guards(31)

## 原先被全文正则误判的卡（旧Matcher vs 真实结构裁决）
  M2_merge: PASS→PARTIAL；M3_merge: FAIL→PARTIAL；P0_GATE: PASS→PARTIAL；S03-ADJ: PASS→PARTIAL；S06_K5: PASS→PARTIAL；S10_K4: FAIL→PARTIAL
  S14-F1: FAIL→PARTIAL；S15-K2: FAIL→PASS；S17-K2: PASS→PARTIAL；S17-K3: FAIL→PASS；W175_global8871: FAIL→PARTIAL；W176_place81: FAIL→PASS
  W178_PATCH: PASS→PARTIAL

## 指定四张卡的真实裁决
- S14-F1：PARTIAL — L46「## 八、裁决：**PARTIAL**」
- S15-K2：PASS — L36「## 裁决：**PASS**」
- W175_global8871：PARTIAL — L29「## 裁决：PARTIAL」
- W176_place81：PASS — L43「## 四、裁决」+ L45「**PASS**。三条核心结论全部经三通道独立复算完全一致，无应降级项。」

## 交付
- STATUS.tsv：85 卡全量状态；MERGE_QUEUE.tsv：仅 mergeable=Y，按卡号排序，无表头。
