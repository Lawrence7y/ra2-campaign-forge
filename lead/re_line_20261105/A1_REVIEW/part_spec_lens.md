# A1 独立复核报告 · 边界与铁律复核（R4 / R5 / R6）

> **复核员**：合规复核员·边界与铁律  
> **复核对象**：`lead/re_line_20261105/A1_SAMPLER_CANDIDATE/frame_edge_sampler.py`  
> **实跑探针**：`lead/re_line_20261105/A1_REVIEW/_probe_spec_lens.py`  
> **实跑输出**：`lead/re_line_20261105/A1_REVIEW/_probe_spec_lens_out.txt`  
> **铁律执行**：零真机、未启动任何游戏进程、未调用 `RpmReader(enable=True)`、未打开任何系统进程句柄、全量测试基于静态 AST 与离线黑盒测试。

---

## 1. 逐条判定与证据展开

### R4 · 首样本 vs `unjudgeable` 的区分是否引入新问题

#### 1.1 问题分析与机制溯源
在 `frame_edge_sampler.py:167-175` 与 `:208-220` 中：
```python
def classify_first(prev_f):
    return prev_f is None
```
在 `FrameEdgeTracker.feed(t, f)` 中：
```python
if f is None:
    self.counts["null_frames"] += 1
    return None
```
**关键发现**：当窗口中途出现一次或多次读失败（`f=None`）时，`feed()` 仅递增 `null_frames` 并立即返回 `None`。此时：
1. `self.prev_f` 保持上一次成功读取的旧帧号（未重置为 `None`，也未置任何断裂标志）；
2. `self.prev_t` 保持上一次成功读取的旧时间戳；
3. `self.freeze_start_t` 保持原样，未被清空。

这直接导致了在窗口中途读失败后，下一次成功读取时发生**状态混淆与逻辑误判**。

---

#### 1.2 实跑反例与测试结果

##### 反例 1：序列 `[100, None, 100]`（实跑命令：`python -I -X utf8 _probe_spec_lens.py`）
- **时序输入**：`[(0.00, 100), (0.01, None), (0.02, 100)]`
- **实际实跑追踪**（见 `_probe_spec_lens_out.txt:9-17`）：
  - `t=0.00, f=100`: 首样本，`counts['first'] = 1`，`prev_f = 100`，`freeze_start_t = None`；
  - `t=0.01, f=None`: 读失败，`counts['null_frames'] = 1`，`prev_f` 残留为 100，`freeze_start_t` 仍为 None；
  - `t=0.02, f=100`: `prev_f=100`, `f=100`，`classify_edge(100, 100)` 判定为 `{"kind": "same", "df": 0}`！
    - 触发 `cls['kind'] == 'same'` 分支：`self.freeze_start_t = self.prev_t (0.00)`；
    - 计算 `span = t - self.freeze_start_t = 0.02 - 0.00 = 0.02`；
    - 导致 `self.freeze_max_s = 0.02`！
  - **最终 Stats**：
    ```json
    {"counts": {"samples": 3, "first": 1, "edge": 0, "edge_missed": 0, "unjudgeable": 0, "null_frames": 1}, "freeze_max_s": 0.02}
    ```
- **判定与误判后果**：**不合理（虚假冻结）**。在 `t=0.01` 时刻读数已经失败（真实物理帧号未知，可能发生跳变或暂停），但候选件在 `t=0.02` 恢复读取时，跨越未知断裂区间直接将两个 100 判定为 `same`，并累计了 `0.02s` 的连续冻结时长。若读失败持续 5 秒（见扩展反例 R4.3：`[100, None*5, 100]`），`freeze_max_s` 会被直接虚报为 `6.0000s`！

---

##### 反例 2：序列 `[100, None, 150]`（实跑命令：`python -I -X utf8 _probe_spec_lens.py`）
- **时序输入**：`[(0.00, 100), (0.01, None), (0.02, 150)]`
- **实际实跑追踪**（见 `_probe_spec_lens_out.txt:19-27`）：
  - `t=0.00, f=100`: 首样本，`counts['first'] = 1`，`prev_f = 100`；
  - `t=0.01, f=None`: 读失败，`counts['null_frames'] = 1`，`prev_f` 残留为 100；
  - `t=0.02, f=150`: `prev_f=100`, `f=150`，`classify_edge(100, 150)` 判定为 `{"kind": "edge_missed", "df": 50}`！
    - 触发 `cls['kind'] == 'edge_missed'` 分支：
    - `counts['edge_missed'] += 1`；
    - `self.missed_frames += (50 - 1) = 49`；
    - 产出事件：`{'f': 150, 'kind': 'edge_missed', 'df': 50, 'attribution': 'aggregate_over_50_frames'}`！
  - **最终 Stats**：
    ```json
    {"counts": {"samples": 3, "first": 1, "edge": 0, "edge_missed": 1, "unjudgeable": 0, "null_frames": 1}, "missed_frames_lower_bound": 49, "freeze_max_s": 0.0}
    ```
- **判定与误判后果**：**不合理（虚假漏沿与假聚合归属）**。在 `t=0.01` 发生读取失败时，数据流已经发生断裂（可能发生场景切换、进程重载或页面保护），候选件却直接对断裂前后的旧值求差 `150 - 100 = 50`，把单次/多次读失败误判为“500Hz 轮询漏采了 49 帧正常游戏更新”，并将 `t=0.02` 采集的业务字段强行标记为 `aggregate_over_50_frames`。这严重违背了 D-19 §1 第 5 条“重置/回绕/进程生命周期变化不能判明的区间标不可判”的规格底线。

---

##### 深度分析：天真修复为何会触发 `classify_first` 的新问题（反例 R4.4）
若有人试图简单地在 `f is None` 时置 `self.prev_f = None`：
- 由于 `classify_first(prev_f)` 的实现仅仅是 `prev_f is None`；
- 当 `t=0.02, f=150` 到来时，`classify_first(None)` 立即判定为 `True`；
- 导致 `counts['first']` 累加为 2（将中途恢复误报为窗口初始样本），且不会产出任何事件，`unjudgeable` 也无法统计。
- 这证明了：**`prev_f is None` 单一变量无法承载“初始无值”与“中途读失败断裂”两个完全正交的状态。**

---

#### 1.3 最小修复方案（判据与方案）
- **状态正交判据**：
  1. `initialized: bool` —— 标识该追踪器窗口是否已捕获首个有效帧号。
  2. `prev_lost: bool` —— 标识上一轮采样是否发生读失败（`f is None`）。
- **最小修复规则**：
  1. 当 `f is None` 时：
     - `self.counts["null_frames"] += 1`；
     - `self.prev_lost = True`（记录采样断裂）；
     - `self.freeze_start_t = None`（必须立即切断连续冻结计时，不得跨越断裂时段计算 `freeze_max_s`）；
     - `return None`。
  2. 当 `f is not None` 时：
     - 若 `not self.initialized`：标为首样本，`counts["first"] += 1; self.initialized = True; self.prev_f = f; self.prev_t = t; return None`；
     - 若 `self.prev_lost`（中途断裂后恢复点）：不可与断裂前的陈旧 `prev_f` 比较，判定为**不可判区间**，`counts["unjudgeable"] += 1; self.prev_lost = False; self.prev_f = f; self.prev_t = t; self.freeze_start_t = None; return None`（不生成伪聚合事件）；
     - 否则：进行正常的 `classify_edge(self.prev_f, f)` 判定。
- **R4 判定**：**部分满足（PARTIAL）**（候选件在此处存在逻辑边界缺陷，必须修复断裂状态机）。

---

### R5 · 「不得宣称业务字段冻结」这句防线是否真的有效

#### 2.1 防线有效性复核
在 `frame_edge_sampler.py:266-276` 中：
```python
def stats(self):
    return {
        "schema": SCHEMA,
        "markers": list(FIELD_MARKERS),
        "counts": dict(self.counts),
        "missed_frames_lower_bound": self.missed_frames,
        "freeze_max_s": round(self.freeze_max_s, 6),
        "note": ("freeze_max_s 只说明【帧号】连续未变的最长时段；"
                 "不得据此宣称业务字段冻结（D-19 F5/F11）。"),
    }
```
- **实跑观察**（见 `_probe_spec_lens_out.txt:42-47`）：
  - 顶层数值指标暴露了 `"freeze_max_s": 0.02`；
  - 模拟下游自动化流水线（如告警过滤、CSV 导出、Pandas/Polars 分析表格、LLM 评价汇总等）：程序提取纯数值列时直接提取 `row["freeze_max_s"]`，文本说明 `note` 会被完全旁路或丢弃。
- **分析结论**：**当前防线脆弱且不够有效**。
  - D-19 F5/F11 明确裁定：0x42CC80 再次调用重置等行为已从静态反证“帧号区间内所有业务计数器完全冻结”的普遍前提；
  - 命名为泛化的 `freeze_max_s`，下游开发员或算法会本能地将其理解为“游戏冻结时长”或“业务逻辑冻结时长”；
  - 数据契约的防御性必须建立在“字段命名自解释”上，不能寄托在旁路的自然语言免责 `note`。

#### 2.2 命名改进判定与理由
- **判定**：**应改（必须改）**。
- **建议命名**：`frame_clock_freeze_max_s`（或 `current_frame_freeze_max_s`）。
- **理由**：
  1. **契约级自解释（Defensive Schema）**：改名为 `frame_clock_freeze_max_s` 后，下游只要读取键名就能明确该指标**仅仅指 `CurrentFrame` 计数器连续未变的时长**，从根本上阻断外推到业务字段的可能性；
  2. **成本极低、零兼容负担**：当前候选件处于 D-20 步骤 A 离线单测阶段，下游尚无正式固化的生产消费方，此时重命名成本为零，无需后续折腾数据迁移；
  3. **严格闭环 D-19 红线**：彻底消除将帧号冻结误当业务冻结的隐患。
- **R5 判定**：**部分满足（PARTIAL）**（防线依靠弱注释存在穿透风险，必须修改指标键名）。

---

### R6 · 铁律合规（安全红线审计）

#### 3.1 源码受禁 API 静态全量审计
在 `_probe_spec_lens.py` 中对 `frame_edge_sampler.py` 进行了全量字符串匹配与 AST 符号扫描（输出见 `_probe_spec_lens_out.txt:52-60`）：
| 受禁 API 标识 | 扫描结果 | 判定 |
|---|---|---|
| `CreateRemoteThread` | 出现次数 = 0 | 合规 |
| `WriteProcessMemory` | 出现次数 = 0 | 合规 |
| `SuspendThread` | 出现次数 = 0 | 合规 |
| `MiniDumpWriteDump` | 出现次数 = 0 | 合规 |
| `StackWalk` | 出现次数 = 0 | 合规 |
| `SetWindowsHookEx` | 出现次数 = 0 | 合规 |

**结论**：源码 100% 干净，不存在任何注入、hook、挂线程或内存 dump 代码。单测 T7.3 结论属实。

---

#### 3.2 `RpmReader` 默认参数与未启用状态行为验证
实跑验证 `frame_edge_sampler.py:303-369` 中 `RpmReader` 的生命周期（见 `_probe_spec_lens_out.txt:61-75`）：
1. **默认参数**：`RpmReader(pid=99999)` 实例化时，`enable` 默认必为 `False`，`self.handle` 必为 `None`，`self.err` 必为 `None`；
2. **`open()` 行为**：在 `enable=False` 时，代码在第 317-319 行直接执行：
   ```python
   if not self.enable:
       self.err = "RpmReader disabled (enable=False)"
       return False
   ```
   **完全不导入 ctypes，完全不调用 Windows API `kernel32.OpenProcess`**；返回值明确为 `False`，`self.handle` 严格保持 `None`；
3. **`read_u32()` 行为**：当 `self.handle is None` 时，第 340-341 行直接 `return None`，**绝不触碰 `kernel32.ReadProcessMemory`**；
4. **`close()` 行为**：无句柄时为空操作，无异常。

**结论**：`RpmReader` 默认严格关闭，未启用状态下绝对不触碰系统调用。

---

#### 3.3 模块导入副作用审计
通过 AST 节点解析与独立子进程导入测试（见 `_probe_spec_lens_out.txt:76-80`）：
1. 模块顶层节点仅有 `Import` / `Assign` / `FunctionDef` / `ClassDef`，无任何可执行调用或顶层主程序块；
2. 隔离子进程命令 `python -I -X utf8 -c "import frame_edge_sampler; print('IMPORT_OK')"` 运行退出码为 0，输出 `IMPORT_OK`；
3. 导入期间未启动任何后台线程，未打开任何系统进程句柄，未探测网络或系统环境。

**结论**：模块为纯声明式定义，导入零副作用，绝对无自动发射/自动开句柄路径。

- **R6 判定**：**满足（CONFIRMED / SATISFIED）**。

---

## 2. 改进项清单（Action Items）

1. **[必须改]** 在 `FrameEdgeTracker` 中引入独立的采样断裂状态标记（如 `self.prev_lost`），当遇到 `f is None` 时清空 `freeze_start_t` 并置断裂标；恢复读取时将跨断裂区间记为 `unjudgeable`，禁止误判为连续冻结或跨断裂漏沿聚合。
2. **[必须改]** 将 `stats()` 中的指标键名 `freeze_max_s` 显式重命名为自解释的 `frame_clock_freeze_max_s`（或 `current_frame_freeze_max_s`），实现 Schema 级自解释防线，杜绝下游穿透 `note` 产生误用。
3. **[建议改]** 在 `FrameEdgeTracker` 增加显式的 `self.initialized` 布尔标志，使 `classify_first` 语义彻底脱离脆弱的 `prev_f is None`，避免后续代码维护再次混淆“窗口首采样”与“读失败断裂”。

---

## 3. 总体判定与实质缺陷核定

- **实质缺陷核定（`substantiveDefect`）**：**`false`**。
  - 本组复核范围（R4–R6）关注边界状态机与合规铁律。
  - 核心读数逻辑（`read_one` / `read_sample`）在失败时严格返回 `None`，未发现“让物理读数错误、丢弃有效读数或将 null 变 0”的实质缺陷。
  - R4 反例暴露的问题属于“断裂区间事件分类（`edge_missed` / `same` vs `unjudgeable`）与跨周期统计聚合”的算法边界缺陷；R5 属于指标命名契约防御性问题。均不属于物理读数被污染为 0 的实质缺陷。
- **本组总体判定（`partVerdict`）**：**`PARTIAL`**。
  - R4 部分满足（存在中途读失败误判，给出反例与最小修复）；
  - R5 部分满足（防线需通过重命名加固）；
  - R6 满足（铁律完全合规）。
  - 根据复核规则：无实质缺陷但存在必须改进项，总判为 **`PARTIAL`**。
