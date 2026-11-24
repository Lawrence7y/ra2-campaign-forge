# UNCOVERED · W36 未覆盖与不确定项

> 卡 `W36_b_line_kickoff`｜2026-11-13｜纯离线只读分析卡
> 口径同 `B_LINE_PLAN.md` §0。按影响排序；每项给「是什么 / 为什么没做 / 最小下一证据 / 归属」。
> 本卡**只出方案**，不写代码、不跑脚本、不启动游戏；下列项目均**未闭环**。

## 1 · 本卡方法学边界（最重要）

| # | 未覆盖 | 原因 | 最小下一证据 | 归属 |
|---|---|---|---|---|
| U1 | **未运行任何回归 / 构建 / 校验脚本**：`regress_dlc_v9/v10/v11.py`、`git apply --check`、`verify`、`build` 全部未跑 | 硬性纪律「纯离线只读 + 不动 `W21`–`W35` 任何目录」，跑这些脚本会在其 `sandbox\` / `out\` 写盘 | `[待运行验证]`：在各自新卡的独立写域复跑，核对 `out\SUMMARY.txt` 的 `cases/passed/assertions/exit` 四元组；本卡 39/45/51 全绿一律 `[转引]` | S3 / 后续执行卡 |
| U2 | **未实算任何镜像 / 文件 SHA-256**（未跑 `Get-FileHash` 或等价哈希实算） | 本卡是只读分析，未对二进制做字节级断言；任务书 L79 明写「实算；后续执行前**仍须重新比对**」 | `[待运行验证]`：S1 在 `BASELINE.json` 里重新实算 `gamemd.exe` / `ddraw.dll` / `ra2md.mix` / `langmd.mix` 的 SHA-256 + 字节数 + 绝对路径，并与任务书 L83-85、`FINAL_RULING.md` §5 三方比对 | S1 |
| U3 | **未独立复算静态反汇编承重指令**：W31/W32/W33/W34 的 `EVIDENCE\step*.py` 未跑，rel32 / 指令边界 / xref 计数未复核 | 本卡不重做 C 线静态取证 | `[转引·待核]`：如 B 线需要引用「散装优先」「`MapSelect::Init` 分支」「菜单徽章硬编码」，须由 Lead 或后续卡复核原始 stdout；本卡仅按 `[转引]` 引用 | S4 / Lead |
| U4 | **未读 `W35_mapselmd_live\out\` 的产物内容**（只做了目录枚举），未看 `install_w27.log` / `verify_after_install.log` / `MAPSELMD.INI.w35_v11` 等 | 避免把未签发产物当事实；且纪律要求不动 `W21`–`W35` | `[待运行验证]`：由 Lead 复核 W35 `out\` 与 `REAL_DIR_PROOF.txt`（当前缺失）后再决定是否签发；在签发前**不得**引用 W35 任何结论 | Lead / C 线 |
| U5 | **未逐行通读 `ra2opt` 全部 17 个模块**，尤其 `backup.py` 的 `restore` 实现、`tests.py` 的 `restore_roundtrip`、`cli.py` 的 `seed --verify` | 本卡对 `ra2opt` 的判定依赖 `patch_capability_audit_20261112\PROGRESS.md` / `FINAL_RULING.md` 的 `[转引]` + 抽样读码（`__init__.py` / `game.py:63-149` / `optimize.py:100-264`） | `[待运行验证]`：S1 盘点时逐写入口补 `file:line`，并确认 `restore` 是否真的调用身份判定；`FINAL_RULING.md` §4 第 3 条已判「完整回滚从未实测」 | S1 / S3 |

## 2 · 四问中明确标 `[待运行验证]` 的部分

| # | 未覆盖 | 现有出处 | 最小下一证据 | 归属 |
|---|---|---|---|---|
| U6 | **散装 `ra2md.csf` / `MAPSELMD.INI` 是否真的覆盖 MIX 内同名并被引擎加载**（端到端） | `W30\UNCOVERED.md` §1；`W34\UNCOVERED.md` U1 / U8；`MAPSELMD_SPEC.md` §5.4 | 真机：投放散装 + 控件文本 / 定时器 / 内存标记 / 截图 ≥2 硬指标；负控删掉散装应复现 W27 报错 | S4 → S5 |
| U7 | **改造前后行为等价性、函数级对拍、按 tick 的 RNG / 事件顺序 / 目标选择对照** | RE-N09 L280-282；`FINAL_RULING.md` §4 第 5 条「没有」；`PROJECT_DIRECTION.md` L40 | 先出契约与样例规格（S4），再真机三臂复跑（S5）；本卡未给任何 fixture | S4 / S5 |
| U8 | **渲染侧（GPU / `Present` / vsync 阻塞 / 掉帧）、更重战斗条件** | `REVIEW\LEAD_VERDICT_Aline_FINAL.md` §5 / §7 | 需注入 / present 打点 / 调试器 —— 本会话禁止，须独立授权 + 隔离载体 | 不在 B 线首轮 |
| U9 | **跨进程存读档、联机双方配置/协议/同步、单机范围标注的实际验证** | RE-N09 L282；`PROJECT_DIRECTION.md` L40-41 | 真机批次；完成前一律标「单机范围」 | S4 / S5 |
| U10 | **`[0xA8F7AD]` 运行时取值、隐藏调试列表打开后的实际效果；三个槽位替换官方战役后的连带影响** | `LEAD_VERDICT_campaign_menu_q1.md` §7 | 真机（且该门控「实测不可达」，靠 INI/散装开不了） | C 线 |
| U11 | **W27 Q2 失败是否由「劫持 `[SOV1]`」诊断手法引起**（未分离） | `PAUSE_STATE_20261113.md` §2 | 单独变量真机对照 | C 线 |

## 3 · 完整回滚 / 独立开关未闭环项（承接 `B_LINE_PLAN.md` §3.4.2）

| # | 未覆盖 | 现有出处 | 最小下一证据 | 归属 |
|---|---|---|---|---|
| U12 | **G-1 复合故障残留对无自愈子命令**：是否「明确且安全可恢复」或「不可恢复、需手工处理」**尚未二选一定谳** | `W26\UNCOVERED.md:10-11`；`REVIEW\LEAD_STATUS_W25_incomplete.md` §4.3 | S3 给二选一文案 + 复现命令 / 期望退出码 / 逐字节 diff 三元组 | S3 |
| U13 | **清单 / digest / seal 信任链**（三者可一起伪造） | `W23\VERIFY.md:10-14`；`W21\UNCOVERED.md:13-14`；`HANDOFF.md` §10 | 签名体系（外部密钥 / TUF 式元数据）属**另立项**，本卡不承诺抗恶意 | 另立项 |
| U14 | **真 `ra2youli` 既存 v0.3 旧包**（`fe3bdf62…`，「钢铁残响」）卸载与否、卸载对 A 线基线的影响 | `HANDOFF.md` §9.3；`PAUSE_STATE_20261113.md` §5 | **用户裁决**；本卡未触碰、未卸载。真实目标上的「逐字节还原」因此从未演示 | 用户 / Lead |
| U15 | **`ra2md.csf` 未纳入 `package_files()` / 备份 / 卸载**；真机确认覆盖规则后的安装策略卡 | `W30\UNCOVERED.md` §2；`CSF_CAPABILITY.md:68-69` | S2 契约 + S3 用例；须同步 digest / seal / 清单 / 卸载 | S2 → S3 |
| U16 | **MAPSELMD whole-file 的合法覆盖路径**：foreign 文件 definite conflict 永不释放、多包并存不支持、`--mapselmd-base` 硬编码校验官方 14 阶段 | `W34\UNCOVERED.md` U6 | S2 的 feature-set 契约覆盖；若需支持第三方 / 其它语言，须另设计「合并式追加」 | S2 / S3 |
| U17 | **`verify` 内容级校验**：MAPSELMD 官方 14 阶段仍在 / 追加键连续 / 末段无子项；CSF 官方 5,211 标签完整性 —— 只在构建时自检，安装后不验 | `W34\UNCOVERED.md` U7 | S3 新增 verify 规则（不得削弱既有语义与 51 例） | S3 |
| U18 | **非 Windows、`WinError 32` 句柄锁、`SIGINT` / 自定义异常、`_uninstall_legacy()` 部分子分支、`backup="keep"` 槽语义、`changed` 孤儿非 strict 分支** | `W26\UNCOVERED.md` §1-§5；`W21\UNCOVERED.md` §2/§4/§7 | S3 补用例设计；本卡未实测 | S3 |
| U19 | **`ra2opt` 侧 `restore`「完整回滚」从未实测**；`apply` 身份门未接；遥测零实现 | `FINAL_RULING.md` §4 第 2/3 条；`PROGRESS.md` §目标 A | S1 盘点 + S3 设计离线 `restore_roundtrip` 复跑（含真实 OS 失败注入） | S1 / S3 |
| U20 | **独立开关的「命中 / 成本 / 失败」记录格式、per-feature 遥测、统一默认关注册表** | RE-N09 L283；`PROJECT_DIRECTION.md` L38；`cli.py` 现有旗标均为事务级 | S2 契约定稿；本卡未给 schema、未估代码量 | S2 |
| U21 | **改动量 / 工期**：切片成本只给「工作单元」级粗估，未做代码级估算 | 本卡只出方案、不写代码 | 各执行卡在动工前自行估算并记入 `RUNLOG.md` | 各执行卡 |

## 4 · 本卡自身的隔离自证（已做 / 未做）

**已做** `[本次实测]`：

- 只读枚举 / 读取：`NEXT_RE_TASKS_20261112.md`、`PROJECT_DIRECTION.md`、`HANDOFF.md`、`PAUSE_STATE_20261113.md`、A/C 线 3 份 Lead 判定、W21/W23/W24/W25/W26/W30/W34 的报告与 `out\SUMMARY.txt`、`ra2forge\`（基线）与 v10/v11 的 `install.py` / `cli.py` / `builder.py` / `design.py` / `__init__.py`、`ra2opt\__init__.py` / `game.py` / `optimize.py`、W35 目录清单。
- 唯一写操作：创建 `lead\next_re_20261112_r02\W36_b_line_kickoff\` 并写入 `B_LINE_PLAN.md` / `DISAGREE.md` / `UNCOVERED.md` 三个 Markdown 文件。

**未做** `[待运行验证]` / 纪律约束：

- 收尾执行了**一次**只读 `git status --porcelain -- ra2forge/ ra2youli/ lead/next_re_20261112_r02/W36_b_line_kickoff/`，输出仅 `?? lead/next_re_20261112_r02/W36_b_line_kickoff/`（即 `ra2forge/`、`ra2youli/` 无改动、W36 为唯一新增未跟踪目录）。但**未做「开工前 / 收尾后」两次快照的前后比对自证**；S1 验收项已要求后续卡补完整的前后比对。本卡 `git` 全程只读、未调用任何 git 写操作。
- 未对 `ra2forge\` / `ra2youli\` / `W21`–`W35` 做任何写操作，也未启动任何游戏进程、未 attach、未读活进程内存。
- 未复核 `W35_mapselmd_live\out\` 产物内容（见 U4）。
- 未验证本卡引用的 `file:line` 在其它工作树/分支上是否漂移；引用均基于当前盘面 `main@3872ef6` 附近的本地只读副本（`W26\UNSEAL_FIX.md:4` `[转引]`）。

## 5 · 给下一卡（S1）的最小输入清单

1. 本卡 `B_LINE_PLAN.md` §2（现状表）与 §3.1（版本守卫判定 + 五判据表 + 推荐组合 + `UNKNOWN` 处理）。
2. 本卡 `DISAGREE.md` D1–D10（不得继承的旧前提）。
3. 本卡 `B_LINE_PLAN.md` §4 的 S1 五条验收检查（可直接当 S1 的通过条件）。
4. 需 S1 自己补的：`BASELINE.json` 实算哈希（U2）、`ra2opt` 逐写入口 `file:line`（U5）、`git status --porcelain` 前后自证（§4）。
