# PATCH_CAPABILITY_AUDIT — 补丁/修改能力对 §2.B 七条硬要求盘点

- 日期：2026-11-12（北京时间）
- 仓库：`D:\Project\ra2-campaign-forge`
- 性质：受限执行方·纯只读审计。除本写域 `lead\patch_capability_audit_20261112\` 外零写入。
- 对照规范：`docs/PROJECT_DIRECTION.md:34-44`（§2.B 关键系统安全修改，7 条硬要求）
- 铁律遵守：未启动 gamemd.exe / ra2loader / YURI.exe，未 attach / 读活进程内存；未跑 `ra2opt apply / restore / seed / clean / laa / play / verify / selftest`（凡会写游戏目录或 `%TEMP%` 的一律未跑）；未改任何既有件；未跑 `ra2opt apply`（含游戏目录写）。实跑仅 4 条只读命令（见 §5）。

---

## STEP 1 · 实现清单：仓库里实际存在的「对引擎做修改」能力

四条修改线 + 一个验证工具族 + lead/ 对拍与门禁件。行数为 2026-11-12 实测。

### A 线 · ra2opt（外围修改：PE 头 / wrapper / 配置 / 注册表 / 启动器）

| 文件:行 | 作用（一句话） |
|---|---|
| `ra2opt/__init__.py:19-27` | 已知引擎版本指纹表 `KNOWN_GAMEMD`：以 `.text` 段 SHA-256 为键（LAA/栈/堆只改 PE 头，代码段不变），仅登记 1 个构建「Yuri's Revenge 1.001 (2001-10-31)」（text `c0368a17…`，full `db264305…`，4,825,360 B） |
| `ra2opt/cli.py:62-132` | 命令面：`audit / apply / verify / status / laa / restore / clean / seed / play / budget / selftest` |
| `ra2opt/optimize.py:42-55` | 双配置档 `safe`（不动 exe 二进制）/`perf`（另置 COFF LAA 位 + DetailLevel=1） |
| `ra2opt/optimize.py:112-325` | `apply` 主流程：cnc-ddraw 升级 → ra2md/ra2.ini `[Video]` 修正 → PE 头（栈 4MB + LAA）→ AppCompatFlags 清理 → 启动器生成；每步 try/except 记 warnings（`optimize.py:175-176,218-219,275-281,297-298,316-317`） |
| `ra2opt/pe.py:282-352` | `set_laa` / `set_stack_reserve` / `set_heap_reserve`：只改 COFF/OptionalHeader 固定字段；`_atomic_write`（`pe.py:265-279`）暂存文件+replace 原子替换；`pe.py:20-25` 记录历史教训（旧版曾把 LAA 误写进 DllCharacteristics，已正名解耦） |
| `ra2opt/backup.py:41-255` | `BackupSet`：改动前快照到 `<游戏目录>/.ra2opt/orig/`（只写一次，`backup.py:63-79`）；`manifest.json` 记录每次 run（run_id/profile/files/registry，`backup.py:107-125`）；`restore`（有快照还原字节、无快照=新建件删除，`backup.py:158-229`）；`clean`（放弃回滚，`backup.py:232-255`） |
| `ra2opt/backup.py:307-367` | `seed`：从另一份安装补回原始快照，`expected={文件名:sha256}` 哈希不符即拒绝（`backup.py:354-356`） |
| `ra2opt/safewrite.py:29-68` | 全项目唯一落盘出口：realpath + commonpath 沙箱（直属层级、拒 `..`、拒软链外逃），先写临时再原子替换 |
| `ra2opt/game.py:104-124` | `GameDir.identity()`：整文件 sha256 + `.text` sha256，查 `KNOWN_GAMEMD` 得 `known_as`；`patched` = text 匹配已知而 full 不匹配 |
| `ra2opt/appcompat.py:140-166` | HKCU `AppCompatFlags\Layers` 读写（64/32 双视图），`merge_flags` 增删标记 |
| `ra2opt/cddraw.py:89-295` | cnc-ddraw：GitHub API 查最新版、下载（仅验 zip 前 4 字节 magic，`cddraw.py:121-122`）、`tune_ini` 以官方新 ini 为基线校验键存在、`install` 覆盖前快照 |
| `ra2opt/launcher.py:20-108` | 生成 `ra2opt_play.bat`（start /high）；`play`（CreateProcessW 白名单）；`smoke_test`（启动游戏观察 N 秒后终止——**真机执行入口，本审计未跑**） |
| `ra2opt/audit.py:98-195, 562-597` | 只读体检：collect（identity/组件/INI/注册表/回滚态/崩溃转储）→ analyze → report.json/md |
| `ra2opt/tests.py:1-14` | `selftest` 覆盖声明：safewrite 沙箱、PE 读写往返（代码段字节不变）、INI 行级保留、备份→回滚字节级往返、临时假游戏目录端到端 apply(perf)→restore（**本审计未实跑**） |

### B 线 · ra2render（引擎内修改：运行时 Hook DLL + 注入器）

| 文件:行 | 作用（一句话） |
|---|---|
| `ra2render/blitter_hooks.cpp`（3,886 行） | 全部引擎内补丁的实现：L1 SSE2 Blitter / L2 寻敌节流 / L3 三态迷雾 / L4 视口刷新 / L5 雷达小地图 + 裂缝保护三点 NOP + VXL 缓存 + SW 充能；遥测与门控 |
| `blitter_hooks.cpp:3507-3600` | **表驱动补丁安装器** `PatchSpec`：每点带目标 VA、原字节、新字节（必须等长）、至多三面守卫窗；「安装前置全查 MATCH 才写（任一不符 ⇒ 拒装，一字节不动）」（:3508）；拒绝路径三分：context-mismatch（:3535）、守卫窗不可读（:3558）、byte-mismatch「既非原字节也非补丁态」（:3574）；幂等（已是补丁态不重复写）与 external-installer 停手（:3594 前后逻辑） |
| `blitter_hooks.cpp:3438-3467` | `RemoveGapProtectionPatch`：硬回滚强制逆序 P-2.3→P-2.2→P-2.1（:3439），只还原我方写过、有回滚资格位的字节（`s_gapProtectWritten`，:3312），回滚未完成打 PARTIAL 告警（:3469） |
| `blitter_hooks.cpp:3641 / :3666 / :3805-3809` | `RemoveVxlCachePrewarmPatch` / `RemoveSwChargeOptPatch`；跨子系统卸载=安装序严格逆序（装序 gap→vxl→sw ⇒ 卸序 sw→vxl→gap） |
| `blitter_hooks.cpp:216` | `MpActive()` 联机状态判定；联机门控落点：GapProtection 联机强制不装（:3342-3343）、TargetScanKey=pointer 联机强制重定向 position 并告警（:339-350, :829）、`s_minimapFogGate=0`（:251） |
| `blitter_hooks.cpp:3476-3500` | `[GAP-MP-EDGE]` 单机↔联机迁移边沿：mp-edge-rollback（进联机逆序硬回滚，:3492-3493）与 mp-edge-reinstall（回单机按完整门禁重装，:3500） |
| `blitter_hooks.cpp:882-1012` | 遥测：`[ra2render-telemetry]` / `-l4dirty` / `-fogswitch` / `-fogsplit` / `-visibility` / `-radar` / `-fogcal` / `-gapprot` / `-vxlpre` / `-swo` / `-fogprobe` 等命名空间，每行附「判据」文本 |
| `ra2render/ra2render.h`（492 行） | 全部补丁点常量：虚表槽/函数入口/字节窗（每点带原字节注释，如 :113-121 三点 `89 99 34 01 00 00` 等）+ 守卫窗 PREV/NEXT；`GAPFIX_HOSTTEST`（:123-161）用 0x3000xxxx 模拟映像把安装/回滚代码搬进宿主单元测试；:111 红线注释「只改已加载映像内存字节：磁盘 gamemd.exe 只读不改」 |
| `ra2render/ra2render.ini`（261 行） | 每补丁独立开关 + 默认值注释：`EnableVxlCachePrewarm=0`（默认关，:19）、`EnableSWChargeOpt=0`（默认关，:46）、`TargetScanInterval/TargetScanKey`（联机门控说明 :24-31）、`EnableStarCraftFog` 总闸三态表（:60-80）等 |
| `ra2render/ra2loader.cpp:36-68` | **注入器**：CREATE_SUSPENDED 启动 gamemd.exe → SetPriorityClass(high) → VirtualAllocEx + WriteProcessMemory + CreateRemoteThread(LoadLibraryA) 注入 ra2render.dll → ResumeThread |
| `ra2render/ra2render.dll`（163,328 B）与 `ra2loader.exe`（106,496 B） | 已构建产物（构建新鲜度未验，见 §6） |

### C 线 · ra2forge（内容安装：战役包进游戏目录）

| 文件:行 | 作用（一句话） |
|---|---|
| `ra2forge/install.py`（1,574 行） | 内容包安装/卸载：`preinstall_plan`（:601-760）逐文件 sha256 预检计划；备份槽 `<name>.ra2forge.bak` 同身份校验（:366-412，防符号链接/硬链接/越界别名）且「最老原版永不覆盖」（:741-743）；TOCTOU 复检（:1031-1053）；暂存写+落盘 sha 复核（:845-916）；`uninstall`（:1120-1287）逐字节还原、安装后被人改过的文件拒绝删除（:1230-1235）；`ra2forge_install.json` 记录 |

### D 族 · 验证/审计工具（只读）

| 文件 | 作用（一句话） |
|---|---|
| `tools/verify_anchors.py`（1,091 行） | 323 条锚点字节断言回归 + 基线完整性审计：固定基线 `ra2youli/gamemd.exe`（:59）与 `.text` raw sha256 常量（:64，与 KNOWN_GAMEMD 同值）；`--segments` 可扩到文件 100% 字节 SHA-256 强校验（:11-12）；退出码契约与 [100% ALL PASS]/[REDUCED-COVERAGE PASS] 等单调措辞阶梯（:19-31） |
| `tools/audit_bytes.py`（32 KB） | 逐批字节断言对拍（S23 31 条，`docs/re/execution_runbook.md:643` 记 100% PASS） |
| `tools/verify_hooks.py`（380 行） | Hook 静态自证（只读）：Install/Remove 配对、`s_orig*Bytes` 备份/还原对称、ini 开关键 vs LoadConfig 读取键、「定义但未安装」/「装了但 Remove 未还原」候选清单（:3-13） |
| `tools/extract_hook_tables.py`、`tools/verify_evidence.py`、`tools/check_except_gate.py` | Hook 表提取 / 证据机械筛 / except 闸门检查（存在性盘点，未逐一实跑） |

### E 组 · lead/ 对拍 harness 与门禁交付件（定向查找，未全量遍历）

| 路径 | 内容 |
|---|---|
| `out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py` | trip harness 母本（B2B 设计稿指纹锚定：sha256 `517889c6…` / 399,508 B / 7,291 行，见 `lead/b2b_design_20261106/B2B_DESIGN.md:24-31`）；同目录另有 16 个 `qc151_trip.py.unapproved_*` 变体 |
| `lead/goal1_harness8_20261031/qc151_trip.harness8_v4.py`（8,856 行） | 载体趟脚本谱系现役版（harness4→7→8_v3→v4→ext）：QC141 授权边界、两控 sha256+VA 字节、AST 禁令自检（零 ReadProcessMemory/WriteProcessMemory/断点/注入）、跑前跑后 FRESHNESS 对拍 |
| `lead/b2b_design_20261106/` | `B2B_DESIGN.md`（唯一合并稿设计：9 个 hunk + freshness 四态/9 verdict/14 行状态矩阵）+ `STATE_MATRIX.json`（机读版）+ `review/B2B_DESIGN_REVIEW.md` |
| `lead/b2b_preaudit_20261106/`、`b2b_candidate_20261106/`、`b2b_candidate_lf_20261107/`、`b2b_isolated_20261107/` | B2 预审 → 候选实现（`qc151_trip.candidate*.py`）→ 隔离副本集成 |
| `lead/gate_validate_20261108/` | 门禁模板实战回归：`GATE_TEMPLATE_REGRESSION.md`（r2）+ 三方独立提取 25 门禁 + 6 组负控 fixtures（evil_launcher / forged_binding / silent_mismatch / getattr 绕过等）+ 12 个绕过向量；独立复核结论 **partial**（r1 强结论全部降级 unconfirmed） |
| `lead/re_line_20261105/W5_HARNESS_EXT/`、`lead/gate_template_20261108/`（被引用） | harness 扩展与门禁模板本体（`GATE_TEMPLATE_FIXED.py.txt`，本审计未直接展开） |

---

## STEP 2 · 七条硬要求逐条实测

判定口径：**有** = 有实现且有证据；**部分有** = 有实现但覆盖不全或关键环节缺失；**没有** = 规范要求但仓库无实现。每条附「实现 vs 验证」的区分。

### 第 1 条（按镜像独立记录 ABI/结构/虚表槽/函数入口/字节窗口/调用契约；原版 game.exe 与 gamemd.exe 地址不得互用）—— **部分有**

| 证据 | 内容 |
|---|---|
| `docs/re/anchor_claims.txt:5-6` | 唯一事实源声明：「基线目标：ra2youli/gamemd.exe (ImageBase 0x00400000, .text VA 0x00401000)；校验口径：raw(SizeOfRawData=0x3E0000)」 |
| `tools/verify_anchors.py:59-66` | 断言脚本把基线镜像与 `.text` raw sha256 写成常量，先验段哈希再跑断言 → **地址账本与镜像的绑定机制存在（verify_anchors 内）** |
| `REVERSE_ENGINEERING_AND_PATCHES.md:207-255`（§七） | 地址速查表逐行带「目标地址 / 原始字节 / 补丁字节」，全部为 gamemd 1.001 地址；勘误直接锚 `ra2youli/gamemd.exe:0x177EC5` 等文件偏移（:246） |
| `ra2render/ra2render.h:12-249` | 虚表槽（TechnoClass 0x007F4960 + 槽号算式注释）、函数入口、调用契约（fastcall/栈参，:76-77）、结构偏移（YRpp+反汇编双向实证注释 :258-270）全部按 gamemd 记录 |
| 实跑（audit report.json:20-23） | `ra2youli\gamemd.exe` → text_sha `c0368a17…`、known_as「Yuri's Revenge 1.001」、patched_by_ra2opt=true |

缺口定性：
- **原版 game.exe 的镜像账本：没有**。全库只有 gamemd 一张地址账；「不得互用」目前是靠「只做了一张账」成立的，不是靠机制阻止混用（未来若开原版线，无防混机制）——**规范要求、仓库无实现（原版账本未开始建）**。
- 【未证】`ra2render.h` 是编译期常量，无「加载前按镜像 sha 选表」的运行时机制；装错镜像只能靠守卫窗字节不符拒装兜底（该兜底为强证据，但「对所有补丁点守卫窗必然拦住异镜像」未证）。

### 第 2 条（补丁安装先验证构建身份与原始字节；未知构建拒绝安装并输出原因）—— **部分有：原始字节校验「有」，构建身份门「没有」**

| 证据 | 内容 |
|---|---|
| 原始字节校验（Hook 线）：`blitter_hooks.cpp:3507-3600` | 表驱动安装器：目标字节「既非原字节也非补丁态」⇒ byte-mismatch 拒装（:3574）；守卫窗不符 ⇒ context-mismatch 拒装「一字节不写」（:3535） |
| 版本识别：`ra2opt/__init__.py:19-27` + `game.py:104-124` | `.text` sha256 指纹识别（设计动机 `__init__.py:16-18`：头字段补丁不改代码段，故用 .text 而非整文件哈希做键） |
| 实跑 1：`ra2opt audit`（本写域 stdout） | 「[+] 已识别引擎版本」；report.json `patched_by_ra2opt=true`（整文件 sha `73201cc0…` ≠ 登记原始 `db264305…`，与 `.ra2opt\manifest.json` 的 apply perf 留痕互证） |
| 实跑 2：`tools/verify_anchors.py`（本写域 stdout） | 323/323 PASS；基线完整性审计输出「RA2OPT_PERF_APPLIED (0xAE=0x20, Stack=4MB, .text未变)」——工具链能把「已被 ra2opt 改过头部的镜像」如实识别并确认代码段零污染 |

**关键缺口（本条最重）：`ra2opt apply` 安装路径无构建身份门**。grep 全包证实 `KNOWN_GAMEMD/identity` 的引用点只有 `audit.py:109`（体检）、`cli.py:308`（seed --verify）、`game.py:117`（识别）、`optimize.py:344`（status）；`optimize.apply`（:112-325）对任意含 gamemd.exe 的目录照改不误——**「未知构建拒绝安装并输出原因」是规范要求、仓库无实现**。
配套缺口：
- `ra2md.exe` / `ra2.exe` 无登记指纹（实跑 report.json:40,58 known_as=null），apply 仍会改其 PE 头（实跑 status：三 exe 栈均 4MB）。
- cnc-ddraw 下载物只验 zip magic，无发布物 sha256 钉扎（`cddraw.py:121-122`）。
- Hook 线安装同样无「构建身份」前置（grep blitter_hooks.cpp 无 checksum/版本校验实现；仅字节窗守卫）。字节窗校验与身份校验是两件事：对 `.text` 相同而头部不同的构建，守卫窗会放行——此推论为机制分析，【未证】。

### 第 3 条（独立开关、安装/卸载日志、必要遥测、失败处理、可实测完整回滚；新实验开关默认关闭）—— **有（四线中能力最全），带两处实现缺口与一处未验**

| 要求面 | 证据 |
|---|---|
| 独立开关 | `ra2render.ini` 每补丁一键且实验键默认 0（`EnableVxlCachePrewarm=0` :19、`EnableSWChargeOpt=0` :46，注释写明「默认 0 = 零行为变化」）；`ra2opt apply` 有 `--no-cddraw/--no-registry/--laa/--no-laa/--detail/--exe/--keep-display/--multi-cpu` 分项（`cli.py:70-89`）；`EnableGapProtection` 门控默认不装（`blitter_hooks.cpp:3262`） |
| 安装日志 | ra2opt：`.ra2opt/manifest.json`（实读 ra2youli 现存 3 条 run：2026-09-25 两次 apply perf + 一次 ddraw.ini 临时改动）；ra2render：LogMessage 落日志（台账 `[v1.6.8]` 引 ra2render.log 真机安装日志 15 处，`REVERSE_ENGINEERING_AND_PATCHES.md:1961-1981` 所在批次）；ra2forge：`ra2forge_install.json` |
| 遥测 | `blitter_hooks.cpp:882-1012` 十余个 `[ra2render-telemetry-*]` 命名空间，每行自带「判据」可机读比对；ra2opt audit 报告落 report.json/md |
| 失败处理 | apply 分步 try/except 收集 warnings 不中断（`optimize.py`）；Hook 安装拒绝三分路径 + PARTIAL 回滚告警（:3469）；ra2forge 备份槽永不覆盖 + TOCTOU 复检 + 暂存写失败不落盘（`install.py`） |
| 完整回滚 | ra2opt `restore`（有快照还字节 / 无快照删新建件，含 AppCompatFlags 还原 `backup.py:205-211`）+ `seed` 哈希校验补快照；Hook 线逆序硬回滚+回滚资格位+PARTIAL 检测；ra2forge `uninstall` 逐字节还原 |
| 新实验默认关 | ini 两键 `=0` 默认 + 注释「0 = 不碰 .text（默认，零行为变化）」；`PROFILES["safe"]` 为 apply 默认档（`cli.py:70` default="safe"） |

缺口定性：
- **实现缺口 1（崩溃窗口）**：快照先于写盘（`backup.py:63-79`），但 run 记录在收尾才 commit（`optimize.py:320-323`）；apply 中途崩溃 ⇒ `orig/` 有孤儿快照、manifest 无记录，而 `restore` 的文件名单取自 manifest（`backup.py:178-180`）⇒ 孤儿快照不被还原也不能被 restore 清理，只能 `clean` 全弃。属「失败处理」未闭合。
- **实现缺口 2（卸载日志）**：restore 把已还原 run 从 manifest 删除（`backup.py:213-228`），卸载动作本身无持久留痕。
- **未验**：`tests.py` 声称的「备份→回滚字节级往返」端到端自检本次未实跑（其临时目录写会越出本审计写域）；对真实游戏目录的 restore「完整回滚」未实测（会写游戏目录，禁止）。故第 3 条判定为「有实现，回滚的正确性在本仓有 selftest 代码承载、本次未复验」。

### 第 4 条（寄存器、栈、线程、对象生命周期、卸载顺序；安装态/执行态/行为态）—— **部分有**

| 证据 | 内容 |
|---|---|
| 卸载顺序 | 安装序/回滚逆序是硬规约且落进代码与注释（`blitter_hooks.cpp:3257,3439,3805-3809`：gap 内部 P-2.3→P-2.2→P-2.1，跨子系统 sw→vxl→gap） |
| 线程/进程生命周期 | `qc151_trip` harness 的进程所有权跟踪与 `terminate_owned_process`（B2B 设计 §3 P7a/P7b 覆盖 finally 各失败区间）；`winproc.spawn` 白名单 CreateProcessW（`launcher.py:7-8` 注释） |
| 安装态 | 遥测 installed 计数：`g_gapProtectionPatchesInstalled`（:963「on 且非联机 应为 3」）、`vxlCacheInstalled`（:968）、`swChargeOptInstalled`（:970） |
| 执行态 | 同遥测行的行为计数（节流率、剔除次数、桩介入次数等 :882-1012） |
| 行为态 | 像素等价（D≡0）与逐帧 CRC 判据已成文（`docs/re/l4_dirty_safety.md`、`b5_mp_card_details.md:103-122`），但**全部 [待实测]**（`docs/re/ARCHITECTURE_ATLAS.md:2720,2733`：「真机联机对拍 [待实测] 未执行」） |

缺口定性：寄存器级运行期校验**没有**（无运行时断言工具；台账的「机器码级定谳」均为静态复算口径，`docs/re/ARCHITECTURE_ATLAS.md:239` 明文「实测一律指静态字节复算」）。行为态三态概念已在遥测/判据文本中承载，但行为态实测=有判据无执行。

### 第 5 条（确定性对拍；存读档跨会话；联机一致/协议/同步）—— **部分有：判据与部分工具齐，行为对拍未执行**

| 证据 | 内容 |
|---|---|
| 确定性对拍（静态层，可跑） | `tools/verify_anchors.py` 323 条锚点断言（本次实跑 323/323 PASS）；`tools/audit_bytes.py` S23 31 条（历史记录 100% PASS，`docs/re/execution_runbook.md:643`） |
| 确定性对拍（行为层，成文未跑） | 联机逐帧 CRC：U-5「≥5000 帧双端 CRC 对拍 [待实测] 未执行」（`docs/re/ARCHITECTURE_ATLAS.md:2733`）；像素等价 D≡0（`docs/re/atlas_rev/R2_fog_l4.md:588`）；B5 判据卡完整（`docs/re/b5_mp_card_details.md:103-158`：N03 双端同镜像对拍场、N10 双端镜像 sha 一致、N11 混联 ≥300 帧零 SYNC、判据原样锚定） |
| 存读档 | 存档块清单/断言在 anchor_claims 来源②（79 条存档块锚点，`anchor_claims.txt:15`）；「打/不打补丁 SAV 核心块哈希一致且原版可读」= B-N17 判据（`docs/re/b_regression_required.md:33`）——**判据成文，跨会话实测未执行** |
| qc151/STATE_MATRIX 是什么 | B2b 设计链 = 对 qc151_trip 载体 harness 的 **except.txt 新鲜度判据重构设计**：`state` 四态（unknown/absent_confirmed/present/error）作唯一判别口、9 值 verdict、14 行状态矩阵（`lead/b2b_design_20261106/B2B_DESIGN.md:146-161` + `STATE_MATRIX.json` 机读版）；含 hunk 级 diff 与 P1-P10 早退覆盖表；**设计稿未应用到母本**（`B2B_DESIGN.md:41-43` 自述「终点是候选实现者可照抄，不等于已获准应用」），独立复核存在（`review/B2B_DESIGN_REVIEW.md`，内容未逐条核，见 §6） |
| 联机配置一致 | Hook 线联机门控（第 3/6 条证据）；R-1「各端必须同构建同开关」红线（`blitter_hooks.cpp:3343,3477`） |

缺口定性：**行为层对拍的可执行 harness（判据执行器）没有成品**——bench_replay.py 为帧数据采集 harness（Q1H 基准线），像素 diff 与双端 CRC 比对器未见成品脚本；oracle 所需「干净零售 1.001」不存在（`docs/re/REWRITE_ROADMAP.md:163`：现镜含 `.detour`+`xyr.dll`，需另备干净件）。存档跨会话与联机对拍=「有判据卡、无执行记录」。

### 第 6 条（未过联机验证的实验功能限定为明确标注的单机范围；客户端 UI 改动说明公平性影响）—— **部分有：门控机制有，标注机制不成体系**

| 证据 | 内容 |
|---|---|
| 联机强制门控（机制） | `MpActive()`（`blitter_hooks.cpp:216`）；GapProtection 联机强制不装并注明混端 DESYNC 风险（:3342-3343）；TargetScanKey=pointer 联机强制重定向 position + 红字告警（:339-350）；EnableMinimapFog 联机整体关闭（:251）；mp-edge 边沿迁移自动回滚/重装（:3476-3500） |
| ini 内标注 | `ra2render.ini` 每键注释写明联机姿态：「联机可装（D-VXL13 SAFE…全端同键同档，禁一端 1 一端 0）」（:15-16）、「MP 可装可保留（不强制关）」（:45）、G-02/G-08 门控说明（:24-31） |
| UI 公平性 | 雷达小地图 UI 改动在联机侧整体关闭（`s_minimapFogGate=0`，:251）；「联机侧已由 … 整体关闭」为代码注释级说明 |

缺口定性：**「单机范围标注」无统一机制**——标注散落在 ini 注释/代码注释/判据文档，无机读字段或集中清单；「公平性影响说明」同样未字段化（有实例、无制度）。属「有零散实现、缺成文机制」。

### 第 7 条（原 exe 只读基线；部署与真机遵守写域/单写者/游戏实例独占）—— **部分有：机械看守有，流程约束靠纪律**

| 证据 | 内容 |
|---|---|
| 只读基线机械看守 | `verify_anchors.py`：`.text` raw 哈希 + 323 条字节断言 + 可选 `--segments` 文件 100% SHA-256 强校验；本次实跑 PASS 且能识别「RA2OPT_PERF_APPLIED 但 .text 未变」的合法留痕态 |
| Hook 线磁盘红线 | `ra2render.h:111`「只改**已加载映像内存字节**：磁盘 gamemd.exe 只读不改（RE_COORDINATION 红线 §3-1）」 |
| 写域单写者（工具层） | `safewrite.py` 唯一落盘出口（realpath+直属层级沙箱）；`ra2forge` 备份槽防别名/防硬链（`install.py:366-412`）；`game.py:14-16` 防绝对路径替换逃逸 |
| 流程层 | `docs/PROJECT_DIRECTION.md:81`「真机测试串行，运行时代码和安装目录维持单写者」；§2.B 最后一条即本要求原文 |

缺口定性：单写者/游戏实例独占在**工具层**有落点（safewrite、qc151 trip 的单进程所有权），但「部署与真机执行遵守任务卡写域」本质靠派工纪律，无跨会话机械互斥（无锁文件/单写者守护进程一类机制）——规范有、机制不完整，此定性按仓库可见材料，【未证】其是否存在仓库外实现。

---

## STEP 3 · 兼容缺口清单：要达到 §2.B 七条还缺什么

### 缺实现（规范要求、仓库无对应代码）

| # | 缺什么 | 为什么现在做不到 | 需要的前置 |
|---|---|---|---|
| G1 | `ra2opt apply` 的构建身份门：未知构建拒绝安装并输出原因 | apply 直接读 PE 头就动手，不查 `KNOWN_GAMEMD`；识别能力已有（identity/KNOWN_GAMEMD），只是没接到安装路径 | 把 `game.identity()` 接进 `optimize.apply` 前置，指纹表扩 ra2md.exe/ra2.exe（需各取一份可信原始字节算 `.text` 指纹入库） |
| G2 | 原版 game.exe 镜像账本（ABI/虚表/字节窗/调用契约） | 项目自 2026-09 起全部锚定 gamemd 一张账；原版线零记录 | 决策是否开原版线；若开，按 anchor_claims+verify_anchors 模板为原版镜像另立事实源与段级基线 |
| G3 | 行为层对拍执行器：像素 diff（D≡0）与双端逐帧 CRC 比对的成品脚本 | 判据卡与「机器判据」文本齐备，但比对器未见实现；oracle 干净零售 1.001 也未备 | 先落地 oracle 镜像与采集格式（bench_replay 已产帧数据），再实现比对器；真机窗口按任务卡另批 |
| G4 | apply 崩溃窗口的孤儿快照处置 | 快照先写、run 后 commit，中途崩溃产生 orig/ 孤儿且 restore 不覆盖 | commit 前置（先记 run 再写盘）或 restore/clean 增加对 orig/ 与 manifest 的对账扫描 |
| G5 | 卸载动作持久留痕 | restore 即删 manifest 记录，卸载历史不落任何文件 | restore 时追加 restore-log（或把已还原 run 移入 history 节） |
| G6 | cnc-ddraw 下载物 sha256 钉扎 | 只验 zip magic，release 物无哈希白名单 | 在 release 元数据中登记官方 sha256（需可信来源），download/install 前置校验 |
| G7 | 实验功能「单机范围/公平性」机读标注 | 标注散在 ini 注释与代码注释，无统一字段 | 定义 manifest/ini 注释规范（如 `MP=off|safe|required-same-build`），verify_hooks 增加「开关⇔标注⇔门控」一致性检查 |

### 缺验证（有实现，仓库内无执行记录/本审计未验）

| # | 什么未验 | 现状 |
|---|---|---|
| V1 | ra2opt restore 对真实游戏目录的端到端回滚 | selftest 代码承载（`tests.py`），本审计未跑（写域限制）；最近真机回滚记录未在本次盘点范围内逐条核对 |
| V2 | Hook Remove* 真机卸载回归（最新构建） | 台账有历史真机验收（v1.6.8 批次等），本审计未重验；静态对称自证工具在（verify_hooks.py） |
| V3 | 联机双端逐帧 CRC 对拍（U-3/U-5） | 文档明标 [待实测] 未执行（`ARCHITECTURE_ATLAS.md:2720,2733`） |
| V4 | 像素等价对拍（L4DirtyMode/auto 档等） | 判据成文（D≡0），执行记录缺 |
| V5 | 存档跨会话保存/加载（B-N17 判据） | 判据成文，无执行记录 |
| V6 | KNOWN_GAMEMD 登记原始 full_sha256 `db264305…` 的出处 | 现盘 gamemd.exe 为 `73201cc0…`（=ra2opt 留痕态，.ra2opt manifest 与 harness 控一互证）；「db264305 是否等于未改原始值」仓库内无可对副本，**未验** |

### 缺文档/缺机制

| # | 什么 | 说明 |
|---|---|---|
| D1 | 镜像绑定的机制化推广 | 「地址账本先验镜像」目前只在 verify_anchors.py 内实现；Hook 表/Ini 注释/其他断言表无统一「本表绑定镜像 sha256」头部约定 |
| D2 | B 链状态与验收状态一页汇总 | B2 否决→B2b 设计→候选→隔离副本→门禁 partial 的链路状态分散在多目录（本审计只能定向抽样） |
| D3 | 对拍样例登记册 | 对拍散布于 anchor_claims / 判据卡 / fixtures / trip harness，无统一清单标注「函数级/场景级 + 判据 + 执行状态」（本报告 §4 即其雏形） |

---

## STEP 4 · 固定场景对拍样例盘点

「对拍从少量可控函数和固定场景开始扩展」——现有对拍分两层。**函数级** = 针对单函数/字节窗/静态结构的可重复断言；**场景级** = 固定场景/固定种子下的整局或多帧行为比对。

### 函数级（可跑/已跑）

| 样例 | 载体 | 判据 | 执行状态 |
|---|---|---|---|
| 323 条决定性锚点断言（S1–S20 全局 43 + 存档块 79 + 触发器 77 + MIX 124） | `docs/re/anchor_claims.txt` → `tools/verify_anchors.py` | 逐 VA 字节串一致 + `.text` raw sha256 | **本次实跑 323/323 PASS**（[REDUCED-COVERAGE PASS]，未启用段级） |
| S23 批次 31 条断言 | `tools/audit_bytes.py`（引 `docs/re/execution_runbook.md:643`） | claims_s23.txt 31/31 OK | 历史记录 PASS；本审计未重跑 |
| Hook 安装/卸载静态对称 | `tools/verify_hooks.py` | Install/Remove 配对、s_orig*Bytes 备份还原对称、ini 键覆盖 | 工具在；本审计未跑（读源码即可跑，属可补跑项） |
| 门禁模板回归（25 门禁 × 12 绕过向量 + 6 负控 fixtures） | `lead/gate_validate_20261108/` | 门禁对伪造/绕过样本必须 FAIL（AST 级） | 已跑且独立复核=partial（r1 强结论降级 unconfirmed） |
| B2b freshness 判据矩阵（离线合成字典单测） | `lead/b2b_design_20261106/`（设计稿内置单测输出 `_draft_semantics_matrix_out.txt`） | unknown 恒 none、absent_confirmed 才可 high 等 14 行 | 设计稿内的离线单测 PASS；**未应用到母本** |

### 场景级（判据成文；除静态金样外均需真机，未执行）

| 样例 | 载体 | 判据 | 执行状态 |
|---|---|---|---|
| qc151 载体趟（启动观测/能否进图 + 两控 + 载体 5 件跑前跑后 FRESHNESS 对拍） | `lead/goal1_harness8_20261031/qc151_trip.harness8_v4.py`（授权制：QC141 §9 用户签署后才可运行） | 两控 sha256/VA 字节一致；FRESHNESS verdict 落盘；直启 exe 零注入零断点（AST 自检） | harness 谱系已交付多版；真机趟按授权制执行（本审计零真机） |
| 联机逐帧 CRC 对拍（B5 ZB5-M01） | `docs/re/b5_mp_card_details.md:107-122` | N03 双端同镜像 MATCH 100%（500/500）、N10 双端镜像 sha 相同、N11 混联 ≥300 帧零 SYNC | **未执行**（[待实测]） |
| 像素等价对拍（L4 E5） | `docs/re/l4_dirty_safety.md`（R2_fog_l4.md:588 转引） | 静态镜头同帧像素差 D≡0 + l4RedrawSkippedStatic>0 | 未执行（[待实测]） |
| 存档往返（B5 ZB5-M02 B-N17） | `docs/re/b_regression_required.md:33` | 打/不打补丁 SAV 核心块哈希一致且原版可读 | 未执行 |
| a3 战役安装金样对拍 | `docs/re/a3_campaign_install_runbook.md:106-194` | gamemd.exe 仅 sha256 对拍不备份；收尾 sha256==基线 + except.txt 无新增；BATTLEMD.INI diff 门禁 | 历史执行过的 runbook（执行记录未逐条核） |
| a3 地图生成器黄金对拍 | `docs/re/a3_map_generator_spec.md:355,396` | `--restore` 后 byte-identical；variant=full 黄金 sha256 `fc49b149…` | 规格成文（执行记录未核） |

层级小结：**函数级对拍已成体系且可机跑**（锚点断言 323 条 + 门禁负控 + Hook 静态对称）；**场景级对拍只有判据卡与 harness 骨架，行为层执行器缺失**（STEP3-G3）。

---

## 5 · 实跑记录（全部落盘于本写域）

| # | 命令 | 结果 | 落盘 |
|---|---|---|---|
| 1 | `python -I -X utf8 lead\patch_capability_audit_20261112\fingerprints.py …fingerprints_pre.txt` | 36 件全部 OK | `fingerprints_pre.txt` |
| 2 | `python -X utf8 -m ra2opt audit --game ra2youli --out lead\patch_capability_audit_20261112\ra2opt_audit_out`（PYTHONPATH=仓库根，PYTHONDONTWRITEBYTECODE=1） | 严重 0 / 警告 0 / 建议 4 / 已达标 4，exit 0；已识别引擎版本 | `ra2opt_audit_stdout.txt` + `ra2opt_audit_out\report.json/.md` |
| 3 | `python -X utf8 -m ra2opt status --game ra2youli` | cnc-ddraw 7.1.0.0；gamemd LAA=开 栈=4MB；3 条 apply 记录；原始快照 7 件 | `ra2opt_status_stdout.txt` |
| 4 | `python -I -X utf8 tools\verify_anchors.py` | 323/323 PASS，exit 0；.text 哈希 PASS；「RA2OPT_PERF_APPLIED (.text未变)」；[REDUCED-COVERAGE PASS]（15.78% 无检测区如实声明） | `verify_anchors_stdout.txt` |
| 5 | `python -I -X utf8 fingerprints.py …fingerprints_post.txt` + 与 pre 比对 | **IDENTICAL：36 个既有件指纹零变化** | `fingerprints_post.txt` |

收尾指纹（关键件摘录，完整 36 件见 `fingerprints_post.txt`）：

```
ra2youli\gamemd.exe   73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476 (4825360 B)
ra2youli\ra2md.exe    9072312a569ec2cb3511f6153be878d60b6821ee19dc6458535d74517786f5a7 (94208 B)
ra2youli\ra2.exe      ab5ef8edc783b19ccf15706de1c81be91f0455731905edcd4310c3f0acb98c1e (129024 B)
ra2youli\ddraw.dll    85e0f7d530dfda134793a57cb3e76b0287dcc96892ee57162dd68f47283b03a9 (411648 B)
ra2youli\.ra2opt\manifest.json  d483297510cfe2c0547bf6181244e11dfd73b499ecea41d190b3ff23fa11ad4c (937 B)
docs\PROJECT_DIRECTION.md       1b1f56ce022694c9aabb2f58e3d3809b689e977720e3176424d82b251763949b (10194 B)
ra2opt\optimize.py              770edca165cf4295015d75cdff369c599c618431cdc430054329d26a9e27f5c8 (15794 B)
ra2render\blitter_hooks.cpp     6504a132af8006ed409db1de4323877c173a2a14c556979e6d1efc4d6a65a4d6 (227989 B)
tools\verify_anchors.py         3fac8a8f2bca7fe5b645f983b419d992264ac155d3be1a45b3be395de3b81acd (53416 B)
```

---

## 6 · 边界与未验

1. **零真机**：全程未启动任何游戏/loader、未注入、未读活进程内存。`smoke_test/play/verify` 代码在（真机入口），仅静态盘点。
2. **只实跑 4 条只读命令**（§5 表 1–4 + 收尾指纹）。`ra2opt apply/restore/seed/clean/laa/play/verify/selftest` 全部未跑——因此第 3 条的「完整回滚可实测」与第 4 条的运行期检验**本会话未验**，只有代码与历史台账证据。
3. **既有件零改动证明**：36 个既有件（ra2youli 全部关键件 + ra2opt/ra2render/tools/docs 代表件）跑前/跑后 SHA-256 逐一对同（§5 第 5 行）。实跑命令均带 `PYTHONDONTWRITEBYTECODE=1` 防止 `__pycache__` 写入。
4. **并发会话痕迹（如实报告）**：`ra2forge\__pycache__\*.cpython-313.pyc`（8 件）的 mtime 为 2026-11-12 0:48:53-54，落在本审计会话窗口内，但**非本审计产生**——本审计在该时刻无任何 python 调用，且本审计全部 python 调用清点为 5 次（fingerprints×2 / audit / status / verify_anchors），解释器均为 3.12（pyc 为 313）。`ra2opt\__pycache__` 与 ra2forge 的 312 批次 mtime 均为 0:23（先于本审计首步 00:42）。归因未验（无法排除父会话或并行会话），列此备查。
5. **KNOWN_GAMEMD 原始 full_sha256（`db264305…`）出处未验**：现盘 gamemd.exe（`73201cc0…`）是 ra2opt 留痕态（manifest 20260925-161048 apply perf 与 verify_anchors「RA2OPT_PERF_APPLIED」互证）；仓库内无未改副本可对 `db264305` 是否真等于未改原始值。
6. **B 链验收状态**：B2b 设计稿与 STATE_MATRIX 未应用到母本（设计稿自述）；`review/B2B_DESIGN_REVIEW.md` 存在但本审计未逐条核其复核内容；gate_validate 复核结论取自其文档自述（partial），未复算。
7. **lead/（253 目录）与 re_atlas/、out/re_work/ 大体量台账未全量遍历**：全部为定向 glob/grep 命中后抽读；可能存在未盘点到的对拍/补丁交付件（尤其 out/re_work 深层）。
8. **ra2render.dll / ra2loader.exe 与当前 .cpp/.h 是否同源构建**未验（无构建时间戳/哈希对照记录被本审计采集）。
9. 本报告的机制推论（如「守卫窗对同 .text 异头部构建会放行」「单写者无跨会话机械互斥」）均已标【未证】，未把静态读数升格为运行时结论。
10. 引用行号以 2026-11-12 本审计读盘时点为准；台账类文件（REVERSE_ENGINEERING_AND_PATCHES.md 等）仍在被其他会话追加，行号可能随其更新漂移。

---

## 附：七条判定速览

| 条 | 要求摘要 | 判定 | 一句话依据 |
|---|---|---|---|
| 1 | 镜像独立记录、地址不互用 | 部分有 | gamemd 一张账且与镜像绑定（verify_anchors/anchor_claims/§七表）；原版 game.exe 账本没有，防混机制没有 |
| 2 | 安装前验构建身份+原始字节 | 部分有 | 字节窗守卫拒装（Hook 线）有；`apply` 无身份门、ra2md/ra2 无指纹、ddraw zip 无钉扎 |
| 3 | 独立开关/日志/遥测/失败处理/回滚 | 有 | 四线齐备且 manifest 实存 3 条 run；缺口=崩溃窗口孤儿快照、卸载不留痕；selftest 未复跑 |
| 4 | 寄存器/栈/线程/生命周期/卸载顺序；三态 | 部分有 | 卸载逆序硬规约+安装态/执行态遥测在；行为态判据成文未执行；寄存器级运行期校验没有 |
| 5 | 确定性对拍/存档/联机 | 部分有 | 函数级对拍可跑（323/323 PASS 实跑）；像素/CRC/存档对拍判据卡齐但全部 [待实测]；STATE_MATRIX/B2B=harness 新鲜度判据设计稿（未应用母本） |
| 6 | 单机限定标注/公平性 | 部分有 | MpActive 联机强制门控+ini 联机姿态注释在；无机读「单机范围/公平性」标注机制 |
| 7 | 只读基线/写域/单写者 | 部分有 | verify_anchors 机械看守基线（实跑 PASS）+safewrite 单出口；单写者/实例独占靠纪律，无跨会话机制 |
