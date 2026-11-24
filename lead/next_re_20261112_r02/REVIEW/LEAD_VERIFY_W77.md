# LEAD_VERIFY_W77 · v16：EXIT 33 消息产品化（message-only，97/97 回归绿）

> 记录人：Lead｜时间：2026-11-14 07:34｜卡：W77（**GLM-5.3-Flash**，纯离线）
> 交付：`W77_exit33_message_v16\V16_CHANGELOG.md` + `ra2forge_patched_v16\` + `out\`（97 份逐例日志 + SUMMARY + 全量 stdout）

## 1 · 交付验收（我核过实际数字，不是采信自述）

`[本次实测·我亲自读 out\SUMMARY.txt 与 regress_full_stdout.txt]`
```
cases: 97   passed: 97   failed: 0
assertions: 844 passed / 0 failed
inherited v13 cases: 89 | S4 cases: 8 | W60 S5 cases: 6 | W77 EXIT-33 message cases: 1
→ PASS=97 FAIL=0, stdout 无 traceback
```
`[自洽交叉]` v15 基线 96 用例/835 断言 → v16 **97/844**：+1 用例、+9 断言，正是 `W77_1` 的 9 条 check。数字对得上。

`[过程中它崩过一次，自己修好了]` 首次全量跑在 `S3_19` 抛 `FileNotFoundError`（缺只读夹具 `s1_revision\guard_decision_table.json`，W43 有但没复制过来）。它发现后复制夹具、**全量重跑**，最终 stdout 干净。
⇒ **我没有因为"它说全绿"就放行**：我先看到的是崩溃的 stdout（只跑到 S3_18），之后才看到重跑后的绿色结果。这条记录在案。

## 2 · 消息改写成什么样（我读了改前/改后原文）

改后（`stdout` 实测）：
> `error: [INPLACE_OFFICIAL_MISMATCH exit=33] INPLACE_OFFICIAL_MISMATCH: campaign package 'org.ra2forge.w77.alpha' (version 1.0) is already installed in <game>: its install rewrote the official loose BATTLEMD.INI, and this version supports ONE campaign package at a time, so installing another package here is refused BEFORE any write (… sha=…, expected …). To install the new package, first run: ra2forge uninstall --game <game>. Zero bytes written.`

`[签发]` 这条消息现在**直说了真因**（一次只支持一个包）、**指名挡路的包**（从 manifest 读 id+version）、**给了救济命令**（具体到本目录），同时**逐字保留**机器可读件：`reason_code=INPLACE_OFFICIAL_MISMATCH`、`exit=33`、sha 对比、`Zero bytes written.`
`[删掉的两处措辞是对的]` ① `content conflict`（让用户以为"我的文件坏了"）② `W60 rewrites ONLY the official bytes`（内部工件名，不该出现在用户消息里）。

## 3 · 一处它主动披露、我审过后接受的测试改动

`[改动]` `s4_cases.py::case_S4_8` 的 delta 遍历从**整包 rglob 收窄到 `ra2forge/` 子树**（2 行收集器 + 注释）。
`[我看了实际 diff]` 只改了两处 `rglob` 的作用域起点；**断言文本、期望集合 `expected_added`、判定逻辑逐字未动**。
`[为什么我接受]`
1. 该用例三条 check 的自述都是「**source** delta is CLOSED / verify.py UNCHANGED / NO `__pycache__`」—— 它守护的是**源码封闭性**，而新增的是 `docs/` 产品文档，不属源码面。收窄后度量更贴合其名称。
2. **它没有走篡改路线**：改 `expected_added` 加上 docs 条目，等于宣布"v15 的封闭性断言里本来就该有文档"——那是改事实。它明确拒绝了这条路。
3. 边界意识正确：它写明「若 Lead 认为包内文档也算封闭面，正确做法是改 S4_8e 的期望集合（那是 **W60 的裁决权**），本卡未越权」。

`[但仍记一条限制]` 收窄后 **S4_8 不再守护"包根下不得出现任意新文件"**。若将来有人往包根塞文件，这条用例不会报。⇒ 建议 W60 归属方后续把 `expected_added` 显式加上 `docs/ONE_PACKAGE_AT_A_TIME.md`，恢复全包扫描。**已记入台账待办**。

## 4 · 结论口径

`[可以写]` v16 的 EXIT 33 消息已产品化；97/97 用例、844 断言、退出码 0；`docs/ONE_PACKAGE_AT_A_TIME.md` 明写"一次一个战役包"。
`[不得写]` "多包共存已支持" —— v16 依旧是**一次一个包**，只是把这句话直说了。
