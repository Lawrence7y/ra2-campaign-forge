# E12 离线修复与独立复验（2026-10-29）

## 授权与职责

本轮仅离线修复和复验；真机再发由用户/原发射 Leader 串行执行。修复者 `e12_repair`、独立复验者 `e12_review`、本会话协调者分别使用不同上下文，均继承本会话默认模型，无外部供应商切换。

DSH Bridge 的 status/models 调用均返回“只允许连接本机 DSH HTTP 地址；登录态不能发往其他机器。”未变更连接配置，未对未知状态的 `dwfrun-6a7ff2e3` 重发或取消。新修复限定在本目录 `candidate/`，避免与原工作流争写源件。

## 实测基线

- 原驱动 SHA-256：`f9d3f36a543d995ffd36d1305afb2b9c0336b6a40111e9a37e168b725d9e89be`。
- 原自检 SHA-256：`731dedfc2c09c11e9265aa9a7280fb9395e3da8831d3949f57c56d4d24bfcfb8`。
- 默认临时目录首次运行 rc=1（临时目录拒写）；工作区长临时目录运行及正常权限复跑仍 rc=1（载体路径长度闸触发，随后报告出现 `KeyError: latch_row_index`）。后两次日志分别为 `baseline_selftest.txt`、`baseline_selftest_unsandboxed.txt`。
- 使用工作区短临时目录 `.e12tmp_base` 重跑原命令 `python lead/qc161_u0400_trip/_drive_c2_x_e12.py --selftest`：真实 **rc=0、82 项、红=0**。完整输出 `baseline_selftest_shorttmp.txt`。前述环境失败不替代此可复现基线，不通过放松生产 130 字符路径门绕过。
- 冻结 v2：`6afe2711136c3b52344cd435f6dbd64508378a1e019c552228ff4f5e653d13b9`。
- 冻结 earlyclose：`2e970eec43fe37ff02cab98e71bce9c764d11d758ab2a7b31b495100d109c2e1`。

## 已发现的账务矛盾（不改历史）

§466 同时出现“还需2趟”与“旧3+新T1+待发1=5”。若 E1 目标仍为该协议总 n=5，则当前旧3+T1=4，仅剩1个有效样本。`5/8` 是另一并趟计数轴，不作为 n=5 队列的分母。再发前由原发射 Leader 根据最终授权和有效样本账纠正剩余数量；本轮不发射，不执行 `--live --approved`。

## 回收门槛

修复报告与独立复验报告必须记录实际命令、真实 rc、断言数量、正反例、变异及固定哈希。未知或未跑项目保持 UNVERIFIED。候选通过不等于真机通过，也不表示 RC-4 收口。

## 最终回收

- 修复者：候选完整 `--selftest` 真实 rc=0，95 项红=0；无授权 `--live` 真实 rc=3。见 `repair_report.md`、`repair_selftest.txt`、`repair_candidate.diff`。
- 独立复验者：候选完整 `--selftest` 真实 rc=0，95 项红=0；自有探针真实 rc=0，16 项红=0。见 `review_report.md`、`review/candidate_selftest.txt`、`review/independent_boot_probe.txt`。
- 独立正反例实跑到 `run_trip`：同会话两趟推进137秒均通过且批次参考不变；模拟重启在 mock popen 前精确拒绝；双向2000ms边界通过，2001ms拒绝；旧raw比较及删除检查变异均被区分性正反例抓出；两个冻结母版分别改副本均拒载。
- 候选驱动 SHA-256：`75daf4f7358996aa0af1aa1454b63bed6156826a7c047f784b3e9d997a652901`。
- 候选自检 SHA-256：`95e365aae0c339820e6a4584af58e95199bcc402b81f68e1d5a381dec18b025c`。
- Leader最终实读：共享原驱动/原自检仍为基线 `f9d3f36a…`/`731dedfc…`，两冻结母版仍为 `6afe2711…`/`2e970eec…`，没有覆盖、部署或真机发射。

结论：**独立候选离线质量门通过，可提交原发射 Leader 预检。** 本交付不证明真机退出修复成立。共享原路径仍是旧算法；需要使用本目录 `candidate/_drive_c2_x_e12.py` 或在确认原工作流停止写入后按 diff 审核集成，不能误用原路径再发。若用本候选做离线自检，TEMP/TMP须指向短的已授权目录，否则夹具会被生产130字符路径闸保守拦截；不得为测试便利放松该闸。

会话门的限制：墙钟校时超过2秒会保守停批；±2秒估计不是精确的开机身份凭证。本轮没有重派R-063静态支线，没有改变其他工作流或历史台账。
