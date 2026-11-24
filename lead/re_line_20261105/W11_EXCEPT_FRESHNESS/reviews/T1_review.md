# W11 · T1 回件独立复核（T1_review.md）

```
复核对象 = lead/re_line_20261105/W11_EXCEPT_FRESHNESS/T1_SEMANTICS.md（03:32:54）
         + _w11_t1.py（03:28:00）+ _w11_t1_out.txt（03:28:05）
复核人   = 独立复核员·T1（W11 reviews 岗）
复核时刻 = 2026-11-06（会话内实跑，全部命令见 §7）
写域     = 本 reviews/ 目录（新建），未改任何既有文件
```

## 0 · 结论速览

| 项 | 结果 |
|---|---|
| verdict | **CONFIRMED**（附 2 条精度类 mustFix，均不动摇主结论） |
| sha256BindingPresent | **是**（头部自算 SHA256/字节/行数，与我实算逐字一致） |
| independentlyReproduced | **是**（指纹、行号、数据面、60 趟比对、T3 测试均独立复算） |
| modifiedForbiddenFile | **否**（qc151_trip.py mtime=2026-10-20 00:08 早于会话 17 天；out/re_work 会话窗口内仅 2 个 Mimosa 钩子自身状态件，非 T1 所写） |

---

## 1 · 检查一：回件是否真含自算 SHA256/字节/行数 —— **PASS**

T1_SEMANTICS.md:5 头部：
`SHA256 = 517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636，字节数 = 399508，行数 = 7291`。

我的复算（被核件实路径 `out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py`）：

```
sha256sum → 517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636   ✓ 一致
wc -c -l  → 7291 行 / 399508 字节                                              ✓ 一致
```

三值绑定成立，且该 SHA 与 T1 回件 headline `sha256Harness` 一致。

## 2 · ★检查二：是否修改 qc151_trip.py 或 out/re_work/ 下任何文件 —— **未修改（modifiedForbiddenFile = 否）**

- **git 面**：`out/` 被 gitignore（`.gitignore:33`），`git ls-files` 对该目录为空 ⇒ 无 tracked 改动可言；`git status --porcelain -- out/` 空。
- **mtime 面**：`stat qc151_trip.py` → `2026-10-20 00:08:02 +0800`，早于本会话（11-06 03:08–04:00）**17 天**；其 sha256 与 T1 报告值一致，说明 T1 报告写的就是未改动的现件。
- **全树扫描**：`find out/re_work -newermt "2026-11-05 22:00" -type f` → **仅 2 件**，均为 `.mimosa` 钩子状态件：
  `qc151_u0400_trip/.mimosa/hook-state/sess_dwf-dwfrun-7d468cc0…-actor_2_1.json`（03:19:19）与
  `…/hook-status/…-actor_2_1-056c093906.json`（03:23:54）。实读内容：`touched:[]`、`bashMutation:false`，
  hook-status 明记 `toolName:Edit, file:…/W11_EXCEPT_FRESHNESS/T2_CRITERIA.md` —— 是 **Mimosa 安全钩**
  对 **T2** 会话（actor_2_1）写 T2 件时落下的自身状态，**时间上与 T1 无关**（T1 探针 03:28 才写盘）。
  属工具链副作用，不计为 T1 违规，但如实记录在案。
- **T1 探针代码面**：`_w11_t1.py` 全文 227 行我已通读——只 `open(...,'rb')` 读、`os.walk` 走，唯一写目标是
  `W11/_w11_t1_out.txt`（:20,:225-226），无任何对 out/re_work 的写路径。语义与 T1「只读探针」自述一致。

## 3 · 检查三：T3 测试是否真跑过、四分支是否覆盖 —— **PASS（含我方独立重跑）**

- `_w11_t3_test_out.txt` 末三行：`Ran 14 tests in 0.273s / OK / PASS=14 FAIL=0 / EXIT=0` ✓。
- 四个必备分支齐全（逐条在 `candidate/test_except_freshness.py`）：
  test_01 源件缺失、test_02 原样遗留、test_03 内容变化、test_04 复制失败（write 抛异常；另有 4b read 变体、4c 源缺失前置）。
- **我的独立重跑**：把 `candidate/except_freshness.py` + `test_except_freshness.py` 原样复制到
  `reviews/_t3_recheck/`（沙箱将落在 reviews/ 内，不触碰 out/re_work），`python -I -X utf8 test_except_freshness.py` →
  **`Ran 14 tests / OK / PASS=14 FAIL=0 / EXIT=0`，进程退出码 0**。测试真绿，非纸面声明。
- 注：T3 不是 T1 的交付物；此项按复核单指名完成，结论只用于佐证 W11 交付链，不影响 T1 verdict。

## 4 · 检查四：T1 三分类是否逐条有「文件:行号」支撑 —— **全部有支撑，且我逐条独立核过**

T1 的 7 条三分类（§0 表）逐项复验（凡写「read」= 我直接读 qc151_trip.py 原文；「grep」= 我跑 grep -n）：

| # | T1 判定 | 我的独立验证 |
|---|---|---|
| 1 | Q1 来源链 = 源码明确设计 | `CARRIER_FILES` :213-214（grep）；`EXCEPT_MASTER` :228-230（grep）；`except_reset` def :623、写载体在 :649-653（read）；**无调用点**：grep 全文件 6 处 = def :623 + `rec.add` 字符串 :643/:646/:663 + 注释 :6391 + U-5 note :6408，零调用 ✓；`create_isolated_carrier` :4908、排他 `os.mkdir` :4927、存在性 :4946-4949、字节复制+复读验 SHA :4957-4961（read）；main 调用 :6318-6325（read）；`ERRATA_CARRIER_REBUILD.md:22` 漂移行（read，`except.drift.6694B75E.26405B.bin`、交接 21:05 早于 22:43）；母本 `sha256sum ra2bench/except.txt` = ca175a71…/26515 ✓ |
| 2 | Q2 基线时点 = 源码明确设计（轻缺陷：基线 sha 未落盘） | :6385-6409 read：backup :6387 → 被动读 :6394-6400 → 缺失 None :6402；该块确实无任何 sha256 落盘 ✓ |
| 3 | Q3 调用时机 = 源码明确设计（轻缺陷：三处缺失处理不一致） | grep `copy_post_except_evidence` 全文件恰 2 处 = def :4561 + 调用 :5939；:6042-6052 read：第 1 项 :6043、restore :6048；三处不一致 read 实证：copy_post 返 None :4575-4578、move_out 必需件失败 :5402-5406（is_required :5396、插队 :5384-5386）、`_except_diff` 无 exists 直接 read_text :5978 ✓ |
| 4 | Q4 全链无新鲜性 = 实现缺陷 | grep：`getmtime`=0、`新鲜`=0、`fresh`=0、`st_mtime` 全文件仅 :4420；:4413-4425 read = `_render_log_probe`，对象 `ra2render*.log`（:4416），只记录不比较 ✓ |
| 5 | Q5 carrier_post_state = 留痕；写了但没人比 | :4591-4598 read（写入）；harness 内 3 处全写入侧（grep）；审计读者 `out/re_work/work_chain/CONTINUE_20261003/lead/goal1_gate_offline_20261021/_audit_trips.py:17-18` 等实读——只取路径长度/件数，无任何与跑前备份的比对 ✓（但「仅这 4 件读者」不全，见 §6-obj2） |
| 6 | Q6 归档/读取 = writer-only 留痕 | writer 唯一 :4581；`unlink(` 4 处（hit_png）、`rmtree(` 1 处 :5759（grep 实数一致）；离线读者 `T42E4_FORENSIC_085458ab/_except_post.py:2-9` 实读 = 读单件 size/mtime/头 1200 字节 ✓（但「唯一读者」不全，见 §6-obj2） |
| ★ | copy_post_except_evidence 就新鲜性 = 实现缺陷 | 核心证据我独立复算（§5）：60 趟 match、0 differ；意图与实现对照基于 :4563-4573 docstring（read）与 :4574-4582 实现（read），推理链成立 ✓ |

## 5 · 数据面独立复算（我的探针，无深度上限、不剪枝；输出存 `reviews/_t1review_probe_out.txt`）

- 母本：`sha256sum ra2bench/except.txt` = ca175a71…f39d / 26515 字节 ✓（=常量 :229-230）。
- 源件：`_src_L3_sf10c_20261021/except.txt` = 6694b75e…c251 / 26405 字节 / wc=1045 换行（1046 逻辑行）✓。
- 两棵趟树（chain + `lead/qc161_u0400_trip`）：diff=64、post=112、state=63；diff 全部 (pre=1046,new=0) → **64/64**。
- **E 段主结论复现**：有 receipt 且含 post 的趟 = **60**；逐件（不止首件）比对 `except_post_*.txt` sha vs
  receipt `sha256_dst` → **match=111，differ=0**。T1 的「60/60 趟副本≡继承内容」成立，且我的口径更严（111 件全部相等）。
- SPOT `l3_20261031hb`：receipt sha256_src=sha256_dst=6694b75e…、except_post_20261031T201653580570.txt 同 sha、
  `evidence/20261031T201653597587/except.txt` 同 sha、ct 目录在、carrier_delete_result.json 在 ✓。
- **计数口径差（见 §6-obj1）**：T1 的「find 不设上限 diff=66、post=113」按其字面 scope（两棵趟树）应得 **64/112**；
  66/113 是把 scope 实际扩到 `CONTINUE_20261003/lead` 父目录（qc161_t13_verify_20261017/raw、qc161_t14_run_20261017/raw 各 1 diff；
  q161/ 1 个 post）所致。我又在两树之外找到 lead/l1_u0800_20261020、lead/t55k_20261020 各 1 diff ⇒ **全仓实为 diff=68**。
  但 **4 个树外 diff 我逐一解析，全部 (1046,0)** ⇒ T1 的实质结论「全 (1046,0)、『59 份』计数过期」方向与内容均成立。

## 6 · Objections（不改变 verdict）

1. **【mustFix·计数口径】** T1_SEMANTICS.md §6/§7/§8 把 diff=66/post=113 归于「两棵趟树（chain + repo-root）不设上限」——
   按该 scope 实为 **64/112**（我 find+walk 双口径一致）；66=61(chain 父目录含 t13/t14)+5(root)、113=112+1(q161)，
   「全仓」则还有 lead/l1_u0800_20261020 与 lead/t55k_20261020 各 1（共 68）。实质结论（全 (1046,0)）不受影响，但数字-口径对应关系须改写。
2. **【mustFix·读者枚举】** §5「仓内读者仅 goal1_gate_offline 4 件」与 §6「except_post 唯一读者 = T42E4/_except_post.py」不完全成立：
   `lead/codex_round_20261030/XVERIFY_TRIPS_20261030/_xv_s04_windows.py:76-78` 读 carrier_post_state（仅 dump）；
   `lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S544_c1606d35/V3/v3_census.py:56,72-84` 对 **112 份 except_post 本体**做过全量普查（搜 007CFC9F），
   :101 还把 carrier_post_state 列入清点件；`XVERIFY_S543_0a451d0b/V2/probe_e4_t42.py:25-27` 亦读 except_post。
   **这些读者同样无一做「跑后 vs 跑前」比对**，故 Q5「写了但没人比」、Q6「harness 内零读者」两条主结论不动摇；只是「唯一/仅」须改为「harness 内零读者；仓内离线读者另有 …」。
3. **【nitpick·不须改】** 探针 [C] 称 except_reset「非定义出现仅 4 处」，实为 5 处非定义（漏 :6391 注释行；其过滤器排除了 # 开头行）。结论「零调用点」不受影响（我 grep 6 处全列，无一调用）。

## 7 · 我实跑过的命令（摘要）

`sha256sum` / `wc -c -l`（harness、母本、源件）；`stat -c %y`（harness、W11 各件）；
`git status --porcelain -- out/`、`git check-ignore -v`、`git ls-files`；
`find out/re_work -newermt "2026-11-05 22:00"`（全树 2 件，均 .mimosa 钩子件）；
`grep -n`（def/调用点/st_mtime/getmtime/新鲜/fresh/unlink/rmtree/except_reset/except_post_/carrier_post_state/passive_read/SKIPPED_U5）；
`find …except_set_diff.json|wc -l`（两树 64、out/re_work 61、lead\qc161 5、lead 另 2）；
`python -I -X utf8 reviews/_t1review_probe.py`（自写只读探针：D 清点、E 逐件比对、SPOT l3_20261031hb）；
`python -I -X utf8` 解析 4 个树外 diff 的 (pre,new)；`python -I -X utf8 reviews/_t3_recheck/test_except_freshness.py`（重跑）；
`sed -n` 实读 ERRATA:18-26、_except_post.py:1-12、_audit_trips.py:14-22、qc151_trip.py :5445-5456。

**未做**：未反汇编 gamemd.exe（按 TASK.md 不需要）；未真机跑任何趟（零真机）。

## 8 · 复核员落盘物

`reviews/T1_review.md`（本文）、`reviews/_t1review_probe.py`、`reviews/_t1review_probe_out.txt`、
`reviews/_t3_recheck/{except_freshness.py,test_except_freshness.py}`（重跑用副本，沙箱自动清理）。
未修改 T1 回件与任何既有文件。
