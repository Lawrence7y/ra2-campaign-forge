# PROGRESS — patch_capability_audit_20261112

- 执行方: ZCode (GLM-5.3-Flash) 重派接手（前任 25 分钟零落盘，已终止）
- 开始时间: 2026-11-12T01:10+08:00（按 turn 采样）
- 写域: 仅 `lead\patch_capability_audit_20261112\`
- 铁律遵守: 零真机、只读边界、python -I、hashlib 实算、不补造

## 第一步 · §2.B 七条逐字摘录

来源: `docs\PROJECT_DIRECTION.md` §2.B「关键系统安全修改」（L34–L42），七条为 L36–L42 逐字:

1. (L36) 「按目标镜像独立记录 ABI、结构、虚表槽、函数入口、字节窗口和调用契约；原版 game.exe 与尤复 gamemd.exe 的地址不得互用。」
2. (L37) 「补丁安装先验证构建身份与原始字节；未知构建或不匹配窗口拒绝安装，并输出原因。」
3. (L38) 「每项补丁具备独立开关、安装/卸载日志、必要遥测、失败处理与可实测的完整回滚；新实验开关默认关闭。」
4. (L39) 「检验寄存器、栈、线程、对象生命周期和卸载顺序；同时检查安装态、执行态与行为态。」
5. (L40) 「涉及模拟结果的修改必须补确定性对拍；涉及存读档的修改必须验证跨会话保存与加载；涉及联机的修改必须验证双方配置一致、协议兼容与同步结果。」
6. (L41) 「未通过联机验证的实验功能限定为明确标注的单机范围；客户端 UI 改动也须说明公平性影响。」
7. (L42) 「原 exe 保留只读基线；部署和真机执行遵守任务卡的明确写域、单写者和游戏实例独占约束。」

（第一步落盘时间点: 本文件即第一步产物。）

## 第二步 · 目标 A: ra2opt/ 盘点

模块清单（`ra2opt/*.py`，17 个文件）:
__init__.py, __main__.py, appcompat.py, audit.py, backup.py, budget.py, cddraw.py,
cli.py, game.py, inifile.py, launcher.py, net.py, optimize.py, pe.py, safewrite.py,
tests.py, winproc.py

### 目标 A 结论（落盘）

- **版本识别：有。** `KNOWN_GAMEMD` 以 `.text` 段 SHA-256 为键（`ra2opt/__init__.py:16-27`）；`game.py:104-124 identity()` 实算整文件 SHA-256 + `.text` 段 SHA-256 做识别，`patched` 标志比较 `full_sha256`。实跑佐证：`ra2opt audit` 输出「已识别引擎版本」「已开启 Large Address Aware」（`ra2opt_audit_stdout.txt:14-15`）。
- **原始字节校验：部分有。** PE 头修改前先 `pe.read` 解析并比较当前栈值/LAA 位，只改需要改的（`optimize.py:221-254`）；ddraw.dll 逐字节相同则跳过写入（`optimize.py:156-157`）；`seed --verify` 用 `full_sha256` 核对来源（`backup.py:307-356`、`cli.py:304-318`）。**缺口：`apply()` 主流程不调用 `identity()`/`KNOWN_GAMEMD`，未知构建不会被拒绝安装**（`optimize.py:112-133` 只校验目录有效性；全模块 grep `identity(` 仅 game.py:104 / audit.py:109 / optimize.py:344 / cli.py:308）。不符合 §2.B 第 2 条「未知构建或不匹配窗口拒绝安装」。
- **备份清单：有。** `.ra2opt/orig/`（首次改动前原始字节，只写一次）+ `manifest.json`（每次 apply 的 run 记录：时间/配置档/文件/注册表前后值/notes）（`backup.py:1-56,95-125`）。
- **完整回滚：有（能力面）。** `restore` 支持按快照覆盖原字节、删除 apply 新建文件、还原 AppCompatFlags 注册表、支持 run_id/dry_run（`backup.py:153-229`、`cli.py:288-301`）。离线自检存在（`tests.py:355,540 restore_roundtrip`），本会话未跑自检（未验）。
- **写域约束：有。** `safewrite.py` 为全项目唯一写盘出口：realpath 规范化 + commonpath 越界拒绝 + 仅基准目录直属层级 + 临时文件原子替换（`safewrite.py:1-62`）。
- **实跑输出**：`python -X utf8 -m ra2opt audit` 已落盘 `ra2opt_audit_stdout.txt`；严重 0 / 警告 0 / 建议 4 / 已达标 4；完整报告由 audit 写入本写域 `ra2opt_audit_out\report.md`。audit 只读游戏目录（`ra2youli`），未写游戏目录。

### 目标 B 结论（落盘）

- **定性一句话：B 链这套设计/判定书属于「观测新鲜性」（崩溃证据文件的新鲜性观测），不是「确定性对拍」。**
- 依据：`STATE_MATRIX.json` 14 行全部判定「跑前/跑后文件快照」的存在性/SHA/mtime 组合（verdict 如 `new_write`/`rewritten_same_content`/`leftover_unchanged`/`vanished`），且每行 `usableAsCrashEvidence:false`；`B2B_DESIGN.md:58-83` 的根治对象全是 `_pre_freshness_snapshot`/`copy_post_except_evidence`/FRESHNESS 字段；R3 判定书确认 F 结论「恒不可作崩溃证据」（`CANDIDATE_SEMANTIC_REVIEW_R3.md:78`）。它观测「异常证据文件是否本趟新写」，不比对模拟结果输出。
- R3 实跑结论：`verdict: PASS`（:21），测试重跑 `PASS=29 FAIL=0`（:110,145），机械门禁 9/9 仅记档 1（:131,146）；并明确「PASS ≠ 可应用到母本」（:23,137）。

### 目标 C 结论（落盘）

- **文件名普查（glob 匹配文件名，非内容遍历）**：`lead/` 下 `check_*.py` 共 **192 个**、`*_verify*.py` 共 **186 个**（glob 按修改时间序返回，全量清单落盘于 spill 文件）。近期（2026-11-06 以后）目录代表：`b2_preaudit_20261106\check_b2_preaudit.py`、`b2b_design_20261106\check_b2b.py`（实见存在，与 B2B_DESIGN.md:48 自陈「无此二文件」为不同时点）、`b2b_candidate_20261106\check_candidate.py`、`d27_ruling_20261106\check_d27.py`、`d28_ruling_20261106\check_d28.py`、`d29_ruling_20261106\check_d29.py`、`d30_ruling_20261106\check_d30.py`、`d13b_design_20261106\check_d13b.py`、`b2b_candidate_review2_20261106\check_semantic_review_r2.py`、`b2b_candidate_review3_20261107\_check_candidate_r3.py`、`stale_pass_20261109\_sp_sandbox\check_d27_baseline.py` 系、`check_masking_20261109\_cm*_tmp\check_d27/d28/d29/d30.py` 系、`andk_rerun_20261109\sandbox\check_d2x_BASE.py` 系。
- **3 个抽样（各读 docstring 首 20 行）**：
  1. `lead\b2b_candidate_20261106\check_candidate.py`（280 行）——「B2b 候选交付件**机械门禁**（只读）」：文件存在性/字节数/ast.parse/母本 SHA-256 实算/PASS=FAIL=0 统计/禁词正则。→ **文档/交付件机械门禁**，非函数级对拍、非场景级对拍。
  2. `lead\d27_ruling_20261106\check_d27.py`（107 行）——「Read-only D-27 gate」：判定书必需标题、`*.md:NN` 引用格式校验。→ **文档结构门禁**，非对拍。
  3. `lead\b2_preaudit_20261106\check_b2_preaudit.py`（253 行）——「B2 设计预审判定书的确定性门禁（只读）」，退出码 0/1/2。→ **文档内容门禁**，非对拍。
- **定性一句话：抽样 3 个全是「文档/交付件机械门禁」，仓库 `check_*.py`/`_verify*.py` 抽样范围内没有「函数级对拍」或「场景级对拍」的确定性对拍样例。** 函数级验证存在于：`ra2opt/tests.py`（离线自检：apply 幂等/restore 往返/版本比较，`tests.py:341-422,503-609`）与 R3 判定书的 14/14 状态矩阵 exec + 36 组穷举（`CANDIDATE_SEMANTIC_REVIEW_R3.md:42-45`，隔离加载真实函数跑 fixture）。场景级最接近物是 `qc151_trip.py` 真机行程观测（`B2B_DESIGN.md:62` 「载体备份完成后、launch 前」，399,508 B 未读未跑）。

## 指纹复核（收尾）

- 前任已落盘 `fingerprints_pre.txt` / `fingerprints_post.txt`：36/36 全 OK（pre==post，含 ra2youli 游戏目录 12 件、ra2opt 12 个模块、ra2render、tools、docs 代表件）。
- 本会话独立复算（Get-FileHash）：`ra2youli\gamemd.exe` 与 `ra2bench\gamemd.exe` 均 = `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476` ✓ 与验收判据一致。
- 顺带实证：`D:\Red2\ra2youli\gamemd.exe` = `db264305c8a6963d17f5d189a5a9720d9c95f7757cc19c534c2fbe4e015255aa`，恰好等于 `KNOWN_GAMEMD` 记录的官方 1.001 `full_sha256`（`ra2opt/__init__.py:23`）——seed 来源前提成立。

## 前任交接说明（重要更正）

前任并非「零文件落盘」：写域内已有其 6 件产物——`PATCH_CAPABILITY_AUDIT.md`（192 行，§1/§2/§2.1/§2.2 已成，留 `<!-- APPEND-MARKER -->`）、`fingerprints.py`、`fingerprints_pre.txt`、`fingerprints_post.txt`、`ra2opt_status_stdout.txt`（`ra2opt status` 实跑输出）。**本会话全部保留、在 APPEND-MARKER 处续写，未覆盖任何一件。**

## 状态

全部三步完成，主报告已续写至 §7 收尾回执。
