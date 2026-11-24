# W69 · `UNKNOWNS.md`（未知 / 局限 / 待验证，全部显式登记）

> 执行者 Hy4（非 Lead）｜本文件只登记**本卡未验证或无法验证的事项**，不隐藏、不自行补跑凑数。裁决权在 Lead。

## U1 ★ 五个离散字段在四趟中全部为单值常量 ⇒ 离散腿读数几乎无信息量

- `[本次实测]` `b_compare_v2.json` 中 `map_name / stage_idx / end_of_game / skip_map_select / battle_idx` 五字段 A∪B 合并池**各只有一个取值**（`SOV01UMD.MAP` / `0` / `0` / `0` / `1`）。
- 因此 `T_f ≡ 0`、`N_disc ≡ 0`、`p_f ≡ 1.0`（`p_method=exact_single_category_degeneracy`），逐字段判定恒 `no_shift_detected`。
- `[静态推断]` 该读数**只说明「值集与占比相同」**，不能反推「装包未扰动行为」，更不能反推等价。W68 `UNKNOWNS.md §2` 已就此声明；V2 的离散腿在本场景下**几乎不提供检出力**，正式判定实际由 B-3 连续腿（`dframe` 两样本 KS + 置换 p）决定。
- `[待运行验证]` 若要让离散腿真正参与检验，需要设计**能产生多取值离散字段**的场景（例如中途切图 / 关卡推进 / 触发 `end_of_game`），并事先在新卡声明；本卡不擅自扩大观测量或改场景。

## U2 观测量集合与时间趋势

- `[静态推断]` 占比、KS、分位数都只比较**边缘分布**，不比较取值顺序。若行为存在时间趋势（如中途切图再切回），占比可能不变而行为已变。这是 FROZEN 连续量已有的局限，V2 未改变。
- 本卡观测量为任务卡冻结的 7 个字段 + `ui_controls`；未采集帧率、CPU、鼠标/键盘输入、AI 行为、网络等其它量。结论**只对该观测量集合**成立。

## U3 场景 / 分辨率 / 语言 / 采样时长的外推边界

- 本卡只在**苏联战役第一关 `SOV01UMD.MAP`**、2560×1440 桌面、1707×960 游戏窗口、单一中文环境下采集；四趟各 75 s 墙钟 / 6 ms 节奏。
- `[待运行验证]` 其它关卡、其它徽章、其它分辨率/语言、更长采样（>75 s）、其它 cadence（如 30 ms）、装包后**重新启动多次**等均未验证。W65 `DISAGREE.md` D5 已登记 6 ms vs 30 ms 的差异未对比。

## U4 `ui_controls` 的 `min(n_a,n_b)` 逐行截断（V2 未修的遗留弱点）

- `[本次读码]` `jaccard_mean` 沿用 FROZEN 的 `min(len_a,len_b)` 逐行配对截断；`CRITERIA_SPEC_V2.md §6` / W68 `UNKNOWNS.md §5` 明确登记为遗留弱点，V2 **未改动**。
- `[本次实测]` 本卡四趟 `ui_controls` 恒为 `[0]`，`J_ui=1.0`；该截断不影响本次读数（两臂逐行集合相等时不可能制造伪差异）。但对采样时长仍敏感，需后续卡单独处理；本卡不擅自扩大改动面。

## U5 合并臂的拼接边界伪差（继承 v1/W65，未剔除）

- `[本次实测]` `A=A1∪A2`、`B=B1∪B2` 各含 1 个跨趟拼接边界 `dframe` 伪差（帧号从 ~2392 跳回 ~48），导致合并臂 `cv_A≈143.09` / `cv_B≈141.06`。两臂各一个、对称存在，与 FROZEN 工具自检 `_merge()` 语义一致。
- 本卡**未做任何剔除**（§3.4 禁止截断/补齐），`b_compare_v2.json` 的 `D_ks=4.888e-05` 已包含它。`[静态推断]` 其对 KS 贡献量级 ≈1/20460。

## U6 判据 C 的快照对象是惰性沙箱，而非 B1/B2 趟内沙箱实体

- `[本次实测]` `--phase audit` 从同一 `sandbox_base` 复制出**独立惰性沙箱**（`sandbox_audit`），用与 B1/B2 **同一条** v15 `install` / `uninstall` 命令取 `S_pre/S_post/S_uninst` 三份全树快照，再跑 `tool_c_writeaudit.py --audit`。与 W65 的做法一致。
- B1/B2 的趟内沙箱在逐字节还原 + `IDENTICAL_TREE=true` 之后按 W63/W65 惯例删除（4×~1.99 GB 占盘），`pristine_<tag>\` 保留了全部根级文件字节副本可复核。
- `[静态推断]` 惰性沙箱与真机沙箱的差异仅在于「未启动 `gamemd.exe` 跑图」；安装期的写入集由 v15 CLI 决定，与是否跑图无关。但**本卡未对 B1/B2 趟内沙箱本体直接跑 `--audit`**，这一点如实登记。

## U7 ★ W68 并发写入冲突（本卡启动后根目录被覆盖）

- `[本次实测]` 本卡于 `00:45:12`（spec）/ `00:46:19`（tool）观察到 `W68_criterion_discrete_fix\` 根目录被并发方从 GLM 版（`CRITERIA_SPEC_V2.md` 10845 B / FROZEN `00:32:14`；`tool_b_stats_v2.py` 22280 B / `B-W68-2`）覆盖为 W68b/Hy4 版（15229 B / FROZEN `00:33:05`；20787 B / `B-W68B-V2-1`）。本卡在 `00:45` 首次读到的即是 GLM 版。
- `[转引]` `W68_criterion_discrete_fix\EVIDENCE\CONCURRENT_WRITER_NOTE.md`（Hy4，00:46）说明：根目录已「恢复自洽」为 W68b 版，并在 §4 给出权威 sha256 与「若再次被覆盖 → 以 `EVIDENCE\W68b_snapshot\` 为准」的验收指引；`REVIEW\LEAD_VERIFY_W68B.md` 的 FROZEN `00:33:05` 亦对应 W68b 版。
- `[本次实测]` 本卡副本（`~00:48` 复制）与上述权威 sha256 **完全一致**（见 `TOOL_HASHES.json` / `LIVE_RESULT_V2.md §6.1`）。
- `[待裁决]` 并发方产物的归属、是否终止并发进程、后续卡是否合并两版（例如采用并发方的「联合 max 统计量置换」处理多重比较）——本卡**不自行拍板**。若 Lead 认为本卡应使用 GLM 版重跑，须**另开卡事先声明**；本卡不事后切换判据。
- `[本次实测]` 两版对 W65 数据的结论一致（`SAME_DISTRIBUTION`），`CONCURRENT_WRITER_NOTE.md §2` 亦判定「口径实质一致」；本卡在 `LIVE_RESULT_V2.md §4.2` 把两版 gate 原句都逐字抄录，避免验收歧义。

## U8 B 臂用 v15 **append** 路线，未验 inplace

- `[本次读码]` + `[转引 W65 DISAGREE.md D1]`：任务卡明确「沿用 W65 的取舍」，B 臂用 append（`BATTLEMD98.INI`），**不用 inplace**，因为要让两臂玩同一张官方图才可比。
- `[本次实测]` 四趟 `0x125C` 全为 `SOV01UMD.MAP`；`sandbox_base\BATTLEMD.INI` 的 `[SOV1] Scenario=SOV01umd.MAP` 逐字未变。
- `[待运行验证]` inplace 就地改写 `[SOV1]` 的装包效果**本卡未验证**；按任务卡要求「若你认为必须验 inplace，另开卡，别在本卡混」。因此本结论**不覆盖** inplace 路线。

## U9 两版 V2 实现细节差异（不影响本卡所用版）

- `[静态推断]` 权威 W68b 版：`N_disc(f)=max(TVD(A1,A2), TVD(B1,B2))`（两臂）、`numpy.random.default_rng(seed).multivariate_hypergeometric` 精确无放回重分、schema `B-W68B-V2-1`。
- 归档 GLM 版：`D_disc=max_f TVD_f` 联合统计量、`random.Random(seed).shuffle`、`N_disc` 仅 A 侧、schema `B-W68-2`、工具输出含 `gate` 字符串。
- `[转引]` W68 `DISAGREE.md §2/§3`、`UNKNOWNS.md §3` 已登记 RNG 非逐字同构、`D_floor` 语义复用、`N_disc` 聚合取 max 未做敏感性分析、多重比较未校正等设计决策。本卡**沿用冻结实现，未复核、未改动**。

## U10 未做的对照

- 未重跑第二轮以「修正」判定（§3.4 禁止事后调整 / verdict shopping）。
- 未对 W65 的四份 NDJSON 再跑一次 V2 作为对照（那是已存在的事后诊断，不是独立采集）；本卡四趟是**全新真机数据**。
- 未验证 `n≈8000/趟` 名义量与实际 `≈10200/趟` 的差异对判定的影响（`n_min=30` 远超，B-0 不敏感）。
- 未做跨卡交叉运行（不直接调用别卡脚本，红线 5）。
