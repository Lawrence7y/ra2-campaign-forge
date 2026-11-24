# _hp_APPENDIX_FINGERPRINTS —— 附录：源件清单与指纹（全部 hashlib 实算）

实跑命令：`python -I -X utf8 D:\Project\ra2-campaign-forge\lead\handoff_pack_20261109\_hp_fp_verify.py`（本轮，写域内新建只读脚本）。
结果：**14/14 与编排方实跑指纹逐字节一致**；COUNTERPART_FIX.md ABSENT（符合编排方 MISSING）；受核件 MATRIX_DEFECT_REACHABILITY.md 为本包补登记（不在编排方指纹表内）。

## A. 编排方指纹表 14 件（本轮实算值）

- 被核对象 SHA256 = b1231ccb8b80c5200e2ff33b15e09ae52b0452a1481dfc7989730f7da16eda5b，字节数 = 22048（lead/v2_precision_fix_20261108/V2_PRECISION_FIX_PROPOSAL.md）
- 被核对象 SHA256 = 4aef8957094008262d980640836ab0aec3e797f892b25fe8ff02b6aa87957fe4，字节数 = 7966（lead/v2_precision_fix_20261108/_pf2_findings_20261109.md）
- 被核对象 SHA256 = 6f2b3009b0de33bbe6a3f61e7a0e1c9b6e7e20215ea9c94a45f4c52479811ae8，字节数 = 29818（lead/matrix_row5_20261109/MATRIX_ROW5_COUPLING.md）
- 被核对象 SHA256 = 75a0369b97f72f9d615ced86c580c6e63bfcce4f29de1c86bd74e8542aa5c895，字节数 = 19552（lead/w2_samecause_20261109/W2_SAME_CAUSE.md）
- 被核对象 SHA256 = 441b073a39a2ac195d90d43e3ba85f3c2202d5fafce31bec9c96e000a01e0923，字节数 = 25095（lead/text_fix_unified_20261109/_uf_UNIFIED_FIX_LIST_20261109.md）
- 被核对象 SHA256 = ce89f6463d1b2fb64deae55f869db4d94086bcb4bce868cec3870317b2c63bf3，字节数 = 2525（lead/u5u6_mirror_20261109/_m5_cells.json）
- 被核对象 SHA256 = f320a80110806e6b57281988085d40776b43e719123db29cdb6564fe68c6c545，字节数 = 24897（lead/u5u6_mirror_20261109/U5U6_MIRROR_TEXTS.md）
- 被核对象 SHA256 = 3a4b1bb7cf7f0bd501b3e99d575c4907dd0e17f5557dd0b8826e5fb07fe2bdc8，字节数 = 23798（lead/strict_exposure_20261109/STRICT_EXPOSURE.md）
- 被核对象 SHA256 = 1d4ccc937cfa78f1ac5144c15fd3e87152e45d41565bf5031bde53202667e016，字节数 = 3558（lead/b2b_design_20261106/STATE_MATRIX.json）
- 被核对象 SHA256 = 565771d8b31c516dc7a1e0100ea047484406a203390492df9f57170a6532feaf，字节数 = 66735（lead/b2b_design_20261106/B2B_DESIGN.md）
- 被核对象 SHA256 = c7bcf035920234bdc66ec410564b296d4c18b62008dd5653ba76a26a38f10801，字节数 = 28897（lead/n4_yi_final_20261108/_n4v2_B_EXECUTION_SPEC_V2.md）
- 被核对象 SHA256 = 3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7，字节数 = 52419（lead/PENDING_DECISIONS.md）
- 被核对象 SHA256 = 2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede，字节数 = 759518（lead/GOAL_THREE_TARGETS_20261018.md）
- 被核对象 SHA256 = （ABSENT/MISSING），字节数 = 0（lead/counterpart_fix_20261109/COUNTERPART_FIX.md——域内实存三件：`_cf_enum_counterpart.py`、`_cf_enum_out.txt`、`_cf_fp_check.py`）

## B. 本包补登记（编排方指纹表之外）

- 被核对象 SHA256 = cd03a91aac610cd0e7d6f3c70008d5a8d351896173aa0ee9d5d035675f2746d6，字节数 = 27825（lead/matrix_reach_20261109/MATRIX_DEFECT_REACHABILITY.md——U8/U9 目标件；与 w2 域 _w2w_fp9.py 及 _uf 清单 §0 所记同值）

## C. 源件 → 条目出处索引（九条改文的唯一正本行）

| 条目 | 改文正本（文件:行） | 目标（文件:行） |
|:--|:--|:--|
| U1 | V2_PRECISION_FIX_PROPOSAL.md §3.5:104（变体：_pf2_findings_20261109.md:27） | _n4v2_B_EXECUTION_SPEC_V2.md:91 |
| U2 | V2_PRECISION_FIX_PROPOSAL.md §4.5:193（row5:131 明写「原样」采同文） | STATE_MATRIX.json:2 |
| U3 | MATRIX_ROW5_COUPLING.md:132（追加注记 + 追加后全文） | STATE_MATRIX.json:5 |
| U4 | MATRIX_ROW5_COUPLING.md:135（加句；拼接点推荐 = _m5_cells.json json4_new_recommended） | STATE_MATRIX.json:4 |
| U5 | _m5_cells.json U5（起草）＋ U5U6_MIRROR_TEXTS.md §3.1（成文交付） | B2B_DESIGN.md:148 |
| U6 | _m5_cells.json U6 ＋ U5U6_MIRROR_TEXTS.md §3.2 | B2B_DESIGN.md:151 |
| U7 | row5:135 同句 ＋ _m5_cells.json U7 ＋ U5U6_MIRROR_TEXTS.md §3.3 | B2B_DESIGN.md:150 |
| U8 | W2_SAME_CAUSE.md §5.2:122（引用块提案） | MATRIX_DEFECT_REACHABILITY.md:154 |
| U9 | W2_SAME_CAUSE.md §5.2:124（建议注记） | MATRIX_DEFECT_REACHABILITY.md:146 |

汇总/旁证件（非改文正本，供交叉核对）：`_uf_UNIFIED_FIX_LIST_20261109.md`（25095）、`UNIFIED_TEXT_FIX.md`（42172，ec0fb8ec47cfb71be5b28bc8a76f9152a6cbd377e741e7be1902a0958fbba154——本包未实算，值转引 U5U6_MIRROR_TEXTS §2.1 表 6）、`STRICT_EXPOSURE.md`（STRICT/LOOSE 暴露面）、counterpart_fix 三件（对比仿真）。

## D. 本轮实跑记录（本会话，全部可复现）

1. `python -I -X utf8 D:\Project\ra2-campaign-forge\lead\handoff_pack_20261109\_hp_fp_verify.py` → 14 OK + ABSENT + EXTRA_OK（见 A/B）。
2. `python -I -X utf8 D:\Project\ra2-campaign-forge\lead\u5u6_mirror_20261109\_m5_mirror_check.py`（现状态，只读）→ `结论（现状改前）: 3/3 PASS`（结构门禁①②＋is_new + 14 行 condition 逐行并列取证）。
3. `python -I -X utf8 D:\Project\ra2-campaign-forge\lead\u5u6_mirror_20261109\_m5_mirror_check.py --after`（内存模拟，不落盘）→ `结论（--after 内存模拟）: 6/6 PASS`（含白名单外零残差、「跑后任意」双侧清零）。
4. `grep -n "W2\|同一持续根因\|罕见" lead/matrix_reach_20261109/MATRIX_DEFECT_REACHABILITY.md` → 命中 :1/:12/:71/:77-90/:146/:147/:154/:180（定位 P10 之 :90 与 U9 对照格 :147）。
5. `grep -n "B2B_DESIGN.md:14[0-9]|B2B_DESIGN.md:15[0-9]|STATE_MATRIX.json:[0-9]" lead/n4_yi_final_20261108/_n4v2_B_EXECUTION_SPEC_V2.md` → 0 命中（V2 无行级引用，第二步(b) 结论）。
6. `grep -n "U5\|U6\|U7" lead/text_fix_unified_20261109/UNIFIED_TEXT_FIX.md` → 定位 :21/:93/:157-186/:235-236/:250-257/:273/:294（确认两汇总件对 U5/U6 如实标「未提供」、镜像正本时间线）。

未跑项（如实登记）：T1/T2/T5 门禁、B2B §2 表程序化逐字 diff、两台账关键词复查、U8/U9 他件绑定检索——见 `_hp_PENDING_AND_SIGNOFFS.md` C 节。
