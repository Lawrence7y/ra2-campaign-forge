# V6 判定书 · W5 扩项副本 V3 状态复核重跑总判定书（D-21 裁 A 之后）

```
判定书编号: V6-V3-REVIEW-20261105
基准裁决: D-21 裁 A (lead/re_line_20261105/D21_RULING/RULING_D21.md)
汇总角色: V6 汇总员
落盘路径: D:/Project/ra2-campaign-forge/lead/re_line_20261105/V6_V3_REVIEW/V6_V3_REVIEW.md
落盘时刻: 2026-11-05
审查纪律: 零真机系统调用、零注入、既有件零修改、全量哈希独立测算
```

---

## 0 总判

**最终裁决：CONFIRMED**

D-21 裁 A 后每沿新增读为 5 次（四 VA + f_post），f_pre 复用外层读数与读前时刻。

### 裁决规则合规核验
1. **实质缺陷检验**：五项复核与五道独立复核中，`substantiveDefect = true` 项数为 0（全部为 false），无任何会导致读数错误、丢读、null 变 0 或 flag-off 行为不一致的逻辑缺陷；
2. **降级审查检验**：五项复核与五道独立复核中，PARTIAL 项数为 0，REFUTED 项数为 0，无需且未发生任何降级；
3. **SHA256 绑定检验**：全部被核对象及五份回件均具备独立实测的完整 SHA256 绑定段（`sha256BindingPresent = true` 且 `sha256IndependentlyMeasured = true`），无任何缺失；
4. **全项全绿准入**：R1、R2、R3、R4、R5 五大项初审与独立复核均全量达成 **CONFIRMED**，必须改项总数为 0。依据总判规则，判定书最终总判正式签发为 **CONFIRMED**。

### R1~R5 判定总表

| 编号 | 复核项名称 | 初审结论 | 独立复核结论 | 实质缺陷 | 必改项数 | 终审判定 |
|---|---|---|---|---|---|---|
| **R1** | 复用前读模式读次度量 | CONFIRMED | CONFIRMED | 无 (False) | 0 | **CONFIRMED** |
| **R2** | 时间戳契约解耦与拆分 | CONFIRMED | CONFIRMED | 无 (False) | 0 | **CONFIRMED** |
| **R3** | W5 副本调用点参数传递 | CONFIRMED | CONFIRMED | 无 (False) | 0 | **CONFIRMED** |
| **R4** | 改动面证明与禁止面扫描 | CONFIRMED | CONFIRMED | 无 (False) | 0 | **CONFIRMED** |
| **R5** | 单测断言强度与覆盖真实性 | CONFIRMED | CONFIRMED | 无 (False) | 0 | **CONFIRMED** |
| **总计** | **五项综合** | **全项通过** | **全项通过** | **0 项缺陷** | **0 项** | **CONFIRMED** |

---

## 1 SHA256 绑定

所有被核对象与基准参考文件均在 Python 隔离沙盒环境（`python -I -c`）下，由汇总员与各独立复核员通过二进制读流（`open(path, 'rb').read()`）独立实测计算哈希值，坚决杜绝静态抄录任务书数值。

### 法定被核对象物理量清单

| # | 对象角色 | 文件绝对路径 | 独立实测 SHA256 | 字节数 (Bytes) | 代码行数 |
|---|---|---|---|---|---|
| 1 | **核心被核对象**<br>(采样候选件) | `D:/Project/ra2-campaign-forge/lead/re_line_20261105/A1_SAMPLER_CANDIDATE/frame_edge_sampler.py` | `b382e893bafc6a7f38d08572affaa663eaef56a8de7c3f361eea38cc34185f3e` | 21,411 | 486 |
| 2 | **核心被核对象**<br>(W5 扩项副本) | `D:/Project/ra2-campaign-forge/lead/re_line_20261105/W5_HARNESS_EXT/qc151_trip.harness8_v4_ext.py` | `5081780c5a2e3da5c934efff4665ed248ad01b1c4c883887eb1a66cc7d83f161` | 499,047 | 9,090 |
| 3 | **核心被核对象**<br>(离线单测试卷) | `D:/Project/ra2-campaign-forge/lead/re_line_20261105/W5_HARNESS_EXT/_w5_test.py` | `df5771a830c4fa2df5445156284a65d7a5d1e2c4ac80945350a0d05c727df2c8` | 36,624 | 741 |
| 4 | **基准对比母本**<br>(Harness8 V4) | `D:/Project/ra2-campaign-forge/lead/goal1_harness8_20261031/qc151_trip.harness8_v4.py` | `38244d2907e7f7fa3cdd28f2603de432585f7ddd9027e0e0ae6348a0892752a8` | 489,502 | 8,857 |
| 5 | **证明执行脚本**<br>(改动面证明) | `D:/Project/ra2-campaign-forge/lead/re_line_20261105/W5_HARNESS_EXT/_w5_diff_proof.py` | `0575dbcc90d4dff133c57981841aa0ffc13b400c8b885323a6399d86e58fa93d` | 8,609 | 206 |

### 审查回件与独立复核件物理量清单

| 回件 / 复核意见书路径 | 独立实测 SHA256 | 字节数 (Bytes) | 头部绑定段核验 |
|---|---|---|---|
| `lead/re_line_20261105/V6_V3_REVIEW/parts/R1.md` | `ee30f89fa6e5eb9ae8858348981e7d825fbbfa177c413e110ea09848f297dbca` | 8,218 | 通过 (L3~L7) |
| `lead/re_line_20261105/V6_V3_REVIEW/parts/R2.md` | `adc1b2330045c65db32359141a60d23684c4e7420b9de61c95e1724d34451aea` | 10,401 | 通过 (L3~L10) |
| `lead/re_line_20261105/V6_V3_REVIEW/parts/R3.md` | `02293b6e82c81358cfa97607a7e8f54be6058d4a6f95d8525bca9e9fa56ddc5c` | 12,079 | 通过 (L3~L7) |
| `lead/re_line_20261105/V6_V3_REVIEW/parts/R4.md` | `ec86e109df9ca343aa1767ee9d53c7a82ecaa1bba29037803a6b0be649f80a0a` | 10,509 | 通过 (L3~L7) |
| `lead/re_line_20261105/V6_V3_REVIEW/parts/R5.md` | `a339163ddab3667d024ea7078dbee86af74ce528740cd4a70123e8207596fcbc` | 15,270 | 通过 (L3~L7) |
| `lead/re_line_20261105/V6_V3_REVIEW/reviews/R1_review.md` | `b6e15998b67119e8cf196238da29571343b22cf51b476e3d93708579ca26fe41` | 6,637 | 通过 (L3~L10) |
| `lead/re_line_20261105/V6_V3_REVIEW/reviews/R2_review.md` | `7be46ef27a19bb69ea979a4da908bb9c07156f4d548ddf5ea25d7065e100c5bc` | 9,528 | 通过 (L3~L15) |
| `lead/re_line_20261105/V6_V3_REVIEW/reviews/R3_review.md` | `3aa8d3fa7bfbbf53c485fa6d5573e86c078ae978bb1d701e6a987d6056cf999a` | 8,345 | 通过 (L3~L7) |
| `lead/re_line_20261105/V6_V3_REVIEW/reviews/R4_review.md` | `bc22625293297a7a58eec4a29a2444ca134260d5bfa4a39bfe00c8b6715f3333` | 11,096 | 通过 (L3~L9) |
| `lead/re_line_20261105/V6_V3_REVIEW/reviews/R5_review.md` | `3795b6dd3bc4fe52fe9d0dd1320ef22cc37a89e9f648ee20857ba0b85a1a1f9e` | 8,755 | 通过 (L3~L9) |

---

## 2 R1-R5 逐条判定

### R1 · 复用前读路径读次度量
- **初审陈述**: 复用前读模式实测严格执行 5 次读取且 0 次前帧号读，缺省保持 6 读向后兼容，未发现实质缺陷（SHA256: `b382e893...`，大小: 21,411 B，无缺陷）。
- **独立复核意见**: **CONFIRMED**。独立重跑 `_v6_r1.py` 退出码为 0，输出与 `_v6_r1_out.txt` 逐字重现。证实：
  1. 复用模式（`f_pre=100, t_pre=199.5`）下，仅发生 1 次 FRAME_VA 读（即 `f_post`）与 4 次业务 VA 读，前帧号自读严格为 0 次，总读次严格等于 5；
  2. 缺省模式（`f_pre=None`）下，FRAME_VA 读取 2 次（前读+后读），四业务 VA 读取 4 次，总读次严格等于 6，向后兼容原 6 读；
  3. 边界值 `f_pre=0` 时，Python 逻辑通过 `f_pre is not None` 判断，未发生布尔误判，依然严格维持 5 读；
  4. 10 沿流式压测累计仅 5 次 `f_post` 读与 20 次业务读，前帧号读数为 0。
- **终审判定**: **CONFIRMED**。

### R2 · 时间戳契约解耦与拆分
- **初审陈述**: 时间戳契约严格依 D-21 裁 A 第 2 条拆分闭合：复用模式下 `ts['f_pre']` 等于传入的外层读前时刻 `t_pre`（绝非进入时刻），`ts['segment_start']` 独立记录业务段起点，缺省 `t_pre` 记 `None` 且 `f_pre_anchor_known=False`，反例偏早 `t_pre` 获绝对保留，无实质缺陷。
- **独立复核意见**: **CONFIRMED**。独立编写并执行 `reviews/_r2_independent_check.py`，7 项校验全部 PASS。证实：
  1. 解耦充分：`frame_edge_sampler.py:270-279` 严格实现 `ts["f_pre"] = float(t_pre) if t_pre is not None else None`，同时 `ts["segment_start"] = clock()` 独立在业务段开头采样；
  2. 缺省安全：传 `f_pre` 但 `t_pre=None` 时，`ts["f_pre"] is None` 且 `ts["f_pre_anchor_known"] = False`，绝无进入时刻冒充外层锚点；
  3. 反例保真：传入偏早一万秒（`t_pre=100.0`，进入时刻 `10100.0`）或偏晚（`t_pre=99999.0`），`ts["f_pre"]` 均绝对保真，与进入时刻差值严格保留；
  4. 时间戳全序链保序：`ts['f_pre'] <= ts['segment_start'] <= ts['gen_stamp'] <= ts['threat_calls'] <= ts['dirty_rect_count'] <= ts['bullet_count'] <= ts['f_post_start'] <= ts['segment_end']`。
- **终审判定**: **CONFIRMED**。

### R3 · W5 副本调用点参数传递
- **初审陈述**: W5 副本 `poll-span-hook` 块内沿触发调用已严格变更为 5 读传参 `(f_pre=f, t_pre=t_now)`，AST 与 Grep 证明全文件调用点严格唯一，无第二处旧式调用漏改。
- **独立复核意见**: **CONFIRMED**。独立执行 `reviews/_r3_independent_check.py` 证实：
  1. 唯一调用点定位：`qc151_trip.harness8_v4_ext.py:4166`（位于第 4 插入块 `poll-span-hook` L4128~L4200 内），调用表达式确为 `frame_edge_sampler.read_sample(reader, time.perf_counter, f_pre=f, t_pre=t_now)`；
  2. AST 与 Grep 拓扑扫描：遍历全文件 9,090 行，AST 语法树中 `read_sample` 调用节点数严格等于 1，Grep 匹配行仅 L4166（纯代码）与 L4164（说明注释），全文件零第二处调用遗留；
  3. 拓扑因果关系严密：L4151 先采 `t_now = time.perf_counter()`，L4154 执行 `f = reader(MEASURE_CURRENT_FRAME_VA)`，L4166 将其作为外层读前锚传入，完全满足 D-21 裁 A 契约。
- **终审判定**: **CONFIRMED**。

### R4 · 改动面证明与禁止面扫描
- **初审陈述**: 独立重跑 `_w5_diff_proof.py` 与独立探针证实：V3 副本删 8 块后 SHA256 仍等于母本，改动面纯新增 233 行、删除 0、修改 0，六个禁止面 API 零增量逐项相同，判定 CONFIRMED。
- **独立复核意见**: **CONFIRMED**。独立重跑 `_w5_diff_proof.py` 及执行 `reviews/_r4_independent_check.py` 证实：
  1. 删 8 块还原母本：从 `qc151_trip.harness8_v4_ext.py` 剥离 8 个定界扩展块后，字节数完全等于 489,502，SHA256 恢复为 `38244d2907e7f7fa3cdd28f2603de432585f7ddd9027e0e0ae6348a0892752a8`，与母本 `qc151_trip.harness8_v4.py` 逐 bit 一致；
  2. 改动面纯净：新增 233 行，删除 0 行，修改 0 行（母本原有代码零变动）；
  3. 禁止面零增量：`WriteProcessMemory` (母3/副3, +0)、`CreateRemoteThread` (母1/副1, +0)、`SuspendThread` (母0/副0, +0)、`MiniDumpWriteDump` (母11/副11, +0)、`StackWalk` (母0/副0, +0)、`SetWindowsHookEx` (母1/副1, +0)。
- **终审判定**: **CONFIRMED**。

### R5 · 单测断言强度与覆盖真实性
- **初审陈述**: CONFIRMED (PASS)：`_w5_test.py` 经独立实跑 6 条全 PASS 且 EXIT=0；用例 2 采用严格等式 `total_extra_reads == edges * 5` 死锁 5 读（非 `<=` 放宽）；用例 2.3 时间戳全序链已适配复用模式；隔离副本改坏 `f_pre` 反例证实单测必 FAIL，断言强度充沛非摆设。
- **独立复核意见**: **CONFIRMED**。独立重跑单测与沙盒反例注入脚本 `reviews/_r5_independent_check.py` 证实：
  1. 单测全绿：`python -I -X utf8 "lead/re_line_20261105/W5_HARNESS_EXT/_w5_test.py"` 执行退出码 EXIT=0，Case 1~6 全部通过；
  2. 强断言死锁：用例 2 包含 `assert total_extra_reads == expected_edges * 5` 与 `assert extra_frame_reads == expected_edges * 1`，以及四 VA 独立的 `== expected_edges` 断言，无任何 `<=` 放宽；
  3. 全序链适配：用例 2.3 断言 `ts['f_pre'] <= ts['segment_start'] <= ... <= ts['segment_end']` 闭环覆盖；
  4. 反例敏感：在隔离沙盒 `reviews/_sandbox_r5` 中注入「退回 6 读」、「冒充时刻」、「时序倒流」三组变异代码，单测均准确触发 `AssertionError` 且抛出非零退出码（EXIT=1）。
- **终审判定**: **CONFIRMED**。

---

## 3 反例与实跑证据

汇总员在当前会话中对全部探针与关键命令进行了独立真实复核与执行，杜绝推演，全部证据均落盘可查：

### 1. 核心单测与改动面证明实跑
- **单测命令**: `python -I -X utf8 "lead/re_line_20261105/W5_HARNESS_EXT/_w5_test.py"`
  - **实跑退出码**: `0`
  - **实跑输出概要**: 耗时 0.074s，6 个用例全项 PASS（Case 1 结构零差异、Case 2 死锁 5 读与 D-21 契约、Case 3 读失败記 null 绝不补 0、Case 4 S4 立即停手、Case 5 拒绝 allow-loader 启动、Case 6 帧冻结窗零样本）。
- **改动面证明命令**: `python -I -X utf8 "lead/re_line_20261105/W5_HARNESS_EXT/_w5_diff_proof.py"`
  - **实跑退出码**: `0`
  - **实跑输出概要**: 识别 8 个定界块，删块后 SHA256 为 `38244d2907e7f7fa3cdd28f2603de432585f7ddd9027e0e0ae6348a0892752a8`（与母本逐字节完全一致）；纯新增 233 行、0 删、0 改；6 项禁止面 API 差值全量为 `+0`。

### 2. R1 反例探针与实测证据
- **探针命令**: `python -I -X utf8 "lead/re_line_20261105/V6_V3_REVIEW/_v6_r1.py"`
  - **实跑退出码**: `0`
  - **反例 1 (FRAME_VA 专用计数探针 `FrameVaOnlyCountingProbe`)**:
    - 默认模式：`pre_frame_reads = 1`, `post_frame_reads = 1`, `reads_per_sample = 6`；
    - 复用模式：`pre_frame_reads = 0`, `post_frame_reads = 1`, `reads_per_sample = 5`。
  - **反例 2 (前读越权拦截探针 `PreReadForbiddenProbe`)**:
    - 在进入业务读取前，若探测到对 `FRAME_VA` 的读访问立即抛出 `ForbiddenPreReadError`；
    - 默认模式：精准捕获 `ForbiddenPreReadError`（证明探针防御有效）；
    - 复用模式：顺利通过且零异常，证明确系零前读。

### 3. R2 时间戳契约反例实测证据
- **探针命令**: `python -I -X utf8 "lead/re_line_20261105/V6_V3_REVIEW/reviews/_r2_independent_check.py"`
  - **实跑退出码**: `0`
  - **反例 1 (偏早 10,000s 锚点注入)**: 传入 `t_pre = 100.0`，函数执行时系统进入时刻为 `10100.0`。输出实测 `ts["f_pre"] == 100.0`，`ts["segment_start"] >= 10100.0`，时间戳严格保留传入值，绝未被函数进入时刻篡改覆盖；
  - **反例 2 (未来偏晚时间戳注入)**: 传入 `t_pre = 99999.0`，实测 `ts["f_pre"] == 99999.0`，完全忠实记录；
  - **反例 3 (缺省 t_pre 模式)**: 传入 `f_pre=100, t_pre=None`，实测 `ts["f_pre"] is None` 且 `ts["f_pre_anchor_known"] = False`，杜绝伪造时间戳。

### 4. R3 AST 拓扑与唯一调用点核查证据
- **探针命令**: `python -I -X utf8 "lead/re_line_20261105/V6_V3_REVIEW/reviews/_r3_independent_check.py"`
  - **实跑退出码**: `0`
  - **AST 节点审查**: 遍历 `qc151_trip.harness8_v4_ext.py` 全语法树，`Call` 表达式为 `read_sample` 的节点计数为 1（L4166:25），实参绑定为 `arg[0]=reader, arg[1]=time.perf_counter, kw[f_pre]=f, kw[t_pre]=t_now`；
  - **因果时序审查**: L4151 `t_now = time.perf_counter()` 先于 L4154 `f = reader(MEASURE_CURRENT_FRAME_VA)` 执行，进入采样时 `t_now` 确系读前时刻。

### 5. R4 改动面篡改敏感性反例证据
- **探针命令**: `python -I -X utf8 "lead/re_line_20261105/V6_V3_REVIEW/reviews/_r4_independent_check.py"`
  - **实跑退出码**: `0`
  - **反例 1 (母本区 1 字节篡改)**: 删 8 块还原后 SHA256 检验立即失配，拦截成功；
  - **反例 2 (插入块内禁止词注入)**: 扫描器即刻告警增量 `+1`，拦截成功；
  - **反例 3 (破坏块定界标记)**: 删块引擎识别不完整抛出异常，拦截成功。

### 6. R5 单测断言破坏变异攻击证据
- **探针命令**: `python -I -X utf8 "lead/re_line_20261105/V6_V3_REVIEW/reviews/_r5_independent_check.py"`
  - **实跑退出码**: `0`
  - **变异 A (复用模式退回 6 读)**: 在沙盒副本中强行追加前帧号读，单测立即触发 `AssertionError: total_extra_reads == expected_edges * 5`，退出码 EXIT=1；
  - **变异 B (冒充外层时刻)**: 在进入函数时重新执行 `t_pre = clock()`，单测立即触发用例 2.1b 断言失败，退出码 EXIT=1；
  - **变异 C (时间戳全序破坏)**: 故意将 `ts['f_pre']` 设为大于 `ts['segment_start']`，单测用例 2.3 全序断言立即崩溃，退出码 EXIT=1。

---

## 4 必须改项

**当前必须整改项清单：0 项（空）。**

```json
{
  "mustFix": [],
  "substantiveDefects": 0,
  "objections": []
}
```

### 依据说明
1. 初审 5 份回件（`parts/R1.md` ~ `parts/R5.md`）未列出任何实质缺陷与必须改项；
2. 独立复核 5 份审查意见书（`reviews/R1_review.md` ~ `reviews/R5_review.md`）亦均给出 `mustFix: []` 与 `objections: []`；
3. 本汇总员全量独立重跑各核心脚本与探针，代码实现、断言强度、时序因果、母本零污染与向后兼容性全部满足 D-21 裁 A 规定；
4. 无读数错误、丢读、伪造 0、时序倒流、旧调用遗漏或禁止 API 泄漏现象，故整改项数为 0。

---

## 5 诚实账

1. **零真机铁律坚守**：
   - 全程未启动 `gamemd.exe`、`ra2loader`、`YURI.exe` 等游戏主程序；
   - 未使用 `taskkill` 或终止任何运行中进程；
   - 未通过 OpenProcess / ReadProcessMemory 读取任何活进程内存，所有实跑均为纯 Python 离线模拟与静态 AST/正则扫描。
2. **零注入代码铁律坚守**：
   - 未编写或执行任何 DLL 注入、线程挂起（SuspendThread）、堆栈回溯（StackWalk）、内存转储（MiniDump）或 Windows 全局钩子。
3. **既有生产文件只读红线**：
   - `lead/goal1_harness8_20261031/` 下母本件绝对未动；
   - `lead/re_line_20261105/A1_SAMPLER_CANDIDATE/` 与 `W5_HARNESS_EXT/` 下的文件在复核期间保持绝对只读；
   - 反例注入攻击完全在隔离沙盒 `lead/re_line_20261105/V6_V3_REVIEW/reviews/_sandbox_r5/` 内进行，并在验证完毕后即刻彻底销毁清理。
4. **测量求真与不造假**：
   - 所有文件 SHA256 均通过 `open(f, 'rb').read()` 配合 `hashlib.sha256()` 动态实测获得，拒绝静态照抄；
   - 每个命令均在终端中完整执行，并核查退出码 `EXIT_CODE=0`，未出现「未跑先判」或「走读代跑」现象。
5. **局限与后续说明**：
   - 本次复核验证了 V3 状态下离线逻辑与断言强度的严密性，并不代表物理真机环境下的真实内存抖动消除；
   - W5 采样记录中携带的双标记（`alpha_uncalibrated` 与 `sampling_sufficiency_unproven`）为合规披露标记，下游消费模块需继续维持对该标记的识别与隔离。
