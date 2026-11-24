# W96 · PROGRESS（预注册 + 逐趟日志）

**FINAL: 2026-11-14 17:3x（Asia/Shanghai）— 5 趟真机全绿（迷你 1 + 主矩阵 4），outcome 全部 VALID_WINDOW_target_reached ok=true，全程零崩溃零 D1，残留 0，finalize ok=true（sandbox/real 双 manifest identical_tree + 4 锚点哈希 identical）。预注册判读落点：m3/m1=1.188 > 0.95 ⇒「移动不是 C6 抬升的主要来源，交战/毁伤才是」；覆写通路判决 = 生效（A8ED50 首非零 0.80 s → 15.53 s + t=30 截图形态证据）；复现带 m1/m2=1.495 未命中 1.77–1.86，如实报。**

卡：W96_matrix（r07）｜真机串行 + 锁 `lead\next_re_20261112_r07\.game_instance.lock`（owner=w96/w96-batchrun，收尾恢复 owner=lead）
工具链：整卡复制自 `r06\W94_batchrun`（batch_runner / batch_analyze / w94_* 工具），本卡私有副本上修改，从不跨卡 import。
时间戳（Get-Date 实测）：2026-11-14 17:0x 起步（Asia/Shanghai）。

---

## 预注册（写于任何真机趟之前 —— 不许事后改）

### 主矩阵（4 格 × 1 趟，observe_sec=150，min_valid=150，hard_cap=200，sample_ms=6）

以 C6 为基线（100×100、NACNST+6×NAPOWR(步长3)+12×TESLA、玩家 300 MTNK Guard、敌 3 house 各 400 MTNK）：

| 格 | 改动 | 旋钮实现 |
|---|---|---|
| m1_ref_combat | 敌全 Hunt（= C6 原样） | arm=C6 预设 |
| m2_ref_idle | 敌全 Guard（= CTRL_C6） | arm=C6 + enemy_mission=Guard |
| m3_slow | 敌全 Hunt + `[MTNK] Speed=1`（map-INI 覆写通路） | arm=C6 + speed_all_mtnk |
| m4_slow_player | 敌全 Hunt + 玩家 300 坦克 Speed=1（敌不变） | arm=C6 + player_slow_clone（见下「实现偏差」） |

### 实现偏差（跑前声明，抄送 DISAGREE.md）

1. **vanilla map-INI 覆写是"按类型全局"的，无 per-house 速度机制** `[静态推断]`（全 4 个 house 共用 MTNK；rulesmd 无 per-house speed bias，只有全局 GameSpeedBias）。因此：
   - **m3** 的 `[MTNK] Speed=1` 实际是**类型全局**：玩家 300 MTNK 也被减速。这与 W95 §5 签发的探针逐字一致。主判读（移动 vs 交战）不受影响：双方移动都被减速，若 CPU 大降 ⇒ 移动成本显著。**"敌方-only 减速"这一原始措辞按此偏差改写**。
   - **m4**（玩家-only 减速）用同一条覆写通路的**类型换装 + 属性克隆**实现：玩家 300 台在设计里换成 `HTNK`，`.MAP` 追加 `[HTNK]` 段，内容 = MTNK 全段键值克隆 + `Speed=1`（Image=GTNK 使外观一致）。敌方 MTNK 原样不动。若覆写通路**未生效**，m4 的克隆也不生效 ⇒ 玩家变成原生 HTNK（400HP/120mm/MZ=Destroyer/Speed=6）——该混杂仅在"通路未生效"判决成立时才进入解读。
2. 迷你验证格 `mini` = C6 臂 1 趟，observe=60（时序验证专用，**不进**主矩阵判读）。

### 预注册判读（主矩阵，跑前锁定；禁止 p 值/CI/显著）

- 度量：`rate_pct_filetime`（窗口线程 CPU / 墙钟，单核占用 %，全采样窗）。
- **先算 m1/m2**：应 ≈ 1.75–1.86（复现 §626 收窄区间 1.77–1.86 为参考带，不作为判据门槛，只作复现核验）。
- **再算 m3/m1**：
  - ≤ 0.85 ⇒ 「移动/寻路占 C6 抬升的显著部分」；
  - 0.85–0.95 ⇒ 「部分」；
  - \> 0.95 ⇒ 「移动不是主要来源，交战/毁伤才是」。
- **m4/m1**：若 ≈ 1.0 而 m3/m1 明显 < 1 ⇒ 敌方移动是主因；反之亦然。（在 §偏差-1 下，m4 的对照意义是"玩家侧移动 + 玩家侧属性改变的贡献"；敌方-only 的纯读数由 m3(全局)−m4(玩家-only) 的差近似。）
- **覆写通路判决（预注册）**：m3 里"变慢"需两条证据至少一条成立才判"通路生效"：
  1. `A8ED50` 首次非零的 idx/时刻显著后移（C6 基线 idx≈52–170、t≈0.3–1.1 s；变慢应显著后移）；
  2. t=30 s 截图敌军集群推进位置比 m1 同刻明显更靠后（形态证据，不逐字转写文本）。
  两条都没有 ⇒ 判「覆写通路未生效」，并写明：**§625 的「Crewed=no 无效」作废**（不是因子无效，是改动没生效）。
- 硬纪律：真机串行；沙箱 only；4 锚点哈希跑前跑后；残留 0；trip 目录唯一；D1/D2/D4 全套；小步落盘。

---

## 逐趟日志

### 主矩阵（run_id=R07_W96_matrix，4 格 × 1 趟，observe=150 s；17:15–17:28）

| 趟 | outcome | ok | CPU 消耗率 % | A8ED50 首非零 idx / t_ingame | 非零占比 | X87E8E0 变化 | D1 | 还原 | 残留 |
|---|---|---|---|---|---|---|---|---|---|
| trip_m1_ref_combat_r1 | VALID_WINDOW_target_reached | true | 37.8446 | 132 / 0.799 s | 0.98625 | 7306 | 无 | ok | 0 |
| trip_m2_ref_idle_r1 | VALID_WINDOW_target_reached | true | 25.3132 | （全窗无非零，占比 0.0） | 0.0 | 0 | 无 | ok | 0 |
| trip_m3_slow_r1 | VALID_WINDOW_target_reached | true | 44.9497 | 2566 / 15.533 s | 0.86597 | 8408 | 无 | ok | 0 |
| trip_m4_slow_player_r1 | VALID_WINDOW_target_reached | true | 46.0636 | 112 / 0.679 s | 0.99220 | 8742 | 无 | ok | 0 |

（首主矩阵尝试于 17:15 在 **build 阶段**中止：m4 克隆段 `Size=3` 污染 verify 的 Size 解析；修复重建后重跑，无真机浪费。）

### 收尾（17:31）
- `w94_finalize.py` ok=true：卸包 → verify exit 0 → 差集清场（无 engine-dropped .sav）→ pristine 逐字节还原 → **sandbox identical_tree** → **real identical_tree + W44 基线 ok（647 files / 1989215270 B / 277 maplike）** → 4 锚点哈希 identical（gamemd.exe / ddraw.dll / RA2MD.INI / BATTLEMD.INI）→ 残留 0 → 锁 owner=lead。
- 真目录 `ra2youli` 零改动（pre/post manifest 逐字节一致），既存 v0.3 只在沙箱副本内卸载（W84/W85/W88 先例）。

### 判读落点（对照预注册）
- m1/m2 = 37.8446/25.3132 = **1.4949** —— 参考带 1.75–1.86 **未复现**（两臂同向抬高 ~+4~7 pp；见 UNKNOWNS U1）。
- m3/m1 = 44.9497/37.8446 = **1.1878 > 0.95** ⇒ 「**移动不是主要来源，交战/毁伤才是**」，且方向为负（减速反升 +18.8 %）。
- m4/m1 = 46.0636/37.8446 = **1.2172** —— 预注册规则前提（m3/m1<1）不成立；观察事实如实记录（见 UNKNOWNS U2）。
- 覆写通路：**生效**（两条预注册证据均成立，见 MATRIX_R07.md §通路判决）。

（每趟完成后追加；时间戳 Get-Date 实测）


### 迷你验证 [本次实测]（2026-11-14 17:14:59）
- trip_mini_r1：build PASS → install(sha短路) → 真机趟 102 s → **VALID_WINDOW_target_reached ok=true**；
- A8ED50 首非零 seq=80 / t_ingame=0.4804 s（落在 C6 基线带 idx 52–170 / t 0.3–1.1 s 内）；
- X87E8E0 首变 t=0.024 s、窗口内变化 4327 次；采样 9951 样 / 读失败 0；
- t=0 / t=30 截图在趟目录；RA2MD.INI / ddraw.ini / benchbak 逐字节还原 ok；残留 gamemd=0；
- 锁：趟始 owner=w96-batchrun → 趟末 owner=lead（try/finally 生效）；
- **修复记录**：w94_trip.py 的 _trip_suffix 未定义（NameError）已在本卡副本修复（trip_<cell>_r<k> → TRIP_RESULT_<cell>_r<k>.json）；
- **判定：迷你验证通过，运行器时序（build→install→trip→TRIP_RESULT 回读→锁归还→残留 0）全部正常。主矩阵放行。**

