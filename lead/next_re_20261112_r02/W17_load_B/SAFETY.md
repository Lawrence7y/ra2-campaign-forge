# SAFETY · W17 RE-N04f

run_id `NEXT_RE_20261112_R02` ｜ 两趟 attempt（1/2）均在选图阶段失败收尾，自愈链两趟完整执行。

## 授权边界（卡面）
- 允许：启动 `ra2youli\gamemd.exe`、只读 `ReadProcessMemory`、`OpenThread`+`GetThreadTimes`/`QueryThreadCycleTime`、枚举窗口与线程、发消息/点控件（仅导航/选图/开局阶段）。
- 禁止（未触碰）：SuspendThread / StackWalk64 / MiniDump / 断点 / 注入 / 写目标进程内存 / 改 exe / dll / hook；增删改 `ra2youli` 文件（配置还原除外）。
- 采样段零输入：本卡未进入采样段（未到 StartGame），导航点击均在允许阶段；无键鼠注入（`PostMessage` BM_CLICK 与 `LB_SETCURSEL` 仅导航用）。

## 进程与实例互斥
- 每趟启动前 `list_gamemd()` 残留检查：attempt1/2 前均为 0（代理侧亦实核 `Get-Process gamemd` = 无）。
- 实例锁：开工认领 `owner=W17-load-B-subagent`（attempt1 于 05:06:40、attempt2 于 05:08:46+08 附近），收尾恢复 `owner=lead`（两趟均成功，`lock_restored=True`）。
- 探针/游戏/观察者全部经 `Invoke-CimMethod Win32_Process Create` 启动，脱离代理进程树（代理结束不杀探针）。

## 实际执行的动作清单
1. WMI 启动探针（脱离）×2；探针内 WMI 启动 gamemd.exe ×2、WMI 启动观察者 0 次（未到采样段）。
2. UI 导航：SinglePlayer → Skirmish → ChooseMap → 读列表（LB_GETCOUNT/LB_GETITEMDATA + RPM 名称串）→ 失败。
3. 收尾：WM_CLOSE → taskkill（无 /F）→ taskkill /F（attempt1 对 pid 43632；attempt2 对 pid 39956）→ 残留核对 0。

## 数据与写域
- 写域仅 `W17_load_B\`（本卡文件 + out\）+ 实例锁（授权例外）。未写仓库其他目录；未 git 操作。
- 只读过：`ra2youli\*.yrm`（离线解析 [Basic]）、`W15_tick_cpu\`、`W16_map_census\MAP_CENSUS.tsv`、`baseline_pre_launch\`。

## 风险与偏差记录
- attempt1 收尾 `taskkill /F` 生效（WM_CLOSE 后游戏未退；对局未开始，强杀无进度损失）。
- 未发生：读失败、窗口线程查询失败、观察者异常（观察者未启动）、焦点丢失段、帧回退。
- 探针崩溃遗留风险：`finally` 链覆盖（两趟验证）；若探针进程本身被杀，残留检查在代理侧兜底（本卡未触发）。
