# 独立复核员·R5 复核审查报告

```
被核回件路径 = D:/Project/ra2-campaign-forge/lead/re_line_20261105/V6_V3_REVIEW/parts/R5.md
被核回件 SHA256 = a339163ddab3667d024ea7078dbee86af74ce528740cd4a70123e8207596fcbc (15,270 字节)
被测目标对象 = D:/Project/ra2-campaign-forge/lead/re_line_20261105/W5_HARNESS_EXT/_w5_test.py
被测目标 SHA256 = df5771a830c4fa2df5445156284a65d7a5d1e2c4ac80945350a0d05c727df2c8 (36,624 字节)
复核脚本路径 = D:/Project/ra2-campaign-forge/lead/re_line_20261105/V6_V3_REVIEW/reviews/_r5_independent_check.py
复核判定时刻 = 2026-11-05
```

---

## 1. 独立复核裁决与结构化指标汇总

| 复核指标项 | 复核结果 | 判定说明 |
|---|---|---|
| **最终裁决 (verdict)** | **`CONFIRMED`** | 认可 R5 报告结论，6 条用例真实实跑全 PASS (EXIT=0)，断言强度极高且死锁 5 读等式 |
| **独立重算 SHA256 (sha256IndependentlyMeasured)** | **`True`** | 独立复核员通过独立 Python 脚本对所有相关文件进行了二进制读取并重算哈希 |
| **明确哈希绑定行 (sha256BindingPresent)** | **`True`** | R5.md 头部 L4~L5 明确声明了被核对象路径、字节数与 SHA256 哈希值 |
| **异议列表 (objections)** | **`[]`（无异议）** | 报告事实清晰，实验严谨，无夸大或弄虚作假 |
| **必改项列表 (mustFix)** | **`[]`（无必改）** | 代码断言严格，符合 D-21 裁 A 契约，无质量或逻辑缺陷 |
| **实质缺陷 (substantiveDefect)** | **`False`** | 未发现任何逻辑漏洞、放宽断言、未捕获异常或时序倒流缺陷 |

---

## 2. 两项重点核查事项专项专项审查

### 2.1 重点核查 1：回件是否真的独立实算了被核对象 SHA256（非抄录）

**核查结论**：**`CONFIRMED（真实独立测算）`**

1. **探针实现证据**：
   - 审查 R5 的探针脚本 `lead/re_line_20261105/V6_V3_REVIEW/_v6_r5.py:54-56`：
     ```python
     def sha256_file(p: Path) -> tuple[str, int]:
         data = p.read_bytes()
         return hashlib.sha256(data).hexdigest(), len(data)
     ```
   - 探针在执行初始（L72）与执行末尾（L266）两次读取硬盘上的二进制原始字节，分别对 `TARGET_TEST`、`TARGET_EXT`、`TARGET_SAMPLER` 进行实算并断言，并在输出中同时展示了“实算 SHA256”与“参照 SHA256”。
2. **复核员独立独立重算比对**：
   - 独立复核员执行 `reviews/_r5_independent_check.py` 测得以下物理量：
     - `lead/re_line_20261105/W5_HARNESS_EXT/_w5_test.py`:
       - SHA256: `df5771a830c4fa2df5445156284a65d7a5d1e2c4ac80945350a0d05c727df2c8`
       - 字节数: `36624` 字节
     - `lead/re_line_20261105/W5_HARNESS_EXT/qc151_trip.harness8_v4_ext.py`:
       - SHA256: `5081780c5a2e3da5c934efff4665ed248ad01b1c4c883887eb1a66cc7d83f161`
       - 字节数: `499047` 字节
     - `lead/re_line_20261105/A1_SAMPLER_CANDIDATE/frame_edge_sampler.py`:
       - SHA256: `b382e893bafc6a7f38d08572affaa663eaef56a8de7c3f361eea38cc34185f3e`
       - 字节数: `21411` 字节
   - 实测结果与 R5 回件中的表格 L42~L44 严格一致（逐位全同）。
3. **绑定行存在性**：
   - R5.md 头部第 4~5 行含明确绑定：
     ```text
     被核对象 SHA256 = df5771a830c4fa2df5445156284a65d7a5d1e2c4ac80945350a0d05c727df2c8，字节数 = 36624
     被核对象路径 = D:/Project/ra2-campaign-forge/lead/re_line_20261105/W5_HARNESS_EXT/_w5_test.py
     ```

### 2.2 重点核查 2：回件结论是否有实跑输出支撑（非仅看代码文字）

**核查结论**：**`CONFIRMED（具备充分的实跑支撑，包含三组反例攻击）`**

1. **原版单测独立重跑支撑**：
   - 复核员独立调用 `python -I -X utf8 D:/Project/ra2-campaign-forge/lead/re_line_20261105/W5_HARNESS_EXT/_w5_test.py` 实跑：
     ```text
     ================================================================================
     测试结果汇总
     ================================================================================
       [PASS] Case 1: 开关为 0 ⇒ 不产生任何新采样行（零行为差结构证明）
       [PASS] Case 2: 开关为 1 ⇒ 每沿恰好追加 5 读（四 VA + f_post，D-21 裁 A）
       [PASS] Case 3: 读失败 ⇒ 字段为 null，不是 0
       [PASS] Case 4: S4 命中 ⇒ 立即停手（不得进入采样）
       [PASS] Case 5: --allow-loader + 扩项 ⇒ 拒绝启动
       [PASS] Case 6: 帧冻结窗 ⇒ 零样本，且不宣称该窗零成本
     --------------------------------------------------------------------------------
     总计: 6 用例, 通过: 6, 失败: 0
     总耗时: 0.026 秒 (全部纯离线模拟，零真机系统调用)
     最终判定: PASS (EXIT=0)
     ================================================================================
     ```
   - 证明 6 条用例全部离线真实通过，进程退出码严格为 0。
2. **反例攻击与断言灵敏度实跑检验**：
   - 复核员在 `reviews/_sandbox_r5/` 隔离环境实施了三组反例注入攻击并实际执行：
     - **反例 A（复用退化为 6 读）**：复用分支强行自读 `FRAME_VA`。实跑退出码 `1`，精准抛出 `AssertionError: 复用模式读序必须为四VA+f_post`。
     - **反例 B（进入时刻冒充读前锚）**：篡改 `ts["f_pre"] = clock()`。实跑退出码 `1`，精准抛出 `AssertionError: f_pre 时刻必须等于外层读前锚，不得用进入时刻冒充`。
     - **反例 C（业务段起点时间倒流）**：篡改 `ts["segment_start"] = (t_pre - 1.0)`。实跑退出码 `1`，精准抛出 `AssertionError`（用例 2.3 全序断言行阻断）。
   - 实跑现象与 R5.md 第 5 节描述完全吻合，证明断言是具有阻断力的活断言，绝非摆设。

---

## 3. 核心断言代码深度审查与 AST 分析

### 3.1 用例 2 断言强度审查（死锁 5 读等式）

在 `_w5_test.py:326-337` 与 AST 遍历中：
- 审查 `total_extra_reads` 断言：
  - AST 断言节点明确为：`total_extra_reads == expected_edges * 5`；
  - 源码与 AST 中**完全不存在** `total_extra_reads <=` 等放宽的不等式断言；
- 审查追加帧号读断言：
  - `assert extra_frame_reads == expected_edges * 1`（每沿仅后读 1 次 `f_post`）；
- 审查四 VA 独立等式断言：
  - `assert call_counts[VA_GEN_STAMP] == expected_edges`
  - `assert call_counts[VA_THREAT_CALLS] == expected_edges`
  - `assert call_counts[VA_DIRTY_RECT] == expected_edges`
  - `assert call_counts[VA_BULLET] == expected_edges`
- 审查纯函数级 5 读断言（`_w5_test.py:227-230`）：
  - `assert len(order_log2) == 5`
  - `assert sample_reuse["reads_per_sample"] == 5`
  - `assert order_log2 == [VA_GEN_STAMP, VA_THREAT_CALLS, VA_DIRTY_RECT, VA_BULLET, FRAME_VA]`

**结论**：用例 2 在纯函数与轮询循环两层上，均采用了最严格的数学恒等式校验，多一读或少一读均直接阻断。

### 3.2 用例 2.3 时间戳全序审查（适配复用模式）

在 `_w5_test.py:348-350` 中：
```python
ts = ev["ts"]
assert ts["f_pre"] <= ts["segment_start"] <= ts["gen_stamp"] <= ts["threat_calls"] \
       <= ts["dirty_rect_count"] <= ts["bullet_count"] <= ts["f_post_start"] <= ts["segment_end"]
```
- AST 解析出的表达式：
  `ts['f_pre'] <= ts['segment_start'] <= ts['gen_stamp'] <= ts['threat_calls'] <= ts['dirty_rect_count'] <= ts['bullet_count'] <= ts['f_post_start'] <= ts['segment_end']`
- **契约适配性**：在 D-21 裁 A 模式下，`f_pre` 是复用外层轮询主循环的读前锚时刻 `t_pre`。外层读前锚时刻自然早于或等于进入本次采样段记录的 `segment_start`（`ts["f_pre"] <= ts["segment_start"]`）。
- 断言既保留了全序单调性的物理约束，又真实反映了外层锚复用的时序拓扑。

---

## 4. 零真机与既有文件保真度审计

1. **零真机审计**：全套单测与复核探针均为离线注入 `fake_reader` 与 `VirtualClock`，无任何 `OpenProcess`、`ReadProcessMemory` 或实际游戏进程调用。
2. **零文件改动审计**：
   - 独立复核脚本 `reviews/_r5_independent_check.py` 运行前后，对 `_w5_test.py`、`qc151_trip.harness8_v4_ext.py`、`frame_edge_sampler.py` 进行了前后哈希严格校验，哈希值前后完全一致；
   - 对 `_w5_test_out.txt` 采取了预读并在跑后恢复原始字节的防护措施，确保工作区既有文件字节零变化；
   - 唯一写入行为严格限制在 `lead/re_line_20261105/V6_V3_REVIEW/reviews/` 目录内。

---

## 5. 结论

被复核件 `parts/R5.md` 报告内容客观真实，数据严谨，SHA256 经独立物理量测定无误，断言强度充沛且有全量实跑输出支撑。裁决为：**`CONFIRMED`**。
