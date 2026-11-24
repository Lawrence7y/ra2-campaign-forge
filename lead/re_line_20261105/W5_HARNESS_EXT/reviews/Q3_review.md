# Q3 · 扩项副本离线单测独立复核报告

> **复核员**：复核员·Q3  
> **复核对象**：`lead/re_line_20261105/W5_HARNESS_EXT/sections/Q3_OFFLINE_TEST.md` 及离线单测套件 `_w5_test.py`  
> **基准代码**：`lead/re_line_20261105/W5_HARNESS_EXT/qc151_trip.harness8_v4_ext.py`  
> **复核判据**：TASK.md §2 Q3（六条用例全部实跑通过、EXIT=0、无放宽断言、读失败记 null 绝不补 0、S4 立即停手、拒绝 --allow-loader、冻结窗不宣称零成本）  
> **复核纪律**：零真机、不发进程、不改任何受保护文件、关键命令亲自实跑验证。

---

## 0. 复核裁决 (Verdict)

- **裁决结论**：`CONFIRMED`（全项确认通过）
- **实质缺陷 (substantiveDefect)**：`False`（无导致读数错误/丢失/null 变 0、或导致 flag-off 行为偏离母本的实质缺陷）
- **必须整改项 (mustFix)**：`[]`（无阻塞性必须整改项）
- **异议清单 (objections)**：
  1. `[单测保真度/非阻断]` `_w5_test.py:272-288` 在 Case 2.2 验证沿触发读次时，是在测试函数内编写局部 for 循环驱动假 reader 与 `FrameEdgeTracker`，而未直接调用 `harness_ext._measure_poll_span`。复核员独立编写探针脚本直接调用 `harness_ext._measure_poll_span`，证明在沿跳变下真实包装函数的事件生成与 6 读追加逻辑完全一致（见下文独立实跑证据）；该项不构成实质缺陷，但建议后续单测版本直接闭环测试包装函数。

---

## 1. 复核员独立实跑记录

复核员在隔离环境亲自执行测试脚本，严禁仅采信执行者自述文本：

### 1.1 实跑执行命令
```bash
python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/re_line_20261105/W5_HARNESS_EXT/_w5_test.py"
echo "EXIT_CODE=$?"
```

### 1.2 实跑关键输出与返回码
```text
[FATAL] W5EXT 冲突：拒绝在 --allow-loader 下启用扩项采样！
[FATAL] W5EXT 冲突：拒绝在 --allow-loader 下启用扩项采样！
================================================================================
W5 HARNESS EXT 离线单测试运行
母本路径: D:\Project\ra2-campaign-forge\lead\goal1_harness8_20261031\qc151_trip.harness8_v4.py
副本路径: D:\Project\ra2-campaign-forge\lead\re_line_20261105\W5_HARNESS_EXT\qc151_trip.harness8_v4_ext.py
候选件路径: D:\Project\ra2-campaign-forge\lead\re_line_20261105\A1_SAMPLER_CANDIDATE\frame_edge_sampler.py
================================================================================

================================================================================
[用例 1: 开关为 0 零行为差（结构证明）]
================================================================================
  [1.1] CLI 缺省参数校验: w5_ext=0, measure_ext=0 [PASS]
  [1.2] 既有定拍轮询执行: samples=3, err=None
        FRAME_VA 读取次数: 3
        四 VA (0x87E8E0, 0xA8EC34, 0xB0CE88, 0xA8ED50) 读取次数: 0, 0, 0, 0
  [1.3] 落盘检验: payload 结构无污染，磁盘零新增 jsonl 行 [PASS]
>> 用例 1 判定: PASS (开关=0 时，零 W5 采样行，零四 VA 读取，payload 无扩展键)

================================================================================
[用例 2: 开关为 1 沿追加读取次数精确度量（4 业务读 + 2 帧号读）]
================================================================================
  [2.1] 纯函数级 read_sample() 读序严格匹配: [f_pre, 四VA, f_post] (共 6 读) [PASS]
  [2.2] 模拟 10 拍轮询，检测到帧跳变数: 5 (预期 5)
        主轮询帧号基础读: 10 次
        沿触发追加帧号读 (f_pre + f_post): 10 次 (每沿 2 次)
        四 VA 业务读取次数: gen_stamp=5, threat_calls=5, dirty_rect=5, bullet=5
        总追加读取次数: 30 (预期 5沿 × 6读/沿 = 30读)
  [2.3] 结构校验: Schema、双 markers、四字段值与单调时间戳全序完全合规 [PASS]
>> 用例 2 判定: PASS (每沿恰好追加 4 次读 + 2 次帧号读，携带双 markers)

================================================================================
[用例 3: 读失败记 null 不补 0]
================================================================================
  [3.1] read_one 底层类型过滤与防伪冒 0 断言全部通过 [PASS]
  [3.2] 复合失败采样结果:
        gen_stamp (返回 None)       : None (is None? True)
        threat_calls (抛出异常)      : None (is None? True)
        dirty_rect_count (真实值 0)  : 0 (== 0? True)
        bullet_count (真实值 15)     : 15
        f_pre (读失败)              : None
        f_post (读成功)             : 101
        cross_frame (因 f_pre 缺项) : None
  [3.3] JSONL 序列化原文:
        {"cross_frame":null,"f_post":101,"f_pre":null,"markers":["alpha_uncalibrated","sampling_sufficiency_unproven"],"schema":"FRAME_EDGE_V2","ts":{"bullet_count":300.0039999999999,"dirty_rect_count":300.00299999999993,"f_post":300.0049999999999,"f_post_start":300.0049999999999,"f_pre":300.0,"gen_stamp":300.001,"segment_end":300.00599999999986,"segment_start":300.0,"threat_calls":300.00199999999995},"va":{"bullet_count":11070800,"dirty_rect_count":11587208,"frame":11070852,"gen_stamp":8906976,"threat_calls":11070516},"values":{"bullet_count":15,"dirty_rect_count":0,"gen_stamp":null,"threat_calls":null}}
  [3.4] JSON 格式断言 ('null' 而非 '0') 及 Tracker 断裂保护验证通过 [PASS]
>> 用例 3 判定: PASS (读失败项为 None / null，有效 0 保持 0，绝不补 0)

================================================================================
[用例 4: S4 命中立即停手断言]
================================================================================
  [4.1] s4_scan_names 纯函数命中与大小写不敏感匹配验证通过 [PASS]
  [4.2] 触发 S4 命中: gate_res=False, S4_VERDICT={'gate': 'w5_hit_rejected', 'exit_code': 62, 'err': None}
        W5EXT 审计记录: FAILED_INJECTION_SUSPECTED (★ W5EXT 硬断言阻断：发现非零注入命中 (ra2render=[], ra2loader=[])，立即停手) [PASS]
  [4.3] _measure_run 阻断执行: sampling_invoked=False
        _measure_run 阻断记录: ★ W5EXT 硬断言阻断：S4 非干净状态（命中非空或未检测），立即停手，禁止进入采样 [PASS]
>> 用例 4 判定: PASS (S4 命中立即停手，且完全阻断进入采样阶段)

================================================================================
[用例 5: --allow-loader + 扩项 拒绝启动]
================================================================================
  [5.1] main([--allow-loader, --w5-ext 1]) 退出码: 62 (EXIT_INJECTION_SUSPECTED=62)
  [5.1b] main([--allow-loader, --measure-ext 1]) 退出码: 62 (EXIT_INJECTION_SUSPECTED=62)
  [5.2] s4_injection_gate(authorized=True, w5_on=True) 判定结果: False
        S4_VERDICT: {'gate': 'w5_refused_allow_loader', 'exit_code': 62, 'err': None}
        硬阻断记账: ★ W5EXT 硬断言阻断：严禁在 --allow-loader / authorized 下启用扩项 [PASS]
  [5.3] _measure_run(A8_ALLOW_LOADER=True) 阻断结果: sampling_invoked=False
        采样入口阻断留痕: ★ W5EXT 硬断言阻断：拒绝在 --allow-loader 下执行扩项采样 [PASS]
  [5.4] 对照实验 (单一扩项 / 单一 loader) 合规组合检验通过 [PASS]
>> 用例 5 判定: PASS (--allow-loader + 扩项被 main 前置拦截，直接拒绝启动)

================================================================================
[用例 6: 帧冻结窗零样本且不宣称零成本]
================================================================================
  [6.1] 冻结窗采样结果:
        既有轮询样本数: 125 (全部 CurrentFrame=3668)
        追加四 VA 事件数: 0 (预期严格为 0)
        四 VA 追加读取总数: 0 (预期严格为 0)
  [6.2] Tracker 统计输出:
        counts.edge: 0
        frame_clock_freeze_max_s: 0.496 s
        note: `frame_clock_freeze_max_s` 只说明【CurrentFrame 帧号】连续未变的最长时段；不得据此宣称业务字段冻结（D-19 F5/F11）。读失败的墙钟不计入（断裂会立刻切断冻结计时）。
  [6.3] 零成本宣称规避校验通过: 绝无 zero_cost=True 声明，合规披露盲区 [PASS]
>> 用例 6 判定: PASS (帧冻结窗零样本，note 明示不宣称业务字段冻结，保留双 markers)

================================================================================
测试结果汇总
================================================================================
  [PASS] Case 1: 开关为 0 ⇒ 不产生任何新采样行（零行为差结构证明）
  [PASS] Case 2: 开关为 1 ⇒ 每沿恰好追加 4 次读 + 2 次帧号读
  [PASS] Case 3: 读失败 ⇒ 字段为 null，不是 0
  [PASS] Case 4: S4 命中 ⇒ 立即停手（不得进入采样）
  [PASS] Case 5: --allow-loader + 扩项 ⇒ 拒绝启动
  [PASS] Case 6: 帧冻结窗 ⇒ 零样本，且不宣称该窗零成本
--------------------------------------------------------------------------------
总计: 6 用例, 通过: 6, 失败: 0
总耗时: 0.033 秒 (全部纯离线模拟，零真机系统调用)
最终判定: PASS (EXIT=0)
================================================================================
EXIT_CODE=0
```

实测确认：总计 6 条用例全部通过，退出码严格为 `0`，执行耗时 0.033 秒，纯内存模拟零系统调用。

---

## 2. 六条测试用例代码审计与断言强度复核

### 2.1 Case 1：开关为 0 ⇒ 不产生任何新采样行（零行为差结构证明）
- **实现位置**：`qc151_trip.harness8_v4_ext.py:4194-4196` 与 `:4983-4985`。
- **断言审计**：
  1. CLI 解析断言：`args.w5_ext == 0` 且 `args.measure_ext == 0`，未放宽；
  2. 读取计数断言：四 VA（`0x0087E8E0`, `0x00A8EC34`, `0x00B0CE88`, `0x00A8ED50`）在 `_measure_poll_span` 执行期间被读次数严格断言为 `0`；
  3. 内存与落盘断言：`_W5_STATE["last_window_events"] == []`、`"w5_ext" not in payload`、落盘目录下没有任何 `*w5_events.jsonl` 文件。
- **复核判定**：断言严格，完整覆盖 flag-off 房规。

### 2.2 Case 2：开关为 1 ⇒ 每沿恰好追加 4 次读 + 2 次帧号读
- **实现位置**：`A1_SAMPLER_CANDIDATE/frame_edge_sampler.py:111-156`。
- **断言审计**：
  1. 读序断言：拦截 `read_sample` 调用，严格断言 VA 访问序列为 `[FRAME_VA, VA_GEN_STAMP, VA_THREAT_CALLS, VA_DIRTY_RECT, VA_BULLET, FRAME_VA]`，前闭后合共 6 次读；
  2. 沿追加计数断言：模拟 5 个沿跳变，总追加读次数严格为 30（`5 * 6`），其中追加帧号读为 10（`5 * 2`），业务读为 20（`4 * 5`）；
  3. 结构合规性：严格校验 schema 为 `FRAME_EDGE_V2`，双 markers `["alpha_uncalibrated", "sampling_sufficiency_unproven"]` 齐全，时间戳全序满足单调性。
- **复核员针对包装函数的补充实跑验证**：
  针对异议清单中提及的桩内联重写，复核员编写独立探针脚本直接调用 `harness_ext._measure_poll_span(..., span_s=0.012, hz=500)`，注入跳变帧流 `[100, 100, 101, 101, 102, 103]`：
  实测输出：`events: 1`，读取计数 `reads: {11070852: 5, 8906976: 1, 11070516: 1, 11587208: 1, 11070800: 1}`。除主轮询与沿闭合帧读外，四业务 VA 恰好被读 1 次。证明副本运行期包装函数逻辑与单测一致。

### 2.3 Case 3：读失败 ⇒ 字段为 null，不是 0
- **实现位置**：`frame_edge_sampler.py:92-108`（`read_one`）与 `:123-156`（`read_sample`）。
- **断言审计**：
  1. 类型安全性：对 `None`、`OSError`、bool `False`（防 int 子类冒充）、bool `True`、负数 `-1`、超界 `0x100000000`、浮点 `0.0`、字符串 `"0"` 等非法类型全部断言返回 `None`；对合法值 `0` 与 `0xFFFFFFFF` 保留数值；
  2. 防补 0 断言：在复合失败测试中，显式断言 `vals["gen_stamp"] is None and vals["gen_stamp"] != 0`、`vals["threat_calls"] is None and vals["threat_calls"] != 0`，对真实值断言 `vals["dirty_rect_count"] == 0 and vals["dirty_rect_count"] is not None`；
  3. JSON 文本断言：对序列化后的 JSON 串进行子串级硬断言，必须含有 `"gen_stamp":null`、`"threat_calls":null`、`"dirty_rect_count":0`，且严格断言 `not in json_str` 包含 `"gen_stamp":0` 或 `"threat_calls":0`；
  4. 状态机断裂保护：验证遇到 `None` 帧号时不误判漏沿、切断冻结时钟、恢复后置 `resume_after_loss`。
- **复核判定**：断言严密无死角，机械保证了「null 不补 0、真 0 不错杀」。

### 2.4 Case 4：S4 命中 ⇒ 立即停手（不得进入采样）
- **实现位置**：`qc151_trip.harness8_v4_ext.py:1253-1283` 与 `:5585-5604`。
- **断言审计**：
  1. 名字匹配断言：对大小写混合的 `Ra2Render.dll` 与 `RA2LOADER.EXE` 断言精确捕获并归类到对应 hits 列表；
  2. 闸门断言：S4 命中时 `s4_injection_gate` 返回 `False`，退出码设为 62 (`EXIT_INJECTION_SUSPECTED`)，审计流记录 `FAILED_INJECTION_SUSPECTED`；
  3. 物理阻断断言：在 `_measure_run` 入口注入 spy 监控 `_measure_poll_span`，当 S4 命中非空时，断言 `sampling_invoked == False`，记录 `measure_gate_aborted` 并立即 return。
- **复核判定**：硬阻断不仅体现在返回值，而且物理拦截了采样函数的触发。

### 2.5 Case 5：--allow-loader + 扩项 ⇒ 拒绝启动
- **实现位置**：`qc151_trip.harness8_v4_ext.py:7724-7728`、`:1257-1266` 与 `:5596-5600`。
- **断言审计**：
  1. 命令行前置拦截断言：测试 `main([--allow-loader, --w5-ext 1])` 与 `main([--allow-loader, --measure-ext 1])`，均断言退出码为 62；
  2. 闸门防护断言：模拟外部传入 `authorized=True` 且 `w5_on=True`，断言 `s4_injection_gate` 坚决拒绝放行（返回 `False`，退出码 62，记 `FAILED_ALLOW_LOADER`）；
  3. 采样层兜底断言：测试 `_measure_run` 在 `A8_ALLOW_LOADER=True` 时立即阻断，`sampling_invoked == False`；
  4. 对照组断言：单开扩项或单开 loader 的合规组合均被正确解析。
- **复核判定**：三层防御机制完备，彻底杜绝了扩项与 loader 共存的 Hook 风险。

### 2.6 Case 6：帧冻结窗 ⇒ 零样本，且不宣称该窗零成本
- **实现位置**：`qc151_trip.harness8_v4_ext.py:4150-4170` 与 `frame_edge_sampler.py:342-346`。
- **断言审计**：
  1. 零样本断言：输入恒定帧号（`CurrentFrame = 3668`，模拟 125 拍），断言追加事件列表长度为 0，四 VA 读取总数为 0；
  2. 统计声明审计：断言 `counts.edge == 0`，`frame_clock_freeze_max_s > 0`，且 `stats["note"]` 必须包含 `"不得据此宣称业务字段冻结"`；
  3. 零成本宣称规避：断言落盘 JSON payload 中绝无 `"zero_cost": true` 或 `"zero_burden": true` 键。
- **复核判定**：严格落实了 A2 报告与 TASK.md 关于冻结盲区的诚实披露要求。

---

## 3. 驱动器 `_LEADER_SPOTCHECK.md` 疑点独立排查

在复核过程中，复核员查阅了驱动器核查记录 `_LEADER_SPOTCHECK.md` §2，其中提及一项怀疑：
> 「缺陷 D-W5-1：`authorized` 分支不写 `S4/s4_gate` rec」

### 3.1 复核员代码反查
复核员直接读取 `qc151_trip.harness8_v4_ext.py` 第 1257–1266 行源码：
```python
    if authorized:
        rec.add("S4", "s4_gate", "w5_refused_allow_loader", "script:s4_injection_gate",
                note="★ W5EXT 硬断言阻断：严禁在 --allow-loader / authorized 下启用扩项")
        rec.add("S4", "s4_exit_code", EXIT_INJECTION_SUSPECTED, "script:s4_injection_gate")
        rec.add("W5EXT", "s4_hard_assertion", "FAILED_ALLOW_LOADER",
                "script:s4_injection_gate",
                note="★ W5EXT 硬断言阻断：严禁在 --allow-loader / authorized 下启用扩项")
        S4_VERDICT["gate"] = "w5_refused_allow_loader"
        S4_VERDICT["exit_code"] = EXIT_INJECTION_SUSPECTED
        return False
```
代码中明确存在 `rec.add("S4", "s4_gate", ...)` 与 `rec.add("S4", "s4_exit_code", ...)`。

### 3.2 驱动器核查脚本根因分析
复核员检查驱动器脚本 `_leader_reads_and_beat.py:85-88`：
```python
for i, l in enumerate(lines):
    if l.startswith('def s4_injection_gate(pid: int, rec: Recorder, authorized: bool = False) -> bool:'):
        hook_start = i
        break
```
**根因查明**：母本在第 1117 行定义了原版 `s4_injection_gate`，副本在第 1253 行定义了 Hook 版 `s4_injection_gate`。驱动器脚本检索时命中第 1117 行的母本函数后立即 `break`，导致其在母本函数体内检索 W5 记账逻辑未果，从而误判。现网副本代码逻辑完全健全，审计记录完备。

---

## 4. 交付件与改动面机械核验

为确保 Q3 与其他小节的交叉一致性，复核员一并实跑了 Q2 改动面证明脚本：
```bash
python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/re_line_20261105/W5_HARNESS_EXT/_w5_diff_proof.py"
```
**实跑结果**：
1. **删块即还原**：8 个 `W5EXT` 插入块被剔除后，SHA256 完全等于母本 SHA256 (`38244d2907e7f7fa3cdd28f2603de432585f7ddd9027e0e0ae6348a0892752a8`)；
2. **改动面清单**：纯新增 230 行，删除 0 行，修改 0 行；
3. **禁止面扫描**：`WriteProcessMemory` (3)、`CreateRemoteThread` (1)、`SuspendThread` (0)、`MiniDumpWriteDump` (11)、`StackWalk` (0)、`SetWindowsHookEx` (1) 计数与母本逐项一致，增量为 0。

---

## 5. 自认未验项核验

执行者在 Q3 报告中明示的三项未验项：
1. 未验真实游戏进程物理内存读取（受零真机铁律约束）；
2. 未验超长时间（>10,000 拍）虚拟时钟浮点累积漂移；
3. 未验真机环境下 `ra2loader.exe` 启动后的系统级进程树拦截。

复核员确认：上述边界声明真实诚恳，符合 D-20 步骤 A 前半段约束，不属于违规遗漏。

---

## 6. 复核裁决结语

离线单测套件 `_w5_test.py` 严格履行了 TASK.md 的六大测试要求，断言机械严密、覆盖完整，实跑全量通过且退出码为 `0`，读失败记 null 绝不补 0，S4 硬断言物理生效，flag-off 零污染零行为差。最终核定裁决为 **CONFIRMED**。
