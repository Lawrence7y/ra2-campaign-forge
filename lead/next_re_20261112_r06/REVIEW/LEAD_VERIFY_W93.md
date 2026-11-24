# LEAD_VERIFY_W93 · `clamp=210` 定谳（= 显示器刷新率）+ ABBA 一套可跑脚本

> 记录人：Lead｜时间：2026-11-14 17:0x（Asia/Shanghai）｜卡：**W93**｜执行：`call-agy` / `agy` **`gemini-4-hydrogen-high`**
> **运行状态：`status=ERROR`（非工作失败）** —— `conversation_id=3b90e933-2dcd-48ba-8d15-4dca6396b4e9`，`elapsed=1109.5 s`；失败原因是**网络层**：`API error (attempt 2): … wsasend: An existing connection was forcibly closed by the remote host`。它在断线前已输出终局文本（"已完成离线卡 W93（限帧通…"）且**全部产物已落盘**。本条按"产物验收"签发，不按其自述。
> 我的复核：`verify_ddraw_globals.py`/`abba_driver.py`/`abba_analyze.py` 的 `--help` 实跑；自测套件实跑；`clamp` 结论用**本机独立实测**复验。

## 1 · 签发：`clamp=210` 已定谳，且**W86 的解读是错的**

| 项 | 结论 |
|---|---|
| `ddraw+0x5EE48` 是什么 | **`DEVMODEA.dmDisplayFrequency`**（当前显示器刷新率），不是"参考上限 60" |
| 结构体 | `0x1005EDD0` 起是全局 `DEVMODEA`；`0x1005EDD0 + 0x78 = 0x1005EE48` |
| 谁写入 | `0x10015E34..0x10015E50` 调 `USER32!EnumDisplaySettingsA(NULL,-1,0x1005EDD0)`，**由系统整块写入结构体** |
| `mov [0x1005EE48], 0x3C` | **只是枚举失败时的兜底**（W86 把它当成"启动时写死 60"，错） |

**我的独立复验（不是转述）**：
- `sizeof(DEVMODEA)=124`、**`off(dmDisplayFrequency)=0x78`**、`0x1005EDD0+0x78 = 0x1005EE48` ✓
- 本机 `EnumDisplaySettingsA(NULL,-1,…)` 返回 **2560×1440 / 32bpp / `dmDisplayFrequency = 210 Hz`** ✓ —— 与 W90 实测的 `clamp=210` **完全吻合**。

⇒ **连带影响（必须改读法）**：门闸 `cmp maxfps(60), [0x1005EE48](210) → jb` 在本机**总是走 `timeGetTime+Sleep` 兜底支路**，而不是 waitable-timer 支路。凡引用"限帧分支"的结论都要按这条重读。
已在台账立 **§628**，并把方法学定为：**"立即数写入" ≠ "运行时值"**，凡断言某全局的运行时值必须活进程读一次，或找全写入者（含结构体级写入）。

## 2 · 签发：ABBA 一套脚本可用（**但从未执行过**）
交付：`abba_driver.py`（按 A→B→B→A 外部启停只读观测器，写 `switch_log.ndjson`）、`abba_analyze.py`（区组内配对 `d_block=mean(A)−mean(B)` + 三档判决）、`verify_ddraw_globals.py`（活进程只读 dump `.data` 窗口 + 断言 maxfps/interval/刷新率）、`ABBA.md`。

我实跑复核：
- 三个脚本 `--help` 正常，参数与协议一致（`--blocks/--seg-sec/--warm-sec/--budget-pp`）。
- `EVIDENCE\test_abba_suite.py` 实跑 → **`[ALL PASS] … self-test suite succeeded`**；判决样例合理：3 区组 `d_block = +0.30 / −0.20 / +0.20 pp`，|均值| 0.10 ≤ 预算 0.50 但**方向不一致** ⇒ 正确落 `[UNRESOLVED] 未分辨`（而不是误判"通过"）——**这正是协议要的行为**。
- `abba_driver.py` 把子进程 stdout **重定向到文件且 `encoding="utf-8"`**（第 201 行），不走 pipe ⇒ 真机运行不受编码问题影响。

## 3 · 我修的一处缺陷（已记录，不是悄悄改）
`EVIDENCE\test_abba_suite.py` 用 `subprocess.run(..., capture_output=True, text=True)` 捕获子进程输出，**默认按 GBK 解码**；遇到非 ASCII 输出即 `UnicodeDecodeError`，随后 `res.stdout` 为 `None` 再抛 `AttributeError`。**而它自己的存档 `abba_selftest.txt` 写着 `[ALL PASS]`** —— 说明存档是在不同编码环境下产生的，**光看存档会漏掉这个缺陷**。
`[我的处置]` 把 5 处 `capture_output=True` 补成 `capture_output=True, encoding="utf-8", errors="replace"` 并删掉 `text=True`，实跑通过。
`[教训]` 与本项目 `call-agy` 处理同一类问题一致：**凡捕获子进程文本输出，必须显式 UTF-8**。

## 4 · 边界（不许越写）
- **ABBA 从未在真机上执行过**：`abba_driver.py`/`abba_analyze.py` 只有自测证据。本卡不产生任何"观测器扰动可接受/不可接受"的结论。
- 裁决 Q3 要求的**独立画面参照**（外置高速摄像或已证精度仪器）本项目**仍然没有** ⇒ 即使将来 ABBA 全绿，也只能说"观测器扰动在预算内"，**不能**据此闭合"画面是否卡"。
- `0x1005F120`（限帧放行时刻）**是否在每条渲染路径下都逐帧更新**，本卡只在报告里给了分支说明；我未逐分支动态验证。
- agy 的 `status=ERROR` 属网络中断；**未重跑**（产物齐全，重跑无收益）。若后续发现脚本在真机上行为异常，再用 `--conversation 3b90e933-…` 续轮。

## 5 · 签发语
`[签发]` ① `clamp=210` = **显示器刷新率 210 Hz**，W86 的"参考上限 60"表述**作废**（台账 §628）；② ABBA 一套脚本**可用但未执行**；③ 我修了测试件的 UTF-8 缺陷并复跑通过。
`[下一张真机卡可直接用]` `verify_ddraw_globals.py <pid>` 做自洽体检；`abba_driver.py --pid <pid> --blocks 3` + `abba_analyze.py` 做扰动校准（代价约 12 分钟局内）。
