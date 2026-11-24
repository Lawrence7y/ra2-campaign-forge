# 帧沿触发采样候选件（D-20 步骤 A）独立复核判定书

> **复核任务**：依据 `REVIEW_TASK.md` 对 `lead/re_line_20261105/A1_SAMPLER_CANDIDATE/frame_edge_sampler.py` 实施双组独立背靠背复核。  
> **输入来源**：语义复核组（读写语义与帧沿篇 R1–R3）与合规复核组（边界与铁律篇 R4–R6）。  
> **基准规范**：`lead/re_line_20261105/D19_RULING/RULING_D19.md` §1 第 4–6 条及 `D20_RULING.md`。  
> **铁律执行**：全流程零真机、零活进程内存读写、零采样实现、禁止启用 `RpmReader(enable=True)`。  

---

## 0 总判

### 判定结论：**PARTIAL**

依据 `REVIEW_TASK.md` §2 规定的裁决准则：
1. **实质缺陷核定**：两组独立复核员均核定 `substantiveDefect = false`。候选件的底层读写语义（`read_one`）严格遵循「失败不补 0」，杜绝了 `bool` 伪装 0、非整数伪装及越界污染，未发现导致真实物理读数错误、丢弃有效读数或将 `None`/失败静默污染为 `0` 的致命缺陷。
2. **分项判定核定**：
   - **语义复核组**：`substantiveDefect: false`，判定为 **PARTIAL**（R1 满足、R2 部分满足、R3 满足；R2 缺少读段闭合结束时间戳，属非实质缺陷但需改进）。
   - **合规复核组**：`substantiveDefect: false`，判定为 **PARTIAL**（R4 部分满足、R5 部分满足、R6 满足；R4 证实中途读失败会导致后续状态机产生虚假冻结与虚假漏沿聚合，R5 证实指标命名易遭下游穿透产生业务冻结误用）。
3. **裁决综合**：根据「任一组报 substantiveDefect=true ⇒ REFUTED；否则只要有一组判 PARTIAL ⇒ PARTIAL；两组均 CONFIRMED 才判 CONFIRMED」之规则，两组均无实质缺陷且均判定为 PARTIAL，故本复核判定书总判裁定为 **PARTIAL**。

候选件整体结构合格、读写防线牢固、铁律完全合规，但存在 **2 项必须改** 的状态机边界与契约防御改进项，必须在落地合并前完成修改。

---

## 1 逐条判定

### R1 · 读写语义是否真的守住了「失败不补 0」
- **判定**：**满足**
- **依据与证据**：
  1. **无静默补 0 路径**（`frame_edge_sampler.py:87–103`）：`read_one(reader, va)` 函数中完全不存在 `v or 0`、`default=0` 或三元兜底表达式。当 `reader(va)` 抛出异常或读取失败时，直接走 `except Exception: return None`；
  2. **严格拦截 `bool` 类型**（`frame_edge_sampler.py:95–96`）：因 Python 中 `bool` 是 `int` 的子类（`issubclass(bool, int) is True`），若直接判定 `isinstance(v, int)` 会导致 `False` 被当作整数 `0` 返回。候选件在第 95 行显式设置门禁 `if isinstance(v, bool): return None`，成功杜绝 `False` 变 `0`、`True` 变 `1`（实跑探针 `R1.2.1`、`R1.2.2` PASS）；
  3. **严格拦截非原生与越界类型**（`frame_edge_sampler.py:97–100`）：`if not isinstance(v, int)` 与 `if v < 0 or v > 0xFFFFFFFF` 拦截了浮点数（`float(0.0)`、`nan`）、高精度十进制（`Decimal(0)`）、NumPy 标量整数（`np.uint32`，其基类为 `np.integer` 而非 Python `int`）以及所有负数和溢出大整数（实跑探针 `R1.3.1–R1.5.11` 全数 PASS）；
  4. **合法业务 0 正常透传**：`reader` 返回整数 `0` 时正常返回 `0`（实跑探针 `R1.4.1` PASS），区分了业务真实 0 与读失败。

### R2 · 读序与时间戳是否满足 D-19 的「每字段或读段起止时间戳」
- **判定**：**部分满足**
- **依据与证据**：
  1. **读序完全合规**（`frame_edge_sampler.py:123–132`）：执行序列严格为 `f_pre`（帧前读） $\to$ 四业务字段（`gen_stamp` / `scenario_frame` / `disp_frame` / `turn_stamp`） $\to$ `f_post`（帧后读），符合 D-19 §1 第 4 条要求；
  2. **跨帧归属判据数学严密**（`frame_edge_sampler.py:134–146`）：
     - 当 $f_{pre} == f_{post} = F$ 时，因帧号在区间内恒定，严格保证四字段属于单一逻辑帧 $F$（`cross_frame = False`）；
     - 当 $f_{pre} \ne f_{post}$ 时，四字段处于逻辑帧跃变过渡态，归属为闭区间 $[f_{pre}, f_{post}]$，标记 `cross_frame = True`，禁止强行认定属于某一瞬时帧；
     - 当 $f_{pre}$ 或 $f_{post}$ 任一读取失败为 `None` 时，标记 `cross_frame = None`（不可判），符合三值逻辑，绝不盲目充当 `False`；
  3. **起止时间戳存在单侧缺失缺陷**：D-19 §1 第 5 条明文规定记录「每字段或读段起止时间戳」。候选件当前仅在读取发起前记录单点 `clock()`（`ts[k] = clock()`）。对于前 5 次读取，后续字段的发起点可作为前字段的紧致耗时上界；但对于最后一次读取 `f_post`，完成后未再调用 `clock()`。若 `f_post` 读取中途遭遇内核调度抢占或延时，系统无法度量其自身耗时，亦无法闭合整段采样的实际总墙钟耗时（实跑探针 `R2.3.2`、`R2.3.3` 证实）。该项不引起读数错误，属于非实质缺陷，判定为部分满足。

### R3 · `df > 1`、`df < 0`、`f is None` 三条边界
- **判定**：**满足**
- **依据与证据**：
  1. **`df > 1`（漏沿）确无插值补帧**（`frame_edge_sampler.py:164, 243–254`）：当检测到跳帧时，`classify_edge` 标记 `kind="edge_missed"`，仅产生 1 个单一事件，将样本归属标注为 `aggregate_over_X_frames`，漏帧数下界严格累加 `(df - 1)`。源码与探针确认无任何 `range` 插值循环或虚构中间帧事件（实跑探针 `R3.1.1–R3.1.4` PASS）；
  2. **`df < 0` 标 `unjudgeable` 充分合理且【当前不可区分】**：全镜像反汇编核查（定谳报告 `lead/goal3t_nightwatch_20261102/swarm_20261104/P03/REPORT.md:21–32`）确认，`CurrentFrame` 在 `0x55DE7E` 邻近 1500 字节的主循环自增路径上无任何写 0 或置初值分支；9 处写 0 点分布在场景释放、会话初始化与联机重置中。在离线只读轮询且缺乏系统级 PID 启动时间戳、代际校验或全局场景指针的前提下，帧号回退、场景重置、读档回跳与进程崩溃重启在数学读数上不可区分，标定为 `unjudgeable` 并清空冻结计时是唯一严谨做法（实跑探针 `R3.2.1–R3.2.3` PASS）；
  3. **`f is None` 边界处理**：返回 `None` 且累加 `null_frames`，不产生误报事件。

### R4 · 首样本 vs `unjudgeable` 的区分是否引入新问题
- **判定**：**部分满足**
- **依据与证据**：
  1. **中途读失败引发状态混淆**（`frame_edge_sampler.py:167–175, 208–220`）：`classify_first` 仅通过 `prev_f is None` 判定首样本；而在 `feed()` 中，当遭遇 `f is None` 时，代码仅递增 `null_frames` 并返回 `None`，旧的 `self.prev_f`、`self.prev_t` 与 `self.freeze_start_t` 全部残留未清空，且未设任何采样断裂标志；
  2. **两大严重逻辑误判实跑证实**：
     - 反例 1 `[100, None, 100]`：中途读失败切断了连续性，但候选件将恢复后的同值误判为连续 `same`（$df=0$），错误地将读失败时段计入 `freeze_max_s`，导致虚假冻结；
     - 反例 2 `[100, None, 150]`：候选件将断裂后的帧号直接与断裂前的旧值求差（$150 - 100 = 50$），将读失败误判为 500Hz 轮询漏采 49 帧，并错误发出 50 帧聚合事件；
  3. **天真修复证伪**：若简单在 `f is None` 时置 `prev_f = None`，恢复点会被 `classify_first` 误判为第二次首样本（`counts['first']=2`）。必须建立正交的断裂状态标记。判定为部分满足。

### R5 · 「不得宣称业务字段冻结」这句防线是否真的有效
- **判定**：**部分满足**
- **依据与证据**：
  1. **防线易遭下游穿透**（`frame_edge_sampler.py:266–276`）：候选件当前仅在 `stats()` 中以自然语言字段 `note` 声明「freeze_max_s 只说明帧号连续未变的最长时段；不得据此宣称业务字段冻结」；
  2. **契约防御脆弱**：实跑模拟下游自动化流水线（如数据分析脚本、报警监控系统、CSV/DataFrame 导出），下游通常只提取顶层纯数值型指标，文本型 `note` 会被完全丢弃；泛化的键名 `freeze_max_s` 极易诱导消费方将其直接解读为「游戏/业务逻辑冻结时长」，击穿 D-19 F5/F11 明确设立的红线防线；
  3. **必须依赖 Schema 自解释**：必须将键名重命名为自解释的 `frame_clock_freeze_max_s`。判定为部分满足。

### R6 · 铁律合规
- **判定**：**满足**
- **依据与证据**：
  1. **受禁 API 静态全量清零**：AST 语法树解析与文本扫描确认，源码中 `CreateRemoteThread`、`WriteProcessMemory`、`SuspendThread`、`MiniDumpWriteDump`、`StackWalk`、`SetWindowsHookEx` 出现次数全部严格为 0（实跑探针 `R6.1` PASS）；
  2. **`RpmReader` 默认关闭且零触碰**（`frame_edge_sampler.py:303–369`）：实例化默认 `enable=False`；未启用时调用 `open()` 在首行即返回 `False`，不导入 `ctypes`，绝不调用 Windows API；未开句柄时 `read_u32()` 立即返回 `None`（实跑探针 `R6.2` PASS）；
  3. **模块导入零副作用**：顶层仅包含类与函数定义及常量赋值，子进程独立导入测试返回码为 0，无任何开句柄、起线程或自动发包逻辑（实跑探针 `R6.3` PASS）。

---

## 2 反例与实跑证据

### 2.1 语义组反例与实跑证据
> **实跑命令**：`python -I -X utf8 lead/re_line_20261105/A1_REVIEW/_probe_code_lens.py`  
> **基准记录**：`lead/re_line_20261105/A1_REVIEW/_probe_code_lens_out.txt`（44 项断言通过）

1. **R1 异常与类型拦截反例**：
   - 注入非法类型：向 `read_one` 传入返回 `False`、`float(0.0)`、`np.uint32(100)`、`Decimal(0)` 的 mock reader；
   - 实跑输出：
     - `[PASS] R1.2.1 reader 返回 False => read_one 返回 None (防 False 变 0)`
     - `[PASS] R1.5.1 float 0.0 => read_one 返回 None (防 float 0.0 漏入)`
     - `[PASS] R1.5.6 numpy uint32 => read_one 返回 None (因 isinstance(np.uint32, int) 为 False)`
   - 证明：成功阻断 Python `bool` 继承 `int` 导致的 `False` 变 0 隐患，且安全拦截非原生标量。
2. **R2 缺少读段闭合结束时间戳反例**：
   - 模拟时延：模拟 `f_post` 读取遭遇 50ms 调度抢占延时；
   - 实跑输出：
     - `[PASS] R2.3.2 缺少整段读段结束时间戳 rec['ts_end'] 或 rec['ts']['f_post_end']`
     - `[PASS] R2.3.3 实测验证：ts['f_post'] 只记发起点，无法测量 f_post 自身耗时与读段闭合时刻`
   - 证明：`ts['f_post']` 仅记录发起点，无法测量 `f_post` 自身耗时及采样读段的总耗时。
3. **R3 漏沿无插值反例**：
   - 注入漏沿序列：$100 \to 105$（$df=5$）；
   - 实跑输出：
     - `[PASS] R3.1.1 df=5 产出唯一事件，kind='edge_missed', df=5`
     - `[PASS] R3.1.2 df=5 attribution 为 aggregate_over_5_frames (非单帧真值)`
     - `[PASS] R3.1.4 edge_missed 计数加 1，绝未补造帧 101/102/103/104 的插值事件`
   - 证明：确无中间帧插值，留痕严密。
4. **R3 回退与重置反例**：
   - 注入回退序列：$105 \to 100$（$df=-5$）；
   - 实跑输出：
     - `[PASS] R3.2.1 df < 0 不产生 edge 事件 (返回 None)`
     - `[PASS] R3.2.2 df < 0 标记 unjudgeable 并使 counts['unjudgeable'] 加 1`
   - 证明：回退样本被严密归入 `unjudgeable`，清空冻结计时。

---

### 2.2 合规组反例与实跑证据
> **实跑命令**：`python -I -X utf8 D:/Project/ra2-campaign-forge/lead/re_line_20261105/A1_REVIEW/_probe_spec_lens.py`  
> **基准记录**：`lead/re_line_20261105/A1_REVIEW/_probe_spec_lens_out.txt`

#### 【反例 1: `[100, None, 100]` —— 虚假冻结】
- **输入序列**：`[(0.00, 100), (0.01, None), (0.02, 100)]`
- **状态机实跑追踪**：
  ```
  Step 1: t=0.00, f=100 -> event=None, prev_f=100, freeze_start_t=None
  Step 2: t=0.01, f=None -> event=None, prev_f=100 (残留旧值), freeze_start_t=None
  Step 3: t=0.02, f=100 -> event=None, prev_f=100, freeze_start_t=0.0, freeze_max_s=0.0200
  Final Stats: {"counts": {"samples": 3, "first": 1, "edge": 0, "edge_missed": 0, "unjudgeable": 0, "null_frames": 1}, "freeze_max_s": 0.02}
  ```
- **判定与危害**：不合理（虚假冻结）。中途读失败切断了物理时序连续性，但候选件将断裂后的恢复读数与断裂前的陈旧 `prev_f` 比较，误判为 `same`（$df=0$），错误地将读失败持续的墙钟时长累计入 `freeze_max_s`；在持续 5 秒读失败扩展实测中（`[100, None*5, 100]`），`freeze_max_s` 被虚报为 `6.0000s`。

#### 【反例 2: `[100, None, 150]` —— 虚假漏沿与假聚合归属】
- **输入序列**：`[(0.00, 100), (0.01, None), (0.02, 150)]`
- **状态机实跑追踪**：
  ```
  Step 1: t=0.00, f=100 -> event=None, prev_f=100, missed_frames=0
  Step 2: t=0.01, f=None -> event=None, prev_f=100 (残留旧值), missed_frames=0
  Step 3: t=0.02, f=150 -> event={'schema': 'FRAME_EDGE_V1', 't': 0.02, 'f': 150, 'kind': 'edge_missed', 'df': 50, 'attribution': 'aggregate_over_50_frames'}, missed_frames=49
  Final Stats: {"counts": {"samples": 3, "first": 1, "edge": 0, "edge_missed": 1, "unjudgeable": 0, "null_frames": 1}, "missed_frames_lower_bound": 49, "freeze_max_s": 0.0}
  ```
- **判定与危害**：不合理（虚假漏沿与假聚合归属）。断裂后的成功读数直接与断裂前的旧值求差（$150 - 100 = 50$），把读失败误判为「500Hz 轮询漏采 49 帧」，并强行归属为「50 帧聚合事件」，严重混淆了「采样读取失败」与「高频采样漏沿」，违背 D-19 规格。

#### 【天真修复对比验证 (`prev_f = None`)】
- **实跑追踪**：若仅在 `f is None` 时置 `prev_f = None`，当 `t=0.02, f=150` 到来时，因 `classify_first` 仅看 `prev_f is None`，恢复点被直接误判为窗口首样本（`counts['first'] = 2`），事件被吞没且未记录任何 `unjudgeable`。证实单一变量无法承载初始态与读断裂态。

---

### 2.3 Leader 独立复核实跑证据
> **实跑文件**：`lead/re_line_20261105/A1_REVIEW/_leader_verify_r4r5.py`  
> **实跑记录**：`lead/re_line_20261105/A1_REVIEW/_leader_verify_r4r5_out.txt`

1. **缺陷复核全体验属实**：
   - R4-1 虚报冻结（`freeze_max_s = 0.0200`，真实冻结应为 0）：**属实**；
   - R4-2 虚报漏沿（`missed = 49`，10ms 内物理不可能）：**属实**；
   - R4-3 冻结大幅虚增（跨 5s 读失败虚报为 `6.000s`）：**属实**；
   - R5 命名可穿透（下游只取数值键丢弃 `note`）：**属实**。
2. **Leader 附加发现**：
   - 候选件缺乏 $dt$ 与 $df$ 的物理相容性守卫：序列 `[(0.0, 100), (0.01, 150)]` 在 10ms 内跳变 50 帧（相当于 5000 fps），物理上绝不可能，但候选件依然发出 `edge_missed` 且无告警。

---

## 3 必须改的改进项

在候选件正式合并前，**必须完成以下 2 项核心修改**：

### 1. 【必须改】引入独立采样断裂状态机，杜绝虚假冻结与虚假漏沿
- **修改目标**：解决 R4 暴露的跨读失败误判缺陷。
- **具体要求**：
  1. 在 `FrameEdgeTracker` 中增设独立采样断裂标记（如 `self.prev_lost: bool`）；
  2. 当 `f is None` 时，必须立即清空 `self.freeze_start_t = None`（彻底切断连续冻结计时），并将 `self.prev_lost = True`；
  3. 当读失败后首次恢复成功读取（`self.prev_lost == True`）时，**严禁**与断裂前的陈旧 `self.prev_f` 比较，必须将该恢复样本记为不可判断裂点（例如记入 `counts["unjudgeable"]` 或独立的 `counts["resume_after_loss"]`），重置 `self.prev_f = f` 与 `self.prev_lost = False`，且不产出任何事件。

### 2. 【必须改】重命名指标键名为自解释的 `frame_clock_freeze_max_s`
- **修改目标**：解决 R5 暴露的 Schema 防御脆弱缺陷。
- **具体要求**：
  1. 将 `stats()` 返回字典中的顶层键名 `freeze_max_s` 显式重命名为 `frame_clock_freeze_max_s`（或 `current_frame_freeze_max_s`）；
  2. 建立 Schema 级防御契约，确保下游消费方仅通过字段名即可明确该指标仅指代逻辑帧号计数器连续不变的最长时段，切断业务字段冻结的误用路径。

---

### 附：其他建议改与不必改项
- **【建议改】解耦首样本判定与 `prev_f`**：在 `FrameEdgeTracker` 增设显式 `self.initialized` 布尔标志，使首采样语义与断裂状态完全解耦。
- **【建议改】补齐读段闭合时间戳**：在 `read_sample` 读完 `f_post` 后追加记录 `rec['ts']['segment_end'] = clock()`，彻底满足 D-19 §1 第 5 条「读段起止时间戳」的要求。
- **【不必改】NumPy 类型支持**：候选件内部维持原生 `int` 严格校验完全正确；若离线重放环境使用 numpy，可在传入前由调用方执行 `int(v)` 转换。
- **【不必改】`df < 0` 的细分**：在缺乏进程生命周期与场景指针辅助信号前，维持标定为 `unjudgeable` 属于唯一严谨做法。

---

## 4 诚实账

本判定书严格遵守「每个结论追溯到实跑命令与源码出处，未验项如实披露」之铁律：

### 4.1 复核员真实实跑并核验的检查项
1. **源码静态审查**：
   - 审查了 `lead/re_line_20261105/A1_SAMPLER_CANDIDATE/frame_edge_sampler.py` 全量源码（第 87–103 行类型拦截门禁、第 123–146 行读序与跨帧标记、第 167–254 行帧沿分类与追踪器状态转移、第 266–276 行指标字典、第 303–369 行 `RpmReader` 声明）；
   - 静态反汇编核查引用定谳证据 `lead/goal3t_nightwatch_20261102/swarm_20261104/P03/REPORT.md:21–32`（确认 `CurrentFrame` 0x55DE7E 邻近无写 0 分支，全镜像 9 处写 0 点分布在场景/会话重置）。
2. **语义组实跑探针**：
   - 执行命令：`python -I -X utf8 lead/re_line_20261105/A1_REVIEW/_probe_code_lens.py`；
   - 记录输出：`_probe_code_lens_out.txt`，44 项黑盒断言全数通过（R1 类型拦截、R2 起止戳缺失、R3 漏沿无插值与回退 unjudgeable）。
3. **合规组实跑探针**：
   - 执行命令：`python -I -X utf8 D:/Project/ra2-campaign-forge/lead/re_line_20261105/A1_REVIEW/_probe_spec_lens.py`；
   - 记录输出：`_probe_spec_lens_out.txt`，实跑验证反例 1 `[100, None, 100]`（证实虚假冻结）、反例 2 `[100, None, 150]`（证实虚假漏沿与假聚合）、反例 3 长时断裂虚报冻结 6.0 秒、天真修复失效验证，以及受禁 API 静态全量扫描（出现 0 次）、`RpmReader` 未启用阻断和子进程导入零副作用。
4. **Leader 独立验证实跑**：
   - 执行命令：`python -I -X utf8 lead/re_line_20261105/A1_REVIEW/_leader_verify_r4r5.py`；
   - 记录输出：`_leader_verify_r4r5_out.txt`，独立实跑证实合规组报告的 R4/R5 缺陷属实，并追加证实 dt/df 物理相容性守卫缺失。

### 4.2 明确声明的「未验」项
1. **真机游戏进程物理内存读数（未验）**：
   - 严格恪守零真机铁律，**未启动** `gamemd.exe`、`ra2loader` 或 `YURI.exe`，**未调用** `RpmReader(enable=True)`，**未打开**任何真实游戏进程句柄。所有读数与时序行为均由离线 mock reader 与确定性时序输入验证。
2. **真实 Windows 500Hz 物理定时器调度下的时钟抖动与抢占（未验）**：
   - 未在活机高负载场景下挂载真实 500Hz 高频轮询线程，`f_post` 的抢占延时系通过 mock 模拟，真实内核模式切换耗时未行物理实测。
3. **游戏引擎运行时多线程数据竞争动态观测（未验）**：
   - 游戏主循环更新 `CurrentFrame` 与四业务字段的汇编时序系基于静态反汇编分析与历史定谳报告，未在游戏执行期间挂载动态调试器进行断点单步跟踪。
