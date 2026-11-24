# LEAD_VERIFY_W81 · `S4_8` 守护缺口已修复（含**反向验证**）

> 记录人：Lead｜时间：2026-11-14 09:33｜卡：W81（**GLM-5.3-Flash**，纯离线）
> 交付：`W81_s4_8_guard\S4_8_GUARD_FIX.md` + `out\`（108 文件）+ `UNKNOWNS.md` + `DISAGREE.md`

## 1 · 修了什么（我核了实际 diff）

`[本次实测·git diff --no-index W77 s4_cases.py vs W81 s4_cases.py]` 恰好三处，且都是我要求的：
1. `s4_cases.py` 两处 delta 收集器：`(v14ref / "ra2forge").rglob("*")` → `v14ref.rglob("*")`，同理 v16 侧 ⇒ **恢复全包扫描**
2. `expected_added` 显式加入 `docs/ONE_PACKAGE_AT_A_TIME.md`（按 `sorted()` 字典序）
3. 注释改写成说明"为什么恢复全包 + 为什么显式承认该文档"（**没有**留下 W77 的旧理由文字）

`[逐字未动]` S4_8 三条 check 的文本与判定逻辑、`expected_changed`、其余 96 个用例（我看了 diff，只有上述三处）。

## 2 · 回归（我核了实际数字）

`out\SUMMARY.txt`：**`cases: 97 passed: 97 failed: 0`**、**`assertions: 844 passed / 0 failed`** —— 与 W77 基线**完全一致**（本卡不改产品代码，只改回归脚本与期望集合，所以应当一致）。
⇒ 也说明"恢复全包扫描"**没有连带打红**别的用例：v14ref 包根仅 `ra2forge/`(23)，v16b 包根 = `ra2forge/`(25)+`docs/`(1)，全包 delta 恰好等于 expected。

## 3 · ★ 反向验证（这是本卡最重要的部分）

**我在任务书里明确要求"不投 stray 文件就不算完成"，它做了，而且结果是可核的。**

| 步骤 | 实测（我读了日志原文） |
|---|---|
| 投 `STRAY.txt` 到包根 | `[note] added: ["STRAY.txt", "docs/ONE_PACKAGE_AT_A_TIME.md", "ra2forge/battlemd_inplace.py", "ra2forge/data/BATTLEMD.OFFICIAL.INI"]`<br>`[assert] S4_8e ... FAIL`<br>**`=== case S4_8: FAIL ===`** |
| 移走 `STRAY.txt` | `[assert] S4_8e ... PASS`<br>**`=== case S4_8: PASS ===`** |

`[签发]` **新守护确实有效**：包根出现任意 stray 文件 ⇒ `added` 里精确点名 ⇒ S4_8e FAIL。不是"改完碰巧全绿"。
`[顺带证明]` "移走即 PASS"本身证明 `expected_added` 里确实含 `docs/ONE_PACKAGE_AT_A_TIME.md` —— 否则移走 stray 后仍会因 docs 而 FAIL。

## 4 · 它主动记录的一次过程失败（我认可这种记录）

`[自述]` S4_8 **首跑 FAIL**（初版 `expected_added` 未按字典序排 docs），修正后全绿。
⇒ 这说明判定逻辑是**如实工作**的（乱序即 FAIL），不是误报被抹平。**如实记录中间失败的做法应保持。**

## 5 · 它做的两处自主取舍（我认可）

1. **未采纳"可选增强第四条 check"**：理由 `S4_8e` 的 `added == expected_added` 本身就是白名单断言，再加一条会让断言数偏离 W77 基线（844）——**保持"与基线可比"比"多一条断言"更重要**。这个判断对。
2. **产品代码零改动**：`ra2forge_patched_v16b` 是 v16 的逐字节副本（26 文件，只读复制），并 spot-check 证实 W77 的 `W43_ROOT_NAME`/`V12_ROOT` 原值未动。符合"不改别卡"的红线。

## 6 · 签发

`[签发]` **S4_8 已恢复全包扫描守护，`docs/ONE_PACKAGE_AT_A_TIME.md` 显式列入 `expected_added`；97/97 全绿（844 断言、退出码 0）；反向验证成立（stray → FAIL，移走 → PASS）；v16 产品代码零改动。**

`[效力]` 这补上了 `LEAD_VERIFY_W77.md` §3 记的那条遗留限制（"收窄后 S4_8 不再守护包根出现任意新文件"）。**该遗留项现可标记闭合**。
`[边界]` 本卡只验证了 `S4_8` 这一条守卫；它不证明 v16 的其它行为，也不涉及真机。
`[待办转交]` 若将来还要把 W81 的修正**回写进 W77 或并入 v17**，那是归属方的动作；本卡只在自身目录内交付。
