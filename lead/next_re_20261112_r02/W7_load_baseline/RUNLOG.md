# RUNLOG.md —— W7 RE-N03 执行日志

- run_id: `NEXT_RE_20261112_R02`；卡片：RE-N03（T1 载体稳定性 / T2 候选代理量 / T3 H1 分层）
- 开始：2026-11-13T01:06+08:00（侦察）；结束：2026-11-13T01:4x+08:00（成文）
- 执行者：W7-load-baseline-subagent（实例锁自 01:07 起持有，收尾已恢复 owner=lead）
- 仓库：`D:\Project\ra2-campaign-forge` @ main 3872ef6（未做任何 git 写操作）
- 探针：`load_baseline_probe.py`（--run 1/2/3 单趟可重跑；--analyze 离线汇总）

## 1. 时间线

| 时刻(本地) | 事件 |
|:--|:--|
| 01:06–01:15 | 侦察：读锁/W1/W6/W3、基线 TSV、H1 定位（文件名/内容/指纹三路搜索）、ProvingGrounds 载体哈希复核（`3e3c8745…` = 卡片值）；抢锁 owner=W7-load-baseline-subagent |
| 01:17 | 写 `load_baseline_probe.py`（v1：mode!=5 门控，按任务卡事实 5） |
| 01:17–01:21 | **首趟 run1（v1 门控）**：选图成功（index 265，`[8] Proving Grounds`，268 条目，1 命中，0 空名），StartGame 后 mode 恒 5 达 180s 超时 → 按失败收尾（配置还原、残留 0）。数据存档 `out\archive_rejected\run1_modegate_rejected.*` |
| 01:21–01:26 | **定性**：W6 存档 `W_A_ingame` 431 拍 mode 全 5 且 frame 推进 → 事实 5「局内非 5」与 W6 自身数据矛盾；mode 区分不了加载/局内。改速率门控（≥28 计数/s 持续 5s 且 elapsed≥15s）。v1 数据留档为修正证据 |
| 01:26–01:29 | **run1（v2）**：exit 0，battle_rate_detected @20.03s，局内 2457 拍；残留 0，配置还原 |
| 01:29–01:32 | **run2（v2）**：exit 0，@20.03s，2456 拍；残留 0，配置还原 |
| 01:32–01:34 | **run3（v2）**：exit 0，@20.03s，2457 拍；残留 0，配置还原 |
| 01:34–01:39 | `--analyze` 汇总 + T2 细节挖掘（B0CE88 脉冲段、87E8E0 计数轨迹、ABCD58 闩核验、loading 逐秒速率曲线） |
| 01:39– | 成文：LOAD_BASELINE / H1_LAYERING / SAFETY / CONFIG_RESTORE / RUNLOG / UNCOVERED；恢复锁 |

## 2. 三趟开工前哈希（①摘要）

三趟开工前 5 文件实算 SHA-256 与 `PRE_LAUNCH_BASELINE.tsv` 全部一致（RA2MD.INI `c91c6a47…`、ddraw.ini `c983abad…`、RA2MD.INI.benchbak `c91c6a47…`、gamemd.exe `73201cc0…`、ddraw.dll `85e0f7d5…`）；启动前 gamemd 残留均为 0。

## 3. 关键命令

```text
python -X utf8 load_baseline_probe.py --run 1   # ×3（run 1/2/3）
python -X utf8 load_baseline_probe.py --analyze
```

被误杀首趟的 stderr/数据：`out\archive_rejected\run1_modegate_rejected.ndjson`（5895 拍 mode=5、frame 5→5630 @31.249/s）、`…_meta.json`（error=load_timeout_still_mode5）、`…_stdout.txt`。

## 4. 收尾核对

- 三趟各自独立收尾：残留 0；RA2MD.INI / ddraw.ini / RA2MD.INI.benchbak 逐字节还原（自证哈希一致）；gamemd.exe/ddraw.dll 未改证实。
- 全卡收尾：实例锁恢复 `owner=lead`；最终 `Get-Process gamemd` 残留 = 0（01:4x 实查）。
- 游戏写回：每趟仅 `RA2MD.INI`（已还原）；无其它新增/删除。

## 5. 结论索引

- T1 载体可用性判定：`LOAD_BASELINE.md` §1–§3（3/3 通过，速率 31.24–31.25 计数/s 区间口径）
- T2 候选代理量现象表：`LOAD_BASELINE.md` §2（A8ED50 恒 0 / B0CE88 脉冲 / 87E8E0 会话计数器；全部语义未定）
- T3 H1 分层：`H1_LAYERING.md`（类 1 文件未发现 + 历史 §5 衔接）
- 门控修正（mode 语义）：`LOAD_BASELINE.md` §0
