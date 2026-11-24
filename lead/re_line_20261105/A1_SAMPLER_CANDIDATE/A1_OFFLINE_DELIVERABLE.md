# D-20 步骤 A（离线半）· 帧沿触发采样候选件 + 离线单测

> 依 D-20 定谳（`dwfrun-abf90739`，`magpie/codex/gpt-6.1-sol$medium`，快裁）第 3 条：
> 「**执行 A**：按 D-19 帧沿规格实现四 VA + 帧号候选件，对读取、格式及 null 处理
> 运行离线单测并记录命令和输出；**通过后**使用隔离载体执行 **3 趟**小批真机验证通道，
> **保留 alpha 未校准与采样充分性未证标记**。」
>
> **本文只覆盖 A 的离线半**（候选件 + 离线单测）。**真机 3 趟尚未执行**。
> 零真机、零采样注入、零母本改动。

## 0. 一句话结论

**候选件已写出，离线单测 67 项全通过（exit=0）**，两个未证标记（`alpha_uncalibrated`、
`sampling_sufficiency_unproven`）**已内建在源码常量与每条记录里**，可被下游机械校验。
**真机通道未验证**——这是 A 的第二半，须另行执行。

## 1. 交付件清单

| 文件 | 作用 | 大小 |
|---|---|---|
| `A1_SAMPLER_CANDIDATE/frame_edge_sampler.py` | 候选件（纯函数 + 帧沿跟踪器 + 可选 RPM 适配器） | 见 `ls` |
| `A1_SAMPLER_CANDIDATE/test_frame_edge_sampler.py` | 离线单测（67 项，7 组） | — |
| `A1_SAMPLER_CANDIDATE/_test_out.txt` | 单测原始输出 | — |
| `A1_REVIEW/REVIEW_TASK.md` | 独立复核任务书（R1–R6 六问） | — |

## 2. 实跑命令与输出

**命令**（逐字）：

```bash
python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/re_line_20261105/A1_SAMPLER_CANDIDATE/test_frame_edge_sampler.py"
```

**退出码**：`0`

**摘要行**（原始输出尾部，逐字）：

```text
==============================================================
SUMMARY  PASS=67  FAIL=0
==============================================================
```

**7 个测试组**（全部 PASS）：

| 组 | 覆盖 | 关键断言 |
|---|---|---|
| T1（9 项） | `read_one` 读取语义 | 失败 ⇒ `None` **不补 0**；越界/负数/非 int/`bool` 全拒收；边界 `0` 与 `0xFFFFFFFF` 接受；reader 抛异常不外泄 |
| T2（13 项） | `read_sample` 读序/齐全/跨帧 | 读序**严格** `帧前 → 四字段 → 帧后`（6 次读）；`f_pre != f_post` ⇒ `cross_frame=True`；后读失败 ⇒ `cross_frame=None`（**不猜**）；单字段失败不影响其他字段；时间戳逐次递增 |
| T3（6 项） | `classify_edge` | `df=0`⇒same、`df=1`⇒edge、`df>1`⇒edge_missed、`df<0`⇒unjudgeable、`None`⇒unjudgeable |
| T4（15 项） | `FrameEdgeTracker` | `df>1` **只出 1 个事件**、归属标 `aggregate_over_N_frames`；漏沿下界 = Σ(df−1)；**首样本单列 `first`，不污染 `unjudgeable`**；`stats.note` 明写「不得据此宣称业务字段冻结」 |
| T5（8 项） | JSONL 格式 | 单行无 `\n`/`\r`；往返一致；`schema` 不符拒收；非 dict 拒收；中文不转义；5000 字符值不破坏单行 |
| T6（8 项） | 静态交叉核对 | 四 VA + 帧号 VA 与 D-19/任务书**逐字**一致；字段顺序固定；harness 常量 `MEASURE_CURRENT_FRAME_VA = 0x00A8ED84`、`MEASURE_HZ = 500` 在场 |
| T7（8 项） | D-19 三条硬要求 + 铁律 | `df=4` 不生成中间帧假值；源码**不含** `CreateRemoteThread`/`WriteProcessMemory`/`SuspendThread`/`MiniDumpWriteDump`/`StackWalk`/`SetWindowsHookEx`；`RpmReader` 默认 `enable=False`，未启用时 `open()` 返回 `False` 且 `read_u32` 返回 `None` |

## 3. 候选件的设计要点（逐条对 D-19 第 4–6 条）

| D-19 要求 | 候选件的落实 |
|---|---|
| 复用既有 500 Hz 帧号轮询，观测到帧号变化时**追加读取** | `FrameEdgeTracker.feed(t, f, sample)` 只在 `df≥1` 时产事件；非沿轮次零产出 |
| 四 VA **不连续**，**不是**一次原子 16 字节快照 | `read_sample` 逐地址单独读、**逐次**打时间戳；`ts` 段 6 个时刻独立字段 |
| 读序与**每字段时间戳** | `FIELDS` 元组顺序即读序（固定不可重排，T6.3 锁死）；`ts[key]` 逐字段记录 |
| `df>1` 记漏沿、**不补造逐帧值** | `classify_edge` 返回 `edge_missed`；归属字段写 `aggregate_over_N_frames`；`missed_frames_lower_bound` 只在统计里记下界 |
| 帧号冻结记**持续时段**、**不宣称业务字段冻结** | `freeze_max_s` + 每条 `stats` 都带 `note` 明文；标记为 **帧号**冻结 |
| 重置/回绕/进程重启**不能判明**的区间标不可判 | `df<0` ⇒ `unjudgeable`（**当前三者确实不可区分**，见 §5 未验项） |
| 读失败**保留 null、不补 0** | `read_one` 四类失败全返 `None`；T1/T2 共 6 项断言锁死 |
| 帧沿时刻为**首次观测**、不能宣称 CPU 事件微秒真值 | `ts` 用 `time.perf_counter()` 记录**读取之前**的时刻；不宣称真值 |

## 4. 两个未证标记的落地方式

```python
MARKER_ALPHA_UNCALIBRATED     = "alpha_uncalibrated"
MARKER_SUFFICIENCY_UNPROVEN   = "sampling_sufficiency_unproven"
FIELD_MARKERS = (MARKER_ALPHA_UNCALIBRATED, MARKER_SUFFICIENCY_UNPROVEN)
```

**每个 `read_sample` 记录、每个 edge 事件、每份 `stats()` 都带 `markers` 字段**，
所以「标记被删」这件事**可被下游机械检出**（缺 `markers` 或值不符 ⇒ 该件作废），
而不是靠人记得。

## 5. 诚实账

1. **我亲验**：`SUMMARY PASS=67 FAIL=0`、`EXIT=0`（上面命令与输出逐字）。
2. **我亲验**：单测首轮曾 **2 项 FAIL**，均如实修正后重跑：
   (a) `T4.10` 期望值写错（我漏算了 `104→103` 回退这一次 `unjudgeable`）——**这是测试期望错，不是候选件错**；
   (b) `T6.4` harness 路径上溯级数错一级（`../../..` 应为四级）——**改为向上搜索祖先目录**。
   **两处都改了再跑，没有靠放宽断言过关。**
3. **我亲验**：`freeze_max_s` 的语义只在**帧号**层面成立；`stats.note` 有明文限制。
4. **我未验**：
   - **真机通道**（A 的第二半）——**一趟都没跑**；
   - `RpmReader(enable=True)` 的真实读取行为——被铁律禁止，**未测**；
   - `df<0` 三种成因（重置 / 回绕 / 进程重启）**能否区分**——当前**不可区分**，候选件只是把三者合并标 `unjudgeable`，没有更强的静态依据；
   - 500 Hz 实际是否达得到、帧沿在慢窗（6 fps）与快窗（31.25 fps）下的漏沿率——**未测**。
5. **本步零真机、零注入、零母本改动、未 commit**。
6. **A 的第二半（3 趟隔离载体真机）尚未执行**，且它需要先解决一个前置问题：
   现有 harness（`qc151_trip.harness8_v4.py`）**不带四 VA 读取**，
   要跑真机通道必须先做一个**只加四个只读 VA** 的 harness 副本，
   而这一步会改动真机发射路径 ⇒ 属 D-19 第 7 条「两闸」范围（用户已全开），
   但仍须独立复核后再发。

## 6. 下一步（最小动作）

1. **等独立复核回件**（`dwfrun-d10c0966`，gemini-3.8-flash$high，两组并行 + 汇总 + 门槛）。
   复核判 REFUTED 或 PARTIAL ⇒ **先按意见改候选件**，改完再重跑离线单测。
2. 复核 CONFIRMED/PARTIAL 后，做 **harness 只读扩项副本**（四个 VA + 帧沿触发），
   同样跑离线单测，然后才考虑 3 趟真机。
3. **两个标记在整个链条里不得移除**。
