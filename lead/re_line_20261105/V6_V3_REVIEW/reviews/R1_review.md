# R1 · 复用前读模式读次独立复核意见书

```
复核对象: D:/Project/ra2-campaign-forge/lead/re_line_20261105/V6_V3_REVIEW/parts/R1.md
被核源文件: D:/Project/ra2-campaign-forge/lead/re_line_20261105/A1_SAMPLER_CANDIDATE/frame_edge_sampler.py
被核源文件独立实测 SHA256: b382e893bafc6a7f38d08572affaa663eaef56a8de7c3f361eea38cc34185f3e
被核源文件独立实测字节数: 21411 字节
独立复核员: 独立复核员·R1
复核时刻: 2026-11-05 21:05:17
复核裁决: CONFIRMED (全部要求项实测通过，无实质缺陷)
```

---

## 1. 复核裁决与核心结论

- **总评判定**: **CONFIRMED**
- **SHA256 绑定段存在性 (`sha256BindingPresent`)**: **True**（`parts/R1.md:3-7` 包含明确、完整的对象路径、实算 SHA256 与字节数、复核时刻三要素）。
- **SHA256 独立重算核验 (`sha256IndependentlyMeasured`)**: **True**（复核员独立使用 `hashlib.sha256` 二进制读流重算，结果 `b382e893bafc6a7f38d08572affaa663eaef56a8de7c3f361eea38cc34185f3e`、大小 21,411 字节，与回件声明及探针输出逐 bit 吻合）。
- **实跑输出支撑性**: **True**（探针脚本 `_v6_r1.py` 经独立复核重跑，退出码 0，原始计数与时序记录逐行重现，非单纯文本走读推断）。
- **异议事项 (`objections`)**: 无。
- **必须整改项 (`mustFix`)**: 无。

---

## 2. 核心核查点独立审计

### 2.1 该回件是否真的独立实算了 SHA256（非抄录参照值）

审查依据：`lead/re_line_20261105/V6_V3_REVIEW/_v6_r1.py:66-90`
```python
def verify_target_object():
    assert os.path.isfile(TARGET_PATH), f"Target file not found: {TARGET_PATH}"
    with open(TARGET_PATH, "rb") as f:
        data = f.read()
    sha256_val = hashlib.sha256(data).hexdigest()
    size_val = os.path.getsize(TARGET_PATH)
```
- **代码审查**: 探针脚本动态打开目标文件，以二进制流读取全量字节并计算 SHA256 与 `os.path.getsize`，将动态变量写入 logger，仅随后与参照值比对以触发 `OBJECT_CHANGED` 告警，非硬编码静态字符串。
- **独立测量**: 复核员在沙箱中独立执行 Python 二进制哈希运算：
  - 路径: `D:/Project/ra2-campaign-forge/lead/re_line_20261105/A1_SAMPLER_CANDIDATE/frame_edge_sampler.py`
  - 测得 SHA256: `b382e893bafc6a7f38d08572affaa663eaef56a8de7c3f361eea38cc34185f3e`
  - 测得大小: `21411` 字节
- **审计结论**: 回件数据确由探针动态独立测得，不存在未核硬抄或伪造哈希的行为。

---

### 2.2 关键命令独立重跑与实跑输出支撑

复核员在隔离环境执行探针重跑：
```bash
python -I -X utf8 -c "import sys; sys.path.insert(0, 'lead/re_line_20261105/V6_V3_REVIEW'); import _v6_r1; _v6_r1.OUT_TXT_PATH='lead/re_line_20261105/V6_V3_REVIEW/reviews/_v6_r1_rerun_out.txt'; _v6_r1.logger.out_file='lead/re_line_20261105/V6_V3_REVIEW/reviews/_v6_r1_rerun_out.txt'; _v6_r1.main()"
```
- **命令退出码**: `0`
- **输出比对**: 重跑输出文件 `reviews/_v6_r1_rerun_out.txt` 与被复核输出 `_v6_r1_out.txt` 进行 `diff -u` 比对，除执行时间戳由 `20:55:51` 变为 `21:05:17` 外，所有原始计数、VA 地址序列、断言日志 **100% 逐行完全一致**。

---

### 2.3 任务要求项逐项核验结果

| # | 任务要求项 | R1 回件声明 | 独立重跑实测数据 | 判定 |
|---|---|---|---|---|
| 1 | 传 `f_pre` 时不调 `reader(FRAME_VA)` 读前帧号 | 业务读前读次为 0；整样本对 FRAME_VA 仅读 1 次 (`f_post`) | `pre_frame_reads = 0`, `post_frame_reads = 1`, `total_frame_reads = 1` | **CONFIRMED** |
| 2 | 缺省 `f_pre=None` 保持原 6 读向后兼容 | 总读次 6，FRAME_VA 读次 2 | `total_reads = 6`, `FRAME_VA 读次 = 2`, `reads_per_sample = 6` | **CONFIRMED** |
| 3 | 可计数 reader 实测两种模式读次与原始读序 | 默认 6 读，复用 5 读，给出 6 步与 5 步完整轨迹 | 默认模式轨迹: 1(前帧号) + 4(业务) + 1(后帧号) = 6;<br>复用模式轨迹: 4(业务) + 1(后帧号) = 5 | **CONFIRMED** |
| 4 | 反例要求：只在 FRAME_VA 计数探针验证 0 次前读 | `FrameVaOnlyCountingProbe` 实测 0 次前读；`PreReadForbiddenProbe` 复用不抛错、默认抛错 | `probe_reuse.pre_frame_reads == 0`;<br>`PreReadForbiddenProbe` 拦截到默认模式违规抛错，复用模式 0 违规平稳执行 | **CONFIRMED** |
| 5 | 边沿测试：`f_pre=0` 假值陷阱 | `reuse = f_pre is not None`，0 不退化为 None | `f_pre_reused = True`, `reads_per_sample = 5`, `pre_frame_reads = 0`, `f_pre = 0` | **CONFIRMED** |
| 6 | 契约测试：`t_pre=None` | `f_pre_reused = True`, `ts.f_pre = None`, `f_pre_anchor_known = False` | 字段值准确，读次依然严格为 5 读且 0 次前读 | **CONFIRMED** |
| 7 | 流式模拟：10 沿实测累计读次 | 累计 `pre_frame_reads = 0`, 累计总追加读 = 50 (节省 10 读) | 实测累计追加读数精确为 50，帧号前读精确为 0 | **CONFIRMED** |

---

### 2.4 代码实现健壮性与架构合规性核查

对 `A1_SAMPLER_CANDIDATE/frame_edge_sampler.py:138-185` 源码进行针对性走读核验：
1. **类型判断严谨性**:
   - `reuse = f_pre is not None`：显式使用 `is not None` 单例比对，彻底规避了 `0` 或空对象在布尔上下文中的隐式类型转换缺陷。
2. **读序保真度**:
   - 复用分支完全短路跳过 `read_one(reader, FRAME_VA)` 与单调时钟取样，首个业务 VA 读取发起前无任何内存或系统调用开销。
   - 业务循环 `FIELDS`（4 个固定字段）保持原子顺序遍历。
   - 闭合后读保留在业务循环之后，精准闭合观测段。
3. **元数据自解释性**:
   - 样本中严格包含 `f_pre_reused`（布尔）与 `reads_per_sample`（5 或 6），使得下游日志消费方与质检门禁可无歧义机械验证读次。

---

## 3. 异议与整改清单

- **异议 (objections)**: 无。
- **必须整改 (mustFix)**: 无。
- **附带建议 (non-blocking)**: 
  当前 `frame_edge_sampler.py` 内部未对 `f_pre` 进行 `isinstance(f_pre, bool)` 防御。由于 Python 中 `bool` 是 `int` 子类，若外层误传 `True`，`f_pre is not None` 为真。但在当前调用拓扑中，W5 harness 传入的 `f` 均源自上一拍轮询的整数读数或 None，无注入风险。当前实现无实质缺陷。

---

## 4. 最终裁定

本复核员本着默认怀疑的立场，对 R1 回件、测试探针及被核源对象进行了全面独立验证与命令重跑。各项证据表明，R1 回件结论完全真实可信，论据充分，实测数据与代码实现完全一致，裁决评定为 **CONFIRMED**。
