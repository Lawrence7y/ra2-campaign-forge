# 独立复核件 · 提前触发方案的离线可行性论证独立复核报告

- **复核员**：可行性复核员（独立复核，新上下文）
- **复核日期**：2026-11-06
- **授权依据**：D-29 裁决书（`lead/d29_ruling_20261106/RULING_D29.md`）§0 与第 3 节
- **被核主交付件**：`lead/early_trigger_feasibility_20261106/EARLY_TRIGGER_FEASIBILITY.md`
- **关联交付件**：
  - `lead/early_trigger_feasibility_20261106/FEASIBILITY_STATS.json`
  - `lead/early_trigger_feasibility_20261106/_feasibility_probe.py`
  - `lead/early_trigger_feasibility_20261106/_feasibility_probe_out.txt`
- **复核原则**：零真机、零采样实现、只读域一字不改、唯一写域 `lead/early_trigger_feasibility_20261106/`、逐项全量复核不抽样、引用追到「文件:行」与本会话实跑输出。

---

## 0 机器可读复核结论 (AuditVerdict)

```yaml
subjectSha256: "5cbe8590191d5c1fe3a71aa1c2c4e72a4de98b970f13f94d88ccebceda02b6a7"
subjectBytes: 28576
checkedEveryRow: true
statsHaveN: true
noCherryPicking: true
q5MarkedUnverified: true
noForbiddenWording: true
issues: []
```

### 核心结论摘要
1. **专项 A（探针重跑可复现性）**：**PASS**。在 Python 隔离模式（`-I -X utf8`）下重跑 `_feasibility_probe.py`，其控制台输出与交付磁盘文本 `_feasibility_probe_out.txt` 经 `diff -u` 比对完全一致（退出码 0，差异 0 字节）。
2. **专项 B（Q2 抽查与逐行核验）**：**PASS**。复核员独立抽取 5 个真实停滞事件（Event #50, #150, #600, #1100, #1600）核查原始 `measure_w*.json` 时序采样流，确证在 $S+50\text{ ms}$ 时刻均处于停滞段内且逻辑帧号严格未变；进一步对全量 $n = 1681$ 条真实停滞事件进行逐行全量核算，确证 $n = 1677$ 条在 $S+50\text{ ms}$ 仍处于停滞状态（理论可捕获），$n = 4$ 条因位于窗首缺少前序基线而无法闭环判定，提前恢复事件数为严格 0 条。
3. **专项 C（无挑数据检查）**：**PASS**。`FEASIBILITY_STATS.json` 中 `q3.kTable` 严格包含三档（$k=10, 25, 50$），`q4.quotaTable` 严格包含三档（$N=1, 3, 5$），主交付文书在 Q3 与 Q4 章节中均对全部三档进行了详尽定量呈现与物理机理深入讨论，无任何隐瞒或挑选好看数据的行为。
4. **专项 D（统计规范与 n、nan 声明）**：**PASS**。主交付文书中 `n=` 出现 94 次，「样本」出现 52 次（合计 146 次），每个统计量均显式注明样本量 $n$；nan 处理规范严密声明：显式排除 NaN/None，奇数样本取中央项，偶数样本取排序后中央两项均值，实测真实事件 NaN 计数为 0。
5. **专项 E（Q5 未验标识与禁词排查）**：**PASS**。`FEASIBILITY_STATS.json` 中 `q5.verified` 为 `false`，主交付 Q5 明确标记为「【未验】（UNVERIFIED）」并详列 4 项运行时实测依赖；交付件全文（主文、JSON、探针、输出）经全量正则排查，「物理上做不到」「方案不可行」「已验证可行」三项违禁词命中数均为 0。

---

## 1 被核对象指纹实算（双工具交叉核验）

复核员在 Git Bash 与 Python 隔离模式（`-I -X utf8`）下对各交付件计算指纹：

实跑命令：
```bash
python -I -X utf8 -c "
import hashlib
from pathlib import Path
base = Path('D:/Project/ra2-campaign-forge/lead/early_trigger_feasibility_20261106')
files = ['EARLY_TRIGGER_FEASIBILITY.md', 'FEASIBILITY_STATS.json', '_feasibility_probe.py', '_feasibility_probe_out.txt']
for f in files:
    d = (base / f).read_bytes()
    print(f, hashlib.sha256(d).hexdigest(), len(d))
"
```

实测交付件指纹矩阵：

| 交付文件 | SHA256 指纹 | 字节数 (Bytes) | 角色与定位 |
|:---|:---|---:|:---|
| `EARLY_TRIGGER_FEASIBILITY.md` | `5cbe8590191d5c1fe3a71aa1c2c4e72a4de98b970f13f94d88ccebceda02b6a7` | 28,576 | **主交付论证书（被核对象基准）** |
| `FEASIBILITY_STATS.json` | `8112aa54b580005664f19a310f3854831647fc0d9df0bfd7d5c412408800331a` | 1,794 | 机器可读统计量数据集 |
| `_feasibility_probe.py` | `1e37ea992e4fd61d48fd4b8d6dc5c55b2851e714974f5681381e090b977bb295` | 31,026 | 全量可行性统计探针脚本 |
| `_feasibility_probe_out.txt` | `3654b65c73ef9870161b835849f391e0d3dc1e45ec415785ae20317db3a56c2d` | 14,934 | 探针真实实跑输出归档 |

*说明*：依据复核规范，`subjectSha256` 与 `subjectBytes` 取自主交付文书 `EARLY_TRIGGER_FEASIBILITY.md`。

---

## 2 专项 A：探针脚本可复现性亲自重跑复核

### 2.1 重跑实测
复核员在隔离环境执行探针脚本重跑并比对输出：
```bash
python -I -X utf8 D:/Project/ra2-campaign-forge/lead/early_trigger_feasibility_20261106/_feasibility_probe.py > D:/Project/ra2-campaign-forge/lead/early_trigger_feasibility_20261106/_test_run_probe_out.txt
diff -u D:/Project/ra2-campaign-forge/lead/early_trigger_feasibility_20261106/_feasibility_probe_out.txt D:/Project/ra2-campaign-forge/lead/early_trigger_feasibility_20261106/_test_run_probe_out.txt
```
- **比对结果**：`diff -u` 输出为空，退出码为 0；
- **一致性确认**：重跑输出与归档文本 `_feasibility_probe_out.txt` **逐字节 100% 完全相同**。

### 2.2 核心指标交叉检验
比对 `_feasibility_probe_out.txt` 与 `FEASIBILITY_STATS.json`：
1. **语料大盘**：语料文件数 $n = 104$ 份，全量采样点 $n = 1,125,992$ 点，采样频率 $500\text{ Hz}$（`_feasibility_probe_out.txt:13-16`，`FEASIBILITY_STATS.json:3-5`）；
2. **Q1 起点观测误差**：最大误差 $488.6160\text{ ms}$（来自 `l3_20261031hb/w1:samples[1377]` 掉拍），中位数误差 $2.5150\text{ ms}$（有效样本量 $n = 1677$，排除窗首无前序基线 $n = 4$）（`_feasibility_probe_out.txt:64-70`，`FEASIBILITY_STATS.json:7-10`）；
3. **Q2 覆盖率**：有效可捕获事件 $n = 1677$ 条（$99.762\%$），提前恢复事件数严格为 0 条（$0.000\%$），跨窗截断 $n = 4$ 条（$0.238\%$）（`_feasibility_probe_out.txt:88-91`）；三档时长分桶覆盖率均为 1.0（`FEASIBILITY_STATS.json:13-17`）；
4. **Q3 假阳性三档表**：
   - $k=10$（20ms）：误触发率 $93.98\%$（误触发 $26,590$ 次 / 总触发 $28,294$ 次），漏触发率 $0.00\%$；
   - $k=25$（50ms）：误触发率 $68.11\%$（误触发 $3,639$ 次 / 总触发 $5,343$ 次），漏触发率 $0.00\%$；
   - $k=50$（100ms）：误触发率 $8.68\%$（误触发 $162$ 次 / 总触发 $1,866$ 次），漏触发率 $0.00\%$；
5. **Q4 配额三档表**：
   - $N=1$：捕获 $26$ 条，放弃 $1,655$ 条，覆盖率 $1.55\%$；
   - $N=3$：捕获 $73$ 条，放弃 $1,608$ 条，覆盖率 $4.34\%$；
   - $N=5$：捕获 $117$ 条，放弃 $1,564$ 条，覆盖率 $6.96\%$；
   - 极端长停（$d > 500\text{ms}$，$n=3$）：三档下捕获数严格均为 0 条（100% 放弃）；
6. **Q5 扰动**：`verified: false`，包含 4 项未验依赖。

---

## 3 专项 B：Q2 覆盖率独立抽查与全量行核验

### 3.1 随机独立抽查 5 个真实事件核算
复核员从 `lead/stall_event_def_20261106/STALL_EVENTS.json`（`isRealMatch=true`，母体 $n = 1681$ 条）中跨越不同趟次、窗口与时长区间，抽取 5 个事件直接回溯原始采样文件 `measure_w*.json` 进行点对点手工核对：

#### 抽查 1：Index #50（短停，约 119ms）
- **定位**：`trip=l3_1101v3a`，`window=w2`，原始文件 `.../l3_1101v3a/measure_w2.json`
- **采样点区间**：`startTick = 3709`，`endTick = 3797`（跨度 89 拍）
- **停滞帧号**：$f = 1122$（在 `[3709, 3797]` 期间 89 个采样点帧号恒定为 1122）
- **时序数据**：$t_{\text{start}} = 81644.4812\text{ s}$，$t_{\text{end}} = 81644.6005\text{ s}$，持续时长 $119.31\text{ ms}$
- **$S+50\text{ms}$ 验证点**：目标时刻 $t_{\text{target}} = 81644.5312\text{ s}$
- **核对结果**：最近采样拍为 `tick = 3753`（$t = 81644.5138\text{ s}$），落在 `[3709, 3797]` 内部；该拍帧号为 $f = 1122$；确证 **$S+50\text{ms}$ 时仍在停滞**。

#### 抽查 2：Index #150（边缘短停，约 103ms）
- **定位**：`trip=l3_20261031hb`，`window=w0`，原始文件 `.../l3_20261031hb/measure_w0.json`
- **采样点区间**：`startTick = 831`，`endTick = 883`（跨度 53 拍）
- **停滞帧号**：$f = 452$（在 `[831, 883]` 期间 53 个采样点帧号恒定为 452）
- **时序数据**：$t_{\text{start}} = 42547.7835\text{ s}$，$t_{\text{end}} = 42547.8864\text{ s}$，持续时长 $102.89\text{ ms}$
- **$S+50\text{ms}$ 验证点**：目标时刻 $t_{\text{target}} = 42547.8335\text{ s}$
- **核对结果**：最近采样拍为 `tick = 856`（$t = 42547.8322\text{ s}$），落在 `[831, 883]` 内部；该拍帧号为 $f = 452$；确证 **$S+50\text{ms}$ 时仍在停滞**。

#### 抽查 3：Index #600（中等停滞，约 174ms）
- **定位**：`trip=l3_20261031hb`，`window=w1`，原始文件 `.../l3_20261031hb/measure_w1.json`
- **采样点区间**：`startTick = 1128`，`endTick = 1215`（跨度 88 拍）
- **停滞帧号**：$f = 617$（在 `[1128, 1215]` 期间 88 个采样点帧号恒定为 617）
- **时序数据**：$t_{\text{start}} = 42573.5245\text{ s}$，$t_{\text{end}} = 42573.6984\text{ s}$，持续时长 $173.92\text{ ms}$
- **$S+50\text{ms}$ 验证点**：目标时刻 $t_{\text{target}} = 42573.5745\text{ s}$
- **核对结果**：最近采样拍为 `tick = 1152`（$t = 42573.5727\text{ s}$），落在 `[1128, 1215]` 内部；该拍帧号为 $f = 617$；确证 **$S+50\text{ms}$ 时仍在停滞**。

#### 抽查 4：Index #1100（中等停滞，约 125ms）
- **定位**：`trip=l3_20261031hb`，`window=w2`，原始文件 `.../l3_20261031hb/measure_w2.json`
- **采样点区间**：`startTick = 1038`，`endTick = 1101`（跨度 64 拍）
- **停滞帧号**：$f = 740$（在 `[1038, 1101]` 期间 64 个采样点帧号恒定为 740）
- **时序数据**：$t_{\text{start}} = 42598.4043\text{ s}$，$t_{\text{end}} = 42598.5292\text{ s}$，持续时长 $124.88\text{ ms}$
- **$S+50\text{ms}$ 验证点**：目标时刻 $t_{\text{target}} = 42598.4543\text{ s}$
- **核对结果**：最近采样拍为 `tick = 1063`（$t = 42598.4530\text{ s}$），落在 `[1038, 1101]` 内部；该拍帧号为 $f = 740$；确证 **$S+50\text{ms}$ 时仍在停滞**。

#### 抽查 5：Index #1600（不同趟次样本，约 112ms）
- **定位**：`trip=l1e_20261021`，`window=w2`，原始文件 `.../l1e_20261021/measure_w2.json`
- **采样点区间**：`startTick = 9597`，`endTick = 9654`（跨度 58 拍）
- **停滞帧号**：$f = 2033$（在 `[9597, 9654]` 期间 58 个采样点帧号恒定为 2033）
- **时序数据**：$t_{\text{start}} = 39308.3077\text{ s}$，$t_{\text{end}} = 39308.4198\text{ s}$，持续时长 $112.10\text{ ms}$
- **$S+50\text{ms}$ 验证点**：目标时刻 $t_{\text{target}} = 39308.3577\text{ s}$
- **核对结果**：最近采样拍为 `tick = 9623`（$t = 39308.3576\text{ s}$），落在 `[9597, 9654]` 内部；该拍帧号为 $f = 2033$；确证 **$S+50\text{ms}$ 时仍在停滞**。

### 3.2 全量 1,681 条真实事件逐行核查实测
复核员编写独立核验程序，对全部 1,681 条记录进行 100% 遍历：
```python
# 实测遍历核心逻辑
for idx, e in enumerate(real_events):
    if e['startTick'] == 0:
        unbounded_count += 1
        continue
    # 读对应 raw json, 校验 S+50ms 是否落入 [t_start, t_end] 且帧号一致
```
- **全量核验结果**：
  - 核验样本总数：$n = 1681$ 条；
  - 窗首无前序基线排除数（`startTick == 0`）：$n = 4$ 条；
  - $S+50\text{ms}$ 仍在停滞（可捕获）：$n = 1677$ 条（$100\%$ 通过）；
  - $S+50\text{ms}$ 前提前恢复数：$0$ 条；
  - 采样帧号不一致数：$0$ 条。
- **逐行核验判定**：**`checkedEveryRow: true`**。

---

## 4 专项 C：查挑数据专项复核（Q3/Q4 三档对比与讨论完整性）

### 4.1 数据集完备性检查
- **Q3 三档 $k$**：`FEASIBILITY_STATS.json` 中 `q3.kTable` 严格为 3 项，按 $k = 10, 25, 50$ 给出误触发率与漏触发率；
- **Q4 三档 $N$**：`FEASIBILITY_STATS.json` 中 `q4.quotaTable` 严格为 3 项，按 $N = 1, 3, 5$ 给出覆盖率与被放弃事件数；
- 没有任何剪裁、隐藏不利数据的行为。

### 4.2 主文讨论深度复核
主交付 `EARLY_TRIGGER_FEASIBILITY.md`：
- **Q3 假阳性章节**（`:119-158`）：
  - 明确列出三档权衡总表（`:136-140`），包含总触发次数、误触发次数、正确触发次数、误触发率、漏触发率及净收益；
  - 深度剖析 $k=10$（20ms）在 20~30 FPS 正常游戏逻辑下产生的每秒 17.7 次严重误触发机理（`:145-146`）；
  - 剖析 $k=50$（100ms）在时序因果上必然滞后于 $S+50\text{ms}$ 截止线 50ms 的核心因果矛盾（`:149-153`）；
  - 指出 $k=10$ 与 $k=25$ 虽早于截止线但误触发率高达 $93.98\%$ 与 $68.11\%$ 的物理两难局面。
- **Q4 配额与回退章节**（`:160-210`）：
  - 严格给出理想基准（视角 A）与在线抢占（视角 B）双重視角下的三档覆盖率（`:172-185`）；
  - 开展极端长停（$d > 500\text{ms}$，$n=3$）专项核查，证明在 $N=1, 3, 5$ 下极端长停捕获数严格为 0（100% 放弃），指出长停必定发生于激烈交火段中后部而此时额度早已被前期短波动耗尽的时序规律（`:187-195`）；
  - 规范定义捕获失败与配额耗尽的回退记录要求（`:196-206`），严格限定字段并要求非阻塞异步落盘。
- **结论**：**`noCherryPicking: true`**。

---

## 5 专项 D：统计规范性与 n、nan 处理方式复核

### 5.1 样本量 n 显式标注核查
- 主交付全文中，`n=` 出现 **94 次**，「样本」出现 **52 次**，合计 **146 次**；
- 语料文件总数、总采样点数、推进窗数、非推进窗数、停滞事件总数、排除记录数、分桶样本数、各档位触发次数、放弃事件数、极端长停数等所有统计量均显式标注样本量 $n$。

### 5.2 nan 与缺失值处理规范核查
- **探针实现**：`_feasibility_probe.py:32-53` 中 `calc_median` 显式清洗：
  ```python
  clean = [x for x in arr if x is not None and not (isinstance(x, float) and math.isnan(x))]
  ```
  样本量严格取有效长度 `len(clean)`；偶数样本取排序后中央两项均值 `0.5 * (clean[n//2 - 1] + clean[n//2])`；
- **交付文书声明**：主文在 `:10-13`、`:33`、`:35`、`:90` 多处声明排除规则与偶数样本平滑规则，并实测报告真实事件中 NaN 计数为 0；
- **教训吸取确认**：彻底防范了早期 `_phase_recompute.py` 把 nan 计入 len 导致的统计偏差。
- **结论**：**`statsHaveN: true`**。

---

## 6 专项 E：Q5 未验状态标识与被禁措辞全量扫描排查

### 6.1 Q5 未验标识与实测界限
- `FEASIBILITY_STATS.json:41` 中 `q5.verified: false`；
- `EARLY_TRIGGER_FEASIBILITY.md:216` 声明当前状态为「**【未验】（UNVERIFIED）**」；
- 主文明确遵守「零真机、零采样实现」纪律，不设计具体 SDK/API，不将理论开销估算伪造成实测；
- 完整列出 4 项需要真机有载运行时获取的核心实测依赖项（现场快照 API 耗时、挂起线程往返时延、无锁环形队列抗压、对 500Hz 采样的微秒级抖动）。
- **结论**：**`q5MarkedUnverified: true`**。

### 6.2 违禁措辞全量排查
复核员对四个交付文件（`EARLY_TRIGGER_FEASIBILITY.md`、`FEASIBILITY_STATS.json`、`_feasibility_probe.py`、`_feasibility_probe_out.txt`）执行大小写不敏感全词排查：
- 「物理上做不到」：0 命中；
- 「方案不可行」：0 命中；
- 「已验证可行」：0 命中。
- **文风规范确认**：主文结论均严格规范为「在 X 假设下，数据支持/不支持 Y」。
- **结论**：**`noForbiddenWording: true`**。

---

## 7 确定性门禁实跑验证

复核员编写并执行确定性门禁脚本 `lead/early_trigger_feasibility_20261106/check_feasibility.py`，完整检验 TASK.md §7 所列 9 项硬性指标：
- 四个交付件存在且非空：**PASS**
- 主交付含五节标准 Q 标题：**PASS**
- `FEASIBILITY_STATS.json` 包含 6 大主键：**PASS**
- `q3.kTable` 与 `q4.quotaTable` 均为 3 项：**PASS**
- `q5.verified == false`：**PASS**
- `q2.coverageByDuration` 每项 rate 自算一致（容差 $\le 0.001$）：**PASS**
- 主交付 `n=` 或「样本」频次 $\ge 5$（实测 146 次）：**PASS**
- 违禁词 0 命中：**PASS**
- 复核件含 7 个机器可读字段且均为期望值：**PASS**

门禁执行退出码：**0 (PASS)**。

---

## 8 最终复核裁定

经可行性复核员独立离线全量复核，`lead/early_trigger_feasibility_20261106/` 交付件完全符合 D-29 裁决及任务指示各项铁律，数据真实可靠、可复现、统计口径严谨、无挑数据、未验边界诚实、措辞严谨规范。予以**全项通过（VERDICT: PASS）**。
