# W65 · DISAGREE.md（异议 / 与上游口径的偏差，全部显式登记）

> 执行者 Hy4｜本文件记录**本卡与任务卡/FROZEN SPEC/上游做法之间的判断分歧**，不隐藏、不自行改写判据。裁决权在 Lead。

## D1 ★ 本卡选用 v15 **append 路线**，未用 `battlemd:inplace` —— 与「W60 是 inplace 卡」的直觉可能不一致

- 任务卡原文：「B = 同一沙箱装 v15 包（用 `W60_battlemd_inplace\ra2forge_patched_v15\`）」，**只指定了工具链目录，未指定 feature-set / 路线**。
- 本卡判断（`[本次读码]` + `[静态推断]`）：任务卡同时要求「苏联徽章（与 W55b/W63 同一入口，**保证可比**）」与「两臂用**同一沙箱起点**」。若用 `battlemd:inplace`，`[SOV1]` 会被改写成自定义 M1，A 臂加载 `SOV01UMD.MAP`、B 臂加载自定义 `RA2F_M1.MAP` ⇒ `map_name` 必然不同 ⇒ FROZEN B-2 直接判 `SHIFT_DETECTED`，且 `dframe` 分布比较的是两张不同地图，不构成「装包是否扰动同一行为」的对照。
- 采用：v15 默认 build（无 `--feature-set`），产出 `BATTLEMD98.INI` + 2 张 MAP + `expandmd98.mix`（`[本次实测]` `out\cmd_prep_build_v15.log`、`out\cadence.json` 记录 route）。`[本次实测]` 四趟 `0x125C` 全为 `SOV01UMD.MAP`，`[SOV1] Scenario=SOV01umd.MAP` 在 BASE 中逐字未变 ⇒ **两臂确实进了同一张图**。
- 相符性：v15 工具链原样使用、未改任何字节；`tool_c_writeaudit.py` 的 C-A 用例（`[转引 W62]`）正是 v15 的 append 路线，故 C 审计判据完全适用。
- **留给 Lead 裁决**：若原意是「必须验 inplace 就地改写」，本卡这一选择即偏差，需另开卡补跑 inplace 臂（见 `UNKNOWNS.md` U5）。本卡不擅自切换，因为切换会破坏「保证可比」。

## D2 ★★ 任务卡采集口径与 FROZEN SPEC §2.1 的结构性冲突 —— 本轮 `SHIFT_DETECTED` 的真实成因

- 任务卡：「采集 ≥30 个 dframe 点（**约 1–2 分钟采样**，6 ms 或 30 ms 节奏按 SPEC 固定，**两臂必须同一 cadence**）」⇒ 只约束**节奏**与**最小时长**，未约束**每趟行数相等**。
- FROZEN `CRITERIA_SPEC.md §2.1`：「离散字段序列 … 用**多重集（值→计数）**比较」；`§2.4` B-2「任一字段多重集不等 ⇒ 直接 `SHIFT_DETECTED`」且**在 B-3/B-4 之前短路**；`tool_b_stats.py:148-149,203-207` 用 `Counter` 实现（计数参与相等判断）。
- 冲突（`[本次实测]`）：固定墙钟 75 s 的四趟行数 10084/10029/10023/10206 ⇒ 合并臂 20113/20229 ⇒ 五个离散字段取值集合完全相同但计数不等 ⇒ **B-2 短路，`SHIFT_DETECTED`**。分布侧 `N_ks=0.001572`、`D_ks=0.001286`、`p=0.766`、`J=1.0` 全部显示无差异，但判据根本没走到 B-3。
- 本卡处置：**按 FROZEN 判据逐字输出 `SHIFT_DETECTED`**，不截断、不补齐、不加白名单、不改工具、不重跑凑数（§3.4 / W55b §2.2 明禁）。同时在 `LIVE_RESULT.md §0` 与最终回复中**显著披露**该词由计数不等触发、不等于检出行为差异。
- **留给 Lead 裁决**：这是判据层缺陷还是采集层缺陷，需 Lead 定；修法（比较取值集合而非计数 / 事先声明每趟固定 N 行 / 按 dframe 长度归一）都涉及改 FROZEN 文件，必须另开卡事先声明，本卡无权做也不做。
- 附带异议（`[本次读码]`）：W62 `tool_b_stats.py` 的 `B-POS/B-NEG/B-NEG2` 自检把所有合成轨迹固定为 `N_SAMPLES=400` 行，**从未覆盖不等长轨迹**，因此该敏感性在交付的工具自检里不可见；这不是本卡能补的。

## D3 对「SHIFT_DETECTED（检出）」这一任务卡括注的措辞保留

- 任务卡把三选一注释为 `SHIFT_DETECTED（检出）`。本卡实测的 `SHIFT_DETECTED` **未检出装包导致的行为分布差异**，只命中了离散多重集计数不等这条规则。
- 本卡因此**不写**「检出装包导致的分布差异」，只写「FROZEN 判据输出 `SHIFT_DETECTED`，触发项为 B-2 `discrete_or_ui_mismatch`，机制见 §2.1」。这是措辞上的保留，不是改判：判定词本身严格取自工具输出，未替换成其它两词之一。
- 同理，**不写**「B 线等价性成立」「等价性成立」；`SAME_DISTRIBUTION ≠ 等价性成立` 的纪律本卡同样遵守。

## D4 每趟结束后删除该趟沙箱目录

- W45 保留 `sandbox_A*` 供复核，W63 收尾删除。本卡在**完成逐字节还原 + 实算 `IDENTICAL_TREE=true` 之后**删除 `sandbox_<tag>`（`out\w65_run.ndjson` 的 `trip_sandbox_removed` 事件）。
- 理由：4 × ~1.99 GB 副本占盘；证据（NDJSON / 截图 / 日志 / `restore_proof_*.json` / `pristine_*` 字节副本）全部已落 `out\`。`[本次实测]` 真目录 `ra2youli` 从未被写，`REAL_DIR_PROOF.txt` 的 PRE/POST 全树零改动即最终自证。
- 若 Lead 要求保留沙箱实体，本卡 `pristine_<tag>\` 已保留全部根级文件字节副本（A 419 / B 425 个），可复核；但完整 2 GB 沙箱已按 W63 惯例清理。

## D5 cadence 取 6 ms 而非 30 ms

- 任务卡：「6 ms 或 30 ms 节奏按 SPEC 固定」。`CRITERIA_SPEC.md §2.1` 示例 `t: 0.006`、`tool_b_stats.py` 合成数据 `t = 0.006*i`；`HANDOFF.md §4.4` 记录 6 ms 是已建立的高频口径（W14 首用），且 W45/W55b 的 75 s 连续采样也是 6 ms。
- 本卡取 **6 ms，四趟同一**（`out\cadence.json`）。`[静态推断]` 若取 30 ms，`dframe` 会变成以 1 为主、对采样相位更敏感的分布，可能抬高 `N_ks`；本卡未对比两种 cadence，不作结论。`[待运行验证]`。

## D6 未重跑以「修正」判定

- 在完成四趟并看到 `SHIFT_DETECTED` 之后，本卡**没有**再跑第二轮（例如改成固定 N 行）来争取另一个词。理由：看到结果后改实验protocol 属于 §3.4 禁止的事后调整，且会产生两套证据、两个判定，容易被误读为 verdict shopping。
- 取舍：宁可交付一个带完整披露的 `SHIFT_DETECTED`，也不交付一个靠事后改动换来的「好看」结果。若 Lead 需要干净的对照，请**另开卡事先声明**新协议再跑。
