# Q3 · 扩项副本离线单测报告（注入假 Reader 六项全覆盖）

> **责任人**：单测设计员·离线  
> **依据**：`lead/re_line_20261105/W5_HARNESS_EXT/TASK.md` §2 Q3  
> **被测件**：  
>   - 扩项副本：`lead/re_line_20261105/W5_HARNESS_EXT/qc151_trip.harness8_v4_ext.py`  
>   - 候选件：`lead/re_line_20261105/A1_SAMPLER_CANDIDATE/frame_edge_sampler.py` (V2)  
> **测试脚本**：`lead/re_line_20261105/W5_HARNESS_EXT/_w5_test.py`  
> **测试产物**：`lead/re_line_20261105/W5_HARNESS_EXT/_w5_test_out.txt`  
> **执行约束**：零真机、纯假 reader 注入、零进程触碰、全用例必须 `EXIT=0`。

---

## 0. 一句话结论

**离线单测 6 项用例全部严格实跑通过（6/6 PASS，脚本退出码 `EXIT=0`），零真机、零放宽断言**：
机械证明了开关为 0 时零行为差与零四 VA 读取、开关为 1 时每沿恰好追加 4 次业务读 + 2 次帧号读（共 6 读）、读失败字段严格为 `null` 而非 `0`、S4 命中立即停手且物理阻断进入采样、`--allow-loader` 扩项组合被入口前置拦截拒绝启动、以及帧冻结窗零样本且严禁宣称零成本。

每份事件与统计均如实保留两个未证标记：
`["alpha_uncalibrated", "sampling_sufficiency_unproven"]`。

★ **安全披露**：
> 「本副本在启用扩项前断言 S4 零命中；若 `ra2render` 在场，`threat_calls` 字段**不可解释为入口调用总数**。」

---

## 1. 实跑命令与原始输出

### 执行命令
```bash
python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/re_line_20261105/W5_HARNESS_EXT/_w5_test.py"
```

### 退出状态
`EXIT=0`（总耗时 0.027 秒，全部为纯内存/函数桩执行，零系统调用）

### 原始输出全文 (`_w5_test_out.txt`)
```text
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
总耗时: 0.027 秒 (全部纯离线模拟，零真机系统调用)
最终判定: PASS (EXIT=0)
================================================================================
```

---

## 2. 六项用例逐项机制与机械判据对照

### 2.1 用例 1：开关为 0 ⇒ 不产生任何新采样行（零行为差结构证明）
- **依据与代码位置**：`qc151_trip.harness8_v4_ext.py:4167-4171`（`_measure_poll_span` 钩子）与 `:4969-4972`（`_measure_write_json` 钩子）。
- **执行机制**：
  - 调用 `w5_reset_state()` 保证 `_W5_STATE["on"] = False`；
  - 注入 fake reader，模拟 500 Hz 逻辑帧前进（`100 -> 101 -> 102`）；
  - 调用 `_measure_poll_span`，内部通过 `if not _W5_STATE["on"]: return _measure_poll_span_mother(...)` 严格直通母本实现；
- **机械断言与实测值**：
  - 四 VA（`0x0087E8E0`, `0x00A8EC34`, `0x00B0CE88`, `0x00A8ED50`）各自读取次数：**严格为 0**；
  - `_W5_STATE["last_window_events"]`：**严格为空列表 `[]`**；
  - 落盘 payload 检查：`"w5_ext" not in payload` 为 True；
  - 磁盘文件检查：输出目录下零 `*w5_events.jsonl` 文件；
- **判定**：**PASS**。结构上保证了开关为 0 时零行为差、零污染。

---

### 2.2 用例 2：开关为 1 ⇒ 每沿恰好追加 4 次读 + 2 次帧号读
- **依据与代码位置**：`A1_SAMPLER_CANDIDATE/frame_edge_sampler.py:111-149`（`read_sample`）与 `TASK.md:65`。
- **执行机制**：
  - 纯函数级检验：注入 spy reader，拦截 `read_sample()` 的全部读取 VA，验证顺序为：`f_pre (0xA8ED84)` → `gen_stamp (0x87E8E0)` → `threat_calls (0xA8EC34)` → `dirty_rect (0xB0CE88)` → `bullet (0xA8ED50)` → `f_post (0xA8ED84)`，共 6 次读；
  - 循环级检验：设置 `_W5_STATE["on"] = True`，喂入 10 拍包含 5 个真实沿（`100->101`, `101->102`, `102->103`, `103->105` [df=2], `105->106`）的帧序列；
- **机械断言与实测值**：
  - 主轮询基础帧号读：10 次；
  - 沿触发追加帧号读（`f_pre + f_post`）：**10 次**（5 沿 × 2 帧号读/沿）；
  - 四 VA 各自读取次数：**各 5 次**（5 沿 × 1 读/沿）；
  - 总追加读取次数：**30 次**（5 沿 × 6 读/沿）；
  - 单沿追加结构：**恰好 4 次业务读 + 2 次帧号读**；
  - 事件结构：全量携带 `markers: ["alpha_uncalibrated", "sampling_sufficiency_unproven"]` 与 `schema: "FRAME_EDGE_V2"`；时间戳单调全序满足 `ts[f_pre] <= ts[gen_stamp] <= ... <= ts[f_post]`。
- **判定**：**PASS**。

---

### 2.3 用例 3：读失败 ⇒ 字段为 null，不是 0
- **依据与代码位置**：`frame_edge_sampler.py:92-108`（`read_one`）与 `:123-156`（`read_sample`）。
- **执行机制**：
  - 针对 `read_one` 进行非法类型全集扫描：`None`、`OSError`、bool `False`（防 int 子类冒充）、bool `True`、负数 `-1`、超界 `0x100000000`、浮点 `0.0`、字符串 `"0"`；全部断言返回 `None`；真实 `0`（`0x0`）断言返回 `0`；
  - 针对 `read_sample` 进行复合场景注入：`gen_stamp` 返回 `None`、`threat_calls` 抛出 `RuntimeError`、`dirty_rect_count` 读到真实值 `0`、`bullet_count` 读到 `15`、`f_pre` 读失败返回 `None`；
- **机械断言与实测值**：
  - `vals["gen_stamp"] is None and vals["gen_stamp"] != 0` 为 True；
  - `vals["threat_calls"] is None and vals["threat_calls"] != 0` 为 True；
  - `vals["dirty_rect_count"] == 0 and vals["dirty_rect_count"] is not None` 为 True；
  - `sample["cross_frame"] is None` 为 True（不可判）；
  - JSONL 文本断言：出现 `"gen_stamp":null`、`"threat_calls":null`、`"dirty_rect_count":0`；**绝不出现 `"gen_stamp":0"` 或 `"threat_calls":0"`**；
  - Tracker 状态机断言：`f is None` 时记录 `null_frames += 1`，立即切断冻结时钟，置 `prev_lost = True`，下一恢复帧记为 `resume_after_loss` 且不误报漏沿。
- **判定**：**PASS**。

---

### 2.4 用例 4：S4 命中 ⇒ 立即停手（不得进入采样）
- **依据与代码位置**：`qc151_trip.harness8_v4_ext.py:999-1008`（`s4_scan_names`）、`:1249-1279`（`s4_injection_gate`）与 `:5570-5595`（`_measure_run` 硬阻断）。
- **执行机制**：
  - 纯函数扫描：输入含 `Ra2Render.dll` 或 `RA2LOADER.EXE` 模块表，大小写不敏感精准匹配；
  - 闸门拦截：在 `_W5_STATE["on"] = True` 下触发 `s4_injection_gate`；
  - 采样入口拦截：设置 spy 探针监控 `_measure_poll_span` 调用，触发 `_measure_run`；
- **机械断言与实测值**：
  - `s4_injection_gate` 返回 `False`；
  - `S4_VERDICT["gate"] == "w5_hit_rejected"`，`S4_VERDICT["exit_code"] == 62` (`EXIT_INJECTION_SUSPECTED`)；
  - 审计流登记：`W5EXT` 组登记 `s4_hard_assertion: FAILED_INJECTION_SUSPECTED`；
  - `_measure_run` 硬阻断拦截：`sampling_invoked` 为 **False**（`_measure_poll_span` 零调用）；
  - 运行留痕：登记 `measure_gate_aborted`（`S4 非干净状态，立即停手，禁止进入采样`）。
- **判定**：**PASS**。

---

### 2.5 用例 5：--allow-loader + 扩项 ⇒ 拒绝启动
- **依据与代码位置**：`qc151_trip.harness8_v4_ext.py:7715-7718`（`main` 入口硬冲突拦截）与 `:1257-1266`（`s4_injection_gate` 旁路拒绝）。
- **执行机制**：
  - 模拟命令行参数冲突组合：`--allow-loader` + `--w5-ext 1`，以及 `--allow-loader` + `--measure-ext 1`；
  - 模拟即使外部授信绕过（`authorized=True`），`s4_injection_gate` 的二次防护；
  - 模拟运行期 `A8_ALLOW_LOADER=True` 时 `_measure_run` 的三次防护；
- **机械断言与实测值**：
  - `main([--allow-loader, --w5-ext 1])` 返回退出码 **62** (`EXIT_INJECTION_SUSPECTED`)；
  - `main([--allow-loader, --measure-ext 1])` 返回退出码 **62**；
  - `s4_injection_gate(authorized=True, w5_on=True)` 返回 **False**，设置 `gate="w5_refused_allow_loader"`，`exit_code=62`，记录 `FAILED_ALLOW_LOADER`；
  - `_measure_run(A8_ALLOW_LOADER=True)` 阻断，`sampling_invoked` 为 **False**；
  - 对照组：`--w5-ext 1`（无 `--allow-loader`）正常放行；`--allow-loader`（无 `--w5-ext`）走母本既有授权放行。
- **判定**：**PASS**。

---

### 2.6 用例 6：帧冻结窗 ⇒ 零样本，且不宣称该窗零成本
- **依据与代码位置**：`A1_SAMPLER_CANDIDATE/frame_edge_sampler.py:267-274`（`FrameEdgeTracker` 冻结累计）、`:342-346`（自解释 note）、`TASK.md:69` 与 A2 报告 §2.4。
- **执行机制**：
  - 设置 `_W5_STATE["on"] = True`，注入恒定帧号（`f = 3668`，对应 A2 冻结窗实测）；
  - 执行 `_w5_measure_poll_span` 模拟 125 拍；
  - 检查落盘 JSON 与统计声明；
- **机械断言与实测值**：
  - 追加事件数 `len(events)`：**严格为 0**；
  - 四 VA 业务读取次数：**严格为 0**；
  - `stats["counts"]["edge"]`：**严格为 0**；
  - `stats["frame_clock_freeze_max_s"]`：正确累计持续时长（`0.496 s`）；
  - 统计字典声明声明检查：`"不得据此宣称业务字段冻结"` in `stats["note"]` 为 True；
  - payload 检查：`w5_ext["events_count"] == 0`，且 payload 绝无 `"zero_cost": true` 或 `"zero_burden": true`；
  - 结构性确认：如实披露冻结盲区，坚决不把「零样本」等同于「该窗业务零成本」。
- **判定**：**PASS**。

---

## 3. 自认未验项（Unverified）

依据诚信原则，对本测试的边界与未验项明示如下：

1. **未验真实游戏进程内存读取**：  
   本报告严格遵从「零真机、不发任何进程」纪律，所有测试均使用注入的假 reader 进行。四 VA 在真实 `gamemd.exe` 进程空间中的物理内存布局（如指针悬空、换页保护导致 RPM 失败）属于真机通道任务，离线单测无法也不应验证。
2. **未验极端长时间（>10,000 拍）的虚拟时钟浮点累计精度**：  
   单测使用微秒级虚拟时钟步进，测试了数百拍内的读序全序与时间差，未进行 25 秒完整 12,500 拍的端到端单调性实跑（但底层 `FrameEdgeTracker` 逻辑与拍数无关）。
3. **未验真机 Loader 启动时的进程树拦截**：  
   `--allow-loader` 拒绝启动测试是在 Python 进程内截断 `main()` 入口与参数判定，未测试由 Windows 启动 `ra2loader.exe` 后的外部信号拦截。

---

## 4. 结论与交付物归档

- 离线单测代码：`lead/re_line_20261105/W5_HARNESS_EXT/_w5_test.py`
- 离线单测输出：`lead/re_line_20261105/W5_HARNESS_EXT/_w5_test_out.txt`
- 判定状态：**全部 6 项用例严格通过，EXIT=0，无阻断性问题（`blocking=False`）**。
