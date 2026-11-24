# 帧沿触发采样候选件独立复核报告 · 读写语义与帧沿篇（R1–R3）

> **复核员**：语义复核员·读写与帧沿  
> **复核对象**：`lead/re_line_20261105/A1_SAMPLER_CANDIDATE/frame_edge_sampler.py`  
> **基准单测**：`lead/re_line_20261105/A1_SAMPLER_CANDIDATE/test_frame_edge_sampler.py`（声称 67 PASS）  
> **规范依据**：`lead/re_line_20261105/D19_RULING/RULING_D19.md` §1「执行步骤」第 4–6 条  
> **参考实现**：`lead/goal1_harness8_20261031/qc151_trip.harness8_v4.py:3831`、`:4004–4045`  
> **本篇范围**：R1（读写语义与失败不补 0）、R2（读序与起止时间戳）、R3（`df>1` / `df<0` / `f is None` 边界）  
> **实跑探针**：`lead/re_line_20261105/A1_REVIEW/_probe_code_lens.py` → `_probe_code_lens_out.txt`（44 检查全部通过）  
> **本组判定**：**PARTIAL**（部分满足：R1 满足，R2 部分满足，R3 满足；**无实质缺陷**，即不产生错误读数/丢数/null 变 0，但 R2 缺少起止时间戳中的闭合戳，属可改进项）

---

## 0. 本组总判定与核心摘要

| 编号 | 审查项 | 判定 | 实质缺陷 | 核心结论与证据 |
|---|---|---|---|---|
| **R1** | 读写语义是否守住「失败不补 0」 | **满足** | 无 | `read_one` 严格过滤异常、`bool`（`True/False`）、越界数值及非 int 类型（`float`/`Decimal`/`numpy`）。合法 0 透传，读失败一律返回 `None`，绝无 `v or 0` 式补 0 逻辑。 |
| **R2** | 读序与时间戳是否满足 D-19「起止时间戳」 | **部分满足** | 无 | 读序（`f_pre` → 四字段 → `f_post`）完全合规；但目前仅记录读取**之前**的单点 `clock()`，缺少读段闭合结束戳（`segment_end`）或字段级 `ts_end`。不导致读数错误，但无法度量 `f_post` 读取耗时与突发总耗时。最小改动仅需 1 行。 |
| **R3** | `df>1`、`df<0`、`f is None` 三条边界 | **满足** | 无 | `df>1` 确未做任何插值补造假帧，归属明确为聚合；`df<0` 标 `unjudgeable` 充分合理，全镜像静态证明 `0x55DE7E` 邻近无写 0 分支，当前无法区分进程重启与回绕；`f is None` 记 `cross_frame=None` 严格遵循三态逻辑。 |

---

## 1. R1 · 读写语义是否真的守住了「失败不补 0」

### 1.1 `read_one()` 是否可能把失败变成一个看起来合法的 0？
- **判定**：**满足（不可能）**。
- **源码审查**（`frame_edge_sampler.py:87–103`）：
  ```python
  def read_one(reader, va: int):
      try:
          v = reader(va)
      except Exception:
          return None
      if isinstance(v, bool):
          return None
      if not isinstance(v, int):
          return None
      if v < 0 or v > 0xFFFFFFFF:
          return None
      return v
  ```
  - 代码中完全不存在将 `None`、空值或错误状态转为 `0` 的路径（没有 `or 0`、`default=0` 或三元运算符兜底）。
  - 只有在 `reader(va)` 明确返回一个 Python 原生 `int`，且该整数属于合法区间 `[0, 0xFFFFFFFF]` 时，才会原样返回。
  - 对于真机封装类 `RpmReader`（`frame_edge_sampler.py:339–360`），当未开句柄、`ReadProcessMemory` 返回失败（`ok == 0`）或读取字节数不足 4 字节（`got.value != 4`）时，统一显式 `return None`，不会返回 0。
- **实跑黑盒证据**（探针 `_probe_code_lens.py`）：
  - `R1.1.1`：`reader` 返回 `None` → `read_one` 输出 `None`（`PASS`）。
  - `R1.1.2`：`reader` 抛出 `RuntimeError` → `read_one` 输出 `None`（`PASS`）。
  - `R1.4.1`：`reader` 返回合法业务 `0` → `read_one` 输出 `0`（`PASS`，证明真实读数 0 不被误杀）。
  - `R1.7.3`：未启用未开句柄的 `RpmReader.read_u32` → 输出 `None`（`PASS`）。

### 1.2 `bool` 拒收是否覆盖了 `True/False`（Python 里 `bool` 是 `int` 子类）？
- **判定**：**满足（完全覆盖）**。
- **技术分析**：
  在 Python 标准库中，`issubclass(bool, int) is True`，且 `False == 0`、`True == 1`。若仅写 `isinstance(v, int)`，`False` 会成功通过类型检查并由于 `0 <= 0 <= 0xFFFFFFFF` 被作为整数 `0` 返回，导致致命的「失败 `False` 变成合法业务读数 `0`」。
- **源码审查**：
  候选件在 `isinstance(v, int)` 前设立显式拦截门（第 97–98 行）：
  ```python
  if isinstance(v, bool):
      return None
  ```
  该分支在 `int` 检查前执行，优先剥离布尔类型。
- **实跑黑盒证据**：
  - `R1.2.1`：`reader` 返回 `False` → `read_one` 输出 `None`（`PASS`，杜绝 `False` 伪装成 0）。
  - `R1.2.2`：`reader` 返回 `True` → `read_one` 输出 `None`（`PASS`，杜绝 `True` 伪装成 1）。

### 1.3 越界值是否被拒？有没有漏掉的类型（float / numpy int / Decimal）？
- **判定**：**满足（无漏网之鱼，非标类型安全拒收）**。
- **审查与分类核验**：
  1. **越界整数**：
     - 负数（如 `-1`, `-0xFFFFFFFF`）：被 `v < 0` 严格拦截返回 `None`（探针 `R1.3.1`, `R1.3.2`）。
     - 大整数（如 `0x1_0000_0000`, `2**64`）：被 `v > 0xFFFFFFFF` 严格拦截返回 `None`（探针 `R1.3.3`, `R1.3.4`）。
  2. **浮点类型（`float`）**：
     - 测试用例：`0.0`, `123.45`, `float('nan')`, `float('inf')`。
     - 行为：`isinstance(float_val, int)` 为 `False`，被 `if not isinstance(v, int)` 统一拒收返回 `None`（探针 `R1.5.1–R1.5.3`）。`0.0` 绝不会被隐式转为整数 `0`。
  3. **高精度十进制数（`decimal.Decimal`）**：
     - 测试用例：`Decimal(0)`, `Decimal(100)`。
     - 行为：`isinstance(Decimal, int)` 为 `False`，统一拒收返回 `None`（探针 `R1.5.4`, `R1.5.5`）。
  4. **NumPy 标量整数（`numpy.uint32` / `numpy.int32` / `numpy.int64`）**：
     - 测试用例：`np.uint32(100)`, `np.int32(100)`, `np.int64(0)`。
     - 行为：在 Python 中，NumPy 整数类型继承自 `np.integer` / `np.number`，**并不**继承自 Python 内置 `int`（`isinstance(np.uint32(0), int) is False`）。因此它们全部被拒收并返回 `None`（探针 `R1.5.6–R1.5.8`）。
     - **复核结论**：在真机场景下，`RpmReader` 产出的 `buf.value` 为 Python 原生 `int`，不会出现 numpy 整数；在离线复查场景下，该行为保证了绝无任何复合对象或非原生类型绕过校验。
  5. **字符串与其他容器**：
     - `'123'`, `[]`, `{}` 均安全返回 `None`（探针 `R1.5.10`, `R1.5.11`）。

---

## 2. R2 · 读序与时间戳是否满足 D-19 的「每字段或读段起止时间戳」

### 2.1 起止时间戳合规性判定
- **判定**：**部分满足（PARTIAL）**。
- **依据与理由**：
  - **D-19 规格原文**（`RULING_D19.md` §1 第 5 条）：
    > 「在观测卡写定读序、**每字段或读段起止时间戳**、帧号前后读与跨帧标记、观测延迟与逻辑帧对应边界……」
  - **候选件现状**（`frame_edge_sampler.py:123–132`）：
    ```python
    rec["ts"]["f_pre"] = clock()
    rec["f_pre"] = read_one(reader, FRAME_VA)

    for key, va, _sem, _bnd in FIELDS:
        rec["va"][key] = va
        rec["ts"][key] = clock()
        rec["values"][key] = read_one(reader, va)

    rec["ts"]["f_post"] = clock()
    rec["f_post"] = read_one(reader, FRAME_VA)
    ```
  - **缺陷分析**：
    1. 候选件仅记录每次读取发起**之前**的单点时刻（`ts[k] = clock()`）。
    2. **缺少字段结束戳**：每个字段没有配对的 `ts_end`。
    3. **缺少读段闭合戳**：对于前 5 次读取，后一个读取的发起时间戳可以作为前一个读取耗时（含循环微小开销）的紧致上限；但是对于最后一次读取 `f_post`，在 `read_one(reader, FRAME_VA)` 完成后，代码**没有再调用一次 `clock()`**。
    4. **实测反例**（探针 `R2.3.3`）：若 `f_post` 在内核 RPM 或系统上下文切换中遭遇 50ms 调度抢占，`rec["ts"]["f_post"]` 仅记录了调用前的时刻，下游完全无法感知该次读取何时完成，也无法计算本次读段的完整总墙钟耗时（`t_end - t_start`）。
  - **是否构成不可接受的实质缺陷**：
    - **否**。这不构成导致读数错误、读数丢失或 null 变 0 的实质缺陷（`substantiveDefect=False`）。因为各字段的数值均由 RPM 真实读取沉淀，且中间字段之间具有单调的时间递增关系（探针 `R2.2.1`）。
    - 但对照 D-19「每字段或读段起止时间戳」的字面与方法学要求，当前只记了「起点」，未记「止点」，因此判定为**部分满足（PARTIAL）**。
- **满足 D-19 的最小改动方案**：
  若采用「读段起止时间戳」口径（开销最低、改动最小）：
  在 `read_sample` 的 `f_post` 读取完成后（第 133 行前）仅追加 1 行代码：
  ```python
  rec["ts"]["segment_end"] = clock()
  ```
  同时将 `rec["ts"]["segment_start"] = rec["ts"]["f_pre"]` 显式标出，即可 100% 达成 D-19「读段起止时间戳」要求。

### 2.2 帧号前读 / 后读时刻与四字段落点区间的判定判据
- **判定**：**满足（判据完备、数学严密）**。
- **判据体系与理论证明**：
  设前读时间为 $t_{pre}$、帧号为 $f_{pre}$；后读时间为 $t_{post}$、帧号为 $f_{post}$；四字段读取时间分别为 $t_1, t_2, t_3, t_4$，满足单调时序：
  $$t_{pre} \le t_1 < t_2 < t_3 < t_4 \le t_{post}$$
  由于引擎全局逻辑帧计数器 `CurrentFrame`（`0x00A8ED84`）在主循环正常帧推进中由 `0x55DE7E inc edx` 单步递增且非负单调，可确立以下三条归属判据：

  1. **判据一：单帧保证判据（`cross_frame == False`）**
     - **条件**：$f_{pre} \ne \text{None} \land f_{post} \ne \text{None} \land f_{pre} == f_{post} = F$。
     - **推导**：因为时钟起点 $t_{pre}$ 时帧号为 $F$，终点 $t_{post}$ 时帧号仍为 $F$，且帧号在帧循环中单调推进，故在整个区间 $[t_{pre}, t_{post}]$ 内，`CurrentFrame` 恒等于 $F$。
     - **归属**：全部四个字段的物理采样时刻均满足 $t_i \in [t_{pre}, t_{post}]$，因此确证全部字段读数** 100% 属于单一逻辑帧 $F$**。
     - 探针验证：`R2.4.1` 验证通过。

  2. **判据二：跨帧区间归属判据（`cross_frame == True`）**
     - **条件**：$f_{pre} \ne \text{None} \land f_{post} \ne \text{None} \land f_{pre} \ne f_{post}$（记 $f_{pre} = F, f_{post} = F + \Delta f, \Delta f \ge 1$）。
     - **推导**：说明在 $(t_{pre}, t_{post})$ 之间，引擎执行了至少一次 `0x55DE7E inc edx`。由于四字段是逐个非原子读取，无法得知帧跃变具体发生在 4 个字段中的哪两个之间。
     - **归属**：**禁止强行认定属于某一帧**，必须归属于闭区间 $[f_{pre}, f_{post}]$。四字段数据属跨帧混合态，分析时不可作为瞬时同一帧快照。
     - 探针验证：`R2.4.2` 验证通过。

  3. **判据三：不可判判据（`cross_frame is None`）**
     - **条件**：$f_{pre} \text{ is None} \lor f_{post} \text{ is None}$。
     - **推导**：帧号边界读数缺失，无法闭合区间两端。
     - **归属**：不可判，标记 `cross_frame = None`，严禁猜测。
     - 探针验证：`R2.4.3` 验证通过。

---

## 3. R3 · `df > 1`、`df < 0`、`f is None` 三条边界

### 3.1 `df > 1` 是否真的没有插值/补帧？
- **判定**：**满足（确无插值，真实留痕）**。
- **源码审查**（`frame_edge_sampler.py:164, 236–238, 243–254`）：
  - 当 `df > 1` 时，`classify_edge` 返回 `{"kind": "edge_missed", "df": df}`。
  - 在 `FrameEdgeTracker.feed()` 中：
    ```python
    elif cls["kind"] == "edge_missed":
        self.counts["edge_missed"] += 1
        self.missed_frames += (cls["df"] - 1)
    ```
  - 当条件满足时，直接将本次采样的 `values` 包装为一个单一事件返回：
    ```python
    ev = {
        "schema": SCHEMA,
        "markers": list(FIELD_MARKERS),
        "t": t,
        "f": f,
        "kind": cls["kind"],
        "df": cls["df"],
        "attribution": ("single_frame" if cls["df"] == 1
                        else "aggregate_over_%d_frames" % cls["df"]),
    }
    ```
  - **证据确凿**：全代码中无任何 `range(prev_f + 1, f)` 的循环补帧，无线性插值（`lerp`），无中间值合成。样本归属显式标注为 `aggregate_over_X_frames`，漏帧数下界严格累加至 `missed_frames`。
- **实跑黑盒证据**：
  - 探针 `R3.1.1–R3.1.4`：喂入 $100 \to 105$（$df=5$），仅生成 1 个事件，`edge_missed` 计数加 1，`missed_frames_lower_bound` 增加 4，未产生帧 101/102/103/104 的任何事件。

### 3.2 `df < 0` 标 `unjudgeable` 是否合理？还是应当进一步区分「进程重启」与「帧号回绕/重置」？
- **判定**：**满足（标 `unjudgeable` 合理；静态与采样条件限制下【当前不可区分】）**。
- **全镜像静态反汇编核查**（引用定谳证据 `lead/goal3t_nightwatch_20261102/swarm_20261104/P03/REPORT.md:21–32`）：
  1. `0x00A8ED84`（`CurrentFrame`）在整个 `gamemd.exe` `.text` 段中共有 10 个显式写点（全部使用 `mov` 指令，无其他 `inc/add` 直接写）：
     - `0x55DE81`：`mov [0xA8ED84], edx`（**全镜像唯一定常递增写回点**，前驱为 `0x55DE7E inc edx`）；
     - `0x5B7329`、`0x5E747C`、`0x795234`：显式常数归零 `mov dword ptr [0xA8ED84], 0`（分别位于场景释放、会话初始化、联机初始化）；
     - `0x52DA08`、`0x5E550F`、`0x68466B`：寄存器清零后写入 `mov [0xA8ED84], reg`（写 0）；
     - `0x5BB20C`、`0x686765`：ebp 清零后写入（写 0）；
     - `0x79758C`：网络同步帧重置；
     - 另外存在 2 处存档流反序列化写入（`push 0xA8ED84` @ `0x67F819` / `0x67FA19`），可将读档得到的历史帧写回。
  2. **`0x55DE7E` 邻近路径分析**：
     - 在 `0x55DE7E` 周边 1500 字节的主循环正常更新路径中，**没有任何分支执行写 0 或置初值**。所有写 0 点均位于高层状态重置或场景析构/重构中。
  3. **为什么「当前不可区分」**：
     - 单次只读轮询器仅观察单个内存地址 `0x00A8ED84` 的读数。
     - 若读数由大变小（$df < 0$），在物理上存在四种同构表现：
       (a) 目标进程崩溃重启，新进程分配了相同 PID 或 handle，帧号从 0 开始；
       (b) 游戏内部重新开始战役或重置地图，命中上述 9 处写 0 点之一；
       (c) 玩家载入了早前的存档，帧号跳回读档点的历史值；
       (d) u32 发生自然整数回绕（$2^{32}-1 \to 0$）。
     - 本候选件作为纯用户态离线观测件，未获取 `GetProcessTimes` 进程启动时间戳，未校验 PID 句柄代际，也未 hook/读取 `ScenarioClass` 指针。
     - 因此，在缺少外部生命周期信号的前提下，将 $df < 0$ 统一诚实标定为 `unjudgeable`（不可判）是唯一不越权、不武断的正确设计。
     - **结论**：**当前不可区分**。

### 3.3 `f is None` 时 `cross_frame` 记 `None`（不可判）而非 `False`，是否正确？
- **判定**：**满足（完全正确）**。
- **理由**：
  - `cross_frame == False` 具有强断言意义，表示「前后帧号均成功读取且相等，确证四字段落在单帧内」；
  - 若 `f_pre` 或 `f_post` 任一读取失败为 `None`，前后边界信息缺失，物理上处于未知状态；
  - 若记为 `False`，下游会将采样错误产生的残缺样本误当成「已验证的高置信度单帧样本」；若记为 `True`，又会伪报跨帧；
  - 记为 `None` 符合现代数据系统的三值逻辑（三态：`True` / `False` / `None`），不混淆「同帧」与「未知」；
  - 实跑探针 `R2.4.3` 验证其行为符合预期。

---

## 4. 探针构造与运行反例清单

在独立黑盒复核中，编写并实跑了探针 `_probe_code_lens.py`，记录于 `_probe_code_lens_out.txt`。主要反例与边界测试如下：

| 编号 | 构造反例场景 | 预期安全行为 | 实际实跑结果 | 结论 |
|---|---|---|---|---|
| **CE-1** | `reader` 返回 `False`（布尔失败） | 绝不可当成数字 0 返回，必须为 `None` | `read_one` 返回 `None` | 成功防范 Python `bool` 继承 `int` 漏洞 |
| **CE-2** | `reader` 返回 `float(0.0)` | 绝不可当成数字 0 返回，必须为 `None` | `read_one` 返回 `None` | 浮点零不冒充整数零 |
| **CE-3** | `reader` 返回 `np.uint32(100)` | 严格按原生 `int` 过滤 | `read_one` 返回 `None` | NumPy 标量被拒绝，类型边界严格 |
| **CE-4** | `f_post` 读取遭遇 50ms 挂起抖动 | 时间戳应能度量读段闭合时刻 | 候选件仅记录前戳，无闭合戳 | **实跑证实 R2 存在起止戳不完整缺陷** |
| **CE-5** | 序列 `[200, None, 201]`（中途丢帧） | `None` 步进不产事件，后续差分计算 | `feed` 产生 `df=1` 的 edge 事件 | `prev_f` 保持 200，差分延续 |
| **CE-6** | 序列 `[100, 105]`（$df=5$ 漏沿） | 绝不可生成 101–104 虚构事件 | 仅 1 个 `edge_missed`，`missed_frames=4` | 确无插值，留痕准确 |

---

## 5. 改进项清单（逐条列出，注明是否必须改）

1. **【建议改 · 非阻断】在 `read_sample` 中补齐读段闭合结束时间戳**：
   - *改进说明*：在 `f_post = read_one(reader, FRAME_VA)` 读取完毕后追加 `rec["ts"]["segment_end"] = clock()`（或 `f_post_end`），使突发采样段具备完整的 $[t_{start}, t_{end}]$ 边界，以 100% 贴合 D-19 §1 第 5 条「每字段或读段起止时间戳」的要求。
   - *级别*：**建议改**（不改不导致读数错误，但改后彻底满足规约）。
2. **【不必改 · 现状保持】NumPy 标量整数类型支持**：
   - *说明*：当前 `read_one` 会拒收 `np.uint32`，这在生产真机环境（使用 `ctypes` 原生 int）完全正确且安全；若未来需进行离线数据框架对接，可在入参前做 `int(v)` 转换，候选件内部维持原生严格校验即可。
   - *级别*：**不必改**。
3. **【不必改 · 现状保持】`df < 0` 的 `unjudgeable` 标记**：
   - *说明*：在没有额外获取系统级 PID 进程创建时间或游戏全局场景指针之前，保持 `unjudgeable` 标记为最佳实践，切勿随意拆解为不可靠的子状态。
   - *级别*：**不必改**。

---

## 6. 诚实账

1. **零真机**：本次复核完全基于静态源码逆向核验与离线内存黑盒探针，未启动 `gamemd.exe`、`ra2loader` 或 `YURI.exe`，未杀死任何进程，未读写活进程内存，严禁并实际未调用 `RpmReader(enable=True)`。
2. **零采样实现代码**：未编写任何 `ReadProcessMemory` 运行时实现，未引入任何 API hook、注入、MiniDump 或线程挂起操作。
3. **只读保护与唯一写域**：除本组指定的写域 `lead/re_line_20261105/A1_REVIEW/`（`part_code_lens.md`、`_probe_code_lens.py`、`_probe_code_lens_out.txt`）外，未修改任何其他项目文件、底稿或台账。
4. **实跑验证留痕**：
   - 探针运行命令：`python -I -X utf8 lead/re_line_20261105/A1_REVIEW/_probe_code_lens.py`
   - 探针执行结果：44/44 PASS，退出码 0，详见同目录 `_probe_code_lens_out.txt`。
