# W72 · `DISAGREE.md` — 与卡面/上游的偏差、取舍与保留意见

> 执行者 Hy4（W72，非 Lead）。**不重新论证 Lead 已定方向**（inplace 是产品路线、append 路线未覆盖发布功能）。本文件只记录执行中的取舍与「我不同意/需 Lead 裁决」的点，供 Lead 签发时对照。

---

## D0 · 权威判据版本：采纳 W68b/Hy4 版，GLM 版仅交叉印证（与 W69 一致，无异议）

任务卡指定 W68b 权威版：`CRITERIA_SPEC_V2.md` sha `7364E700…`、`tool_b_stats_v2.py` sha `B419959A…`。本卡**先复制到 `work\criteria_frozen\` 并逐位核对**（`SHA256_PROOF.json`），运行时只用卡内副本；W68 根目录因本会话两次并发覆盖不可信。GLM 版（`B-W68-2`，sha `62B0C275…`）**未进入判定路径**。此项与 `W69\INSTRUCTION_FROM_LEAD.md` §3 的通用规则一致，**无分歧**。

## D1 · 「唯一自变量」——执行上与卡面措辞有偏差，已如实登记（**请 Lead 注意**）

卡面写：

> **唯一自变量** = 「`BATTLEMD.INI` 被 inplace 机制改写过（`.bak` 在位、清单记录 `original_sha256`）」

`[本次实测]` 文件系统层面，B 臂相对 A 臂**还多了 6 个文件**：`BATTLEMD.INI.ra2forge.bak`、`W72M1.MAP`、`W72M2.MAP`、`expandmd98.mix`、`ra2forge_install.json`、`ra2forge_install.json.seal`（见 `out\c_audit_verdict.json` 的 `write_set`）。

- **原因**：v15 `builder.py` 对任何 design 都无条件产出 `*.MAP` + `expandmd98.mix`；`install.package_files()` 也总把它们列入复制集。要让包「只含 `BATTLEMD.INI`」需要事后裁剪包内容，但那会与 feature_set 的 `shipped()` / plan-actual 对账冲突，风险未评估，本卡**未擅自改动工具链**。
- **本卡的取舍**：保留产物路线（更贴近 W63/W70 的真实产品包），把「唯一自变量」理解为**行为层面**的隔离——`Scenario` 指向官方图，包内地图惰性不加载，四趟 `0x125C` 全为 `SOV01UMD.MAP` 实证两臂同图。同类惰性产物在 W65/W69 的 append B 臂已存在且该卡判 `SAME_DISTRIBUTION`。
- **保留意见**：若 Lead 要求「字节层面绝对唯一自变量」，需另开卡做「极简 inplace 包」对照；本卡结论不覆盖该更严口径。见 `UNKNOWNS.md` U2。

## D2 · 采用「等价但不同的写法」而非「值与原值完全相同」（卡面允许的分支，说明理由）

卡面主方案是 `Scenario=SOV01UMD.MAP`（就地改写，值与原值相同或等价）；并预告「若 v15 预检拒绝改写后值与原值相同，改用等价但不同的写法」。

本卡**直接采用等价但不同的写法**（全大写 `SOV01UMD.MAP` vs 官方 `SOV01umd.MAP`），理由有三：

1. `[本次读码]` v15 的 `inplace_preflight()` / `rewrite_sov1()` / `builder.py` **都没有**「无变化/无意义」拒绝门（离线 dry-run build exit 0 已实证）。卡面担心的那类拒绝**不存在**。
2. 但 `install.py:1386` 的「字节与包内一致但未记账」ADOPT 分支、`resolve_integration.SECOND_INSTALL_SEMANTICS.IDEMPOTENT_REPLAY` 语义意味着：**若包内 `BATTLEMD.INI` 与官方逐字节相同**，安装会走「零写」路径 ⇒ 不生 `.bak`、manifest 不记 `original_sha256` ⇒ **C-6 与本卡自变量都不成立**。所以字节相同不可用。
3. 大小写差异在 Windows/引擎按文件名大小写不敏感匹配下**语义等价**，且四趟 `0x125C` 实测同为 `SOV01UMD.MAP`（A 臂官方 `SOV01umd.MAP` 也被引擎读成全大写），两臂同图成立。

⇒ 实际 diff **仍只有 1 行**（卡面要求），见 `out\ini_diff.json`。**此项是卡面明确授权的分支，不是偏离。**

## D3 · 「引擎不加载差异」的措辞澄清（比卡面更保守）

卡面要求：若改写后**值与原值完全相同**（引擎不加载差异）要明说、收窄结论。本卡情况更细：**字节不完全相同**（1 行大小写），**但引擎加载的地图完全相同，引擎不加载差异**。本卡按更保守方式处理：在 `INPLACE_NONINTERFERENCE.md` §2 与 §6 限制 2 中**明说这是「写了但内容等价」**，与「写了不同内容」是两种情形，结论范围收窄；**不外推到「inplace 改写任意内容都不扰动」**。这与任务卡「结论范围要相应收窄」的意图一致。

## D4 · V2 自检第一次失败：保留失败日志，不粉饰

`--selftest` 第一次 exit 1（冻结工具把 fixture 解析到工具同目录 `EVIDENCE\ce_*`，卡内副本无此 fixture）。本卡**没有**删除或覆写失败日志，而是复制 W68 的 fixture **数据**（非脚本）到卡内并重跑同一份字节不变的冻结工具得 exit 0，把两次尝试都记进 `out\compare_summary.json`。`--compare` 走显式路径参数，第一次即 exit 0，与自检失败无关。详见 `UNKNOWNS.md` U8。**不把合成自检当真机结论。**

## D5 · 未触发 `--allow-content-conflict`

W69 对 append 包保留了 rc==1 时加 `--allow-content-conflict` 的重试；本卡对 inplace 包保留同样逻辑但**四趟 / 审计安装均一次 rc=0**（`out\cmd_B?_install.log`、`out\cmd_audit_install.log`），未触发。原因：`inplace_preflight` 取代了通用 content-conflict 对该目标文件的适用性，且 A/B 两臂起点一致（v0.3 已卸载、孤儿 `.bak` 已移除）。此为实测事实，非事后放宽。

## D6 · 结论签发权在 Lead

本卡**不写**「B 线等价性成立」「inplace 无影响」「等价性成立」，**不签发**任何等价/不等价结论。只交付「原始产物 + 退出码 + 判据逐字输出」与严格口径句：

> 「在 V2 判据、该场景、该观测量集合下，未检出 inplace 改写 `BATTLEMD.INI` 所导致的行为分布差异」。

## D7 · 与 W65/W69 的关系（不覆盖、不重判）

- W65 的 `SHIFT_DETECTED`（采样时长伪差异）、W68 对 W65 数据的诊断性 V2 重算、W69 用 V2 **重新采集**的 append 路线 `SAME_DISTRIBUTION` —— **三件事互不覆盖**，本卡也未改动任何他卡产物。
- 本卡补的是「产品路线 inplace」的覆盖缺口；**append 结论与 inplace 结论是两条不同路线的独立判定**，不能互相替代，也不能合并成「B 线等价性成立」。
- W63/W70 的 inplace 三关链证明「功能贯通」，本卡证明「该场景/该观测量集合下未检出 inplace 改写导致的行为分布差异」，两者口径不同。
