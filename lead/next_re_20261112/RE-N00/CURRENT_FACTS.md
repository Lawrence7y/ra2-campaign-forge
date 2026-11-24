# RE-N00 · 本轮事实底账（CURRENT_FACTS.md）

- run_id：`NEXT_RE_20261112_R01`
- 生成时刻：UTC `2026-11-12T07:33:07.582983+00:00` / Asia/Shanghai `2026-11-12T15:33:07.582983+08:00`
- 生成器：`lead/next_re_20261112/RE-N00/_baseline.py`（一条命令重建 BASELINE.json / INPUTS.tsv / CURRENT_FACTS.md / RECONSTRUCT.md）
- git：`main` @ `3872ef6635bb8a24be6463f53a6c2f5439d1cdbd`，未提交改动 `291` 条（只读计数；本轮零 git 写操作）
- 本轮授权：真机发射 / 活进程采集 **未授权**（详见 §3）；未启动任何游戏、未 attach、未读活进程内存、未注入/挂起/转储/断点/taskkill。
- 证据等级只用五种：`[本次实测]` / `[本次读码]` / `[静态推断]` / `[转引]` / `[待运行验证]`；**每行必标，转引不升级为已证**。

## 0 · 本轮实测原始记录（命令 + 原始输出 + 退出码）

> 下表为本轮 `_baseline.py` 实跑并记录的只读命令；完整 stdout/stderr 在 `BASELINE.json → commands[]`，逐文件 git 判定在 `BASELINE.json → git_tracking_checks[]`。哈希由脚本内 `hashlib` 流式实算（并有独立 `Get-FileHash` / `python -c hashlib` 交叉记录），**无转引**。

| # | 标签 | 命令 | 退出码 | 原始输出 |
|---|---|---|---|---|
| #1 | PSVersion | pwsh -NoProfile -Command $PSVersionTable.PSVersion.ToString() | 0 | 7.6.10<br> |
| #2 | OS | pwsh -NoProfile -Command Get-CimInstance Win32_OperatingSystem \| Select-Object Caption,Version,BuildNumber,OSArchitecture \| Format-List | 0 | <br>Caption        : Microsoft Windows 11 专业版<br>Version        : 10.0.26200<br>BuildNumber    : 26200<br>OSArchitecture : 64 位<br><br> |
| #3 | CPU | pwsh -NoProfile -Command Get-CimInstance Win32_Processor \| Select-Object Name,NumberOfCores,NumberOfLogicalProcessors \| Format-List | 0 | <br>Name                      : AMD Ryzen 7 6800H with Radeon Graphics         <br>NumberOfCores             : 8<br>NumberOfLogicalProcessors : 16<br><br> |
| #4 | ini-list | pwsh -NoProfile -Command Get-ChildItem -Path 'D:\Project\ra2-campaign-forge\ra2youli' -Filter '*.ini' -File \| Select-Object -ExpandProperty Name | 0 | BATTLEMD.INI<br>BATTLEMD98.INI<br>ddraw.ini<br>ra2.ini<br>RA2MD.INI<br>ra2render.ini<br>Register.ini<br> |
| #5 | toolchain-versions | C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe -c import platform,capstone,pefile,sys;print('python',platform.python_version());print('capstone',capstone.__version__);print('pefile',pefile.__version__);print('exe',sys.executable) | 0 | python 3.12.10<br>capstone 5.0.7<br>pefile 2024.8.26<br>exe C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe<br> |
| #6 | git-branch | git -C D:\Project\ra2-campaign-forge rev-parse --abbrev-ref HEAD | 0 | main<br> |
| #7 | git-HEAD | git -C D:\Project\ra2-campaign-forge rev-parse HEAD | 0 | 3872ef6635bb8a24be6463f53a6c2f5439d1cdbd<br> |
| #8 | git-status | git -C D:\Project\ra2-campaign-forge status --porcelain | 0 |  M lead/GOAL_THREE_TARGETS_20261018.md<br> M lead/PENDING_DECISIONS.md<br> M lead/ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md<br>?? .asar-dump/<br>?? .tmp/<br>?? GLM<br>?? Qwen<br>?? "Step\343\200\202\357\200\252\357\200\252dfmodel=DeepSeek"<br>?? _tmp_pending_new.md<br>?? asarpeek.cjs<br>?? docs/re/NEXT_RE_TASKS_20261112.md<br>?? import-smoke.mjs<br>?? lead/_routing_policy/<br>?? lead/a_class_fix_2026… …(完整 291 行原始输出见 BASELINE.json → commands[git-status].stdout) |
| #9 | Get-FileHash-exe-pair | pwsh -NoProfile -Command Get-FileHash -LiteralPath 'D:\Project\ra2-campaign-forge\ra2bench\gamemd.exe','D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe' -Algorithm SHA256 \| Format-Table -AutoSize Path,Hash | 0 | <br>Path                                              Hash<br>----                                              ----<br>D:\Project\ra2-campaign-forge\ra2bench\gamemd.exe 73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476<br>D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe 73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476<br><br> |
| #10 | hashlib-table | C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe -c import hashlib,pathlib; r=pathlib.Path(r'D:\Project\ra2-campaign-forge'); fs=['ra2bench/gamemd.exe', 'ra2youli/gamemd.exe', 'ra2youli/ddraw.dll', 'lead/re_d13_ruling_20261112/_run_hl_… | 0 | ra2bench/gamemd.exe 4825360 73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476<br>ra2youli/gamemd.exe 4825360 73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476<br>ra2youli/ddraw.dll 411648 85e0f7d530dfda134793a57cb3e76b0287dcc96892ee57162dd68f47283b03a9<br>lead/re_d13_ruling_20261112/_run_hl_match.py 15949 33bb2f61a7696e51eed979452f3d6d86859ebcb1d8322f348ff04bdb0ffa9426<br>lead/re_d13_ruling_20261112/e3_stack_sampler_candidate.py 55720 98210b4af460a75746913e35c791147982ec9d492349c9ace275ec817d51840a<br>lead/qc161_u0400_trip/_drive_c2_x_probe_v2.py 48630 6afe2711136c3b52344cd435f6dbd64508378a1e019c552228ff4f5e653d13b9<br>lead/qc161_u0400_trip/_drive_c2_x_earlyclose.py 9061 2e970eec43fe37ff02cab98e71bce9c764d11d758ab2a7b31b495100d109c2e1<br> |
| #11 | git-ls-files-per-input | git ls-files --error-unmatch -- <relpath>  (executed once per input, 40 times) | n/a (per-call exit codes in git_tracking_checks[]) | rc=1 ra2bench/gamemd.exe<br>rc=1 ra2youli/gamemd.exe<br>rc=1 ra2youli/ddraw.dll<br>rc=1 ra2youli/ddraw.ini<br>rc=1 ra2youli/RA2MD.INI<br>rc=1 ra2youli/ra2md.ini<br>rc=1 ra2youli/RA2MD.INI.benchbak<br>rc=1 ra2youli/ddraw.ini.benchbak<br>rc=1 ra2youli/BATTLEMD.INI<br>rc=1 ra2youli/BATTLEMD.INI.ra2forg… …(完整 40 行见 BASELINE.json → git_tracking_checks[]) |

## 1 · 三栏事实底账（可直接复用 / 需要条件 / 未证）

### 1.1 可直接复用

| 事实 | 证据指针 | 等级 | 下一步 |
|---|---|---|---|
| `ra2bench/gamemd.exe` 与 `ra2youli/gamemd.exe` 字节完全相同（同 sha256 `73201cc0…f67476`、同 4,825,360 B），属同一构建的同一份字节。 | `BASELINE.json → inputs[analysis_gamemd_exe]` / `inputs[game_gamemd_exe]`；命令#9(Get-FileHash-exe-pair, exit=0)；`lead/GOAL_THREE_TARGETS_20261018.md:9851` | `[本次实测]` | 静态分析可任选其一；但「原版对照」仍需来源证明。 |
| §2.2 五条声称哈希本轮逐项实算 **5/5 match**；两份冻结母本 **2/2 match**；§610 靶件 sha/字节也 MATCH。 | `BASELINE.json → verification`；`docs/re/NEXT_RE_TASKS_20261112.md:81-87`；命令#10(hashlib-table, exit=0) | `[本次实测]` | 每次执行前重跑 `_baseline.py`；输入漂移会自动变 mismatch。 |
| 本轮工具链：python 3.12.10 / capstone 5.0.7 / pefile 2024.8.26 / PowerShell 7.6.10；OS Microsoft Windows 11 专业版 10.0.26200 (64 位)；CPU AMD Ryzen 7 6800H with Radeon Graphics，物理核 8 / 逻辑 16。 | 命令#5(toolchain-versions, exit=0)；命令#2(OS, exit=0)；命令#3(CPU, exit=0)；命令#1(PSVersion, exit=0)（`BASELINE.json → host/toolchain`） | `[本次实测]` | 换机重跑脚本并把版本差异登记到本表。 |
| git 分支 `main`、HEAD `3872ef6635bb8a24be6463f53a6c2f5439d1cdbd`、未提交改动 `291` 条（生成时点值；含他人并行工作及本轮输出根目录 `?? lead/next_re_20261112/`）；本轮未执行任何 git 写操作。 | 命令#6(git-branch, exit=0)；命令#7(git-HEAD, exit=0)；命令#8(git-status, exit=0) | `[本次实测]` | 若他人改动输入，立即重算 sha 并按任务书 §4.3 停批。 |
| `ra2youli\*.ini` 实见 7 个目录条目，另有 3 个 `.bak/.benchbak` 备份；`ra2youli/ra2md.ini` 不是独立条目（Windows 大小写不敏感，解析到 `RA2MD.INI`）。 | 命令#4(ini-list, exit=0)；`BASELINE.json → ini_directory_entries / path_alias_checks` | `[本次实测]` | 真机趟前为这些可写 ini 保存启动前副本（本轮无真机，未做）。 |
| `RA2MD.INI.benchbak` 与当前 `RA2MD.INI` 字节完全相同（同 sha `c91c6a47…cd3c27d`、同 1,754 B），仅 mtime 不同；`ddraw.ini.benchbak` 与 `ddraw.ini` 不同（14,352 vs 14,782 B）。 | `BASELINE.json → inputs[game_ini_ra2md_benchbak] / inputs[game_ini_ra2md] / identical_hash_groups`；`INPUTS.tsv` | `[本次实测]` | 该 `.benchbak` **不是**独立的更老基线；真机趟不得用它替代本轮启动前副本后宣称逐字节恢复（任务书 §3 第 0 步第 4 项）。 |
| 主台账 §610 已定位且结构与任务书描述一致：A 18 / B 3 / C 8。 | `lead/GOAL_THREE_TARGETS_20261018.md:9848`（A :9860-9877；B :9883-9885；C :9889-9896）；`BASELINE.json → ledger_610` | `[本次读码]` | 引用一律用条目号；C 节不得随附表升格。 |
| `ra2bench/gamemd.exe` 的 VA `0x54A56E` 文件偏移 `0x14a56e` 处 7 字节 `c7 46 04 00 00 00 00`、VA `0x54A577` 处 `89 7e 04`，与 §610-A08/A09 的字节读数一致。 | `BASELINE.json → static_checks.a08_a09`；§610-A08/A09 见 `GOAL_THREE_TARGETS_20261018.md:9867-9868` | `[本次实测]` | 仅作为字节读数使用；不扩展为运行期结论。 |
| 上述两组字节的 capstone 解码为 `mov dword ptr [esi + 4], 0` / `mov dword ptr [esi + 4], edi`（VA/RVA/文件偏移已给出）。 | `BASELINE.json → static_checks.a08_a09.decoder` | `[静态推断]` | 需函数边界与上游调用链才能扩展为 CFG 结论。 |
| `[8]试验地_Pro_ProvingGrounds.yrm` 内 `[Basic] Name=[8] Proving Grounds`（文件偏移 `44355`，段偏移 `44346`），sha256 `3e3c874572bc02199cddce05b3633888caf968e6fbb457e763fb70b9fbfd5b19`、175361 B。 | `BASELINE.json → map_search.yrm_candidate / content_hits` | `[本次实测]` | 需证明该散装 `.yrm` 即当趟游戏加载载体（选图索引/文件身份）。 |
| D-13 候选件存在且含 `--live` 入口（本轮未执行）；离线单测输出 `:17-21` 自述「真机发射 / 活进程采集未获授权」。 | `lead/re_d13_ruling_20261112/e3_stack_sampler_candidate.py:1026-1037`；`lead/re_d13_ruling_20261112/_selftest_out.txt:17-21` | `[本次读码]` | 候选件与实测报告分栏引用，不能互相顶替。 |
| 全部必需输入当前均 `exists=true`，字节数/sha256/mtime 已固定；无一项被本工作包保存字节副本。 | `BASELINE.json → inputs[]`（40 项）；`INPUTS.tsv` | `[本次实测]` | 见 `RECONSTRUCT.md`：输入只能靠路径+哈希引用。 |

### 1.2 需要条件

| 事实 | 证据指针 | 等级 | 下一步 |
|---|---|---|---|
| §610 A 节 18 条字节级读数可复用，但条件是靶件 sha 仍为 `73201cc0…f67476` 且按 `sf/cw/ps/oo/md/ld` 六个证据目录重跑探针。 | `lead/GOAL_THREE_TARGETS_20261018.md:9852,9856-9877`；§5 逐条表 | `[转引]` | RE-N11 归位时六探针逐条对拍；本轮未重跑。 |
| §610 B 节 3 条 CFG 结论为静态推断，台账自标「未做运行期确认」。 | `lead/GOAL_THREE_TARGETS_20261018.md:9879-9885,9909` | `[转引]` | 需可信指令边界 + 运行期确认；不得写成已证。 |
| 3493 采样 / 1 事件 / 帧 349→15042 / 229 s 零Δ段 / 栈 7 帧，是既有实测结果，不是本轮实测。 | `lead/re_d13_ruling_20261112/STALL_CAPTURE_FINAL.md:58-94`；`_hl_match_14412.json:9,11-23`；§4 逐条分级 | `[转引]` | 需全量 samples 落盘后离线重算（RE-N01）。 |
| D-13 候选件离线单测（`_selftest_out.txt`，全部 Win32 经 stub）只证明 stub 路径，不证明 Win32 行为或「≤50 ms 硬超时」。 | `lead/re_d13_ruling_20261112/_selftest_out.txt:2-30`；`docs/re/NEXT_RE_TASKS_20261112.md:128` | `[转引]` | 补有区分力的离线测试 + 合成线程校准，再谈仪器。 |
| `[8] Proving Grounds` 的散装 `.yrm` 候选是否与当趟实际加载图为同一输入，需进图身份证据；`.map`/`.mpr` 未定位。 | `BASELINE.json → map_search.verdict`；`STALL_CAPTURE_FINAL.md:60`；`_maplist_full.txt:271` | `[待运行验证]` | RE-N03：解析 MIX 索引或保存实际加载文件字节 + 选图索引证据。 |
| 真机项（RE-N01 校准、RE-N02 状态校准、RE-N04 三臂基线、RE-N06 对照趟、RE-N08 新鲜性趟）依赖当轮明示授权 + 明确写域 + 启动前配置副本。 | `docs/re/NEXT_RE_TASKS_20261112.md:339-348`；`lead/PENDING_DECISIONS.md:65,68` | `[待运行验证]` | 标「待执行」；授权前不预写结果、不发射。 |

### 1.3 未证

| 事实 | 证据指针 | 等级 | 下一步 |
|---|---|---|---|
| `ra2bench/gamemd.exe` 是否「官方未修改原版」——本轮没有任何来源证明（发行介质/签名/构建记录/供应链）。 | `docs/re/NEXT_RE_TASKS_20261112.md:89`（自述「不能只凭游戏名视作官方未修改原版」）；无来源材料 | `[转引]` | Lead 提供来源证明；无则继续标未证，不得当原版对照臂。 |
| §610 C 节 8 项待证全部维持【未证】（台账仅给前 4 项编号 §610-C01…C04；第 5–8 项台账未编号，本包不代拟条目号），含「无别名逃逸」等全称否定。 | `lead/GOAL_THREE_TARGETS_20261018.md:9887-9896,9853,9909`；§5 逐条表 | `[转引]` | 运行期/普查补证；零真机铁律下不可得。 |
| `[8] Proving Grounds` 的 `.map`/`.mpr` 字节载体：未定位（MIX 索引未解析，散装仅 `.yrm` 候选）。 | `BASELINE.json → map_search` | `[待运行验证]` | MIX 索引解析 + 进图身份核对；找不到就保持「未定位」。 |
| 授权台账与四份回执/代码 docstring 的冲突 **未裁**。 | §3 全文 | `[转引]` | 建议 Lead 立新待裁条目（见 §3 结论）。 |
| 229 s 段被报告自认为「由三个数字自洽推出的强推断，不是逐样本复核过的已证」；JSON 未保存完整 3493 个样本序列。 | `lead/re_d13_ruling_20261112/STALL_CAPTURE_FINAL.md:85-94` | `[转引]` | 全量序列落盘再重算；本轮不得升级。 |
| 双份 exe 相同 ≠ 原版对照臂有效；旧独立评审绑定的哈希不能自动覆盖当前候选件/驱动脚本。 | `docs/re/NEXT_RE_TASKS_20261112.md:89,173` | `[转引]` | 三臂设计前先做来源确认；每张卡重新绑定指纹。 |
| 帧号 `0xA8ED84` 的每 tick 写者、线程归属、生命周期、相邻 `0xA8ED80` 字段宽度。 | `docs/re/NEXT_RE_TASKS_20261112.md:46,71-73,136-145`；`lead/re_d13_ruling_20261112/STATIC_FRAME_SEMANTICS.md:1-16` | `[待运行验证]` | RE-N02 从可信指令边界重验写点。 |

## 2 · 输入指纹与镜像身份

| 事实 | 证据指针 | 等级 | 下一步 |
|---|---|---|---|
| 两份 `gamemd.exe` sha/字节完全相同 ⇒ 本次实测的「同一构建」。 | `BASELINE.json → inputs`；命令#9(Get-FileHash-exe-pair, exit=0)；命令#10(hashlib-table, exit=0) | `[本次实测]` | 结论仅限「字节相同」，不外推到来源/版本官方性。 |
| 分析镜像 `ra2bench/gamemd.exe` 的「官方未修改原版」身份：**未证**，本轮无来源证明。 | `docs/re/NEXT_RE_TASKS_20261112.md:89`；`BASELINE.json → verification.ledger_610_target`（仅证明与 §610 靶件指纹一致） | `[转引]` | 补发行介质/数字签名/构建记录来源链；无则三臂对照不得称「纯原版」。 |
| §2.2 五条声称哈希逐项比对（2026-11-12 早些时候值 vs 本轮实算）： | `docs/re/NEXT_RE_TASKS_20261112.md:79-87`；`BASELINE.json → verification.doc_2_2` | `[本次实测]` | 逐项结果如下；以后每次执行前重算。 |

| 对象 | doc_claim | actual（本轮实算） | match | 证据指针 | 等级 |
|---|---|---|---|---|---|
| 分析用 gamemd.exe | `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476` | `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476` | **match** | `docs/re/NEXT_RE_TASKS_20261112.md:83` | `[本次实测]` |
| 游戏目录 gamemd.exe | `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476` | `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476` | **match** | `docs/re/NEXT_RE_TASKS_20261112.md:84` | `[本次实测]` |
| 当前 ddraw.dll | `85e0f7d530dfda134793a57cb3e76b0287dcc96892ee57162dd68f47283b03a9` | `85e0f7d530dfda134793a57cb3e76b0287dcc96892ee57162dd68f47283b03a9` | **match** | `docs/re/NEXT_RE_TASKS_20261112.md:85` | `[本次实测]` |
| 运行脚本 | `33bb2f61a7696e51eed979452f3d6d86859ebcb1d8322f348ff04bdb0ffa9426` | `33bb2f61a7696e51eed979452f3d6d86859ebcb1d8322f348ff04bdb0ffa9426` | **match** | `docs/re/NEXT_RE_TASKS_20261112.md:86` | `[本次实测]` |
| 采样候选件 | `98210b4af460a75746913e35c791147982ec9d492349c9ace275ec817d51840a` | `98210b4af460a75746913e35c791147982ec9d492349c9ace275ec817d51840a` | **match** | `docs/re/NEXT_RE_TASKS_20261112.md:87` | `[本次实测]` |

| 冻结母本 | 期望 sha（任务卡） | actual（本轮实算） | match | 证据指针 | 等级 |
|---|---|---|---|---|---|
| `lead/qc161_u0400_trip/_drive_c2_x_probe_v2.py` | `6afe2711136c3b52344cd435f6dbd64508378a1e019c552228ff4f5e653d13b9` | `6afe2711136c3b52344cd435f6dbd64508378a1e019c552228ff4f5e653d13b9` | **match** | RE-N00 任务卡（期望值）；`INPUTS.tsv` | `[本次实测]` |
| `lead/qc161_u0400_trip/_drive_c2_x_earlyclose.py` | `2e970eec43fe37ff02cab98e71bce9c764d11d758ab2a7b31b495100d109c2e1` | `2e970eec43fe37ff02cab98e71bce9c764d11d758ab2a7b31b495100d109c2e1` | **match** | RE-N00 任务卡（期望值）；`INPUTS.tsv` | `[本次实测]` |

> §610 靶件行（`lead/GOAL_THREE_TARGETS_20261018.md:9851`）声称 `4,825,360 B` / `73201cc0…f67476`，本轮实算 bytes=4825360 / sha=73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476 ⇒ sha match=True、bytes match=True。`[本次实测]`

## 3 · 授权状态（本轮）

**3.1 授权台账 D-13（2026-11-12）段原文（`[本次读码]`，逐字引用）：**

> `lead/PENDING_DECISIONS.md:22-23`：
> 「**D-13 已裁决（2026-11-12，用户当轮明示「D 13 选 c」）：见「已裁决记录」段。**
> **★ 本次裁决只解除「编写候选件 + 离线单测」的禁令**；**真机发射 / 活进程采集仍未授权**，按 D-15 与 D-31 Q4 须**当轮明示**，不得由本条或既有裁决代授。」
>
> `lead/PENDING_DECISIONS.md:61-65,68`（已裁决记录，逐字引用关键行）：
> 「- **D-13 已裁决（2026-11-12）：用户当轮明示「D 13 选 c」⇒ 选 (C)。**」（:61）
> 「2. **结论**：走**甲案 `SuspendThread` + `GetThreadContext` + `StackWalk64`**（≤50 ms/次）尝试覆盖短停主体。」（:62）
> 「1. **已解除**：D-31 Q4 曾判「**不批准**以『只编写候选件 + 离线单测』放行采样代码」——用户本次明示选择 C，构成对该禁令的**明确改变**，故**编写 SuspendThread/StackWalk 候选件 + 离线单测**现已获授权。」（:64）
> 「2. **未解除**：**真机发射 / 活进程采集 / attach / 读活进程内存**仍未授权。依据 D-15 已裁决原文「未经用户明示授权的 E3/MiniDump/SuspendThread/StackWalk/**真机发射/活进程采集**一律不得执行」与 D-31 Q4「真机/活进程须**当轮明示**」，用户本轮只说「选 c / 继续」，**未**就真机发射明示 ⇒ 仍不执行。」（:65）
> 「5. **仍待用户另行明示**：真机发射批次、以及是否接受「C 案死锁风险可能污染②读数」这一代价。」（:68）

**3.2 冲突陈述（全部 `[转引]`，不得升级为已证）：**

| 出处 | 原文要点 | 等级 |
|---|---|---|
| `lead/re_d13_ruling_20261112/WOW64_RECEIPT.md:4` | 「前置授权：用户 2026-11-12 明示「D 13 选 c」+「**统一真机以及一切操作，可以上传GitHub**」」 | `[转引]` |
| `lead/re_d13_ruling_20261112/RULING_RECEIPT_611.md:129` | 「## 6 · 真机验证（用户 2026-11-12 授权「**统一真机以及一切操作**」后执行）」 | `[转引]` |
| `lead/re_d13_ruling_20261112/FRAMESOURCE_RECEIPT.md:4` | 「前置授权：**真机 + 一切操作（2026-11-12）**」 | `[转引]` |
| `lead/re_d13_ruling_20261112/e3_stack_sampler_candidate.py:1030` | docstring：「`--live` 入口：**真机采集**（用户 2026-11-12 授权「**统一真机以及一切操作**」）」 | `[转引]` |
| `lead/re_d13_ruling_20261112/STACKWALK_RECEIPT.md:4`（补充登记） | 「前置：**真机已授权**」 | `[转引]` |
| `lead/re_d13_ruling_20261112/_selftest_out.txt:17-21`（同目录内的反向陈述） | 「!! 拒绝执行：**真机发射 / 活进程采集未获授权**……用户 2026-11-12 仅明示「D-13 选 c」……本件因此只提供 --selftest」 | `[转引]` |

| 事实 | 证据指针 | 等级 | 下一步 |
|---|---|---|---|
| 台账与回执、`--live` docstring、离线单测输出之间存在 **同一日期、互相矛盾的授权陈述**；本轮未见用户原始会话记录，无法裁定。 | 上表六处；`docs/re/NEXT_RE_TASKS_20261112.md:348`（「后续实测报告不能自动替代授权记录」） | `[转引]` | 建议 Lead **立新待裁条目**：请用户当轮明示「统一真机以及一切操作」是否成立、生效时点、批次与写域。 |
| 本轮授权状态结论（任务卡要求的固定措辞）。 | `lead/PENDING_DECISIONS.md:22-23,61-65` + 本卡授权边界铁律 | `[转引]` | 按结论执行，不因回执自行放宽。 |

> **结论（逐字）**：授权台账（PENDING_DECISIONS）为唯一口径，回执属转引；两者冲突**未裁**；故本轮按『真机未授权』执行，所有真机项标 `[待运行验证] / 待执行`。

建议 Lead 立新待裁条目，把「2026-11-12 是否确有『统一真机以及一切操作』明示、其生效时点/批次/写域、以及回执与台账冲突如何归档」单列裁决。

| 事实 | 证据指针 | 等级 | 下一步 |
|---|---|---|---|
| 本轮所有真机项（游戏发射、attach、ReadProcessMemory、SuspendThread/ResumeThread、StackWalk64、MiniDump、断点/注入、taskkill、部署）= 待执行，未执行。 | 本卡「授权边界（铁律）」第 1–2 条；`docs/re/NEXT_RE_TASKS_20261112.md:339-348` | `[待运行验证]` | 获当轮明示授权且写域明确后另立批次；本包只做离线只读。 |

## 4 · 既有实测结果的分级（逐条 `[转引]`）

> 以下 5 条全部来自 `lead/re_d13_ruling_20261112/` 的历史运行结果，本轮**未重放、未启动游戏**；按任务卡要求逐条标 `[转引]`，并指出报告自认的「强推断非已证」。

| 事实 | 证据指针 | 等级 | 下一步 |
|---|---|---|---|
| 3493 次采样、可读 3493 次（100%）。 | `lead/re_d13_ruling_20261112/_hl_match_14412.json:9-10`；`STALL_CAPTURE_FINAL.md:65` | `[转引]` | RE-N01 全量 NDJSON 落盘后可离线复算。 |
| 停滞事件 = 1（`events` 数组 1 项，t=471.266 s、frame=15042、mode=single_thread、paused_ms=0.0、errors=null）。 | `lead/re_d13_ruling_20261112/_hl_match_14412.json:11-18`；`STALL_CAPTURE_FINAL.md:68,74` | `[转引]` | `errors:null` 不能替代恢复状态核验（任务书 §2.1 缺口一）。 |
| 帧号 349 → 15042（Δ 中位 6 ⇒ 报告写 30.0 fps）。 | `lead/re_d13_ruling_20261112/STALL_CAPTURE_FINAL.md:64-68` | `[转引]` | 需逐帧边沿时间戳；0.2 s 轮询不得算伪逐帧 P95/P99（任务书 §3 RE-N04）。 |
| 零Δ段 1 个、最长 229.00 s（`700 − 471.27 = 228.7 ≈ 229`），报告据此称「永久冻结」。 | `lead/re_d13_ruling_20261112/STALL_CAPTURE_FINAL.md:67,85-90` | `[转引]` | **报告自认 `:92-94`：这是【强推断】不是【已证】，JSON 未保存完整 3493 个样本序列**；需全量落盘重算。 |
| 栈 7 帧：`ntdll+0x7858c` → `KERNELBASE×2` → `gamemd.exe+0x207f17` → `USER32+0x74775` → `USER32+0x3505d` → `gamemd.exe+0x20833f`。 | `lead/re_d13_ruling_20261112/_hl_match_14412.json:19-52`；`STALL_CAPTURE_FINAL.md:75-82,96-109` | `[转引]` | 两个栈签名不同只说明捕获路径不同，不能推出两条独立根因（`docs/re/NEXT_RE_TASKS_20261112.md:65`）；RE-N05 静态回溯。 |

## 5 · 主台账 §610 三栏导出

**定位结果：`[本次读码]` 已定位**（非「未定位」）：`lead/GOAL_THREE_TARGETS_20261018.md:9848` 标题即含「18 条字节级【已证】+ 3 条【已证（CFG）】+ 8 条待证」，A 节 `:9860-9877`（18 行）、B 节 `:9883-9885`（3 行）、C 节 `:9889-9896`（8 项），与任务书描述一致。`[转引]` 登记，本轮未重跑 `sf/cw/ps/oo/md/ld` 六探针（`:9852`、`:9909`），故全部条目不升级为本轮实测。定级口径见 `:9853`。

**实际搜索过的关键词与命中情况（`[本次实测]`，脚本重算「包含该关键词的行数」）：**

| 关键词 | 命中行数 |
|---|---|
| `§610` | 27 |
| `610` | 325 |
| `0x54A56E` | 0 |
| `slot2` | 5 |
| `18 条` | 2 |
| `3 条静态` | 0 |
| `8 项待证` | 0 |
| `三栏` | 0 |
| `0x54A4F0` | 5 |
| `0xAA1078` | 4 |
| `已证（CFG）` | 4 |

### 5.1 可直接复用（A 节 18 条字节级读数，`[转引]`）

| 条目号 | 读数（截短） | 证据指针 | 等级 | 下一步 |
|---|---|---|---|---|
| §610-A01 | .text 单次线性 disasm 于 fo 0x6F59D（VA 0x46F59D）截断，得 155,215 条（11.13%）；分块 0x10000 得 1,150,117 条；seg-e… | GOAL_THREE_TARGETS_20261018.md:9860；sf:L7-L11 | `[转引]` | 重跑六探针 sf:L7-L11 对拍；引用用条目号 |
| §610-A02 | 全 .text 直接 `call/jmp` 0x54A4F0 = 0、0x54A630 = 0；FF 15/25 绝对间接 = 0；全镜像 dword 位点 0x54A4F0={0x7ECC0… | GOAL_THREE_TARGETS_20261018.md:9861；sf:L13-L15 | `[转引]` | 重跑六探针 sf:L13-L15 对拍；引用用条目号 |
| §610-A03 | 全镜像 dword==0x54A4F0 恰 1 处（0x7ECC04 = vtable 0x7ECBFC slot2）；dword==0x54A630 恰 1 处（0x7ECBE4 = vta… | GOAL_THREE_TARGETS_20261018.md:9862；sf:L18-L19 | `[转引]` | 重跑六探针 sf:L18-L19 对拍；引用用条目号 |
| §610-A04 | 对 slot2 单元的 call/jmp [单元]/A1/8B/89/SIB-abs 装载或复制全编码 = 0 | GOAL_THREE_TARGETS_20261018.md:9863；sf:L20 | `[转引]` | 重跑六探针 sf:L20 对拍；引用用条目号 |
| §610-A05 | 0x546069 处字节 `FF 50 08` = `call dword ptr [eax+8]`；0x54605F `mov eax,[0xAA1078]`；0x546064 `mov e… | GOAL_THREE_TARGETS_20261018.md:9864；sf:L66-L68 | `[转引]` | 重跑六探针 sf:L66-L68 对拍；引用用条目号 |
| §610-A06 | `call/jmp [reg+8]` 普查：字节级 1716（call 1715 + jmp 1 + 异形 2 计法见源）、主流 seg-extend 1714；imm32/disp32 引用… | GOAL_THREE_TARGETS_20261018.md:9865；sf:L26-L29, L31-L35 | `[转引]` | 重跑六探针 sf:L26-L29, L31-L35 对拍；引用用条目号 |
| §610-A07 | c7 存储锚点：0x543E8D `mov dword [0xAA1078],0x7ECBDC`；0x543EBE `mov dword [0xAA1078],0x7ECBFC`；0x54A7… | GOAL_THREE_TARGETS_20261018.md:9866；sf:L21-L23 | `[转引]` | 重跑六探针 sf:L21-L23 对拍；引用用条目号 |
| §610-A08 | 0x0054A56E 指令 `C7 46 04 00 00 00 00` = `mov dword ptr [esi+4], 0` | GOAL_THREE_TARGETS_20261018.md:9867；cw:L66 | `[转引]` | 重跑六探针 cw:L66 对拍；引用用条目号 |
| §610-A09 | 0x0054A577 指令 `89 7E 04` = `mov dword ptr [esi+4], edi`；与 0x0054A56E 相距 9 字节；两指令间仅 `33C0 xor eax… | GOAL_THREE_TARGETS_20261018.md:9868；cw:L66-L68 | `[转引]` | 重跑六探针 cw:L66-L68 对拍；引用用条目号 |
| §610-A10 | XMP29U2.MAP（311,822 B，sha256 `0add791d…`）[Houses] 声明 14 house；含 `Country=` 的节恰 14 个，一一对应无多出节；14 … | GOAL_THREE_TARGETS_20261018.md:9869；oo:L6, L28-L46; 地图原文件 grep 14 处 `PlayerControl=no` | `[转引]` | 重跑六探针 oo:L6, L28-L46; 地图原文件 grep 14 … 对拍；引用用条目号 |
| §610-A11 | XMP29U2.MAP [Units]=3360、[Infantry]=2240，合计 5600；14 owner 各 400（240 车+160 步） | GOAL_THREE_TARGETS_20261018.md:9870；md:L17-L50; oo:L50-L52, L56-L82 | `[转引]` | 重跑六探针 md:L17-L50; oo:L50-L52, L56-L8… 对拍；引用用条目号 |
| §610-A12 | 大版 `ra2bench/[2]0LoadBench_U0400.yrm`（92,332 B，sha `cb5785a1…`）Units=240 Inf=160 Structures=41；R… | GOAL_THREE_TARGETS_20261018.md:9871；md:L54-L78; ld:L25-L28 | `[转引]` | 重跑六探针 md:L54-L78; ld:L25-L28 对拍；引用用条目号 |
| §610-A13 | 小版 `out/loadbench/[2]0LoadBench_U0400.yrm`（25,604 B，sha `6027eb20…`）Units=240 Inf=160 Structures… | GOAL_THREE_TARGETS_20261018.md:9872；md:L81-L103; ld:L29-L31 | `[转引]` | 重跑六探针 md:L81-L103; ld:L29-L31 对拍；引用用条目号 |
| §610-A14 | 三份载体 size/sha/内容结构互异（另列 222,799 B / md5 `11ec8ff6` 变体）：熵 5.652 vs 4.699、首字节 `;` vs `[`、小节集 34 vs… | GOAL_THREE_TARGETS_20261018.md:9873；ld:L88-L103; md:L55, L82; oo:L6 | `[转引]` | 重跑六探针 ld:L88-L103; md:L55, L82; oo:L… 对拍；引用用条目号 |
| §610-A15 | 字符串 `PlayerControl` 全镜像恰 1 处 @0x824E28；.text 中 LE32==0x824E28 的 xref 2 处（0x500BBF、0x5012ED） | GOAL_THREE_TARGETS_20261018.md:9874；ps:L11, L32-L34 | `[转引]` | 重跑六探针 ps:L11, L32-L34 对拍；引用用条目号 |
| §610-A16 | 0x500BD6 `call 0x5295f0`；0x500BDB `test al,al`；0x500BDD `8883 ed010000` = `mov byte ptr [ebx+0x1… | GOAL_THREE_TARGETS_20261018.md:9875；ps:L113-L115 | `[转引]` | 重跑六探针 ps:L113-L115 对拍；引用用条目号 |
| §610-A17 | ctor 0x4F54A0 的 call 普查恰 8 处：0x500A30 / 0x500B19 / 0x59A198 / 0x687FC3 / 0x6881A0 / 0x6882FE / 0… | GOAL_THREE_TARGETS_20261018.md:9876；ps:L905 | `[转引]` | 重跑六探针 ps:L905 对拍；引用用条目号 |
| §610-A18 | 字符串 `PercentBuilt` 恰 1 处 @0x8189A0；全 .text 原始字节 `1c 57 00 00` 命中恰 3 处（0x401E00/0x674FC0/0x6750B0… | GOAL_THREE_TARGETS_20261018.md:9877；ps:L12, L36-L39, L894-L899 | `[转引]` | 重跑六探针 ps:L12, L36-L39, L894-L899 对拍；引用用条目号 |

> 本轮补做的一处独立字节核对（`[本次实测]` + `[静态推断]`）：§610-A08/A09 的 `c7 46 04 00 00 00 00` / `89 7e 04` 在 `ra2bench/gamemd.exe` 的 VA `0x54A56E`（RVA `0x14a56e`、文件偏移 `0x14a56e`）与 VA `0x54A577`（RVA `0x14a577`、文件偏移 `0x14a577`）读得，capstone 解码 `mov dword ptr [esi + 4], 0` / `mov dword ptr [esi + 4], edi`。仅支持字节读数，不替代 A 节其余 16 条的重跑。

### 5.2 需要条件（B 节 3 条静态 CFG 结论，`[转引]`）

| 条目号 | 静态推断（截短） | 证据指针 | 等级 | 下一步 |
|---|---|---|---|---|
| §610-B01 | 0x54A4F0 内静态 CFG：`test edi,edi`→若 edi==0 走 0x54A52C 弹栈提前返回、不达置零点；`test eax,eax`/`test al,al`→Vector==0 或 IsAll… | GOAL_THREE_TARGETS_20261018.md:9883；cw:L34-L66 | `[转引]` | 需可信指令边界 + 运行期确认；勿升为已证 |
| §610-B02 | 能指向 0x54A4F0/0x54A630 的 `call/jmp [reg+8]` 调用点全镜像唯一 = 0x546069（污点传播唯一消费者）；由此推「进入两函数必须经虚派发」。**C3 更正：原括注「无别名逃逸」已… | GOAL_THREE_TARGETS_20261018.md:9884；sf:L39-L47; sf:L20, L28, L40 | `[转引]` | 需可信指令边界 + 运行期确认；勿升为已证 |
| §610-B03 | PlayerControl 控制流影响：0x500BE3 `je 0x500C51`（no→跳过难度资金加成）；0x500ABF `je 0x500ad0`（战役循环选 Scen+0x60C/0x610 难度）；0x50… | GOAL_THREE_TARGETS_20261018.md:9885；ps:L116-L147, L589, L1183-L1214, L905; ps json verdict | `[转引]` | 需可信指令边界 + 运行期确认；勿升为已证 |

### 5.3 未证（C 节 8 项待证，`[转引]`）

> 台账 `:9889-9896` 仅给第 1–4 项显式编号 `§610-C01`…`§610-C04`；第 5–8 项**没有**条目号，本包按「C 节第 N 项（台账未编号）」如实登记，不代拟编号。

| 条目号 | 待证内容（截短） | 证据指针 | 等级 | 下一步 |
|---|---|---|---|---|
| §610-C01 | §610-C01【未证】0x543E70=「动态初始化器」、0x543EB0=「atexit 析构器」及其时序（常态 slot2→0x54A630、析构后→0x54A4F0）：缺 CRT 初始化表遍历与 atexit 注… | GOAL_THREE_TARGETS_20261018.md:9889 | `[转引]` | 运行期/普查补证；本轮零真机，标待证 |
| §610-C02 | §610-C02【未证】「函数指针值无法在运行期逃逸或复制到其它函数指针变量」：静态普查仅证无静态编码引用，运行期机制未证（sf:L20 由「全编码=0」跳到「无法运行期复制」）。 | GOAL_THREE_TARGETS_20261018.md:9890 | `[转引]` | 运行期/普查补证；本轮零真机，标待证 |
| §610-C03 | **§610-C03【未证】（C3 本修正版新增）「0xAA1078 无别名逃逸」**：CHAIN_SYNTHESIS.md L69 边界列原文「污点分析证明 0xAA1078 是全镜像唯一消费者，无别名逃逸」。该断言不… | GOAL_THREE_TARGETS_20261018.md:9891 | `[转引]` | 运行期/普查补证；本轮零真机，标待证 |
| §610-C04 | §610-C04【未证】（C4 拆出）`ps:L899-L900`「引擎无任何运行时读取点」：全称否定机制断言，非字节级读数；PercentBuilt 的普查计数仍按字节级收入 A 节，边界以 CHAIN_SYNTHES… | GOAL_THREE_TARGETS_20261018.md:9892 | `[转引]` | 运行期/普查补证；本轮零真机，标待证 |
| C 节第 5 项（台账未编号） | 【未证】（维持）0x0084F2BA 崩溃定谳：缺 MiniDump/调用栈，禁定 DEP 取指违规（CHAIN_SYNTHESIS.md:L74/L143 原标恰当）。 | GOAL_THREE_TARGETS_20261018.md:9893 | `[转引]` | 运行期/普查补证；本轮零真机，标待证 |
| C 节第 6 项（台账未编号） | 【未证】（维持）引擎运行期 HouseClass 实例数决定机制（L76/L146）。 | GOAL_THREE_TARGETS_20261018.md:9894 | `[转引]` | 运行期/普查补证；本轮零真机，标待证 |
| C 节第 7 项（台账未编号） | 【未验】（维持）PercentBuilt 经 BaseClass*/间接/动态偏移读点的全镜像普查（L84/L149）。 | GOAL_THREE_TARGETS_20261018.md:9895 | `[转引]` | 运行期/普查补证；本轮零真机，标待证 |
| C 节第 8 项（台账未编号） | 【未决】（维持）台账历史指纹 93c2974b 算法（L152）。 | GOAL_THREE_TARGETS_20261018.md:9896 | `[转引]` | 运行期/普查补证；本轮零真机，标待证 |

## 6 · D-13 候选件与后续实测报告分栏（不能互相顶替）

| 栏 | 内容 | 证据指针 | 等级 | 下一步 |
|---|---|---|---|---|
| **候选件 / 实现** | `e3_stack_sampler_candidate.py`（55,720 B，sha `98210b4a…d51840a`）、`e3_stackwalker.py`、`e3_framesource.py`、`_static_frame_semantics.py`、`_run_hl_match.py` 是代码；`--live` 入口定义于 `:1029-1037`，本轮未调用。 | `BASELINE.json → inputs[d13_*]`；`e3_stack_sampler_candidate.py:1026-1037` | `[本次读码]` | 引用实现必须带文件+sha；改动需另立候选副本。 |
| **离线单测** | `_selftest_out.txt` 记「E3 候选件离线单测（零真机 · 全部 Win32 经 stub）」及 `:17-21` 的拒绝真机陈述。 | `lead/re_d13_ruling_20261112/_selftest_out.txt:2-21`；`RULING_RECEIPT_611.md:123-125` | `[转引]` | 只证明 stub 路径；不能证明真机能力或 ≤50 ms 硬保证。 |
| **后续实测报告 / 运行结果** | `STALL_CAPTURE_FINAL.md`、`STALL_CAPTURE_SUCCESS.md`、`STATIC_FRAME_SEMANTICS.md`、四份 RECEIPT 及 `_hl_match_*.json`、`_battle_stack_sample.json` 是历史运行结果/回执（转引）。 | `BASELINE.json → inputs[d13_report_* / d13_event_*]`；`STALL_CAPTURE_FINAL.md:58-94` | `[转引]` | 不得用报告数量或「已跑过」替代授权或测量链可信度。 |
| **分栏结论** | 候选件是实现、离线单测是 stub 验证、实测报告是运行结果；三者互不等价，任一都不能顶替另一。 | `docs/re/NEXT_RE_TASKS_20261112.md:101,348`；`lead/PENDING_DECISIONS.md:63-65` | `[转引]` | 任务卡、验收、知识库均按三栏分别引用；RE-N01 需独立回放统计。 |

## 7 · 本轮工具链版本

| 工具 | 版本 | 证据指针 | 等级 | 下一步 |
|---|---|---|---|---|
| Python | 3.12.10 (3.12.10 (tags/v3.12.10:0cc8128, Apr  8 2025, 12:21:36) [MSC v.1943 64 bit (AMD64)]) | 命令#5(toolchain-versions, exit=0) | `[本次实测]` | 换机重跑 `python lead/next_re_20261112/RE-N00/_baseline.py`。 |
| capstone | 5.0.7 | 命令#5(toolchain-versions, exit=0)；`BASELINE.json → static_checks.a08_a09.decoder` | `[本次实测]` | 反汇编/解码结果须带 VA/RVA/文件偏移/字节。 |
| pefile | 2024.8.26 | 命令#5(toolchain-versions, exit=0)；`BASELINE.json → static_checks.pe_files` | `[本次实测]` | PE 节映射回读字节时记录 raw_offset。 |
| PowerShell | 7.6.10 (Core) | 命令#1(PSVersion, exit=0) | `[本次实测]` | 主机信息命令的原始输出见 §0。 |
| OS / CPU | Microsoft Windows 11 专业版 10.0.26200 (build 26200, 64 位)；AMD Ryzen 7 6800H with Radeon Graphics，物理核 8 / 逻辑 16 | 命令#2(OS, exit=0)；命令#3(CPU, exit=0) | `[本次实测]` | 与性能基线（RE-N04）固定机器条件一起登记。 |

## 未覆盖项

- 本轮按授权边界**未执行任何真机项**：未启动 `gamemd.exe`/`ra2loader`/`YURI.exe`，未 attach、未 ReadProcessMemory 活游戏进程、未 SuspendThread/ResumeThread/StackWalk64/MiniDump/断点/注入/部署/taskkill；RE-N01 校准趟、RE-N02 状态校准、RE-N04 三臂基线、RE-N06 对照趟、RE-N08 新鲜性趟全部未做。
- 未对 17 个 `.mix` 容器做索引解析（多数首 4 字节为 `00 00 02 00` / `00 00 03 00`，加密头需 Blowfish 密钥与格式确认）；只做了明文分块扫描（294 个文件 / 1944474219 B）。
- 未重跑 §610 的六个探针（`sf/cw/ps/oo/md/ld`）与 `:9907` 自认「自愿不做」的 24 个引用区间逐数复核；A 节 18 条中仅 A08/A09 做了本轮字节核对。
- 未为游戏可写 ini 保存启动前副本 / 退出后比较（任务书 §3 第 0 步第 4 项），因本轮无真机且写域只限 `RE-N00\`；也未生成任何输入字节副本（见 `RECONSTRUCT.md`）。
- 未解析 `_hl_match_*.json` 的全量样本序列（原 JSON 未保存，报告自认）；未复算 229 s 段。
- 未核对旧独立评审 `lead/re_d13_review_20261112/REVIEW.md:5` 绑定的另一哈希（不在必需输入清单；仅按任务书 `:89` 转引登记）。
- 未做两份 `gamemd.exe` 的数字签名 / 发行介质 / 构建记录核验；未做 `ddraw.dll+0x22B06` 的调用契约静态回溯。
- 未执行任何 git 写操作；未审阅 291 条未提交改动的内容（只计数，避免触碰他人工作）。

## 未知项

- `ra2bench/gamemd.exe` 的来源与「官方未修改原版」身份；以及 §610 六探针读数是否可在本机按同一口径完全复现。
- `[8] Proving Grounds` 的 `.map`/`.mpr` 字节载体是否位于某个 MIX 内；当趟游戏实际加载哪一份文件、以何索引选中。选图索引在既有材料中不一致：`_hl_match_14412.json:4-7`=265、`STALL_CAPTURE_SUCCESS.md:12`=268、`_maplist_full.txt:271`=269，原因未知。
- 用户 2026-11-12 是否确有「统一真机以及一切操作，可以上传GitHub」的当轮明示（原始会话记录不在本轮输入中）；台账与回执冲突如何裁定、生效时点与批次。
- 229 s 零Δ段的真实游戏状态（战斗 / 暂停 / 菜单 / 记分板 / 失焦 / 结束）、唤醒条件与观察器扰动。
- 帧号 `[0xA8ED84]` 的写点、更新线程、生命周期、相邻 `[0xA8ED80]` 字段宽度；窗口线程与逻辑线程关系。
- §610 C 节 8 项运行期机制、崩溃家族新鲜性与责任写者、DLC 引擎资源覆盖顺序。
- 他人未提交改动是否会在本轮之后修改这些输入；本包所有 sha 均为本时点值，重跑 `_baseline.py` 才能确认是否漂移。
- 真机授权何时、以何批次解除；解除后哪些历史输入仍可作为同版本对照。

---
*本文件由 `_baseline.py` 生成；所有数字均来自本轮实算或注明出处的转引，无来源的数字不写入。*
