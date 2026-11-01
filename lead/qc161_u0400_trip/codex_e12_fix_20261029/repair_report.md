# E12 BOOT 候选修复（离线，2026-10-29）

本文件为修复者自证，不能代替另一上下文的独立复验或 Leader 发射判定。写域仅本目录 candidate、repair*、tmp 及获准短临时域 `.e12tmp_repair`。未修改共享源件、台账、TRIP_INDEX、游戏目录或两冻结母本。

## 基线

- 原驱动 SHA-256：`f9d3f36a543d995ffd36d1305afb2b9c0336b6a40111e9a37e168b725d9e89be`。
- 原驱动 `--selftest`：短临时域 `.e12tmp_repair` 下真实 rc=0，82 项、红=0；完整输出见 `repair_baseline_shorttmp.txt`。
- 长工作区 TEMP 下的 `KeyError: latch_row_index` 不是 BOOT 源码回归：独立调用 `trip_once('hang')` 发现原始记录 phase=`mkdir`、fail=`carrier_pathlen`，长夹具路径触发生产 130 字符闸；后续格式化缺失字段掩盖前置失败。候选仅在 A 组首次趟失败时打印完整原记录并 rc=1，不放松路径闸、不吞错误充绿。

## 候选修改

1. 新增 `wallclock_ms` OPS seam，用真实 `time.time_ns() // 1_000_000` 与每次现读 uptime 计算 `boot_wallclock_ms`。显式设置 GetTickCount64 的 64 位返回类型，避免长期运行时默认 ctypes 32 位截断。
2. 批次前 `capture_boot()` 保存不可变参考；每趟重新 `capture_boot()`，`assert_same_boot()` 比较开机墙钟估计，绝对差大于 2000ms 才阻断。不是每趟重置参考。
3. 继续记录 `boot_ms_at_start`，追加当前墙钟、开机墙钟估计、参考和容差，保留取证。无效时钟/参考保守拒绝。
4. 将原 B-18/B-19 和 F:boot_assert 改为新的开机会话语义，保留检查意图及原有其他检查；虚拟时钟的 uptime 与墙钟一起推进。
5. 新增实际双趟推进 137 秒正例、实际重启在 popen 前阻断反例、双向 ±2000/2001ms 边界、无效参考；旧 raw 比较和删除检查的变异由同一正反例判据击杀。新增 BOOT 变异仅接受指定 TripFail，任意异常不会被当作成功击杀。

## 证据与限制

- 候选目录包含驱动、自检及两个逐字节相同的冻结依赖副本，没有复制游戏目录。
- 所有执行均为离线自检或无授权 `--live` 拒绝测试，未运行 `--live --approved`。
- 墙钟超过 2 秒的校时会保守停批；这是已知可用性限制。墙钟减 uptime 是有容差的会话门，不是加密强度的开机身份；相差不超过容差的变化按规格放行。
- 原套件 F 组任意异常可计 caught 的旧边界未扩写为新 BOOT 测试；独立复验应专门检验变异与两向对照。
- 原共享候选可能仍被外部工作流使用，因此本轮仅交付独立候选，未自行集成。

## 最终测试结果

- `python candidate/_drive_c2_x_e12.py --selftest`：真实 **rc=0，95 项红=0**，原 82 项保留，新增 BOOT 13 项；完整输出 `repair_selftest.txt`。
- `python candidate/_drive_c2_x_e12.py --live`（未给 approved）：真实 **rc=3**，输出 `repair_live_refusal.txt`。
- 母版不符/不可读拒载由 E-02/E-03 覆盖，两冻结依赖副本和原件哈希均未变。
- 候选驱动 SHA-256：`75daf4f7358996aa0af1aa1454b63bed6156826a7c047f784b3e9d997a652901`。
- 候选自检 SHA-256：`95e365aae0c339820e6a4584af58e95199bcc402b81f68e1d5a381dec18b025c`。
- 冻结早窗依赖：`2e970eec43fe37ff02cab98e71bce9c764d11d758ab2a7b31b495100d109c2e1`。
- 冻结 v2 依赖：`6afe2711136c3b52344cd435f6dbd64508378a1e019c552228ff4f5e653d13b9`。
- 候选完成后现读共享源驱动仍 `f9d3f36a…89be`、共享源自检仍 `731dedfc…bfcfb8`，无漂移。
- 本结果只是制作方自证，独立复验未在本报告中冒充完成。
