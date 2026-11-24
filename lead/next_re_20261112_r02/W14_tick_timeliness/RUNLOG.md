# RUNLOG · W14 RE-N04d（单趟）

- 04:01:05 代理抢锁 owner=W14-tick-timeliness-subagent；gamemd 残留 0；载体哈希实算一致。
- 04:01:11 探针经 WMI 独立启动（cmd_pid=39056，父=WmiPrvSE）；S0 守卫全过
  （锁 self_held / 残留 0 / 5 文件哈希 match / 载体钉定一致 / 清单 647 项）。
- 04:01:12 pid=2236（wmi_child_parent_pid），is32=True，代码签名@0x55DE4F ok。
- 04:01:30 主菜单就绪（18.0 s）。
- 04:01:40 选图：ListBox 268 条，模式 `Proving Grounds` 唯一命中 idx 265
  `[8] Proving Grounds`，空名条目 0。
- 04:01:44 置前成功（最后一次输入）；StartGame 点击；观察者经 WMI 独立启动
  （cmd_pid=2840→watcher pid=44608）；timeBeginPeriod(1)→0；探针 BELOW_NORMAL。
- 04:01:49 首个 frame>0（frame=2，StartGame 后 5.240 s）⇒ 采样计时起点。
- 04:01:49–04:05:49 采样 240.0 s @6 ms 目标：40,806 拍，读失败 0，n_resync=0，
  每个进度点 fg=True；frame 2→7502（31.2492 计数/s）。
- 04:05:49 target_reached 停止；写观察者停机文件；WM_CLOSE 游戏窗（局内弹确认框，
  6 s 未退）→ taskkill /PID 2236（无 /F，rc=0）→ taskkill /F（rc=0）→ 进程退出。
- 04:06:02 观察者退出确认（0.02 s，reason=stop_file）；残留 0；清单 647/647
  （changed=1=RA2MD.INI，游戏自身改写）；三配置逐字节还原自证；锁恢复 owner=lead；
  meta_end 写入（exit_code=0）。NDJSON 40,872 行。
- 04:06–04:09 代理离线复算 analyze_ticks.py；终态再核（RA2MD.INI/ddraw.ini 实算
  match、gamemd=0、锁 owner=lead）。

## 已知缺陷（均化妆级，不影响数据与结论）
1. **taskkill 输出 GBK 解码失败**：`subprocess capture_output text=True`（W13 原样继承）
   的 reader 线程对中文系统 taskkill 输出抛 UnicodeDecodeError → stdout/stderr 捕获为空
   （`out=''`）。taskkill rc=0 两次均已验证、进程确认退出。仅日志缺 taskkill 文本。
2. **meta 字段陈旧**：`meta.watcher.state_reads_ok/fail` 保持初始化的 0；真实计数
   在 `meta.sampling.watcher_state_reads_ok=270 / fail=1`（1 次失败是 state.json
   建立前的首个读点，符合预期）。字段放错位置，数据无损。
3. **目录元数据缓存**：轮询期 `Get-ChildItem Length` 对活动写入文件显示陈旧值
   （如 run.ndjson 显示 18 KB）；以 `Get-Content` 实读为准（终值 15,745,742 B）。
4. 代理侧一次轮询 Start-Sleep 130 s 超过 pwsh 默认 120 s 转入后台 job；
   已 job_output 取回（exit 0），无进程遗留。

## 复算入口
`python -X utf8 analyze_ticks.py`（对 out\run.ndjson 全量重算，输出
analysis.json / increments.csv / stdout 摘要）。
