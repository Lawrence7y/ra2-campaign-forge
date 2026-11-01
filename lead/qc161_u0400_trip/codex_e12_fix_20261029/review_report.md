# E12 BOOT 修复独立复验记录

状态：**候选离线质量门通过，可提交原发射 Leader 预检**。复验者为独立新上下文；全程离线。本判定不替代真机授权、本机预检或 RC-4 行为验收。

## 原件基线（独立实测）

- 原驱动 SHA256：`f9d3f36a543d995ffd36d1305afb2b9c0336b6a40111e9a37e168b725d9e89be`。
- 短 TEMP/TMP=`D:\Project\ra2-campaign-forge\.e12tmp_review`，命令 `python -B lead\qc161_u0400_trip\_drive_c2_x_e12.py --selftest`：真实 rc=0，82 项，红=0。证据：`review/baseline_shorttmp_selftest.txt`。
- 长 TEMP 的独立 `trip_once('hang')` 探针：phase=`mkdir`、verdict=`FAIL`、fail=`carrier_pathlen`；生产 CARRIER_PATH_MAX=130。证据：`review/baseline_longtmp_probe.txt`。因此早先 `KeyError: latch_row_index` 掩盖了首次 rec.fail，不能归因 BOOT 修复或通过放松路径闸解决。
- 冻结母本现读：v2=`6afe2711136c3b52344cd435f6dbd64508378a1e019c552228ff4f5e653d13b9`；earlyclose=`2e970eec43fe37ff02cab98e71bce9c764d11d758ab2a7b31b495100d109c2e1`。基线全自检末尾亦报告两者未变。

## 计数核对

§466 的有效协议样本公式是旧 P3e 3 趟 + 新 T1 1 趟 = 当前 4 趟。若目标总 n=5，则尚需 1 趟有效样本；T2 未启动游戏，不计有效趟。正文“还需2趟/修复后 --trips 2”与自身括号公式冲突，需要 Leader 追加勘误并明确实际剩余范围。本复验不作真机授权。

## 既有套件的诚实边界

原 F 组 `_run_mutations` 对任何 `Exception` 均记 caught=True；因此变异汇总通过不能单独证明目标断言被精确杀死。新 BOOT 复验必须另外检查正例、重启反例及精确失败原因，排除 KeyError/IndexError 等旁路异常冒充成功。

原 `main_suite` 首个 A-01 在前置失败时仍索引 latch 字段，导致 KeyError 掩盖真正 rec.fail；这影响失败诊断，不代表生产路径闸错误。候选增加首次失败的 `FIRST_TRIP_FAILURE` 明示并返回 1，未放松生产路径闸。

## 候选复验

被复验候选目录：`lead/qc161_u0400_trip/codex_e12_fix_20261029/candidate/`。

- 驱动 SHA256：`75daf4f7358996aa0af1aa1454b63bed6156826a7c047f784b3e9d997a652901`。
- 自检 SHA256：`95e365aae0c339820e6a4584af58e95199bcc402b81f68e1d5a381dec18b025c`。
- 依赖副本分别为冻结母本原哈希；独立复验前后四文件哈希完全相同，证据 `review/candidate_hashes_before.txt`、`review/candidate_hashes_after.txt`。
- 源路径原件仍为 `f9d3f36a…`，本次没有覆盖源件。不得把源路径命令误当已修复候选命令。

### 独立亲跑命令与结果

均设置 TEMP/TMP 为独占短临时域 `D:\Project\ra2-campaign-forge\.e12tmp_review`、`PYTHONIOENCODING=utf-8`，不改变生产路径上限。

1. `python -B lead\qc161_u0400_trip\codex_e12_fix_20261029\candidate\_drive_c2_x_e12.py --selftest`：**真实 rc=0，95 项红=0**，日志 `review/candidate_selftest.txt`。
2. `python -B lead\qc161_u0400_trip\codex_e12_fix_20261029\review\independent_boot_review.py lead\qc161_u0400_trip\codex_e12_fix_20261029\candidate`：**真实 rc=0，16 项红=0**，日志 `review/independent_boot_probe.txt`。此脚本使用夹具的替身 OS，但时钟参数、可观察 mock popen 计数、判据和变异由复验者独立构造，不调用制作方 `_boot_regressions` 充当独立结果。

### 逐项判定

| 项目 | 判定 | 亲验证据 |
|---|---|---|
| 完整候选自检 | CONFIRMED | 95 项红=0，真实 rc=0；旧 82 个检查 ID 全保留、新增 13 个，见 `review/suite_ids_and_hash_audit.txt` |
| 同会话双趟实际走到判据 | CONFIRMED | 自有时钟下 `run_trip(971/972)` 均 OK；插入 137 秒推进；mock popen 恰 2 次；uptime 从 1200000 增至 1346231；批次 reference 未改 |
| 重启反例发射前拦停 | CONFIRMED | 同一 reference 下将 uptime 变为 1000；`run_trip(973)` 返回 FAIL，精确原因 `stop_condition:boot_changed_between_trips`，mock popen 总数仍 2，无第三次 |
| ±2 秒容差 | CONFIRMED | -2001/+2001 拦；-2000/-1999/0/+1999/+2000 放；异常必须为 TripFail 且匹配 boot_changed 前缀 |
| 回退旧 raw 比较变异 | CONFIRMED | 独立内存变异后，同会话被误拦且等 raw uptime 的重启反例被漏拦；正反例明确区分旧缺陷，不用任意异常冒充抓红 |
| 删除检查变异 | CONFIRMED | 独立内存变异 `if False` 后重启不被拦，精确抓出保护被删除 |
| `--live` 无 `--approved` | CONFIRMED | 真子进程 rc=3，输出需批准；没有运行 `--live --approved` |
| 母版哈希门 | CONFIRMED | 在自建临时目录逐一改 v2/earlyclose 的副本；两次真子进程均 rc=1，stderr 为对应 `frozen_master_mismatch` RuntimeError，未改源件 |
| 原始 uptime 取证保留 | CONFIRMED | 两趟 rec 保留 `boot_ms_at_start`，另附 wallclock、估计开机时刻、reference 和 tolerance |
| 其他断言和逻辑未弱化 | CONFIRMED（限定本差分） | 独立 AST 对照：原函数零删除；9 个原函数完全一致；仅 extend_ops_real/run_trip/extra_preflight/main 改动，逐处为 BOOT seam/判据/附加取证/文案与参考捕获；E2、交互、finalize、授权闸逻辑保留。见 `review/ast_function_audit.txt` |
| 冻结两母本和原驱动不变 | CONFIRMED | 复验结束后现读源两母本仍 6afe2711/2e970eec、原驱动仍 f9d3f36a；候选四文件前后相同 |
| 真机修复效果 | UNVERIFIED | 本轮严格离线，未启动游戏；此处只修 BOOT 跨趟误拦，不证明退出挂死已修复 |

### 结论与限制

未发现需要回修的候选红项。候选保留“同批次开机会话一致”意图，以每趟重新读取 wallclock-uptime 的估计值对照固定批次参考，而非每趟重置参考或删除检查。超过容差的墙钟校正会保守停批；它不是强身份认证级的开机会话 ID，该边界已在代码注明。

可以把上述固定哈希候选交给原发射 Leader 进行本机预检、源件/依赖一致性核对和剩余样本账务修正。本复验不覆盖外部 `dwfrun-6a7ff2e3` 的状态，不替其宣布成功；不授权真机、不自动集成源件、不给 `--trips 2` 新增授权。按当前 n=5 目标的算术尚缺 1 个有效协议样本，需 Leader 追加勘误后按既有批准范围串行执行。
