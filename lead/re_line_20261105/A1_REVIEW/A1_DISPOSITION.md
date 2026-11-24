# A1 复核处置记录 · 两组均判 PARTIAL，5 条缺陷已全部闭合

> **复核执行者**：`dwfrun-d10c0966`（`magpie/antigravity/gemini-3.8-flash$high`，两组并行）
> **被复核对象**：`A1_SAMPLER_CANDIDATE/frame_edge_sampler.py`（`FRAME_EDGE_V1`，67 项单测）
> **本文件地位**：记录**复核判定**与**我的处置**。汇总件 `A1_REVIEW.md` 由工作流汇总员写，
> 但它**基于修复前**的候选件；本文件记载的是**修复后**的状态，两者以本文件为准。

## 0. 一句话结论

**两组独立复核均判 `PARTIAL`（无单一"实质缺陷"，但共 5 条必修/建议改）。**
**5 条已全部修复**，候选件升版 `FRAME_EDGE_V1 → FRAME_EDGE_V2`，
离线单测 **67 → 85 项，全通过（`EXIT=0`）**，并有 19 项**修复后独立验证**全部通过。

## 1. 复核判定（两侧原话要点）

| 组 | 模型上下文 | 判定 | `substantiveDefect` | 通过项 / 问题项 |
|---|---|---|---|---|
| 语义组（R1–R3，`part_code_lens.md`，19.4 KB） | 独立子代理 | **PARTIAL** | `False` | R1 **满足**（失败不补 0、`bool` 拒收、越界拒收、合法 0 透传）；R2 **部分满足**（缺读段闭合止点）；R3 **满足**（`df>1` 无插值、`df<0` 不可判合理、`f is None` 三态正确） |
| 合规组（R4–R6，`part_spec_lens.md`，12.9 KB） | 独立子代理 | **PARTIAL** | `False` | R4 **部分满足**（读失败断裂状态机有缺陷，给 2 组反例）；R5 **部分满足**（`freeze_max_s` 命名可被下游穿透 `note`）；R6 **满足**（受禁 API 全 0、`RpmReader` 默认关闭、导入零副作用） |

## 2. 五条缺陷 + 我的独立验证（不采信转述）

复核报出后，我先写 `_leader_verify_r4r5.py` **自己复现**，全部属实：

| # | 缺陷 | 复现序列 | 修复前实测 | 谁发现 |
|---|---|---|---|---|
| D1 | 读失败后恢复同值 ⇒ **虚报冻结** | `[100, None, 100]` | `freeze_max_s = 0.02`（真实应为 0） | 复核 R4 |
| D2 | 读失败后恢复跳值 ⇒ **虚报漏沿 + 假聚合** | `[100, None, 150]` | `missed = 49`、事件标 `aggregate_over_50_frames` | 复核 R4 |
| D3 | 长时段读失败 ⇒ **冻结大幅虚增** | `[100, None×5, 100]` | `freeze_max_s = 6.0`（真实应为 0） | 复核 R4 |
| D4 | `read_sample` **缺读段闭合止点** | — | `ts` 无 `segment_end`，无法度量 `f_post` 耗时 | 复核 R2 |
| D5 | **无 dt/df 物理相容性守卫** | `[100, 150]`（10 ms 内 df=50） | 记 `missed=49`，隐含 **5000 fps** 却无任何告警 | **我自己发现**（复核未提） |

★ D1/D2/D3 **同根**：`prev_f is None` 一个变量同时承载「窗口首样本」与「读失败断裂」两种含义。
★ D5 与 D2 **同源**：都缺「dt 与 df 是否相容」的检查。

## 3. 修复内容（`FRAME_EDGE_V1 → V2`）

| 修复 | 做法 |
|---|---|
| D1/D2/D3 | 引入 **两个正交状态**：`initialized`（本窗是否已捕获首帧号）+ `prev_lost`（上一轮是否读失败）。读失败**立刻切断冻结计时**；恢复点一律记 `resume_after_loss` 并**重新起算**，**不跨断裂比较、不跨断裂累计冻结、不跨断裂求差**。新增计数 `resume_after_loss`。 |
| D4 | `read_sample` 增加 `ts["segment_start"]` / `ts["f_post_start"]` / `ts["segment_end"]`，读段具备完整 `[start, end]` 边界。 |
| D5 | 新增 `MAX_PLAUSIBLE_FPS = 1000.0` 与 `_df_dt_plausible()`；`df>1` 时若隐含帧率超上界 ⇒ 计数 `implausible_df` 并给事件打 `df_dt_plausible=False`。`t` 缺失/间隔 ≤0 ⇒ 返回 `None`（**不猜**）。 |
| R5 | `stats()` 键名 `freeze_max_s` → **`frame_clock_freeze_max_s`**（自解释），`note` 增写「读失败墙钟不计入」。 |
| 版本 | `SCHEMA = "FRAME_EDGE_V2"`，下游按版本拒收旧件。 |

★ **修复过程中我自己又犯了一个错并当场抓到**：`prev_t` 在 dt/df 判定**之前**就被覆盖，
导致 `df_dt_plausible` 恒为 `None`（T8.13 FAIL）。已改为先抓 `prev_t = self.prev_t` 再判定。

## 4. 实跑命令与结果

```bash
# 修复后离线单测
python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/re_line_20261105/A1_SAMPLER_CANDIDATE/test_frame_edge_sampler.py"
# → EXIT=0，SUMMARY PASS=85  FAIL=0

# 修复后独立验证（我另写一份，不依赖单测框架）
python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/re_line_20261105/A1_REVIEW/_leader_verify_after_fix.py"
# → EXIT=0，SUMMARY PASS=19  FAIL=0
```

**独立验证的 19 项**覆盖：D1/D2/D3 已闭合、**真冻结仍被测到**（防修复过度）、
R5 键名新旧交替、D5 告警生效、**合理 df 不误报**（`df=5/1s` = 5 fps 合法）、
**`df<0` 仍记 `unjudgeable`**（防修复吃掉原语义）、schema 已升 V2。

## 5. 诚实账

1. **我亲验**：两组复核回件（逐行读过）；D1–D5 全部用我自己的脚本复现（修复前）；
   修复后 85 项单测 + 19 项独立验证，均 `EXIT=0`。
2. **我亲验**：修复过程中引入的 `prev_t` 覆盖 bug（T8.13 FAIL → 修正 → 通过）。
   这是**我改出来的**，不是复核员报的。
3. **我未验**：
   - **真机通道**——仍未跑一趟；
   - `df<0` 的三种成因（重置/回绕/进程重启）**仍不可区分**（语义组 R3 也确认静态上无信号，
     建议保持 `unjudgeable`，我采纳）；
   - 汇总件 `A1_REVIEW.md` 尚未产出（工作流 phase 2 在跑），且它基于**修复前**的候选件
     ⇒ **即使它写 CONFIRMED/PARTIAL，也是旧状态的判定**，以本文件为准。
4. **未改**复核员写的任何文件；**未 commit**；本步**零真机**。

## 6. 下一步

1. 汇总件落盘后**只作参考**（它评的是 V1）。
2. 做 **harness 只读扩项副本**（四 VA + 帧沿触发），先离线单测。
3. 才考虑 3 趟隔离载体真机。
4. **两个未证标记全链条不得移除**（修复后仍在每条记录的 `markers` 字段）。
