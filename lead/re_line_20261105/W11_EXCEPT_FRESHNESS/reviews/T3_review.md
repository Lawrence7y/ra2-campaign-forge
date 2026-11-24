# T3 独立复核 · 离线修复候选（except_freshness）+ 14 用例测试

复核人 = 独立复核员·T3（workflow actor_5_3）
复核时刻 = 2026-11-06T04:30+08:00 前后
被复核件 = `T3_CANDIDATE.md`、`candidate/except_freshness.py`、`candidate/test_except_freshness.py`、
`candidate/PATCH_SUGGESTION.md`、`_w11_t3_test_out.txt`
本复核写域 = `reviews/`（复核沙箱 `reviews/_t3_review_rerun/`，用后保留作证据，未清理前无 `_t3_sandbox_*` 残留）

## 0 · 总判

**verdict = CONFIRMED**。T3 回件的四项关键主张（SHA256 自算绑定 / 未改禁区文件 /
14 用例实跑全绿且四分支全覆盖 / 引用行号可落点）全部经本人独立重跑或亲读证实。
无 mustFix。

## 1 · 检查一：回件是否真含自算 SHA256 / 字节数 / 行数 —— ✅ 是

- `T3_CANDIDATE.md:3-10` 含强制头部：`qc151_trip.py SHA256 = 517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636，字节数 = 399508，行数 = 7291`，
  并注明自算方法（sha256sum + wc -c + wc -l）、时刻（2026-11-06T03:36+08:00）与路径。
  `candidate/PATCH_SUGGESTION.md:3-10` 亦含同值头部（03:38 实算）。
- **本人重算**（本 ask 期间执行）：
  ```
  命令：sha256sum / wc -c / wc -l
        out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py
  输出：517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636
        399508 / 7291
  stat：mtime = 2026-10-20 00:08:02.206731100 +0800
  ```
  三个值与 T3 自算逐字一致。旁证：T1/T2/T4 回件头各自独立实算的同值
  （`T1_SEMANTICS.md:5`、`T2_CRITERIA.md:5`、`T4_IMPACT.md:5`）——四窗口文件未变。

## 2 · 检查二（★）：是否修改 qc151_trip.py 或 out/re_work/ 下任何文件 —— ✅ 否（modifiedForbiddenFile = false）

本人执行的核（非转述）：
1. **SHA 比对**：现算 sha256 与 T3 回件、T1/T2/T4 回件四处同值（见 §1）。
2. **mtime**：`qc151_trip.py` mtime = 2026-10-20 00:08:02 +0800，早于 T3 工作窗口
   （2026-11-06 03:36–03:52）17 天。若被改动，mtime 必然更新——未更新。
3. **全树扫描**：
   ```
   命令：find out/re_work -type f -newermt '2026-11-06 00:00'
         find out/re_work -type d -newermt '2026-11-06 00:00'
         find out/re_work -path '*/.mimosa/*' -type f -newermt '2026-11-05 23:00'
   结果：仅 2 个 mimosa 插件记账件（hook-state / hook-status），
         文件名含 sess_dwf-dwfrun-7d468cc0-…-actor_2_1（=T2 会话，非 T3），
         mtime 2026-11-06 03:19:19 / 03:23:54（均在 T3 窗口之前），内容 "touched":[]（零文件改动）。
   ```
   **当前 run 的 T3 会话（actor_3_*）在 out/re_work/ 下无任何落痕**；全 run 亦无
   actor_3_* 的 mimosa 记账件。那 2 个插件记账件是 mimosa hook 的自动行为、
   归属 T2 会话，非 T3 所为、非内容修改——如实登记，不计入 T3 违规。
4. **沙箱零残留**：`find`（仓内 maxdepth 3 与 out/re_work 全树）+ `ls -la`
   W11 目录均无 `_t3_sandbox_*`（T3 自查主张复现成立）。
5. **git**：`git status --porcelain -- out/` 为空、`git check-ignore -v` 显示
   `out/` 被 `.gitignore:33` 忽略——git 对 out/ 无账可查，本项结论靠
   mtime+SHA+全树扫描三重印证（如实说明，git 不是本项证据来源）。
6. **PATCH_SUGGESTION.md 仅建议性**：亲读全文，三段 diff 均标「建议性文本，未应用」，
   上下文行与真件逐字吻合（`:4457-4461`、`:4561-4582`、`:5938-5939` 等本人核对），
   而真件 SHA/mtime 未变——未应用，实证成立。

## 3 · 检查三：测试是否真跑、四分支是否覆盖 —— ✅ 是（本人独立重跑复现）

- **T3 输出件** `_w11_t3_test_out.txt`（亲读）：末尾
  `Ran 14 tests in 0.273s / OK / PASS=14 FAIL=0 / EXIT=0`。
- **本人重跑**（复制 candidate 两件到 `reviews/_t3_review_rerun/` 后执行，
  沙箱因测试代码取「测试件父目录的父目录」而落在 reviews/ 内——唯一写域内）：
  ```
  命令：python -I -X utf8
        D:/Project/ra2-campaign-forge/lead/re_line_20261105/W11_EXCEPT_FRESHNESS/reviews/_t3_review_rerun/test_except_freshness.py
  输出：Ran 14 tests in 0.275s / OK / PASS=14 FAIL=0 / EXIT=0
  退出码：EXIT_CODE=0
  ```
  与 T3 主张完全一致。旁证：reviews/_t3check、_t3_recheck 存有前序复核者
  对同一测试的复跑副本。
- **四必备分支逐一在代码与输出中落实**（非凭表面对账）：
  | TASK 分支 | 用例（test_except_freshness.py 行号） | 判定 | 本人重跑结果 |
  |---|---|---|---|
  | 源件缺失 | `test_01_branch1_source_missing`（:43-52） | absent_both / is_new=False / low / notes 含「不能证」 | ok |
  | 原样遗留 | `test_02_branch2_leftover_unchanged`（:54-66） | leftover_unchanged / is_new=False / high | ok |
  | 内容变化 | `test_03_branch3_content_changed`（:68-81） | new_write / is_new=True / high / f_vs_e_note 含「集合差」 | ok |
  | 复制失败 | `test_04_…_write`（:83-93）+ 4b（:95-102）+ 4c（:104-109） | ok=False + stage（write_bytes/read_bytes/src_missing）+ traceback 非空、无静默半成品 | ok |
- 扩展用例 test_05–test_12（post 读失败、同内容重写、vanished、C 模式、
  时钟回拨旗标、run_start 旁证不参与定判、纯函数性、快照失败留痕）全部 ok。
- **纯函数性核**（亲读代码，非只信测试）：`except_freshness.py:25-29` 仅导入
  hashlib/time/traceback/datetime/pathlib——无 subprocess/ctypes/socket，不启动
  进程、不读活进程内存；`classify_except_post`（:99-240）对 post_path 只读；
  写盘仅 `copy_post_evidence_guarded`（:243-278）且只写调用方指定 out_dir。
  沙箱构造于 W11 内（test:19-31 `SANDBOX_PARENT=Path(_W11)`），不涉 out/re_work。

## 4 · 检查四：三分类是否每条有「文件:行号」支撑 —— ✅（职责在 T1，T3 正确留空）

- T3 回件 JSON `classification=[]` 为**正确留空**：TASK §1 明确三分类归 T1
  （`T3_CANDIDATE.md:14-15` 亦自述「T1 语义三分类归 T1_SEMANTICS.md，本件只引用」）。
- 对 T1 三分类表（`T1_SEMANTICS.md:24-31` + `:210` ★ 行）逐条核支撑：7 条全部带
  `文件:行号`（如 :228/:623/:4946-4958/:677、:6394-6408、:5939+:6042-6052+:6048、
  :4420、:4591-4598）。本人对其中关键行号在 qc151_trip.py 亲验落点：
  - `:4420` 确为 `"mtime": _st.st_mtime`（ra2render*.log 匹配记录用，非新鲜性检查）——支撑 T1 第 4 条；
  - `:677` 确为「★不得用 sha 变化判 crash（★游戏自身会重写该文件）」——支撑 ★ 条与 T3 对方案 D 的否决逻辑；
  - `:6387`（backup_carrier 调用）、`:6394-6408`（passive_read / SKIPPED_U5）、
    `:5939`（唯一调用点）、`:6042-6052`（序：evidence copy :6043 先于 restore :6048）均落点吻合。
- T3 自身引用的 harness 行号全部亲验吻合：`:173`（import time）、`:446`（Recorder.add 签名）、
  `:4457-4461`（backup_carrier 只记 path/size/sha256，无 mtime）、`:4561-4599`
  （copy_post_except_evidence：exists 判 :4575、read_bytes :4579、sha :4580、
  write_bytes :4582）、`:4591-4596`（carrier_post_state 写入）、`:4489`
  （restore_carrier `ok = (h == info["sha256"]) and (dst.stat().st_size == info["size"])`——只比 sha+size）。
- T3 判据与 T2 对齐有据：`T2_CRITERIA.md:204-216` §6「推荐判据组合与决策表」实存六分支表。

## 5 · 次要观察（不影响 verdict，无 mustFix）

1. **时刻小矛盾**：T3 JSON 自述「两次实算 03:36 与 03:52」，而件内头部为
   03:36（T3_CANDIDATE.md:6）与 03:38（PATCH_SUGGESTION.md:6）。可能存在第三次
   未留痕实算，无从核；因本人现算同值，不构成实质问题。
2. `test_04c`（test:109）的 `assertFalse(rec["ok"] is None)` 断言偏弱（ok=False 时恒真）；
   同用例的 `assertEqual(rec["stage"], "src_missing")` 已覆盖本意。
3. `candidate/__pycache__/except_freshness.cpython-312.pyc`（mtime 03:57）为
   W11 写域内的导入副产物（时间与 T4 探针窗口 03:49-03:59 吻合），无害。
4. mimosa 插件会在子代理 cwd 落 `.mimosa/hook-state` 记账件——本轮在
   `out/re_work/.../qc151_u0400_trip/.mimosa/` 留下 T2 会话（actor_2_1）两件。
   建议 Leader 知悉该插件侧写行为（内容 "touched":[]，未触真实趟件）。

## 6 · 未验项（如实登记）

- `gamemd.exe SHA256 = 73201cc0…`（TASK 给定锚点）：本复核未重算（零真机范围、
  四项检查不涉）。
- T2 判据可行性论证本身、T4 影响面清单：归各自主复核，本件只核了 T3 引用到的
  锚点（T2 §6 表存在性）。
- T3 补丁 2 的「内联移植版」语义一致性：T3 已如实声明未测（PATCH_SUGGESTION
  属建议文本），本复核不视其为缺陷。
