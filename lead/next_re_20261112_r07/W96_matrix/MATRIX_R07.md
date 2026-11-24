# W96 · MATRIX_R07 —— 批量运行器首跑（端到端）+ C6 抬升的"行军/寻路"份额

> 卡：W96_matrix（r07）｜执行：subagent `w96-matrix`｜时间：2026-11-14 17:00–17:32（Asia/Shanghai，Get-Date 实测）
> 工具链：整卡复制自 `r06\W94_batchrun`（batch_runner / batch_analyze / w94_* 工具），本卡私有副本上修改；本卡副本修复 2 个 bug（见 §6）。
> 纪律：真机串行 + 锁（owner=w96/w96-batchrun → 趟末 owner=lead）；沙箱 only（真目录 `ra2youli` 只读，pre/post manifest 逐字节一致）；全程无注入/无调试器/无 taskkill 非本卡进程；trip 目录唯一；每趟后 PROGRESS.md + HEARTBEAT.txt 落盘。

---

## 0. 一句话结论

**运行器端到端首跑通过（5 趟全绿）；预注册判读落点：`m3/m1 = 1.188 > 0.95` ⇒ 「移动/寻路不是 C6 抬升的主要来源，交战/毁伤才是」——且慢速臂 CPU 反升（m3 +18.8 %、m4 +21.7 %），方向为负；map-INI 覆写通路被引擎采纳 `[本次实测]`（A8ED50 首非零 0.80 s → 15.53 s + t=30 截图形态证据）；复现带 m1/m2 = 1.495 未命中 1.77–1.86，如实报。**

---

## 1. 迷你验证（第 0 步，先行）

`examples\matrix_R07_mini.json`（1 格 × 1 趟，observe=60 s，run_id=R07_W96_mini）：

- trip_mini_r1：build PASS → install（sha 短路）→ 真机趟 102 s 墙钟 → **VALID_WINDOW_target_reached ok=true**；
- 时序链验证：**build→install→trip→TRIP_RESULT 回读→锁归还→残留 0** 全部正常；A8ED50 首非零 t=0.480 s（落在 C6 基线带内）；RA2MD.INI/ddraw.ini/benchbak 逐字节还原 ok；残留 0；
- **迷你验证通过，主矩阵放行**（判据：任一环节失败即就地修运行器，未触发）。

## 2. 主矩阵（4 格 × 1 趟，observe=150 s，run_id=R07_W96_matrix）

以 C6 为基线（100×100、NACNST+6×NAPOWR(步长3)+12×TESLA、玩家 300 MTNK Guard、敌 3 house 各 400 MTNK）：

| 格 | 改动 | CPU 消耗率 %（FILETIME 全窗） | outcome | ok |
|---|---|---|---|---|
| m1_ref_combat | 敌全 Hunt（= C6 原样） | **37.8446** | VALID_WINDOW_target_reached | true |
| m2_ref_idle | 敌全 Guard（= CTRL_C6） | **25.3132** | VALID_WINDOW_target_reached | true |
| m3_slow | 敌全 Hunt + `[MTNK] Speed=1`（类型全局，见 §6-1） | **44.9497** | VALID_WINDOW_target_reached | true |
| m4_slow_player | 敌全 Hunt + 玩家 300 台 HTNK+`[HTNK]` MTNK 克隆段 Speed=1（敌不变，见 §6-2） | **46.0636** | VALID_WINDOW_target_reached | true |

锚点明细（batch_analyze，idx=样本序号）：

| 趟 | A8ED50 首非零 idx / t_ingame | 非零占比 | X87E8E0 变化 | 读失败 | 前台丢失 | D1 |
|---|---|---|---|---|---|---|
| m1 | 132 / 0.799 s | 0.98625 | 7306 | 0 | 0 | 无 |
| m2 | （全窗无非零） | 0.0 | 0（首值 0xFFFFFFFF，无交战） | 0 | 0 | 无 |
| m3 | **2566 / 15.533 s** | 0.86597 | 8408 | 0 | 0 | 无 |
| m4 | 112 / 0.679 s | 0.99220 | 8742 | 0 | 0 | 无 |

全程零崩溃：5 趟无 except.txt 新件、无 WER、无 EIP 归档、无残留进程；D2 语义 `ok` 全 true；4 格均未触发 stop_on。

## 3. 预注册判读落点（跑前锁定，未事后改）

1. **复现核验**：`m1/m2 = 37.8446/25.3132 = 1.4949` —— 参考带 1.75–1.86 **未复现** `[本次实测]`。两臂绝对值同向高于签发带（m1 37.84 vs 31.0–33.6；m2 25.31 vs 17.75–18.10，抬高 ~+4~7 pp），比值被压缩。未改窗口、未改判据、未重跑凑数；来源候选见 UNKNOWNS U1 `[未证]`。m2 侧"零交战"锚健康：A8ED50 全窗零非零、X87E8E0 零变化 —— 度量链本身干净。
2. **核心判读**：`m3/m1 = 1.1878` —— **> 0.95 档 ⇒ 「移动不是 C6 抬升的主要来源，交战/毁伤才是」** `[本次实测]`。且方向为负：把全场 MTNK 速度 7→1，150 s 窗 CPU **反升 18.8 %**。
3. **谁在动**：`m4/m1 = 1.2172` —— 预注册规则的前提（m3/m1 明显 <1）不成立，规则不触发；观察事实：只减速玩家的 300 台 Guard 坦克（几乎不动的单位）CPU 也**反升 21.7 %**，而敌方到触时刻不变（A8ED50 idx 112 ≈ m1 的 132；t=30 截图敌军与 m1 同刻压境）`[本次实测]`。机理 `[未证]`（UNKNOWNS U2）。
4. **对 §626 第二问的回答**：按本卡判据，**「+75~86 %」不能主要归给行军/寻路**——把"单位时间内移动格数"压到 1/7 后，窗口 CPU 不降反升。C6 抬升的主承载仍是交战/毁伤（及毁伤触发的生兵链）。口径注意：这是 C6（100×100）150 s 全窗读数；W91 的 200×200「纯行军相位 56.86 %」是另一张图、另一种窗口，不与本读数矛盾（前 60 s 相位本就更贵：迷你 60 s 窗 58.4 % vs 150 s 全窗 37.8 %）`[本次实测]`。

## 4. 覆写通路判决（预注册两条证据，均成立）

**判决：map-INI 覆写通路被引擎采纳 `[本次实测]`**

1. **A8ED50 首非零显著后移**：m1 idx 132 / t=0.799 s（复现 C6 基线带 idx 52–170 / t≈0.3–1.1 s）→ m3 idx **2566** / t=**15.533 s**（~19× 后移，显著越出基线带）。m4 idx 112 / t=0.679 s ≈ m1 —— 敌方未被改动（对照一致性）。
2. **t=30 s 截图形态证据**（不逐字转写文本）：
   - m1 t=30：敌军（蓝灰）集群已**抵达玩家基地**并开火，弹坑密布、Tesla 线圈交火中（`out\trip_m1_ref_combat_r1\screen_..._combat_t030.png`）；
   - m3 t=30：**视野内敌军踪影全无**，基地完整、**零弹坑**（`out\trip_m3_slow_r1\screen_..._combat_t030.png`）；
   - m4 t=30：敌军与 m1 同刻压境（`out\trip_m4_slow_player_r1\screen_..._combat_t030.png`）——玩家侧克隆不影响敌军推进，与设计一致。

**推论**：W95 洞 1 的「红=零信息」框架可以收口——对 **Speed** 键，`apply_crewed_override` 通路（`[XX]\r\nKey=Value\r\n` 追加进 `.MAP`）被 RulesClass 解析并生效 `[本次实测]`；§625 的「`Crewed=no` 无效」**不因通路问题作废**（本卡落在"通路生效"分支）；但 **Crewed 键本身**的采纳仍 `[未证]`（本卡没有直接测 Crewed 键）。

## 5. 分级汇总

- `[本次实测]`：5 趟全部 outcome/ok；四格 CPU 消耗率与三组比值（1.4949 / 1.1878 / 1.2172）；A8ED50 首非零 idx/t 四组；m2 零交战锚（A8ED50 全窗零非零、X87E8E0 零变化）；覆写通路两证据（m3 到触后移 + 三张 t=30 截图形态）；真目录零改动 + 4 锚点哈希跑前跑后 identical；迷你端到端时序链。
- `[静态推断]`：vanilla 无 per-house 速度覆写（4 house 共用 MTNK，仅全局 GameSpeedBias）；m3 减速为类型全局（玩家同减速）；m4 的"只减速玩家"只能经类型换装+克隆段实现。
- `[未证]`：m3/m4 CPU 反升的机理（UNKNOWNS U2/U3）；复现带未命中的来源（U1）；Crewed 键采纳（U4）；本图与 W91 行军相位的关系（U5）。

## 6. 本卡副本修复（非绕过）

1. `w94_trip.py`：`_trip_suffix` 未定义（W94 副本隐性 NameError，任何真机趟都会 FATAL）⇒ 修复为 `trip_<cell>_r<k> → TRIP_RESULT_<cell>_r<k>.json`；迷你验证覆盖该路径。
2. m4 克隆段首版含 `Size=3`（MTNK 占格键）污染 verify 的 `Size=` 解析 ⇒ 首次主矩阵在 build 阶段中止（无真机浪费），删键重建后 PASS。
3. 新增臂旋钮 `speed_all_mtnk` / `player_slow_clone`（runner 校验互斥 + build 追加段 + verify 附加存在性断言与 `russian_htnk` 计数），锁 owner 扩为 w96/w96-batchrun，锁 run_id 改 R07；日志 `lock_write.owner` 字段仍是硬编码 "w94-batchrun" 字符串（锁文件实际内容逐字正确，见 DISAGREE.md-5）。

## 7. 未覆盖 / 边界

- 每格 1 趟（卡面指定 4×1）：格内极差不可估，比值为单趟样本（UNKNOWNS U6）；
- 未做 ABBA 观测器校准、未挂 render_channel（默认 false）；
- 未测 Crewed 键、未动 200×200 几何、未做任何显著性表述（无 p 值/CI/"显著"）；
- W97_artmd 的 artmd.ini / Foundation 之争不在本卡范围。

## 8. 交付物清单

- `MATRIX_R07.md`（本文）、`matrix.json` + `matrix_mini.json`（实际用的矩阵）、`examples\matrix_R07_*.json`
- `out\`：5 个唯一 trip 目录（D1 无崩、D4 输入归档含 design JSON/.MAP/BATTLEMD.INI/MAPSELMD.INI+sha256、t=0/30… 截图）、`SUMMARY.csv`/`SUMMARY.md`（分析器产出，5 行含 mini）、`matrix_log.ndjson`、`plan_*.json`、`BUILD_*.json`、`OFFLINE_mini.json`、`FINALIZE.json`（ok=true）
- `PROGRESS.md`（顶部 `FINAL:`）、`HEARTBEAT.txt`、`UNKNOWNS.md`、`DISAGREE.md`、`BATCH.md`（W94 原版说明，本卡复制件）
