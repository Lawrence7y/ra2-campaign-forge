# _la_SUMMARY.md — 入账核对员·GLM 四笔待入账项核对汇总（本写域索引；本文件不是台账、不入台账）

- 日期：2026-11-08。任务：四笔上游订正/登记的逐笔核对 + 可整段复制追加的草案正文。
- **台账零改动声明**：`lead/PENDING_DECISIONS.md` 与 `lead/GOAL_THREE_TARGETS_20261018.md` 本任务全程只读（grep/Read/sed 抽行），未改一字；收尾指纹复算见文末「收尾完整性核查」。全部产出仅落本写域 `lead/ledger_appendix_20261108/`，均 `_la_` 前缀；未 commit、未 push；零真机、零采样代码。

## 四笔结论与草案索引

| 笔 | 对象 | 核对结论 | 草案件 | 建议入账位置（暂编节号，Leader 可重排） |
|---|---|---|---|---|
| 1 | N-9:205「P6 静态 u64 窗口读可闭」前提勘误（[0x7E1738] 真 / [0xB0CD48] 假 → P6 改「半闭半开」） | **成立** | `_la_draft1_n9_p6_erratum.md` | GOAL_THREE_TARGETS 尾部新节 §605；锚点 = STATIC_COUNT_SPEC.md:205（**非** NEXT_STEPS） |
| 2 | D 维 O4 订正（necessaryCount=3，O4 非必要被 O2 蕴含；最小集改 O1–O3） | **成立** | `_la_draft2_o4_necessity.md` | GOAL_THREE_TARGETS 尾部新节 §606；D-13 状态行不动、不改 PENDING_DECISIONS |
| 3 | §604「空档/空档差」缺口列复算（时长列复现、两列不可复现、复算 15 窗全正） | **成立** | `_la_draft3_s604_gapdiff.md` | GOAL_THREE_TARGETS 尾部新节 §607（锚点 §604 :9704-9729；原文修订与否由台账所有者裁决） |
| 4 | 「以乙替代甲」补登（九 hunk + 四项分支差异 + 11 件指纹 + 四条未完成生效条件） | **成立（附两条引用限定，已写入草案）** | `_la_draft4_yi_supersede_jia.md` | GOAL_THREE_TARGETS 尾部新节 §608；不进 PENDING_DECISIONS（非待裁项） |

**confirmedCount = 4**（四笔事实基础均在现盘成立）。

## 基线指纹（追加前基线，两条——每份草案正文均载）

- `lead/PENDING_DECISIONS.md` SHA256 = `3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7`（382 行口径；52419 B；本会话实测 splitlines=381/newlines=381——文件末尾带换行，「382」为含末尾空段的计数口径，字节与哈希两口径完全一致）
- `lead/GOAL_THREE_TARGETS_20261018.md` SHA256 = `2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede`（759518 B；同上口径注：实测 splitlines=9757，含末尾空段口径 9758）

## 被核对象绑定（复核回件要件：SHA256 + 字节数，本会话 hashlib 实算）

| 被核对象 | SHA256 | 字节数 |
|---|---|---:|
| lead/static_spec_n9_20261107/STATIC_COUNT_SPEC.md（笔1 主对象） | 5b933fe2fcb3cc35c5026cb57b45f29da29c90b67a618346af248744ed3ccdb9 | 32281 |
| lead/n9_erratum_20261108/N9_SPEC_ERRATUM.md（笔1 依据件） | 61446db581a273725010e9b09cf3ebeba0d1412fc8666c0c6b8c660e4f7d22b4 | 20630 |
| lead/d_o1o4_necessity_20261108/O1_O4_NECESSITY.md（笔2 主对象） | d4ac0f28c108986b7037b2315a796766d7ed5d8212bce6f3c08af815310b1661 | 35637 |
| lead/slowframe_r3_20261108/S604_GAP_RECHECK.md（笔3 主对象） | 5d1b0ecc9f0e21ddecc38584c363afa0c758f40089ccc57749f237aeffbdf726 | 19291 |
| lead/b2b_yi_supersede_20261108/YI_SUPERSEDE_JIA_BINDING.md（笔4 主对象） | 255356ca789955cc2c084388f547a1435feb310f210617b988f761e7ff331c7b | 7344 |

其余绑定件（笔1 勘误登记件 41479540…/15794；笔2 被核对象 bb61eedb…/18262 与 _d14_ 三件；笔3 SLOW_WINDOW_LIMITS e7c29e06…/23707 与 _r3_ 五件；笔4 §4 表 11 件）全部本会话实算 MATCH：`_la_fpcheck.py`（12 件）+ `_la_fpcheck2.py`（23 件，SUMMARY 23/23 MATCH），输出存 `_la_fpcheck_out.txt` / `_la_fpcheck2_out.txt`。

## 本会话独立复跑（三件，全部逐字节同哈希）

| 复跑 | 命令 | 输出绑定 | 与存档关系 |
|---|---|---|---|
| 笔1 PE 结构判定 | `python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/n9_erratum_20261108/_er_report_pe.py"`（EXIT=0，stdout 重定向至写域） | `_la_er_pe_rerun_out.txt` = ac2d247600ab098c98e042359353e29978cf711f4c83a85881ec472c2bcb1a58 / 6908 B | 与存档 `_er_report_pe_out.txt` **同哈希** |
| 笔2 O1–O4 语料重算 | 写域副本 `_la_d14_recompute_copy.py`（仅改 OUT 路径），`python -I -X utf8` EXIT=0 | `_la_d14_recompute_out.txt` = 9270cbb8…/2456 B | 与存档 `_d14_recompute_out.txt` **同哈希** |
| 笔3 §604 空档差复算 | 写域副本 `_la_r3_recompute_copy.py`（仅改 OUT 路径），`python -I -X utf8` EXIT=0 | `_la_r3_recompute_out.txt` = f1f55791…/9494 B | 与存档 `_r3_recompute_out.txt` **同哈希** |

（笔4 无需脚本复跑：`git diff --no-index --numstat` = 255/13、`grep -c "^@@"` = 9、`grep -c "_finish("` = 14 已独立复现；母本指纹复算 MATCH。）

## 附带核对记录

- `lead/NEXT_STEPS_20261106.md` 实测 **不存在**（MISSING，与编排方指纹清单一致）；计划件实为 `lead/nextstep_plan_20261106/NEXT_STEPS_20261106.md` = 27225 B / 135 行（实算），与笔1 无关。
- 台账锚点亲读：PENDING_DECISIONS.md:20-88（待裁决段现仅 D-13/D-14 两项，D-13 状态行 :22-27）；GOAL_THREE_TARGETS:9687-9757（§604 全节）、:9535/:9613（edge 口径双锚点）；两台账内均无 0xB0CD48/静态 u64/乙替代甲/H01 既有登记（grep 0 命中）——四笔确均未入账，无重复登记风险。
- 笔4 引用限定两点（未补造）：①YI §1 引文在裁决书 grep 0 逐字命中（实质内容在 :23/:62/:66 有对应裁定）；②RULING_DIRECTION.md 整体 unconfirmed、Q1=待有权签发人确认的方向意见。
- 行数口径注：编排方所载 382/9758 行与本会话实测 381/9757（splitlines/newlines）系「含末尾空段」计数口径差，字节与 SHA256 完全一致，不影响指纹效力。

## 收尾完整性核查（收尾实测，证明台账零改动）

收尾重跑 `_la_fpcheck.py` 结果（与开工首跑逐位一致）：
- `lead/PENDING_DECISIONS.md` = `3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7` / 52419 B
- `lead/GOAL_THREE_TARGETS_20261018.md` = `2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede` / 759518 B
- 两条台账指纹开工/收尾同值 ⇒ 台账零改动坐实（指纹口径，非 git diff 口径）。

## 本写域产物清单（全部 `_la_` 前缀）

`_la_SUMMARY.md`（本件）、`_la_draft1_n9_p6_erratum.md`、`_la_draft2_o4_necessity.md`、`_la_draft3_s604_gapdiff.md`、`_la_draft4_yi_supersede_jia.md`、`_la_fpcheck.py`、`_la_fpcheck_out.txt`、`_la_fpcheck2.py`、`_la_fpcheck2_out.txt`、`_la_fpcheck_rerun_out.txt`、`_la_er_pe_rerun_out.txt`、`_la_d14_recompute_copy.py`、`_la_d14_recompute_out.txt`、`_la_r3_recompute_copy.py`、`_la_r3_recompute_out.txt`。

——核对完毕。**零真机、零采样代码、台账零改动、未 commit、未 push。**
