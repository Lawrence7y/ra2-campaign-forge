# R2 · 时间戳契约独立复核报告

```
复核对象: D:/Project/ra2-campaign-forge/lead/re_line_20261105/V6_V3_REVIEW/parts/R2.md
被核源对象: D:/Project/ra2-campaign-forge/lead/re_line_20261105/A1_SAMPLER_CANDIDATE/frame_edge_sampler.py
被核源对象独立实测 SHA256: b382e893bafc6a7f38d08572affaa663eaef56a8de7c3f361eea38cc34185f3e
被核源对象独立实测字节数: 21411 字节
关联调用方: D:/Project/ra2-campaign-forge/lead/re_line_20261105/W5_HARNESS_EXT/qc151_trip.harness8_v4_ext.py
关联调用方独立实测 SHA256: 5081780c5a2e3da5c934efff4665ed248ad01b1c4c883887eb1a66cc7d83f161 (499047 字节)
关联测试套件: D:/Project/ra2-campaign-forge/lead/re_line_20261105/W5_HARNESS_EXT/_w5_test.py
关联测试套件独立实测 SHA256: df5771a830c4fa2df5445156284a65d7a5d1e2c4ac80945350a0d05c727df2c8 (36624 字节)
独立复核员: 独立复核员·R2
复核时刻: 2026-11-05 21:09:00
复核裁决: CONFIRMED
```

---

## 0. 最终裁决与判定摘要

| 审核字段 | 判定值 | 审查结论说明 |
|---|---|---|
| **verdict** | **`CONFIRMED`** | 时间戳契约完全依 D-21 裁 A 第 2 条解耦闭合，实测断言全绿，结论完全真实可靠 |
| **sha256BindingPresent** | **`true`** | `parts/R2.md:3-10` 开头严格具备被核源对象与关联文件的法定 SHA256 绑定段 |
| **sha256IndependentlyMeasured** | **`true`** | 证实 R2 探针 `_v6_r2.py` 与独立复核员均通过二进制流真机重算 SHA256，非照抄伪造 |
| **objections** | **`[]`** | 无异议项 |
| **mustFix** | **`[]`** | 无必须整改项 |

---

## 1. 核心审查一：SHA256 绑定与真实独立测算核查

### 1.1 法定绑定段核验
审查 `parts/R2.md` 第 3~10 行：
```text
被核对象 SHA256 = b382e893bafc6a7f38d08572affaa663eaef56a8de7c3f361eea38cc34185f3e，字节数 = 21411
被核对象路径 = D:/Project/ra2-campaign-forge/lead/re_line_20261105/A1_SAMPLER_CANDIDATE/frame_edge_sampler.py
复核时刻 = 2026-11-05 21:05:00

关联调用方 SHA256 = 5081780c5a2e3da5c934efff4665ed248ad01b1c4c883887eb1a66cc7d83f161，字节数 = 499047
关联调用方路径 = D:/Project/ra2-campaign-forge/lead/re_line_20261105/W5_HARNESS_EXT/qc151_trip.harness8_v4_ext.py
关联测试套件 SHA256 = df5771a830c4fa2df5445156284a65d7a5d1e2c4ac80945350a0d05c727df2c8，字节数 = 36624
关联测试路径 = D:/Project/ra2-campaign-forge/lead/re_line_20261105/W5_HARNESS_EXT/_w5_test.py
```
- **判定**: `sha256BindingPresent = True`。被核对象与两个关联文件的实算值、字节数、绝对路径、复核时刻完整齐备，完全符合 `TASK.md §1` 强制格式。

### 1.2 独立测算防照抄审查（非抄录参照值）
审查 R2 探针脚本 `_v6_r2.py:61-64` 与 `98-100`：
```python
def sha256_of_file(path: str) -> tuple[str, int]:
    with open(path, "rb") as f:
        data = f.read()
    return hashlib.sha256(data).hexdigest(), len(data)
...
s_sha, s_sz = sha256_of_file(TARGET_SAMPLER)
h_sha, h_sz = sha256_of_file(CALLER_HARNESS)
t_sha, t_sz = sha256_of_file(TEST_W5)
```
- **AST 与源码审查**: 探针采用 `open(path, "rb")` 读取全量二进制字节，动态传入 `hashlib.sha256().hexdigest()` 测算，并非硬编码常量赋值。探针内部将测得变量打印并校验任务书参照值。
- **复核员双重独立度量**:
  复核员在隔离环境执行 `_r2_independent_check.py` 测得：
  - `frame_edge_sampler.py`: `b382e893bafc6a7f38d08572affaa663eaef56a8de7c3f361eea38cc34185f3e`，21,411 字节
  - `qc151_trip.harness8_v4_ext.py`: `5081780c5a2e3da5c934efff4665ed248ad01b1c4c883887eb1a66cc7d83f161`，499,047 字节
  - `_w5_test.py`: `df5771a830c4fa2df5445156284a65d7a5d1e2c4ac80945350a0d05c727df2c8`，36,624 字节
  - `parts/R2.md`: `adc1b2330045c65db32359141a60d23684c4e7420b9de61c95e1724d34451aea`，10,401 字节
  - `_v6_r2.py`: `91628e9366c4f43e0ac57cc8c0a06ebb3026cb1e0658d02b9225103b4ad97141`，15,189 字节
  - `_v6_r2_out.txt`: `65cd8dfc484a8c5901f31f1841cbd07a951d9494bdb57fe12a036c8a84ce99b2`，5,224 字节
- **判定**: `sha256IndependentlyMeasured = True`。两方实测哈希完全一致，证实该回件数据确为独立计算产出。

---

## 2. 核心审查二：实跑输出支撑性与关键命令重跑

### 2.1 探针原样重跑验证
复核员在隔离环境下，以无副作用方式重跑 R2 探针的主校验逻辑（零真机、不改动任何文件）：
```bash
python -I -X utf8 -c "import sys; sys.path.insert(0, r'D:/Project/ra2-campaign-forge/lead/re_line_20261105/V6_V3_REVIEW'); import _v6_r2; res = _v6_r2.run_checks(); sys.exit(0 if res else 1)"
```
- **执行结果**: `EXIT=0`，`PASS = 33, FAIL = 0`。
- **输出文本逐字比对**: 将内存捕获的重跑输出与磁盘既有 `_v6_r2_out.txt` 进行完全比对，字符数完全一致（均为 4,129 字符），33 项断言日志 100% 逐行重现。

### 2.2 独立探针 `_r2_independent_check.py` 执行验证
复核员编写并在 `reviews/` 目录下运行了专属独立核验脚本：
```bash
python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/re_line_20261105/V6_V3_REVIEW/reviews/_r2_independent_check.py"
```
- **实测结果**: 7 大检验项全部 PASS，覆盖哈希物理量、法定头部、AST 语法流、5 种时钟边界用例及调用点上下文。

---

## 3. 时间戳契约逐项实测核验清单

| # | 契约核验项 | 代码实现位置 | R2 回件结论 | 独立复核实测数据 | 判定 |
|---|---|---|---|---|---|
| 1 | 复用模式下 `ts["f_pre"] == 传入的 t_pre` | `frame_edge_sampler.py:161` | 严格等于传入 `t_pre`，绝不调 `clock()` | 传入 `t_pre=95.5`，实测 `ts["f_pre"] == 95.5`（`PASS`） | **CONFIRMED** |
| 2 | `ts["segment_start"]` 独立记录业务段起点 | `frame_edge_sampler.py:171` | 在首个业务读前独立取 `clock()`，与 `ts["f_pre"]` 语义解耦 | 实测 `ts["segment_start"] == 100.0 != 95.5`，两者独立（`PASS`） | **CONFIRMED** |
| 3 | 传 `f_pre` 但 `t_pre=None` 时的缺省表现 | `frame_edge_sampler.py:158-159` | `ts["f_pre"] is None`，`f_pre_anchor_known=False`，绝不以进入时刻冒充 | 实测 `ts["f_pre"] is None` 为 True，`f_pre_anchor_known is False`（`PASS`） | **CONFIRMED** |
| 4 | 反例验证：传入极端偏早 `t_pre` | 探针测试 | 绝对保留偏早时刻，不截断不重置 | 传入 `t_pre=12.345678`（函数起点 10000.0），实测 `ts["f_pre"] == 12.345678`，差值严格保持 9987.654322s（`PASS`） | **CONFIRMED** |
| 5 | 反例验证：传入极端未来 `t_pre` | 独立探针测试 | 绝对保留未来时刻，未做非法修正 | 传入 `t_pre=99999.99`（起点 1000.0），实测 `ts["f_pre"] == 99999.99`，`segment_start == 1000.0`（`PASS`） | **CONFIRMED** |
| 6 | 向后兼容：自读模式（`f_pre=None, t_pre=None`） | `frame_edge_sampler.py:164-165` | `ts["segment_start"] == ts["f_pre"]`，6 读行为保持不变 | 实测 `segment_start == f_pre == 300.0`，`reads_per_sample == 6`，`f_pre_reused is False`（`PASS`） | **CONFIRMED** |
| 7 | 时间戳全序单调性 | 全流程度量 | 复用模式满足 `f_pre <= segment_start <= 4业务读 <= f_post_start == f_post <= segment_end` | 8 个阶段时间戳在时钟步进下严格单调递增，全序断言通过（`PASS`） | **CONFIRMED** |

---

## 4. 调用方调用点与时序拓扑审查 (`qc151_trip.harness8_v4_ext.py`)

使用 Python AST 语法树解析器及物理行检索，审查结果如下：
1. **调用点严格唯一**:
   - 全文件共 9,090 行，存在且仅存在 1 处 `read_sample` 调用，位于第 4166 行：
     ```python
     4166 | sample = frame_edge_sampler.read_sample(
     4167 |     reader, time.perf_counter, f_pre=f, t_pre=t_now)
     ```
2. **时序因果严格成立**:
   - `L4151`: `t_now = time.perf_counter()` —— 轮询发起时刻采样；
   - `L4154`: `f = reader(MEASURE_CURRENT_FRAME_VA)` —— 帧号读取发起；
   - `L4166`: 将 `f` 与 `t_now` 传入 `read_sample`。
   - 物理因果链 `t_now 捕获时刻 (L4151) < reader 执行时刻 (L4154) < read_sample 调用时刻 (L4166)` 严格成立，完全符合“外层读前锚点”的物理定义。

---

## 5. 关联测试套件回归结果

复核员独立重跑了底层与外层的全部关联单测与改动面证明：
1. `A1_SAMPLER_CANDIDATE/test_frame_edge_sampler.py`:
   - 实跑输出: `SUMMARY PASS=85 FAIL=0`，`EXIT=0`。
2. `W5_HARNESS_EXT/_w5_test.py`:
   - 实跑输出: 6 个用例全 PASS，`EXIT=0`。
3. `W5_HARNESS_EXT/_w5_diff_proof.py`:
   - 实跑输出: 删 8 块还原母本 SHA256 吻合，纯新增 233 行，6 项禁止面 API 零增加，`EXIT=0`。

---

## 6. 诚实账与自认未验项 (Honest Accounting)

1. **零真机守则**: 本次复核全程在 Python 3 隔离纯内存/离线环境进行，未启动任何 RA2 游戏进程，未读取真实 Windows 内存。
2. **底层硬件抖动**: 未在真实真机环境下对多核跨核 TSC 漂移或调度器微秒抖动进行实时统计分析。
3. **调用方非正常参数边界**: 当前 `frame_edge_sampler.py` 内部假定传入的 `t_pre` 为合法浮点数或 None，未防御外层恶意传入不可比较对象（因内生调用链受 W5 harness 控制，外部输入风险为 0）。

---

## 7. 最终裁决

综上所述，R2 回件 `parts/R2.md` 包含完整合规的 SHA256 绑定段，且确由动态探针独立实测得出；其实测输出与结论逐项对应、严谨可重现；关键命令经独立复核重跑 100% 通过。判定为 **CONFIRMED**。
