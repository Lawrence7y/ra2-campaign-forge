# W94 · 批量真机矩阵运行器（batch_runner）使用说明

> 卡：W94（r06）｜离线实现卡：本卡实现 + 自测全程**未启动游戏**（真机锁当时归 W91：`.game_instance.lock` owner=w91）。
> 工具链来源：`W90_replicates\work\tools`（w90_run/offline/finalize/lib/common）与 `W88_envelope\work\tools\w88_build.py`，**已整卡复制进本卡再改**（`work\tools\w94_*.py`），从不跨卡 import。
> 时间戳：2026-11-14 16:20–17:0x（Asia/Shanghai，Get-Date 实测）。

## 0. 一句话

`batch_runner.py` 读一份矩阵 JSON → 逐格构建/安装/跑趟 → 每趟一个唯一证据包目录 → `batch_analyze.py` 汇总成 `SUMMARY.csv` + `SUMMARY.md`。矩阵层**只编排**，所有真机纪律都在被复制的单趟工具链里执行，矩阵层绕不过去。

```
python batch_runner.py  <matrix.json> [--dry-run] [--resume] [--pyexe PATH] [--trip-timeout-s N]
python batch_analyze.py [out_root] [--matrix <matrix.json>] [--out-dir DIR]
```

## 1. 矩阵 JSON 字段（完整）

```jsonc
{
  "run_id": "R07_matrix_demo",          // 必填；[A-Za-z0-9_-]，用于 plan/matrix_result 文件名
  "defaults": {                          // 可选；全部字段的格子级缺省
    "arm_template": "C6",                // 预设臂，见 §2；默认 "C6"
    "observe_sec": 150,                  // 采样目标秒（首个 frame>0 起算）；默认 155
    "min_valid_sec": 150,                // 有效窗下限（D2 判据）；默认 150
    "hard_cap_sec": 200,                 // 硬上限秒；默认 200
    "sample_ms": 6,                      // 采样节拍 ms；默认 6
    "render_channel": false              // 是否给每趟挂 W86 RPM 限帧放行通道；默认 false
  },
  "order": { "mode": "shuffle", "seed": 1234 },   // "fixed"（默认）或 {"mode":"shuffle","seed":int}
  "stop_on": ["engine_error_count>=2", "any_crash"],// 见 §4；缺省 = 不停，跑完全部
  "cells": [
    {
      "id": "c4",                        // 必填；[A-Za-z0-9_-]；不得以 _r<数字> 结尾（trip 目录名解析依赖）
      "overrides": {
        "enemy_mission": "Hunt",         // "Guard"|"Hunt"：三屋全体；展开成 hunt_all/hunt_british=0
        "hunt_british": 30,              // 最小剂量旋钮：仅 British 前 n 台 Hunt（与 Hunt 全开互斥）
        "napowr_step": 2,                // 2|3：NAPOWR 列间距（W88 C3 的「地基重叠」因子）
        "crewed": true,                  // true 时对构建产物地图追加 [NAPOWR] Crewed=no（W88 C4 口径，含同款 caveat）
        "observe_sec": 120,              // 格级时长旋钮（min_valid<=observe<=hard_cap 强制）
        "render_channel": true           // 格级渲染通道开关
      },
      "repeats": 3                       // 同格重复趟数；每趟唯一目录 trip_<id>_r1..rN；默认 1
    }
  ]
}
```

### 1.1 生效臂（effective arm）

`arm = ARM_PRESETS[arm_template] ← defaults 里的臂键 ← overrides 里的臂键`，归一化后为四元组
`{hunt_all, hunt_british, napowr_step, crewed}`，交给 `w94_build.py`（W85 绿基线几何 + W88 参数化，`Crewed` 覆盖照抄 W88 的"是否被规则库解析不可静态证明"备注）。

### 1.2 目录与文件布局（运行期）

```
W94_batchrun\
├── out\
│   ├── matrix_log.ndjson            矩阵全程事件（含实际执行顺序，逐行 JSON，append）
│   ├── plan_<run_id>.json           执行计划（含 shuffle 后顺序、每格生效臂）
│   ├── matrix_result_<run_id>.json  收尾汇总
│   ├── sandbox_game\                沙箱副本（一次性 FRESH 建立，矩阵运行器自己绝不 robocopy）
│   ├── sandbox_pre.json             建立时的全树 manifest（清理判定的唯一依据）
│   ├── specs\<cell>.json            每格臂规格（喂给 w94_build）
│   ├── inputs\<cell>\               D4：设计 JSON + 构建产物 + sha256
│   ├── BUILD_<cell>.json / OFFLINE_<cell>.json
│   ├── trip_<cell>_r<k>\            每趟证据包（唯一，永不复用）
│   │   ├── run.ndjson  TRIP_RESULT.json  installed_inputs\  archived_except*.txt
│   │   ├── wer_events.txt  archived_ndjson_tail.ndjson  TRIP_RESULT 顶部截图...
│   ├── aborted\<trip>_<ts>\         --resume 时被挪开的"未完成趟"目录
│   └── logs\<stage>.log             每个阶段子进程的 stdout/stderr
└── work\tools\w94_*.py              本卡私有副本工具链
```

## 2. arm_template 预设

| 模板 | hunt_all | hunt_british | napowr_step | crewed | 说明 |
|---|---|---|---|---|---|
| `C6`  | ✓ | 0 | 3 | — | 全 1200 敌军 Hunt + 无重叠地基（W88 包络臂） |
| `C2`  | ✓ | 0 | 2 | — | 全 Hunt + 重叠地基（阳性对照，崩预期） |
| `C1`  | — | 30 | 2 | — | 最小剂量 |
| `C7`  | ✓ | 0 | 2 | ✓ | 全 Hunt + Crewed=no（判 "车组刷新是否必要"） |
| `C0`/`CTRL` | — | 0 | 2 | — | 全 Guard 对照（零交战基线） |

注意：示例矩阵 `arm_template=C6` 下 `c2`（只给 `enemy_mission: Hunt`）与 `c3`（再给 `napowr_step: 3`）**生效臂相同** —— 运行器会打 `[warn] cells c2 and c3 have IDENTICAL effective arm+timing`（只警告不阻止；完全相同的格合法时就是"复制趟"）。

## 3. 每趟固定流程（矩阵层逐条执行，一条不省）

1. **锁**：`lead\next_re_20261112_r06\.game_instance.lock` —— 趟开始写 `owner=w94-batchrun` + 实测时间（`datetime.now().astimezone().isoformat()`），趟结束（try/finally，**崩了也写**）恢复 `owner=lead` 并记录 outcome 与残留进程数。写锁事件连同完整锁文件内容进 `matrix_log.ndjson`。
2. **启动前检查**：`tasklist gamemd.exe` 必须为空（趟内 `w94_trip.py` 用 Toolhelp32 再查一次）；沙箱必须已存在且是副本（`out/sandbox_pre.json` + `gamemd.exe` 存在；矩阵运行器**绝不**自己 robocopy，缺了就中止并提示先做一次 `W94_FRESH=1` 建立）。
3. **构建/安装**：每格构建一次（`BUILD_<cell>.json` verdict=PASS 则复用）；安装时若沙箱内三件套与格包 sha256 逐字节相同且 verify 过 → 短路跳过（重复趟不重装）。
4. **单趟**（`w94_trip.py` 子进程，复制自 W90 全纪律）：锁门禁（owner 必须 w94*）→ D4 输入归档（design JSON + `.MAP` + `BATTLEMD.INI` + `MAPSELMD.INI` + sha256）→ WMI 拉起**沙箱内** gamemd → 只读 RPM 采样（`observe_sec`/`sample_ms` 来自矩阵）→ D2 语义 → 关闭**只关自己拉的 pid** → 每趟 `RA2MD.INI`/`ddraw.ini` 逐字节还原 + 实算哈希自证。
5. **D1 崩溃取证**：检测到 `engine_internal_error_dialog` 或进程异常退出 ⇒ **立即**（任何清理之前）把沙箱根 `except.txt` 按 mtime/sha 区分 `fresh`/`pre_existing`（ra2youli 自带 2026-11-13 历史件）+ WER 事件 + ndjson 尾部复制进当趟目录；趟末还有 late 补拍安全网。
6. **清理**：趟内还原配置；**包卸载/差集清场**在整矩阵结束后由 `w94_finalize.py` 做（复制自 W90）：一切删除按 **sandbox_pre manifest 差集**判定，**禁止** `save*.sav` 类通配（W90 U4 教训：通配误删过基线 `SAVE0029.SAV`）。
7. **趟记录**：`TRIP_RESULT.json`（含 outcome/ok/sampling/engagement/d1_forensics）+ `matrix_log.ndjson` 的 `trip_start/trip_end`。

## 4. 停止条件（按格累计）

```jsonc
"stop_on": ["any_crash", "engine_error_count>=2", "any_defeat_count", "blocked_count>=1"]
```

- 语法：`any_crash`（= `crash_count>=1`）、`any_<metric>`（≥1）、`<metric>>=<N>`。无法解析/未知指标 ⇒ **计划期硬报错**（dry-run 就会拦下）。
- 指标（每格累计其**已完成趟**）：
  - `engine_error_count`：outcome 含 `ENGINE_ERROR` 或终态为引擎错误对话框；
  - `crash_count`：引擎错误 **或** `ABORTED_CRASH_*` 异常退出（故 `crash_count >= engine_error_count`）；
  - `defeat_count`：`*DEFEAT_DIALOG*`；`blocked_count`：`BLOCKED*`（如安装失败）；`fatal_count`：`FATAL*`；`nonvalid_count`：ok=false；`ok_count`：ok=true。
- 语义：**每趟结束后**对该格评估；命中 ⇒ 该格**剩余趟**全部记 `SKIPPED_STOP_CONDITION`，其他格继续。`--resume` 时已完成趟的 outcome 会重新计入累计值。
- 注意：卡面示例同时给 `engine_error_count>=2` 与 `any_crash`，而引擎错误计入 crash ⇒ 实际上 `any_crash` 会先触发、>=2 那条形同虚设 —— 示例按卡面保留，实际用时二选一。

## 5. 失败与崩溃时它怎么处置

| 情形 | 处置 |
|---|---|
| 趟内引擎错误/进程异常退出 | 趟runner先做 D1 取证再清理；outcome=`ABORTED_ENGINE_ERROR`/`ABORTED_CRASH_*`；矩阵层计 crash，按格触发停止条件 |
| 趟返回后仍有残留 gamemd | **整个矩阵停止**（后续趟记 `SKIPPED_RESIDUAL_GAMEMD`），matrix_log 记 `residual_gamemd_stop` + pid 清单；运行器**不做**一揽子 taskkill（只关自己拉的 pid 是纪律），留人工处置 |
| 安装失败 | 该趟记 `BLOCKED_INSTALL_FAILED`，计入 blocked_count；触发停止条件则跳过该格剩余趟 |
| 趟子进程超时（默认 900s + hard_cap×5，可 `--trip-timeout-s`） | 杀掉 runner 子进程并明确提示：游戏本体是 WMI 拉起的 detached 进程可能还活着 → 走残留检测 → 矩阵停，人工 D1 |
| trip 目录已存在 | 非复用：无 `--resume` ⇒ 中止报错；`--resume` ⇒ 完整（有 TRIP_RESULT 且带 outcome）跳过、不完整挪 `out/aborted/<名>_<时间戳>` 重跑新目录 |
| 构建失败 | 矩阵中止（不在缺包状态下跑趟） |

## 6. `--resume` 的可靠性边界

实现为：**完成判定 = trip 目录内有可解析且带 `outcome` 的 `TRIP_RESULT.json`**（趟runner的 finally 块总会写它，除非 runner 进程本身被杀）。据此：完整→跳过并计入停止条件累计；不完整→挪走重跑。**未实现/做不到的部分**：无法恢复一个"被杀趟"的半截 ndjson（它被整体挪到 aborted/，不参与汇总，避免半截数据混进均值）。

## 7. 它**不做**什么

- 不做 ABBA 观测器校准（W86/裁决 Q3 的规程；挂了 render_channel 的趟照旧"未校准"）；
- 不做 200×200 之类的地图几何推理——几何常量是 W85 签字绿基线，矩阵只拨 W88 已验证的旋钮（剂量/间距/Crewed）；
- 不做配对判定措辞（比值 <1.10 / 初估抬升）——那是单对配对分析的规则，SUMMARY 只给每趟描述统计，配对决策留给 Lead；
- 不自己 robocopy 建沙箱、不动真目录 `ra2youli`（全程只读）、不注入、不调 gamemd 内存写、不碰别卡脚本（工具链是本卡私有副本）；
- 不做显著性表述（无 p 值/置信区间/显著字样）。

## 8. 已验证（离线证据，见 EVIDENCE\）

- `dry_run_demo_console.txt` + `dry_run_plan_demo.json`：示例矩阵 dry-run，6 趟计划、shuffle seed=1234 确定性顺序、重复臂警告；
- `unit_checks_console.txt`：停止条件解析（4 种坏形式拒绝）、outcome 计数器 5 例、矩阵校验 4 例坏矩阵拒绝、计划确定性、Guard 翻译、时长边界；
- `SUMMARY.csv` / `SUMMARY.md` + `make_fake_trips_selftest.py`：**不启动游戏**的伪造 ndjson 自测 —— 6 趟/4 格汇总正确（CPU 均值/极差、A8ED50 占比、X87E8E0 变化、EIP 0047C538 与 EAC8D5DF 归档命中、outcome 分布）。自测还真抓出并修掉一个键名错位 bug（`x87e8e0_n_changes` vs `x87e8e0_changes`）。

## 9. 真机首跑的最短路径（给下一张卡）

1. 确认锁空闲 → `W94_FRESH=1` 建 `out/sandbox_game`（一次性）；
2. `python batch_runner.py examples\matrix_demo.json`（或真矩阵）；
3. 跑完 `python batch_analyze.py out --matrix examples\matrix_demo.json`；
4. 收尾差集清场：`python work\tools\w94_finalize.py`（锁 owner 需 w94*/lead）。
