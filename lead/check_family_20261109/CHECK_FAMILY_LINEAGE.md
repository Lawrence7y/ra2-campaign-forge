# CHECK_FAMILY_LINEAGE.md — 全库 `check_*.py` 同族普查与模板来源追溯

写域：`lead/check_family_20261109/`。产出日期 2026-11-09。本件**只做普查与追溯**，不改任何脚本。
上游数据（同写域）：`_cf_full_census.md`（180 行逐件表）、`_cf_census_out.json`、`_cf_lineage_out.json`、`_cf_detect_out.json`、`_cf_REPORT.md`、`_cfv_census_out.json`、`_cfv_lineage_out.json`、`_cfv_*` 快照件。

---

## 1 目的与边界

**目的**：对全库 `check_*.py` 做逐个普查；给出「同族」的**代码级判据**（同一段写法 / 同一个函数模板，不是名字像）；追溯四件生产门禁的模板来源与相似度；评估 D-27 / D-28 / D-29 / D-30 四条裁决的连带影响；给修复方向。**只做普查与追溯**：本会话未修改、追加、覆盖任何既有脚本、自检件、台账或裁决书。

**铁律落地（本会话实跑/可查）**
- 零真机：未启动 `gamemd.exe` / `ra2loader` / `YURI.exe`，未 `taskkill`，未读活进程内存（本会话命令登记见下，无任何进程类命令）。
- 零采样代码：未写 hook / MiniDump / SuspendThread / StackWalk / 探针注入 / 动态内存解析；本会话新建的唯一可执行文件是本件的生成器 `_cf_compose_lineage.py`，只做 `hashlib` + JSON 解析 + 文本拼装。
- 绝对只读：`lead/d27_ruling_20261106/`、`d28_`、`d29_`、`d30_`、全库其余 `check_*.py` 与自检脚本、`lead/check_masking_20261109/`、`lead/stale_pass_20261109/`、两件台账（`lead/PENDING_DECISIONS.md`、`lead/GOAL_THREE_TARGETS_20261018.md`）一律未改。复核方 `_cfv_snapshot_before.json` / `_cfv_snapshot_after.json` 对 273 件保护文件实跑比对 `missing=[] added=[] changed=[]`（sha256/bytes/mtime_ns 全比）；本会话在其后亦未写入这些路径。
- 唯一写域 = `lead/check_family_20261109/`；不 commit、不 push（`git status --short | wc -l` 本会话基线 237 行，仅为只读观察）。
- Python 一律 `python -I -X utf8` + 绝对路径；指纹用 `hashlib`（本会话实跑 `python -I -X utf8 -c` 读 bytes 后 `hashlib.sha256`，五值见 §6.2；`sha256sum` 交叉验证）。

**本会话实跑命令与输出（逐条可复核）**
| 命令 | 输出 |
|---|---|
| `find "D:/Project/ra2-campaign-forge" -type f -name "check_*.py" 2>/dev/null \| wc -l` | `173` |
| `python -I -X utf8 -c` 解析 `_cf_census_out.json` | `total_files=173`、`missing=[]`、`all_files` 173 条含完整 64 位 `sha256` |
| `python -I -X utf8 -c "…hashlib…"` 读 5 件 bytes | 5 行绑定值，见 §6.2（与题给【复核】`sha256Line` 逐字吻合） |
| `sha256sum lead/d27_ruling_20261106/check_d27.py lead/stale_pass_20261109/_sp_sandbox/check_d27_baseline.py` | 两行同为 `3b769d7c64c2725100186439725198dbc134a277914e2cb2e9b0af844fe7671c` |
| `sed -n '100p'` 上述两件 | 两行同为 `print(f"PASS: D-27 八项机械检查通过；裁决书引用 {count} 处")` |
| `grep -n "门禁.*exit=0\|exit=0.*门禁" lead/PENDING_DECISIONS.md` | 7 行：`:92 :105 :117 :129 :162 :186 :199` |
| `grep -c "D-27\|D-28\|D-29\|D-30" lead/GOAL_THREE_TARGETS_20261018.md` | `0` |
| `stat -c '%y\|%s\|%n'` 六件 d2* 门禁 + 10-02 模板件 | mtime 链见 §3.3 |
| `git log --oneline -- lead/d2[5-9]_ruling_20261106/check_*.py lead/d30_ruling_20261106/check_d30.py` | 无输出（历史空） |
| `git status --short --` 六个 `d2*_ruling_20261106/` 目录 | 六行全 `??`（未跟踪） |
| `grep -rln "for number, title, words, require_all in requirements" --include="*.py" . \| wc -l` | `38`（Python 拆分：29 件 `check_*.py` + 9 件非 `check_*.py` 的 `_w_dNN_[ABS].py`） |
| `grep -rln "require_all" --include="*.py" . \| wc -l` | `44`（本会话时点；普查件记 42 ⇒ 时点/口径差，如实记，见 §3.5） |
| `find lead/stale_pass_20261109/_sp_sandbox -name '_w_d*_*.py' \| wc -l` | `12` |
| `python -I -X utf8 D:/Project/ra2-campaign-forge/lead/check_family_20261109/_cf_compose_lineage.py` | 生成本件（含 173 行逐件表、逐对相似度表、绑定行） |

**未跑**：本会话未做坏针哨兵注入实证，未重跑 `_d27/_d28/_d29/_d30_facts.py` 数值断言，未部署修复、未跑修复后回归；均标「未验」，见 §6.4。编排方 `ranCommands=47` 与复核方 `ranCommands=22` 系各自手工点算，本会话不复核也不重报自己的调用条数。

**清单边界**：173 件含 `.dsh-watch/`、`.tmp/`、`.zcode-watch/` 及 `out/re_work/**` 自嵌套树；`.git/` 内部与符号链接目标未纳入（复核方 `_cfv_checklist.txt` 同边界）。复核方两次 Python 全树 `rglob` 在 `out/re_work/work_chain/CONTINUE_20261003/…/snap_T3/…` 遇 `[WinError 1921]` 卡死并 `TaskStop`，改 `find` 清单绕开 —— 属复核方实跑事实，本会话未重跑该遍历。

---

## 2 全库普查

### 2.1 计数与口径

`find . -type f -name "check_*.py" | sort` → **173 件**（编排方【普查数据】实跑 25 件是其子集）。本会话实跑 `find … | wc -l` = 173，并解析 `_cf_census_out.json` 得 `total_files=173, missing=[]`。逐件 `rel / bytes / 完整 64 位 sha256 / lines / mtime` 见 §2.2 表；同数据亦在 `_cf_full_census.md:9-181`（sha16 版）与 `_cf_census_out.json:all_files[*].sha256`（全 64 位）。

### 2.2 ★ 逐件清单（173 件，全 64 位指纹）

| # | rel | bytes | sha256 (完整 64 位) | lines | mtime | orch_any | require_all | pass_print |
|---|---|---|---|---|---|---|---|---|
| 1 | `.dsh-watch/check_compact.py` | 1192 | `5d6374f798edb98325ff2f9a34d4caa6f4f055d0ef6ae87365f851ac38b43a38` | 21 | 2026-10-24 12:10:21 | - | - | - |
| 2 | `.dsh-watch/check_state.py` | 2031 | `4348fe705251ac784119ed17a90ce96e5ba82959146ff643a8b1b8e2189d8b65` | 26 | 2026-10-24 12:18:48 | - | - | - |
| 3 | `.tmp/check_base.py` | 921 | `7487d2ce2e700d5170fc924602ff825e2549669e3a41b7069d0b52c445c31be2` | 28 | 2026-11-05 16:05:56 | - | - | - |
| 4 | `.tmp/check_bullet_update.py` | 1133 | `bdb1ff59ba17bc0f61db1a5eb2d44c95684c03159cdf295f057753c3dc61a296` | 33 | 2026-11-05 16:09:45 | - | - | - |
| 5 | `.tmp/check_diff_body.py` | 2730 | `2604e7061245e25c0c3d309c05589a19a12347ca5c29354d70c8beb7d043bab8` | 78 | 2026-11-07 14:44:15 | - | - | - |
| 6 | `.tmp/q3b_review/check_18.py` | 1798 | `5174a45003d966963fe729d10d9357f0be85c3e68c512dbec8c1b744431c62f5` | 40 | 2026-11-05 15:44:58 | - | - | - |
| 7 | `.tmp/q3b_review/check_mix.py` | 1133 | `91caac6f081fcb767cfd48581bd778abf1978cf514a2e5175e7e466649eb1208` | 25 | 2026-11-05 15:34:57 | - | - | - |
| 8 | `.zcode-watch/check_a.py` | 1048 | `4fe6b99fd827d9400615da4de0238bc2544d3f7e7fbe7f6adff3e27423291d6a` | 20 | 2026-10-24 01:35:26 | - | - | - |
| 9 | `.zcode-watch/check_a_deep.py` | 1117 | `8090e1da6421e826368afc4a1425569c1ccc13df40d109938f351aacfc7d6836` | 19 | 2026-10-24 09:25:49 | - | - | - |
| 10 | `.zcode-watch/check_activity.py` | 976 | `45c8f24e7844e899026a68287776fc829a1d439bdd6a7f3cbc54a88d5c30d5e8` | 21 | 2026-10-23 22:59:40 | - | - | - |
| 11 | `.zcode-watch/check_wb_files.py` | 495 | `254cd42b48953c86afef4611818266ed9eda98a0e35c262655b03e7094ff4ea3` | 15 | 2026-10-23 17:43:20 | - | - | - |
| 12 | `lead/a_residual_20261106/check_a_residual.py` | 10477 | `10aae9d6fd4d45c59fba3329cda612ac770bde62ac0afbcdce6c8b4c8ab01355` | 248 | 2026-11-06 12:39:44 | - | - | 240 |
| 13 | `lead/b2_preaudit_20261106/check_b2_preaudit.py` | 10300 | `cb0926e1eec7c203d7d2db1abd09661112a1a7f1871af196400f115e24fe7209` | 253 | 2026-11-06 14:22:04 | - | - | 231,248 |
| 14 | `lead/b2b_candidate_20261106/check_candidate.py` | 12175 | `4b9a278b91722f8b4cf776a3b00133c6b3dc6fc0c8ba774cd1567e911ba35e88` | 280 | 2026-11-06 18:27:23 | - | - | 263,274 |
| 15 | `lead/b2b_candidate_review2_20261106/check_semantic_review_r2.py` | 16874 | `7c4b9aa9cabe9912731417da4c8f354149a8dea164486e1251e13019d9091206` | 374 | 2026-11-06 22:20:33 | 266 | - | 358,368 |
| 16 | `lead/b2b_candidate_review_20261106/check_semantic_review.py` | 15332 | `814c2ceec0591ae359c9952abca55a3913ed83738197da50d8a0b8555eb8e955` | 344 | 2026-11-06 20:12:58 | 257 | - | 330,338 |
| 17 | `lead/b2b_design_20261106/check_b2b.py` | 9118 | `fc4fd378d3d1080caff9111ebc4f5006f36fc16f35e7447fec2171b6f562581e` | 220 | 2026-11-06 16:17:59 | - | - | 96,102,215 |
| 18 | `lead/b2b_preaudit_20261106/check_b2b_preaudit.py` | 13946 | `293758f274f4fba1e6347543aafd50e1c480ed56611bc646fa5dfae6f98e04b7` | 315 | 2026-11-06 17:36:09 | - | - | 310 |
| 19 | `lead/check_masking_20261109/_cm_tmp/d27/a_kill_1/check_d27.py` | 3764 | `3b769d7c64c2725100186439725198dbc134a277914e2cb2e9b0af844fe7671c` | 107 | 2026-11-06 16:41:55 | 86 | - | 100 |
| 20 | `lead/check_masking_20261109/_cm_tmp/d27/a_kill_2/check_d27.py` | 3764 | `3b769d7c64c2725100186439725198dbc134a277914e2cb2e9b0af844fe7671c` | 107 | 2026-11-06 16:41:55 | 86 | - | 100 |
| 21 | `lead/check_masking_20261109/_cm_tmp/d27/b_kill_1/check_d27.py` | 3792 | `e7284d28098e72e700496e24c7638d162b17287d982a6aef9ac98518e0858f96` | 107 | 2026-11-09 16:01:13 | 86 | - | 100 |
| 22 | `lead/check_masking_20261109/_cm_tmp/d27/b_kill_2/check_d27.py` | 3783 | `f404f58783ab4da0e59ef94afda5bcc97e69d58914465dad2a36769ab5d7af89` | 107 | 2026-11-09 16:01:13 | 86 | - | 100 |
| 23 | `lead/check_masking_20261109/_cm_tmp/d27/control/check_d27.py` | 3764 | `3b769d7c64c2725100186439725198dbc134a277914e2cb2e9b0af844fe7671c` | 107 | 2026-11-06 16:41:55 | 86 | - | 100 |
| 24 | `lead/check_masking_20261109/_cm_tmp/d27/neg_ctrl/check_d27.py` | 3764 | `3b769d7c64c2725100186439725198dbc134a277914e2cb2e9b0af844fe7671c` | 107 | 2026-11-06 16:41:55 | 86 | - | 100 |
| 25 | `lead/check_masking_20261109/_cm_tmp/d29/a_kill_1/check_d29.py` | 3906 | `2a50b09adff555dbce4c5740a2af78b779876cad771b6fdf887ba3c0dc780f14` | 110 | 2026-11-06 19:33:47 | 84 | 80,83,88 | 105 |
| 26 | `lead/check_masking_20261109/_cm_tmp/d29/a_kill_2/check_d29.py` | 3906 | `2a50b09adff555dbce4c5740a2af78b779876cad771b6fdf887ba3c0dc780f14` | 110 | 2026-11-06 19:33:47 | 84 | 80,83,88 | 105 |
| 27 | `lead/check_masking_20261109/_cm_tmp/d29/and_kill_1/check_d29.py` | 3906 | `2a50b09adff555dbce4c5740a2af78b779876cad771b6fdf887ba3c0dc780f14` | 110 | 2026-11-06 19:33:47 | 84 | 80,83,88 | 105 |
| 28 | `lead/check_masking_20261109/_cm_tmp/d29/b_kill_1/check_d29.py` | 3934 | `164822488182985362740da30dcceaabdf29c0a7cd91e6480b1b4d31facf38af` | 110 | 2026-11-09 16:01:14 | 84 | 80,83,88 | 105 |
| 29 | `lead/check_masking_20261109/_cm_tmp/d29/b_kill_2/check_d29.py` | 3934 | `2399e95a43eaafa4ba5409b0850a89e3ed27a0ef345a8f9628bfbf641580ced5` | 110 | 2026-11-09 16:01:13 | 84 | 80,83,88 | 105 |
| 30 | `lead/check_masking_20261109/_cm_tmp/d29/control/check_d29.py` | 3906 | `2a50b09adff555dbce4c5740a2af78b779876cad771b6fdf887ba3c0dc780f14` | 110 | 2026-11-06 19:33:47 | 84 | 80,83,88 | 105 |
| 31 | `lead/check_masking_20261109/_cm_tmp/d29/neg_ctrl/check_d29.py` | 3906 | `2a50b09adff555dbce4c5740a2af78b779876cad771b6fdf887ba3c0dc780f14` | 110 | 2026-11-06 19:33:47 | 84 | 80,83,88 | 105 |
| 32 | `lead/check_masking_20261109/_cm_tmp/d29/neg_ctrl_all/check_d29.py` | 3906 | `2a50b09adff555dbce4c5740a2af78b779876cad771b6fdf887ba3c0dc780f14` | 110 | 2026-11-06 19:33:47 | 84 | 80,83,88 | 105 |
| 33 | `lead/check_masking_20261109/_cm_tmp/d30/a_kill_1/check_d30.py` | 3926 | `6cb737963fc62a0e045f51247b4fa57ef190acb0b524da3aa6b7713fd05ee9fd` | 110 | 2026-11-06 21:57:57 | 84 | 80,83,88 | 105 |
| 34 | `lead/check_masking_20261109/_cm_tmp/d30/a_kill_2/check_d30.py` | 3926 | `6cb737963fc62a0e045f51247b4fa57ef190acb0b524da3aa6b7713fd05ee9fd` | 110 | 2026-11-06 21:57:57 | 84 | 80,83,88 | 105 |
| 35 | `lead/check_masking_20261109/_cm_tmp/d30/and_kill_1/check_d30.py` | 3926 | `6cb737963fc62a0e045f51247b4fa57ef190acb0b524da3aa6b7713fd05ee9fd` | 110 | 2026-11-06 21:57:57 | 84 | 80,83,88 | 105 |
| 36 | `lead/check_masking_20261109/_cm_tmp/d30/b_kill_1/check_d30.py` | 3955 | `132685366f014171a3b1d085d877b0959ad99514326403adb5adc318524c632a` | 110 | 2026-11-09 16:01:14 | 84 | 80,83,88 | 105 |
| 37 | `lead/check_masking_20261109/_cm_tmp/d30/b_kill_2/check_d30.py` | 3951 | `b1670537e12a6d7ccc48e636088016a0c482ae00bd3ee5280b810d88af9c7129` | 110 | 2026-11-09 16:01:14 | 84 | 80,83,88 | 105 |
| 38 | `lead/check_masking_20261109/_cm_tmp/d30/control/check_d30.py` | 3926 | `6cb737963fc62a0e045f51247b4fa57ef190acb0b524da3aa6b7713fd05ee9fd` | 110 | 2026-11-06 21:57:57 | 84 | 80,83,88 | 105 |
| 39 | `lead/check_masking_20261109/_cm_tmp/d30/neg_ctrl/check_d30.py` | 3926 | `6cb737963fc62a0e045f51247b4fa57ef190acb0b524da3aa6b7713fd05ee9fd` | 110 | 2026-11-06 21:57:57 | 84 | 80,83,88 | 105 |
| 40 | `lead/check_masking_20261109/_cm_tmp/d30/neg_ctrl_all/check_d30.py` | 3926 | `6cb737963fc62a0e045f51247b4fa57ef190acb0b524da3aa6b7713fd05ee9fd` | 110 | 2026-11-06 21:57:57 | 84 | 80,83,88 | 105 |
| 41 | `lead/check_masking_20261109/_cmv_tmp/d27/v_a_kill_2/check_d27.py` | 3764 | `3b769d7c64c2725100186439725198dbc134a277914e2cb2e9b0af844fe7671c` | 107 | 2026-11-06 16:41:55 | 86 | - | 100 |
| 42 | `lead/check_masking_20261109/_cmv_tmp/d27/v_b_kill_2/check_d27.py` | 3783 | `f404f58783ab4da0e59ef94afda5bcc97e69d58914465dad2a36769ab5d7af89` | 107 | 2026-11-09 16:46:41 | 86 | - | 100 |
| 43 | `lead/check_masking_20261109/_cmv_tmp/d29/v_b_kill_2/check_d29.py` | 3934 | `2399e95a43eaafa4ba5409b0850a89e3ed27a0ef345a8f9628bfbf641580ced5` | 110 | 2026-11-09 16:46:41 | 84 | 80,83,88 | 105 |
| 44 | `lead/check_masking_20261109/_cmv_tmp/d29/v_neg_ctrl_all/check_d29.py` | 3906 | `2a50b09adff555dbce4c5740a2af78b779876cad771b6fdf887ba3c0dc780f14` | 110 | 2026-11-06 19:33:47 | 84 | 80,83,88 | 105 |
| 45 | `lead/check_masking_20261109/_cmv_tmp/d30/v_b_kill_2/check_d30.py` | 3951 | `b1670537e12a6d7ccc48e636088016a0c482ae00bd3ee5280b810d88af9c7129` | 110 | 2026-11-09 16:46:41 | 84 | 80,83,88 | 105 |
| 46 | `lead/d13b_design_20261106/check_d13b.py` | 9942 | `316949444d9fd8f435b687beb8466810b57639eefb51ccfae172eb9b101c42b7` | 242 | 2026-11-06 18:20:50 | - | - | 120,126,237 |
| 47 | `lead/d13b_timing_clarify_20261106/check_timing_clarify.py` | 16844 | `de86d9fc4bdb0b2a41f383b6dfe1a8a3a4130c0b38b61ffaad3ec88f11239009` | 390 | 2026-11-06 19:58:42 | - | - | 124,130,385 |
| 48 | `lead/d25_ruling_20261106/check_d25.py` | 2877 | `ceca9d89f38a3701a8b406077274e1f2f23ac5dface420a86e5ea04315c57d0e` | 84 | 2026-11-06 14:41:54 | - | - | 79 |
| 49 | `lead/d26_ruling_20261106/check_d26.py` | 4245 | `0018116a350de46dd98bbecc5f7aae15a3bd599a4e82bb5d43f3dc688c7f9f65` | 111 | 2026-11-06 14:59:27 | 85 | - | 103 |
| 50 | `lead/d27_ruling_20261106/check_d27.py` | 3764 | `3b769d7c64c2725100186439725198dbc134a277914e2cb2e9b0af844fe7671c` | 107 | 2026-11-06 16:41:55 | 86 | - | 100 |
| 51 | `lead/d28_ruling_20261106/check_d28.py` | 4539 | `5b42a34a40046d7a705776002d7aebe8ffda34248849a75b628d40712d9df268` | 122 | 2026-11-06 18:42:26 | - | 94,97,98 | 115 |
| 52 | `lead/d29_ruling_20261106/check_d29.py` | 3906 | `2a50b09adff555dbce4c5740a2af78b779876cad771b6fdf887ba3c0dc780f14` | 110 | 2026-11-06 19:33:47 | 84 | 80,83,88 | 105 |
| 53 | `lead/d30_ruling_20261106/check_d30.py` | 3926 | `6cb737963fc62a0e045f51247b4fa57ef190acb0b524da3aa6b7713fd05ee9fd` | 110 | 2026-11-06 21:57:57 | 84 | 80,83,88 | 105 |
| 54 | `lead/early_trigger_feasibility_20261106/check_feasibility.py` | 18295 | `406c1d58ca0a22657a4f19ceee84c37a0e865f9f046986e4598aa13be69e0f2d` | 389 | 2026-11-06 21:40:56 | 366 | - | 119,149,176,197,206,214,223,383 |
| 55 | `lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S543_0a451d0b/V2/check_burst.py` | 430 | `c48d125285480c70e699d14b3791e47c7e682047c0a69a20a5a4f09240154c7c` | 12 | 2026-11-04 10:37:59 | - | - | - |
| 56 | `lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S543_0a451d0b/V2/check_capture_code.py` | 456 | `a97227777b19d8e461197792bd4522a9f9ff62bf398760c274baac5b558fe52e` | 12 | 2026-11-04 10:36:19 | - | - | - |
| 57 | `lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S543_0a451d0b/V2/check_f61c.py` | 567 | `df8b8e00946064b2f3fe5d32d595de24fe682fa29adf42f81465b73ffb54e417` | 14 | 2026-11-04 10:37:10 | - | - | - |
| 58 | `lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S543_0a451d0b/V2/check_l1_early.py` | 1351 | `3101bbcf793d8bcf82b5c191fb505534510cffe0e057e1ef7a0463cf27d3e6fd` | 28 | 2026-11-04 10:35:34 | - | - | - |
| 59 | `lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S543_0a451d0b/V2/check_png_sha.py` | 1446 | `a89127a145cd81a5a8ee5452bd63064e611a4b99a8e33e748beab4b474d6df59` | 38 | 2026-11-04 10:32:53 | - | - | - |
| 60 | `lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S543_0a451d0b/V2/check_schema.py` | 673 | `e82c95acb0811a0adebbf88c18ce6d14841529c4b6961e5857b23c690b997fa5` | 20 | 2026-11-04 10:30:36 | - | - | - |
| 61 | `lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S543_0a451d0b/V2/check_t35.py` | 297 | `0e7c1b81695297f58f990937e6cb2b3d25f2d587f80292f40b24674300fba40a` | 7 | 2026-11-04 10:37:47 | - | - | - |
| 62 | `lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S543_0a451d0b/V2/check_trip_pngs.py` | 536 | `8a07147cefad2b39208039b9ff30745348145b0ce7c1c3c712a4b217b0a10923` | 15 | 2026-11-04 10:36:35 | - | - | - |
| 63 | `lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S543_0a451d0b/V2/check_trips.py` | 289 | `cf66ce783f3012608942f02d4db9540a47916bb514a52f82c29065d2f22c7ddc` | 12 | 2026-11-04 10:33:58 | - | - | - |
| 64 | `lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S543_0a451d0b/V2/check_v4_all.py` | 638 | `855897ea3c2661d321ca3d8b41e2f301b5e2a2d68c47e924bb8ab815e35fb8d7` | 15 | 2026-11-04 10:34:13 | - | - | - |
| 65 | `lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S543_0a451d0b/V2/check_v4b.py` | 1181 | `ab1a25349eecb404490c2a22d69f65fee4da988abde165f681a1c7affa9c9a90` | 29 | 2026-11-04 10:33:34 | - | - | - |
| 66 | `lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S543_0a451d0b/V3/check_dup_group1_details.py` | 1026 | `eb5047f30110255e1f7211230b1f2019c47aea69c3e5326e20ece1c020c3abc2` | 27 | 2026-11-04 10:32:37 | - | - | - |
| 67 | `lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S543_0a451d0b/V3/check_duplicates.py` | 1469 | `ac96fea89a3286803f926d93adf946ff173d4c89b684bc9c1d7042f73395b8ee` | 39 | 2026-11-04 10:31:29 | - | - | - |
| 68 | `lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S543_0a451d0b/V3/check_l1_image.py` | 527 | `9873aa15f3e05165fee39a23827a4d1e730c53ac1ca48e222105c9f37f5fe17f` | 14 | 2026-11-04 10:33:47 | - | - | - |
| 69 | `lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S543_0a451d0b/V3/check_t38_forensics.py` | 357 | `1e7645093bde387099a305a0b82f65dcd397443d42011bc01b614e213e278933` | 11 | 2026-11-04 10:32:03 | - | - | - |
| 70 | `lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S543_0a451d0b/V3/check_t38_forensics_format.py` | 356 | `866809c7430f0000b2fc5cfe7cb077168a785feeb1d4b5317b42a92fb2731239` | 10 | 2026-11-04 10:32:13 | - | - | - |
| 71 | `lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S543_0a451d0b/V3/check_table2_frames.py` | 993 | `52db1cf4f9745415307b4101f5e20f02c444abbbe32ef235f6798786d5f6cf54` | 28 | 2026-11-04 10:35:46 | - | - | - |
| 72 | `lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S543_0a451d0b/V3/check_trips_mtime.py` | 499 | `27c3dc74f15145f4da0b1adff5ab2c9f7260507cdddd160966817e7d7f4ce57b` | 12 | 2026-11-04 10:31:41 | - | - | - |
| 73 | `lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S543_0a451d0b/V3/check_windows_png.py` | 1912 | `af1a2469faa9ea0c8ea229bfb61399ee59c33148bd20a6b6650daff33113117e` | 59 | 2026-11-04 10:31:00 | - | - | - |
| 74 | `lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S544_ae38d56c/V2/check_fields.py` | 678 | `5808d48b8deff664161864fa6c2a7679b0f0a581a76167712308d0051a0b6357` | 18 | 2026-11-04 18:05:29 | - | - | - |
| 75 | `lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S544_ae38d56c/V2/check_fields2.py` | 528 | `48cd2d6f5756bb48436cd68f88ce07730750191137d82675fb450dad5d76f4c5` | 16 | 2026-11-04 18:05:53 | - | - | - |
| 76 | `lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S544_ae38d56c/V2/check_fields3.py` | 650 | `d81c1b49fbed2dd567f4a51ea4ce99428e59815dd159d1e517239b7b649214f4` | 16 | 2026-11-04 18:06:14 | - | - | - |
| 77 | `lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S544_ae38d56c/V2/check_maps.py` | 377 | `6e11f796a680cea5959d3bf90bbeb2d5dbad1d78a392023e6d9c3f15fe593b76` | 10 | 2026-11-04 18:06:29 | - | - | - |
| 78 | `lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S544_ae38d56c/V2/check_trips_count.py` | 998 | `06291eba12ecbe5ffe20084a23b197b4a54f7f0108820f3bedbcd285671a6204` | 28 | 2026-11-04 18:08:49 | - | - | - |
| 79 | `lead/nextstep_plan_20261106/check_plan.py` | 3956 | `0ead428e33d8707eb760f7ba0391bf30595e4b53a456d9305f9047c3e457b26b` | 117 | 2026-11-06 11:06:01 | - | - | 112 |
| 80 | `lead/stale_pass_20261109/_sp_sandbox/check_d27_baseline.py` | 3764 | `3b769d7c64c2725100186439725198dbc134a277914e2cb2e9b0af844fe7671c` | 107 | 2026-11-09 17:08:16 | 86 | - | 100 |
| 81 | `lead/stale_pass_20261109/_sp_sandbox/check_d27_injected.py` | 3783 | `f404f58783ab4da0e59ef94afda5bcc97e69d58914465dad2a36769ab5d7af89` | 107 | 2026-11-09 17:09:14 | 86 | - | 100 |
| 82 | `lead/stale_pass_20261109/_sp_sandbox/d28/check_d28_baseline.py` | 4539 | `5b42a34a40046d7a705776002d7aebe8ffda34248849a75b628d40712d9df268` | 122 | 2026-11-09 17:14:06 | - | 94,97,98 | 115 |
| 83 | `lead/stale_pass_20261109/_sp_sandbox/d28x/a/b/check_d28_baseline.py` | 4539 | `5b42a34a40046d7a705776002d7aebe8ffda34248849a75b628d40712d9df268` | 122 | 2026-11-09 17:14:16 | - | 94,97,98 | 115 |
| 84 | `lead/stale_pass_20261109/_sp_sandbox/d28x/a/b/check_d28_injected.py` | 4569 | `f5ae184ca7ddc6cfb9965124e26d506992903305aabbdd1a3beb500eb4692314` | 122 | 2026-11-09 17:14:33 | - | 94,97,98 | 115 |
| 85 | `lead/stale_pass_20261109/_sp_sandbox/d29/check_d29_baseline.py` | 3906 | `2a50b09adff555dbce4c5740a2af78b779876cad771b6fdf887ba3c0dc780f14` | 110 | 2026-11-09 17:09:49 | 84 | 80,83,88 | 105 |
| 86 | `lead/stale_pass_20261109/_sp_sandbox/d29/check_d29_injected.py` | 3934 | `2399e95a43eaafa4ba5409b0850a89e3ed27a0ef345a8f9628bfbf641580ced5` | 110 | 2026-11-09 17:09:49 | 84 | 80,83,88 | 105 |
| 87 | `lead/stale_pass_20261109/_sp_sandbox/d30/check_d30_baseline.py` | 3926 | `6cb737963fc62a0e045f51247b4fa57ef190acb0b524da3aa6b7713fd05ee9fd` | 110 | 2026-11-09 17:09:49 | 84 | 80,83,88 | 105 |
| 88 | `lead/stale_pass_20261109/_sp_sandbox/d30/check_d30_injected.py` | 3951 | `b1670537e12a6d7ccc48e636088016a0c482ae00bd3ee5280b810d88af9c7129` | 110 | 2026-11-09 17:09:49 | 84 | 80,83,88 | 105 |
| 89 | `lead/stall_event_def_20261106/check_stall_def.py` | 10883 | `ce6e5d9f65fb764a8753d331bad9fa22f5ddff986c5b50655eff67a7439628c5` | 271 | 2026-11-06 16:14:38 | 118 | - | 244,264 |
| 90 | `out/re_work/_lead_baseline/W3/check_m4r_byte_slips.py` | 1461 | `fd7eeaa4d86fbcf0a702b070853a5eb0c628035ff19785223ed3e84ee95988b8` | 36 | 2026-10-01 23:42:11 | - | - | - |
| 91 | `out/re_work/_lead_baseline/W3/forensics/snapshot_R182/coverage_ledger/_verify_cmdwindows_20261002/check_windows_cmds.py` | 5811 | `433a270509db0b37f3ce5067205a52d0e3aa0ea34a66083ae1e93f13fb255aae` | 132 | 2026-10-02 06:42:02 | 82 | - | 131 |
| 92 | `out/re_work/_lead_baseline/W3/forensics/snapshot_R196/coverage_ledger/_verify_cmdwindows_20261002/check_windows_cmds.py` | 5811 | `433a270509db0b37f3ce5067205a52d0e3aa0ea34a66083ae1e93f13fb255aae` | 132 | 2026-10-02 06:42:02 | 82 | - | 131 |
| 93 | `out/re_work/agy/W3_20261001/errata_apply/check_anchors.py` | 1248 | `f3b6afbe2e475ecbdd5b666b81ccf597f02df3f8bc991fb4498e0a09c52b17b8` | 28 | 2026-10-01 21:59:42 | - | - | - |
| 94 | `out/re_work/agy/W3_20261001/errata_apply/check_segments.py` | 1066 | `65c90463b4462e41d3dd3eda81b62a9f75e4cd26fd367a598c269b0ca4c30603` | 28 | 2026-10-01 22:00:31 | - | - | - |
| 95 | `out/re_work/agy/W3_20261001/landing/check_current_lines.py` | 1323 | `8a89ddeb7bfd0682f9ff506c107f638a10952a1d802da6f2ac36ded4321d1a45` | 41 | 2026-10-01 23:13:51 | - | - | - |
| 96 | `out/re_work/agy/W3_20261001/merge_matrix/check_contradicts.py` | 591 | `96f103c77a5be87a3ec911966434572ad90475b719aabfd706c476bd6d07cc31` | 17 | 2026-10-01 22:49:33 | - | - | - |
| 97 | `out/re_work/agy/W3_20261001/merge_matrix/check_overlap_items.py` | 2168 | `e5825bf5bef5cb1ef61bb0570fcb1a18fd3eb4e5839f460115102e67abcc1861` | 54 | 2026-10-01 22:48:39 | - | - | - |
| 98 | `out/re_work/agy/W3_20261001/merge_matrix/check_potential_conflicts.py` | 1086 | `1127a828170cb1ce8d88cea2049253b1fe505af2c08439fc7f2a76a7221340a4` | 30 | 2026-10-01 22:49:51 | - | - | - |
| 99 | `out/re_work/agy/W3_20261001/merge_matrix/check_self_healed.py` | 2606 | `4544ddcd4f6f659cc28321fc018eea39f524ca4974f0a2f703b8d1452c5977ca` | 48 | 2026-10-01 22:54:31 | - | - | - |
| 100 | `out/re_work/agy/W3_20261001/merge_matrix/check_zero_clean_hits.py` | 882 | `ab8e0b980fb249c099671fc71293de424da57928c19bd94fcec3e85064ac0f78` | 27 | 2026-10-01 22:51:38 | - | - | - |
| 101 | `out/re_work/agy_fog_firststage/r3/alt/check_h3_tables.py` | 3023 | `16f88e3141286f74273d21faef1fd8615082cbd9dd2875c452bfd50abac98918` | 80 | 2026-09-28 11:04:35 | - | - | - |
| 102 | `out/re_work/agy_fog_firststage/r3/calldraw/check_h2_calldraw.py` | 1633 | `ad164d60e64236f53976e7f5f0f984637d63b22b896d362d1edd224bdf22f09c` | 50 | 2026-09-28 11:04:12 | - | - | - |
| 103 | `out/re_work/agy_patchhex/bytes/check_bytes.py` | 5890 | `9a087a168dfdf42fec3bf5e642f8599bb91b9bab3cd13b2570d251161cb1032f` | 117 | 2026-09-28 11:05:18 | - | - | - |
| 104 | `out/re_work/atlas_rev/R6/check_doc.py` | 910 | `5f9e7940865cd24678c22b884d308e89549ae0330c8274151444d21961820b4c` | 26 | 2026-09-29 13:13:20 | - | - | - |
| 105 | `out/re_work/doc_audit/check_refs.py` | 2039 | `9e45f50a1af36fb0807e3b4b2294d79621d3eb6d9d3e851c64b2ae1275daa897` | 38 | 2026-09-27 09:01:21 | - | - | - |
| 106 | `out/re_work/landing_audit/check_trampoline.py` | 5592 | `25165e35f4c5c71895e927d6a93289f2e4abf2bc0d54486d0e0a9c9376af7036` | 129 | 2026-09-29 19:02:56 | - | - | - |
| 107 | `out/re_work/mp_landing/check_known_fixes.py` | 3704 | `19cae767cc5c7936760482a485962f7ddf0a9b21e43048f48548eb93358ab237` | 77 | 2026-09-26 23:47:53 | - | - | - |
| 108 | `out/re_work/qc/W3_20261001/coverage_ledger/_agame_recompute_20261002/check_report_tables_match_artifact.py` | 2525 | `95c8c54fa0579b91711ddb49c34b3d4ee57ea25cded72f05c393c879c4c70f96` | 52 | 2026-10-02 10:31:59 | - | - | 50 |
| 109 | `out/re_work/qc/W3_20261001/coverage_ledger/_verify_cmdwindows_20261002/check_windows_cmds.py` | 5811 | `433a270509db0b37f3ce5067205a52d0e3aa0ea34a66083ae1e93f13fb255aae` | 132 | 2026-10-02 06:42:02 | 82 | - | 131 |
| 110 | `out/re_work/qc/W3_20261001/docfix2/check_fileoffset_axiom.py` | 31955 | `4e42d7b2acf090c3454d8e5715ad2c3ab638b7086f964c00d1f21dff84b00891` | 421 | 2026-10-02 01:06:25 | 301,312 | - | 407 |
| 111 | `out/re_work/qc/W3_20261001/docfix2/check_fileoffset_axiom.template.py` | 11843 | `93689dcb0c723a9ecf02a881267300acc506e33aa8c287831c327b0b4e88d1e8` | 266 | 2026-10-02 01:00:46 | 146,157 | - | 252 |
| 112 | `out/re_work/qc/W3_20261001/scripts/check_gate.py` | 5354 | `4cdf32d79045ecfcf5c03e9532736110b20dbf3350b5eb7bf697876d69ae83f6` | 131 | 2026-10-01 22:18:17 | - | - | 101,125 |
| 113 | `out/re_work/qc/W3_20261002/doc2_runbook_terms/scripts/check_citations.py` | 2063 | `17356f21e14c354aa7cbefb5400002e32c241655d9b28cde43e92a643af9d72a` | 60 | 2026-10-02 21:16:08 | - | - | - |
| 114 | `out/re_work/re_sprint/R_b_static/check_trampoline_rel32.py` | 8760 | `cb60aa5abc9e16903bd43bca273d539a4f15fbbb7508959368df664aa38d85cd` | 189 | 2026-09-30 19:54:01 | - | - | 21,184 |
| 115 | `out/re_work/re_sprint/S1/check_134_all.py` | 469 | `b915bd757f3e44fefaf35eedf427b4998be0a2307cc085bb18a10c11b0e5b832` | 9 | 2026-09-26 20:12:32 | - | - | - |
| 116 | `out/re_work/re_sprint/S1/check_134_inc.py` | 455 | `68c9156a40e32475d2a2a1368135b3f0ff2e737b0ca1495252a636f135fee512` | 9 | 2026-09-26 20:12:56 | 8 | - | - |
| 117 | `out/re_work/re_sprint/S1/check_134_refs.py` | 408 | `a7aa88545c61c2eff63041c2aafcc649ab152cfa979335104f35c1b47386d1d9` | 9 | 2026-09-26 20:12:22 | - | - | - |
| 118 | `out/re_work/re_sprint/S1/check_1707.py` | 681 | `bb4a5ea618cd60ff6d157573e6c21cce7d00cc08c60aebaf88d52cb8fe16ddb7` | 21 | 2026-09-26 20:11:11 | - | - | - |
| 119 | `out/re_work/re_sprint/S1/check_5f0_writes.py` | 1650 | `fa604df7566a19a3ab8f222d6142d2dc6c788131fd9107b53487e3bfd2ea74d3` | 36 | 2026-09-26 20:11:22 | - | - | - |
| 120 | `out/re_work/re_sprint/S1/check_5f4.py` | 681 | `b4b271b5768aed9a7c51f592c500c3556328227455d0fc4e2cecdab51171d1c3` | 21 | 2026-09-26 20:11:56 | - | - | - |
| 121 | `out/re_work/re_sprint/S1/check_sight_ini.py` | 1225 | `d263361dc511b76c6fc07daccdf746722376f5e0784c3bcc7cd1ecca443836b1` | 42 | 2026-09-26 20:11:42 | - | - | - |
| 122 | `out/re_work/re_sprint/S1/check_true_gap.py` | 1380 | `ffa89f5277f65fa665679052d10061533f4eaeda01bfd2fa27da1ace3ec4ee4f` | 41 | 2026-09-26 20:12:08 | - | - | - |
| 123 | `out/re_work/re_sprint/S10/check_symbols.py` | 519 | `64c8b94fe8b17b4710289f5bf828fef90a7259a4f51715e0d4e41c15fc2610a3` | 11 | 2026-09-26 21:08:04 | - | - | - |
| 124 | `out/re_work/re_sprint/S11/check_other_allocs.py` | 851 | `0b66ee30130a7d471ace58999a98065de13de7d396ff4d68b4e37ca1a7eea13b` | 25 | 2026-09-26 21:00:19 | - | - | - |
| 125 | `out/re_work/re_sprint/S12/check_rtti.py` | 604 | `bb3171daf463dea5c268da5687e64b5d91cc3f64d5fe965d597f560b43b6566a` | 15 | 2026-09-26 21:03:52 | - | - | - |
| 126 | `out/re_work/re_sprint/S14/check_locks.py` | 1292 | `ece18331cdb0d7199d95175fdac8ec0f549fdf8d69e0b0a33863731774d10d47` | 39 | 2026-09-26 22:37:39 | - | - | - |
| 127 | `out/re_work/re_sprint/S14/check_queue_408ee0.py` | 1077 | `9188a05b357a03cca56d6fc5bdfff505642f9ff9cd7e88a044807a95042524c7` | 36 | 2026-09-26 22:40:19 | - | - | - |
| 128 | `out/re_work/re_sprint/S14/check_threads.py` | 1052 | `a33e64a4577a4f54aaf1517c1f783c4d597089c47a8f68b808be421f38aab41d` | 33 | 2026-09-26 22:37:01 | - | - | - |
| 129 | `out/re_work/re_sprint/S15/check_audio_abi.py` | 876 | `5b91f8ab24fed57e410c1c5518625b52b24f9b5e6d014a3c0671c5864c45aeac` | 28 | 2026-09-26 22:37:37 | - | - | - |
| 130 | `out/re_work/re_sprint/S15/check_crt_details.py` | 897 | `57aee5247b193b233aefba3277a14bed151e0fe670738d5b4b06f0c86b6f97ff` | 28 | 2026-09-26 22:37:51 | - | - | - |
| 131 | `out/re_work/re_sprint/S16/check_mp_vars.py` | 1919 | `4ad5000a28cf574c3ecd7cdb80631280669fe7ac636468e88675a81201355610` | 52 | 2026-09-26 22:38:56 | - | - | - |
| 132 | `out/re_work/re_sprint/S16/check_no_hit_files.py` | 527 | `cd71b184ad9a41e78c0b8484233ef03a0959df2f73784427eae7c8545fd45d6c` | 14 | 2026-09-26 22:37:08 | - | - | - |
| 133 | `out/re_work/re_sprint/S2/check_8a0360_cluster.py` | 2132 | `3cc37aab71fdf4b9ad58e855b35d25e9417ab8b492fc4e04d231bbcf5f6ec127` | 60 | 2026-09-26 20:33:23 | - | - | - |
| 134 | `out/re_work/re_sprint/S2/check_abstract_save_load.py` | 2188 | `ae3634812393b8bd87c69cfd5f61d465f7b6a008542a288313717ab0c8fdf748` | 59 | 2026-09-26 20:24:59 | - | - | - |
| 135 | `out/re_work/re_sprint/S2/check_rtti_whatami.py` | 1908 | `598ee2026c92dc072ef2e1cfabeb0614e57bb412201190f0575a20848e7b3741` | 49 | 2026-09-26 20:33:35 | - | - | - |
| 136 | `out/re_work/re_sprint/S21/check_all_re_points.py` | 4699 | `994a877830b61e98b586ef66add891e34c19db3fd547dad44c795671102b4152` | 116 | 2026-09-26 23:30:45 | - | - | - |
| 137 | `out/re_work/re_sprint/S21/check_classes.py` | 2235 | `26b0fd2afdd8f6a00fc0b5dd98e29a89dfff90e1a11b5b3b37364fc6b63e3c68` | 64 | 2026-09-26 23:31:36 | - | - | - |
| 138 | `out/re_work/re_sprint/S21/check_extra_points.py` | 2049 | `69a66947c33f05e81edf389310dd12b9a5d5950bfc85016c64c9a65857e9330a` | 56 | 2026-09-26 23:35:39 | - | - | - |
| 139 | `out/re_work/re_sprint/S21/check_frame_writes.py` | 813 | `6450389e65f9ded82e62f75ddd66899d9cbe9fc3c5dc5274732b9863c92d625a` | 26 | 2026-09-26 23:35:48 | - | - | - |
| 140 | `out/re_work/re_sprint/S21/check_houses_teamtypes.py` | 1260 | `47eae868c5776a563c366c14d038a4380c2a0b362aec32efe87b3043be17e590` | 34 | 2026-09-26 23:31:46 | - | - | - |
| 141 | `out/re_work/re_sprint/S21/check_item8.py` | 1999 | `b79565966447812b776d6861557d25971f8470ecf5886761c22d51f2d5a04462` | 56 | 2026-09-26 23:33:24 | - | - | - |
| 142 | `out/re_work/re_sprint/S21/check_load_funcs.py` | 1912 | `ac4b1bfe9ef05abbdc6156f02abbd37753eb688e4f0b9a36a8bdd6af87229dbe` | 56 | 2026-09-26 23:32:32 | - | - | - |
| 143 | `out/re_work/re_sprint/S21/check_vectors.py` | 1254 | `13a41b3879d3f5db574039cd340401aba99c56b4abc4eaa324faab67acf2362e` | 36 | 2026-09-26 23:31:25 | - | - | - |
| 144 | `out/re_work/re_sprint/S21/check_vtables.py` | 1430 | `f31d4589c39a4530475e10237fd70a79e77c36eeac6b76de758be245fe8b8f59` | 41 | 2026-09-26 23:34:04 | - | - | - |
| 145 | `out/re_work/re_sprint/S4/check_hooks.py` | 355 | `546e227c9712baec8d4b489bf256b90c351b32416b826133d8ebcac748c42bc7` | 12 | 2026-09-26 20:10:48 | - | - | - |
| 146 | `out/re_work/re_sprint/S4/check_perf.py` | 659 | `d9652af97314f330eadb998887a32c608ff4f9e2c97c976f29b37057f1bc76f4` | 18 | 2026-09-26 20:10:37 | - | - | - |
| 147 | `out/re_work/re_sprint/S5/check_eax_exact.py` | 2789 | `30c16fc81b8f823d18e937f3a982d5b82d75ce88242607c370f5b1ae56db1d18` | 75 | 2026-09-26 20:27:56 | 41,53,58 | - | - |
| 148 | `out/re_work/re_sprint/S8/check_data_raw.py` | 408 | `8cecf8ee9bbc975012ea3e6cf717f1fce8d3503f6fe1d58558164c570f06412e` | 8 | 2026-09-26 20:09:05 | - | - | - |
| 149 | `out/re_work/re_sprint/S8/check_house_34.py` | 617 | `c66e6972faa8db3cf56cd72fd817944eb11ad29ded5bd8cfd73dc0ccefc9c743` | 20 | 2026-09-26 20:24:32 | - | - | - |
| 150 | `out/re_work/re_sprint/S8/check_particle_in_crc.py` | 366 | `25ecaa3377f404ec18adb9810aeb2e3caa656c83b4275225e682043e9cb24c5c` | 8 | 2026-09-26 20:13:26 | - | - | - |
| 151 | `out/re_work/re_sprint/S8/check_points.py` | 914 | `08cd4739972afe2e49f2bd1f858e2d327eac4b1b6ba5ffe98e6180b1db24d786` | 29 | 2026-09-26 20:06:05 | - | - | - |
| 152 | `out/re_work/re_sprint/S8/check_sync_strings.py` | 427 | `50ee77ccf9f993d1436c78b937a003394934c322c93490ec35c9860fd1a4c7e9` | 15 | 2026-09-26 20:14:04 | - | - | - |
| 153 | `out/re_work/re_sprint/S8/check_v11_returns.py` | 916 | `381995c498aa910f34fe07967f21708fad4ac2c6a46f9298062c8129159d94f2` | 31 | 2026-09-26 20:10:26 | - | - | - |
| 154 | `out/re_work/re_sprint/S8/check_v30_layer.py` | 985 | `afb3a8cc8ed5836c65f7e5e5469472c16c660a4d9abf03fd1c015776e4d856c3` | 24 | 2026-09-26 20:11:28 | - | - | - |
| 155 | `out/re_work/re_sprint/S9/check_86e_section.py` | 1550 | `19e9335942728f728d92dccc7ce69ff9f055f99d5773ef1a0b9f09cb2eed2a60` | 56 | 2026-09-26 21:00:56 | - | - | - |
| 156 | `out/re_work/triggers/check_doc.py` | 503 | `34a05a00edfc3165192e6c41dbb5923453bbe03d5622ee69bd0a244fc9150b7d` | 11 | 2026-09-26 23:22:02 | - | - | - |
| 157 | `out/re_work/work_chain/CONTINUE_20261003/lead/cluster_b2/scripts/check_41_46.py` | 495 | `d457b1ed57d2d815d00bc791b4da8c7e77f3c2f3ab3f02a49c7e24d5a24dc669` | 9 | 2026-10-11 11:16:52 | - | - | - |
| 158 | `out/re_work/work_chain/CONTINUE_20261003/lead/cluster_b2/scripts/check_tails.py` | 1472 | `7623d3b9630d2a45db6c3fbfc94250697416b4dc9425337ff56bc8fb07092431` | 42 | 2026-10-11 11:17:12 | - | - | - |
| 159 | `out/re_work/work_chain/CONTINUE_20261003/lead/cluster_b2/scripts/check_vts.py` | 789 | `07145caa30e86211a700f9067f3bbdadc0f832e6d018f3676af6bb7a92982a01` | 14 | 2026-10-11 11:17:54 | - | - | - |
| 160 | `out/re_work/work_chain/CONTINUE_20261003/lead/goal3_expect_recompute_20261021/check_symbols.py` | 5897 | `ff2ceb11a715e73eb1e8c6ca8e66307c30f701759132a3b1bfa35f857123ff39` | 128 | 2026-10-21 14:03:57 | - | - | - |
| 161 | `out/re_work/work_chain/CONTINUE_20261003/lead/h1_install/tools/check_report.py` | 8702 | `863e022f1b1cd29f9911e54990fc9db424675343ff7689f1e8c431826a794127` | 175 | 2026-10-08 23:13:00 | - | - | - |
| 162 | `out/re_work/work_chain/CONTINUE_20261003/lead/hook_xcheck/repos/Phobos/.agents/skills/check-hooks/check_hook_conflicts.py` | 7798 | `6d931080d149a1410c6bd8cc683d49b7fab8b0ffd48165845a0a7c1a1724fa81` | 197 | 2026-10-09 19:46:51 | - | - | - |
| 163 | `out/re_work/work_chain/CONTINUE_20261003/lead/rc4_impl_v2/entryid_refactor/tools/check_fixtures.py` | 5988 | `f85fb6f3e933541eb0a1f0867071b7943a4e8300b1ea6e7d5e82f085c581752b` | 119 | 2026-10-05 16:54:16 | - | - | 112 |
| 164 | `out/re_work/zcode_live/W3_20261002/cs1_cascade/nc1_tree/ra2-campaign-forge/out/re_work/agy/W3_20261001/errata_apply/check_anchors.py` | 1248 | `f3b6afbe2e475ecbdd5b666b81ccf597f02df3f8bc991fb4498e0a09c52b17b8` | 28 | 2026-10-01 21:59:42 | - | - | - |
| 165 | `out/re_work/zcode_live/W3_20261002/cs1_cascade/nc1_tree/ra2-campaign-forge/out/re_work/agy/W3_20261001/errata_apply/check_segments.py` | 1066 | `65c90463b4462e41d3dd3eda81b62a9f75e4cd26fd367a598c269b0ca4c30603` | 28 | 2026-10-01 22:00:31 | - | - | - |
| 166 | `out/re_work/zcode_live/W3_20261002/cs1_cascade/nc1_tree/ra2-campaign-forge/out/re_work/agy/W3_20261001/landing/check_current_lines.py` | 1323 | `8a89ddeb7bfd0682f9ff506c107f638a10952a1d802da6f2ac36ded4321d1a45` | 41 | 2026-10-01 23:13:51 | - | - | - |
| 167 | `out/re_work/zcode_live/W3_20261002/cs1_cascade/nc1_tree/ra2-campaign-forge/out/re_work/agy/W3_20261001/merge_matrix/check_contradicts.py` | 591 | `96f103c77a5be87a3ec911966434572ad90475b719aabfd706c476bd6d07cc31` | 17 | 2026-10-01 22:49:33 | - | - | - |
| 168 | `out/re_work/zcode_live/W3_20261002/cs1_cascade/nc1_tree/ra2-campaign-forge/out/re_work/agy/W3_20261001/merge_matrix/check_overlap_items.py` | 2168 | `e5825bf5bef5cb1ef61bb0570fcb1a18fd3eb4e5839f460115102e67abcc1861` | 54 | 2026-10-01 22:48:39 | - | - | - |
| 169 | `out/re_work/zcode_live/W3_20261002/cs1_cascade/nc1_tree/ra2-campaign-forge/out/re_work/agy/W3_20261001/merge_matrix/check_potential_conflicts.py` | 1086 | `1127a828170cb1ce8d88cea2049253b1fe505af2c08439fc7f2a76a7221340a4` | 30 | 2026-10-01 22:49:51 | - | - | - |
| 170 | `out/re_work/zcode_live/W3_20261002/cs1_cascade/nc1_tree/ra2-campaign-forge/out/re_work/agy/W3_20261001/merge_matrix/check_self_healed.py` | 2606 | `4544ddcd4f6f659cc28321fc018eea39f524ca4974f0a2f703b8d1452c5977ca` | 48 | 2026-10-01 22:54:31 | - | - | - |
| 171 | `out/re_work/zcode_live/W3_20261002/cs1_cascade/nc1_tree/ra2-campaign-forge/out/re_work/agy/W3_20261001/merge_matrix/check_zero_clean_hits.py` | 882 | `ab8e0b980fb249c099671fc71293de424da57928c19bd94fcec3e85064ac0f78` | 27 | 2026-10-01 22:51:38 | - | - | - |
| 172 | `tools/check_except_gate.py` | 15204 | `88758b04d099f176ebe3337d5785446ee039f5ebc046bbe52e92c6ba2349cea6` | 364 | 2026-10-21 22:08:49 | - | - | 258,336 |
| 173 | `tools/check_syms.py` | 689 | `4c43af3c11fc3e1a43b659c4d230ff1b06b1f7fd03b6ffaa2ef3ac3203dc8367` | 20 | 2026-10-21 22:08:49 | - | - | - |

### 2.3 含 `any()` 与 `require_all` 的清单

**含 `any()`（`orch_any` 或 `any_gen` 非空）= 53 件**（`_cf_census_out.json:summary.n_any_gen=53`、`n_orch_any=48`、`n_any_membership=53`、`n_any_word_or=40`）：

| rel | orch_any | any_gen | require_all |
|---|---|---|---|
| `lead/b2b_candidate_review2_20261106/check_semantic_review_r2.py` | 266 | 216,266,281,283 | - |
| `lead/b2b_candidate_review_20261106/check_semantic_review.py` | 257 | 207,257,272,274 | - |
| `lead/check_masking_20261109/_cm_tmp/d27/a_kill_1/check_d27.py` | 86 | 86 | - |
| `lead/check_masking_20261109/_cm_tmp/d27/a_kill_2/check_d27.py` | 86 | 86 | - |
| `lead/check_masking_20261109/_cm_tmp/d27/b_kill_1/check_d27.py` | 86 | 86 | - |
| `lead/check_masking_20261109/_cm_tmp/d27/b_kill_2/check_d27.py` | 86 | 86 | - |
| `lead/check_masking_20261109/_cm_tmp/d27/control/check_d27.py` | 86 | 86 | - |
| `lead/check_masking_20261109/_cm_tmp/d27/neg_ctrl/check_d27.py` | 86 | 86 | - |
| `lead/check_masking_20261109/_cm_tmp/d29/a_kill_1/check_d29.py` | 84 | 84 | 80,83,88 |
| `lead/check_masking_20261109/_cm_tmp/d29/a_kill_2/check_d29.py` | 84 | 84 | 80,83,88 |
| `lead/check_masking_20261109/_cm_tmp/d29/and_kill_1/check_d29.py` | 84 | 84 | 80,83,88 |
| `lead/check_masking_20261109/_cm_tmp/d29/b_kill_1/check_d29.py` | 84 | 84 | 80,83,88 |
| `lead/check_masking_20261109/_cm_tmp/d29/b_kill_2/check_d29.py` | 84 | 84 | 80,83,88 |
| `lead/check_masking_20261109/_cm_tmp/d29/control/check_d29.py` | 84 | 84 | 80,83,88 |
| `lead/check_masking_20261109/_cm_tmp/d29/neg_ctrl/check_d29.py` | 84 | 84 | 80,83,88 |
| `lead/check_masking_20261109/_cm_tmp/d29/neg_ctrl_all/check_d29.py` | 84 | 84 | 80,83,88 |
| `lead/check_masking_20261109/_cm_tmp/d30/a_kill_1/check_d30.py` | 84 | 84 | 80,83,88 |
| `lead/check_masking_20261109/_cm_tmp/d30/a_kill_2/check_d30.py` | 84 | 84 | 80,83,88 |
| `lead/check_masking_20261109/_cm_tmp/d30/and_kill_1/check_d30.py` | 84 | 84 | 80,83,88 |
| `lead/check_masking_20261109/_cm_tmp/d30/b_kill_1/check_d30.py` | 84 | 84 | 80,83,88 |
| `lead/check_masking_20261109/_cm_tmp/d30/b_kill_2/check_d30.py` | 84 | 84 | 80,83,88 |
| `lead/check_masking_20261109/_cm_tmp/d30/control/check_d30.py` | 84 | 84 | 80,83,88 |
| `lead/check_masking_20261109/_cm_tmp/d30/neg_ctrl/check_d30.py` | 84 | 84 | 80,83,88 |
| `lead/check_masking_20261109/_cm_tmp/d30/neg_ctrl_all/check_d30.py` | 84 | 84 | 80,83,88 |
| `lead/check_masking_20261109/_cmv_tmp/d27/v_a_kill_2/check_d27.py` | 86 | 86 | - |
| `lead/check_masking_20261109/_cmv_tmp/d27/v_b_kill_2/check_d27.py` | 86 | 86 | - |
| `lead/check_masking_20261109/_cmv_tmp/d29/v_b_kill_2/check_d29.py` | 84 | 84 | 80,83,88 |
| `lead/check_masking_20261109/_cmv_tmp/d29/v_neg_ctrl_all/check_d29.py` | 84 | 84 | 80,83,88 |
| `lead/check_masking_20261109/_cmv_tmp/d30/v_b_kill_2/check_d30.py` | 84 | 84 | 80,83,88 |
| `lead/d13b_design_20261106/check_d13b.py` | - | 135 | - |
| `lead/d13b_timing_clarify_20261106/check_timing_clarify.py` | - | 143 | - |
| `lead/d26_ruling_20261106/check_d26.py` | 85 | 85 | - |
| `lead/d27_ruling_20261106/check_d27.py` | 86 | 86 | - |
| `lead/d29_ruling_20261106/check_d29.py` | 84 | 84 | 80,83,88 |
| `lead/d30_ruling_20261106/check_d30.py` | 84 | 84 | 80,83,88 |
| `lead/early_trigger_feasibility_20261106/check_feasibility.py` | 366 | 366 | - |
| `lead/nextstep_plan_20261106/check_plan.py` | - | 48 | - |
| `lead/stale_pass_20261109/_sp_sandbox/check_d27_baseline.py` | 86 | 86 | - |
| `lead/stale_pass_20261109/_sp_sandbox/check_d27_injected.py` | 86 | 86 | - |
| `lead/stale_pass_20261109/_sp_sandbox/d29/check_d29_baseline.py` | 84 | 84 | 80,83,88 |
| `lead/stale_pass_20261109/_sp_sandbox/d29/check_d29_injected.py` | 84 | 84 | 80,83,88 |
| `lead/stale_pass_20261109/_sp_sandbox/d30/check_d30_baseline.py` | 84 | 84 | 80,83,88 |
| `lead/stale_pass_20261109/_sp_sandbox/d30/check_d30_injected.py` | 84 | 84 | 80,83,88 |
| `lead/stall_event_def_20261106/check_stall_def.py` | 118 | 118 | - |
| `out/re_work/_lead_baseline/W3/forensics/snapshot_R182/coverage_ledger/_verify_cmdwindows_20261002/check_windows_cmds.py` | 82 | 82 | - |
| `out/re_work/_lead_baseline/W3/forensics/snapshot_R196/coverage_ledger/_verify_cmdwindows_20261002/check_windows_cmds.py` | 82 | 82 | - |
| `out/re_work/qc/W3_20261001/coverage_ledger/_verify_cmdwindows_20261002/check_windows_cmds.py` | 82 | 82 | - |
| `out/re_work/qc/W3_20261001/docfix2/check_fileoffset_axiom.py` | 301,312 | 301,312 | - |
| `out/re_work/qc/W3_20261001/docfix2/check_fileoffset_axiom.template.py` | 146,157 | 146,157 | - |
| `out/re_work/qc/W3_20261001/scripts/check_gate.py` | - | 53 | - |
| `out/re_work/re_sprint/S1/check_134_inc.py` | 8 | 8 | - |
| `out/re_work/re_sprint/S5/check_eax_exact.py` | 41,53,58 | 41,53,58 | - |
| `out/re_work/work_chain/CONTINUE_20261003/lead/h1_install/tools/check_report.py` | - | 59 | - |

**含 `require_all` = 29 件**（`_cf_census_out.json:summary.n_require_all=29`、`n_requirements_assign=29`）：

| rel | require_all 行 | bytes | sha16 |
|---|---|---|---|
| `lead/check_masking_20261109/_cm_tmp/d29/a_kill_1/check_d29.py` | 80,83,88 | 3906 | 2a50b09adff555db |
| `lead/check_masking_20261109/_cm_tmp/d29/a_kill_2/check_d29.py` | 80,83,88 | 3906 | 2a50b09adff555db |
| `lead/check_masking_20261109/_cm_tmp/d29/and_kill_1/check_d29.py` | 80,83,88 | 3906 | 2a50b09adff555db |
| `lead/check_masking_20261109/_cm_tmp/d29/b_kill_1/check_d29.py` | 80,83,88 | 3934 | 1648224881829853 |
| `lead/check_masking_20261109/_cm_tmp/d29/b_kill_2/check_d29.py` | 80,83,88 | 3934 | 2399e95a43eaafa4 |
| `lead/check_masking_20261109/_cm_tmp/d29/control/check_d29.py` | 80,83,88 | 3906 | 2a50b09adff555db |
| `lead/check_masking_20261109/_cm_tmp/d29/neg_ctrl/check_d29.py` | 80,83,88 | 3906 | 2a50b09adff555db |
| `lead/check_masking_20261109/_cm_tmp/d29/neg_ctrl_all/check_d29.py` | 80,83,88 | 3906 | 2a50b09adff555db |
| `lead/check_masking_20261109/_cm_tmp/d30/a_kill_1/check_d30.py` | 80,83,88 | 3926 | 6cb737963fc62a0e |
| `lead/check_masking_20261109/_cm_tmp/d30/a_kill_2/check_d30.py` | 80,83,88 | 3926 | 6cb737963fc62a0e |
| `lead/check_masking_20261109/_cm_tmp/d30/and_kill_1/check_d30.py` | 80,83,88 | 3926 | 6cb737963fc62a0e |
| `lead/check_masking_20261109/_cm_tmp/d30/b_kill_1/check_d30.py` | 80,83,88 | 3955 | 132685366f014171 |
| `lead/check_masking_20261109/_cm_tmp/d30/b_kill_2/check_d30.py` | 80,83,88 | 3951 | b1670537e12a6d7c |
| `lead/check_masking_20261109/_cm_tmp/d30/control/check_d30.py` | 80,83,88 | 3926 | 6cb737963fc62a0e |
| `lead/check_masking_20261109/_cm_tmp/d30/neg_ctrl/check_d30.py` | 80,83,88 | 3926 | 6cb737963fc62a0e |
| `lead/check_masking_20261109/_cm_tmp/d30/neg_ctrl_all/check_d30.py` | 80,83,88 | 3926 | 6cb737963fc62a0e |
| `lead/check_masking_20261109/_cmv_tmp/d29/v_b_kill_2/check_d29.py` | 80,83,88 | 3934 | 2399e95a43eaafa4 |
| `lead/check_masking_20261109/_cmv_tmp/d29/v_neg_ctrl_all/check_d29.py` | 80,83,88 | 3906 | 2a50b09adff555db |
| `lead/check_masking_20261109/_cmv_tmp/d30/v_b_kill_2/check_d30.py` | 80,83,88 | 3951 | b1670537e12a6d7c |
| `lead/d28_ruling_20261106/check_d28.py` | 94,97,98 | 4539 | 5b42a34a40046d7a |
| `lead/d29_ruling_20261106/check_d29.py` | 80,83,88 | 3906 | 2a50b09adff555db |
| `lead/d30_ruling_20261106/check_d30.py` | 80,83,88 | 3926 | 6cb737963fc62a0e |
| `lead/stale_pass_20261109/_sp_sandbox/d28/check_d28_baseline.py` | 94,97,98 | 4539 | 5b42a34a40046d7a |
| `lead/stale_pass_20261109/_sp_sandbox/d28x/a/b/check_d28_baseline.py` | 94,97,98 | 4539 | 5b42a34a40046d7a |
| `lead/stale_pass_20261109/_sp_sandbox/d28x/a/b/check_d28_injected.py` | 94,97,98 | 4569 | f5ae184ca7ddc6cf |
| `lead/stale_pass_20261109/_sp_sandbox/d29/check_d29_baseline.py` | 80,83,88 | 3906 | 2a50b09adff555db |
| `lead/stale_pass_20261109/_sp_sandbox/d29/check_d29_injected.py` | 80,83,88 | 3934 | 2399e95a43eaafa4 |
| `lead/stale_pass_20261109/_sp_sandbox/d30/check_d30_baseline.py` | 80,83,88 | 3926 | 6cb737963fc62a0e |
| `lead/stale_pass_20261109/_sp_sandbox/d30/check_d30_injected.py` | 80,83,88 | 3951 | b1670537e12a6d7c |

**编排方 25 件子集核对**：`_cf_census_out.json:orchestrator_25_check[*]` 的 `bytes_match / sha16_match / any_match / req_match` 全 `true`（窄口径 `orch_any_line`：`_cf_census.py:55-59` 要求同一行有 `any(` + 两处 ` in ` + ` for `）。★ 但 `pass` 列自相矛盾：本会话实跑 `sha256sum` + `sed -n '100p'` 证明 `check_d27.py` 与 `_sp_sandbox/check_d27_baseline.py` 同 SHA256、同 `:100` f-string PASS 行，编排方 `pass` 一为 `[]` 一为 `[100]`（`_cf_census_out.json:orch_pass_contradictions`）。故本件不采用其 `pass` 列，改用 `pass_print = ^\s*print\(.*PASS`（`_cf_census.py:80-83`）。★ 复核方宽口径逐字段比对得 27 处不一致（`_cfv_census_out.json:orch_check.field_mismatches`，`any` 14 / `pass` 13），`bytes/sha16/require_all` 全吻合 ⇒ 这是**窄/宽口径差**，非数据矛盾，两种读法都列出。

### 2.4 同族风险数字（三种口径，均本会话实跑/实读）

| 口径 | 数字 | 来源 |
|---|---|---|
| 严格字面组合（`orch_any` 且 `print("PASS` 立即开头） | **28** | `_cf_census_out.json:summary.n_combo_orchany_passliteral` |
| 宽口径（`orch_any` 且 `pass_print`） | **46** | `summary.n_combo_orchany_passprint` |
| 复核方通用宽口径（`\bany\s*\(` + `^\s*print\(.*PASS`） | **54**，四件生产门禁全命中、`literal_screen_misses_confirmed=[]` | `_cfv_census_out.json:n_literal_any_plus_PASS` |
| AST 静态候选 | **40**（`n=173`，`suspect=3`） | `_cf_detect_out.json`；四件 `four` 全 `CONFIRMED` 且 P1–P4 全 `true` |
| 40 件按 SHA 去重 | **11** 个字节串；**27** 件与四件生产门禁字节完全相同、**13** 件为已注入哨兵的变体 | 本会话 `python -I -X utf8 -c` 分解 `confirmed` |
| 复核方独立判据 | `CONFIRMED 28 / SUSPECT 21 / NOT_FAMILY 122 / SUSPECT_ANTI_MASKING 2` | `_cfv_census_out.json:my_verdict_counts` |
| 文本判据（48 件候选内） | `CONFIRMED 37 / SUSPECT 2 / NOT_FAMILY 9` | `_cf_lineage_out.json:family_counts` |
| 173 件按 SHA 去重 | 134 个不同字节串、16 个重复组 | `_cfv_lineage_out.json:n_distinct_check_py` / `n_duplicate_groups` |

★ **「字面 `any()`+PASS 筛会漏掉 d28/d27」标 unconfirmed**（复核 verdict=`partial` 破口①）：该结论只在撰写件自定义窄口径（`_cf_census.py:55-59` 的 `orch_any_line` + `:80` 的 `print("PASS` 立即开头）下成立 —— d28 `check_d28.py:97` 是 `any(present)`（布尔列表 Name，非生成器）、d27 `check_d27.py:100` 是 f-string PASS；在通用宽口径下四件全命中（54 件、零漏判）。筛查仍必须用代码级判据（§4），但「漏判」叙事不作为确定结论。

★ **40 件表述须限缩**：40 件是 AST **静态结构命中**，其中 13 件是 `_cm_tmp` / `_cmv_tmp` / `_sp_sandbox` 里已注入坏针的副本（如 `d28x/a/b/check_d28_injected.py`、`_cmv_tmp/d27/v_b_kill_2/check_d27.py`），故「全库 40 件都带同一缺陷代码」**不成立**，只是同一函数模板的静态候选 —— 与撰写件自述「静态只给候选，确诊仍需动态哨兵注入」一致。

### 2.5 写法像但实为逐输入的区分（逐件确定判断）

| 件 | 代码级证据 | 确定判断 |
|---|---|---|
| `lead/d25_ruling_20261106/check_d25.py` | 本会话 `grep -n 'any('` → `NO_ANY_IN_D25`（0 命中）；`:58,:60` 单词检查 | **NOT_FAMILY**（确定）：无 `any()` 塌缩 |
| `lead/d26_ruling_20261106/check_d26.py` | `:85` `any("本次不授权" in body for body in …)`、`:87` `any("勘误" in body and "挂账" in body …)`、`:90` `any(bodies.get(…))` —— 三个 `any()` 都是跨 section body 的**存在性/非空**检查，非 k 词 OR | **NOT_FAMILY 于本族**（确定）；但 `PENDING:162` 记 exit=0、未注射实证 ⇒ 列 **SUSPECT / 未验**（`_cf_detect_out.json:suspect` 含此件）。复核方 `_cfv_census.py` 把它误判 `CONFIRMED`，撰写件判 SUSPECT 更准确 |
| `lead/b2b_candidate_review_20261106/check_semantic_review.py:330` | 本会话 `sed -n '326,332p'` 实读：`for p in passes: print(f"PASS {p}")` 在 `for` 内 | **NOT_FAMILY**（确定）：逐检查项可归因 |
| `lead/b2b_candidate_review2_20261106/check_semantic_review_r2.py:358` | 本会话 `sed -n '354,360p'` 实读：同样 `for p in passes: print(f"PASS {p}")` | **NOT_FAMILY**（确定） |
| `lead/stall_event_def_20261106/check_stall_def.py:244` | `sed -n '240,246p'` 实读：`for p_msg in passed_items: print(f"PASS: {p_msg}")` | **NOT_FAMILY**（确定） |
| `lead/early_trigger_feasibility_20261106/check_feasibility.py` | 本会话 `grep -n '\[PASS\]'` 命中 `:119,149,164,176,197,206,214,223,259,333`，逐项 `[PASS] 检查项 N` | **NOT_FAMILY**（确定） |
| `all()` 的用法边界 | `all(` 全库 61 件、`all` 生成器 28 件（`_cf_census_out.json:summary`）；本族四件里 `all()` 只出现在 `check_d29.py:83` / `check_d30.py:83` 的 `require_all=True` 分支和 `check_d28.py:97` 的 `all(present)` | **NOT_FAMILY 判据**（确定）：`all()` 本身不红（`CHECK_MASKING_INJECT.md:454`），粗计数不可当同族数 |
| `out/re_work/qc/W3_20261001/docfix2/check_fileoffset_axiom.template.py` / `.py` | 本会话 `grep` 实读 `:35 NAIVE_FLOOR`、`:48 GOLDEN_POS`、`:59 GOLDEN_NEG`、`:99-104` 「扫描器自检（金样例 + 段落判据），失败即 EXIT=3」、`:161-162` `SCANNER-DEAD`、`:235` 下限打印 | **SUSPECT_ANTI_MASKING**（确定非确诊同族）：有金样例回归 + 下限 + 失能退出硬闸；本会话未注射实证 ⇒ 未验 |
| `lead/refsync_scope_20261109/_rs_carrier_scan.py` | 本会话 `grep`/`sed` 实读 `:165 min((line.find(n) …))`、`:194 --needle action="append"`、`:229 any(n in txt for n in a.needle)`、`:343 ok &= good`、`:346 SELF_TEST = PASS`、`:349 return 0 if ok else 1` | **异族同抽象**（按本件代码模板判据，确定）：CLI `--needle` + `min/argmin` 反向掩蔽 + 非 `check_*.py`；按抽象 k→1bit 判据可算同族（两种读法都列出，`STALE_PASS_INVENTORY.md:167` 记其 A+B 级） |

---

## 3 模板来源追溯

### 3.1 四件逐对相似度（撰写件 `_cf_lineage.py` 实跑 + 复核件 `_cfv_lineage.py` 交叉，本会话解析两 JSON）

规范化行 = 去空行/纯注释；Jaccard 为规范化行集合交/并；difflib 两件因归一化序列不同故数值不同，两列都列。**每行给确定判断，逐对给出确定判定，不作泛化推测**。

| 对 | 共同行 | 仅 a / 仅 b | 行 Jaccard | difflib（撰写件） | difflib（复核件） | 确定判断 |
|---|---|---|---|---|---|---|
| d27\|d28 | 22 | 69 / 89 | 0.1222 | 0.1980 | 0.1018 | 跨模板线；仅 import/常量块与尾部 4 行块相同 ⇒ **不共享实现，确定** |
| d27\|d29 | 19 | 72 / 79 | 0.1118 | 0.1693 | 0.3420 | 跨模板线；无任何 ≥4 行共同块 ⇒ **不共享实现，确定** |
| d27\|d30 | 19 | 72 / 79 | 0.1118 | 0.1693 | 0.3360 | 跨模板线；与 d27\|d29 数值全同 ⇒ **不共享实现，确定** |
| d27\|d25 | 18 | 73 / 53 | 0.1250 | 0.1605 | 0.2689 | 源头范式相似但 d25 无任何 `any()` ⇒ **非本族，确定** |
| d27\|d26 | 69 | 22 / 27 | 0.5847 | 0.7380 | 0.7889 | `sections()` 27/29 行共同、ratio 0.9474；23 行最长连续块 ⇒ **同一模板线 A，确定**；方向 neither_subset ⇒ 谁抄谁 **unconfirmed** |
| d28\|d29 | 30 | 81 / 68 | 0.1676 | 0.2679 | 0.3335 | 共享 `requirements` 四元组骨架；`section_bodies()` 仅 5/30 共同（ratio 0.1695）⇒ **骨架同源、提取器为不同实现，确定** |
| d28\|d30 | 30 | 81 / 68 | 0.1676 | 0.2679 | 0.3698 | 与 d28\|d29 数值全同 ⇒ **骨架同源、提取器为不同实现，确定** |
| d28\|d25 | 18 | 93 / 53 | 0.1098 | 0.1868 | 0.2720 | 无 ≥3 行共同块 ⇒ **非本族，确定** |
| d28\|d26 | 27 | 84 / 69 | 0.1500 | 0.2415 | 0.1066 | 仅 import/零散 4 行块 ⇒ **非本族，确定** |
| d29\|d30 | 84 | 14 / 14 | 0.7500 | 0.8571 | 0.9552 | `section_bodies()` 29/29 逐行相同（identical=true）；14 处常量/词表差异、最长连续块 35 行 ⇒ **同一实现（仅数据不同），确定**；方向 neither_subset ⇒ 谁抄谁 **unconfirmed** |
| d29\|d25 | 17 | 81 / 54 | 0.1118 | 0.2012 | 0.3309 | 无 ≥4 行共同块 ⇒ **非本族，确定** |
| d29\|d26 | 19 | 79 / 77 | 0.1086 | 0.1649 | 0.2711 | 无 ≥4 行共同块 ⇒ **非本族，确定** |
| d30\|d25 | 17 | 81 / 54 | 0.1118 | 0.2012 | 0.3322 | 与 d29\|d25 全同 ⇒ **非本族，确定** |
| d30\|d26 | 19 | 79 / 77 | 0.1086 | 0.1649 | 0.2764 | 与 d29\|d26 全同 ⇒ **非本族，确定** |
| d25\|d26 | 19 | 52 / 77 | 0.1284 | 0.1677 | 0.2723 | 无 ≥3 行共同块，且 d25 无 `any()` ⇒ **非本族，确定** |

**函数体级相似度**（`_cf_lineage_out.json:function_identity`）：
- `sections()`：`d27|d26` 共同 27 行 / 29、28 行、`ratio=0.9474`、`identical=false` ⇒ **同一提取器模板，确定**。
- `section_bodies()`：`d29|d30` 共同 29/29、`ratio=1.0`、`identical=true` ⇒ **逐行同一实现，确定**；`d28|d29` 与 `d28|d30` 均 5/30、`ratio=0.1695` ⇒ **不同实现，确定**。
- 复核件 `_cfv_lineage_out.json:pairs[d29|d30]`：`direction_hint=neither_subset`、`jaccard_norm=0.75`、`difflib=0.9552`、`largest_block=35`、`shared_func_bodies[section_bodies].identical=true`；`d26|d27` 亦 `neither_subset`（J=0.575、difflib=0.7889、最长连续块 23）。全部 d2x 对 `direction_hint=neither_subset`（除字节相同的沙箱副本对）。

### 3.2 确定判断与 unconfirmed 边界

- **确定 A**：四件生产门禁属**同一「同族」**——共享同一函数模板：字面 k≥2 词 OR 表 → `any()` 压成 1 bit → 恰好一个聚合 `PASS` + `return 0` + section 正文提取器喂词测试。`_cf_detect_out.json:four` 四件 P1–P4 全 `true`；抽象式见 `CHECK_MASKING_INJECT.md:445-450`（待证 ∀i 有效、观测量只有 ∃i 命中、不保留 hits 下标）。
- **确定 B**：**不是一条逐字复制链，而是两条模板线 + 一个共同源头范式**。线 A = `d26 ↔ d27`（`sections()` 同源，全文件 J=0.5847 / difflib=0.738）；线 B = `d28 ↔ d29 ↔ d30`（`requirements` 四元组 + `require_all` 骨架；`d29|d30` 逐行同一实现；`d28` 自带 30 行 `section_bodies()`，与 d29/d30 的 29 行版只 5 行共同）。跨线 J ≤ 0.1676 ⇒ 共享的是函数模板，不是文件字节。
- **确定 C**：`d29|d30` 差异仅 14/14 行（词表/标题常量），最长连续共同块 35 行 ⇒ 二者是**同一实现**，确定；`d27|d28` 等跨线对无任何 ≥5 行共同块 ⇒ **不共享实现**，确定。
- ★ **unconfirmed（复核 verdict=`partial` 破口②）**：`_cf_REPORT.md:26-28,70` 的「mtime 19:33:47 < 21:57:57 ⇒ d30 抄 d29」「d27 抄 d26 的提取器」「d29 抄的是 d28 的四元组骨架」等**方向/作者**判断。证据：相似度是对称量、复核件全部 `direction_hint=neither_subset`；`_cf_lineage.py:40-56` 的 `pairwise()` 只算对称指标、无任何方向判据；本会话实跑 `git log` 五件全空、`git status` 六目录全 `??`，mtime 可被复制/改写。`_cf_REPORT.md:70` 自己也写「判不了历史作者归属与是否被改过」—— 一边判不了、一边用「抄」自相矛盾。**本件只写「两条模板线 + 共同函数模板」，不写谁抄谁**。要改判需 git 作者/提交链或不可篡改时间戳，本会话拿不到。

### 3.3 最早件（本会话 `stat -c '%y|%s|%n'` 实跑）

| 件 | mtime | bytes | 定位 |
|---|---|---|---|
| `out/re_work/qc/W3_20261001/docfix2/check_fileoffset_axiom.template.py` | 2026-10-02 01:00:46 | 11843 | 形态相似但带反掩蔽硬闸 ⇒ 非确诊同族 |
| `lead/d25_ruling_20261106/check_d25.py` | 2026-11-06 14:41:54 | 2877 | 源头范式（格式门禁，无 `any()`） |
| `lead/d26_ruling_20261106/check_d26.py` | 2026-11-06 14:59:27 | 4245 | 源头范式（`sections()` + 八项格式检查） |
| **`lead/d27_ruling_20261106/check_d27.py`** | **2026-11-06 16:41:55** | **3764** | **同族原件中最早件**：首次引入 k 词 OR + `any()` |
| `lead/d28_ruling_20261106/check_d28.py` | 2026-11-06 18:42:26 | 4539 | 引入 `require_all` 四元组 |
| `lead/d29_ruling_20261106/check_d29.py` | 2026-11-06 19:33:47 | 3906 | 线 B 的 29 行 `section_bodies()` |
| `lead/d30_ruling_20261106/check_d30.py` | 2026-11-06 21:57:57 | 3926 | 与 d29 同一实现 |

全库最早 `check_*.py` 在 2026-09-26 `out/re_work/re_sprint/`（`_cf_lineage_out.json:mtime_first20` 前 12 件），无 `any()`+PASS 组合。`_sp_sandbox/check_d27_baseline.py` 与生产 d27 字节/指纹全同但 mtime 为 2026-11-09（沙箱复制时点），不作为最早件依据。

### 3.4 原始写法意图（逐行直读）

`check_d27.py:1` / `check_d26.py:1` docstring 为 `"Read-only D-27 gate …"` / `"Read-only D-26 gate …"`；`check_d26.py:21-48` `sections()` 收二级标题正文，`:72-97` 检查 verdict 行、7 个必需小节、`本次不授权`、`勘误`+`挂账`（AND）、`未背书` 非空、引用 ≥8、`selfBias` ⇒ **意图是「裁决书格式/机械合规」，不是验事实**（`STALE_PASS_INVENTORY.md:196` 同判）。

缺陷进入点（确定）：`check_d27.py:81-88` 首次把「正文须含 X」泛化成「正文须含 X 或 Y」，用 3 元组 `("外推","卡顿不存在")` + `any(keyword in body …)`，并沿用「逐项 `errors.append` + 末尾一行 `PASS`」汇总；`check_d28.py:89-99` 再引入 `requirements` 四元组 + `require_all` 旗标把 OR/AND 并进同一循环（`:97` `any(present)`）；`check_d29.py:75-89` / `check_d30.py:75-89` 换成双层 `matches` 列表 + `any(matches)` 但**逐行同构**。三者共同点：k 个观测压成 1 bit，不保留命中下标。

### 3.5 是否扩散到别处（确定 + 连带）

扩散链（本会话 grep / find 实跑）：4 件生产门禁 → 台账 `PENDING_DECISIONS.md:92/105/117/129` → D-27→D-28→D-29→D-30 引用链（`PENDING:113,125`、`RULING_D30.md:6`）→ 审计沙箱/注入副本（`_cm_tmp` 22、`_cmv_tmp` 5、`_sp_sandbox` 9 落在 40 件口径内）→ 12 件非 `check_*.py` 的 `_w_dNN_[ABS].py`（`find … | wc -l` = 12；其中 9 件带四元组，如 `_w_d29_A.py:75-88` 仍整段 OR 塌缩 + `:105-106` 单行 PASS）→ 交付件 `REFSYNC_SCOPE_FIX.md:251/252/253` 三行（属异族同抽象的 `_rs_carrier_scan.py`）。

- `grep -rln "for number, title, words, require_all in requirements" --include="*.py" . | wc -l` → **38**；本会话 Python 拆分 = **29 件 `check_*.py` + 9 件非 `check_*.py`**（d28x/d29/d30 的 `_w_dNN_A/B/S.py`）。★ 撰写件写「12 件非 `check_*.py` 的 `_w_dNN_[ABS].py` 注入副本」带四元组 —— 12 是副本总数，带四元组的只有 9 件（3 件 `_w_d27_*.py` 源自 3 元组 d27），此处按实跑更正。
- `grep -rln "require_all" --include="*.py" . | wc -l` → **44**（本会话时点，含写域内 4 件 `_cf*/_cfv*` 生成脚本、`_cm_inject.py`、`_mev_final.py` 及 12 件 `_w_dNN_*.py`）；普查件记 42 ⇒ 撰写期后新增文件造成的**时点差**，如实记，不判孰错。
- ★ 连带影响（确定）：按字面批量替换会连带改动证据生产副本，必须先分离审计沙箱与生产门禁；`REFSYNC_SCOPE_FIX.md:251/252/253` 三行 PASS 失效会推翻 `:243` 的 **R6 负控自检**承诺与 `:273`（4 件）、`:274`（6 件）、`:276`（主答案 4 件）、`:282-286` 六行件数表（`STALE_PASS_INVENTORY.md:167`），但**不波及任何 D-27..D-30 裁决**。

---

## 4 代码级判据

### 4.1 形式判据（同一段写法 / 同一个函数模板，不是名字像）

抽象语义（`CHECK_MASKING_INJECT.md:445-450`）：待证 `∀i 输入_i 有效`，观测量只有 `∃i 命中`，`PASS` 把 k 个输入压成 1 bit 且不保留 `hits=[命中下标]` ⇒ 逐输入可归因 = 否。`DISTINGUISHABLE_PASS = AND_k(真实逐输入自检)`（`:450`）。落到 AST/源码的四条判据：

| 判据 | 代码级定义 | 四件落点（本会话 Read 直读） |
|---|---|---|
| **F1** | 字面元组/列表表的行含 k≥2 个字符串词，且该行走 OR 分支（`require_all=False` 显式旗标，或 d27 式无旗标的 3 元组） | `check_d27.py:81-85`（`("外推","卡顿不存在")`）；`check_d28.py:89-93`（`("历史数字","1681"), False`）；`check_d29.py:75-79`（`("互斥","前提"), False`）；`check_d30.py:75-79`（`("93.98","误报率"), False`） |
| **F2** | `any(...)` 把该 k 词 OR 塌缩成单个布尔：生成器成员测试 / 布尔列表绑定后 `any(Name)` / `any(matches)` | `check_d27.py:86-87` `any(keyword in body … for keyword in keywords)`；`check_d28.py:96-97` `present=[word in body …]` + `any(present)`；`check_d29.py:82-87` / `check_d30.py:82-87` `matches=[all(…) if require_all else any(…) …]` + `if not any(matches)` |
| **F3** | 恰好一个**聚合** `PASS` print（不在 `for` 内）+ `return 0`/退出；无逐词 `HIT/DEAD` / `PER_NEEDLE` 输出 | `check_d27.py:100-101` 单行 f-string PASS + `return 0`；`check_d28.py:115-116`；`check_d29.py:105-106` `print("PASS")`；`check_d30.py:105-106` |
| **F4** | section 正文提取器把 Markdown 小节喂给词测试 | `check_d27.py:21-50 sections()`；`check_d28.py:21-50 section_bodies()`；`check_d29.py:18-46` / `check_d30.py:18-46 section_bodies()`（二者逐行全同） |

`grep` 级 4 步判据见 `CHECK_MASKING_INJECT.md:452-459`；本件采用的判据比「名字含 check_」「同目录 d2*」更严：逐输入打印件（§2.5）F3 为假，不归族。

### 4.2 确诊与存疑清单（确定）

- **CONFIRMED（生产门禁，4 件）**：`check_d27.py` / `check_d28.py` / `check_d29.py` / `check_d30.py`。`_cf_detect_out.json:four` 逐件 `P1–P4=true`；四件「坏针仍 PASS」的既有实证见 `STALE_PASS_INVENTORY.md:126-131`（4 行逐件列 OR 词表与 `check_dNN.py` 行号）与 `CHECK_MASKING_INJECT.md:183-365` —— **本会话未独立复现注入，标未验**（§6.4①）。
- **静态候选 40 件**：`_cf_detect_out.json:confirmed`，含 4 原件 + 27 件字节相同副本 + 13 件注入变体；按 SHA 去重 11 个字节串。★ 这只是 F1–F4 静态命中，**不等于 40 件确诊**。
- **SUSPECT 3 件**（`_cf_detect_out.json:suspect`）：`check_d26.py`（`PENDING:162` 记 exit=0，`STALE_PASS_INVENTORY.md:133,385` 列 C 级未注射）、`out/re_work/qc/W3_20261001/docfix2/check_fileoffset_axiom.py` 与 `.template.py`（带 GOLDEN/NAIVE_FLOOR/EXIT=3 反掩蔽硬闸）。三者本会话均未做哨兵注入 ⇒ **未验**，不冒充确诊或排除。
- **NOT_FAMILY 130 件**（AST 口径 173−40−3）；复核方独立口径为 `NOT_FAMILY 122 / SUSPECT 21 / CONFIRMED 28 / SUSPECT_ANTI_MASKING 2`。两套口径差来自 F3/F4 严格度与 d28 沙箱副本，如实并列。

### 4.3 自动化检测设计（已实现 + 必须补强）

已实现：`lead/check_family_20261109/_cf_detect.py`，`ast.parse` 一次跑完 173 件（输出 `_cf_detect_out.json`）。P1 抓「元组表行含 ≥2 字符串 + False 旗标或 3 元组」；P2 抓 `any(GeneratorExp/ListComp)` 成员测试、`any(Name)` 与布尔列表绑定；P3 抓聚合 PASS print 与 `for` 内逐项打印、并用 `ast.Module(body=[n], type_ignores=[])` 包 print 再 `ast.walk` 取 `JoinedStr` 常量（`:104-107`，修掉了首版把 d27 f-string PASS 漏判成假阴性）。

★ **「检测器纯代码级 / 直接实现确诊」标 unconfirmed**（复核 verdict=`partial` 破口⑤）：
1. `_cf_detect.py:54-55` 的 P4 是**名字级** —— `n.name in ("sections","section_bodies","section_body","exact_h2_body") or "section" in n.name`。复核方实跑量化 `P4_by_name_hits=48`、`P4_name_AND_body_hits=41`，7 件只有名字无正文结构（`check_b2b.py` 的 `section`、`check_b2_preaudit.py` 的 `section_lines_span`）⇒ 函数改名即漏判，不满足铁律「同一段写法/同一函数模板」的纯代码级要求。应改为 AST 结构判据：函数体含 `splitlines()` + heading 正则收集 + 返回 bodies 映射。
2. 检测器把**已注入哨兵的副本**也判 `CONFIRMED` ⇒ 静态结构 ≠ 确诊。要「直接实现确诊」须补：动态坏针注入 + `DISTINGUISHABLE_PASS = AND_k(REAL per-input self-test)`（`MASKING_EFFECT_AUDIT.md:176`）、每根输入单独跑并绑定脚本 SHA256 + 输入语料指纹（`STALE_PASS_INVENTORY.md:251-268` 第 4 条）、`require_all=True` 的 AND 项排除在 `AND_k` 之外（`CHECK_MASKING_INJECT.md:539-540`，`and_kill_1` 实证 `EXIT=1`）。
3. 复核方 `_cfv_census.py` 把 `check_d26.py` 误判 `CONFIRMED`（其三个 `any()` 是跨 body 存在性检查），说明 F2 还需区分「k 词 OR」与「跨样本存在性」—— 撰写件 `_cf_detect.py` 判其为 SUSPECT 更准确。

### 4.4 其它值得普查的族（按写法，不按名字）

| 族 | 代码级锚点 | 状态 |
|---|---|---|
| `min()/argmin` 反向掩蔽 + `ok &= good` + 单 `SELF_TEST` | `_rs_carrier_scan.py:165,229,343,346,349` | 异族同抽象；A+B 级（`STALE_PASS_INVENTORY.md:167`），`REFSYNC_SCOPE_FIX.md:251/252/253` 三行依赖 |
| `0==0` 空真 PASS / `verify_hooks` 假绿 | `GOAL_THREE_TARGETS_20261018.md:261,262,327` | D 级、异族、已自认（`STALE_PASS_INVENTORY.md:176`） |
| CWD 相对路径使门禁结果随 `cwd` 漂移 | `check_d27.py:8` `DIRECTORY = Path("lead/d27_ruling_20261106")` vs `check_d29.py:50` `Path(__file__).resolve().parent` vs `check_d28.py:54-55` `parents[2]` | 三种路径基准，`STALE_PASS_INVENTORY.md:251-268` 第 1 条「路径坑」 |
| PASS 不绑定输入语料指纹致计数漂移 | 627 → 655 → 662（`STALE_PASS_INVENTORY.md:167`、`CHECK_MASKING_INJECT.md:392`） | 未验（当时三个数字） |
| `require_all=True` 的 AND 项逐词不可归因 | `check_d29.py:83` / `check_d30.py:83`；`STALE_PASS_INVENTORY.md:389` | 未验 |
| 台账裸 `exit=0` 无状态字段 / 制度根因 | `STALE_PASS_INVENTORY.md:348-367`（8 条） | 制度层，非代码族 |

---

## 5 连带影响

### 5.1 四条裁决的台账登记是否写 `exit=0`（本会话实跑）

`grep -n "门禁.*exit=0\|exit=0.*门禁" lead/PENDING_DECISIONS.md` → **7 行**：

| 行 | 内容 |
|---|---|
| `:92` | D-30：门禁 `check_d30.py` 实跑 **exit=0**（2026-11-07 复跑仍 PASS） |
| `:105` | D-29：`check_d29.py` 实跑 **exit=0** |
| `:117` | D-28：`check_d28.py` 实跑 **exit=0** |
| `:129` | D-27：`check_d27.py` 实跑 **exit=0**（含「71 处引用」） |
| `:162` | D-26：`check_d26.py` 实跑 **exit=0** |
| `:186` | D-25：`check_d25.py` 实跑 **exit=0** |
| `:199` | N-1：门禁 **exit=0** |

**确定判断：D-27 / D-28 / D-29 / D-30 四条全部写了 `exit=0`**。`grep -c "D-27\|D-28\|D-29\|D-30" lead/GOAL_THREE_TARGETS_20261018.md` → **`0`**（GOAL 台账零命中）。

### 5.2 实质是否依赖失效 PASS 的独立判断（确定 + 限缩）

**定谳行**（本会话 `grep -n '^main:\|^q1:\|^q2:'` 实跑）：`RULING_D27.md:6 main: B`、`RULING_D28.md:4 q1: A` / `:5 q2: 丁`、`RULING_D29.md:4 q1: 丁`、`RULING_D30.md:4 q1: 戊` —— **零引用自身 `check_dNN.py` 的 PASS**。

**逐字否认句**（本会话 `grep -n "门禁\|exit\|PASS\|退出码"` 实跑）：`RULING_D27.md:3,36,58,69,73,75,77`；`RULING_D28.md:9,62,72,78,80`；`RULING_D29.md:55,67,69,71`；`RULING_D30.md:62,76`。典型：`RULING_D30.md:76`「不把原探针、`check_feasibility.py` 或原门禁计为通过；后三者本次未运行」；`RULING_D28.md:78`「未运行核证脚本、门禁、历史测试、探针或统计重算」；`RULING_D29.md:71`「未运行原探针、门禁、历史语料重算…不记通过」；`RULING_D27.md:75`「退出码 0 由题给 F1 提供，本阶段未重跑」。

**数值来源**：`RULING_D29.md:14` 记本阶段实跑 `_d29_facts.py` 退出码 0、`pureLogicalCounterexampleMs` 六项 true；`RULING_D30.md:76` 记 `_d30_facts.py` 输出 `All numeric assertions passed` / `corpus {files:104, samples:1125992}`；`RULING_D27.md:75` 的数值来自题给 F1。本会话**未重跑**这些数值断言 ⇒ 只判依赖结构，不判结论真值。

**确定判断**：四条裁决的**实质结论确定不依赖自身失效 PASS**（依赖结构判定，无一条反例）。失效的是台账把「裁决书 + FACTCHECK + 门禁 `exit=0`」并列为「已验证」交付包的**证据资格**（`STALE_PASS_INVENTORY.md:213`；`PENDING:90-101/103-113/127-158`）。最接近的形式数字是 `PENDING:129` 的「71 处引用」——由 `check_d27.py:100` 的 gate 产出（`STALE_PASS_INVENTORY.md:155`），本会话未独立重算该 regex ⇒ **未验**。

★ **「零次正面引用」标 unconfirmed**（复核 verdict=`partial` 破口③）：`RULING_D28.md:22` **正面引用** F5「独立核证阶段候选机械门禁 9/9、D-13b 机械门禁 8/8 通过」及 `check_candidate.py:195,:228`、`check_d13b_design_20261106/check_d13b.py:202`；`FACTCHECK.md:31-40` 明载两件他件门禁 `exit=0` 输出 `ALL 9 GATES PASSED! EXIT=0` 与 `[RESULT] PASS — 全部 8 项检查通过（exit 0）`。故撰写件的「对 `check_dNN.py` / PASS / `exit=0` 零次正面引用」不成立。本件**限缩**为：「对**自身四件同族门禁**零正面引用；D-28 有他件门禁的正面引用并明确限缩为题给输入、不记本阶段亲跑通过（`RULING_D28.md:9,72,78`）」。那两件他件门禁是否也失效，本会话**未验**；`RULING_D28.md:13`「这是补齐既定下一门，不是签候选通过」⇒ 不构成对 5.2 结论的推翻。

### 5.3 是否波及其它裁决（确定判断）

- **A 级确诊仅 D-27..D-30 四条**（`STALE_PASS_INVENTORY.md:126-131` 逐件列 OR 词表与源码行号）。
- **C 级其它裁决**：D-26（`PENDING:162`）、D-25（`:186`）、N-1（`:199`，无可复跑脚本）—— 未注射实证 ⇒ **未验**，不冒充确诊或排除（`STALE_PASS_INVENTORY.md:385,390`）。
- **非裁决波及**：`REFSYNC_SCOPE_FIX.md:251/252/253`（A+B 级）与 `:273/:274/:276/:282-286` 六行计数（`:167`）；`GOAL:261/262/327` verify_hooks 假绿（D 级、异族、已自认）。
- **形式引用链**：D-28 是 D-29 / D-30 的上游（`PENDING:113,125`；`RULING_D30.md:6`），故 `PENDING` 的形式链须四件一并补注（`STALE_PASS_INVENTORY.md:176`）。
- **无一条实质依赖门禁 ⇒ 无实质反例**；代价集中在证据资格与台账加注，不在定谳。

---

## 6 复核回件、结论与未验项

### 6.1 复核 verdict 如实记

**`verdict = partial`（如实记，不修饰）**。复核方自报 `ranCommands=22`；撰写方 `ranCommands=47` 系手工点算，本会话无法复核、也不重报自己的调用条数。**按交付要求，`partial` ⇒ 相关判断标 `unconfirmed`**：

| # | 撰写件主张 | 复核结论 | 本件标记 |
|---|---|---|---|
| ① | 「字面 `any()`+PASS 筛会漏掉 d28/d27，已用 AST 补上」 | 通用宽口径 54 件四件全命中、零漏判；28/46 来自 `_cf_census.py:55-59,80` 的自定义窄口径 | **unconfirmed** |
| ② | 「d30 抄 d29」「d27 抄 d26」「d29 抄 d28」方向链 | 全部 `direction_hint=neither_subset`；`git log` 空、六目录全 `??`；mtime 可改写 | **unconfirmed**（只保留「两条模板线 + 共同函数模板」） |
| ③ | 检测器「纯代码级」「直接实现确诊」 | `_cf_detect.py:54-55` P4 名字级（48/41 差 7 件）；静态结构 ≠ 确诊；注入副本判 CONFIRMED | **unconfirmed** |
| ④ | 「对 PASS/exit=0 零次正面引用」 | `RULING_D28.md:22` + `FACTCHECK.md:31-40` 正面引用他件门禁 exit=0 | **unconfirmed**（已限缩为「自身四件」） |

**可确认四项**（复核方明列）：173 件普查、四件生产门禁代码级同族、四份裁决实质不依赖自身失效 PASS、未越界。复核方另如实报告：`check_semantic_review.py:330` / `_r2.py:358` 未直读（未验）—— **本会话已用 `sed -n` 直读该两行，见 §2.5，故该项在本件为已验**；复核方 `_cfv_census.py` 误判 `check_d26.py` 为 CONFIRMED，本件按撰写件判 SUSPECT（见 §2.5）。

### 6.2 ★ 复核回件绑定行（本会话 `python -I -X utf8 -c` 读 bytes 后 `hashlib.sha256` 实算）

被核对象 SHA256 = 3b769d7c64c2725100186439725198dbc134a277914e2cb2e9b0af844fe7671c，字节数 = 3764
被核对象 SHA256 = 5b42a34a40046d7a705776002d7aebe8ffda34248849a75b628d40712d9df268，字节数 = 4539
被核对象 SHA256 = 2a50b09adff555dbce4c5740a2af78b779876cad771b6fdf887ba3c0dc780f14，字节数 = 3906
被核对象 SHA256 = 6cb737963fc62a0e045f51247b4fa57ef190acb0b524da3aa6b7713fd05ee9fd，字节数 = 3926
被核对象 SHA256 = 0018116a350de46dd98bbecc5f7aae15a3bd599a4e82bb5d43f3dc688c7f9f65，字节数 = 4245

依序对应：`lead/d27_ruling_20261106/check_d27.py`、`lead/d28_ruling_20261106/check_d28.py`、`lead/d29_ruling_20261106/check_d29.py`、`lead/d30_ruling_20261106/check_d30.py`、`lead/d26_ruling_20261106/check_d26.py`（母本范式）。本会话 `sha256sum` 交叉验证前四件及 `_sp_sandbox/check_d27_baseline.py` 同值；五值逐字吻合题给【复核】`sha256Line`。

### 6.3 结论

**① 同族总数**（三种口径，均本会话实跑/实读，逐件给确定判定）：
- 按「有台账登记、覆盖裁决的生产门禁」= **4 件**（`check_d27/d28/d29/d30.py`），去重后 **3 套代码模板**（d27 三元组线、d28 四元组+30 行提取器线、d29/d30 四元组+29 行提取器线）。**确定**：四件同族，F1–F4 全中。
- 按「全库带该模板的 `check_*.py` 静态实例」= **40 件**（`_cf_detect_out.json`），按 SHA 去重 **11** 个字节串；其中 **27** 件与四件生产门禁字节完全相同、**13** 件为已注入哨兵变体 ⇒ **「40 件全带同一缺陷」标 unconfirmed**，只作静态候选。另有 12 件非 `check_*.py` 的 `_w_dNN_[ABS].py` 副本带同一 `requirements` 模板（其中 9 件带四元组）。
- 复核方独立口径 `CONFIRMED 28 / SUSPECT 21 / NOT_FAMILY 122 / SUSPECT_ANTI_MASKING 2`；文本判据 `37/2/9`。确定判断：**确诊生产门禁 4 件；SUSPECT 3 件未验；逐输入打印件确定非本族**。

**② 来源追溯结论（确定）**：不是一条逐字复制链，而是**两条模板线 + 一个共同源头范式**。源头 = 2026-11-06 14:41:54 的 `check_d25.py` 与 14:59:27 的 `check_d26.py`「只读机械格式门禁」意图（`check_d26.py:21-48,72-97`）；线 A `d26↔d27`（`sections()` 27/29 共同、ratio 0.9474，全文件 J=0.5847），线 B `d28↔d29↔d30`（四元组骨架，`d29|d30` J=0.75、`section_bodies()` 29/29 逐行全同，`d28` 提取器仅 5/30 共同）；跨线 J≤0.1676。四件共享的是「格式门禁 + k 词 OR + `any()` → 1 bit + 单行 PASS」**函数模板**。**同族原件中最早件 = `check_d27.py`（2026-11-06 16:41:55）**；更早的 10-02 `check_fileoffset_axiom.template.py` 带反掩蔽硬闸，确定非确诊同族；全库最早 `check_*.py` 在 2026-09-26 且无 `any()`+PASS 组合。★ **方向/作者 unconfirmed**（§3.2）。

**③ 逐件改还是统一外壳（确定）**：**统一甲' 外部外壳为主，不逐件改源码**。依据：四件在绝对只读域且 `PENDING:112,124` 明记「不改门禁脚本」；`CHECK_MASKING_INJECT.md:522-534,634` 证明只有甲'（逐输入独立跑自检 + `AND_k` + 坏针注入）通吃四件且被审脚本 **0 行改动**，逐件内嵌需动 3–4 处约 **55 行**（`:634-642`）并破坏只读铁律。但**适配器不能一行通吃**（`:535-540`）：scanner 是 CLI `--needle`（`_rs_carrier_scan.py:194`），三 gate 是源码硬编码字面量且无 CLI ⇒ 走沙箱副本；`d29/d30` 的 `require_all=True` 项必须排除在 `AND_k` 外（`:539-540`，`and_kill_1` 实证 `EXIT=1`）；路径基准三种（`check_d27.py:8` CWD 相对 / `check_d29.py:50` `__file__.parent` / `check_d28.py:54-55` `parents[2]`）。且不能只靠现成外壳：`_sp_andk.py` 是 hardcode 12 副本的**演示外壳、未部署**（`STALE_PASS_INVENTORY.md:251-268`，`_sp_andk.py:27-42` 的 `AND_k(over 2 real per-word runs)`）；`_cm_AUDIT.md` 旧模板套 d29 实测 `BAD_NEEDLE_CAUGHT=False`（`CHECK_MASKING_INJECT.md:544-565`），须用修正版（`:570-628`，作者实跑 `TEMPLATE_EXIT=0`）。落地 = **统一外壳 + 逐件适配器 + 逐件 `hashlib` 指纹绑定 + 台账 7 处就地加注**（`PENDING:92/105/117/129` 与 `REFSYNC_SCOPE_FIX.md:251/252/253`）。★ 本会话**未部署、未跑修复后回归**（§6.4④）。

**④ 判不了什么（确定列出）**：四条裁决实质真值；git 历史作者/复制方向/是否被改过；`d25`/`d26`/N-1 与 10-02 两件 SUSPECT 是否真掩蔽；`require_all=True` 逐词可归因；编排方 `pass` 列真实口径与 `ranCommands=47`；`.git/` 内部与符号链接目标；`PENDING:129`「71 处引用」独立重算；D-28 F5 引用的两件他件门禁是否失效；`_rs_carrier_scan.py` 是否算同族（随判据严格度，见 §2.5 两种读法）。

### 6.4 未验项（逐条标「未验」，不补造）

1. **未验**：本会话坏针哨兵注入实证。四件「坏针仍 PASS」引自 `CHECK_MASKING_INJECT.md:183-365` 与 `STALE_PASS_INVENTORY.md:126-131` 的既有实跑，未独立复现；故 `_cf_detect.py` 的 40 件只算静态候选。
2. **未验**：`_d27_facts.py` / `_d28_facts.py` / `_d29_facts.py` / `_d30_facts.py` 数值断言重跑 ⇒ §5.2 只判「实质依赖结构」，不判结论真值。
3. **未验**：`check_d25.py` / `check_d26.py` / N-1 门禁与 10-02 两件 `check_fileoffset_axiom*.py` 的注射实证（`STALE_PASS_INVENTORY.md:385-386` 列 C 级）。
4. **未验**：修复部署与修复后回归（`STALE_PASS_INVENTORY.md:388`；`CHECK_MASKING_INJECT.md:620-628` 自认只做演示外壳）。
5. **未验**：git 历史全空 + 六目录全 `??` ⇒ 作者身份、复制方向、历史是否被改过（`STALE_PASS_INVENTORY.md:390`）。
6. **未验**：`RULING_D28.md:22` / `FACTCHECK.md:31-40` 引用的 `check_candidate.py`、`check_d13b.py` 两件他件门禁是否也失效。
7. **未验**：`require_all=True` 的 AND 项是否有逐词可归因问题（`STALE_PASS_INVENTORY.md:389`）。
8. **未验**：`REFSYNC_SCOPE_FIX.md:251` 当时三个数字（语料已漂移 627→655→662，`STALE_PASS_INVENTORY.md:167,387`）；`PENDING:129`「71 处引用」独立重算（`:155`）。
9. **未验**：`.git/` 内部与符号链接目标（173 清单边界）；编排方 `pass` 列真实口径与两份 `ranCommands` 手工点算。
10. **未验**：复核方两次 Python 全树 `rglob` 的 `[WinError 1921]` 超限路径内容 —— 本会话未重跑该遍历，只采用 `find` 清单（`_cfv_checklist.txt`）。

---

**只做普查与追溯**：本件未改任何既有脚本、自检件、台账或裁决书；未 commit / push；零真机、零采样代码。新增文件仅在 `lead/check_family_20261109/`（本件及其生成器 `_cf_compose_lineage.py`）。题给【普查结论】的 `severity=high`、四件生产门禁同族、`PENDING` 四行 `exit=0` 证据资格失效，本件均予确认；题给【复核】的 `verdict=partial` 及四处破口，本件如实登记并将相关判断标为 `unconfirmed`。
