# A'' 重启后执行手册 v2 ·2026-11-01——依用户七点修正重写；用户重启+告知后按序执行；暂不加趟

> **v2 变更（对 v1）**：① BOOT 身份=单调源（GetTickCount64 P/Invoke，2026-11-01T10:58 实测验证）
> 与墙钟**分列记录**，**撤回 v1「双钟三列等效」表述**（v1 未实现独立单调时钟）；② 冻结锚扩展至
> launcher/judge/轨迹分析件/地图/配置+argv 全文；③ 每命令显式工作目录（绝对路径，不依赖前步
> cd 生效）；④ 分析脚本用**版本化副本**，重启前原实现与原输出保留不动；⑤ 首趟仅 v4-d 筛查，
> **第二趟不自动发射**（由首趟有效性与新增信息决定，用户批准）；⑥ §507 补记限定已入台账
> （采集计数与解析吻合；读失败=0≠观测伪影全排除）；⑦ 混杂前置声明（重启前基线已自然改善）。

## 前提（硬闸）
- 用户本轮明确告知「已重启」；E3 未授权维持；RC-4 不收口；①机制未闭合口径不变。
- 授权范围=runbook 各步在既有 A'' 授权边界内；任何超界（E3/加趟/改参数）另行请示。

## 步 0｜BOOT 身份核对（单调源与墙钟分列；任一不符即停，向用户核实）
工作目录 `D:/Project/ra2-campaign-forge`（Git Bash；`\$` 为 Bash 转义，PowerShell 原生会话免）：
```
cd "D:/Project/ra2-campaign-forge" && powershell -NoProfile -Command "Add-Type -Namespace W -Name K -MemberDefinition '[DllImport(\"kernel32.dll\")] public static extern ulong GetTickCount64();'; Write-Output ('TICK64_ms=' + [W.K]::GetTickCount64()); \$os = Get-CimInstance Win32_OperatingSystem; Write-Output ('BOOT_TIME=' + \$os.LastBootUpTime); Write-Output ('UPTIME_ms=' + [long]((Get-Date) - \$os.LastBootUpTime).TotalMilliseconds); Write-Output ('WALL=' + (Get-Date -Format o))"
```
- 判定：`BOOT_TIME ≠ 2026/10/31 8:26:27` ⇒ 已离开 BOOT#5；UPTIME_ms 应 ≪ 95.5Mms（26.5h）。
- 记录：TICK64_ms（单调轴）与 UPTIME_ms/BOOT_TIME/WALL（墙钟轴）**分列如实**；两者差 ~1.6s=
  开机时钟粒度（2026-11-01T10:58 实测 TICK64=95509968 vs UPTIME=95511537），**不宣称同轴/等效**。

## 步 1｜post 环境快照（对齐 pre 快照格式，同文件式追加落盘）
```
cd "D:/Project/ra2-campaign-forge" && { powershell -NoProfile -Command "Write-Output ('=== POST-REBOOT ENV SNAPSHOT ' + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss') + ' ==='); Write-Output ('WALL=' + (Get-Date -Format o)); \$os = Get-CimInstance Win32_OperatingSystem; Write-Output ('BOOT_TIME=' + \$os.LastBootUpTime); Write-Output ('UPTIME_ms=' + [long]((Get-Date) - \$os.LastBootUpTime).TotalMilliseconds); systeminfo"; powershell -NoProfile -Command "Get-Process | Sort-Object WS -Descending | Select-Object -First 40 Name,Id,WS | Format-Table -AutoSize | Out-String -Width 200"; } > "D:/Project/ra2-campaign-forge/lead/codex_round_20261030/LEADER_battle/env_snapshot_post_reboot_20261101.txt" 2>&1
```
（TOP40 命令形态 2026-11-01 实测验证；systeminfo 与 tasklist 面同 pre 快照轴。）

## 步 2｜冻结锚复验（扩展清单 v2=母本八件+本轮五件+配置两件；先 pre 锚落盘，趟后复验对照）
```
cd "D:/Project/ra2-campaign-forge" && sha256sum lead/goal1_harness7_20261023/qc151_trip.harness7.py ra2youli/gamemd.exe lead/goal1_harness8_20261031/qc151_trip.harness8.py lead/goal1_harness8_20261031/qc151_trip.harness8_v3.py lead/goal1_harness8_20261031/qc151_trip.harness8_v4.py lead/qc161_u0400_trip/codex_e12_e5_20261030/candidate/_drive_c2_x_e12.py lead/qc161_u0400_trip/_drive_c2_x_probe_v2.py lead/qc161_u0400_trip/_drive_c2_x_earlyclose.py lead/goal1_harness8_20261031/_launch_h8v4_20261101.py lead/goal1_harness8_20261031/_judge_h8v4_20261101.py lead/codex_round_20261030/LEADER_battle/_h8_waittrace_decomp.py out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/_src_L3_sf10c_20261021/XMP29U2.MAP out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/_src_L3_sf10c_20261021/ddraw.ini out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/_src_L3_sf10c_20261021/RA2MD.INI ra2youli/ra2md.ini | tee "D:/Project/ra2-campaign-forge/lead/codex_round_20261030/LEADER_battle/frozen_recheck_v4d_pre.txt"
```
- 期望锚（2026-11-01 实测）：launcher `d3b2e8c12a8c…`、judge `75303c296145…`、分析件
  `d27f676e252e…`、地图 `f3bb0a4e…`、载体 ddraw.ini `95949842…`、载体源 RA2MD.INI `0cc65385…`、
  母本 ra2md.ini（ra2youli/）`2ccf13c2…`；母本八件=frozen_recheck_v4.txt 逐位。
- **argv 完整记录**：发射后以 `l3_1101v4d/_launch_result.json` 的 `argv` 全文为 argv 锚
  （v4-b/c receipt 同格式已核：尾部=`--evid-diff --probe-frames 3900,4200,…,6000
  --h7-measure-start-frame 800 --h8-wait-trace`）。
- 配置注（B 席勘误②口径）：GameSpeed=2 语义归属=母本 ra2md.ini 口径源，趟级锚定受限；
  载体源 RA2MD.INI 并列锚定，语义归属不改判。

## 步 3｜v4-d 发射（单趟筛查；第二趟不自动发射）
```
cd "D:/Project/ra2-campaign-forge/lead/goal1_harness8_20261031" && python -I -X utf8 _launch_h8v4_20261101.py --suffix d --extra-argv "--h7-measure-start-frame 800 --h8-wait-trace"
```
- launcher 自补 `--measure 1 --fullscreen --evid-diff --probe-frames 3900,…,6000`；
  产物=`out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_1101v4d/`。
- **v4-e 不自动发射**：首趟有效性（轨迹三件套+窗可判）与新增信息量评估后**报告用户，由用户决定**。

## 步 4｜判档
```
cd "D:/Project/ra2-campaign-forge/lead/goal1_harness8_20261031" && python -I -X utf8 _judge_h8v4_20261101.py --trip-dir "D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_1101v4d"
```

## 步 5｜等待轨迹分解（版本化副本；原实现与原输出保留不动）
```
cd "D:/Project/ra2-campaign-forge" && cp "lead/codex_round_20261030/LEADER_battle/_h8_waittrace_decomp.py" "lead/codex_round_20261030/LEADER_battle/_h8_waittrace_decomp_v4d.py"
```
- 仅在**副本**内改 TRIPS 字典（指向 v4-d + v4-c 对照）；原件 `_h8_waittrace_decomp.py` 与原输出
  `waittrace_decomp_20261101.txt`（重启前实现+输出）保留不动。
```
cd "D:/Project/ra2-campaign-forge/lead/codex_round_20261030/LEADER_battle" && python -I -X utf8 _h8_waittrace_decomp_v4d.py > waittrace_decomp_v4d_20261101.txt 2>&1
```

## 步 6｜对照判读（§503 口径+C-1 分流+混杂前置）
- **混杂前置声明（用户第 7 点）**：重启前基线 v4-c（BOOT#5 内 09:41）已自然改善（§504 同 BOOT
  小时尺度振荡）⇒ 新 BOOT 的改善与 BOOT 内自然振荡**不可区分（时间混淆），归因力弱**。
- 结果口径：新 BOOT 零-低停滞 ⇒ **只支持「重启相关环境变化可能缓解」**（待重复与持续性验证）；
  仍滞 ⇒ **只说明「本次重启未消除」**（不得直接判持久软件态）；无有效窗/采样失效 ⇒ 无结论。
- 重启暂时缓解≠修复完成、**不改变 RC-4**；E3 不因此解锁；①机制未闭合口径不变。

## 步 7｜异上下文复算 ⇒ §508 入账
- 原始轨迹交不同上下文复算（A/B 席 occ_a+BOOT 锚定方法沿用）；引 §507 时用限定口径
  （采集计数与解析吻合；读失败=0≠观测伪影全排除）。

## 停止/回退
- 超时/短路 ⇒ 只报轨迹；趟后清场复验（carrier delete receipt 自动+T0/T1 zero-write 对照）；
  判别力下修背景（§504/§507）如实随结果附注；不加趟、不凑样本。
