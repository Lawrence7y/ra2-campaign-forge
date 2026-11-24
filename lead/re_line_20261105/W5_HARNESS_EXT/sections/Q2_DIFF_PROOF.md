# Q2 改动面证明审计报告

> **执行角色**：改动面审计员·字节级  
> **任务来源**：`lead/re_line_20261105/W5_HARNESS_EXT/TASK.md` §2 Q2  
> **状态**：**阻断 (BLOCKING)** —— 前置 Q1 副本件尚未生成，工具链已就绪并实跑登记

---

## 1. 核心结论与阻断声明

- **一句话结论**：机械验证脚本 `_w5_diff_proof.py` 已就绪并完成母本基线建档与逻辑自测，但经 3 次轮询（间隔 15 秒）前置 Q1 产物 `qc151_trip.harness8_v4_ext.py` 尚未就位；依审计铁律严禁代写副本，本项如实标定 `blocking=true` 阻断等待前置产出。
- **阻断原因**：`lead/re_line_20261105/W5_HARNESS_EXT/qc151_trip.harness8_v4_ext.py` 文件不存在。
- **前置轮询实录**：
  - 第 1 次轮询：`exists=False`
  - 第 2 次轮询（+15s）：`exists=False`
  - 第 3 次轮询（+15s）：`exists=False`
  - 最终状态：`False`

---

## 2. 母本基线核验档案

母本文件路径：`lead/goal1_harness8_20261031/qc151_trip.harness8_v4.py`

| 指标 | 测量值 | 任务书要求 / 判定 |
|---|---|---|
| **文件大小** | 489,502 字节 | 对齐 TASK.md line 20 (489,502 B) |
| **行数统计** | 8,857 行 (换行符 LF 计 8,856 处，零 CRLF) | 格式严谨 |
| **SHA256 哈希** | `38244d2907e7f7fa3cdd28f2603de432585f7ddd9027e0e0ae6348a0892752a8` | 完全对齐 TASK.md line 20 |

### 母本高危/禁止面 API 出现基线扫描

按 Q2 判据，对 6 项关键 Windows API 在母本中的出现次数完成穷举基线建档：

| API 名称 | 母本出现次数 | 审计规则（副本要求） |
|---|---|---|
| `WriteProcessMemory` | 3 | 次数不得变多 (<= 3) |
| `CreateRemoteThread` | 1 | 次数不得变多 (<= 1) |
| `SuspendThread` | 0 | 次数不得变多 (<= 0) |
| `MiniDumpWriteDump` | 11 | 次数不得变多 (<= 11) |
| `StackWalk` | 0 | 次数不得变多 (<= 0) |
| `SetWindowsHookEx` | 1 | 次数不得变多 (<= 1) |

---

## 3. 机械化改动面证明工具设计 (`_w5_diff_proof.py`)

审计工具落地于 `lead/re_line_20261105/W5_HARNESS_EXT/_w5_diff_proof.py`，实现全自动无人工干预的三重断言：

1. **删块即还原 (Byte-level Identity)**：
   - 算法：逐行扫描并剥离所有位于 `# >>> W5EXT-BEGIN` 至 `# <<< W5EXT-END`（或含 `W5EXT-BEGIN` / `W5EXT-END` 标记行）之间的内容。
   - 判定标准：剥离后文本重新按原始换行符拼接为 `restored_bytes`，直接与母本 `mother_bytes` 进行 `restored_bytes == mother_bytes` 逐字节比对，并断言 `SHA256(restored_bytes) == mother_sha`。
2. **改动面清单 (Zero-Modification / Zero-Deletion)**：
   - 算法：使用 `difflib.SequenceMatcher` 对母本与副本进行逐行比对。
   - 判定标准：断言 `deleted_lines == 0`，`modified_lines == 0`，且全部 `added_lines` 严格限定于被识别的 `W5EXT` 块内。
3. **禁止面扫描 (Zero-Increase on Prohibited Surface)**：
   - 算法：精确统计 `WriteProcessMemory`, `CreateRemoteThread`, `SuspendThread`, `MiniDumpWriteDump`, `StackWalk`, `SetWindowsHookEx` 在副本中的出现频次。
   - 判定标准：`count_ext <= count_mother`，差值必须 `<= 0`。

---

## 4. 实跑记录与输出证据

### 执行命令
```bash
python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/re_line_20261105/W5_HARNESS_EXT/_w5_diff_proof.py"
```

### 产出文件
`lead/re_line_20261105/W5_HARNESS_EXT/_w5_diff_proof_out.txt`

### 关键输出片段
```text
================================================================================
W5 改动面证明 (Q2) 机械验证
================================================================================
母本路径: D:\Project\ra2-campaign-forge\lead\goal1_harness8_20261031\qc151_trip.harness8_v4.py
副本路径: D:\Project\ra2-campaign-forge\lead\re_line_20261105\W5_HARNESS_EXT\qc151_trip.harness8_v4_ext.py
--------------------------------------------------------------------------------
母本字节数: 489502
母本行数:   8857
母本 SHA256: 38244d2907e7f7fa3cdd28f2603de432585f7ddd9027e0e0ae6348a0892752a8
母本禁止面 API 出现基线:
  - WriteProcessMemory: 3
  - CreateRemoteThread: 1
  - SuspendThread: 0
  - MiniDumpWriteDump: 11
  - StackWalk: 0
  - SetWindowsHookEx: 1
--------------------------------------------------------------------------------
[BLOCKING] Q1 副本文件尚未生成: qc151_trip.harness8_v4_ext.py 不存在！
根据任务书规定，不可代写副本，阻断等待 Q1 交付件。
================================================================================
结论: 阻断 (BLOCKING - PREREQUISITE MISSING)
================================================================================
```

---

## 5. 自认未验项 (Unverified)

1. **未验副本逐字节还原**：因 `qc151_trip.harness8_v4_ext.py` 尚未由 Q1 交付，实际副本删块后的 SHA256 与字节一致性尚未运行通过。
2. **未验副本差异清单统计**：实际新增行数 N 尚未测定（待副本就位后机械统计）。
3. **未验副本禁止面 API 计数**：实际副本代码中高危 API 频次尚未在真实副本上完成比对。

---

## 6. 后续解阻方案

当 Q1 角色交付 `lead/re_line_20261105/W5_HARNESS_EXT/qc151_trip.harness8_v4_ext.py` 后，仅需重新运行：
```bash
python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/re_line_20261105/W5_HARNESS_EXT/_w5_diff_proof.py"
```
即可直接生成合规证明并解除阻断。
