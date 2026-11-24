# W36 · B 线（安全改造能力）起步方案与可行性定谳

> 卡：`W36_b_line_kickoff`｜离线分析卡｜run_id `NEXT_RE_20261112_R02`｜2026-11-13（Asia/Shanghai）
> 工作目录：`D:\Project\ra2-campaign-forge`
> 纪律：**纯离线只读**。本卡未启动游戏、未 attach、未写 `ra2youli`、未改仓库 `ra2forge/`、未动 `W21`–`W35` 任何目录、`git` 只读、不写代码。
> 交付：仅本目录 `B_LINE_PLAN.md` / `DISAGREE.md` / `UNCOVERED.md` 三个 Markdown 文件。

## 0 · 结论分级与红线（本卡口径）

| 标记 | 本卡含义 |
|---|---|
| `[本次实测]` | 本卡用只读命令对**当前盘面**直接取得并核对的事实（目录枚举、文件清单、SUMMARY 数字、`file:line`） |
| `[本次读码]` | 本卡逐行读源码/文档得到的代码事实或原文 |
| `[静态推断]` | 由多项读码/盘面事实组合推出的工程判定（四问可行性、耦合矩阵、失效风险） |
| `[转引]` | 来自既有卡片 / Lead 判定书 / 任务书的结论，本卡未独立复算 |
| `[待运行验证]` | 须运行脚本或真机才能定谳，本卡未做 |

**红线（全卡适用）**：`[转引]` 的「回归全绿」只表示**离线文件层断言通过**，**不得**写成「游戏行为正确」。RE-N09 通过条件原文即「文档门禁 PASS 不代替游戏行为对照」（见 §1）。本卡未运行任何回归/构建/校验脚本。

---

## 1 · RE-N09 原文摘引（逐条，不转述）

来源：`docs\re\NEXT_RE_TASKS_20261112.md` L272–L287。`[本次读码]`

> ### 第 9 步 · RE-N09：把逆向结论转成安全补丁契约
>
> **目标：** 每个准备采用的修改，都能说明适用对象、原行为、失败方式和回滚。
>
> 操作顺序：
>
> 1. 对实际写入口核查构建身份与原始字节守卫；未知镜像、已被其他补丁覆盖或入口窗不符均拒绝，并给出原因。审计已提示 ra2opt 的识别功能与 apply 路径可能未接通，需按当前版本验证。
> 2. 补齐寄存器、EFLAGS、栈、调用约定、线程、生命周期和卸载顺序；处理部分安装失败，验证已装项能还原。
> 3. 函数级比较真实原函数与候选函数的相同输入输出，包括边界输入、像素/缓冲、返回值和副作用；不要仅比较两个自行重写的算法。
> 4. 影响模拟时，固定输入和初始状态，按 tick 比较对象状态、RNG 调用序列、事件顺序和目标选择。状态 ID 和输出归一化规则必须事先说明，差异给出首个分歧点。
> 5. 涉及存档则验证退出进程后的重新加载，涉及联机则另验双方配置、协议与同步。在完成前标清单机范围。
> 6. 独立开关默认关闭，记录命中、成本与失败；演练安装→触发→关闭→卸载→原字节/配置还原。
>
> **交付：** `PATCH_CONTRACT.md`、版本矩阵、原函数对照样例、场景回归与回滚记录。
>
> **通过条件：** 安装态、执行态、行为态三项分别有证据；文档门禁 PASS 不代替游戏行为对照。

### 1.1 任务书中与 RE-N09 直接相关的其它原文（上下文摘引）

`[本次读码]`，均出自 `docs\re\NEXT_RE_TASKS_20261112.md`：

- L27：`RE-N06 / RE-N07 / RE-N08 → RE-N09 安全契约、回归与回滚`
- L36：`- **P2：RE-N07、RE-N09。** 根据基线选择修复对象；影响模拟的实现须先有相应行为对照。`
- L48（§2 表格「安全改动」行）：`| 安全改动 | 已有版本识别、开关、备份、回滚等部分实现与审计 | 不同入口是否真正执行守卫，运行/行为验证是否齐全 | “有识别功能”不等于“所有写入口拒绝未知构建” |`
- L79（原文含反引号，改用引文块避免转义）：

  > 以下 SHA-256 为本次用 `Get-FileHash` 实算；后续执行前仍须重新比对。

- L89：`分析镜像也不能只凭游戏名就视作官方未修改原版；后续“原版对照”须另行确认来源与指纹。`
- L246：`通过 RE-N09 的行为与回滚检查后，按 RE-N04 三臂复跑。未达预设目标则默认关闭或撤回，保留逆向知识。`
- L258：`相关事实见[安全能力盘点](../../lead/patch_capability_audit_20261112/PROGRESS.md#L38)。`
- L363（§5 任务卡模板）：`ID / 所属 A性能稳定性、B安全修改、C DLC 交付线` —— B 线即「B安全修改」。
- L374：`静态证据必须包含真实边界下的指令与 PE 映射；扫描无命中需说明搜索范围、支持的编码和反例校验。动态证据必须绑定实际目标、时钟与运行状态。行为结论必须包含有区分力的对照，不能以“脚本成功退出”替代。`

### 1.2 B 线上位规范（`docs\PROJECT_DIRECTION.md` §2.B L36–L42，逐字）

`[本次读码]`。这是「B 整体目标」在方向文档中的原始七条，比本卡四件口径更严，切片计划以其为边界：

> - 按目标镜像独立记录 ABI、结构、虚表槽、函数入口、字节窗口和调用契约；原版 game.exe 与尤复 gamemd.exe 的地址不得互用。
> - 补丁安装先验证构建身份与原始字节；未知构建或不匹配窗口拒绝安装，并输出原因。
> - 每项补丁具备独立开关、安装/卸载日志、必要遥测、失败处理与可实测的完整回滚；新实验开关默认关闭。
> - 检验寄存器、栈、线程、对象生命周期和卸载顺序；同时检查安装态、执行态与行为态。
> - 涉及模拟结果的修改必须补确定性对拍；涉及存读档的修改必须验证跨会话保存与加载；涉及联机的修改必须验证双方配置一致、协议兼容与同步结果。
> - 未通过联机验证的实验功能限定为明确标注的单机范围；客户端 UI 改动也须说明公平性影响。
> - 原 exe 保留只读基线；部署和真机执行遵守任务卡的明确写域、单写者和游戏实例独占约束。

L30 另有一条直接约束本卡的措辞：`不以“进程没退出”“CPU 不满”“截图正常”代替性能收益、稳定性或行为正确性验收。`

---

## 2 · 现状盘点（只读）

### 2.1 版本线与模块清单

`[本次实测]`（本卡 `Get-ChildItem -Filter *.py` 只读枚举）＋ `[本次读码]`（`file:line`）：

| 包 / 目录 | `.py` 模块数 | `TOOL_VERSION` | `__version__` | 回归（盘上 SUMMARY） | 状态 |
|---|---:|---|---|---|---|
| 仓库 `ra2forge\` | **11**：`__init__ __main__ builder cli design format80 install lzo maplib mixlib triggers` | `0.4`（`install.py:262`） | `0.3.0`（`__init__.py:9`） | — | 基线，**没有** `verify.py` |
| `W21_dlc_orphan\ra2forge_patched\` | 11 | `0.5` | `0.3.0` | V1–V7 用例 | ORPHAN-FIX01 |
| `W22_dlc_identity\ra2forge_patched_v6\` | 11 | `0.6` | `0.3.0` | 14 用例 / 116 断言 | PKG-IDENT01 |
| `W23_dlc_verify\ra2forge_patched_v7\` | 12（+`verify.py`） | `0.7` | `0.3.0` | 22 用例 / 196 断言 | SEAL-CHAIN01 |
| `W24_dlc_seal_fault\ra2forge_patched_v7i\` | 12 | `0.7` | `0.3.0` | 故障注入卡 | — |
| `W25_dlc_unseal\ra2forge_patched_v8\` | 12 | `0.8` | `0.3.0` | **39 用例 / 36 通过 / 3 失败** | 卡未完成（代理中途死亡） |
| `W26_dlc_unseal_fix\ra2forge_patched_v9\` | 12 | `0.9` | `0.3.0` | **39/39 PASS，387/387**，exit 0 | UNSEAL-FIX02 |
| `W30_csf_capability\ra2forge_patched_v10\` | **13**（11 + `csf.py` + `verify.py`） | **`1.0`** | `0.3.0` | **45/45 PASS，413/413**，exit 0 | 新增 CSF 读写 |
| `W34_mapselmd\ra2forge_patched_v11\` | **14**（+ `mapselmd.py`） | **`1.0`** | `0.3.0` | **51/51 PASS，462/462**，exit 0 | 新增 MAPSELMD 生成 |

补充事实 `[本次实测]`：

- 用户口径「仓库 `ra2forge\` 是 0.4 版」对应的是 **`TOOL_VERSION = "0.4"`**（`ra2forge\install.py:262`），不是 `__version__ = "0.3.0"`；两个版本号是不同字段，引用时不可混写（见 `DISAGREE.md` D2/D3）。
- `W30_csf_capability\regress_dlc_v10.py`、`W34_mapselmd\regress_dlc_v11.py` 均在盘；本卡**未复跑**（纪律：不动 `W21`–`W35`），故 45/51 全绿为 `[转引]` + `[待运行验证]`。
- `W35_mapselmd_live\` 目录存在，`out\` 下有 13 个产物（`install_w27.log` / `verify_after_install.log` / `MAPSELMD.INI.w35_v11` / `pristine_*` …），但**缺** `LIVE_RESULT.md`、`UNKNOWNS.md`、`DISAGREE.md`、`REAL_DIR_PROOF.txt`（对照 `REVIEW\_w35_prompt.md` §六）⇒ 按任务卡口径**未交付 / 未签发**。`[本次实测]` 目录枚举；是否跑过真机 `[待运行验证]`。

### 2.2 四件事 × 现状 × 缺口

| 用户口径目标 | 已具备（代码 / 产物） | 缺 | 判定 |
|---|---|---|---|
| **① 版本守卫** | `ra2opt\__init__.py:19-27` `KNOWN_GAMEMD`（以 `.text` 段 SHA-256 为键）；`ra2opt\game.py:104-124` `identity()` 实算整文件 SHA-256 + `.text` 段 SHA-256 + `patched` 标志；`FINAL_RULING.md` §5 对 `db264305…` 三重吻合复算 `[转引]`。`ra2forge_patched_v11\install.py:1140` 仅检查 `(game / "gamemd.exe").is_file()` | 所有**写入口**未接身份判定（`ra2opt\optimize.py:112-133` 的 `apply()` 只校验目录有效性，全函数体不调用 `identity()`，`FINAL_RULING.md` §4 第 2 条）；无镜像/发行版矩阵、无 `BASELINE.json` 绑定、无「拒绝或降级」策略、无「判据不足」处理、无版本矩阵的运行时观测 | **部分有 / 未接通**（不是「已具备」） |
| **② 行为验证** | `verify` 五项只读（结构 / `package_digest` 自洽 / 磁盘 sha256 漂移 / 孤儿 / seal，`W23\VERIFY.md:26-34`）；`csf.py` 写后 `read_csf(strict=True)` 往返；`builder._verify_next_scenario_chain` / `_verify_mix_contents`；`mapselmd._verify_output()`；离线回归 39/45/51 | **函数级确定性对拍 = 0 样例**（`FINAL_RULING.md` §4 第 5 条判「没有」）；改造前后行为等价性、按 tick 对象状态/RNG/事件顺序对照、跨进程存读档、联机同步、执行态 / 行为态证据均无交付 | **文件层有；行为层没有** |
| **③ 独立开关** | 构建期 `--csf-out` / `--csf-base`（W30）、`--mapselmd` / `--mapselmd-base`（W34），**默认关**且关闭时产物与前一版逐字节相同（`CSF_CAPABILITY.md:56`、`MAPSELMD_SPEC.md:174-176`）；`install --allow-content-conflict` / `--adopt-legacy`，`uninstall --legacy` / `--force`；`ra2opt` `profile` 配置档 + `skip_cddraw` 等旗标 | 安装期是**整包事务**：`package_files()`（`v11\install.py:702-723`）固定返回 `BATTLEMD98.INI` + 可选 `MAPSELMD.INI` + `*.MAP` + `expandmd98.mix`；`ra2md.csf` **不在**安装清单（W30 `UNCOVERED.md` §2）；无 per-feature 命中 / 成本 / 失败记录；无统一「新实验开关默认关闭」注册表；单活动包、异 id 拒绝 exit 3 | **构建期可分；安装期全有全无** |
| **④ 完整回滚** | W21–W26 累计：零写预检 + 事务 undo、`original_absent` / `_plan_orphans` / `removed_orphans`、`_rollback` 与记录回滚解耦、`uninstall` 收尾故障隔离 + `actions` 完整性、seal 门禁（exit 7/8/10）、三态报告、`verify` 漂移检测 | 复合故障残留「记录/seal 对」无自愈子命令；清单/seal 无信任链；真 `ra2youli` 有既存 v0.3 旧包未卸载；CSF / MAPSELMD 未全量纳入备份回滚；`verify` 无内容级校验；非 Windows / `WinError 32` / `SIGINT` / `keep` 槽 / legacy 子分支未实测 | **沙箱单包文件层有；「任何改造逐字节还原」未闭合** |

### 2.3 已有能力清单（W21–W26 累计，逐项核对）

`[本次读码]` 依据 `HANDOFF.md` §9、`W21\ORPHAN_FIX.md`、`W23\VERIFY.md`、`W26\UNSEAL_FIX.md`：

1. **安装事务 / 零写预检**：`DLC-STRICT01` 三分类（definite content conflict / unresolvable risk / notice），`--allow-content-conflict` 只释放内容冲突，路径安全 / 损坏清单 / 备份槽保护永不释放。
2. **seal**：`ra2forge_install.json.seal` 绑定清单规范化字节哈希；`verify` / `uninstall` 门禁；旧清单降级但不假 ok。`W23\VERIFY.md:10-14` 明确「seal 是防误操作与意外损坏的机制，**不是**抗恶意攻击的机制」。
3. **`verify`（只读）**：五项检查 + 退出码 `0/1/2/5/6/7/8/9`，`--json`；`gamemd.exe` 不是必需（`cli.py:246`）。
4. **`ra2forge_uninstall`**：按清单记录 + sha256 归属判定删除/还原，`original_absent` 处理「原版不存在」，`--json` 三态。
5. **内容冲突预检**：`--allow-content-conflict`；W34 追加 `MAPSELMD.INI` 的**永不释放**冲突类。
6. **原子替换**：`_stage_and_replace` / `_stage_text_and_replace`，同目录临时文件 + `os.replace()`，落地槽即时重验（防 TOCTOU / 别名）。
7. **回归**：`regress_dlc_v9.py` 39 例、`regress_dlc_v10.py` 45 例、`regress_dlc_v11.py` 51 例，用例只增不减、判据零放宽（`W26\DISAGREE.md` §2、`W30\DISAGREE.md` §3）。

### 2.4 回归结果的分级（防误引）

| 套件 | 盘上 `out\SUMMARY.txt` | 等级 |
|---|---|---|
| `regress_dlc_v8.py`（W25） | `cases: 39  passed: 36  failed: 3` / `assertions: 376 passed / 6 failed`，FAIL = `V5`(8/12)、`F7`(22/23)、`R2`(12/13) | `[转引]` 盘上产物，本卡未复跑 `[待运行验证]` |
| `regress_dlc_v9.py`（W26） | `cases: 39  passed: 39  failed: 0` / `387 passed / 0 failed` | `[转引]` + `[待运行验证]` |
| `regress_dlc_v10.py`（W30） | `cases: 45  passed: 45  failed: 0` / `413 passed / 0 failed` | `[转引]` + `[待运行验证]` |
| `regress_dlc_v11.py`（W34） | `cases: 51  passed: 51  failed: 0` / `462 passed / 0 failed` | `[转引]` + `[待运行验证]` |

`[本次读码]` `W34\UNCOVERED.md` U9 原文：「**回归是离线文件级**：`MS1..MS6` 验的是字节、清单、预检与还原，不是引擎行为。沙箱内 `gamemd.exe` 是 inert 占位文件，从不执行。」⇒ **任何「回归全绿 ⇒ 行为正确」的写法都违反本卡与 RE-N09 通过条件**。

---

## 3 · 四问判定

### 3.1 版本守卫

**判定 `[静态推断]`：工程上可行，且必须做；但「已具备」不成立 —— 现状是「有识别函数、无写入口接线」，须先补接线再谈判据强度。**

#### 3.1.1 五类判据的失效风险

| 判据 | 现有实现 / 证据 | 失效风险 | 建议用途 |
|---|---|---|---|
| **镜像整文件 SHA-256** | `ra2opt\game.py:108` 实算；任务书 L83-85 登记 `gamemd.exe`=`73201cc0…`、`ddraw.dll`=`85e0f7d5…` `[转引]`；`FINAL_RULING.md` §5 复算 `db264305…` 三重吻合 `[转引]` | 任一 PE 头改动（LAA / 栈扩容，`optimize.py:221-261`）、第三方 Detours 段、资源节改写、重打包、加壳都会改变整文件哈希 ⇒ 同一引擎版本出现多个合法哈希。本机已证存在**多个物理副本**：两个 `73201cc0…` 留痕态 + 至少两个 `db264305…` 原始态（`FINAL_RULING.md` §5 / ZCode 报告 `[转引]`）。且「官方 1.001」基线本身带 `.detour` 段（`ra2opt\__init__.py:25`），**不是干净零售件**（`FINAL_RULING.md` §5.1） | 只作**「这一份具体字节」的身份**，不作「发行版」判定；必须与字节数、节表、`.text` 哈希同时登记 |
| **`.text` 段 SHA-256** | `ra2opt\__init__.py:16-24` 用作 `KNOWN_GAMEMD` 键；设计理由「LAA/栈/堆只改 PE 头，代码段字节不变」`[本次读码]` | ① 代码级补丁 / hook / syringe / Ares / Phobos / Detours 改 `.text` ⇒ 失配，`game.py:120-121` 只能回落「未知（被第三方 Detours 补丁改过）」；② 同一代码段可对应不同发行版/语种/资源包（中文版、EA/Steam 重打包）⇒ **不能区分发行版**；③ 段范围定义（raw offset/size）随 PE 解析实现而异，需用同一 `pe.text_section_sha256` 口径 | **主判据之一**，用于「引擎代码是否为已登记版本」；必须附带节表与整文件哈希 |
| **PE 时间戳**（`TimeDateStamp` / 签名时间） | `ra2opt\__init__.py:25` 记「签名时间 2001-10-31」`[本次读码]`；`game.py:42-60` 输出 `characteristics` / `checksum` / `dll_characteristics` | 可任意伪造（链接器开关 / 手工改字段）；可复现构建使不同产物共享同一时间戳；同一官方版本的不同语言/发行版可能同戳；**与「是否被补丁改过」无关** | 仅作**描述性元数据**与冲突排查线索，**不得单独作为放行依据** |
| **`RA2MD.INI` 结构** | 本轮每趟启动前存字节副本、收尾逐字节还原（`HANDOFF.md` §5）；W35 基线 `RA2MD.INI`=`c91c6a47…`（`_w35_prompt.md` L57 `[转引]`）；`ra2opt` 会改其键值（`optimize.py:200-219`） | 用户可编辑、随分辨率 / 渲染后端 / `maxfps` / 音频 / 限帧变化（`RE-N04` 配置维实验即改这些）；同一镜像可有多份合法配置；配置项集合不能区分「哪个 exe / 哪个发行版」；该文件是**每趟要还原的可写配置**，不是只读身份凭据 | 只作**配置兼容性检查**与「本轮基线是否被还原」，**不参与镜像身份判定** |
| **关键文件存在性** | `ra2forge\install.py:615-618` / `ra2forge_patched_v11\install.py:1140-1143`：`(game / "gamemd.exe").is_file()`；`ra2opt\game.py:71` `self.valid = self.gamemd.is_file()`；`verify --help` 明确 `gamemd.exe is NOT required`（`cli.py:246`）；W21 V6a 用「无 gamemd.exe ⇒ 拒绝」`[转引]` | 最弱：复制几个文件名即可伪造；不区分版本 / 语种 / 是否被改；「有 `gamemd.exe`」连「是不是尤复」都不能严格证明；`verify` 故意不要求它 ⇒ 存在性与「可写操作」无必然联系 | 只作**「能否开始只读检查」的目录有效性前置**，绝不作身份放行 |

补充可用判据 `[静态推断]`（用于补强，非用户列举项）：PE 节表（节名 / 节数 / 各节 VA 与 raw size，特别是 `.detour`）、`ra2md.mix` / `langmd.mix` 内关键文件字节哈希（`MAPSELMD.INI` 5,573 B、`ra2md.csf` 5,211 标签，`W34\MAPSELMD_SPEC.md` / `W30\CSF_CAPABILITY.md` `[转引]`）、`ddraw.dll` 哈希、以及 `present_exes()` / `components()` 的组件集合（`ra2opt\game.py:99-142`）。

#### 3.1.2 推荐组合（分层，按强度递减）

| 层 | 内容 | 输出 |
|---|---|---|
| **L0 前置** | 目录有效性：`gamemd.exe` 存在 + 路径规范化（裸文件名、realpath、`commonpath` 越界拒绝） | `DIR_OK / DIR_INVALID`；只允许进入只读检查 |
| **L1 主判据（必须全部登记）** | `.text` 段 SHA-256 **＋** 整文件 SHA-256 **＋** 字节数 **＋** PE 节表（含 `.detour` 有无、各节 raw offset/size、COFF Characteristics / checksum） | `TARGET_ID`；与 `BASELINE.json` 逐字段比对，任一项不符即 `UNKNOWN`，不做「宽匹配」 |
| **L2 发行版 / 语种 / 第三方态** | `ra2md.mix` / `langmd.mix` 内关键条目字节哈希、`MAPSELMD.INI` 全长哈希、`ra2md.csf` 标签数与魔数、`ddraw.dll` 哈希、`present_exes()` / `components()` 集合 | `EDITION_LABEL`（如「YR 1.001 中文 / 含 .detour / 已装 ra2opt / 含 cnc-ddraw」） |
| **L3 弱判据** | PE 时间戳、`RA2MD.INI` 结构 | **仅描述与配置兼容**，不参与放行 |

**接线要求（这是本问最关键的工程结论）** `[静态推断]`：

- 把身份判定抽成单一 `identify_target(game_dir) -> {TARGET_ID, EDITION_LABEL, evidence, confidence}`，在**每一个写入口**的零写预检里调用：`ra2forge install` / `uninstall` / `build --install`、`ra2opt apply` / `restore`、`seed --verify` 的产物落位。禁止再出现「`identity()` 存在但 `apply()` 不调用」（`FINAL_RULING.md` §4 第 2 条三版一致的实测缺口）。
- 匹配结果三态：`MATCH` → 放行；`MISMATCH` → **拒绝写入并输出原因码**（对应 RE-N09 L278「未知镜像、已被其他补丁覆盖或入口窗不符均拒绝，并给出原因」）；`DEGRADED`（仅当用户明确授权）→ **只允许只读路径**（`verify` / `inspect` / `audit`）与构建期产物，**不允许落盘到游戏目录**。
- 「入口窗不符」还需绑定**原始字节窗口**：对 `ra2opt` 的 PE 头字段先 `pe.read` 比对当前值再只改需要改的（`optimize.py:221-254` `[本次读码]` 已具备该模式），对任何二进制 patch 必须保存「改前 N 字节 + 改后 N 字节 + VA/RVA/FOFF」。

#### 3.1.3 判据不足时该怎么办

`[静态推断]`，按 RE-N00 L100-107 与 RE-N09 L278：

1. **不回退、不猜测**：不得降级为「看起来像游戏目录」「旧哈希宽匹配」「文件名对得上」。`UNKNOWN` 就是 `UNKNOWN`。
2. **拒绝一切写**，把 `TARGET_ID=UNKNOWN`、缺失证据清单、实际读到的全部判据值写入 `BASELINE.json` / 本卡 `UNCOVERED.md`；`verify`/`inspect`/`audit` 等只读命令仍可运行并明确标注「未定谳」。
3. **可重建的重建来源**：按 RE-N00 L100 保存「完整 SHA-256 + 字节数 + 路径 + 字节副本或可验证重建来源」；本卡未实算哈希，任务书 L79 明确「后续执行前仍须重新比对」。
4. **上报 Lead 定谳**，在 `PATCH_CONTRACT.md` 版本矩阵中该行标 `[待运行验证]`；禁止以「分析镜像 = 官方未修改原版」为前提（任务书 L89）。
5. **多副本歧义**：`FINAL_RULING.md` §5 已证本机存在多个 `gamemd.exe` 物理副本 ⇒ 必须在判据里显式写「本次针对的是哪个绝对路径的哪一份字节」，不得用「本机那份 1.001」这种无路径指代。

---

### 3.2 行为验证

**判定 `[静态推断]`：不启动游戏可证「文件字节 / 静态指令 / 构建结构 / 安装态」四层，证不了「引擎行为」；「改造前后行为等价性」必须真机，且需与离线证据分成三态分别出具。**

#### 3.2.1 离线能证（本卡 `[本次读码]` 核对的现有能力）

| 层 | 可证命题 | 现有证据 / 手段 |
|---|---|---|
| 文件字节 | 安装后每个记录文件磁盘 sha256 == 记录值；卸载后目录逐字节 == golden；`ra2md.csf` 官方 5,211 标签解析再编码 `orig.to_bytes() == raw`；`MAPSELMD.INI` 官方 5,573 B 全文逐行存活 | `verify` 第 3 项、W21/W26 `diffsnap`、W30 `CSF_CAPABILITY.md:47-49`、W34 `MAPSELMD_SPEC.md:152-157` `[转引]` |
| 静态指令 | PE 映射 `FOFF = VA − 0x400000`、指令字节、rel32 解码、xref 计数、函数入口对齐 | W31/W32/W33/W34 `EVIDENCE\step*.py` `[转引]`；RE-N09 L374 要求「真实边界下的指令与 PE 映射」 |
| 构建结构 | `[Basic] NextScenario` 链与设计序一致；`expandmd98.mix` 恰含地图且 0 个 INI；`BUILD_REPORT.txt` 自检；补丁 `git apply --check` 可干净应用 | `builder.py:70-73, 123-147, 365-378` `[本次读码]` |
| 安装态 | 清单结构、`package_digest` 自洽、seal 门禁、孤儿、`actions` / 退出码 / 三态报告 | `W23\VERIFY.md:26-34`、`W26\UNSEAL_FIX.md` §3 `[转引]` |

**离线不能证** `[静态推断]`：散装 `ra2md.csf` / `MAPSELMD.INI` 是否真的覆盖 MIX 内同名并被引擎加载（W30 `UNCOVERED.md` §1、W34 `UNCOVERED.md` U1 均自标 `[待运行验证]`）；战役菜单条目可见性、通关→下一关推进、跨进程存读档、联机同步；渲染帧时间 / 掉帧；tick 语义与 RNG / 事件顺序；**改造前后行为等价性**（RE-N09 L280-282）。

> 特别提醒 `[本次读码]`：`W34\UNCOVERED.md` U9 明写「沙箱内 `gamemd.exe` 是 inert 占位文件，从不执行」；`W23\VERIFY.md:31` 明写 `package_digest`「**只能证明清单内部一致，不能证明磁盘上是什么**」。二者是「离线能证」的硬边界，不是措辞谦辞。

#### 3.2.2 真机可自动观测的行为（本会话已积累手段，`[转引]`）

依据 `REVIEW\_w35_prompt.md` L42-45、`HANDOFF.md` §4.4/§8、`REVIEW\LEAD_VERDICT_Aline_FINAL.md` §5/§6：

| 手段 | 能自动观测 | 已证边界 / 陷阱 |
|---|---|---|
| **枚举控件文本**（`EnumChildWindows`） | 菜单/对话框控件文本、`GUI:Continue`、`MSG:UnableMapSelect` 弹窗、战役菜单条目 | W27 Q1/Q2 实测靠此 + 截图；但「进图成功」不能靠 `mode[0xA8B238]` 判（`HANDOFF.md` §2 已自我推翻） |
| **读 `[0xA8ED84]` 定时器** | 局内是否推进（31.25 计数/s）、停推段 | **32 ms 定拍计时器，不是 FPS**，对负载不敏感（A-line FINAL §6）；闲置态必停推，`S_sleep`/`S_modal_ui` 是正常态（`HANDOFF.md` §3.3） |
| **`QueryThreadCycleTime`** | 窗口线程每拍 cycle → 每拍 CPU ms / 单核占用 | CPU 时间**结构性不含阻塞等待**，不能支持「画面不卡」（A-line FINAL §5、`HANDOFF.md` §4.4） |
| **内存标记检索** | `ECH02.MAP` 等 ASCII / UTF-16LE 命中，判断目标资源是否真的进入进程 | 命中 ≠ 已加载/已实例化；须与定时器、截图交叉（W35 prompt L47 要求 ≥2 硬指标） |
| **截图** | 关键节点画面（雪地图 / 基地 / 「任務完成」 / 报错框） | 「截图看着像」**不是证据**（W35 prompt L63）；需与定时器 / 内存 / 控件至少两项硬指标并用 |

**真机也不能自动观测（本会话授权内）** `[转引]`：渲染侧（GPU / `Present` / vsync 阻塞 / 掉帧）——A-line FINAL §5 判定需注入 / present 打点 / 调试器，而注入在本会话被明令禁止；更重战斗 / 大兵团；`[0xA8F7AD]` 运行时取值与打开效果（`LEAD_VERDICT_campaign_menu_q1.md` §7）。

#### 3.2.3 「离线能证 / 必须真机」分界表

`[静态推断]`（契约草案，供切片 S4 细化）：

| 命题 | 离线 | 真机 | 说明 |
|---|---|---|---|
| 包文件字节与记录一致、卸载逐字节还原 | ✅ 可证 | — | `verify` + diffsnap |
| 候选函数与真实原函数在同一输入下输出 / 副作用一致 | ⚠️ 仅静态指令级 | ✅ 必须 | RE-N09 L280「不要仅比较两个自行重写的算法」；`FINAL_RULING.md` §4 第 5 条判「没有」函数级对拍样例 |
| 按 tick 的对象状态 / RNG 序列 / 事件顺序 / 目标选择 | ❌ | ✅ 必须 | RE-N09 L281；须事先说明状态 ID 与输出归一化，给首个分歧点 |
| 散装 CSF / MAPSELMD 被引擎采用 | ❌ | ✅ 必须 | W30/W34 自标 `[待运行验证]` |
| 战役推进 / 菜单可见 / 跨进程存读档 | ❌ | ✅ 必须 | RE-N09 L282、`REVIEW\LEAD_VERDICT_map_start_root_cause.md` §3 |
| 安装态（清单/seal/actions/退出码） | ✅ 可证 | — | 三态之一 |
| **执行态 / 行为态** | ❌ | ✅ 必须 | RE-N09 L287 通过条件 |

**结论**：B 线的「行为验证」必须双轨 —— 离线只出三态中的**安装态**证据；**执行态与行为态**另立真机批次（S5），且 `文档门禁 PASS 不代替游戏行为对照`。任何以「回归 39/45/51 全绿」「脚本 exit 0」「游戏没崩」代替行为对照的写法均违反 RE-N09 L287、任务书 L374 与 `PROJECT_DIRECTION.md` L30。

---

### 3.3 独立开关

**判定 `[本次读码]` + `[静态推断]`：构建期已天然可分（两个 opt-in 开关默认关且字节级兼容）；安装期不可分（整包事务、全有全无）。要做「可单独启用/停用某项改造」，必须把开关下沉到 `package_files()` 之前的一层「feature set → 文件子集」映射，并同步 digest / seal / 备份 / 卸载。**

#### 3.3.1 现状（代码事实）

- `v11\install.py:702-723` `package_files()` 返回顺序：`BATTLEMD98.INI`（必需）→ 可选 `MAPSELMD.INI`（`--mapselmd` 构建时才有）→ `*.MAP` → `expandmd98.mix`。`[本次读码]`
- `ra2md.csf` / `csf_patch.json` **不在** `package_files()`；W30 `UNCOVERED.md` §2 原文：「**`install.py` 安装/备份/卸载链路尚未接入 `ra2md.csf`**」。`[本次读码]`
- `builder.py:131-138`：启用 `--csf-out` 时 `BATTLEMD98.INI` 的 `Description=` 从原始文本改为稳定标签 `RA2F:<8hex>`，即**改 INI 字节**。`[本次读码]`
- `builder.py:143-147`：`expandmd98.mix` 由同一批 `map_texts` 生成，`_verify_mix_contents()` 强制「恰含地图、0 个 INI」。`[本次读码]`
- `W34\MAPSELMD_SPEC.md:150-158`：MAPSELMD 阶段 `Scenario=<MAP>.MAP`、末段无子项、追加键连续，全部派生自 design 的 missions / chain / side。`[转引]`
- `cli.py:150-159, 289-304`：`--csf-out` / `--csf-base` / `--mapselmd` / `--mapselmd-base`，默认关；`--csf-base` 单独用返回 2、`--mapselmd-base` 单独用返回 2。`[本次读码]`
- `W30\CSF_CAPABILITY.md:56` 与 `W34\MAPSELMD_SPEC.md:174-176`：不传开关时产物与 v9 / v10 **逐字节相同**。`[转引]`
- `install` 旗标是**事务级**而非改造点级：`--force`（明确「NO effect on install」，`cli.py:173-181`）、`--allow-content-conflict`（只释放内容冲突）、`--adopt-legacy`（身份继承）；`uninstall --legacy` / `--drop-legacy-battlemd` / `--force`。`[本次读码]`
- `W22` 身份规则：单活动包，异 `package_id` 拒绝 exit 3，`--force`/`--allow-content-conflict`/`--adopt-legacy` 均不可越过（`HANDOFF.md` §9.2 `[转引]`）。

#### 3.3.2 耦合矩阵

行 = 改造点 A，列 = 改造点 B；单元格 = 耦合类型与依据。`[静态推断]`，依据均为上节 `[本次读码]` 事实。

| A \ B | `*.MAP` | `BATTLEMD98.INI` | `expandmd98.mix` | `ra2md.csf` | `MAPSELMD.INI` |
|---|---|---|---|---|---|
| **`*.MAP`** | — | **中**：INI 的 battle 条目引用关卡 / 战役名；没有 INI 就没有游戏内入口 | **强**：MIX 内容就是同一批地图的 GBK 字节，`_verify_mix_contents` 强制 exactly maps ⇒ 必须同批生成 / 同批装 / 同批卸 | 无 | **强**：阶段段 `Scenario=` 必须等于地图文件名，link/末关来自同一 `chain` 与 `EndOfGame` |
| **`BATTLEMD98.INI`** | 中 | — | **弱**：MIX 内禁止任何 INI（`builder.py:367-369`） | **强**：启用 CSF 后 `Description=` 变标签；装 INI 不装 CSF ⇒ `MISSING:RA2F:...`（W30 `UNCOVERED.md` §1） | **中**：菜单可见徽章只有 3 个硬编码槽（`LEAD_VERDICT_campaign_menu_q1.md` §2 `[转引]`），借官方 id 时 INI 覆写与推进注册联动 |
| **`expandmd98.mix`** | 强 | 弱 | — | 无 | 无（MIX 只放地图） |
| **`ra2md.csf`** | 无 | 强 | 无 | — | **中**：两者都是「**完整合法文件的 whole-file 覆盖**」（最小文件会让官方全挂，W29 CSF 警告 / W34 D4）；CSF 当前未接安装清单，MAPSELMD 已接但冲突永不释放 |
| **`MAPSELMD.INI`** | 强 | 中 | 无 | 中 | — |
| **全体 × 安装事务** | **强（全局）** | **强（全局）** | **强（全局）** | **强（当前未纳入，是缺口）** | **强（全局）** |

最后一行含义：`package_digest` 由 `package_files()` 的 steps 计算（`v11\install.py:682-695`），seal 绑定清单字节，备份/卸载按清单条目遍历 ⇒ **任何文件子集变化都会改变 digest、seal、清单、备份槽与卸载动作**，不能只改一个文件而让其余元数据保持不变。

#### 3.3.3 必须一起动的组 / 天然可分开的点

**必须一起动**：

- **G1 最小可运行包** = `{*.MAP, expandmd98.mix, BATTLEMD98.INI}` —— 入口 + 内容，MIX 与地图同源。
- **G2 CSF 组** = `{BATTLEMD98.INI, ra2md.csf}` —— 启用 CSF 时 INI 字节改变，两者不可拆。
- **G3 战役推进组** = `{*.MAP, MAPSELMD.INI, BATTLEMD98.INI}` —— `Scenario=`、link、side 与 battle 条目同源；且 W34 明确「仅改 `SkipMapSelect` 或仅打包 MIX 都不修」`[转引]`。
- **G4 全局事务** = 所有入选文件 ∈ 同一 `package_id` 的清单 / digest / seal / 备份 / 卸载；单活动包、无并存（`W34\UNCOVERED.md` U6）。

**天然可分开（构建期已证）**：

- `--csf-out` 与 `--mapselmd` 互不依赖、各自默认关；关闭时产物与前一版逐字节相同（`W30\DISAGREE.md` §3、`W34\APPLY.md` §4）。
- `MAPSELMD.INI` 在 `package_files()` 里按「文件是否存在」条件纳入 ⇒ v10 包不受影响（`v11\install.py:714-718`）。
- CSF 产物落在包目录但**当前不进安装清单** ⇒ 它事实上与安装事务解耦，但这是**缺口**不是设计：真机一旦确认散装覆盖，就必须补进备份/卸载（W30 `UNCOVERED.md` §2）。

**不可分 / 不能只动一半**：`install`/`uninstall` 是整包事务；`MAPSELMD.INI` 是 whole-file 覆盖，不能只追加我方条目（W34 D4 硬规则）；`ra2md.csf` 必须克隆官方全文后追加（W30 `CSF_CAPABILITY.md:41-45`）。

**可行性结论** `[静态推断]`：可行，但不是「加几个布尔旗标」——需要新的一层 `FEATURE_SET`（默认全关）→ `package_files()` 子集 → digest/seal/备份/卸载联动 → 每个开关记录命中 / 成本 / 失败（RE-N09 L283、PROJECT_DIRECTION L38）。这必然改动 `install.py` 并新增回归（既有 51 例判据零放宽）。

---

### 3.4 完整回滚

**判定 `[转引]` + `[本次读码]`：现有卸载路径在「隔离沙箱 / 单活动包 / 文件层 / Windows / `OSError(WinError 5)`」范围内可逐字节还原且诚实报告；但用户口径「任何改造都能逐字节还原」**尚未闭合**。以下是自己核对的原文，不采用任务书转述。**

#### 3.4.1 原文核对

**(a) W21「错还原」缺陷** —— `W21_dlc_orphan\DISAGREE.md:17-24` 原文 `[本次读码]`：

> ## 2. 「卸载时可能删错」→ 实测未发现误删，真实风险是「卸载时错还原」
> - 未发现任何误删：用户文件（USERMAP1.MAP、BATTLEMD.INI、RA2MD.INI、gamemd.exe）在全部用例中逐字节未动；uninstall 只动清单记录过的名字，且 sha 匹配才删。
> - 实际发生的第二张面孔是**过度还原（over-restore）**：A 自己创建的文件（INI/Y/MIX，原版状态是"不存在"）在 A′ 替换时被写进 `.ra2forge.bak`（"最旧原版优先"策略把 A 的字节当成了原版），uninstall 于是把它们"还原"回 A 的内容——卸载后残留 4 个 A 时代文件（`snaps/t1_31_after_uninstall.sha.txt`）。本补丁用 `original_absent` 旗标修复了这一支（V3：卸载后逐字节回到初始态）。

`W21\DISAGREE.md:10-15` 另修正机制：「清单条目被**整体丢弃**，文件留在盘上」，不是「仍被旧清单记录」；根因见 `W21\ORPHAN_FIX.md:64-66`（`preinstall_plan()` 只遍历新包文件、`install_package()` 用只含新包文件的 entries 整体重写清单）。修复：`original_absent` / `_plan_orphans()` / `_execute_orphan_plan()` / `_rollback()` undo 日志（`ORPHAN_FIX.md` §3）。`[本次读码]`

**(b) W25「复合故障下配不上的记录/seal 对」** —— 该结论出自 `REVIEW\LEAD_STATUS_W25_incomplete.md:30-33`（Lead 依据 W25 的 `R1` 17/17 PASS 判定），**不是 W25 卡自己的报告**（同文件 L12-13：`报告类交付…缺失（代理死在写报告之前）`）。原文 `[本次读码]`：

> ⇒ **`install.py` 里那处 `except OSError: pass` 会把"清单回滚失败"吞掉，导致新记录留存**，随后 `verify` **exit 8**（seal 与清单不配对）。
> **这直接否证了 v7 docstring 那句「install never leaves a seal-era record standing without its seal」的普适性**——在"回滚自身也失败"的复合故障下，它会留下配不上的记录/seal 对。

同文件 §2.2 `R2` 失败断言原文：`R2: package files rolled back (created files removed) - the tree is exactly golden + the standing record ... FAIL`；§2.3 `F7` 原文：`F7 (W25): actions intact - every recorded file restored/removed and the record deleted ... FAIL`。盘上 `W25\out\SUMMARY.txt:2-3`：`cases: 39  passed: 36  failed: 3` / `assertions: 376 passed / 6 failed`（FAIL = `V5` 8/12、`F7` 22/23、`R2` 12/13）。`[本次读码]`

**(c) W26 对 W25 的勘误（不得继承旧前提）** —— `W26\DISAGREE.md` §1/§3/§4 原文 `[本次读码]`：

> - **任务书前提**：引述 `R2` 失败断言认为"记录回滚失败中断了后面的包文件回滚，导致创建的包文件没有被移除"。
> - **实测事实**：① W25 `install.py:1979-1980` 用 `except OSError: pass` **直接吞掉了**记录回滚异常，所以外层 `L1988` 的 `_rollback(game, undo)` **当时实际执行了**且已经移除了全部 4 个包文件；② `regress_dlc_v8.py:2202` 失败的直接原因是 `sha_tree()` 按 `Path` 顺序、`tree_lines_without()` 按 SHA-256 hex 排序导致行序不一致；③ **但生产隐患真实存在**：吞掉 `[WinError 5]` 并撒谎称 `"the install record was rolled back ... nothing was left in the unsealed state"`。
> - `F7` 失败出自**夹具错配**（卸载的是 A1 的 4 个 `created` 文件，正确动作本就是 `removed    Y.MAP`）；第 3 项失败是 `V5`（`DRIVER` 错指 `v8_rollback_fault_driver.py`，3 次注入全被 usage exit 3 拒绝）。

W26 修复（`UNSEAL_FIX.md` §2）：`_rollback()` 逐项 `except Exception` 隔离、记录回滚与包文件回滚解耦并诚实聚合、`uninstall()` 全链路收尾隔离 + `actions` 完整性、`failed_step → exit 1`；39/39 PASS、387/387 断言、exit 0（`out\SUMMARY.txt`）。`[本次读码]`

**(d) 复合故障的残留状态仍无自愈** —— `W26\UNCOVERED.md:10-11` 原文 `[本次读码]`：

> 在 `R1` 中，旧 seal 保持未动、新清单因自身回滚写失败而留盘上，形成"新清单 + 旧 seal"不匹配对（`verify` exit 8、`uninstall` exit 8、`install` 因盘上是旧字节而与新清单不符触发 strict risks 拒绝）。本卡已保证**诚实报错并完整回滚所有包文件**，但不越权删除用户/只读清单文件，仍需清除只读并人工清理损坏记录对后重装——若未来需要专用诊断/恢复子命令需另立设计。

`REVIEW\LEAD_STATUS_W25_incomplete.md` §4.3 同要求：「要么提供**明确且安全**的恢复路径…要么在文档里**明确写"不可恢复、需手工处理"**——不许含糊」。`[本次读码]`

**(e) 其它原文**：`W23\VERIFY.md:10-14`「seal 是**防误操作与意外损坏**的机制，**不是**抗恶意攻击的机制：能改清单的人同样能重算 seal」；`W21\UNCOVERED.md:13-14` 伪造清单威胁面（V6c 实测：`removed USERMAP1.MAP`）；`W26\UNCOVERED.md` §1–§6（非 Windows、`WinError 32`、`SIGINT`、legacy 子分支、`failed_actions[]` schema）；`W30\UNCOVERED.md` §2（CSF 未接安装/卸载）；`W34\UNCOVERED.md` U6/U7/U8（MAPSELMD whole-file 冲突无自动路径、verify 无 MAPSELMD 专项校验、散装 vs MIX 未做二选一真机对照）。`[本次读码]`

#### 3.4.2 已知缺口表

| # | 缺口 | 原文出处 | 对「完整回滚」的影响 | 归属切片 |
|---|---|---|---|---|
| G-1 | 复合故障残留「新清单 + 旧 seal」对：`verify`/`uninstall` exit 8、`install` strict risks 拒绝；**无专用恢复子命令**，只能清只读 + 人工清理 + 重装 | `W26\UNCOVERED.md:10-11`；`LEAD_STATUS_W25_incomplete.md` §4.3 | 最坏失败态**不能由工具自愈**；「任何改造都能还原」在该分支不成立 | S3 |
| G-2 | 清单 / digest / seal **无信任链**（三者可一起伪造）；`verify` 只能靠磁盘对账暴露 | `W23\VERIFY.md:10-14`；`W21\UNCOVERED.md:13-14`；`HANDOFF.md` §9.4 | 不能声称「抗恶意 / 签名」；「完整」限于防误操作 | 另立项（签名体系），本卡不承诺 |
| G-3 | 真 `ra2youli` **不是干净态**：既存 v0.3 旧包（`fe3bdf62…`，「钢铁残响」），Lead 未卸载、等用户裁决 | `HANDOFF.md` §9.3；`PAUSE_STATE_20261113.md` §5 | 真实目标上的「逐字节还原」**从未演示**；所有 install/uninstall 实验都在隔离沙箱 | 需用户裁决；S3 只写契约 |
| G-4 | `ra2md.csf` **未纳入** `package_files()` / 备份 / 卸载；散装覆盖是否生效还需真机 | `W30\UNCOVERED.md` §1-§2；`CSF_CAPABILITY.md:68-69` | 若 CSF 改造点落地，卸载**还原不到它** | S2 → S3 |
| G-5 | `MAPSELMD.INI` 是 whole-file：foreign 文件 definite conflict **永不释放**、`--allow-content-conflict` 也不放行；多包并存不支持；`--mapselmd-base` 硬编码校验官方 14 阶段 | `W34\UNCOVERED.md` U6；`install.py:380-384, 1151-1154` | 第三方 / 其它语言版本无自动化覆盖路径；每目录只能一个带 MAPSELMD 的包 | S2 → S3 |
| G-6 | `verify` 无**内容级**校验：MAPSELMD 官方 14 阶段仍在 / 追加键连续 / 末段无子项、CSF 官方 5,211 标签完整性，只在构建时自检 | `W34\UNCOVERED.md` U7 | 安装后「仍完整」缺证据；回滚后「确实还原成合法文件」也缺证据 | S3 |
| G-7 | 非 Windows、`WinError 32` 句柄锁、`SIGINT`/自定义 `RuntimeError`、`_uninstall_legacy()` 部分子分支、`backup="keep"` 槽语义、`changed` 孤儿非 strict 分支 | `W26\UNCOVERED.md` §1-§5；`W21\UNCOVERED.md` §2/§4/§7 | 回滚在其它故障类 / 平台上的行为未实测 | S3（补用例设计） |
| G-8 | `ra2opt` 侧 `restore`「完整回滚」**从未实测**（只有 `tests.py` 离线自检代码，`apply` 未验身份门） | `patch_capability_audit_20261112\FINAL_RULING.md` §4 第 2/3 条；`PROGRESS.md` §目标 A | B 线是**两条工具链**：`ra2forge`（文件层）与 `ra2opt`（PE/渲染/配置层）；后者的回滚未闭环 | S1（盘点）→ S3 |
| G-9 | 散装 `ra2md.csf` / `MAPSELMD.INI` 覆盖 MIX 内同名的**端到端引擎行为**未真机验证 | `W30\UNCOVERED.md` §1；`W34\UNCOVERED.md` U1/U8 | 回滚「还原到哪个文件」的前提本身未定谳 | S4 → S5 |

**判定汇总**：已修的是「沙箱内、单活动包、文件层、Windows、`WinError 5`」的回滚与诚实报告；**未闭合**的是真机目标、全部改造点（CSF/MAPSELMD）覆盖、复合故障自愈、信任链、内容级校验、非 Windows/异常类覆盖、`ra2opt` 侧实测。因此本卡不写「完整回滚已具备」，只写「沙箱文件层已具备，完整回滚未定谳」。

---

## 4 · 最小可交付切片（按依赖排序）

原则：一次只做一件事；每片给**可执行的验收检查**；首片纯离线、当晚可完成；不改仓库 `ra2forge/`、不动 `W21`–`W35`、不启动游戏；后续各片各自新建独立写域。成本单位为工作单元（约 2–4 h，非工期承诺，任务书 L352）。

### S1 · 版本守卫契约与写入口盘点（**首片，纯离线，当晚可完成**）

- **目标**：产出 `TARGET_IDENTITY.md` + `GUARD_MATRIX.csv` + `DISAGREE.md` / `UNCOVERED.md`。固化 §3.1 五类判据的失效风险、L0–L3 推荐组合、`UNKNOWN` 处理；逐写入口列出现有守卫与「是否调用身份判定」。
- **验收（可执行检查）**：
  1. `GUARD_MATRIX.csv` 每个写入口一行，至少覆盖 `ra2forge install` / `ra2forge uninstall` / `build --install` / `ra2opt apply` / `ra2opt restore` / `seed --verify`；每行含 `file:line`、现有判据、是否调用 `identity()`、判定（`MATCH`/`MISMATCH`/`UNKNOWN`）、原因码。
  2. `ra2opt\optimize.py:112-133` 与 `ra2forge_patched_v11\install.py:1140-1143` 各有引用行；矩阵含「`FINAL_RULING.md` §4 第 2 条：`apply()` 全函数体不调用 `identity()`」这一缺口行。
  3. 矩阵有一行专门写「判据不足 → 拒绝写入 + `TARGET_ID=UNKNOWN` + 缺失证据清单 + 仅只读降级」，且与 RE-N00 L100-107 / RE-N09 L278 逐条可对齐。
  4. 五类判据各有一行「失效风险」与「是否可作放行依据」，PE 时间戳 / `RA2MD.INI` 结构 / 关键文件存在性三行明确标「**不得单独放行**」。
  5. 隔离自证：`git status --porcelain -- ra2forge/ ra2youli/ lead/next_re_20261112_r02/W21*` 前后一致；全程零游戏进程、零写游戏目录。
- **依赖**：无（本卡 W36 的 §2/§3.1 即输入）。
- **成本**：**1 个工作单元**，无真机、无注入、无回归脚本改动、不写代码。

### S2 · 独立开关的「feature set → 文件子集」契约（纯离线）

- **目标**：`FEATURE_SWITCH_CONTRACT.md`：每个改造点的默认关状态、文件子集、耦合组 G1–G4、digest/seal/备份/卸载同步规则、命中/成本/失败记录格式；以现有「关闭时字节级兼容」为先例。
- **验收**：
  1. 对 §3.3.2 矩阵每个「强耦合」对给出一条可执行检查（例：「启用 CSF 而不投放 `ra2md.csf` ⇒ `BATTLEMD98.INI` 的 `Description=` 必须仍为原始文本，或构建期硬拒绝」）。
  2. 契约覆盖 `package_files()` 全部返回项 **＋** `ra2md.csf`；每条开关有 `default=off`、回退态与「关闭时与 v10/v11 逐字节相同」的检查命令。
  3. 明确写出「G4 全局事务：子集变化 ⇒ digest / seal / 清单 / 备份 / 卸载同步变化」的公式与校验点。
  4. 不要求改代码；不改既有 51 例判据。
- **依赖**：S1（身份判定决定开关是否可启用）。
- **成本**：1 个工作单元。

### S3 · 完整回滚缺口闭环（离线，含新增回归设计）

- **目标**：在隔离沙箱补 G-1 的「明确且安全恢复路径」设计、G-6 的 `verify` 内容级校验规则、G-4/G-5 的 CSF/MAPSELMD 纳入清单/备份/卸载的契约、G-7 的用例清单；给回归用例设计（既有 51 例一条不减、判据零放宽）。
- **验收**：
  1. 每条缺口有「复现命令 → 期望退出码/输出 → 与 golden 逐字节 diff」三元组。
  2. G-1 状态在契约里二选一定谳：`recover`（给出安全子命令的输入/输出/失败分支）或 `manual-only`（写明「不可恢复、需手工处理」的具体步骤），**不许含糊**（`LEAD_STATUS_W25_incomplete.md` §4.3）。
  3. 新增用例列表标明「继承 51 例 + 新增 N 例」，无删减、无阈值放宽。
  4. 明确不承诺抗恶意（G-2 另立项）。
- **依赖**：S2（开关决定哪些改造点进清单）。
- **成本**：2 个工作单元（含回归设计与离线复跑）。

### S4 · 行为验证双轨契约（离线契约 + 真机批次前置）

- **目标**：`BEHAVIOR_CONTRACT.md`：§3.2.3 分界表定稿、三态证据模板（安装态/执行态/行为态）、函数级对拍样例规格（RE-N09 L280）、按 tick 比较口径与首个分歧点格式（L281）、单机范围标注（L282）、自动观测手段与「≥2 硬指标」规则。
- **验收**：
  1. 分界表每条命题可映射到具体命令，或明确标 `[待运行验证]`；不得出现「回归全绿 ⇒ 行为正确」「游戏没崩 ⇒ 功能正常」「脚本 exit 0 ⇒ 行为对照通过」。
  2. 三态各给一份证据模板，且明写「离线只出安装态」。
  3. 真机部分**只写预案不执行**；列明所需授权、隔离载体、单实例锁（`HANDOFF.md` §5）、`BASELINE.json` 输入指纹（RE-N00 L107）。
- **依赖**：S1–S3（版本、开关、回滚定谳后才谈行为对照）。
- **成本**：1 个工作单元契约；真机另立预算。

### S5 · 真机行为对照批次（**非本卡执行，需明确授权**）

- **目标**：按 RE-N04 三臂（经来源确认的对照构建 / 同补丁关开关 / 开开关）复跑，补执行态与行为态证据；演练 RE-N09 L283「安装→触发→关闭→卸载→原字节/配置还原」。
- **验收**：安装态 / 执行态 / 行为态三项分别有证据；每条承重结论可定位到「输入指纹 + 原始证据 + 生成方法」；差异给首个分歧点；跨进程存读档 / 联机按范围标注；未达预设目标则默认关闭或撤回（任务书 L246）。
- **依赖**：S1–S4 + 用户明确真机授权 + 隔离载体 + `.game_instance.lock` 单实例 + 收尾逐字节还原。
- **成本**：另立批次，**不在当晚**。

**依赖链**：`S1 → S2 → S3 → S4 →（授权）S5`。S1 无前置、纯离线、可当晚完成；S5 之前全部不启动游戏。

---

## 5 · 纪律复核

- 纯离线只读：未启动游戏、未 attach、未写 `ra2youli`、未改仓库 `ra2forge/`、未动 `W21`–`W35` 任何目录、`git` 只读、未写代码。唯一写操作是创建并写入 `lead\next_re_20261112_r02\W36_b_line_kickoff\` 下三个 Markdown 文件。
- 结论分级：全文按 §0 口径标注；既有回归数字一律 `[转引]` + `[待运行验证]`，未把「全绿」写成「行为正确」。
- 与任务书前提不符处：见 `DISAGREE.md`（D1–D9），**未迁就**。
- 未覆盖与不确定项：见 `UNCOVERED.md`。
- A 线停放依据 `REVIEW\LEAD_VERDICT_Aline_FINAL.md` §7 / `PAUSE_STATE_20261113.md` §2 `[转引]`；C 线两条判定的**性质**见 `DISAGREE.md` D8。
