# RUNLOG · W18 RE-N04g（高建筑载体 B′ HexBay 负载对照）

run_id `NEXT_RE_20261112_R02` ｜ 卡 RE-N04g ｜ 2026-11-13 05:28–05:52+08（Asia/Shanghai）

## T0 开工核对（05:28–05:35）

1. 锁 `owner=lead` 可认领；`Get-Process gamemd` 残留 = 0。
2. 载体核对：`ra2youli\[8]黑心湾_HexBay.yrm` = **355,713 B** ✓，sha256 开工实算 `cb6c5224…529d` 钉定入探针；离线实读 `[Basic].Name = "Hex Bay (2-8)"`（GBK，[Basic] 段偏移 58,922）、Official=no、MaxPlayer=8/MinPlayer=2、GameMode=standard、`[Structures]` 逐行实算 **144**、含 `[Triggers]` ✓。
3. **撞名预检**：W17 实测名单 `W17_load_B\out\maplist_names.json`（268 条）中 `Hex Bay` 仅命中 **索引 267 一条**（`Tiger Bay Night`@119、`Pirate Bay (2)`@127 均非同名）→ 唯一，无取舍问题，无需停手上报。
4. 仪器改造：`make_w18_from_w17.py` 有序替换生成 `load_hexbay_probe.py` / `load_hexbay_ui_watch.py` / `analyze_hexbay.py`（换载体钉定、map-patterns、关键词探针、卡名、判据文案 `[B′ 不可用]`；docstring 整块重写），三文件 `py_compile` 通过。转换过程中修正三处自身 bug（替换顺序依赖、docstring 边界定位、兜底替换超集），转换可复现。
5. 启动前二次核对：锁 owner=lead、gamemd 残留 0。

## attempt1（05:35:03 启动，WMI cmd_pid=39692）

- S0：锁认领 `owner=W18-load-HexBay-subagent`；残留 0；五文件哈希全 match；载体 355,713 B / sha 一致；清单 647 项。
- S1：pid=44120、is32=True、代码签名 @0x55DE4F ok；主菜单就绪 18.0 s；窗口 hwnd=32116528、tid=22032；初始线程扫 n=32。
- S2：SinglePlayer→Skirmish→ChooseMap，ListBox **268 条**，全名单落盘 `out\maplist_names.json`（与 W17 逐条一致）；模式 `Hex Bay (2-8)` **精确命中 1 个**（索引 267），空名 0；LB_SETCURSEL(267)→UseMap。
- S3：置前成功（开局阶段最后一次输入）；StartGame 点击。
- S4：观察者独立启动（cmd_pid=44404）；timeBeginPeriod(1)=0；**StartGame 后 5.690 s 首个 frame>0**（frame=2）；240 s @ 6 ms 采样，n_resync=0，进度帧率 31.25 计数/s 稳定。
- 05:39:43.84 采样段结束 `reason=target_reached`，有效局内段 **240.006 s**，seq=40,881。
- finally 自愈全链：观察者 0.01 s 退出 → WM_CLOSE→taskkill→taskkill /F → 存活=False → 残留 0 → 配置三文件逐字节还原自证 True → 清单 647→647 → meta_end → **锁恢复 owner=lead**。exit_code=0。

## T1 分析（05:41–05:52，未再启动游戏）

1. `analyze_hexbay.py` 首跑成功：进图 entered=True；cycle 每拍中位 1.767 ms；占用率 5.67%；TIER=[无显著差异]。
2. **★ 标定口径勘误（本卡新发现）**：首跑输出 `cyc_per_ms_B=3.311e6 cyc/ms` 与卡面引用的 A 系数 `3.104e9 cyc/ms` 比值 0.0011，暴露**卡面单位错误**——3.104e9 实为 **cyc/s**（≈3.104 GHz 时钟频率），正确 cyc/ms 口径 = 3.104e6。W15/W17 判读均用各自全段自标定（ms 口径），**结论不受影响**；仅 `cyc_ms_A_factor` 旁证列偏小 1000 倍。
3. 分析器修正（除数 3.104e6 + 勘误说明写入 `analysis.json.cycle_calibration`）后重跑：ratio_B_over_A_corrected = **1.0667**（B′ 标定频率 ≈3.311 GHz，turbo 状态差异，正常）；全部判读数值不变，TIER 仍 `[无显著差异]`。
4. 监控器工具 bug（如实记录，不影响探针）：首个后台监控 job 用 `[System.IO.File]::ReadAllLines` 读 `run.ndjson` 无共享读权限，被探针写句柄挡住（IOException）→ 误判"60 s 无增长"提前退出；**探针采样本身正常**。重起监控（`Get-Content` 共享读）后正常轮询至 meta_end（05:40:04）。

## 结论分档

**`[无显著差异]`**（cycle 每拍中位 1.767 ms = A×1.045；占用率 5.67% = A×1.052；均 <20% 阈值；进图 240.006 s 有效段）。单趟成功，无重试。

## 产物

`load_hexbay_probe.py`（可重跑；--map-patterns/--target-seconds/--interval-ms 旋钮）、`load_hexbay_ui_watch.py`、`analyze_hexbay.py`、`make_w18_from_w17.py`、
`out\run.ndjson`（40,950 行 = meta 1 + sample 40,934 + event 12 + thread_sweep 2 + meta_end 1）、`out\meta.json`、`out\tickcost.csv`（7,501 行）、`out\analysis.json`、`out\maplist_names.json`、`out\ui_watch.ndjson`（435 行）、`out\state.json`、`out\probe_live_stdout.txt`、`out\analyze_stdout.txt`、
`LOAD_HEXBAY.md`、`SAFETY.md`、`CONFIG_RESTORE.md`、`RUNLOG.md`（本文件）、`UNCOVERED.md`。
