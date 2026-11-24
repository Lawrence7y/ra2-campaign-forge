# R3 独立复核报告 · W5 副本调用点与参数传递

```
被核对象 SHA256 = 5081780c5a2e3da5c934efff4665ed248ad01b1c4c883887eb1a66cc7d83f161，字节数 = 499047
被核对象路径 = D:/Project/ra2-campaign-forge/lead/re_line_20261105/W5_HARNESS_EXT/qc151_trip.harness8_v4_ext.py
复核时刻 = 2026-11-05T21:05:00
```

> **复核角色**：独立复核员·R3（默认怀疑，严守零真机、不改任何既有文件）  
> **复核目标**：复核员·R3 的回件 `lead/re_line_20261105/V6_V3_REVIEW/parts/R3.md` 及其探针脚本 `_v6_r3.py` 与实跑输出 `_v6_r3_out.txt`  
> **核心任务**：  
> 1) 严审该回件是否**真的**独立计算了被核对象 SHA256（还是照抄任务书参照值）；  
> 2) 严审该回件的结论是否有实跑输出支撑（不是只看代码文字）；  
> 3) 独立亲自重跑关键命令与独立探针，给出终审裁决。

---

## 0. 最终裁决与判定摘要

| 裁决字段 | 裁决值 | 说明 |
|---|---|---|
| **verdict** | **`CONFIRMED`** | 结论完全成立，调用点符合 D-21 裁 A 契约，AST 与 Grep 证明严格唯一 |
| **sha256BindingPresent** | **`true`** | R3 回件头部明确包含标准 SHA256 绑定段（L3~L7） |
| **sha256IndependentlyMeasured** | **`true`** | R3 在 `_v6_r3.py` 中以二进制真实读取并计算 SHA256，且复核员独立重算完全吻合 |
| **objections** | **`[]`** | 无异议项，结论扎实可靠 |
| **mustFix** | **`[]`** | 无必须修改项 |

---

## 1. 物理量独立实测与防照抄审查

### 1.1 复核员独立度量
独立复核员在隔离环境（`python -I`）执行独立实测：
- **实测命令**：
  ```bash
  python -I -c "import hashlib; data = open(r'D:\Project\ra2-campaign-forge\lead\re_line_20261105\W5_HARNESS_EXT\qc151_trip.harness8_v4_ext.py', 'rb').read(); print('SHA256:', hashlib.sha256(data).hexdigest()); print('SIZE:', len(data))"
  ```
- **实测输出**：
  - SHA256: `5081780c5a2e3da5c934efff4665ed248ad01b1c4c883887eb1a66cc7d83f161`
  - SIZE: `499,047` 字节
  - LINES: `9,090` 行

### 1.2 R3 回件防照抄审查
检查 R3 探针脚本 `_v6_r3.py:38-56`：
```python
with open(target_path, "rb") as f:
    raw_bytes = f.read()

size_measured = len(raw_bytes)
sha256_measured = hashlib.sha256(raw_bytes).hexdigest()
```
- **审查结论**：R3 并非直接硬编码任务书的预设值或照抄常量，而是在执行探针时通过 `open(target_path, "rb")` 读取文件字节流并调用 `hashlib.sha256()` 进行动态度量，并带有 `assert check_sha and check_size` 双重防伪断言。
- **绑定段完备性**：`parts/R3.md:3-7` 包含完整的三行声明（SHA256、字节数、被核对象路径、复核时刻），完全符合任务书 §1 铁律。

---

## 2. 结论实跑支撑与命令独立重跑

### 2.1 关键命令重跑
独立复核员在 Bash 环境下亲自重跑 R3 探针：
- **执行命令**：
  ```bash
  python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/re_line_20261105/V6_V3_REVIEW/_v6_r3.py"
  ```
- **执行结果**：退出码 `EXIT_CODE=0`。实际输出与 `_v6_r3_out.txt` 逐字逐行核对完全一致（仅时刻戳随当前执行时间自然更新）。

### 2.2 独立探针交叉核验
独立复核员另编写独立验证脚本 `lead/re_line_20261105/V6_V3_REVIEW/reviews/_r3_independent_check.py`，脱离 R3 脚本结构进行交叉扫描：
- **执行命令**：
  ```bash
  python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/re_line_20261105/V6_V3_REVIEW/reviews/_r3_independent_check.py"
  ```
- **实跑输出核心数据**：
  1. `poll-span-hook` 块范围：`qc151_trip.harness8_v4_ext.py:4128 ~ 4200`（共 73 行）。
  2. AST 递归扫描 `read_sample` 调用节点数恰好为 **1**；Attribute (`read_sample`) 节点数恰好为 **1**。
  3. 唯一调用点定位：`qc151_trip.harness8_v4_ext.py:4166:25`。
  4. AST 解析表达式：`frame_edge_sampler.read_sample(reader, time.perf_counter, f_pre=f, t_pre=t_now)`。
  5. 参数展开核验：
     - 位置参数 0：`reader`
     - 位置参数 1：`time.perf_counter`
     - 关键字参数 `f_pre`：`f`
     - 关键字参数 `t_pre`：`t_now`
  6. 文本 Grep 结果：全文件命中 2 行，L4164 为纯注释行，L4166 为唯一代码行。

---

## 3. 时序链与 D-21 裁 A 契约符合性核验

独立复核员审查 `qc151_trip.harness8_v4_ext.py:4150-4174` 的执行时序流：
```python
4151:        t_now = time.perf_counter()
4152:        if t_now >= t_end:
4153:            break
4154:        f = reader(MEASURE_CURRENT_FRAME_VA)
4155:        if f is None:
...
4161:            samples.append((t_now, f))
4162:            if prev_f is not None and f != prev_f:
4166:                sample = frame_edge_sampler.read_sample(
4167:                    reader, time.perf_counter, f_pre=f, t_pre=t_now)
4168:                ev = tracker.feed(t_now, f, sample=sample)
```

**契约审查结论**：
1. **读前时刻保真**：`t_now` 于 L4151 采集，发生在 L4154 调用 `reader(MEASURE_CURRENT_FRAME_VA)` **之前**。因此，传入 `t_pre=t_now` 严格代表外层读 `f` 之前的真实时刻。
2. **严防时刻冒充**：`read_sample` 接收到 `t_pre` 后，直接将其记入 `ts["f_pre"]`，而业务追加段起点 `ts["segment_start"]` 则另行取 `clock()`。这完全符合 D-21 裁决书 §2 第 2 条「不得把进入 read_sample 的新时刻冒充外层 f 的读前时刻」与 EXECUTION_D21 §1.1 的时间戳分离契约。
3. **时序拓扑严密**：`t_now` (4151) < `f` 读数 (4154) < 跳变判定 (4162) < 5 读追加采样 (4166) < `tracker.feed` (4168)，单调先后全序完全成立。

---

## 4. 目录全貌与关联文件核验

独立复核员对 `lead/re_line_20261105/W5_HARNESS_EXT/` 目录下全部 Python 文件进行了独立 AST 与 Grep 扫描：
- `qc151_trip.harness8_v4_ext.py`（被核副本）：AST 调用数 = 1（L4166 新版调用），Grep 命中 = 2（1 注释 + 1 代码）。
- `_w5_test.py`（单测套件）：AST 调用数 = 4，Grep 命中 = 7。包含用例 2.1（6 读兼容测试）、2.1b（5 读复用专项测试）、2.2（10 拍轮询驱动测试）、3.2（读失败测试）。经独立实跑 `_w5_test.py`，6 个测试用例全部 PASS，退出码为 0。
- `_build_ext.py`（初版一次性组装脚本）：AST 调用数 = 0，Grep 命中 = 1（L147 `block4` 字符串模板）。
- `_leader_reads_and_beat.py`：AST 调用数 = 0，Grep 命中 = 8（均为分析员静态计数与字符串匹配）。
- `_w5_burden.py`：AST 调用数 = 0，Grep 命中 = 2（均为注释）。
- `_w5_diff_proof.py`：AST 调用数 = 0，Grep 命中 = 0。
- `_leader_s4_assert_check.py`：AST 调用数 = 0，Grep 命中 = 0。

**对 `_build_ext.py` 模板遗留项的复核评价**：
- R3 在报告 §5 中指出的「`_build_ext.py:147` 模板字符串保留旧式调用」属实，且 R3 定性准确：该脚本为一次性离线组装工具，不在任何运行期、测试期或单测执行链路中，不属于当前待验副本 `qc151_trip.harness8_v4_ext.py` 本身的实质缺陷。复核员认同 R3 将其定为「运维隐患 / 维护性提示」而非阻塞性缺陷的处理。

---

## 5. 独立复核员诚实账

- **实跑命令与痕迹**：
  1. `python -I -c "import hashlib; ..."` 独立实测 SHA256 与字节数；
  2. `python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/re_line_20261105/V6_V3_REVIEW/_v6_r3.py"` 亲自重跑 R3 探针脚本，核对控制台输出与 `_v6_r3_out.txt`；
  3. `python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/re_line_20261105/V6_V3_REVIEW/reviews/_r3_independent_check.py"` 独立实现并实跑 AST 递归与 Grep 逐行多维度检验；
  4. `python -I -X utf8 "lead/re_line_20261105/W5_HARNESS_EXT/_w5_test.py"` 独立实跑单测套件，确认 6/6 全 PASS，EXIT=0。
- **纪律恪守**：
  - 零真机：未启动任何游戏进程或注入器，未执行任何进程内存读取；
  - 零既有文件改动：未修改任何仓库既有代码或前置报告；
  - 唯一写域：仅在 `lead/re_line_20261105/V6_V3_REVIEW/reviews/` 下创建复核脚本 `_r3_independent_check.py` 与本报告 `R3_review.md`。
- **终审结论**：R3 回件真实可靠、论据充分、实跑支撑完备、SHA256 独立计算无虚假。最终判定：**`CONFIRMED`**。
