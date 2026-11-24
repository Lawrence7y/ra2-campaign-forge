# R4 · 改动面与禁止面独立复核审查报告（V3 状态）

```
被核回件路径 = D:/Project/ra2-campaign-forge/lead/re_line_20261105/V6_V3_REVIEW/parts/R4.md
被核对象路径 = D:/Project/ra2-campaign-forge/lead/re_line_20261105/W5_HARNESS_EXT/qc151_trip.harness8_v4_ext.py
被核对象实测 SHA256 = 5081780c5a2e3da5c934efff4665ed248ad01b1c4c883887eb1a66cc7d83f161，字节数 = 499047
基准母本路径 = D:/Project/ra2-campaign-forge/lead/goal1_harness8_20261031/qc151_trip.harness8_v4.py
基准母本实测 SHA256 = 38244d2907e7f7fa3cdd28f2603de432585f7ddd9027e0e0ae6348a0892752a8，字节数 = 489502
复核时刻 = 2026-11-05T21:12:00
```

> **复核员**：独立复核员·R4  
> **复核立场**：默认怀疑，零真机，不修改既有文件，唯一写域 `lead/re_line_20261105/V6_V3_REVIEW/reviews/`。  
> **复核标的**：R4 回件 `parts/R4.md` 及其探针 `_v6_r4.py`、`_v6_r4_out.txt`、`_w5_diff_proof.py`。  
> **复核焦点**：
> 1. 该回件是否**真的**独立计算了被核对象 SHA256（还是照抄了任务书的参照值）；  
> 2. 该回件的结论是否有实跑输出支撑（不是只看代码文字）。

---

## 0. 独立复核裁决 (Verdict)

| 审核项 | 审评结果 | 证据与判定依据 |
|---|---|---|
| **复核判定 (verdict)** | **`CONFIRMED`** | 机械改动面三大判据全项实跑通过，删 8 块还原母本 SHA256 逐字节闭合，回件结论完全属实 |
| **SHA256 独立测算** | **`true`** | 探针代码与复核脚本真读磁盘并动态哈希，本复核员独立重算亦完全一致 |
| **SHA256 绑定段** | **`true`** | 回件头部第 3~7 行完整包含 SHA256、字节数、绝对路径与复核时刻 |
| **实跑输出支撑** | **`true`** | 既有脚本 `_w5_diff_proof.py` 与探针逻辑均有真实落盘及本复核员独立重跑输出支撑 |
| **实质缺陷 (substantiveDefect)** | **`false`** | 无让读数错/丢/null 变 0 缺陷，母本已有行为逐字节受控保真 |
| **异议清单 (objections)** | **`[]`** | 无任何事实异议或逻辑漏洞 |
| **必改清单 (mustFix)** | **`[]`** | 质量完全达标，无须返工修改 |

---

## 1. 焦点核验一：是否**真的**独立计算 SHA256（非照抄参照值）

### 1.1 探针代码审计（`_v6_r4.py`）
审查 `lead/re_line_20261105/V6_V3_REVIEW/_v6_r4.py:84-109`：
```python
    with open(MOTHER_PATH, "rb") as f:
        mother_b = f.read()
    with open(EXT_PATH, "rb") as f:
        ext_b = f.read()

    m_sha = sha256_b(mother_b)
    m_size = len(mother_b)
    ...
    e_sha = sha256_b(ext_b)
    e_size = len(ext_b)
```
- **真实读取**：代码通过标准文件 I/O 读取磁盘二进制数据流 `ext_b = f.read()`；
- **动态哈希**：通过 `hashlib.sha256(data).hexdigest()` 动态生成 `e_sha`，并非将字符串常量赋给测量结果；
- **任务书参照值作为断言守护**：代码中定义 `EXPECTED_EXT_SHA256` 仅用于与实测 `e_sha` 做相等性断言（`pass_base = ... and e_sha == EXPECTED_EXT_SHA256`），符合测试框架标准规范。
- 相同情况见于 `lead/re_line_20261105/W5_HARNESS_EXT/_w5_diff_proof.py:117-124`，同样从磁盘读入字节并动态计算哈希。

### 1.2 本复核员独立测量比对
本复核员在隔离环境（`python -I -X utf8`）中独立运行哈希计算命令：
```bash
python -I -X utf8 -c "
import hashlib
for p in ['lead/goal1_harness8_20261031/qc151_trip.harness8_v4.py', 'lead/re_line_20261105/W5_HARNESS_EXT/qc151_trip.harness8_v4_ext.py']:
    with open(p, 'rb') as f: b = f.read()
    print(p, hashlib.sha256(b).hexdigest(), len(b), len(b.split(b'\n')))
"
```
**测量结果对照表**：

| 文件 | R4 回件申报值 | 本复核员独立实测值 | 任务书参照值 | 是否闭合 |
|---|---|---|---|---|
| **待验副本** | `5081780c5a2e3da5c934efff4665ed248ad01b1c4c883887eb1a66cc7d83f161` (499,047 字节, 9,090 行) | `5081780c5a2e3da5c934efff4665ed248ad01b1c4c883887eb1a66cc7d83f161` (499,047 字节, 9,090 行) | `5081780c5a2e3da5c934efff4665ed248ad01b1c4c883887eb1a66cc7d83f161` (499,047 字节) | **全同 PASS** |
| **基准母本** | `38244d2907e7f7fa3cdd28f2603de432585f7ddd9027e0e0ae6348a0892752a8` (489,502 字节, 8,857 行) | `38244d2907e7f7fa3cdd28f2603de432585f7ddd9027e0e0ae6348a0892752a8` (489,502 字节, 8,857 行) | `38244d2907e7f7fa3cdd28f2603de432585f7ddd9027e0e0ae6348a0892752a8` (489,502 字节) | **全同 PASS** |

**结论**：R4 确系独立从文件字节流实算 SHA256 与字节数，未照抄参照值伪造测量。

---

## 2. 焦点核验二：回件结论是否有实跑输出支撑

### 2.1 既有证明脚本独立重跑
在 Bash 环境中重跑既有证明脚本：
```bash
python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/re_line_20261105/W5_HARNESS_EXT/_w5_diff_proof.py"
```
**实跑执行状态**：`EXIT=0`  
**输出关键段落比对**：
- 识别到 W5EXT 插入块数量: 8（块 #1~#8 行号与行数精准吻合）；
- 删块后字节数: 489,502（母本 489,502），删块后 SHA256: `38244d2907e7f7fa3cdd28f2603de432585f7ddd9027e0e0ae6348a0892752a8`（`restored == mother`）；
- 改动统计: 新增 233 行, 删除 0 行, 修改 0 行；
- 禁止面扫描: 6 项受限 API 差异全为 `+0`；
- 最终判定: `PASS`。
实跑输出与 R4 回件第 3.1 节引述内容逐字吻合。

### 2.2 独立复核探针实跑（`reviews/_r4_independent_check.py`）
为恪守「不修改任何既有文件」纪律，避免直接执行 `_v6_r4.py` 覆盖更新其既有输出文件 `_v6_r4_out.txt` 的时间戳，本复核员在专属写域编写并运行独立探针：
```bash
python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/re_line_20261105/V6_V3_REVIEW/reviews/_r4_independent_check.py"
```
**实跑输出记录**：
```text
================================================================================
独立复核员·R4: 独立复核探针执行
================================================================================
[1] 独立物理量测量
  母本: SHA256=38244d2907e7f7fa3cdd28f2603de432585f7ddd9027e0e0ae6348a0892752a8, 字节数=489502, 行数=8857
  副本: SHA256=5081780c5a2e3da5c934efff4665ed248ad01b1c4c883887eb1a66cc7d83f161, 字节数=499047, 行数=9090

[2] 删 8 块即还原独立验证
  识别插入块数: 8
    块 #1: L176~L211 (36 行) [# >>> W5EXT-BEGIN imports ... # <<< W5EXT-END imports]
    块 #2: L999~L1009 (11 行) [# >>> W5EXT-BEGIN s4-scan-hook ... # <<< W5EXT-END s4-scan-hook]
    块 #3: L1249~L1283 (35 行) [# >>> W5EXT-BEGIN s4-gate-hook ... # <<< W5EXT-END s4-gate-hook]
    块 #4: L4128~L4200 (73 行) [# >>> W5EXT-BEGIN poll-span-hook ... # <<< W5EXT-END poll-span-hook]
    块 #5: L4981~L5017 (37 行) [# >>> W5EXT-BEGIN json-hook ... # <<< W5EXT-END json-hook]
    块 #6: L5582~L5607 (26 行) [# >>> W5EXT-BEGIN measure-run-hook ... # <<< W5EXT-END measure-run-hook]
    块 #7: L7714~L7719 (6 行) [# >>> W5EXT-BEGIN argparse ... # <<< W5EXT-END argparse]
    块 #8: L7726~L7734 (9 行) [# >>> W5EXT-BEGIN main-gate ... # <<< W5EXT-END main-gate]
  插入块总行数: 233
  删块后尺寸: 489502 (母本=489502)
  删块后 SHA256: 38244d2907e7f7fa3cdd28f2603de432585f7ddd9027e0e0ae6348a0892752a8
  逐字节完全相同: True
  删块还原 PASS: True

[3] 改动面清单 (SequenceMatcher) 独立验证
    [INSERT] 副本 L176~L211 (母本 L175 后插入 36 行)
    [INSERT] 副本 L999~L1009 (母本 L962 后插入 11 行)
    [INSERT] 副本 L1249~L1283 (母本 L1201 后插入 35 行)
    [INSERT] 副本 L4128~L4200 (母本 L4045 后插入 73 行)
    [INSERT] 副本 L4981~L5017 (母本 L4825 后插入 37 行)
    [INSERT] 副本 L5582~L5607 (母本 L5389 后插入 26 行)
    [INSERT] 副本 L7714~L7719 (母本 L7495 后插入 6 行)
    [INSERT] 副本 L7726~L7734 (母本 L7501 后插入 9 行)
  改动面统计: 新增=233, 删除=0, 修改=0
  改动面 PASS: True

[4] 禁止面 API 独立扫描
    - WriteProcessMemory    : 母本= 3, 副本= 3, 差值=+0
    - CreateRemoteThread    : 母本= 1, 副本= 1, 差值=+0
    - SuspendThread         : 母本= 0, 副本= 0, 差值=+0
    - MiniDumpWriteDump     : 母本=11, 副本=11, 差值=+0
    - StackWalk             : 母本= 0, 副本= 0, 差值=+0
    - SetWindowsHookEx      : 母本= 1, 副本= 1, 差值=+0
  禁止面扫描 PASS: True

[5] 反例与篡改敏感性独立验证
    反例 1 (母本区单字节篡改): 拦截成功=True
    反例 2 (块内注入禁止词): 拦截成功=True
    反例 3 (破坏块定界符): 拦截成功=True

[6] R4 探针代码与落盘输出核验
  _v6_r4_out.txt 包含母本 SHA: True
  _v6_r4_out.txt 包含副本 SHA: True
  _v6_r4_out.txt 包含 8 块识别: True
  _v6_r4_out.txt 包含 233 行新增/0删/0改: True
  _v6_r4_out.txt 包含禁止词差值+0: True
  _v6_r4_out.txt 包含 CONFIRMED 判定: True
  R4 探针是否真有从磁盘读取并动态哈希逻辑: True

================================================================================
独立复核总结论: CONFIRMED (PASS)
================================================================================
```

---

## 3. 详细判据逐条对照

### 3.1 删 8 块即还原（逐字节保真）
- 待验副本中存在 8 个严格以 `# >>> W5EXT-BEGIN <tag>` 与 `# <<< W5EXT-END <tag>` 围合的扩项块；
- 剥离此 8 块（总计 233 行）后，所得字节流大小为 489,502 字节，SHA256 为 `38244d2907e7f7fa3cdd28f2603de432585f7ddd9027e0e0ae6348a0892752a8`；
- `restored_bytes == mother_bytes` 评估为 `True`，逐字节完全一致；
- **判定**：**PASS**。

### 3.2 改动面清单（母本行零改动）
- 使用 Python `difflib.SequenceMatcher` 对行序列进行对比，未发现任何 `delete` 或 `replace` 操作；
- 8 处改动均为纯 `insert`，各块行数分别为 36, 11, 35, 73, 37, 26, 6, 9，合计新增 233 行；
- **判定**：**PASS**。

### 3.3 禁止面 API 同数扫描
- 对 6 个高危控制/注入 API 进行精确匹配：
  1. `WriteProcessMemory`: 母本 3, 副本 3 (Δ = +0)
  2. `CreateRemoteThread`: 母本 1, 副本 1 (Δ = +0)
  3. `SuspendThread`: 母本 0, 副本 0 (Δ = +0)
  4. `MiniDumpWriteDump`: 母本 11, 副本 11 (Δ = +0)
  5. `StackWalk`: 母本 0, 副本 0 (Δ = +0)
  6. `SetWindowsHookEx`: 母本 1, 副本 1 (Δ = +0)
- 零新增注入面，调用次数增量全部严格为 0；
- **判定**：**PASS**。

### 3.4 反例与门禁非空跑验证
- 内存篡改母本区 1 字节：SHA256 检验立即失败并拦截；
- 块内注入禁止词：禁止面扫描立即报警；
- 破坏定界符：块识别与还原立即失败；
- 门禁机制高度敏感有效，绝非摆设或空跑。

---

## 4. 结论与裁定

R4 回件 `parts/R4.md` 具有严密的实跑命令和探针输出支撑；独立计算了被核对象 SHA256，绑定段规范完整；核心结论（删 8 块还原母本 SHA256、新增 233 行/删 0/改 0、禁止面 API 零增量）完全属实，无任何虚构造假或实质缺陷。

**终审裁决**：**`CONFIRMED`**（通过）。
