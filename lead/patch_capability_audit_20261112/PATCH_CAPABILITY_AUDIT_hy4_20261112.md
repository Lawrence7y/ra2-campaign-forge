# PATCH_CAPABILITY_AUDIT — 补丁能力审计

- 项目：ra2-campaign-forge 逆向项目（受限执行方）｜写域：仅 `lead\patch_capability_audit_20261112\`
- 采样时间：2026-11-12T01:31+08:00（按 turn 采样）
- 性质：**静态能力审计**。零真机（未启动 gamemd.exe / ra2loader / YURI.exe、未 attach、未读活进程内存、未写 hook/采样/MiniDump）、未部署任何补丁、**未跑 `ra2opt apply`**。
- 依据：在盘材料 `PROGRESS.md`、`ra2opt_audit_stdout.txt`、`ra2opt_status_stdout.txt`、`fingerprints_pre.txt`、`fingerprints.py` + 定向只读 grep/head/glob。材料未直接支持者写「未验」，不补造。

---

## §1 规范基线：`docs\PROJECT_DIRECTION.md` §2.B 七条逐字清单

来源：`docs\PROJECT_DIRECTION.md` §2.B「关键系统安全修改」标题 `:34`，七条为 `:36-42` 逐字；已从 `PROJECT_DIRECTION.md:30-49` 逐行核对，与 `PROGRESS.md:12-18` 一致。基线指纹 `fingerprints_pre.txt:13` = `1b1f56ce022694c9aabb2f58e3d3809b689e977720e3176424d82b251763949b`（10194 B）。

1. **(L36)** 「按目标镜像独立记录 ABI、结构、虚表槽、函数入口、字节窗口和调用契约；原版 game.exe 与尤复 gamemd.exe 的地址不得互用。」
2. **(L37)** 「补丁安装先验证构建身份与原始字节；未知构建或不匹配窗口拒绝安装，并输出原因。」
3. **(L38)** 「每项补丁具备独立开关、安装/卸载日志、必要遥测、失败处理与可实测的完整回滚；新实验开关默认关闭。」
4. **(L39)** 「检验寄存器、栈、线程、对象生命周期和卸载顺序；同时检查安装态、执行态与行为态。」
5. **(L40)** 「涉及模拟结果的修改必须补确定性对拍；涉及存读档的修改必须验证跨会话保存与加载；涉及联机的修改必须验证双方配置一致、协议兼容与同步结果。」
6. **(L41)** 「未通过联机验证的实验功能限定为明确标注的单机范围；客户端 UI 改动也须说明公平性影响。」
7. **(L42)** 「原 exe 保留只读基线；部署和真机执行遵守任务卡的明确写域、单写者和游戏实例独占约束。」

> 七条为**规范要求**（normative），非能力陈述；逐条判定见 §3，「规范要求但无实现」与「有实现但未验证」分别标注。

---

## §2 审计对象：`ra2opt/` 17 个模块清单

来源 `PROGRESS.md:24-27`（「模块清单（`ra2opt/*.py`，17 个文件）」），直接搬入：

`__init__.py`、`__main__.py`、`appcompat.py`、`audit.py`、`backup.py`、`budget.py`、`cddraw.py`、`cli.py`、`game.py`、`inifile.py`、`launcher.py`、`net.py`、`optimize.py`、`pe.py`、`safewrite.py`、`tests.py`、`winproc.py`。

体积/sha256 见 `fingerprints_pre.txt:15-26`（收录 12 个：`__init__.py` 2021 B … `tests.py` 32285 B）；`__main__.py` / `budget.py` / `inifile.py` / `net.py` / `winproc.py` 未收录 → 体积/哈希**未验**。四个目标文件指纹：`backup.py` `b651f734…`(`fingerprints_pre.txt:18`)、`game.py` `b85b638f…`(`:20`)、`pe.py` `b5c39251…`(`:21`)、`safewrite.py` `f4250ea3…`(`:22`)。`fingerprints_pre.txt` 共 36 行，覆盖游戏目录、`ra2opt/`、`ra2render/`、`tools/`、`docs/` 代表件；「未收录」不代表文件不存在。

---

## §2.1 目标 A · `ra2opt/` 守卫 / 回滚能力（七条第 2、3 条）

查证方式：**仅**对 `ra2opt/backup.py`、`ra2opt/safewrite.py`、`ra2opt/pe.py`、`ra2opt/game.py` 定向 grep 定行 + 小范围行段读；未全读、未扩到其他模块实现细节（后续因并发材料触发的 2 处补充定向读单列于 §2.4）。

**Q1 · 版本/构建身份识别 → 有（识别能力）；「未知构建拒绝安装」未验**

- `ra2opt/game.py:20-28` `ExeIdentity(sha256, text_sha256, known, patched)`；`:104-124` `identity()`（`:108` 整文件 `sha256_file()`、`:113` `pe.text_section_sha256()`、`:117` `KNOWN_GAMEMD.get(text_sha)`、`:122` `patched = sha != entry["full_sha256"]`）
- `ra2opt/game.py:121` 不匹配 → `known="未知（exe 被第三方 Detours 补丁改过…）"`（**仅标签，不阻断**）；`:144-148` `ddraw_version()`；`:162-209` PE `FileVersion` 扫描 / `version_tuple()` / `compare_versions()`
- `ra2opt/pe.py:364-380` `.text` 段 SHA-256 作引擎指纹；`:367-369` 「LAA/栈/堆只改 Optional Header，代码段不变」
- `ra2opt/backup.py:314,322,353-355` `seed()` 内 `hashlib.sha256(data).hexdigest()` 用于 `expected` 核对
- 实跑（读留存 stdout，**未重跑**）：`ra2opt_audit_stdout.txt:14` 「[+] 已识别引擎版本」；`:13` 「[+] cnc-ddraw 版本 7.1.0.0（已是最新或无法确认）」（`ra2opt_status_stdout.txt:2` 同）；`:15` 「[+] 已开启 Large Address Aware」（`ra2opt_status_stdout.txt:6-8`：`gamemd.exe LAA=开 栈=4MB` / `ra2md.exe LAA=关` / `ra2.exe LAA=关`）；`:17` 「严重 0 / 警告 0 / 建议 4 / 已达标 4」
- 易混淆：`backup.py:98/102/140/144` 的 `{"version":1}` 是 **manifest schema 版本**，非构建身份。**缺口**：四文件内未 grep 到「未知构建 → 拒绝安装并输出原因」分支（`:121` 只给标签）；`apply()` 入口的复核见 §2.4。

**Q2 · 是否校验原始字节 → 部分有；「安装前逐窗口字节校验 / 不匹配窗口拒绝」未验**

- `ra2opt/backup.py:7` `orig/<文件名> 首次被改动前的原始字节（只写一次，永远保留）`；`:63-79` `snapshot()`（`:71` `resolve_within()`、`:77` `read_bytes()`、`:78` 写入 `orig/`、`:75-76` 已有则不动）；`:147-148` `pristine_files()`
- `ra2opt/backup.py:314-320` `seed()` 文档「`expected` 传 {文件名: sha256} 时逐个核对——只有哈希对得上才接受」，状态含 `hash-mismatch`；`:353-355` 实算 digest 并拒绝不匹配文件
- `ra2opt/game.py:122` 整文件哈希判定偏离已知基线；`ra2opt/safewrite.py:12` 「调用方负责在写入前做备份」；`:3-10,29-45` 仅 `realpath`+`commonpath` 路径守卫、默认不新建、原子替换 —— **属写域守卫，非字节内容校验**
- **缺口**：L37「字节窗口比对 / 窗口不匹配即拒绝」四文件内无线索（`safewrite.py` 全文 69 行）→ **未验**，不能写成「已具备」。

**Q3 · 是否留备份清单 → 有（实现 + 盘上实物 + 实跑输出）**

- `ra2opt/backup.py:8` `manifest.json 每次 apply 的记录：时间/配置档/改了哪些键/注册表前后值`；`:24-26` `AREA_NAME/ORIG_DIR/MANIFEST`；`:84-92` `record_file()/record_registry()/add_note()`；`:95-105` `_load_manifest()/_manifest_path()`；`:107-125` `commit()` 写 `run_id/label/profile/created/files/registry/notes`；`:127-132` 正常退出自动 `commit()`、异常不提交；`:136-138,154-155` `manifest()/has_backup()`
- `fingerprints_pre.txt:12` 实物 `ra2youli\.ra2opt\manifest.json`（937 B，`d4832975…`）
- `ra2opt_status_stdout.txt:10-13` apply 记录 3 条（`20260925-161048 perf 改动 7 个文件` / `161827 perf 1 个文件` / `181013 - 1 个文件`）；`:15` 原始快照 7 项 `RA2MD.INI, ddraw.dll, ddraw.ini, gamemd.exe, ra2.exe, ra2.ini, ra2md.exe`；`ra2opt_audit_stdout.txt:12` 「[+] 存在原始快照，可随时回滚」
- **缺口**：L38「独立开关 / 安装卸载日志 / 必要遥测」在 `commit()` 字段（`:113-121`）无对应项 → **未验**。

**Q4 · 是否支持完整回滚 → 有实现；「可实测的完整回滚」实测结论未验**

- `ra2opt/backup.py:10-11` 「`restore` 把 `orig/` 里的内容覆盖回去，并还原 AppCompatFlags 注册表值，所以任何一次优化都能一键撤销」；`:158-161` `restore(game_dir, *, run_id=None, dry_run=False)`，`:161` 「`run_id` 为空表示全部还原」
- `:169-180` 读 `manifest["runs"]`、按 `run_id` 精确选 targets（找不到抛 `ValueError`）、名字取自 `manifest.files`；`:183-203` 有快照 → 覆盖回并删快照 / 无快照（apply 新建）→ 删除 / `dry_run` 不写；`:205-211` `appcompat.set_layer(..., before)` 还原注册表；`:213-228` 移除已回滚 run、全清则连 manifest 一起清掉 `.ra2opt`；`:232-233` `clean()`「删除全部快照（放弃回滚能力）」；`:274-275` 模块级 `restore()`
- `ra2opt_status_stdout.txt:10` 「apply 记录（可用 restore --run 精确回滚）」
- grep 补充：`restore|rollback|revert|undo` 在四文件仅 5 处命中，**全在 `backup.py`**（`:10/:158/:274/:275/:312`），`rollback/revert/undo` 零命中
- **缺口**：本次受只读边界**未运行 `restore`**、未改动游戏目录，L38「可实测的」无实测结论 → 判「**有实现但未验证**」。`ra2opt_audit_stdout.txt:7` 的 `python -m ra2opt apply --profile perf …` 是体检工具**建议文本**，本次**未执行**。

---

## §2.2 目标 B · B 链对拍件定性（七条第 5 条）

定向读：`lead\b2b_design_20261106\STATE_MATRIX.json`（3,558 B，**全 16 行全读**）；`lead\b2b_design_20261106\B2B_DESIGN.md`（**仅头 80 行**，共 693 行，未全读）。

**一句话定性：这套属于「观测新鲜性」，不属于「确定性对拍」** —— 裁决「崩溃证据文件是否本趟新产生/新写入」（跑前 vs 跑后的存在性、sha256、mtime 与置信度），而非把两次确定性执行的**模拟结果**做逐字节/逐状态对拍。

依据行：

- `STATE_MATRIX.json:1-16` 全件 15 条规则，字段一律 `state/preState/condition/verdict/confidence/usableAsCrashEvidence`，**无**模拟结果、RNG 种子、单位状态、帧序列、双方同步结果字段；`:2-15` 15 条**全部** `usableAsCrashEvidence:false`
- `STATE_MATRIX.json:2-3` 跑前快照未采集 → `unknown/none`；`:4-5,13-14` 采集异常 / 缺 `pre.sha256` / 缺 `post.sha256` → 独立 error 出口「不降级、不静默、不给 high」；`:6-7` `new_first_appearance` / `absent_both`；`:8-12` `leftover_unchanged`（sha 一致+mtime 未变）/ `new_write`（sha 不同 ⇒ 本趟被写）/ `rewritten_same_content`（sha 同+mtime 变大/回拨，置信 high→medium→low）；`:10` 「sha 不同 ⇒ 字节内容不同，本趟被写；是否新异常归集合差（:677）」；`:15` `vanished`「须人工复核；不给 high」
- `B2B_DESIGN.md:46` 「零真机、零运行时复现……不是运行时复现。未运行 `qc151_trip.py` 本体，未启动任何游戏进程」；`:58-62` H07 预初始化 `_pre_freshness_snapshot: dict | None = None`（`:61`「`None` 语义 = 未采集（unknown），绝不等于『跑前无件』」）、H08 在 launch 前才调 `make_pre_freshness_snapshot(...)`；`:6` 「`patched` 文本只存在于检查脚本的内存里，`ast.parse` 后即丢弃」；`:35` 核对的是母本文件 sha256/字节数（`517889c…` 399508 B 等）；`:41-44` 验收口径是「改动清单每条能在同文件 diff 找到对应 hunk」且「不等于已获准应用到母本」；`:48` 「按现状不会 PASS，如实记为『未验』，不伪造复核结论」

规范对照：`docs\PROJECT_DIRECTION.md:40`（§2.B 第 5 条）要求模拟结果**确定性对拍** / 跨会话存读档 / 联机双方配置一致·协议兼容·同步结果；`:44`（§2.B 后「优先逆向」段）才是「**对拍从少量可控函数和固定场景开始扩展**」原文出处（任务卡归到第 5 条，按原文更正为 **L44**）。→ B 链件**不能充当 L40 确定性对拍的证据**。`:48` 的「以下是待实现目标，不表示已经具备」**仅针对 §C**，不可外推；§2.B 规范性由 `:34` 标题及 `:36-42` 的「必须/不得/先验证」措辞确立。时点差异：`B2B_DESIGN.md:48` 自陈其会话「全仓无 `check_b2b.py`」，本次实见 `lead\b2b_design_20261106\check_b2b.py:3-11`；按各自材料如实并列，不合并推断。

---

## §2.3 目标 C · 门禁 / 对拍脚本抽样（第 5 条与 `PROJECT_DIRECTION.md:44`）

方法：单级目录列举（`Get-ChildItem -Directory`，**未递归遍历**）取 `lead\` 下按末尾 YYYYMMDD 倒序的最近 20 个日期目录；再用 glob 按文件名模式列出（**只列文件名**）：`check_*.py`、`_verify*.py`、`*_verify*.py`、`*check*.py`、`*verify*.py`。

最近 20 目录（单级列举所得，8 个 `*_20261112` + 12 个 `*_20261111`）；命中文件所在目录仅 `round_gap_disposition_20261112`、`re_ledger_apply_20261111`、`docs_drift_20261112`。

命中文件名：

- **`check_*.py`：0 个**（`lead/*_20261112/check_*.py`、`lead/*_20261111/check_*.py` 均 No files found）。补充：`check_*.py` 集中在更早 `20261106` 目录（18 个，如 `check_b2b.py`/`check_d25.py`/`check_candidate.py`），**不在最近 20 内，不计入**
- **`_verify*.py`：2 个** → `_verify_census.py`（`lead\round_gap_disposition_20261112\`）、`_verify.py`（`lead\re_ledger_apply_20261111\`）
- **`*_verify*.py`：追加 1 个** → `_fd_verify_docs.py`（`lead\docs_drift_20261112\`）
- **`*check*.py`：4 个** → `_integrity_check.py`、`hash_recheck_20261112.py`、`_fix_checks.py`、`final_check.py`（末一个为**本次写域内新建**，非既有门禁，见 §6）

挑 3 个读头 20 行 → 函数级 / 场景级判定：

| # | 脚本 | 判定 | 依据行 |
|---|---|---|---|
| 1 | `_verify.py`（`lead\re_ledger_apply_20261111\`） | **函数级**（单件/字节级窄口径，无场景矩阵） | `:2-14` 7 条固定断言（a. `after` 前 `before_bytes` 字节的 sha256 == before 全文件 sha256；b. §605…§609 各恰好 1 次；c. 追加段起止行号/字节数；d. UTF-8 读回行数 = 旧+追加；e. 5 段逐字正文逐字节比对；f. 只读文件未动；g. 零真机只读边界）；`:28-36` 硬编码 `EXPECTED_BEFORE_BYTES=759518` / `EXPECTED_BEFORE_SHA256=2baa0de4…` / `EXPECTED_APPEND_BYTES=28432` |
| 2 | `_verify_census.py`（`lead\round_gap_disposition_20261112\`） | **场景级**（固定数据窗口 / 固定口径对拍） | `:2-3` 「核对 `_enum_rounds.json` 的口径：逐日期顶层计数 / 报告窗口分解 / 第12个C / 枚举后实时churn」；`:15-19` 载入固定快照 `records` 取 `depth==0`；`:23-38` 固定窗口 `[20261106..20261111]` 与报告 `182=153+18+11` 对拍；`:41-44` 锁定「第12个C」 |
| 3 | `_fd_verify_docs.py`（`lead\docs_drift_20261112\`） | **函数级**（单件指纹重算比对） | `:2-3` 「recompute every `docs/` fingerprint and compare with the START manifest」；`:5` `python -I -X utf8 <绝对路径>`；`:10` `import hashlib`；`:15-19` `ROOT/DOCS/WD/EV/TZ` |

**共同边界**：三者均为**静态产物/文件级核验**，读盘上 JSON / 台账 / docs 字节，**没有两次模拟执行的逐状态对拍**（无 RNG 种子、无单位状态、无帧序列、无双方同步结果）。→ 相对 `PROJECT_DIRECTION.md:40` 判**未验**；相对 `:44` 判**部分有**（固定窗口/固定断言的窄口径核验存在，仅覆盖产物一致性）。

范围外补充（**不在最近 20 目录**）：`lead\p11_stations_20261108\_verify_host414a80.py:2-20` 函数/地址级（`:4` capstone、`:6-7` 读**磁盘** `ra2youli\gamemd.exe` 非活进程内存、`:11-13` 解码 `0x414A80..0x414B40`）；`lead\gate_validate_20261108\_verify_hy4_run_vectors.py:15-20` 场景级（`CASES` 固定用例 `v1_launch`/`v2_newedge`/`v3_dual`/`v4_anchor` + 期望 `ok`，但对拍对象是**检查器判定**而非游戏模拟）；`lead\b2b_design_20261106\check_b2b.py:3-11` 机械文档门禁（`:3`「只读，只用标准库」），两者皆非。

---

## §2.4 补充定向复核（并发会话材料触发）

**并发写域事件（如实记录）**：本次审计期间，同一写域内有另一执行方并发落盘 —— `PROGRESS.md` 由 1,952 B 增至 8,478 B（新增目标 A/B/C 结论与「状态：主报告已续写至 §7 收尾回执」），新增 `verify_anchors_stdout.txt`（2,831 B），并于 01:47:54 把 `PATCH_CAPABILITY_AUDIT.md` 整文件覆盖为另一结构的版本（STEP 1–4 + §5/§6 + 附，标题「补丁/修改能力对 §2.B 七条硬要求盘点」，无 §1 七条逐字、§2 17 模块、§3 判定表）。该版本已由本轮 `Copy-Item` **原样保留**为写域内 `PATCH_CAPABILITY_AUDIT_parallel_20261112.md`（37,141 B），未丢内容；主交付本文件恢复为任务卡要求的 §1–§6 结构。最终以哪一版为准由派发方仲裁。

**由并发材料触发、本轮独立复核的 2 处小范围定向读**（超出 §2.1 四文件范围，故单列）：

- `ra2opt/__init__.py:16-27`：`KNOWN_GAMEMD` 以 `.text` 段 SHA-256 为键；`:20-26` 唯一条目 `name="Yuri's Revenge 1.001 (2001-10-31)"`、`size=4825360`、`full_sha256=db264305c8a6963d17f5d189a5a9720d9c95f7757cc19c534c2fbe4e015255aa`、`text_sha256=c0368a17…`；`:18` 明文「整文件 SHA-256 会被我们自己的补丁改掉」。→ 直接解释 §6.3 的快照哈希：`ra2youli\.ra2opt\orig\gamemd.exe`（db264305…）即官方 1.001 原始基线副本，现行 `73201cc…` 为改 PE Optional Header 后的留痕态，与 `ra2opt/pe.py:367-369`、`ra2opt_status_stdout.txt:6` `LAA=开` 一致。**逐字节 diff 未做，差异清单仍未验。**
- `ra2opt/optimize.py:112-135`：`apply()` 入口只校验 `profile ∈ PROFILES`（`:118-119`）与 `g.valid`（目录含 `gamemod.GAMEMD_EXE`，`:121-123`），随后 `bk = backup.BackupSet(...)`（`:133`）；**入口段未见 `identity()` / `KNOWN_GAMEMD` 身份门** → L37「未知构建拒绝安装」在 apply 入口确实缺失，§3 第 2 条据此由「未验」升级为**有直接缺失证据**。仅读 `:105-139`，全函数其余部分是否另有身份校验**未验**（并行方 `PROGRESS.md:32` 称做过全模块 grep 得同一结论，本轮未独立复跑该 grep）。

**并行会话产出、本轮未执行也未并入 §3 判定的材料**（标注以免混淆）：

- `verify_anchors_stdout.txt:9-11,20-21`（并行方实跑 `tools/verify_anchors.py` 的留存输出）：323/323 断言 PASS、`.text` 哈希 `c0368a17…`、`.detour` 原生签名 PASS；但 `:15-17,21` 为 **[REDUCED-COVERAGE PASS]** —— 段级基线未启用，约 15.78%（761,569 B，`.rdata/.data/.rsrc/.detour/PE头/尾部`）无检测区域，`:21` 明写「**非生产放行依据**」。本轮**未跑** `verify_anchors.py`；该输出只说明 `docs/re/anchor_claims.txt` 有 323 条针对 `gamemd.exe` 的静态锚点断言，不构成 L36「逐镜像 ABI / 虚表槽 / 调用契约登记册 + 两版地址隔离」的充分证据。
- 并行版 §6 第 5 条称「仓库内无未改副本可对 `db264305…` 是否真等于未改原始值」—— 与 `ra2opt/__init__.py:23` 及本轮实算的 `ra2youli\.ra2opt\orig\gamemd.exe` = `db264305…` 不符，**按本轮实算更正**（不改写对方文件，仅在本报告记录）。
- 并行方 `PROGRESS.md:31-35,41-51,57` 的其余结论（`optimize.py:221-254` PE 头改前比较、`optimize.py:156-157` ddraw.dll 逐字节相同跳过、`tests.py:355,540 restore_roundtrip` 离线自检、Target C 全仓 192/186 个脚本普查、R3 判定书 PASS=29 等）本轮**未独立复核**，一律不并入 §3 判定，保留为「未验」。

---

## §3 七条逐条判定表

口径：`有` / `部分有` / `没有`；**【规范有·无实现】** = 规范要求但无实现证据；**【有实现·未验证】** = 代码/产物在盘但本次未实测。「没有」= 本次定向范围内未见证据，不等于全仓不存在（§5）。七条已与 `docs\PROJECT_DIRECTION.md:34-42` 逐行核对，与 §1 一致。

| # | 条文 | 判定 | 证据（`文件:行` / 实跑输出） | 缺口一句话 |
|---|---|---|---|---|
| 1 | **L36** 逐镜像 ABI/结构/虚表槽/函数入口/字节窗口/调用契约；game.exe 与 gamemd.exe 地址不得互用 | **部分有** | `ra2opt/game.py:20-28,104-124`；`ra2opt/__init__.py:16-27`（`KNOWN_GAMEMD` 以 `.text` SHA 为键）；`ra2opt/pe.py:364-380`；`fingerprints_pre.txt:33-36`（`tools/verify_anchors.py`/`audit_bytes.py`/`verify_hooks.py`/`docs/re/anchor_claims.txt` 在盘）；`lead\p11_stations_20261108\_verify_host414a80.py:2-18` | **【规范有·无实现】** 未见逐镜像登记册与两版 exe 地址隔离硬约束；`REVERSE_ENGINEERING_AND_PATCHES.md` 406,585 B(`fingerprints_pre.txt:14`) >100 KB 未展开 → 内容**未验**（并行 `verify_anchors_stdout.txt` 的 323 断言仅覆盖 gamemd.exe 静态锚点，见 §2.4） |
| 2 | **L37** 安装先验证构建身份与原始字节；未知构建或不匹配窗口拒绝安装并输出原因 | **部分有** | `ra2opt/game.py:104-124,117,121,122,144-148,162-209`；`ra2opt/__init__.py:19-27`；`ra2opt/pe.py:364-380`；`ra2opt/backup.py:314,353-355`；`ra2opt/optimize.py:112-135`（apply 入口只校验 profile 与目录有效性）；`ra2opt_audit_stdout.txt:13-15` | **【规范有·无实现】** 「未知构建 → 拒绝安装并输出原因」缺失已有直接证据：`game.py:121` 仅标签不阻断、`optimize.py:112-135` 入口无身份门；「字节窗口 / 不匹配窗口」四文件内无线索（`ra2opt/safewrite.py:3-10,29-45` 仅路径守卫）→ 全函数/全模块是否另有实现 **未验** |
| 3 | **L38** 独立开关 / 安装卸载日志 / 必要遥测 / 失败处理 / 可实测完整回滚；新实验开关默认关闭 | **部分有** | `ra2opt/backup.py:8,24-26,84-92,107-125,127-132,158-228,274-275`；`ra2opt_status_stdout.txt:10-15`（3 条 apply 记录 + 7 项原始快照）；`ra2opt_audit_stdout.txt:12`（存在原始快照，可随时回滚） | **【有实现·未验证】** `restore()` 在盘但**本次未运行**（只读边界），「可实测的完整回滚」无实测结论；**【规范有·无实现】** 独立开关/卸载日志/遥测/默认关闭在 `commit()` 字段 `:113-121` 无对应项 → **未验** |
| 4 | **L39** 寄存器、栈、线程、对象生命周期、卸载顺序；安装态/执行态/行为态 | **部分有**（仅静态 PE/栈） | `ra2opt/game.py:31-59`（`laa`/`stack_mb`/`stack_reserve`/`heap_reserve`/`nx_compat`/`has_detour_section`/`writable_executable_sections`/`checksum`/`dll_characteristics`）；`ra2opt_status_stdout.txt:6-8` `栈=4MB`；`lead\p11_stations_20261108\_verify_host414a80.py:2-20` | **【规范有·无实现】** 运行时寄存器/线程/生命周期/卸载顺序检验及三态检查均无；`tools/verify_hooks.py`(`fingerprints_pre.txt:35`) 在盘未读 → **未验** |
| 5 | **L40** 模拟结果确定性对拍；存读档跨会话；联机配置一致/协议兼容/同步结果 | **部分有**（仅固定场景静态核验） | `docs\PROJECT_DIRECTION.md:44`；`lead\round_gap_disposition_20261112\_verify_census.py:2-3,23-38,41-44`（固定窗口 `182=153+18+11`）；`lead\gate_validate_20261108\_verify_hy4_run_vectors.py:15-20`（`CASES` 固定用例 + 期望 `ok`）；`lead\re_ledger_apply_20261111\_verify.py:2-14,28-36`；`STATE_MATRIX.json:1-16` + `B2B_DESIGN.md:46,58-62` → **观测新鲜性** | **【规范有·无实现】** 模拟结果确定性对拍 / 跨会话存读档 / 联机配置·协议·同步结果均未见；**【有实现·未验证】** 上述脚本实跑输出本次未读 → **未验** |
| 6 | **L41** 未过联机验证的功能限定明确标注单机范围；客户端 UI 改动须说明公平性影响 | **没有**（本次范围未见实现证据） | `docs\PROJECT_DIRECTION.md:41`（规范文本）；`PROGRESS.md:26` `ra2opt/net.py` 在清单内；`ra2opt_audit_stdout.txt:3-4` 仅说明 ra2forge 战役包「可以共存」；`B2B_DESIGN.md:5` | **【规范有·无实现】** 单机范围标注 / UI 公平性说明无对应文档或字段；`ra2opt/net.py` 本次未读（范围外）→ **未验**（并行版判「部分有：门控机制有」系其独立查证，本轮未复核，见 §2.4） |
| 7 | **L42** 原 exe 保留只读基线；部署/真机执行遵守明确写域、单写者、游戏实例独占 | **部分有** | `ra2opt/backup.py:7,63-79`；`ra2opt/__init__.py:23`（官方 1.001 `full_sha256` 基线值）；`ra2opt_status_stdout.txt:15`（原始快照含 `gamemd.exe`）；`fingerprints_pre.txt:1,12` 与 §6 前后实算一致；`ra2opt/safewrite.py:3-10,29-45`；`B2B_DESIGN.md:5-6,46` | **【有实现·未验证】** 写域/单写者/实例独占**代码级强制**未见（`safewrite.py` 仅约束路径层级）；原 exe 只读属性未查；本次写域靠任务卡与执行方自律 → **未验**（并发事件本身即说明写域非工具级互斥，见 §2.4） |

**汇总**：有 0 / **部分有 6**（1、2、3、4、5、7）/ **没有 1**（6）。
**关键区分**：① **规范要求但无实现** = L36 登记册与地址隔离、L37 拒绝安装门禁、L38 独立开关·卸载日志·遥测·默认关闭、L39 运行时检验与三态、L40 模拟结果对拍·跨会话存读档·联机同步、L41 单机标注·UI 公平性、L42 写域/单写者/实例独占强制；② **有实现但未验证** = `backup.restore()`（`backup.py:158-228`，未运行）、固定场景/断言脚本（`_verify_census.py`/`_verify_hy4_run_vectors.py`/`_verify.py`，未读实跑输出）、原始字节快照与写盘守卫（`backup.py:7,63-79` / `safewrite.py:3-10`，未做 restore 实测）。
实跑直接支持的结论仅 `ra2opt_audit_stdout.txt:12-15,17` 与 `ra2opt_status_stdout.txt:2,6-8,10-15` —— **前序执行方留存输出**，本轮**未重跑** `ra2opt audit`/`status`，也**未跑** `apply`。

---

## §4 兼容缺口清单（缺实现 / 缺验证 / 缺文档）

### 4.1 缺实现（规范要求，本次范围内无实现证据）

- **L36** 逐镜像 ABI / 结构 / 虚表槽 / 函数入口 / 字节窗口 / 调用契约登记册 + 两版 exe 地址隔离硬约束 —— 现只有 `ra2opt/game.py:104-124` exe 指纹、`ra2opt/__init__.py:19-27` `KNOWN_GAMEMD`、`ra2opt/pe.py:364-380` `.text` 指纹
- **L37** 「未知构建 / 不匹配字节窗口 → **拒绝安装并输出原因**」门禁 —— `ra2opt/game.py:121` 只标签不阻断、`ra2opt/optimize.py:112-135` apply 入口无身份门；字节窗口比对机制（`ra2opt/safewrite.py:3-10,29-45` 只做路径守卫）
- **L38** 独立开关、安装/卸载日志、必要遥测、失败处理链、新实验开关默认关闭 —— `ra2opt/backup.py:113-121` `commit()` 字段仅 7 项，`:127-132` 仅「异常不 commit」
- **L39** 运行时寄存器/线程/对象生命周期/卸载顺序检验 + 安装/执行/行为三态检查 —— 现只有 `ra2opt/game.py:31-59` 静态 PE/栈字段与 `ra2opt_status_stdout.txt:6-8` `栈=4MB`
- **L40** 模拟结果确定性对拍 / 跨会话存读档验证 / 联机双方配置·协议·同步结果 —— 抽样脚本均为静态产物核验（§2.3），B 链为观测新鲜性（§2.2）
- **L41** 单机范围明确标注、客户端 UI 公平性影响说明 —— 查证材料内无对应文档或字段；`ra2opt/net.py` 在清单内未读
- **L42** 写域 / 单写者 / 游戏实例独占的代码级强制 —— `ra2opt/safewrite.py:29-45` 仅约束路径直属层级；§2.4 的并发覆盖事件本身说明写域无工具级互斥

> 「无实现证据」限定本次范围（四文件 + §2.4 两处补充读 + 定向读 + 留存 stdout + 脚本头 20 行），**不等于全仓绝对不存在**；跨模块一律「未验」（§5）。

### 4.2 缺验证（有实现/有产物，本次未实测）

- `ra2opt/backup.py:158-228,274-275` `restore()` 完整回滚 → **未运行**（只读边界）；`ra2opt_status_stdout.txt:10` 仅写「可用 restore --run 精确回滚」
- `ra2opt/backup.py:7,63-79` 原始字节快照可还原性 + `ra2opt_status_stdout.txt:15` 快照清单 → 未演练；快照副本与现行 exe 哈希不同，基线出处见 `ra2opt/__init__.py:23`，**逐字节 diff 未做**
- `ra2opt/backup.py:314,353-355` `seed(expected)` 的 `hash-mismatch` 路径、`ra2opt/game.py:117-122` identity 对未知 exe 的判定 → 未跑
- 三个抽样脚本（`_verify_census.py:2-3,23-38` / `_verify.py:2-14,28-36` / `_fd_verify_docs.py:2-3`）实跑输出 → 仅读头 20 行（+少量续行）
- `ra2opt audit`/`status` 本轮**未重跑**，结论来自前序留存 stdout，时点是否仍成立 → 未验
- 未展开：`fingerprints_pre.txt:14`（406,585 B `REVERSE_ENGINEERING_AND_PATCHES.md`）、`:33-36`（4 个 tools/anchor 件 53,416/32,175/14,437/35,514 B）、`ra2opt/tests.py` 32,285 B；`ra2opt/__main__.py` 等 5 个模块未读
- 真机 / 联机 / 存读档 / 模拟结果 → 铁律禁止，**全部未验**

### 4.3 缺文档

- 七条 ↔ `ra2opt` 能力**逐条映射件**：本报告首次补齐，未见既有对照件
- 「已识别引擎版本」**具体版本号**：`ra2opt_audit_stdout.txt:14` 只有 `[+]` 标记；`ra2opt_status_stdout.txt:2` 仅 cnc-ddraw `7.1.0.0`（但 `ra2opt/__init__.py:21` 已给出 `Yuri's Revenge 1.001 (2001-10-31)` 的版本名，属源码内记录而非报告输出）
- 独立开关/默认关闭策略说明（L38）、三态验收清单（L39）、「少量可控函数 + 固定场景」清单与结果记录（L40/`:44`）、单机范围与 UI 公平性说明（L41）、`restore --run` 回滚演练记录（L38）→ **均未见**
- `REVERSE_ENGINEERING_AND_PATCHES.md` / `docs/re/anchor_claims.txt` 是否覆盖逐镜像 ABI（L36）→ >100 KB 未展开，**未验**

---

## §5 边界与未验

### 5.1 执行边界（本次实际遵守）

- **零真机**：未启动 `gamemd.exe` / `ra2loader` / `YURI.exe` / 任何游戏进程；未 attach、未读活进程内存、未写 hook / 采样 / MiniDump。`lead\p11_stations_20261108\_verify_host414a80.py:6-7` 读的是**磁盘上的** `ra2youli\gamemd.exe` 字节，本次仅引用其文本，**未执行该脚本**。
- **未部署任何补丁**：**未跑 `ra2opt apply`**、未跑 `python -m ra2opt apply`（`ra2opt_audit_stdout.txt:7` 为**建议文本**）、未跑 `restore`/`clean`/`seed`、未跑 `verify_anchors.py`、未运行任何会写游戏目录的操作。
- **写域唯一**：仅 `lead\patch_capability_audit_20261112\` 内新建 4 文件（§6），其余只读；未做 git commit / push / reset / checkout；`ra2youli\` **零改动**；未改 `ra2opt\` 任何文件。
- **防卡死**：未做全仓遍历（`lead/` 目录数多、单文件最大 73 MB 未触碰）；>100 KB 文件未展开，引用仅来自 `fingerprints_pre.txt` 清单行。
- **工具口径**：python 一律 `python -I -X utf8 <绝对路径>`；指纹一律 `hashlib` 实算（`fingerprints.py:63-67`、`final_check.py`），未抄派发材料。
- **并发写域**：§2.4 记录的另一执行方与本会话在同一写域并发落盘，曾于 01:47:54 覆盖主交付；本轮已保留其版本并恢复任务卡要求的 §1–§6 结构。**本会话未修改对方任何文件**（仅 Copy-Item 生成保留副本）。

### 5.2 判定口径局限

- 「没有」= 本次定向范围未见实现证据，**不等于全仓绝对不存在**；跨模块情形记「未验」。
- 「部分有」**不等于「可用」**；L37/L38/L39/L40 运行时环节均**无本次实测**。
- §3 实跑结论全部来自**前序留存 stdout**；本轮未重跑 `ra2opt audit`/`status`，其时点是否仍成立 → **未验**。
- `STATE_MATRIX.json` 全 16 行已全读；`B2B_DESIGN.md` 共 693 行**仅读头 80 行**，§4–§8（含 9 个 hunk 实际内容）→ **未验**。
- 时点差异：`B2B_DESIGN.md:48` 自陈其会话「全仓无 `check_b2b.py`」，本次实见 `lead\b2b_design_20261106\check_b2b.py:3-11`；按各自材料并列，不合并推断。
- 并行方 `PROGRESS.md:31-35,41-51,57` 与 `PATCH_CAPABILITY_AUDIT_parallel_20261112.md` 的结论本轮未独立复核，未并入 §3；两版判定不一致处（如第 6 条「没有」vs「部分有」）以本轮读盘证据为准，仲裁权在派发方。

### 5.3 明确未验清单

1. 七条「规范有·无实现」各项在 `ra2opt/` 其余 13 模块 / `tools/` / `ra2render/` / 406 KB 大文件中是否存在实现 → 未验。
2. `restore()` 真实回滚效果、失败处理、AppCompatFlags 还原完整性 → 未验（未运行）。
3. 现行 `gamemd.exe` 与 `.ra2opt/orig/gamemd.exe` 的**逐字节差异清单** → 未做 diff；基线出处与机制见 `ra2opt/__init__.py:23` / `pe.py:367-369`，仍未验。
4. 模拟结果对拍 / 跨会话存读档 / 联机双方同步 / 三态运行时检验 / 单机范围与公平性 → **全部未验**（零真机）。
5. `ra2opt/tests.py`（32,285 B）用例覆盖与实跑结果 → 未读，未验。
6. `ra2opt/net.py`/`budget.py`/`inifile.py`/`winproc.py`/`__main__.py` 内容 → 未读，未验（仅 `PROGRESS.md:25-27` 列名）。
7. 抽样脚本实跑输出 / PASS 结论 → 未读，未验。
8. 原 exe 是否置只读属性、单写者与实例独占是否有工具级强制 → 未查，未验（§2.4 并发事件提示无跨会话互斥）。
9. `apply()` 全函数其余部分（`:140-356`）是否另有身份门 → 未读，未验。

---

## §6 收尾回执

### 6.1 改了哪些文件（写域内，4 个新建）

| 文件 | 动作 | 说明 |
|---|---|---|
| `lead\patch_capability_audit_20261112\PATCH_CAPABILITY_AUDIT.md` | **新建/恢复** | 主交付，本文件（§1–§6） |
| `lead\patch_capability_audit_20261112\final_check.py` | **新建** | 收尾指纹复核（只读 + `hashlib`） |
| `lead\patch_capability_audit_20261112\fingerprints_post.txt` | **新建** | `fingerprints.py` 本轮输出，36 行 |
| `lead\patch_capability_audit_20261112\PATCH_CAPABILITY_AUDIT_parallel_20261112.md` | **新建（保留副本）** | 并发执行方 01:47:54 版本原样保留，37,141 B，未改其内容 |

**未改**：`PROGRESS.md`（由并发方改写，非本会话）、`verify_anchors_stdout.txt`（并发方新增）、`ra2opt_audit_stdout.txt`、`ra2opt_status_stdout.txt`、`fingerprints.py`、`fingerprints_pre.txt`、`ra2youli\**`、`ra2opt\**` 及 `fingerprints_pre.txt` 所列 36 个既有件（`PRE_POST_IDENTICAL True`）。未做 git commit / push / reset / checkout。

### 6.2 跑了哪些命令 / 只读操作

1. `python -I -X utf8 …\fingerprints.py …\fingerprints_post.txt` → 36 行 `OK`，与 pre 逐行相同。
2. `python -I -X utf8 …\final_check.py` → 两个 gamemd 哈希（6.3）+ `PRE_POST_IDENTICAL True` + 两份指纹文件自身 sha256 同为 `e0b661d66787c1ec1927b5f9e503f37e4ed8770d7cc4bbf04cdd10a08798c931`。
3. `pwsh`：`Get-ChildItem -LiteralPath 'D:\Project\ra2-campaign-forge\lead' -Directory …`（**单级**列举取最近 20 日期目录）；`Get-Item` 查体积；`Copy-Item` 保留并发方版本。
4. `read`（定向）：`PROGRESS.md`、两份 stdout、`fingerprints_pre.txt`、`fingerprints.py`、`verify_anchors_stdout.txt`、`docs\PROJECT_DIRECTION.md:30-49`、`STATE_MATRIX.json`（全 16 行）、`B2B_DESIGN.md:1-80`、`backup.py:1-30/63-132/155-234`、`game.py:1-60/100-129`、`safewrite.py:1-45`、`pe.py:360-381`、`ra2opt/__init__.py:1-32`、`ra2opt/optimize.py:105-139`、6 个脚本头 20 行。
5. `grep`（定行）：四文件 × 4 组关键词（`sha256|hash|version|build|identity` / `orig|pristine|original|verify` / `backup|manifest|snapshot|restore` / `restore|rollback|revert|undo`）。
6. `glob`（**只列文件名**）：`lead/*/check_*.py`、`lead/*/_verify*.py`、`lead/*/*_verify*.py`、`lead/*_2026111[12]/…`，未递归遍历。

> `…` 为 `D:\Project\ra2-campaign-forge\lead\patch_capability_audit_20261112\` 缩写；两次 python 均为 `python -I -X utf8 <绝对路径>` 形式。

**明确未跑**：`ra2opt apply`（含 `python -m ra2opt apply`）、`restore`/`clean`/`seed`、本轮 `audit`/`status`/`verify_anchors` 重跑、任何补丁部署、任何游戏进程启动 / attach / 活进程内存读取、任何 hook / 采样 / MiniDump 代码、任何 git 写操作。

### 6.3 两个 `gamemd.exe` 的 sha256（验收项）

「两个」按**审计前 / 审计后两次实算**口径（同一路径 `ra2youli\gamemd.exe`）：

| 时点 | 来源 | sha256 | 体积 |
|---|---|---|---|
| 审计前 | `fingerprints_pre.txt:1` | `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476` | 4,825,360 B |
| 审计后 | `fingerprints_post.txt:1`（本轮 `hashlib` 实算） | `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476` | 4,825,360 B |

**两者一致，且与验收期望值 `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476` 一致 ⇒ `ra2youli\` 零改动成立。**

补充（第二个**物理副本**）：`ra2youli\.ra2opt\orig\gamemd.exe` = `db264305c8a6963d17f5d189a5a9720d9c95f7757cc19c534c2fbe4e015255aa`（4,825,360 B，本轮实算），是 `ra2opt_status_stdout.txt:15` 所列原始快照之一；`ra2opt/__init__.py:23` 明文记录该值为官方 `Yuri's Revenge 1.001 (2001-10-31)` 的 `full_sha256`（`:18` 说明整文件 SHA-256 会被 ra2opt 自己的补丁改掉），与 `ra2opt/pe.py:367-369`、`ra2opt_status_stdout.txt:6` `LAA=开` 一致 ⇒ 快照为原始基线、现行 exe 为改 PE Optional Header 后的留痕态。**逐字节 diff 未做，差异清单仍未验**（并行版 §6 第 5 条「仓库内无未改副本」的表述按本轮实算更正，见 §2.4）。全量佐证：`PRE_POST_IDENTICAL True`（36 个目标逐字节一致）。

### 6.4 结论一句话

`ra2opt` 在构建身份识别（`ra2opt/game.py:104-124`、`__init__.py:19-27`）/ 原始字节快照与 manifest（`ra2opt/backup.py:7-8,63-125`）/ `restore` 回滚实现（`ra2opt/backup.py:158-228`）上有**静态可确认的实现**，但七条中 **6 条仅「部分有」、1 条「没有」**，必须严格区分「**规范要求但无实现**」（L37 拒绝安装门禁 —— `optimize.py:112-135` 已证入口缺失、L38 开关/遥测、L39 运行时检验、L40 模拟结果对拍、L41 单机标注/公平性、L42 写域强制）与「**有实现但未验证**」（`restore()`、固定场景静态核验脚本、快照可还原性）；在无真机与回滚实测下，不能把「有代码」写成「能力已具备」。

### 6.5 遗留未验项

见 §5.3 九项。优先序建议（**均不在本次授权范围，未执行**）：① `restore` 回滚演练（需另行授权写域与实例独占）；② L37 门禁跨模块查证（`ra2opt/optimize.py:140-356`、`cli.py`、`audit.py`）；③ L40 模拟结果对拍的场景/函数清单；④ 按「>100 KB 只读头尾各 80 行」定向展开 `REVERSE_ENGINEERING_AND_PATCHES.md` 与 `anchor_claims.txt`，确认 L36 登记是否已存在；⑤ `ra2opt/tests.py` 覆盖与实跑结果；⑥ 派发方仲裁：主交付以本 §1–§6 版还是 `PATCH_CAPABILITY_AUDIT_parallel_20261112.md` 为准（两版判定不一致，尤其第 6 条）。

---

（全文完 · 写域 `lead\patch_capability_audit_20261112\` · 零真机 · 未跑 `ra2opt apply`）
