# T2_review · 对 T2_CRITERIA.md 的独立复核

- 复核人：独立复核员（W11/T2 席位）
- 复核时刻：2026-11-06T04:1x+08:00
- 被复核件：`T2_CRITERIA.md`（实测 245 行）+ `_w11_t2_mtime_probe.py` / `_w11_t2_mtime_probe_out.txt`
- 方法：全部关键命令本人重跑；代码引用逐条对行号核读；违禁写域用 git + mtime + SHA 三路核。
- 本复核唯一写域：`reviews/`（探针/测试均在 `reviews/` 内的副本上重跑，未动 T2 原件）。

---

## 0 · 判定

**CONFIRMED**（主体成立：SHA 绑定真实、四方案 A/B/C/D 齐备且结论有据、探针可复现、l1b 抽查数值全部复验一致、未碰违禁文件）。
**但 §7.1 诚实账第 1 条「ERRATA_CARRIER_REBUILD.md 未找到」被驳回**（该文件一直在盘上），列为 mustFix。

---

## 1 · SHA256 绑定核验 —— ✅ 真实自算，复算一致

本人命令与输出（2026-11-06）：

```
sha256sum out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py
→ 517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636
wc -c → 399508 ；wc -l → 7291
sha256sum ra2youli/gamemd.exe
→ 73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476
```

与 `T2_CRITERIA.md` 头部（:3-9）及回件自述 `sha256Harness` 逐位一致。绑定成立。

## 2 · 违禁写域核验（modifiedForbiddenFile）—— ✅ 未修改

1. **qc151_trip.py**：`stat` mtime = `2026-10-20 00:08:02 +0800`（远早于本轮）；当前 SHA = T2 所记绑定值 ⇒ 自 T2 算哈希起字节未变。
2. **git**：`git status --porcelain -- lead/qc151_trip.py out/re_work/` 输出为空；`git diff --stat HEAD -- out/re_work/` 为空。
3. **out/re_work 全树 mtime 扫描**（`find out/re_work -newermt "2026-11-05 00:00" -type f`）：仅 5 件 —
   - 4 件 `.mimosa/hook-state|hook-status/sess_dwf-dwfrun-7d468cc0…-actor_2_1*.json`（03:19:19 / 03:23:54，T2 会话窗口）。本人读其内容：hook-state 为 `{"touched":[],"bashMutation":false,...}` 纯插件基线元数据；hook-status 为 PostToolUse 记录且 `file` 字段指向 `T2_CRITERIA.md`（合规写域内）。与该两目录里自 2026-10-17 起约 90 个同模式会话件对照，判定为 mimosa 插件基础设施副产物，**非 T2 对趟件的内容修改**。
   - `…/qc161_u0400_trip/s4_module_table.txt` mtime = `2026-11-05 19:44:21`，早于本 workflow 启动（11-06 03:08），**非 T2 所为**（归属另行追查，不在本件下判）。
4. **T2 探针临时目录**：`w11_t2_mtime_*` 建在 W11 目录内且自清理，`ls | grep w11_t2_mtime` 仅余 .py 与 _out.txt 两件本人外的 T2 正当工件，无残留。
5. **旁证**：mimosa hook-status 记录 T2 会话唯一 Edit 目标 = `T2_CRITERIA.md`；`D22_RULING/` 三件 mtime 02:18-02:31（leader 建材，先于 run）。

结论：**T2 未修改 qc151_trip.py 与 out/re_work/ 下任何文件内容**。`.mimosa` 插件副产物作为观察项记录在案（objection O4）。

## 3 · 代码引用逐条核对 —— ✅ 全部命中（2 处轻微瑕疵见 O2/O3）

对 `qc151_trip.py`（绑定版）逐行核读：

| T2 引用 | 核对结果 |
|---|---|
| `:4561` def copy_post_except_evidence；`:4575 if not src.exists():`；`:4579 read_bytes`；`:4581` 副本名；`:4583-4585` size/sha256；**全函数无 mtime/新鲜性** | ✅ 逐行证实 |
| `:4926-4927` `carrier_dir = …c_{stamp}_{pid}` + `os.mkdir` 排他；`:4958 d.write_bytes(s.read_bytes())`；`:4973` copy_method；`:4962-4963` sha256_src/dst | ✅ |
| `:675-677` 「不得用 sha 变化判 crash（★ 游戏自身会重写该文件）」；`:679` 新异常判据；`:685` Counter 多重集差 | ✅ 原文逐字一致 |
| `:6387` backup_carrier 调用（launch 前）；`:6390-6409` U-5 被动基线（`:6394-6400` passive_read、`:6396` errors="replace"、`:6406-6408` SKIPPED_U5） | ✅ |
| `:4447-4462` backup_carrier；`:4458` write_bytes；`:4460` 只记 size+sha（无 mtime）；`:4461` backup_sha256 | ✅ |
| `:4465-4499` restore_carrier；`:4489` 只比 sha+size 不比 mtime；`:4477-4479` restore_skipped；`:4492` current_sha256 | ✅ |
| `:766-796` get_process_creation_time，`:790-792` FILETIME→100-ns 计数；`:1107/:1109` launch 锚点；`:1072` def launch_direct | ✅（T2 引 `:766-786` 略短，实体至 :796，见 O3） |
| `:432-434` now_iso 秒级 | ✅ |
| `:6042-6052` run_guarded_steps 序：evidence_copy 第1(:6043) / set_diff 第3(:6045) / restore 第6(:6048) | ✅ |
| `:5973-5985` `_except_diff`，`:5978-5979` 直接重读载体件（先于 restore） | ✅ |
| `:4413-4425` `_render_log_probe`；全文件 `grep -n mtime` 仅 `:4420/:4422` | ✅ 精确两处 |
| `:4591-4596` carrier_post_state.json 五件 post size+sha | ✅ |
| `:5001-5003` handover 证明 `files{name:{sha256}}` | ✅（docstring） |

## 4 · 探针复跑 —— ✅ 全部复现

本人把 `_w11_t2_mtime_probe.py` 原样复制到 `reviews/`（OUT 落在脚本同目录 ⇒ 写域合规）后运行：
`python -I -X utf8 _reviewer_t2_rerun_mtime_probe.py` → **EXIT=0**，探针 [0]-[7] 全部复现：
[0] NTFS；[1] write_bytes 不保留 mtime；[2] copy2 保留；[3] utime 伪造成功；[4] 同内容重写 sha 同/mtime 变；[5] 改内容+utime 拉回 sha 变/mtime 同；[6] 连写 200 次得 **128** 个不同 mtime（T2 测得 122 —— 运行间涨落，两次都证实「部分不可分辨」同量级结论）；[7] 时钟回拨如实标未实测。
⇒ T2 报告的探针证据真实、结论「B 与 A 盲区互不重叠」成立。

## 5 · l1b_20261021 工件复验 —— ✅ 数值全部一致

对 `out/re_work/.../qc161_u0400_trip/l1b_20261021/`（只读）本人解析四件：

- `carrier_creation_receipt.json`：created_at=2026-10-21T18:42:42+08:00；copy_method=read_bytes→write_bytes；except.txt src=`…\_src_L1_sf8_20261020\except.txt`，**sha256_src == sha256_dst == 6694b75e…aac251**，size=26405 —— 与 T2 §1.10 一致。
- `carrier_post_state.json`：except.txt sha256 同上、size 26405。
- `except_set_diff.json`：pre=1046 / post=1046 / new_exception_count=0。
- `qc151_fields.json`（149 条记录）：同时含 `RESTORE.backup_sha256:except.txt` 与 `RESTORE.current_sha256:except.txt`，值均 6694b75e… ⇒ T2 §1.4/§1.9/§5「跑前/跑后哈希工件已在盘上、可离线补算 F」的可行性主张成立。

## 6 · 范围与四方案覆盖 —— ✅

TASK §1.T2 要求逐条评估 A/B/C/D 并说清 mtime 不可靠场景与 B 的同内容重写盲区：T2 §0/§3 四方案齐备；A 的六类不可靠场景（其中[2][3][4][5][6]探针实测、[7]如实标原理项）；B 的四类误判风险；C 触 U-5（`:6390-6408` 政策冲突论证与代码事实相符）；D 与 `:677` 矛盾否决。F/E/C 三问题拆分（§2）与 :677 的「禁 crash 归因、不禁 freshness」读法经原文核对成立。

## 7 · 关联件复核（TASK 检查单第 3/4 条）

- **T3 测试真实跑过**：本人将 `candidate/except_freshness.py + test_except_freshness.py` 复制到 `reviews/_t3check/` 重跑 `python -I -X utf8 test_except_freshness.py` → `Ran 14 tests … OK / PASS=14 FAIL=0 / EXIT=0`，与 `_w11_t3_test_out.txt` 一致；TASK 四分支（源件缺失/原样遗留/内容变化/复制失败 4+4b+4c）全覆盖，另含 T2 盲区（rewritten_same_content）、vanished、时钟回拨旗标等补测。
- **T1 三分类**：`T1_SEMANTICS.md` 三分类一览表 7 行均带 file:line。抽验 3 处成立：`:228` EXCEPT_MASTER 只读母本；`:623` def except_reset 且全文件无调用点（grep 证实仅 def+内部 source 标签+U-5 注释）；`:5939` copy_post_except_evidence 全文件唯一调用点（grep 证实 def:4561 / call:5939）。未见凭感觉归类的条目。

## 8 · 发现的问题

- **mustFix M1（§7.1 被驳回）**：`ERRATA_CARRIER_REBUILD.md` **存在**：`out/re_work/work_chain/CONTINUE_20261003/lead/qc163_a5_prep_20261017/ERRATA_CARRIER_REBUILD.md`，birth=mtime=2026-10-18 00:46:14、2552 字节（本人 `find . -name "ERRATA_CARRIER_REBUILD*"` 命中）。T2 的「find 全仓无此名文件 ⇒ 未验」为假阴性，须更正 §7.1 并补读该件——其内容（A5 交接载体 86 件清空事故、以母本 82+变体 3 件逐件 sha256 重建、归因 UNRESOLVED）正好补强 T2 §7.4「交接路径」警示：交接载体曾被整目录重建，逐件 sha 可验但 **mtime 保留与否仍未验**。
- O2：回件自述 keyFact 写「CTRL1_SHA256 :215」——实际在 **:219**（:215 为空行）。`T2_CRITERIA.md` 正文未引此行号，仅自述件有误，须在汇总稿更正。
- O3（轻微）：`T2_CRITERIA.md` 实测 245 行（自述 244）；get_process_creation_time 实体至 :796（T2 引 :766-786 截短）。「载体目录 ct/ 已被删除链清理（ls 实证不存在）」措辞不准：out/re_work 版 l1b 下 `ct/` 仍在（空目录，mtime 2026-10-21 18:45:22），被清理的是载体实例 `ct/c_184242594319_11992`（carrier_delete_result.json 所记 abspath 已不存在）——实质成立，表述需精确。
- O4：mimosa 插件在 T2 会话窗口内于 `out/re_work/…/.mimosa/` 写入 2 个 hook 状态件（内容为空基线元数据）。属插件自动化副产物、gitignored、与既有 ~90 个同类件同模式；不判为违禁修改，但汇总账应留痕。

## 9 · 未复核 / 超范围

- 「59 份 setdiff 全 0」全量复核未做（T2 已如实声明只抽查 l1b 一份；全量归 T4）——本人仅复验 l1b 一份。
- s4_module_table.txt（11-05 19:44）的实际写入者未追查（先于本 run，非 T2）。
- gamemd.exe 未反汇编（TASK 明令不做）。
