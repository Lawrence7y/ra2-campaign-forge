# LEAD_VERIFY_V83 · `call-agy`（Gemini 4 H）独立复审 W80 的"三旋钮否证"：**证实**

> 记录人：Lead｜时间：2026-11-14 10:11
> 手段：`call-agy` → Antigravity `gemini-4-hydrogen-high`（conversation `7e66364f-b8ab-4fb9-9ae8-17c886b36626`，51.5 s），**Lead 亲跑**其脚本
> 被审对象：`REVIEW\LEAD_VERIFY_W80.md`（"`maxgameticks`/`GameSpeed`/`UnlockGameSpeed` 三个旋钮都不影响 `survive` 斜率"）

## 1 · 它的脚本做了什么（我要求的"不看散文、只看原始记录"）

1. 递归发现所有 `TRIP_RESULT.json`（**不硬编码趟名**）
2. **防御性提取**判胜帧：兼容 `result.observation.terminal` 与 `result.terminal` 两种形状，缺 `frame_at` 时回退 `frame`，**并逐文件打印它用的是哪条路径**
3. 从同名 trip 目录读 `CONFIG_PRE.json`，报 `condition` 与 `config_diff_vs_pristine`（**哪几个文件被改**）
4. 按 `N` 分组做不变性检验，**并逐 N 核对是否等于 `15N+90`**
5. 打印它无法分类的趟（**不允许静默丢弃**）

## 2 · 结果（我亲跑，退出码 0）

```
trip                 condition    changed_files   frame_at  ok    outcome
trip_base_s20        base         []              390       True  VICTORY_RESULT_AND_TERMINATION_OK
trip_base_s8         base         []              210       True  VICTORY_RESULT_AND_TERMINATION_OK
trip_e1_30_s20       e1_30        ddraw.ini       390       True  VICTORY_RESULT_AND_TERMINATION_OK
trip_e1_30_s8        e1_30        ddraw.ini       210       True  VICTORY_RESULT_AND_TERMINATION_OK
trip_e2_gs2_s20      e2_gs2       RA2MD.INI       390       True  VICTORY_RESULT_AND_TERMINATION_OK
trip_e2b_all_s20     e2_gs2_all   RA2MD.INI       390       True  VICTORY_RESULT_AND_TERMINATION_OK
trip_e3_unlock_s20   e3_unlock    ra2render.ini   390       True  VICTORY_RESULT_AND_TERMINATION_OK

PER_N_SUMMARY:
  N=8 : trips=2  frames=[210,210]                       invariant=True  equals_15N_plus_90=True
  N=20: trips=5  frames=[390,390,390,390,390]           invariant=True  equals_15N_plus_90=True
VERDICT: CLAIM HOLDS per-N frames are invariant
UNCLASSIFIED: none
```

## 3 · 签发

`[签发]` **W80 的"三旋钮否证"成立**，且 `frame = 15N + 90` 再次在 7 个点上成立（分 N 后：N=8 两点、N=20 五点，**逐 N 完全不变**）。
`[证据等级提升]` 这不再是"我读了卡的数据"，而是**异模型自己写解析器、自己分组、自己判不变性**得出的同一结论。且它**逐 N 核对了 `15N+90`**（我原签发件只做了整体拟合）。

## 4 · 它报告的两处"异常"，我判定都不是问题

`trip_base_s20` / `trip_base_s8` 的 `config_diff_vs_pristine` 为空 —— **这正是基线臂的定义**（`condition=base`、不改任何配置）。它按"异常"列出是保守做法，值得肯定。

## 5 · 我采纳的一条方法论改进

它把**"按 N 分组看不变性"**做成了显式检验（`invariant=True` + `equals_15N_plus_90=True` 分开报）。我原先只做"拟合一条直线"—— 那会掩盖"某个 N 的点彼此不一致"这种情况（例如若 `survive(20)` 的两趟分别是 390 与 400，整体拟合仍可能看起来没问题）。**今后凡"规律类"结论，都要按自变量分组核不变性，而不是只拟合。**

## 6 · 边界

`[仍未解决]` `15` 这个斜率**从哪里来**（三个配置旋钮已排除；H-E「引擎把 15 帧当 1 秒」仍无直接证据）。
`[本复审核的是什么]` 只核"三旋钮无效 + `15N+90` 在 7 点成立"这一**事实层**；**不涉及机制解释**。
