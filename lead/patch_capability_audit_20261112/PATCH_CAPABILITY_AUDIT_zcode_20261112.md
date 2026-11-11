# PATCH_CAPABILITY_AUDIT · ZCode 会话版（2026-11-12）

> **文件身份说明**：本文件是重派 ZCode 会话（GLM-5.3-Flash）的**独立完整交付**，自成一体，不覆盖写域内任何既有件。写域内另有一份并行会话的 `PATCH_CAPABILITY_AUDIT.md`（181 行完整版，最后写入 01:53:04，自称与本版为「两版判定不一致」待仲裁），以及其部分中间态产物。本版与并行版的差异点集中在第 1 条与第 7 条的判定与证据取材；两版对第 2–6 条的核心结论一致（详见 §3）。
> 时段：2026-11-12T01:10–01:55+08:00。铁律遵守：零真机、只读边界、`python -I -X utf8`、hashlib 实算、未跑 `ra2opt apply`。

## §1 七条规范逐字清单

来源：`docs\PROJECT_DIRECTION.md` §2.B「关键系统安全修改」（L34–L42），七条为 **L36–L42 逐字**。基线文件指纹：`fingerprints_pre.txt:13` → sha256 `1b1f56ce022694c9aabb2f58e3d3809b689e977720e3176424d82b251763949b`（10194 B）。

1. **(L36)** 「按目标镜像独立记录 ABI、结构、虚表槽、函数入口、字节窗口和调用契约；原版 game.exe 与尤复 gamemd.exe 的地址不得互用。」
2. **(L37)** 「补丁安装先验证构建身份与原始字节；未知构建或不匹配窗口拒绝安装，并输出原因。」
3. **(L38)** 「每项补丁具备独立开关、安装/卸载日志、必要遥测、失败处理与可实测的完整回滚；新实验开关默认关闭。」
4. **(L39)** 「检验寄存器、栈、线程、对象生命周期和卸载顺序；同时检查安装态、执行态与行为态。」
5. **(L40)** 「涉及模拟结果的修改必须补确定性对拍；涉及存读档的修改必须验证跨会话保存与加载；涉及联机的修改必须验证双方配置一致、协议兼容与同步结果。」
6. **(L41)** 「未通过联机验证的实验功能限定为明确标注的单机范围；客户端 UI 改动也须说明公平性影响。」
7. **(L42)** 「原 exe 保留只读基线；部署和真机执行遵守任务卡的明确写域、单写者和游戏实例独占约束。」

> 以上是规范要求（normative），非实现陈述。`docs\PROJECT_DIRECTION.md:44`（§2.B 末「优先逆向」段）另含「对拍从少量可控函数和固定场景开始扩展」的原文。

## §2 审计对象与方法

- **目标 A**：`ra2opt/` 17 模块（`__init__/__main__/appcompat/audit/backup/budget/cddraw/cli/game/inifile/launcher/net/optimize/pe/safewrite/tests/winproc`）。定向读：`__init__.py`（全 42 行）、`game.py:95-139`、`optimize.py:112-324`、`backup.py:1-70/150-239/300-367`、`safewrite.py`（全 69 行）、`cli.py:288-322`；`audit.py`/`pe.py`/`tests.py` 仅 grep 定行。
- **目标 B**：`lead\b2b_design_20261106\B2B_DESIGN.md`（头 100 行 / 693 行）、`STATE_MATRIX.json`（全 16 行）、`lead\b2b_candidate_review3_20261107\CANDIDATE_SEMANTIC_REVIEW_R3.md`（头 80 行 + grep PASS|FAIL）。
- **目标 C**：glob 文件名普查（非内容遍历）：`lead/` 下 `check_*.py` **192 个**、`*_verify*.py` **186 个**；抽 3 个读 docstring 首 20 行。
- **实跑**：`python -X utf8 -m ra2opt audit`（PYTHONPATH=仓库根，只读）→ `ra2opt_audit_stdout.txt`，退出码 0；`Get-FileHash` 指纹复算。`ra2opt status` 输出沿用并行会话在档件（`ra2opt_status_stdout.txt`）。

## §3 七条逐条判定表

| # | 判定 | 证据（文件:行 或 实跑输出） | 缺口 |
|---|---|---|---|
| 1 | **没有**（ra2opt 范围；未验保留） | ra2opt 全部指纹记录仅 `KNOWN_GAMEMD` 的 `.text` 段 SHA-256 + full_sha256（`__init__.py:19-27`、`game.py:104-124`）；无 ABI/虚表槽/函数入口/字节窗口/调用契约条目 | **缺实现**（ra2opt 内）。未验：`tools/verify_anchors.py`(53,416B)、`tools/audit_bytes.py`(32,175B)、`REVERSE_ENGINEERING_AND_PATCHES.md`(406,585B)、`docs/re/anchor_claims.txt`(35,514B) 可能含 ABI/锚点登记，未读 |
| 2 | **部分有** | 识别有：`game.py:104-124 identity()`（整文件+`.text` 双哈希、`patched` 标志）+ 实跑「已识别引擎版本」（`ra2opt_audit_stdout.txt:14`）；原始字节留存：`backup.py:63-79`；seed 哈希核对：`backup.py:353-356`、`cli.py:304-318`；PE 改前读当前栈值/LAA 位（`optimize.py:221-254`） | **缺实现**：`optimize.apply():112-133` 不调 `identity()`/`KNOWN_GAMEMD`——未知构建不拒绝安装、无原因输出（全模块 grep `identity(` 仅 `game.py:104`/`audit.py:109`/`optimize.py:344`/`cli.py:308`）；无「字节窗口比对→拒绝」路径（对 ra2opt 现有 PE 头/INI 改动面不适用，对代码补丁缺位） |
| 3 | **部分有** | 开关：`--no-cddraw/--no-registry/--dry-run/--exe/multi_cpu`（`optimize.py:112-116`）+ profile safe/perf（:118-126）；日志：manifest run `run_id/label/profile/created/files/registry/notes`（`backup.py:29-56,107-125`）+ report steps（`optimize.py:319-324`）；失败处理：逐步 try/except→warnings（`optimize.py:175-176,218-219,275-277`）；完整回滚实现：`backup.py:158-229`（快照覆盖/新建件删除/注册表还原/run_id/dry_run/清场）；新实验开关默认关：`multi_cpu=False`、`keep_display=False`（:114-115） | **缺实现**：遥测零实现（grep `telemetry|遥测` 零命中）；逐补丁独立开关缺（现为 profile 粗粒度）。**缺验证**：回滚未实测（restore/自检未跑）；盘上有可回滚实物（`ra2opt_status_stdout.txt:10-15` 3 条 run + 7 项快照；`fingerprints_pre.txt:12` manifest.json 937B 在档） |
| 4 | **没有**（运行态检验；安装态有雏形） | 安装态：audit 实跑「严重 0/警告 0/建议 4/已达标 4」（`ra2opt_audit_stdout.txt:17`）；执行态雏形：`optimize.verify()` 启动冒烟（`optimize.py:328`，真机能力，未跑）；行为态无 | **缺实现**：寄存器/栈/线程/生命周期/卸载顺序运行时检验无实现（需真机，另行任务卡）；行为态检查无 |
| 5 | **没有** | B 链定性为「观测新鲜性」非对拍（`STATE_MATRIX.json` 14 行全部判定跑前/跑后文件快照，全行 `usableAsCrashEvidence:false`；`B2B_DESIGN.md:58-83` 全是 FRESHNESS 字段设计；R3 `:78` 确认 F 恒不可作崩溃证据）；门禁抽样 3 个全是文档门禁（§5）；ra2opt grep `对拍|联机|存档|savegame|sync` 仅 `cddraw.py:58,210` vsync 文案 | **缺实现**：确定性对拍、跨会话存读档验证、联机三验全无。未验：`net.py`/`budget.py`/`inifile.py`/`winproc.py`/`launcher.py`/`appcompat.py` 未读全文 |
| 6 | **没有**（低置信，标未验） | ra2opt profiles/开关无单机范围标注字段；抽样材料无公平性说明 | **缺实现**：标注机制缺位；仅基于定向读+关键词 grep，audit.py/cli.py 报告文案未全文读 |
| 7 | **部分有** | 只读基线：`orig/` 只写一次（`backup.py:63-68,75-76`）+ 盘上实物（`ra2youli\.ra2opt\orig\gamemd.exe`=db264305…，并行版 §6.3 实算；本会话另实证 `D:\Red2\ra2youli\gamemd.exe`=同值，恰为 `KNOWN_GAMEMD` 官方 1.001 `full_sha256`，`__init__.py:23`）；写域守卫：`safewrite.py:29-53`（realpath/commonpath/直属层级/拒绝`..`/临时件原子替换） | **缺实现**：单写者约束、游戏实例独占（互斥/mutex/进程检测）无实现线索（`winproc.py`/`launcher.py` 未读→此半句未验） |

## §4 兼容缺口清单

**缺实现**（规范要求但仓库无实现）：G1=ABI/虚表/字节窗口/调用契约登记库（#1，tools/ 四件未验）；G2=apply 安装前版本/构建守卫（#2，`identity()` 已有未接入）；G3=字节窗口比对拒绝（#2，对现改动面不适用）；G4=遥测+逐补丁开关（#3）；G5=运行态检验与行为态（#4）；G6=确定性对拍/存读档跨会话/联机三验（#5）；G7=单机范围标注与公平性说明（#6）；G8=单写者/实例独占（#7，未验半句）。

**缺验证**（有实现未跑）：V1=restore 回滚实测与 `tests.py` 离线自检（restore_roundtrip/apply_is_idempotent，`tests.py:355,540`）；V2=`optimize.verify()` 执行态冒烟（真机）；V3=`seed --verify` 路径（前置实证已成立）；V4=`ra2opt_audit_out\report.{md,json}` 未逐字读。

**缺文档**：D1=ra2opt↔§2.B 七条映射文档（本报告首次盘点）；D2=B 链 PASS≠可应用母本，集成步骤未做（`R3:23,137`）；D3=`B2B_DESIGN.md:48` 自陈复核件缺失与其时点后 `check_b2b.py` 已实见的并置说明。

## §5 对拍样例清单

| 层级 | 样例 | 定性 |
|---|---|---|
| 函数级（离线） | `ra2opt/tests.py:341-422,503-609`（apply 幂等/restore 往返/版本比较/tune 拒未知键/pe 拒`..`） | 函数级自检，非对拍（无双路输出比对） |
| 函数级（离线） | R3 状态矩阵 14/14 exec + 36 组穷举（`CANDIDATE_SEMANTIC_REVIEW_R3.md:42-45`） | 函数级验证（隔离加载真实函数跑 fixture），非模拟结果对拍 |
| 文档门禁 | `check_candidate.py`（交付件机械门禁：存在性/字节数/ast.parse/母本指纹/PASS 统计）、`check_d27.py`（判定书标题+引用格式）、`check_b2_preaudit.py`（判定书内容门禁，退出码 0/1/2） | 文档/交付件机械门禁，非对拍 |
| 场景级（观测） | `qc151_trip.py`（399,508B）真机行程 + B 链 pre/post 新鲜性快照（launch 前采集，`B2B_DESIGN.md:62`） | 场景级观测，非确定性对拍 |
| **场景级（确定性对拍）** | **无** | L40/L44 要求的「少量可控函数+固定场景」对拍样例在已查范围内为零 |

## §6 边界与未验

1. 只跑只读命令：`ra2opt audit`（本会话）+ 在档 `ra2opt status`（并行会话跑）；未跑 apply/restore/clean/seed/verify、未启动任何游戏进程、未 attach、未写 hook/采样/MiniDump 代码、无 git 写操作。
2. `net.py`/`budget.py`/`inifile.py`/`winproc.py`/`launcher.py`/`appcompat.py`/`cddraw.py`/`pe.py`/`audit.py` 未读全文；`REVERSE_ENGINEERING_AND_PATCHES.md`、`tools/verify_anchors.py`、`tools/audit_bytes.py`、`docs/re/anchor_claims.txt` 未读（73MB 级证据文件一律未读，lead/ 238 目录未遍历，仅 glob 文件名）。
3. §3 #6 为低置信判定；§3 #1/#7 的「未验」半句依赖上述未读件。
4. `check_*.py`/`_verify*.py` 仅 3 个抽样读内容，其余 375 个只列文件名，不排除个别为真对拍脚本。
5. `ra2opt_audit_out\report.md`/`report.json`（audit 完整报告，落在写域内）仅读 stdout 摘要。
6. **并发写域警示**：`PATCH_CAPABILITY_AUDIT.md` 在本会话读取（01:31，192 行含 APPEND-MARKER）后被并行会话整体重写（01:53，181 行完整版，自称待仲裁）；写域单写者约束事实破裂，交付仲裁由派发方定。

## §7 收尾回执

- 指纹验收：`ra2youli\gamemd.exe` 与 `ra2bench\gamemd.exe` 本会话 Get-FileHash 独立实算均 = `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476` ✓（与验收期望一致）；并行会话 pre/post 36/36 对账 OK；`D:\Red2\ra2youli\gamemd.exe` = `db264305…` 恰为 `KNOWN_GAMEMD` 官方 1.001 `full_sha256`。
- 既有件与 `ra2youli\` 零改动 ✓（两轮实算指纹一致；本会话无任何写域外写操作）。
- 写域内本会话产物：本文件 + `PROGRESS.md`（增量过程档）；其余为并行会话/audit 产物。
- 一句话总判：**ra2opt 具备「识别 + 快照 + 回滚」骨架，七条中 #2/#3/#7 部分有、#1/#4/#5 没有（#6 低置信没有）；规范要求但无实现的最高价值缺口是 G2（把 `identity()` 接进 `apply`，未知构建拒绝安装）与 G6（函数级确定性对拍起步）——两者均可离线实现+自测，无需真机。**
- （全文完 · 写域 `lead\patch_capability_audit_20261112\` · 零真机 · 未跑 `ra2opt apply`）
