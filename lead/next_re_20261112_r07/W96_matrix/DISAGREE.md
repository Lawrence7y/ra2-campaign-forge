# W96 · DISAGREE（与卡面的偏差，全部跑前声明/跑中如实记录）

1. **m3 的「敌方 MTNK Speed=1」实现为类型全局**。vanilla rules 无 per-house 速度键（只有全局 GameSpeedBias），且 4 个 house 共用 MTNK 类型 ⇒ 追加 `[MTNK] Speed=1` 必然同时减速玩家的 300 MTNK `[静态推断]`。实现与 W95 §5 签发探针逐字一致；卡面"敌方-only"措辞按此改写。
2. **m4 的「玩家 300 MTNK Speed=1（敌方不变）」用类型换装 + 属性克隆实现**：玩家 300 台在设计里换成 HTNK，`.MAP` 追加 `[HTNK]` 段 = MTNK 全键克隆 + `Speed=1`（Image=GTNK 保外观）。敌方 MTNK 原样不动。这是 vanilla 覆写通路下"只减速玩家"的唯一忠实实现；若通路死，m4 退化为"玩家=原生 HTNK"混杂臂（实际通路被 m3 证明是活的）。
3. **修复记录（两处，均已入本卡副本，非绕过）**：
   - `w94_trip.py` 的 `_trip_suffix` 在 W94 副本中**未定义**（引用于 result 字典与 TRIP_RESULT 文件名）⇒ 每趟必然 NameError。已修复：`trip_<cell>_r<k> → TRIP_RESULT_<cell>_r<k>.json`，迷你验证覆盖了该路径。
   - m4 克隆段首版含 `Size=3`（MTNK 的占格键），污染 verify_pkg 的 `Size=` 解析（期望 `0,0,100,100`）⇒ 首次主矩阵 build 阶段即中止（无真机浪费）。已删除该键重建，build PASS。
4. **复现带判读**：卡面预注册「m1/m2 应 ≈ 1.75–1.86」实测 1.4949，如实报"未复现"，未改窗口、未改判据、未重跑凑数。
5. batch_runner 的 matrix_log 里 `lock_write` 事件的 `owner` 字段硬编码字符串仍写 "w94-batchrun"（日志字段），而锁文件实际内容（逐字记录在同一事件里）为 `owner=w96-batchrun`——纯日志标签不一致，锁文件本身正确。
