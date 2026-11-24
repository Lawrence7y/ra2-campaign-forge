# 起点独立复核报告：物理起点 S 还原与不确定度独立审计

- **复核角色**：起点独立复核员
- **复核对象**：
  - `lead/dstart_observable_20261107/S_ESTIMATES.json`
  - `lead/dstart_observable_20261107/S_UNCERTAINTY.md`
- **复核立场**：默认怀疑。不采信上报数值，完全从原始语料 `out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip` 下 64 个推进窗 `measure_w*.json` 及 `lead/stall_event_def_20261106/STALL_EVENTS.json` 重新计算。
- **纪律遵守**：零真机运行、零采样代码实现（无 ctypes / OpenProcess / SetWindowsHookEx 等调用）、不修改任何既有文件；唯一写域为 `lead/dstart_observable_20261107/`。

---

## 1. 上报统计指标独立重算复现核验（上报 vs 实算）

| 指标名称 | 上报数值 | 独立实算数值 | 吻合判定 | 实算依据与计算方法 |
|:---|---:|---:|:---:|:---|
| **总事件数 $n$** | 1681 | 1681 | **MATCH** | `STALL_EVENTS.json` 中 `isRealMatch == true` 事件数 |
| **不可还原数 `unknownCount`** | 4 | 4 | **MATCH** | 窗首拍即停滞（`startTick == 0`）的真实事件数 |
| **区间约束数 `boundedCount`** | 182 | 182 | **MATCH** | 存在前拍推进但 $priorIntervalMs > 6.0\text{ ms}$ 的事件数 |
| **精确还原数 `fullCount`** | 1495 | 1495 | **MATCH** | 存在前拍推进且 $priorIntervalMs \le 6.0\text{ ms}$ 的事件数 |
| **不确定度中位数 `uncertaintyP50Ms`** | 2.515 ms | 2.515 ms | **MATCH** | 有效样本 $n=1677$ 排序数组第 838 项（奇数中央项） |
| **不确定度 P95 分位 `uncertaintyP95Ms`** | 35.367 ms | 35.367 ms | **MATCH** | 线性最近秩 $\text{index} = \lfloor 0.95 \times 1676 \rfloor = 1592$（线性插值为 35.457 ms） |
| **不确定度极大值 `uncertaintyMaxMs`** | 488.616 ms | 488.616 ms | **MATCH** | 出处 `l3_20261031hb/w1:samples[1377]` |

**全量 1681 条事件核验结论**：
经 `lead/dstart_observable_20261107/_independent_audit_probe.py` 全量比对，1681 条事件的 `firstObservedMs`、`sLowerBoundMs`、`sUpperBoundMs`、`sUncertaintyMs`、`priorIntervalMs`、`quality` 字段与上报文件 **0 差异、100% 吻合**。

---

## 2. 独立抽样 20 条事件原始语料逐条复算对比（含全部 4 条 unknown）

从全量事件中独立抽取全部 4 条 `unknown` 事件、8 条覆盖不同尺度区间的 `bounded` 事件、8 条不同分位特征的 `full` 事件，与原始语料切片时间戳重算对比：

| 抽样档位 | 事件标识 (`eventId`) | 原始语料切片依据 | 实算 $sLowerBoundMs$ | 实算 $sUpperBoundMs$ | 实算 $sUncertaintyMs$ | 上报 $sUncertaintyMs$ | 档位判定 | 逐条比对 |
|:---|:---|:---|---:|---:|---:|---:|:---:|:---:|
| **unknown** | `l3_20261031ha/w0/0/103` | `measure_w0.json:samples[0]` | 0.000 | 0.000 | 0.000 | 0.000 | unknown | **MATCH** |
| **unknown** | `l1c_20261021/w0/0/56` | `measure_w0.json:samples[0]` | 0.000 | 0.000 | 0.000 | 0.000 | unknown | **MATCH** |
| **unknown** | `l3_20261031hb/w2/0/52` | `measure_w2.json:samples[0]` | 0.000 | 0.000 | 0.000 | 0.000 | unknown | **MATCH** |
| **unknown** | `l3_1101v3a/w0/0/68` | `measure_w0.json:samples[0]` | 0.000 | 0.000 | 0.000 | 0.000 | unknown | **MATCH** |
| **bounded (Max)** | `l3_20261031hb/w1/1377/1736` | `measure_w1.json:samples[1376:1377]` | 2749.574 | 3238.190 | 488.616 | 488.616 | bounded | **MATCH** |
| **bounded (2nd)**| `l3_20261031hb/w1/1814/2071` | `measure_w1.json:samples[1813:1814]` | 3623.825 | 4066.855 | 443.030 | 443.030 | bounded | **MATCH** |
| **bounded (3rd)**| `l3_20261031hb/w1/11952/12210` | `measure_w1.json:samples[11951:11952]`| 23899.695 | 24237.852 | 338.157 | 338.157 | bounded | **MATCH** |
| **bounded (~100ms)**| `l3_1101v3b/w2/4894/5021` | `measure_w2.json:samples[4893:4894]` | 9784.533 | 9885.145 | 100.612 | 100.612 | bounded | **MATCH** |
| **bounded (P95)** | `l3_1101v3a/w2/4227/4334` | `measure_w2.json:samples[4226:4227]` | 8450.966 | 8486.333 | 35.367 | 35.367 | bounded | **MATCH** |
| **bounded (~20ms)** | `l3_1101v3b/w1/11395/11506` | `measure_w1.json:samples[11394:11395]`| 22785.668 | 22806.340 | 20.672 | 20.672 | bounded | **MATCH** |
| **bounded (~10ms)** | `l3_20261031hb/w0/6240/6476` | `measure_w0.json:samples[6239:6240]` | 12477.236 | 12487.059 | 9.823 | 9.823 | bounded | **MATCH** |
| **bounded (Min)** | `l3_20261031hb/w0/11963/12090` | `measure_w0.json:samples[11962:11963]`| 23922.408 | 23928.520 | 6.112 | 6.112 | bounded | **MATCH** |
| **full (Min)** | `l3_20261031hb/w1/10702/10930`| `measure_w1.json:samples[10701:10702]`| 21401.678 | 21401.686 | 0.008 | 0.008 | full | **MATCH** |
| **full (Max)** | `l3_1101v3b/w2/5022/5115` | `measure_w2.json:samples[5021:5022]` | 10040.581 | 10046.437 | 5.856 | 5.856 | full | **MATCH** |
| **full (P10)** | `l1d_20261021/w2/11697/11764` | `measure_w2.json:samples[11696:11697]`| 23390.052 | 23392.314 | 2.262 | 2.262 | full | **MATCH** |
| **full (P25)** | `l1c_20261021/w2/5336/5391` | `measure_w2.json:samples[5335:5336]` | 10668.859 | 10671.325 | 2.466 | 2.466 | full | **MATCH** |
| **full (P50)** | `l1c_20261021/w1/3440/3510` | `measure_w1.json:samples[3439:3440]` | 6875.751 | 6878.266 | 2.515 | 2.515 | full | **MATCH** |
| **full (P75)** | `l3_20261031hb/w0/2675/2744` | `measure_w0.json:samples[2674:2675]` | 5346.202 | 5348.785 | 2.583 | 2.583 | full | **MATCH** |
| **full (~3.5ms)** | `l3_20261031hb/w0/10593/10690`| `measure_w0.json:samples[10592:10593]`| 21182.535 | 21185.999 | 3.464 | 3.464 | full | **MATCH** |
| **full (~0.5ms)** | `l3_1101v3a/w2/10695/10798` | `measure_w2.json:samples[10694:10695]`| 21391.699 | 21392.151 | 0.452 | 0.452 | full | **MATCH** |

---

## 3. startTick=0 盲区事件独立核查与档位归属

1. **真实事件中的 startTick=0 计数**：
   - 在 `STALL_EVENTS.json` 全量 1737 条候选平台中，`startTick == 0` 的记录共有 40 条；
   - 经 `isRealMatch == true` 准入过滤后，真实停滞事件中的 `startTick == 0` **恰好为 4 条**，无一遗漏；
2. **档位归属审查**：
   - 查验 4 条事件在 `S_ESTIMATES.json` 中的字段：全部标定为 `quality = "unknown"`，`priorIntervalMs = null`，`sUncertaintyMs = 0.0`；
   - 交叉检验：全量 1681 条中，`startTick == 0` 且 `quality != "unknown"` 的条目数为 **0**；`startTick != 0` 且 `quality == "unknown"` 的条目数为 **0**；
   - **判定结论**：4 条事件**全部真实落入 unknown 档位，未被静默算作 bounded 或 full**。

---

## 4. 采样掉拍（Sampling Gap）与真实停滞的严格辨析

针对 488.616 ms 极值事件（`l3_20261031hb/w1/1377/1736`）进行语料切片现场剖析：

1. **切片原始物理数据**：
   - 采样索引 1376：$t = 42574.019111\text{ s}$，帧号 $f = 618$；
   - 采样索引 1377：$t = 42574.507727\text{ s}$，帧号 $f = 620$；
   - 两拍采样时间差：$\Delta t = 488.616\text{ ms}$；两拍期间采样点数为 0；
   - 采样索引 1377 至 1736：帧号恒定为 620，包含 360 个连续采样点，停滞跨度为 $231.716\text{ ms}$；
   - 采样索引 1737：帧号恢复推进为 621。
2. **物理事实界定**：
   - **停滞事实**：引擎在帧 620 上的真实战术停滞时长为 **231.716 ms**（非 488 ms）；
   - **掉拍事实**：在此停滞发生前，外部采样线程发生了长达 **488.616 ms 的调度停顿/掉拍（Sampling Gap）**，在此空白期内游戏完成了帧 618 到 620 的 2 帧推进；
   - **不确定度虚高原因**：由于采样工具在此 488 ms 内完全缺失采样点，观测者无法得知帧 620 究竟在该 488 ms 区间内的哪个微秒开始，机械推演导致 $sLowerBound$ 被退后至 $t[1376]$，形成了高达 488.616 ms 的观测不确定度。
3. **上报文档的处理方式审查**：
   - `S_UNCERTAINTY.md` §5 专门设立了《采样掉拍（Sampling Gap）与真实停滞的严密物理区分》，明确定性 231.72 ms 为真实战术停滞，488 ms 为采样线程掉拍，并判定不确定度虚高系观测端采集缺陷所致；
   - 报告未将 488 ms 误当成停滞时长，且正确将其划入 `bounded`，未污染 `full` 级精度。

---

## 5. 三项核心质询独立判定

### 判定一：上报的 uncertainty 统计是否可复现？
- **判定结论**：**完全可复现**。
- **依据**：独立探针从原始语料重算结果显示：$n=1681$、`unknownCount`=4、`boundedCount`=182、`fullCount`=1495、`uncertaintyP50Ms`=2.515 ms、`uncertaintyP95Ms`=35.367 ms（插值 35.457 ms）、`uncertaintyMaxMs`=488.616 ms，所有统计量逐项 100% 吻合。

### 判定二：「S 的不确定度」是否被恰当地与「:177 能否满足」分开？
- **判定结论**：**已恰当分开，边界清晰严密**。
- **依据**：
  1. `S_UNCERTAINTY.md` §6.1 与 §6.2 明确指出 $U$ 是离线事后核验工具的测量不确定度，说明的是离线核验工具链的数学证伪分辨率瓶颈，**绝不说明 :177 在工程物理上不可满足**；
  2. 报告特别强调：在线探针若常驻主线程或以高频时钟运行，其捕获与保存由在线架构决定，不受离线采样线程掉拍影响；
  3. 报告严格执行 D-29 §1 裁决，将 :177 起算点（物理起点 $S$，受 $U$ 累及）与 :190 起算点（检测确认时刻 $D$，探针离散事件，不确定度为 0，完全不受 $U$ 影响）正交分离，未把对 $S$ 的观测不确定度转嫁给 :190。

### 判定三：有没有任何一处把「S 不可精确观测」暗示成了「物理上采不到」？
- **判定结论**：**没有任何一处**。
- **依据**：
  1. `S_UNCERTAINTY.md` 全文对不可精确还原的定性严格限定于「在现有离线 500 Hz 采样语料下」；
  2. 报告在 §6.2 第 160 行与 §7.3 第 201 行**两次明文驳斥外推**：「绝不说明在线真实实现物理上采不到该停滞（D-30 §2 原文明文裁定）」、「若将离线语料采样线程掉拍导致的 $U$ 较大外推为游戏引擎主循环或在线探针物理上不可达，【这是外推】，且违反 D-30 §2 裁决」；
  3. 全文无任何暗示物理不可达的词句，完全恪守了 D-30 §2 的裁决边界。
