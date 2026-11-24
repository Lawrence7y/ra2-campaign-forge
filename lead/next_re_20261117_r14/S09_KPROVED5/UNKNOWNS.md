# S09-KPROVED5 UNKNOWNS

## U1 · 已并入 22 行 vs 4 张 prior delta 的 27 entry —— 口径核对（已解决）
任务给定「已并入 22 行」。从 S09_KPROVED / 2 / 3 / 4 的 coverage_delta.tsv 逐张读出 entry 共 **27 个互不重复**。
交叉 `COVERAGE\coverage.tsv` 现态 grade：其中 **22 个为 `[已证]`**（=真已并入），**5 个仍为 `[静态推断]`**（未落盘）：
`004E2830`(GaugeClass::slot31)、`00565B00`(MouseClass::slot23)、`0069DEB0`(ShapeButtonClass::slot27)、
`006A7D70`(SidebarClass::slot54)、`00723EC0`(ShapeButtonClass::slot31)。
→ 已并入 22 行 = 这 22 个 `[已证]` 项；5 个 `[静态推断]` 项未并入。为彻底避免重复提交，本卡把**全部 27 个** prior-delta entry 都从候选池剔除，
另剔除 `00654320`（③a）与 `0069DEB0`（细则#1 不达，已在 27 内）。证据：`work/build_pool.py`、`work/check_merged_grade.py`。

## U2 · 候选池口径
S09 A 集合（②仅RTTI ∩ ④严格档）= **103 行**，其中 direct-call 口径 **102**、livevt-only **1**（`004F4240` MouseClass::slot0）。
剔除 27 prior-delta + 00654320 后、限 direct-call 口径的合格池 = **74 行**（全部 `[静态推断]`）。
本卡只在这 74 行中选 8 行。livevt-only `004F4240` 无 direct-call 站点，本卡不取（其 ④ 为 livevt，与任务「严格直调口径」不符）。
证据：`work/build_pool.py`、`work/A_set.json`、`work/s09_A_eligible.json`。

## U3 · ③b 判为不成立 / 未选的候选（理由）
| entry | 不选理由 |
|---|---|
| `0063F730` PowerClass::slot7 | S4 检测器假阳性：函数是无分支的字段清 0/置 -1（+0x0013..+0x0069），属 D-42 ③a「清零+置默认值」，无 ≥2 vt 写亦无 ≥10 字段布局断言的构造语义，不满足 ③b。 |
| `006A5BF0` SidebarClass::slot50 | 24 道 guard 全部执行同一动作（free 指针 0x7c8b3d + 清标志），仅全局地址不同 —— 违 D-42 细则#1「各闸动作不同」，与黑名单 `0069DEB0` 同型。 |
| `0069DE00` ShapeButtonClass::slot34 | `0069DEB0`（已黑名单）同族兄弟，五模式汇入同一 call 0x4aed70、仅参数不同，细则#1 不达。 |
| `005576A0` ListClass::slot34 | S6 检出但真支多为同构字段搬移，未满足「各闸被调目标互异」的可证伪多支，保守不取。 |
| `005BDC80` MouseClass::slot19 / `004F4480` 之外的低 jcc 行 | ③b 信号弱（仅 S5 loose 或无），③a 嫌疑，不取。 |

以上均未进 delta；其余 74-8 行或未入选、或 ③b 仅 loose/③a，不逐一列。

## U4 · ③b 基率口径
population = S09 全部 629 行（`[静态推断]` ∩ atlas）；随机不放回抽 8 行，seed=20261119，2000 次。
strict 基率 = 123/629 = 0.195548；loose 基率 = 144/629 = 0.228935。
`K = draw_size × mean_per_row` 是恒等式（M3/判据3），不作校验；本卡只报上列基率作证据。
证据：`work/baseline.py`、`EVIDENCE/BASELINE_3B.json`、`EVIDENCE/BASELINE_3B.txt`、`EVIDENCE/BASELINE_3B_FEATURES.tsv`。

## U5 · 未做真机 / 只读约束
本卡为纯静态只读分析：未运行 gamemd.exe、未改任何游戏文件、未建 venv、未 pip install、未 git commit。
目标 SHA-256 前缀 73201CC0 / 后缀 F67476（`s09lib.py` 加载 exe 只读）。
