# W72 · `UNKNOWNS.md` — 未覆盖 / 待验证 / 诚实缺口

> 执行者 Hy4（W72，非 Lead）。本文件只登记**本卡没有证明**的事，不把「未检出」包装成「已证否」。
> 与 `INPLACE_NONINTERFERENCE.md` §6「三条限制」互补：§6 是结论口径必须写的三条；本文件是全部登记项。

---

## U1 · 「写了不同内容」完全未测（最重要的缺口）

本卡的 inplace 改写是 `Scenario=SOV01umd.MAP` → `SOV01UMD.MAP`（大小写差异，引擎加载**同一张官方图**）。**没有**测过把 `Scenario` 指向另一张图（产品路线 W63/W70 三关链的实际用法）。W63/W70 证明的是「三关链能贯通」（功能），不是「A/B 行为分布等价」（本卡口径）。因此：

- 本卡 `SAME_DISTRIBUTION` **不能**外推到「inplace 改写任意 `Scenario` 内容都不扰动行为」。
- 若要覆盖，需另开卡：让 inplace 把 `[SOV1]` 指向一张**与官方字节等价但引擎确实不同**的图，同时让 A 臂也加载同一张图（否则两臂不同图，比较无效）——设计上比本卡更难。

## U2 · 「唯一自变量」是行为层面隔离，不是文件系统字节层面的绝对唯一

B 臂相对 A 臂多了 6 个文件：`BATTLEMD.INI.ra2forge.bak`、`W72M1.MAP`、`W72M2.MAP`、`expandmd98.mix`、`ra2forge_install.json`、`ra2forge_install.json.seal`。原因：`[本次读码]` v15 `builder.py:150-218` 对任何 design 都无条件编译 `*.MAP` 并写 `expandmd98.mix`，`install.package_files()` 也总把它们列入复制集。

- 本卡**没有**做「只含 `BATTLEMD.INI` 的极简 inplace 包」对照（删掉包内 maps/mix 可能触发 feature_set `shipped()` 与 plan/actual 对账不一致，风险未评估）。
- 缓解依据：包内地图是**惰性**的（`Scenario` 指向官方图，永不加载）；W65/W69 的 append B 臂也带了同类 `*.MAP` + `expandmd98.mix`，在同一观测量集合上已判 `SAME_DISTRIBUTION`。但这只是**间接**依据，不是本卡对「极简包」的实测。

## U3 · 观测量集合 / 场景 / 时长的边界

- 只在「官方苏联第一关、不动 UI、6 ms cadence × 75 s、n≈10,300 行/趟」下采样。
- 未覆盖：其它战役/场景、战役链推进（M1→M2→M3）、长时程与稀有偶发事件、UI 交互、`ui_controls` 非 `[0]` 的情形、存档/网络/音频/渲染等非本观测量集合、以及任何未被 RPM 读取的内部状态。
- `ui_controls` 四趟全程 `[0]` ⇒ `J_ui=1.0` 恒等，**UI 侧同样没有判别力**。FROZEN `jaccard_mean` 仍沿用 `min(len_a,len_b)` 逐行截断语义（`CRITERIA_SPEC_V2.md` §2.5 第 5 条自认遗留弱点），本卡未擅自改动。

## U4 · 离散侧退化之外的 V2 遗留弱点（转引，本卡未修正）

- `REVIEW\LEAD_VERIFY_W68B.md` §8 末段列：离散侧在本场景退化（TVD≡0/p≡1）；`N_disc` 只取 A 侧（B 侧更抖则判定带偏窄）；稀有值尾部未实测；灰区余量有限。
- `[本次读码]` 复核：权威 V2 工具 `tool_b_stats_v2.py:196-197` 的 `discrete_noise_band()` 实现为 `N_disc = max(TVD(A1,A2), TVD(B1,B2))`（**两臂取 max**），与 §8 那句「只取 A 侧」表述不一致。本卡按**工具实际输出**报告，不代为裁决哪一版表述为准；登记为待 Lead 裁项。
- 本卡 `max_N_disc=0.0`（五字段单值），无论取哪侧都不影响本次 B-1 判定，但不改变「离散侧无判别力」这一结论。

## U5 · `.bak` 是否被引擎的 `BATTLEMD*.INI` 枚举捕获

`[静态推断]` 备份名 `BATTLEMD.INI.ra2forge.bak` **不以 `.INI` 结尾**，不应被 `FindFirstFileA("BATTLEMD*.INI")` 枚举（W60 `INPLACE_MODE.md` §1.2 亦如此声明）。本卡**未反汇编复核**该枚举模式，也未单独做「只放一个 `.bak` 不改写 INI」的对照趟。间接证据：四趟 `battle_idx=1`、`map_name=SOV01UMD.MAP` 完全一致，未见入口级扰动。

## U6 · 大小写等价依赖 Windows 文件名语义

`SOV01umd.MAP` 与 `SOV01UMD.MAP` 的等价性建立在「Windows/引擎按文件名大小写不敏感匹配」之上（本卡四趟 `0x125C` 实测印证）。未在其它 OS、其它语言版本引擎、或其它大小写敏感路径上验证。若该前提不成立，两臂会同图失败，本卡已用逐行 `map_check` 硬断言把这种失败显式化为「比较无效」而非静默通过。

## U7 · 采集节奏与进图起点的实际漂移

- 名义 6 ms cadence；实测 ≈10,300 行 / 75 s ≈ 7.27 ms/采样（与 W69 同量级，循环含 RPM + EnumWindows + `time.sleep(0.006)`）。V2 工具**不使用 `t`**（只用 `frame` 差分），故不构成判定偏差，登记备查。
- 本卡进图耗时约 87 s（影片/简报阶段），W69 约 30 s 内；但四趟 `frame` 首值 47/48 与 W69 一致、`Δframe` 2343/2344 一致，采样窗口起点漂移未在本观测量上显出差异。原因未单独追查（按键重试时序/影片解码），登记为环境噪声。

## U8 · V2 工具自检的第一次失败（已修复，如实留痕）

冻结工具 `run_selftest()` 把合成 fixture 解析为「工具文件同目录 `EVIDENCE\ce_*`」，卡内副本目录无此 fixture ⇒ 第一次 `--selftest` exit 1（`FileNotFoundError`）。本卡把 W68 的 `ce_A/ce_B/ce_C` **NDJSON fixture 数据**（不是脚本）复制到 `work\criteria_frozen\EVIDENCE\` 后，用**同一份字节不变的冻结工具**重跑得 exit 0、`V2_SELFTEST_PASS=True`。`--compare` 走显式路径参数，与该自检失败**无关**（第一次即 exit 0）。两次尝试均记在 `out\compare_summary.json` 的 `selftest_attempts`，未删除失败日志 `out\cmd_tool_b_stats_v2_selftest.log`。

## U9 · `W ⊆ D` 的 `D` 由本卡内联镜像构造

`out\c_audit_declared.json` 由 `tools\w72_collect.py:build_declared()` 内联镜像 FROZEN `tool_c_writeaudit.declared_write_set()` 生成（包内容 + 固定引擎白名单，非运行时写集反推），再由冻结工具 `--audit` 消费。本卡**未**把两者逐函数比对（只比对了最终 `D` 与工具输出的 `write_set_flat ⊆ D` 一致）。若需更严的自证，可另跑一次工具自身的 `declared_write_set()` 与本卡 JSON 做逐项 diff。

## U10 · 「写了但内容等价」与「写了不同内容」的措辞风险

本卡改写后 `BATTLEMD.INI` 与官方**字节不同**（1 行大小写），但**引擎加载的地图完全相同**（语义等价、引擎不加载差异）。任务卡要求「若改写后值与原值完全相同（引擎不加载差异），要明说并收窄结论」。本卡按更保守的方式处理：**明确写出「字节不同 / 语义等价 / 引擎不加载差异」三者的区别**，并把结论范围限定为「写了但内容等价」，不外推到「写了不同内容」。见 `INPLACE_NONINTERFERENCE.md` §2、§6 限制 2。
